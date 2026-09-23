# Phase 3 Raw-OHLC Replay Follow-Up Analysis

**Created UTC:** 2026-05-01T13:08:20.738538+00:00
**Summary:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\raw_ohlc_prequential_replay_20260501T111737Z.json`
**Event log:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\raw_ohlc_prequential_events_20260501T104217Z.jsonl`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- This analysis uses the full raw-OHLC replay event log and summary.
- DSR, PBO, and effective_N diagnostics are same-dataset and not promotion-usable.
- The purpose is interpretation, ambiguity reduction, and next-step prioritization.

## Run Scope

| source_scope | rows_replayed | event_rows_read | take_rows_seen | first_take_clock | last_take_clock | active_cohorts |
| --- | --- | --- | --- | --- | --- | --- |
| FULL_AVAILABLE_CORPUS | 131726 | 131726 | 15827 | 2022-03-01T07:15:00+00:00 | 2026-04-30T09:30:00+00:00 | 8 |

## Direct Answers

| question | answer |
| --- | --- |
| Was the headline mostly held back by the GBPUSD negative control? | Yes, materially. The GBPUSD control contributed -69.2339R and its mean R was -0.117545. But the bigger result is target-vs-control separation. |
| Did the approved target cohorts separate from negative controls? | Yes. Targets: n=1224, mean R=0.408527, sum R=500.0366. Negative controls: n=1277, mean R=-0.064495, sum R=-82.3606. |
| Does this promote a strategy? | No. DSR/PBO/effective_N diagnostics remain same-dataset and post-hoc. PBO diagnostic status=COMPUTED_POSTHOC_DIAGNOSTIC_ONLY, pbo=0.462413; target effective_N=4.732366. |
| What is the main remaining risk? | Individual-cohort recent-period power is uneven. The family-level recency is encouraging, but several target cohorts have low or zero 2026 resolved rows. |

## Group Summary

| group | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | same_dataset_dsr_p | same_dataset_dsr_threshold_met | dsr_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_enabled | 15827 | 7106 | 2501 | 417.676 | 0.167004 | 0.482607 | 5.1355484e-05 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| all_excluding_gbpusd_control | 13942 | 5637 | 1912 | 486.9099 | 0.25466 | 0.51569 | 7.13e-10 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| target_cohorts | 8222 | 3808 | 1224 | 500.0366 | 0.408527 | 0.575163 | 0.0 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| primary_controlled_family | 4086 | 1661 | 577 | 217.5845 | 0.377096 | 0.566724 | 1.4219426e-05 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| cleared_non_primary_targets | 4136 | 2147 | 647 | 282.4521 | 0.436557 | 0.582689 | 9.496e-09 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| negative_controls | 7605 | 3298 | 1277 | -82.3606 | -0.064495 | 0.393892 | 0.999999748843 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |  |  | INSUFFICIENT_RESOLVED_RETURNS |

## Target-Control Separation

| target_mean_r | control_mean_r | blocked_control_mean_r | target_minus_control_mean_r | target_sum_r | control_sum_r | blocked_control_sum_r | target_minus_blocked_control_mean_r | gbpusd_control_drag_r | headline_mean_r_all_enabled | headline_mean_r_without_gbpusd_control |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.408527 | -0.064495 |  | 0.473022 | 500.0366 | -82.3606 | 0.0 |  | -69.2339 | 0.167004 | 0.25466 |

## Recency Windows

| window_group | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| all\|target_cohorts | 8222 | 3808 | 1224 | 500.0366 | 0.408527 | 0.575163 |
| all\|negative_controls | 7605 | 3298 | 1277 | -82.3606 | -0.064495 | 0.393892 |
| all\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |
| 2024_plus\|target_cohorts | 5202 | 2354 | 700 | 330.8552 | 0.47265 | 0.604286 |
| 2024_plus\|negative_controls | 3870 | 1612 | 619 | 11.8216 | 0.019098 | 0.432956 |
| 2024_plus\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |
| 2025_plus\|target_cohorts | 3613 | 1617 | 466 | 236.6332 | 0.507797 | 0.609442 |
| 2025_plus\|negative_controls | 2386 | 945 | 399 | -75.6849 | -0.189686 | 0.350877 |
| 2025_plus\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |
| 2026_only\|target_cohorts | 523 | 134 | 50 | 19.5084 | 0.390168 | 0.58 |
| 2026_only\|negative_controls | 961 | 348 | 190 | -5.0133 | -0.026386 | 0.426316 |
| 2026_only\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |
| last_12m_from_2025_05\|target_cohorts | 2151 | 881 | 277 | 163.1332 | 0.588929 | 0.646209 |
| last_12m_from_2025_05\|negative_controls | 2047 | 879 | 373 | -97.9919 | -0.262713 | 0.313673 |
| last_12m_from_2025_05\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |
| last_6m_from_2025_11\|target_cohorts | 703 | 265 | 80 | 64.6306 | 0.807883 | 0.7375 |
| last_6m_from_2025_11\|negative_controls | 1311 | 501 | 221 | 1.5083 | 0.006825 | 0.434389 |
| last_6m_from_2025_11\|blocked_dominance_controls | 0 | 0 | 0 | 0.0 |  |  |

## Cohort Recency Detail

| cohort_window | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | role | population_per_action | resolved_per_action | top_outcome | top_outcome_count | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1\|2025_plus | 1229 | 494 | 209 | 95.8452 | 0.458589 | 0.578947 | primary_controlled_child | 0.401953 | 0.170057 | SETUP_NOT_REFINABLE | 634 | TARGET_POSITIVE_WINDOW |
| GBPJPY\|tokyo\|bullish\|D1\|2026_only | 305 | 83 | 35 | -0.4916 | -0.014046 | 0.428571 | primary_controlled_child | 0.272131 | 0.114754 | SETUP_NOT_REFINABLE | 181 | TARGET_NON_POSITIVE_WINDOW |
| GBPJPY\|tokyo\|bullish\|D1\|last_12m_from_2025_05 | 1157 | 434 | 161 | 83.8452 | 0.520778 | 0.602484 | primary_controlled_child | 0.375108 | 0.139153 | SETUP_NOT_REFINABLE | 622 | TARGET_POSITIVE_WINDOW |
| GBPJPY\|tokyo\|bullish\|D1\|last_6m_from_2025_11 | 485 | 214 | 65 | 44.6306 | 0.686625 | 0.692308 | primary_controlled_child | 0.441237 | 0.134021 | SETUP_NOT_REFINABLE | 229 | TARGET_POSITIVE_WINDOW |
| GBPUSD\|london\|bearish\|H4+H1_consensus\|2025_plus | 688 | 549 | 206 | -134.6898 | -0.653834 | 0.160194 | negative_control | 0.797965 | 0.299419 | NO_ENTRY | 343 | CONTROL_NON_POSITIVE_WINDOW |
| GBPUSD\|london\|bearish\|H4+H1_consensus\|2026_only | 204 | 144 | 65 | -43.6896 | -0.672148 | 0.2 | negative_control | 0.705882 | 0.318627 | NO_ENTRY | 79 | CONTROL_NON_POSITIVE_WINDOW |
| GBPUSD\|london\|bearish\|H4+H1_consensus\|last_12m_from_2025_05 | 648 | 509 | 206 | -134.6898 | -0.653834 | 0.160194 | negative_control | 0.785494 | 0.317901 | NO_ENTRY | 303 | CONTROL_NON_POSITIVE_WINDOW |
| GBPUSD\|london\|bearish\|H4+H1_consensus\|last_6m_from_2025_11 | 224 | 164 | 65 | -43.6896 | -0.672148 | 0.2 | negative_control | 0.732143 | 0.290179 | NO_ENTRY | 99 | CONTROL_NON_POSITIVE_WINDOW |
| USDJPY\|london\|bearish\|D1\|2025_plus | 416 | 183 | 35 | 47.5 | 1.357143 | 0.942857 | cleared_non_primary_strong_lead | 0.439904 | 0.084135 | SETUP_NOT_REFINABLE | 166 | TARGET_POSITIVE_WINDOW |
| USDJPY\|london\|bearish\|D1\|2026_only | 40 | 0 | 0 | 0.0 |  |  | cleared_non_primary_strong_lead | 0.0 | 0.0 | SETUP_NOT_REFINABLE | 20 | UNDERPOWERED_WINDOW |
| USDJPY\|london\|bearish\|D1\|last_12m_from_2025_05 | 90 | 2 | 2 | 3.0 | 1.5 | 1.0 | cleared_non_primary_strong_lead | 0.022222 | 0.022222 | SETUP_NOT_REFINABLE | 62 | UNDERPOWERED_WINDOW |
| USDJPY\|london\|bearish\|D1\|last_6m_from_2025_11 | 40 | 0 | 0 | 0.0 |  |  | cleared_non_primary_strong_lead | 0.0 | 0.0 | SETUP_NOT_REFINABLE | 20 | UNDERPOWERED_WINDOW |
| USDJPY\|london\|bullish\|D1\|2025_plus | 774 | 167 | 76 | 26.5216 | 0.348968 | 0.539474 | negative_control | 0.215762 | 0.098191 | SETUP_NOT_REFINABLE | 519 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|london\|bullish\|D1\|2026_only | 340 | 94 | 53 | 29.5 | 0.556604 | 0.622642 | negative_control | 0.276471 | 0.155882 | SETUP_NOT_REFINABLE | 223 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|london\|bullish\|D1\|last_12m_from_2025_05 | 634 | 159 | 68 | 14.5216 | 0.213553 | 0.485294 | negative_control | 0.250789 | 0.107256 | SETUP_NOT_REFINABLE | 399 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|london\|bullish\|D1\|last_6m_from_2025_11 | 490 | 148 | 67 | 15.5216 | 0.231666 | 0.492537 | negative_control | 0.302041 | 0.136735 | SETUP_NOT_REFINABLE | 300 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|tokyo\|bearish\|D1\|2025_plus | 494 | 209 | 55 | 0.0 | 0.0 | 0.4 | primary_controlled_child | 0.423077 | 0.111336 | SETUP_NOT_REFINABLE | 214 | TARGET_NON_POSITIVE_WINDOW |
| USDJPY\|tokyo\|bearish\|D1\|2026_only | 48 | 1 | 1 | -1.0 | -1.0 | 0.0 | primary_controlled_child | 0.020833 | 0.020833 | SETUP_NOT_REFINABLE | 31 | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bearish\|D1\|last_12m_from_2025_05 | 108 | 1 | 1 | -1.0 | -1.0 | 0.0 | primary_controlled_child | 0.009259 | 0.009259 | SETUP_NOT_REFINABLE | 81 | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bearish\|D1\|last_6m_from_2025_11 | 48 | 1 | 1 | -1.0 | -1.0 | 0.0 | primary_controlled_child | 0.020833 | 0.020833 | SETUP_NOT_REFINABLE | 31 | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus\|2025_plus | 168 | 77 | 44 | 16.0 | 0.363636 | 0.545455 | cleared_non_primary_strong_lead | 0.458333 | 0.261905 | SETUP_NOT_REFINABLE | 62 | TARGET_POSITIVE_WINDOW |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus\|2026_only | 0 | 0 | 0 | 0.0 |  |  | cleared_non_primary_strong_lead |  |  |  |  | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus\|last_12m_from_2025_05 | 36 | 19 | 19 | 11.0 | 0.578947 | 0.631579 | cleared_non_primary_strong_lead | 0.527778 | 0.527778 | TP | 12 | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus\|last_6m_from_2025_11 | 0 | 0 | 0 | 0.0 |  |  | cleared_non_primary_strong_lead |  |  |  |  | UNDERPOWERED_WINDOW |
| USDJPY\|tokyo\|bullish\|D1\|2025_plus | 924 | 229 | 117 | 32.4833 | 0.277635 | 0.564103 | negative_control | 0.247835 | 0.126623 | SETUP_NOT_REFINABLE | 546 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|tokyo\|bullish\|D1\|2026_only | 417 | 110 | 72 | 9.1763 | 0.127449 | 0.486111 | negative_control | 0.263789 | 0.172662 | SETUP_NOT_REFINABLE | 269 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|tokyo\|bullish\|D1\|last_12m_from_2025_05 | 765 | 211 | 99 | 22.1763 | 0.224003 | 0.515152 | negative_control | 0.275817 | 0.129412 | SETUP_NOT_REFINABLE | 425 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| USDJPY\|tokyo\|bullish\|D1\|last_6m_from_2025_11 | 597 | 189 | 89 | 29.6763 | 0.333442 | 0.561798 | negative_control | 0.316583 | 0.149079 | SETUP_NOT_REFINABLE | 324 | CONTROL_POSITIVE_WINDOW_CHECK_REQUIRED |
| XAGUSD\|london\|bullish\|D1\|2025_plus | 1306 | 654 | 123 | 77.288 | 0.628358 | 0.682927 | cleared_non_primary_strong_lead | 0.500766 | 0.094181 | NO_ENTRY | 531 | TARGET_POSITIVE_WINDOW |
| XAGUSD\|london\|bullish\|D1\|2026_only | 130 | 50 | 14 | 21.0 | 1.5 | 1.0 | cleared_non_primary_strong_lead | 0.384615 | 0.107692 | SETUP_NOT_REFINABLE | 59 | UNDERPOWERED_WINDOW |
| XAGUSD\|london\|bullish\|D1\|last_12m_from_2025_05 | 760 | 425 | 94 | 66.288 | 0.705191 | 0.723404 | cleared_non_primary_strong_lead | 0.559211 | 0.123684 | NO_ENTRY | 331 | TARGET_POSITIVE_WINDOW |
| XAGUSD\|london\|bullish\|D1\|last_6m_from_2025_11 | 130 | 50 | 14 | 21.0 | 1.5 | 1.0 | cleared_non_primary_strong_lead | 0.384615 | 0.107692 | SETUP_NOT_REFINABLE | 59 | UNDERPOWERED_WINDOW |

## Cohort Summary

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | role | valid_years_n_ge_30 | positive_valid_years | top_year | top_year_resolved_share | top_year_mean_r | top_month | top_month_resolved_share | mean_r_2025_plus | resolved_n_2025_plus | mean_r_2026 | resolved_n_2026 | status_read | same_dataset_dsr_p | same_dataset_dsr_threshold_met | dsr_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|london\|bearish\|D1 | 1118 | 453 | 129 | 66.0 | 0.511628 | 0.604651 | cleared_non_primary_strong_lead | 3 | 2 | 2023 | 0.348837 | -0.111111 | 2022-11 | 0.255814 | 1.357143 | 35 |  | 0 | TARGET_POSITIVE_OVERALL_BUT_2026_UNDERPOWERED | 0.104188436748 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 690 | 541 | 212 | 100.2102 | 0.47269 | 0.603774 | cleared_non_primary_strong_lead | 4 | 4 | 2023 | 0.320755 | 0.590671 | 2023-11 | 0.169811 | 0.363636 | 44 |  | 0 | TARGET_POSITIVE_OVERALL_BUT_2026_UNDERPOWERED | 0.009674082524 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| XAGUSD\|london\|bullish\|D1 | 2328 | 1153 | 306 | 116.2419 | 0.379875 | 0.558824 | cleared_non_primary_strong_lead | 4 | 4 | 2025 | 0.356209 | 0.516404 | 2022-12 | 0.153595 | 0.628358 | 123 | 1.5 | 14 | TARGET_POSITIVE_OVERALL_BUT_2026_UNDERPOWERED | 0.014631411028 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| USDJPY\|london\|bullish\|D1 | 2581 | 819 | 308 | -1.5765 | -0.005119 | 0.399351 | negative_control | 3 | 2 | 2023 | 0.480519 | 0.031535 | 2026-03 | 0.13961 | 0.348968 | 76 | 0.556604 | 53 | NEGATIVE_CONTROL_RECENT_POSITIVE_CHECK_REQUIRED | 0.999190128792 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| USDJPY\|tokyo\|bullish\|D1 | 3139 | 1010 | 380 | -11.5502 | -0.030395 | 0.418421 | negative_control | 5 | 3 | 2023 | 0.418421 | -0.346123 | 2023-05 | 0.102632 | 0.277635 | 117 | 0.127449 | 72 | NEGATIVE_CONTROL_RECENT_POSITIVE_CHECK_REQUIRED | 0.999828269958 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| GBPUSD\|london\|bearish\|H4+H1_consensus | 1885 | 1469 | 589 | -69.2339 | -0.117545 | 0.375212 | negative_control | 5 | 2 | 2023 | 0.322581 | -0.106139 | 2025-07 | 0.101868 | -0.653834 | 206 | -0.672148 | 65 | NEGATIVE_CONTROL_NON_POSITIVE_FULL_CORPUS | 0.9999999805 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| GBPJPY\|tokyo\|bullish\|D1 | 2741 | 1106 | 387 | 155.0845 | 0.400735 | 0.583979 | primary_controlled_child | 4 | 3 | 2025 | 0.449612 | 0.55366 | 2025-03 | 0.124031 | 0.458589 | 209 | -0.014046 | 35 | TARGET_POSITIVE_OVERALL_BUT_2026_NON_POSITIVE | 0.000486213193 | True | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |
| USDJPY\|tokyo\|bearish\|D1 | 1345 | 555 | 190 | 62.5 | 0.328947 | 0.531579 | primary_controlled_child | 3 | 3 | 2022 | 0.310526 | 0.228814 | 2025-02 | 0.284211 | 0.0 | 55 | -1.0 | 1 | TARGET_POSITIVE_OVERALL_BUT_2026_UNDERPOWERED | 0.31591235284 | False | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY |

## Methodology Diagnostics

| pbo | pbo_status | pbo_promotion_usable | all_enabled_effective_N | target_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- | --- |
| 0.462413 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | False | 7.153523 | 4.732366 | False |

## PBO Variants

| variant | strategy_count | period_count | pbo | status | combination_count | logit_mean | promotion_usable | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_enabled_individual_cohorts | 8 | 50 | 0.462413 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | 3432 | 0.099241 | False | Risk of selecting the best individual cohort from all enabled cohorts. |
| target_child_selection | 5 | 50 | 0.546037 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | 3432 | -0.380746 | False | Risk of selecting the best child from the five target cohorts. |
| negative_control_child_selection | 3 | 50 | 0.67366 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | 3432 | -0.716403 | False | Diagnostic behavior of the negative-control child universe. |
| target_family_vs_negative_control_family | 2 | 50 | 0.0 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | 3432 | 0.693147 | False | Stability of the pre-registered target-family composite versus negative controls. |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| No-leak replay integrity | RESOLVED_FOR_THIS_RUN | The parent full replay reported 0 future exposure, 0 HTF as-of violations, and 0 AI calls. |
| GBPUSD control drag | RESOLVED_FOR_THIS_RUN | Quantified separately; it is a negative-control drag, not a hidden target failure. |
| Target-vs-control separation | RESOLVED_FOR_THIS_RUN | Targets are positive as a family while negative controls are negative as a family. |
| 2026 individual cohort recency | REMAINS_UNDERPOWERED | USDJPY\|london\|bearish\|D1; USDJPY\|tokyo\|bearish\|H4+H1_consensus; XAGUSD\|london\|bullish\|D1; USDJPY\|tokyo\|bearish\|D1 |
| 2026 target non-positive windows | REMAINS_RECENCY_WARNING | GBPJPY\|tokyo\|bullish\|D1 |
| Recent negative-control cleanliness | REMAINS_MIXED_BY_COHORT | USDJPY\|london\|bullish\|D1; USDJPY\|tokyo\|bullish\|D1 |
| Blocked dominance-watchlist controls | NO_POSITIVE_BLOCKED_CONTROL_SIGNAL | No blocked dominance-watchlist control had positive full-corpus mean R. |
| Post-hoc PBO diagnostic | WARNING_POSTHOC_PBO_ABOVE_0_4 | PBO=0.462413; diagnostic-only and not promotion-grade. |
| Promotion methodology | BLOCKED_BY_DESIGN | PBO=0.462413 and effective_N diagnostics exist but are not promotion-usable: Historical same-dataset effective_N diagnostic only. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Prospective or untouched replay lane for the five target cohorts | Family separation is strong enough to justify forward validation, not promotion. |
| 2 | Run blocked dominance-watchlist controls explicitly as controls | Checks whether NAS100/US30/XAU dominance names are broad-market artifacts. |
| 3 | Investigate 2026 underpowered target cells before live conclusions | Some target cohorts have too few recent resolved rows for standalone confidence. |
| 4 | Compare raw replay event funnel to live candidate funnel | Large NO_ENTRY and SETUP_NOT_REFINABLE counts need live-equivalence context. |

## Synthesis

- The GBPUSD negative control did drag the combined headline, but it is not the central story.
- The central story is that the five target cohorts remained positive as a family while the negative controls did not.
- Recency strengthens the family-level target/control split, but standalone 2026 power is uneven by individual target cohort.
- The result opens a prospective validation lane and blocked-control lane; it does not open a promotion lane.
