# Raw-OHLC Path Scaling V1 Failure Forensics

**Created UTC:** 2026-05-01T20:55:20.884438+00:00
**Event log:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\path_ablation_v1_mtf\raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl`
**Event log SHA256:** `cf3364825735c5858486b5c1e8678455748099250ee899b69a27379e469d38a0`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Scope:** `FULL_AVAILABLE_CORPUS_V1_EVENT_LOG`

## Boundary

- Research/tooling only
- No live trading logic changes
- No prompt edits
- No parameter optimization
- No paid AI/API calls
- No V2/V3 implementation

## Direct Answers

| question | answer |
| --- | --- |
| What exactly worked in V1? | The MTF measurement layer worked as infrastructure: for J46 it resolved 299 prior V0 same-bars and reduced J46 same-bars from 1045 to 713. The J46 exit itself also remained the best global resolved/stressed comparator. |
| What exactly did not work? | The fixed-R lock-only exit policies did not work as promotion candidates. Under the full-corpus headline treatment, best-lock-minus-J46=-0.022328; under samebar-pessimistic stress, best-lock-minus-J46=-0.155922. |
| Did V1 fail because there is no favorable path before failure? | No. J46 nonpositive outcomes still show meaningful favorable excursions: MFE>=1R rate=0.22771, MFE>=1.5R rate=0.140645, MFE>=2R rate=0.066136. |
| Did fixed-R lock-only beat J46 on paired resolved rows? | Only narrowly on common paired resolved rows, and only for PATH_LOCK_HALF_GAIN_V0, with mean_delta_lock_minus_J46=0.003043 over n=3884 paired resolved rows. That is diagnostic, not promotion evidence, because the full-corpus and same-bar stress treatments still favor J46. |
| Was the failure mostly execution? | No live execution was tested. The failure is research-layer exit logic: fixed-R locks did not robustly improve the same raw setup stream. |
| Was the failure mostly market structure or fixed-R logic? | V1 cannot test structure. What it does show is that fixed-R anchors are too blunt; any remaining path-scaling thesis must move to pre-registered structural levels. |
| Did lock-only truncate winners? | Yes. All lock variants show truncation where lock/BE stops exited below the J46 result. For PATH_LOCK_HALF_GAIN_V0, truncation_n=270 and truncation_lost_R=401.888178. |
| Did lock-only rescue enough J46 losers? | It rescued some nonpositive J46 outcomes, but not enough for the registered full-corpus decision metric. For PATH_LOCK_HALF_GAIN_V0, rescued_j46_nonpositive_n=220, while j46_better_n=270; samebar-pessimistic all-enabled best-lock-minus-J46=-0.155922. |
| Where did the path-scaling idea still look alive? | It looked alive only in the headline target-family treatment and lower-timeframe diagnostics, not as robust promotion evidence. Target conservative mean delta=-0.000653; target half-gain mean delta=-0.034521; target samebar-pessimistic best-lock-minus-J46=-0.077802. |
| Why did the aggressive early-BE idea fail? | It protected earlier but created too much path-order ambiguity and reward suppression: early-BE same_bar_n=1989 versus J46 same_bar_n=713, and early-BE gross_mean_r=0.145509 versus J46 gross_mean_r=0.213894. |

## What Worked

| item | evidence | interpretation |
| --- | --- | --- |
| MTF path-resolution infrastructure | J46 V0 same-bars=1045; resolved by MTF=299; remaining V1 same-bars=713. | This worked as a measurement improvement, not as a tradable edge. |
| J46-J49 comparator robustness | J46 stayed best globally under unresolved exclusion and samebar-pessimistic stress. | The delayed 3R-to-BE / 6R-target architecture preserved more right-tail payoff than fixed-R lock ladders. |
| Target-cohort lock hint under headline exclusion | Target best-lock-minus-J46=0.063597 under exclude_unresolved. | There is a real-looking local hint, but it is not promotion-grade because it fails stress handling. |
| M5 diagnostic subset | M5 conservative lock mean_delta_lock_minus_J46=0.017339. | Lower-timeframe coverage can expose useful path mechanics, but coverage skew blocks final inference. |

## What Failed

| item | evidence | interpretation |
| --- | --- | --- |
| Global fixed-R lock-only promotion | Best lock=PATH_LOCK_HALF_GAIN_V0; paired mean_delta_lock_minus_J46=0.003043; paired sum_delta=11.817627; full-corpus exclude_unresolved best-lock-minus-J46=-0.022328; samebar-pessimistic best-lock-minus-J46=-0.155922. | A small common-row gain did not survive the registered full-corpus treatment or conservative ordering stress. |
| Aggressive early protection | Early-BE same_bar_n=1989 versus J46 same_bar_n=713; early-BE gross_mean_r=0.145509 versus J46 gross_mean_r=0.213894. | Moving locks earlier increased ambiguous policy collisions and compressed payoff. |
| Target-cohort promotion robustness | Samebar-pessimistic target best-lock-minus-J46=-0.077802. | The best-looking local result is not reliable once unresolved ordering is treated conservatively. |
| Fixed-R abstraction | Forensic casebooks contain both true rescues and large winner truncations under the same static thresholds. | The same rule helps some trades and harms others because it ignores structural context. |

## Root Cause Summary

| cause | diagnosis | evidence |
| --- | --- | --- |
| Primary | Fixed-R lock-only is too blunt. | Half-gain is slightly positive on common resolved rows, but the registered full-corpus and samebar-pessimistic decision metrics still favor J46. |
| Secondary | Winner truncation is material. | Lock/BE stops frequently exit below J46 outcomes; large truncation appears in the top J46-better cohorts and casebook. |
| Secondary | Residual same-bar uncertainty is decision-critical for local target claims. | Target-family edge under unresolved exclusion flips negative under samebar-pessimistic stress. |
| Not supported | The market never offers favorable path movement. | J46 nonpositive rows still show substantial MFE beyond 1R/1.5R/2R thresholds. |
| Not tested | Structural-level path scaling or reentry. | V1 contains no structural lock selector, no reentry engine, and no composite risk accounting. |

## Variant Outcome Summary

| variant_id | event_rows | policy_event_rows | resolved_n | same_bar_n | no_entry_n | setup_not_refinable_n | lock_triggered_n | lock_then_stop_n | selected_M1_n | selected_M5_n | selected_M15_n | gross_mean_r | samebar_rate_over_policy_events | lock_trigger_rate_over_policy_events | lock_then_stop_rate_after_trigger | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | 23483 | 5193 | 3898 | 1295 | 7631 | 10652 | 0 | 0 | 774 | 4738 | 17971 | 0.206545 | 0.249374 | 0.0 |  | {'NO_ENTRY': 7631, 'SAME_BAR': 1295, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1888, 'TIMEOUT': 301, 'TP': 1716} |
| J46_J49_ONLY | 23483 | 5190 | 4477 | 713 | 7631 | 10652 | 442 | 28 | 774 | 4738 | 17971 | 0.213894 | 0.13738 | 0.085164 | 0.063348 | {'BE_STOP': 28, 'NO_ENTRY': 7631, 'SAME_BAR': 713, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1953, 'TIMEOUT': 2419, 'TP': 87} |
| PATH_LOCK_CONSERVATIVE_V0 | 23483 | 5193 | 3884 | 1309 | 7631 | 10652 | 1241 | 439 | 774 | 4738 | 17971 | 0.188345 | 0.25207 | 0.238976 | 0.353747 | {'BE_STOP': 216, 'LOCK_STOP': 223, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1965, 'TP': 41} |
| PATH_LOCK_HALF_GAIN_V0 | 23483 | 5193 | 3884 | 1309 | 7631 | 10652 | 1241 | 692 | 774 | 4738 | 17971 | 0.191565 | 0.25207 | 0.238976 | 0.557615 | {'LOCK_STOP': 692, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1722, 'TP': 31} |
| PATH_LOCK_EARLY_BE_V0 | 23483 | 5195 | 3206 | 1989 | 7631 | 10652 | 1525 | 792 | 774 | 4738 | 17971 | 0.145509 | 0.382868 | 0.293551 | 0.519344 | {'BE_STOP': 322, 'LOCK_STOP': 470, 'NO_ENTRY': 7631, 'SAME_BAR': 1989, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1057, 'TIMEOUT': 1343, 'TP': 19} |

## MTF Resolution Summary

| variant_id | v0_samebar_n | v1_samebar_n | v0_samebar_resolved_by_mtf_n | v0_samebar_still_unresolved_n | selected_M1_n | selected_M5_n | selected_M15_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | 1805 | 1295 | 469 | 1295 | 774 | 4738 | 17971 |
| J46_J49_ONLY | 1045 | 713 | 299 | 713 | 774 | 4738 | 17971 |
| PATH_LOCK_CONSERVATIVE_V0 | 1828 | 1309 | 478 | 1309 | 774 | 4738 | 17971 |
| PATH_LOCK_HALF_GAIN_V0 | 1828 | 1309 | 478 | 1309 | 774 | 4738 | 17971 |
| PATH_LOCK_EARLY_BE_V0 | 2598 | 1989 | 534 | 1989 | 774 | 4738 | 17971 |

## Same-Bar Stress Delta Summary

| treatment | group | j46_net_mean_r_cost_0.05 | j46_n | best_lock_variant | best_lock_net_mean_r_cost_0.05 | best_lock_n | best_lock_minus_j46 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | all_enabled | 0.163894 | 4477 | PATH_LOCK_HALF_GAIN_V0 | 0.141565 | 3884 | -0.022328 |
| exclude_unresolved | target_cohorts | 0.409292 | 1406 | PATH_LOCK_CONSERVATIVE_V0 | 0.472889 | 1270 | 0.063597 |
| exclude_unresolved | primary_controlled_family | 0.395481 | 674 | PATH_LOCK_CONSERVATIVE_V0 | 0.423483 | 596 | 0.028003 |
| exclude_unresolved | cleared_non_primary_targets | 0.422008 | 732 | PATH_LOCK_EARLY_BE_V0 | 0.584256 | 576 | 0.162247 |
| exclude_unresolved | negative_controls | -0.150354 | 1518 | PATH_LOCK_HALF_GAIN_V0 | -0.16443 | 1426 | -0.014076 |
| exclude_unresolved | blocked_dominance_controls | 0.248889 | 1553 | PATH_LOCK_HALF_GAIN_V0 | 0.190875 | 1188 | -0.058014 |
| samebar_breakeven | all_enabled | 0.134509 | 5190 | PATH_LOCK_HALF_GAIN_V0 | 0.093277 | 5193 | -0.041232 |
| samebar_breakeven | target_cohorts | 0.372344 | 1529 | PATH_LOCK_CONSERVATIVE_V0 | 0.384032 | 1530 | 0.011687 |
| samebar_breakeven | primary_controlled_family | 0.359065 | 734 | PATH_LOCK_CONSERVATIVE_V0 | 0.334463 | 734 | -0.024602 |
| samebar_breakeven | cleared_non_primary_targets | 0.384604 | 795 | PATH_LOCK_HALF_GAIN_V0 | 0.44659 | 796 | 0.061986 |
| samebar_breakeven | negative_controls | -0.137299 | 1745 | PATH_LOCK_HALF_GAIN_V0 | -0.143511 | 1745 | -0.006212 |
| samebar_breakeven | blocked_dominance_controls | 0.192262 | 1916 | PATH_LOCK_HALF_GAIN_V0 | 0.099197 | 1918 | -0.093065 |
| samebar_pessimistic | all_enabled | -0.002871 | 5190 | PATH_LOCK_HALF_GAIN_V0 | -0.158793 | 5193 | -0.155922 |
| samebar_pessimistic | target_cohorts | 0.291899 | 1529 | PATH_LOCK_CONSERVATIVE_V0 | 0.214097 | 1530 | -0.077802 |
| samebar_pessimistic | primary_controlled_family | 0.277322 | 734 | PATH_LOCK_CONSERVATIVE_V0 | 0.146452 | 734 | -0.130869 |
| samebar_pessimistic | cleared_non_primary_targets | 0.305359 | 795 | PATH_LOCK_HALF_GAIN_V0 | 0.293323 | 796 | -0.012035 |
| samebar_pessimistic | negative_controls | -0.267385 | 1745 | PATH_LOCK_HALF_GAIN_V0 | -0.326319 | 1745 | -0.058934 |
| samebar_pessimistic | blocked_dominance_controls | 0.002805 | 1916 | PATH_LOCK_HALF_GAIN_V0 | -0.281408 | 1918 | -0.284213 |

## Pairwise Variant Summary

| variant_id | scope | key | paired_resolved_n | j46_mean_r | lock_mean_r | mean_delta_lock_minus_j46 | sum_delta_lock_minus_j46 | lock_better_rate | j46_better_rate | lock_better_n | j46_better_n | tie_n | j46_positive_n | lock_positive_n | both_positive_n | both_nonpositive_n | lock_triggered_n | lock_triggered_rate | lock_triggered_positive_n | lock_triggered_nonpositive_n | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | large_truncation_n | rescued_j46_nonpositive_n | rescued_to_positive_n | lock_made_j46_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | all | all_enabled | 3884 | 0.188523 | 0.188345 | -0.000178 | -0.691343 | 0.064109 | 0.048919 | 249 | 190 | 3445 | 1846 | 1850 | 1754 | 1942 | 1241 | 0.319516 | 1025 | 216 | 190 | 252.654132 | 0.06505 | 33 | 220 | 96 | 92 |
| PATH_LOCK_HALF_GAIN_V0 | all | all_enabled | 3884 | 0.188523 | 0.191565 | 0.003043 | 11.817627 | 0.108651 | 0.069516 | 422 | 270 | 3192 | 1846 | 2066 | 1846 | 1818 | 1241 | 0.319516 | 1241 | 0 | 270 | 401.888178 | 0.103473 | 66 | 220 | 220 | 0 |
| PATH_LOCK_EARLY_BE_V0 | all | all_enabled | 3206 | 0.160074 | 0.145509 | -0.014565 | -46.696507 | 0.135683 | 0.111354 | 435 | 357 | 2414 | 1577 | 1547 | 1417 | 1499 | 1525 | 0.475671 | 1203 | 322 | 357 | 410.853847 | 0.128152 | 44 | 292 | 130 | 160 |

## Pairwise Group Summary

| variant_id | scope | key | paired_resolved_n | j46_mean_r | lock_mean_r | mean_delta_lock_minus_j46 | sum_delta_lock_minus_j46 | lock_better_rate | j46_better_rate | lock_better_n | j46_better_n | tie_n | j46_positive_n | lock_positive_n | both_positive_n | both_nonpositive_n | lock_triggered_n | lock_triggered_rate | lock_triggered_positive_n | lock_triggered_nonpositive_n | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | large_truncation_n | rescued_j46_nonpositive_n | rescued_to_positive_n | lock_made_j46_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | group | all_enabled | 3884 | 0.188523 | 0.188345 | -0.000178 | -0.691343 | 0.064109 | 0.048919 | 249 | 190 | 3445 | 1846 | 1850 | 1754 | 1942 | 1241 | 0.319516 | 1025 | 216 | 190 | 252.654132 | 0.06505 | 33 | 220 | 96 | 92 |
| PATH_LOCK_CONSERVATIVE_V0 | group | target_cohorts | 1270 | 0.523542 | 0.522889 | -0.000653 | -0.829405 | 0.079528 | 0.048031 | 101 | 61 | 1108 | 730 | 736 | 693 | 497 | 474 | 0.373228 | 387 | 87 | 61 | 111.031862 | 0.087427 | 13 | 93 | 43 | 37 |
| PATH_LOCK_CONSERVATIVE_V0 | group | primary_controlled_family | 596 | 0.469489 | 0.473483 | 0.003994 | 2.380594 | 0.04698 | 0.025168 | 28 | 15 | 553 | 356 | 356 | 344 | 228 | 188 | 0.315436 | 162 | 26 | 15 | 28.921668 | 0.048526 | 3 | 26 | 12 | 12 |
| PATH_LOCK_CONSERVATIVE_V0 | group | cleared_non_primary_targets | 674 | 0.571339 | 0.566576 | -0.004763 | -3.209999 | 0.108309 | 0.068249 | 73 | 46 | 555 | 374 | 380 | 349 | 269 | 286 | 0.424332 | 225 | 61 | 46 | 82.110194 | 0.121825 | 10 | 67 | 31 | 25 |
| PATH_LOCK_CONSERVATIVE_V0 | group | negative_controls | 1426 | -0.128175 | -0.119888 | 0.008287 | 11.817308 | 0.021739 | 0.02244 | 31 | 32 | 1363 | 565 | 565 | 564 | 860 | 292 | 0.204769 | 266 | 26 | 32 | 11.893446 | 0.00834 | 0 | 26 | 1 | 1 |
| PATH_LOCK_CONSERVATIVE_V0 | group | blocked_dominance_controls | 1188 | 0.210523 | 0.200692 | -0.009831 | -11.679246 | 0.098485 | 0.08165 | 117 | 97 | 974 | 551 | 549 | 497 | 585 | 475 | 0.399832 | 372 | 103 | 97 | 129.728824 | 0.109199 | 20 | 101 | 52 | 54 |
| PATH_LOCK_HALF_GAIN_V0 | group | all_enabled | 3884 | 0.188523 | 0.191565 | 0.003043 | 11.817627 | 0.108651 | 0.069516 | 422 | 270 | 3192 | 1846 | 2066 | 1846 | 1818 | 1241 | 0.319516 | 1241 | 0 | 270 | 401.888178 | 0.103473 | 66 | 220 | 220 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | group | target_cohorts | 1270 | 0.523542 | 0.489021 | -0.034521 | -43.841311 | 0.1 | 0.092913 | 127 | 118 | 1025 | 730 | 823 | 730 | 447 | 474 | 0.373228 | 474 | 0 | 118 | 206.425047 | 0.162539 | 43 | 93 | 93 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | group | primary_controlled_family | 596 | 0.469489 | 0.37881 | -0.090679 | -54.044428 | 0.068792 | 0.08557 | 41 | 51 | 504 | 356 | 382 | 356 | 214 | 188 | 0.315436 | 188 | 0 | 51 | 100.471238 | 0.168576 | 23 | 26 | 26 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | group | cleared_non_primary_targets | 674 | 0.571339 | 0.586477 | 0.015138 | 10.203117 | 0.127596 | 0.099407 | 86 | 67 | 521 | 374 | 441 | 374 | 233 | 286 | 0.424332 | 286 | 0 | 67 | 105.953809 | 0.157201 | 20 | 67 | 67 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | group | negative_controls | 1426 | -0.128175 | -0.11443 | 0.013745 | 19.600809 | 0.062412 | 0.040673 | 89 | 58 | 1279 | 565 | 591 | 565 | 835 | 292 | 0.204769 | 292 | 0 | 58 | 37.157055 | 0.026057 | 0 | 26 | 26 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | group | blocked_dominance_controls | 1188 | 0.210523 | 0.240875 | 0.030352 | 36.058129 | 0.173401 | 0.079125 | 206 | 94 | 888 | 551 | 652 | 551 | 536 | 475 | 0.399832 | 475 | 0 | 94 | 158.306076 | 0.133254 | 23 | 101 | 101 | 0 |
| PATH_LOCK_EARLY_BE_V0 | group | all_enabled | 3206 | 0.160074 | 0.145509 | -0.014565 | -46.696507 | 0.135683 | 0.111354 | 435 | 357 | 2414 | 1577 | 1547 | 1417 | 1499 | 1525 | 0.475671 | 1203 | 322 | 357 | 410.853847 | 0.128152 | 44 | 292 | 130 | 160 |
| PATH_LOCK_EARLY_BE_V0 | group | target_cohorts | 1113 | 0.583321 | 0.477437 | -0.105884 | -117.849112 | 0.119497 | 0.135669 | 133 | 151 | 829 | 681 | 683 | 639 | 388 | 644 | 0.578616 | 534 | 110 | 151 | 235.54197 | 0.211628 | 43 | 112 | 44 | 42 |
| PATH_LOCK_EARLY_BE_V0 | group | primary_controlled_family | 537 | 0.389672 | 0.309229 | -0.080444 | -43.198201 | 0.148976 | 0.10987 | 80 | 59 | 398 | 321 | 319 | 306 | 203 | 292 | 0.543762 | 223 | 69 | 59 | 106.644231 | 0.198593 | 23 | 67 | 13 | 15 |
| PATH_LOCK_EARLY_BE_V0 | group | cleared_non_primary_targets | 576 | 0.763858 | 0.634256 | -0.129602 | -74.650911 | 0.092014 | 0.159722 | 53 | 92 | 431 | 360 | 364 | 333 | 185 | 352 | 0.611111 | 311 | 41 | 92 | 128.897739 | 0.223781 | 20 | 45 | 31 | 27 |
| PATH_LOCK_EARLY_BE_V0 | group | negative_controls | 1229 | -0.160343 | -0.186156 | -0.025814 | -31.72496 | 0.068348 | 0.084622 | 84 | 104 | 1041 | 502 | 463 | 446 | 710 | 398 | 0.323841 | 318 | 80 | 104 | 92.291341 | 0.075095 | 0 | 41 | 17 | 56 |
| PATH_LOCK_EARLY_BE_V0 | group | blocked_dominance_controls | 864 | 0.070629 | 0.1897 | 0.119071 | 102.877565 | 0.252315 | 0.118056 | 218 | 102 | 544 | 394 | 401 | 332 | 401 | 483 | 0.559028 | 351 | 132 | 102 | 83.020536 | 0.096089 | 1 | 139 | 69 | 62 |

## Pairwise Timeframe Summary

| variant_id | scope | key | paired_resolved_n | j46_mean_r | lock_mean_r | mean_delta_lock_minus_j46 | sum_delta_lock_minus_j46 | lock_better_rate | j46_better_rate | lock_better_n | j46_better_n | tie_n | j46_positive_n | lock_positive_n | both_positive_n | both_nonpositive_n | lock_triggered_n | lock_triggered_rate | lock_triggered_positive_n | lock_triggered_nonpositive_n | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | large_truncation_n | rescued_j46_nonpositive_n | rescued_to_positive_n | lock_made_j46_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M1 | 390 | -0.022279 | 0.129565 | 0.151844 | 59.21907 | 0.138462 | 0.058974 | 54 | 23 | 313 | 163 | 187 | 161 | 201 | 158 | 0.405128 | 129 | 29 | 23 | 6.998996 | 0.017946 | 0 | 53 | 26 | 2 |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M5 | 1447 | 0.225674 | 0.243013 | 0.017339 | 25.089578 | 0.070491 | 0.044921 | 102 | 65 | 1280 | 680 | 686 | 641 | 722 | 499 | 0.344851 | 419 | 80 | 65 | 71.758991 | 0.049592 | 7 | 86 | 45 | 39 |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M15 | 2047 | 0.202423 | 0.160899 | -0.041524 | -84.999991 | 0.045432 | 0.049829 | 93 | 102 | 1852 | 1003 | 977 | 952 | 1019 | 584 | 0.285296 | 477 | 107 | 102 | 173.896145 | 0.084952 | 26 | 81 | 25 | 51 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M1 | 390 | -0.022279 | 0.191599 | 0.213878 | 83.412278 | 0.217949 | 0.076923 | 85 | 30 | 275 | 163 | 216 | 163 | 174 | 158 | 0.405128 | 158 | 0 | 30 | 20.221962 | 0.051851 | 0 | 53 | 53 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M5 | 1447 | 0.225674 | 0.222783 | -0.00289 | -4.182066 | 0.13407 | 0.050449 | 194 | 73 | 1180 | 680 | 766 | 680 | 681 | 499 | 0.344851 | 499 | 0 | 73 | 171.021468 | 0.11819 | 32 | 86 | 86 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M15 | 2047 | 0.202423 | 0.169491 | -0.032932 | -67.412585 | 0.069858 | 0.081583 | 143 | 167 | 1737 | 1003 | 1084 | 1003 | 963 | 584 | 0.285296 | 584 | 0 | 167 | 210.644748 | 0.102904 | 34 | 81 | 81 | 0 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M1 | 353 | -0.124145 | 0.078003 | 0.202149 | 71.358492 | 0.25779 | 0.107649 | 91 | 38 | 224 | 126 | 159 | 118 | 186 | 182 | 0.515581 | 136 | 46 | 38 | 26.2447 | 0.074348 | 0 | 79 | 41 | 8 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M5 | 1233 | 0.188638 | 0.224693 | 0.036054 | 44.454958 | 0.191403 | 0.081103 | 236 | 100 | 897 | 588 | 585 | 527 | 587 | 622 | 0.504461 | 475 | 147 | 100 | 138.016181 | 0.111935 | 23 | 144 | 58 | 61 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M15 | 1620 | 0.200266 | 0.099951 | -0.100315 | -162.509957 | 0.066667 | 0.135185 | 108 | 219 | 1293 | 863 | 803 | 772 | 726 | 721 | 0.445062 | 592 | 129 | 219 | 246.592966 | 0.152218 | 21 | 69 | 31 | 91 |

## Mechanism Group Summary

| variant_id | scope | key | paired_resolved_n | mean_delta_lock_minus_j46 | lock_rescued_loss_to_positive_n | lock_rescued_loss_to_positive_rate | lock_reduced_loss_only_n | lock_reduced_loss_only_rate | lock_failed_to_improve_j46_nonpositive_n | lock_failed_to_improve_j46_nonpositive_rate | winner_truncated_to_nonpositive_n | winner_truncated_to_nonpositive_rate | winner_truncated_but_positive_n | winner_truncated_but_positive_rate | lock_improved_positive_winner_n | lock_improved_positive_winner_rate | same_result_n | same_result_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | group | all_enabled | 3884 | -0.000178 | 96 | 0.024717 | 124 | 0.031926 | 0 | 0.0 | 92 | 0.023687 | 98 | 0.025232 | 29 | 0.007467 | 3445 | 0.886972 |
| PATH_LOCK_CONSERVATIVE_V0 | group | target_cohorts | 1270 | -0.000653 | 43 | 0.033858 | 50 | 0.03937 | 0 | 0.0 | 37 | 0.029134 | 24 | 0.018898 | 8 | 0.006299 | 1108 | 0.872441 |
| PATH_LOCK_CONSERVATIVE_V0 | group | primary_controlled_family | 596 | 0.003994 | 12 | 0.020134 | 14 | 0.02349 | 0 | 0.0 | 12 | 0.020134 | 3 | 0.005034 | 2 | 0.003356 | 553 | 0.927852 |
| PATH_LOCK_CONSERVATIVE_V0 | group | cleared_non_primary_targets | 674 | -0.004763 | 31 | 0.045994 | 36 | 0.053412 | 0 | 0.0 | 25 | 0.037092 | 21 | 0.031157 | 6 | 0.008902 | 555 | 0.823442 |
| PATH_LOCK_CONSERVATIVE_V0 | group | negative_controls | 1426 | 0.008287 | 1 | 0.000701 | 25 | 0.017532 | 0 | 0.0 | 1 | 0.000701 | 31 | 0.021739 | 5 | 0.003506 | 1363 | 0.95582 |
| PATH_LOCK_CONSERVATIVE_V0 | group | blocked_dominance_controls | 1188 | -0.009831 | 52 | 0.043771 | 49 | 0.041246 | 0 | 0.0 | 54 | 0.045455 | 43 | 0.036195 | 16 | 0.013468 | 974 | 0.819865 |
| PATH_LOCK_HALF_GAIN_V0 | group | all_enabled | 3884 | 0.003043 | 220 | 0.056643 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 270 | 0.069516 | 202 | 0.052008 | 3192 | 0.821833 |
| PATH_LOCK_HALF_GAIN_V0 | group | target_cohorts | 1270 | -0.034521 | 93 | 0.073228 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 118 | 0.092913 | 34 | 0.026772 | 1025 | 0.807087 |
| PATH_LOCK_HALF_GAIN_V0 | group | primary_controlled_family | 596 | -0.090679 | 26 | 0.043624 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 51 | 0.08557 | 15 | 0.025168 | 504 | 0.845638 |
| PATH_LOCK_HALF_GAIN_V0 | group | cleared_non_primary_targets | 674 | 0.015138 | 67 | 0.099407 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 67 | 0.099407 | 19 | 0.02819 | 521 | 0.772997 |
| PATH_LOCK_HALF_GAIN_V0 | group | negative_controls | 1426 | 0.013745 | 26 | 0.018233 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 58 | 0.040673 | 63 | 0.04418 | 1279 | 0.896914 |
| PATH_LOCK_HALF_GAIN_V0 | group | blocked_dominance_controls | 1188 | 0.030352 | 101 | 0.085017 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 94 | 0.079125 | 105 | 0.088384 | 888 | 0.747475 |
| PATH_LOCK_EARLY_BE_V0 | group | all_enabled | 3206 | -0.014565 | 130 | 0.040549 | 162 | 0.05053 | 0 | 0.0 | 160 | 0.049906 | 197 | 0.061447 | 143 | 0.044604 | 2414 | 0.752963 |
| PATH_LOCK_EARLY_BE_V0 | group | target_cohorts | 1113 | -0.105884 | 44 | 0.039533 | 68 | 0.061096 | 0 | 0.0 | 42 | 0.037736 | 109 | 0.097934 | 21 | 0.018868 | 829 | 0.744834 |
| PATH_LOCK_EARLY_BE_V0 | group | primary_controlled_family | 537 | -0.080444 | 13 | 0.024209 | 54 | 0.100559 | 0 | 0.0 | 15 | 0.027933 | 44 | 0.081937 | 13 | 0.024209 | 398 | 0.741155 |
| PATH_LOCK_EARLY_BE_V0 | group | cleared_non_primary_targets | 576 | -0.129602 | 31 | 0.053819 | 14 | 0.024306 | 0 | 0.0 | 27 | 0.046875 | 65 | 0.112847 | 8 | 0.013889 | 431 | 0.748264 |
| PATH_LOCK_EARLY_BE_V0 | group | negative_controls | 1229 | -0.025814 | 17 | 0.013832 | 24 | 0.019528 | 0 | 0.0 | 56 | 0.045566 | 48 | 0.039056 | 43 | 0.034988 | 1041 | 0.84703 |
| PATH_LOCK_EARLY_BE_V0 | group | blocked_dominance_controls | 864 | 0.119071 | 69 | 0.079861 | 70 | 0.081019 | 0 | 0.0 | 62 | 0.071759 | 40 | 0.046296 | 79 | 0.091435 | 544 | 0.62963 |

## Mechanism Timeframe Summary

| variant_id | scope | key | paired_resolved_n | mean_delta_lock_minus_j46 | lock_rescued_loss_to_positive_n | lock_rescued_loss_to_positive_rate | lock_reduced_loss_only_n | lock_reduced_loss_only_rate | lock_failed_to_improve_j46_nonpositive_n | lock_failed_to_improve_j46_nonpositive_rate | winner_truncated_to_nonpositive_n | winner_truncated_to_nonpositive_rate | winner_truncated_but_positive_n | winner_truncated_but_positive_rate | lock_improved_positive_winner_n | lock_improved_positive_winner_rate | same_result_n | same_result_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M1 | 390 | 0.151844 | 26 | 0.066667 | 27 | 0.069231 | 0 | 0.0 | 2 | 0.005128 | 21 | 0.053846 | 1 | 0.002564 | 313 | 0.802564 |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M5 | 1447 | 0.017339 | 45 | 0.031099 | 41 | 0.028334 | 0 | 0.0 | 39 | 0.026952 | 26 | 0.017968 | 16 | 0.011057 | 1280 | 0.884589 |
| PATH_LOCK_CONSERVATIVE_V0 | timeframe | M15 | 2047 | -0.041524 | 25 | 0.012213 | 56 | 0.027357 | 0 | 0.0 | 51 | 0.024915 | 51 | 0.024915 | 12 | 0.005862 | 1852 | 0.904739 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M1 | 390 | 0.213878 | 53 | 0.135897 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 30 | 0.076923 | 32 | 0.082051 | 275 | 0.705128 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M5 | 1447 | -0.00289 | 86 | 0.059433 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 73 | 0.050449 | 108 | 0.074637 | 1180 | 0.81548 |
| PATH_LOCK_HALF_GAIN_V0 | timeframe | M15 | 2047 | -0.032932 | 81 | 0.03957 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 167 | 0.081583 | 62 | 0.030288 | 1737 | 0.848559 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M1 | 353 | 0.202149 | 41 | 0.116147 | 38 | 0.107649 | 0 | 0.0 | 8 | 0.022663 | 30 | 0.084986 | 12 | 0.033994 | 224 | 0.634561 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M5 | 1233 | 0.036054 | 58 | 0.04704 | 86 | 0.069749 | 0 | 0.0 | 61 | 0.049473 | 39 | 0.03163 | 92 | 0.074615 | 897 | 0.727494 |
| PATH_LOCK_EARLY_BE_V0 | timeframe | M15 | 1620 | -0.100315 | 31 | 0.019136 | 38 | 0.023457 | 0 | 0.0 | 91 | 0.056173 | 128 | 0.079012 | 39 | 0.024074 | 1293 | 0.798148 |

## Top J46 Better Cohorts

| variant_id | scope | key | paired_resolved_n | j46_mean_r | lock_mean_r | mean_delta_lock_minus_j46 | sum_delta_lock_minus_j46 | lock_better_rate | j46_better_rate | lock_better_n | j46_better_n | tie_n | j46_positive_n | lock_positive_n | both_positive_n | both_nonpositive_n | lock_triggered_n | lock_triggered_rate | lock_triggered_positive_n | lock_triggered_nonpositive_n | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | large_truncation_n | rescued_j46_nonpositive_n | rescued_to_positive_n | lock_made_j46_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_HALF_GAIN_V0 | cohort | USDJPY\|tokyo\|bearish\|D1\|primary_controlled_child | 202 | 0.999704 | 0.516471 | -0.483233 | -97.613098 | 0.019802 | 0.252475 | 4 | 51 | 147 | 144 | 145 | 144 | 57 | 89 | 0.440594 | 89 | 0 | 51 | 100.471238 | 0.497382 | 23 | 1 | 1 | 0 |
| PATH_LOCK_EARLY_BE_V0 | cohort | USDJPY\|london\|bearish\|D1\|cleared_non_primary_strong_lead | 124 | 1.43902 | 0.66635 | -0.772671 | -95.81116 | 0.0 | 0.379032 | 0 | 47 | 77 | 93 | 87 | 87 | 31 | 89 | 0.717742 | 83 | 6 | 47 | 95.81116 | 0.772671 | 20 | 0 | 0 | 6 |
| PATH_LOCK_EARLY_BE_V0 | cohort | USDJPY\|tokyo\|bearish\|D1\|primary_controlled_child | 190 | 1.001558 | 0.502995 | -0.498564 | -94.72711 | 0.036842 | 0.242105 | 7 | 46 | 137 | 135 | 134 | 133 | 54 | 107 | 0.563158 | 100 | 7 | 46 | 100.427346 | 0.528565 | 23 | 6 | 1 | 2 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | USDJPY\|london\|bearish\|D1\|cleared_non_primary_strong_lead | 139 | 1.260466 | 0.641204 | -0.619262 | -86.077378 | 0.079137 | 0.294964 | 11 | 41 | 87 | 98 | 98 | 98 | 41 | 81 | 0.582734 | 81 | 0 | 41 | 90.282108 | 0.649512 | 20 | 0 | 0 | 0 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | USDJPY\|london\|bearish\|D1\|cleared_non_primary_strong_lead | 139 | 1.260466 | 0.745596 | -0.514869 | -71.566815 | 0.043165 | 0.251799 | 6 | 35 | 98 | 98 | 78 | 78 | 41 | 81 | 0.582734 | 61 | 20 | 35 | 72.037763 | 0.518257 | 10 | 0 | 0 | 20 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | USDJPY\|tokyo\|bearish\|D1\|primary_controlled_child | 202 | 0.999704 | 0.862474 | -0.13723 | -27.72055 | 0.014851 | 0.074257 | 3 | 15 | 184 | 144 | 132 | 132 | 58 | 89 | 0.440594 | 76 | 13 | 15 | 28.921668 | 0.143177 | 3 | 1 | 0 | 12 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | XAUUSD\|ny\|bullish\|D1\|dominance_watchlist | 448 | 0.44123 | 0.40304 | -0.03819 | -17.109341 | 0.095982 | 0.053571 | 43 | 24 | 381 | 246 | 247 | 243 | 198 | 154 | 0.34375 | 127 | 27 | 24 | 52.919291 | 0.118123 | 8 | 28 | 4 | 3 |
| PATH_LOCK_EARLY_BE_V0 | cohort | USDJPY\|london\|bullish\|D1\|negative_control | 280 | 0.040586 | -0.013847 | -0.054434 | -15.241421 | 0.078571 | 0.157143 | 22 | 44 | 214 | 146 | 126 | 119 | 127 | 120 | 0.428571 | 88 | 32 | 44 | 33.493696 | 0.11962 | 0 | 12 | 7 | 27 |
| PATH_LOCK_EARLY_BE_V0 | cohort | GBPUSD\|london\|bearish\|H4+H1_consensus\|negative_control | 579 | -0.276489 | -0.290967 | -0.014478 | -8.382482 | 0.058722 | 0.041451 | 34 | 24 | 521 | 187 | 171 | 170 | 391 | 150 | 0.259067 | 122 | 28 | 24 | 28.320648 | 0.048913 | 0 | 12 | 1 | 17 |
| PATH_LOCK_EARLY_BE_V0 | cohort | USDJPY\|tokyo\|bullish\|D1\|negative_control | 370 | -0.130644 | -0.152539 | -0.021895 | -8.101057 | 0.075676 | 0.097297 | 28 | 36 | 306 | 169 | 166 | 157 | 192 | 128 | 0.345946 | 108 | 20 | 36 | 30.476997 | 0.08237 | 0 | 17 | 9 | 12 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | USDJPY\|tokyo\|bullish\|D1\|negative_control | 424 | -0.20445 | -0.213731 | -0.009281 | -3.935335 | 0.056604 | 0.058962 | 24 | 25 | 375 | 173 | 186 | 173 | 238 | 69 | 0.162736 | 69 | 0 | 25 | 24.311275 | 0.057338 | 0 | 13 | 13 | 0 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | NAS100\|ny\|bullish\|D1\|dominance_watchlist | 571 | 0.079474 | 0.076533 | -0.002941 | -1.679427 | 0.110333 | 0.10683 | 63 | 61 | 447 | 233 | 225 | 188 | 301 | 240 | 0.420315 | 170 | 70 | 61 | 67.419055 | 0.118072 | 12 | 62 | 37 | 45 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | GBPUSD\|london\|bearish\|H4+H1_consensus\|negative_control | 670 | -0.134851 | -0.13533 | -0.000478 | -0.320447 | 0.013433 | 0.034328 | 9 | 23 | 638 | 229 | 228 | 228 | 441 | 133 | 0.198507 | 128 | 5 | 23 | 4.395058 | 0.00656 | 0 | 4 | 0 | 1 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | USDJPY\|london\|bullish\|D1\|negative_control | 332 | -0.01729 | -0.005567 | 0.011723 | 3.892084 | 0.027108 | 0.009036 | 9 | 3 | 320 | 163 | 163 | 163 | 169 | 90 | 0.271084 | 81 | 9 | 3 | 5.107916 | 0.015385 | 0 | 9 | 0 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | USDJPY\|london\|bullish\|D1\|negative_control | 332 | -0.01729 | -0.005241 | 0.012049 | 4.000295 | 0.057229 | 0.078313 | 19 | 26 | 287 | 163 | 172 | 163 | 160 | 90 | 0.271084 | 90 | 0 | 26 | 12.25198 | 0.036904 | 0 | 9 | 9 | 0 |

## Top Lock Better Cohorts

| variant_id | scope | key | paired_resolved_n | j46_mean_r | lock_mean_r | mean_delta_lock_minus_j46 | sum_delta_lock_minus_j46 | lock_better_rate | j46_better_rate | lock_better_n | j46_better_n | tie_n | j46_positive_n | lock_positive_n | both_positive_n | both_nonpositive_n | lock_triggered_n | lock_triggered_rate | lock_triggered_positive_n | lock_triggered_nonpositive_n | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | large_truncation_n | rescued_j46_nonpositive_n | rescued_to_positive_n | lock_made_j46_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_HALF_GAIN_V0 | cohort | USDJPY\|tokyo\|bearish\|H4+H1_consensus\|cleared_non_primary_strong_lead | 231 | 0.113259 | 0.43174 | 0.318481 | 73.569102 | 0.207792 | 0.030303 | 48 | 7 | 176 | 91 | 139 | 91 | 92 | 90 | 0.38961 | 90 | 0 | 7 | 4.430898 | 0.019181 | 0 | 48 | 48 | 0 |
| PATH_LOCK_EARLY_BE_V0 | cohort | GBPJPY\|tokyo\|bullish\|D1\|primary_controlled_child | 347 | 0.054634 | 0.203132 | 0.148498 | 51.528909 | 0.210375 | 0.037464 | 73 | 13 | 261 | 186 | 185 | 173 | 149 | 185 | 0.533141 | 123 | 62 | 13 | 6.216885 | 0.017916 | 0 | 61 | 12 | 13 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | USDJPY\|tokyo\|bearish\|H4+H1_consensus\|cleared_non_primary_strong_lead | 231 | 0.113259 | 0.323121 | 0.209862 | 48.478149 | 0.207792 | 0.021645 | 48 | 5 | 178 | 91 | 98 | 86 | 128 | 90 | 0.38961 | 49 | 41 | 5 | 5.521851 | 0.023904 | 0 | 48 | 12 | 5 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | GBPJPY\|tokyo\|bullish\|D1\|primary_controlled_child | 394 | 0.197653 | 0.308233 | 0.11058 | 43.56867 | 0.093909 | 0.0 | 37 | 0 | 357 | 212 | 237 | 212 | 157 | 99 | 0.251269 | 99 | 0 | 0 | 0.0 | 0.0 | 0 | 25 | 25 | 0 |
| PATH_LOCK_EARLY_BE_V0 | cohort | XAUUSD\|ny\|bullish\|D1\|dominance_watchlist | 308 | 0.330835 | 0.460777 | 0.129942 | 40.022062 | 0.201299 | 0.077922 | 62 | 24 | 222 | 170 | 178 | 158 | 118 | 176 | 0.571429 | 145 | 31 | 24 | 10.990579 | 0.035684 | 0 | 39 | 20 | 12 |
| PATH_LOCK_EARLY_BE_V0 | cohort | NAS100\|ny\|bullish\|D1\|dominance_watchlist | 423 | -0.079254 | 0.014595 | 0.093849 | 39.698035 | 0.255319 | 0.137116 | 108 | 58 | 257 | 169 | 165 | 127 | 216 | 226 | 0.534279 | 150 | 76 | 58 | 51.185942 | 0.121007 | 1 | 72 | 38 | 42 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | GBPJPY\|tokyo\|bullish\|D1\|primary_controlled_child | 394 | 0.197653 | 0.274052 | 0.076399 | 30.101144 | 0.063452 | 0.0 | 25 | 0 | 369 | 212 | 224 | 212 | 170 | 99 | 0.251269 | 86 | 13 | 0 | 0.0 | 0.0 | 0 | 25 | 12 | 0 |
| PATH_LOCK_EARLY_BE_V0 | cohort | US30_cash\|ny\|bullish\|H4+H1_consensus\|dominance_watchlist | 133 | -0.055262 | 0.118855 | 0.174116 | 23.157468 | 0.360902 | 0.150376 | 48 | 20 | 65 | 55 | 58 | 47 | 67 | 81 | 0.609023 | 56 | 25 | 20 | 20.844015 | 0.156722 | 0 | 28 | 11 | 8 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | XAGUSD\|london\|bullish\|D1\|cleared_non_primary_strong_lead | 304 | 0.604325 | 0.679033 | 0.074709 | 22.711393 | 0.088816 | 0.0625 | 27 | 19 | 258 | 185 | 204 | 185 | 100 | 115 | 0.378289 | 115 | 0 | 19 | 11.240803 | 0.036976 | 0 | 19 | 19 | 0 |
| PATH_LOCK_CONSERVATIVE_V0 | cohort | XAGUSD\|london\|bullish\|D1\|cleared_non_primary_strong_lead | 304 | 0.604325 | 0.669715 | 0.06539 | 19.878667 | 0.0625 | 0.019737 | 19 | 6 | 279 | 185 | 204 | 185 | 100 | 115 | 0.378289 | 115 | 0 | 6 | 4.55058 | 0.014969 | 0 | 19 | 19 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | GBPUSD\|london\|bearish\|H4+H1_consensus\|negative_control | 670 | -0.134851 | -0.105693 | 0.029158 | 19.535849 | 0.068657 | 0.010448 | 46 | 7 | 617 | 229 | 233 | 229 | 437 | 133 | 0.198507 | 133 | 0 | 7 | 0.5938 | 0.000886 | 0 | 4 | 4 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | NAS100\|ny\|bullish\|D1\|dominance_watchlist | 571 | 0.079474 | 0.109613 | 0.030139 | 17.209322 | 0.204904 | 0.084063 | 117 | 48 | 406 | 233 | 295 | 233 | 276 | 240 | 0.420315 | 240 | 0 | 48 | 89.721226 | 0.15713 | 13 | 62 | 62 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | cohort | US30_cash\|ny\|bullish\|H4+H1_consensus\|dominance_watchlist | 169 | 0.04172 | 0.119986 | 0.078267 | 13.227053 | 0.195266 | 0.142012 | 33 | 24 | 112 | 72 | 83 | 72 | 86 | 81 | 0.47929 | 81 | 0 | 24 | 14.312772 | 0.084691 | 0 | 11 | 11 | 0 |
| PATH_LOCK_EARLY_BE_V0 | cohort | USDJPY\|tokyo\|bearish\|H4+H1_consensus\|cleared_non_primary_strong_lead | 174 | 0.391991 | 0.460609 | 0.068618 | 11.93951 | 0.137931 | 0.045977 | 24 | 8 | 142 | 88 | 99 | 87 | 74 | 87 | 0.5 | 74 | 13 | 8 | 6.355122 | 0.036524 | 0 | 24 | 12 | 1 |
| PATH_LOCK_EARLY_BE_V0 | cohort | XAGUSD\|london\|bullish\|D1\|cleared_non_primary_strong_lead | 278 | 0.695458 | 0.728626 | 0.033168 | 9.220739 | 0.104317 | 0.133094 | 29 | 37 | 212 | 179 | 178 | 159 | 80 | 176 | 0.633094 | 154 | 22 | 37 | 26.731457 | 0.096156 | 0 | 21 | 19 | 20 |

## Unresolved Pair Summary

| variant_id | both_samebar | j46_resolved_lock_samebar | j46_resolved_lock_samebar_j46_r_bucket__0_to_1R | j46_resolved_lock_samebar_j46_r_bucket__1_to_3R | j46_resolved_lock_samebar_j46_r_bucket__ge_3R | j46_resolved_lock_samebar_j46_r_bucket__le_-1R | j46_resolved_lock_samebar_j46_r_bucket__le_0R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | 713 | 593 | 77 | 81 | 84 | 325 | 26 |
| PATH_LOCK_HALF_GAIN_V0 | 713 | 593 | 77 | 81 | 84 | 325 | 26 |
| PATH_LOCK_EARLY_BE_V0 | 713 | 1271 | 139 | 221 | 151 | 689 | 71 |

## Outcome Transition Summary

| variant_id | j46_outcome | lock_outcome | count |
| --- | --- | --- | --- |
| PATH_LOCK_CONSERVATIVE_V0 | SETUP_NOT_REFINABLE | SETUP_NOT_REFINABLE | 10652 |
| PATH_LOCK_CONSERVATIVE_V0 | NO_ENTRY | NO_ENTRY | 7631 |
| PATH_LOCK_CONSERVATIVE_V0 | TIMEOUT | TIMEOUT | 1965 |
| PATH_LOCK_CONSERVATIVE_V0 | SL | SL | 1446 |
| PATH_LOCK_CONSERVATIVE_V0 | SAME_BAR | SAME_BAR | 713 |
| PATH_LOCK_CONSERVATIVE_V0 | SL | SAME_BAR | 325 |
| PATH_LOCK_CONSERVATIVE_V0 | TIMEOUT | SAME_BAR | 223 |
| PATH_LOCK_CONSERVATIVE_V0 | TIMEOUT | LOCK_STOP | 129 |
| PATH_LOCK_CONSERVATIVE_V0 | SL | BE_STOP | 114 |
| PATH_LOCK_CONSERVATIVE_V0 | TIMEOUT | BE_STOP | 102 |
| PATH_LOCK_CONSERVATIVE_V0 | SL | LOCK_STOP | 68 |
| PATH_LOCK_CONSERVATIVE_V0 | TP | TP | 41 |
| PATH_LOCK_CONSERVATIVE_V0 | TP | SAME_BAR | 26 |
| PATH_LOCK_CONSERVATIVE_V0 | BE_STOP | SAME_BAR | 22 |
| PATH_LOCK_CONSERVATIVE_V0 | TP | LOCK_STOP | 20 |
| PATH_LOCK_CONSERVATIVE_V0 | BE_STOP | LOCK_STOP | 6 |
| PATH_LOCK_HALF_GAIN_V0 | SETUP_NOT_REFINABLE | SETUP_NOT_REFINABLE | 10652 |
| PATH_LOCK_HALF_GAIN_V0 | NO_ENTRY | NO_ENTRY | 7631 |
| PATH_LOCK_HALF_GAIN_V0 | TIMEOUT | TIMEOUT | 1722 |
| PATH_LOCK_HALF_GAIN_V0 | SL | SL | 1446 |
| PATH_LOCK_HALF_GAIN_V0 | SAME_BAR | SAME_BAR | 713 |
| PATH_LOCK_HALF_GAIN_V0 | TIMEOUT | LOCK_STOP | 474 |
| PATH_LOCK_HALF_GAIN_V0 | SL | SAME_BAR | 325 |
| PATH_LOCK_HALF_GAIN_V0 | TIMEOUT | SAME_BAR | 223 |
| PATH_LOCK_HALF_GAIN_V0 | SL | LOCK_STOP | 182 |
| PATH_LOCK_HALF_GAIN_V0 | TP | TP | 31 |
| PATH_LOCK_HALF_GAIN_V0 | TP | LOCK_STOP | 30 |
| PATH_LOCK_HALF_GAIN_V0 | TP | SAME_BAR | 26 |
| PATH_LOCK_HALF_GAIN_V0 | BE_STOP | SAME_BAR | 22 |
| PATH_LOCK_HALF_GAIN_V0 | BE_STOP | LOCK_STOP | 6 |
| PATH_LOCK_EARLY_BE_V0 | SETUP_NOT_REFINABLE | SETUP_NOT_REFINABLE | 10652 |
| PATH_LOCK_EARLY_BE_V0 | NO_ENTRY | NO_ENTRY | 7631 |
| PATH_LOCK_EARLY_BE_V0 | TIMEOUT | TIMEOUT | 1343 |
| PATH_LOCK_EARLY_BE_V0 | SL | SL | 1057 |
| PATH_LOCK_EARLY_BE_V0 | SAME_BAR | SAME_BAR | 713 |
| PATH_LOCK_EARLY_BE_V0 | SL | SAME_BAR | 689 |
| PATH_LOCK_EARLY_BE_V0 | TIMEOUT | SAME_BAR | 518 |
| PATH_LOCK_EARLY_BE_V0 | TIMEOUT | LOCK_STOP | 346 |
| PATH_LOCK_EARLY_BE_V0 | TIMEOUT | BE_STOP | 212 |
| PATH_LOCK_EARLY_BE_V0 | SL | BE_STOP | 110 |
| PATH_LOCK_EARLY_BE_V0 | SL | LOCK_STOP | 97 |
| PATH_LOCK_EARLY_BE_V0 | TP | SAME_BAR | 47 |
| PATH_LOCK_EARLY_BE_V0 | BE_STOP | SAME_BAR | 22 |
| PATH_LOCK_EARLY_BE_V0 | TP | LOCK_STOP | 21 |
| PATH_LOCK_EARLY_BE_V0 | TP | TP | 19 |
| PATH_LOCK_EARLY_BE_V0 | BE_STOP | LOCK_STOP | 6 |

## MFE Opportunity Summary

| scope | key | j46_resolved_n | j46_nonpositive_n | j46_positive_n | nonpositive_mfe_avg | nonpositive_mfe_p50 | nonpositive_mfe_p75 | nonpositive_mfe_ge_1_n | nonpositive_mfe_ge_1_rate | nonpositive_mfe_ge_1.5_n | nonpositive_mfe_ge_1.5_rate | nonpositive_mfe_ge_2_n | nonpositive_mfe_ge_2_rate | nonpositive_mfe_ge_3_n | nonpositive_mfe_ge_3_rate | nonpositive_mfe_ge_6_n | nonpositive_mfe_ge_6_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group | all_enabled | 4477 | 2389 | 2088 | 0.65403 | 0.479793 | 0.916273 | 544 | 0.22771 | 336 | 0.140645 | 158 | 0.066136 | 31 | 0.012976 | 0 | 0.0 |
| group | target_cohorts | 1406 | 619 | 787 | 0.763581 | 0.616384 | 1.087653 | 181 | 0.292407 | 120 | 0.193861 | 57 | 0.092084 | 0 | 0.0 | 0 | 0.0 |
| group | primary_controlled_family | 674 | 269 | 405 | 0.765782 | 0.671456 | 1.080482 | 85 | 0.315985 | 38 | 0.141264 | 12 | 0.04461 | 0 | 0.0 | 0 | 0.0 |
| group | cleared_non_primary_targets | 732 | 350 | 382 | 0.76189 | 0.561867 | 1.195347 | 96 | 0.274286 | 82 | 0.234286 | 45 | 0.128571 | 0 | 0.0 | 0 | 0.0 |
| group | negative_controls | 1518 | 895 | 623 | 0.368094 | 0.268624 | 0.593746 | 61 | 0.068156 | 41 | 0.04581 | 10 | 0.011173 | 7 | 0.007821 | 0 | 0.0 |
| group | blocked_dominance_controls | 1553 | 875 | 678 | 0.869001 | 0.662503 | 1.246632 | 302 | 0.345143 | 175 | 0.2 | 91 | 0.104 | 24 | 0.027429 | 0 | 0.0 |
| timeframe | M1 | 402 | 239 | 163 | 0.858983 | 0.718429 | 1.685261 | 91 | 0.380753 | 65 | 0.271967 | 26 | 0.108787 | 0 | 0.0 | 0 | 0.0 |
| timeframe | M5 | 1643 | 875 | 768 | 0.677404 | 0.47995 | 0.913801 | 211 | 0.241143 | 121 | 0.138286 | 68 | 0.077714 | 20 | 0.022857 | 0 | 0.0 |
| timeframe | M15 | 2432 | 1275 | 1157 | 0.59957 | 0.464542 | 0.791241 | 242 | 0.189804 | 150 | 0.117647 | 64 | 0.050196 | 11 | 0.008627 | 0 | 0.0 |
| cohort | GBPJPY\|tokyo\|bullish\|D1\|primary_controlled_child | 455 | 206 | 249 | 0.884813 | 0.724452 | 1.20219 | 78 | 0.378641 | 37 | 0.179612 | 12 | 0.058252 | 0 | 0.0 | 0 | 0.0 |
| cohort | GBPUSD\|london\|bearish\|H4+H1_consensus\|negative_control | 715 | 466 | 249 | 0.282949 | 0.175149 | 0.479716 | 23 | 0.049356 | 11 | 0.023605 | 7 | 0.015021 | 7 | 0.015021 | 0 | 0.0 |
| cohort | NAS100\|ny\|bullish\|D1\|dominance_watchlist | 775 | 453 | 322 | 0.805262 | 0.48297 | 1.061109 | 114 | 0.251656 | 82 | 0.181015 | 57 | 0.125828 | 19 | 0.041943 | 0 | 0.0 |
| cohort | US30_cash\|ny\|bullish\|H4+H1_consensus\|dominance_watchlist | 298 | 189 | 109 | 1.074947 | 0.870198 | 1.546207 | 92 | 0.486772 | 50 | 0.26455 | 24 | 0.126984 | 1 | 0.005291 | 0 | 0.0 |
| cohort | USDJPY\|london\|bearish\|D1\|cleared_non_primary_strong_lead | 149 | 51 | 98 | 0.384142 | 0.555919 | 0.618521 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 |
| cohort | USDJPY\|london\|bullish\|D1\|negative_control | 346 | 169 | 177 | 0.471163 | 0.475188 | 0.622665 | 17 | 0.100592 | 9 | 0.053254 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 |
| cohort | USDJPY\|tokyo\|bearish\|D1\|primary_controlled_child | 219 | 63 | 156 | 0.376569 | 0.204932 | 0.666678 | 7 | 0.111111 | 1 | 0.015873 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 |
| cohort | USDJPY\|tokyo\|bearish\|H4+H1_consensus\|cleared_non_primary_strong_lead | 257 | 162 | 95 | 0.878467 | 0.649783 | 1.602647 | 61 | 0.376543 | 49 | 0.302469 | 12 | 0.074074 | 0 | 0.0 | 0 | 0.0 |
| cohort | USDJPY\|tokyo\|bullish\|D1\|negative_control | 457 | 260 | 197 | 0.453706 | 0.40114 | 0.594319 | 21 | 0.080769 | 21 | 0.080769 | 3 | 0.011538 | 0 | 0.0 | 0 | 0.0 |
| cohort | XAGUSD\|london\|bullish\|D1\|cleared_non_primary_strong_lead | 326 | 137 | 189 | 0.764661 | 0.499897 | 1.122391 | 35 | 0.255474 | 33 | 0.240876 | 33 | 0.240876 | 0 | 0.0 | 0 | 0.0 |
| cohort | XAUUSD\|ny\|bullish\|D1\|dominance_watchlist | 480 | 233 | 247 | 0.825869 | 0.634746 | 1.335699 | 96 | 0.412017 | 43 | 0.184549 | 10 | 0.042918 | 4 | 0.017167 | 0 | 0.0 |

## Casebook

### Largest J46 Better Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | delta_lock_minus_j46 | mfe_r | mae_r | max_locked_floor_r | lock_steps | bars_in_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2025-04-03T14:00:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.071864 | -0.109135 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T14:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.111093 | -0.10984 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T14:30:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.105418 | -0.109738 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T14:45:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.061464 | -0.108948 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T15:00:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.061464 | -0.108948 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T15:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.188026 | -0.111223 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T15:30:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 7.170518 | -0.107174 | 0.5 | 1.5->0.0;2.0->0.5 | 1 |
| XAUUSD\|2025-04-03T15:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.904423 | -0.103197 | 0.5 | 1.5->0.5 | 1 |
| XAUUSD\|2025-04-03T16:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M5 | TP | 6.0 | LOCK_STOP | 0.5 | -5.5 | 6.904423 | -0.103197 | 0.5 | 1.5->0.5 | 1 |
| USDJPY\|2022-11-30T00:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T00:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T00:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T00:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T00:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T00:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T01:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T01:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.232458 | -0.176451 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T01:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.313177 | -0.178736 | 1.0 | 1.5->0.0;2.0->0.5;3.0->1.0 | 12 |
| USDJPY\|2022-11-30T01:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.278378 | -0.177751 | 1.0 | 1.5->0.5;2.0->1.0 | 12 |
| USDJPY\|2022-11-30T01:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | M15 | TP | 6.0 | LOCK_STOP | 1.0 | -5.0 | 6.278378 | -0.177751 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 12 |

### Largest Lock Better Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | delta_lock_minus_j46 | mfe_r | mae_r | max_locked_floor_r | lock_steps | bars_in_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAS100\|2023-04-11T13:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.203967 | -1.185279 | 1.0 | 1.5->0.5;2.0->1.0 | 6 |
| NAS100\|2023-04-11T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.203967 | -1.185279 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 6 |
| NAS100\|2023-06-13T13:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.725342 | -1.377054 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.725342 | -1.377054 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.690872 | -1.367009 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.690872 | -1.367009 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.653202 | -1.356031 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.653202 | -1.356031 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| US30_cash\|2023-06-16T15:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.724809 | -1.025161 | 1.0 | 1.5->0.5;2.0->1.0 | 2 |
| US30_cash\|2023-06-16T15:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.724809 | -1.025161 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 2 |
| USDJPY\|2023-07-19T00:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T00:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T00:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.460195 | -1.550866 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.518715 | -1.009631 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.49535 | -1.000266 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.453183 | -1.546446 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.453183 | -1.546446 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.481343 | -1.564197 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.481081 | -1.564032 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |

### Winner Truncated To Nonpositive Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | delta_lock_minus_j46 | mfe_r | mae_r | max_locked_floor_r | lock_steps | bars_in_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2022-02-16T14:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.466349 | BE_STOP | 0.0 | -4.466349 | 5.722215 | -0.670425 | 0.0 | 1.5->0.0 | 4 |
| NAS100\|2023-07-06T15:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 3.672569 | BE_STOP | 0.0 | -3.672569 | 3.878893 | -0.358393 | 0.0 | 1.5->0.0 | 3 |
| NAS100\|2023-07-06T15:30:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 3.670566 | BE_STOP | 0.0 | -3.670566 | 3.876777 | -0.358197 | 0.0 | 1.5->0.0 | 3 |
| NAS100\|2023-07-06T15:00:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 3.642406 | BE_STOP | 0.0 | -3.642406 | 3.847035 | -0.355449 | 0.0 | 1.5->0.0 | 3 |
| NAS100\|2023-07-06T15:45:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 3.575477 | BE_STOP | 0.0 | -3.575477 | 3.776346 | -0.348918 | 0.0 | 1.5->0.0 | 3 |
| NAS100\|2023-07-06T16:00:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 3.549775 | BE_STOP | 0.0 | -3.549775 | 3.749201 | -0.34641 | 0.0 | 1.5->0.0 | 3 |
| NAS100\|2023-06-28T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 2.867803 | BE_STOP | 0.0 | -2.867803 | 3.173186 | -0.764157 | 0.0 | 1.0->0.0 | 10 |
| NAS100\|2023-06-28T13:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 2.862441 | BE_STOP | 0.0 | -2.862441 | 3.167253 | -0.762728 | 0.0 | 1.0->0.0 | 10 |
| GBPUSD\|2023-02-06T08:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.444083 | BE_STOP | 0.0 | -2.444083 | 2.452216 | -0.122001 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T09:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.444083 | BE_STOP | 0.0 | -2.444083 | 2.452216 | -0.122001 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T07:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.441105 | BE_STOP | 0.0 | -2.441105 | 2.449228 | -0.121852 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T08:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.440114 | BE_STOP | 0.0 | -2.440114 | 2.448234 | -0.121803 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T08:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.440114 | BE_STOP | 0.0 | -2.440114 | 2.448234 | -0.121803 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T09:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.439123 | BE_STOP | 0.0 | -2.439123 | 2.44724 | -0.121753 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T07:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.438134 | BE_STOP | 0.0 | -2.438134 | 2.446247 | -0.121704 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T07:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.425343 | BE_STOP | 0.0 | -2.425343 | 2.433414 | -0.121065 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T08:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.425343 | BE_STOP | 0.0 | -2.425343 | 2.433414 | -0.121065 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T09:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.424365 | BE_STOP | 0.0 | -2.424365 | 2.432432 | -0.121017 | 0.0 | 1.0->0.0 | 8 |
| GBPUSD\|2023-02-06T09:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | 2.424365 | BE_STOP | 0.0 | -2.424365 | 2.432432 | -0.121017 | 0.0 | 1.0->0.0 | 8 |
| NAS100\|2025-06-13T15:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M5 | TIMEOUT | 2.381496 | BE_STOP | 0.0 | -2.381496 | 2.41832 | -0.342213 | 0.0 | 1.5->0.0 | 6 |

### True Rescue Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | delta_lock_minus_j46 | mfe_r | mae_r | max_locked_floor_r | lock_steps | bars_in_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAS100\|2023-04-11T13:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.203967 | -1.185279 | 1.0 | 1.5->0.5;2.0->1.0 | 6 |
| NAS100\|2023-04-11T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.203967 | -1.185279 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 6 |
| NAS100\|2023-06-13T13:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.725342 | -1.377054 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.725342 | -1.377054 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.690872 | -1.367009 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.690872 | -1.367009 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.653202 | -1.356031 | 1.0 | 1.5->0.5;2.0->1.0 | 3 |
| NAS100\|2023-06-13T13:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 4.653202 | -1.356031 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 3 |
| US30_cash\|2023-06-16T15:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.724809 | -1.025161 | 1.0 | 1.5->0.5;2.0->1.0 | 2 |
| US30_cash\|2023-06-16T15:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.724809 | -1.025161 | 1.0 | 1.0->0.0;1.5->0.5;2.0->1.0 | 2 |
| USDJPY\|2023-07-19T00:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T00:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T00:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.489954 | -1.569626 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.460195 | -1.550866 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.518715 | -1.009631 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.49535 | -1.000266 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T01:45:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.453183 | -1.546446 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:00:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.453183 | -1.546446 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.481343 | -1.564197 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |
| USDJPY\|2023-07-19T02:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | LOCK_STOP | 1.0 | 2.0 | 2.481081 | -1.564032 | 1.0 | 1.5->0.5;2.0->1.0 | 4 |

### Missed Favorable Path Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | delta_lock_minus_j46 | mfe_r | mae_r | max_locked_floor_r | lock_steps | bars_in_trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2023-12-12T15:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SL | -1.0 | 0.0 | 2.956818 | -1.721275 |  |  | 1 |
| XAUUSD\|2023-12-12T15:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SL | -1.0 | 0.0 | 2.956818 | -1.721275 |  |  | 1 |
| GBPJPY\|2026-02-05T02:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.675885 | -1.728465 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T02:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.667293 | -1.722915 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T02:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.664887 | -1.721361 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T01:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.651135 | -1.712478 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T01:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.646809 | -1.709683 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T01:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.646809 | -1.709683 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T02:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.637549 | -1.703702 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T03:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.629225 | -1.698325 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T00:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.608508 | -1.684943 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T00:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.608508 | -1.684943 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T00:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.608508 | -1.684943 | 0.0 | 1.0->0.0 | 2 |
| GBPJPY\|2026-02-05T01:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | M1 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.608508 | -1.684943 | 0.0 | 1.0->0.0 | 2 |
| USDJPY\|2024-06-14T01:30:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | M15 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.236822 | -1.681378 | 0.0 | 1.5->0.0 | 11 |
| USDJPY\|2024-06-14T02:00:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | M15 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.236065 | -1.680809 | 0.0 | 1.5->0.0 | 11 |
| NAS100\|2025-11-13T15:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M5 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.192732 | -1.242531 | 0.0 | 1.0->0.0 | 2 |
| NAS100\|2025-11-13T13:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M5 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.185672 | -1.23853 | 0.0 | 1.0->0.0 | 2 |
| NAS100\|2025-11-13T15:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M5 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.178888 | -1.234686 | 0.0 | 1.0->0.0 | 2 |
| NAS100\|2025-11-13T14:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | M5 | SL | -1.0 | BE_STOP | 0.0 | 1.0 | 2.178811 | -1.234642 | 0.0 | 1.0->0.0 | 2 |

### Residual Samebar Examples

| event_key | variant_id | cohort | role | timeframe | j46_outcome | j46_r | lock_outcome | lock_r | mfe_r | mae_r | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2022-02-07T15:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 1.379514 | SAME_BAR |  | 1.763135 | -0.793069 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-07T15:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 1.365804 | SAME_BAR |  | 1.745612 | -0.785187 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:15:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:15:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:30:00+00:00 | PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:30:00+00:00 | PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-09T15:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 0.637743 | -1.169559 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-16T13:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.437625 | SAME_BAR |  | 5.685414 | -0.666113 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-16T13:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.43354 | SAME_BAR |  | 5.680181 | -0.6655 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-16T14:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.396013 | SAME_BAR |  | 5.632101 | -0.659867 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-16T14:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.466349 | SAME_BAR |  | 5.722215 | -0.670425 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-16T14:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | TIMEOUT | 4.433085 | SAME_BAR |  | 5.679598 | -0.665431 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-28T15:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 1.469791 | -1.355722 | OHLC cannot order the policy events inside the selected bar. |
| XAUUSD\|2022-02-28T15:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | M15 | SL | -1.0 | SAME_BAR |  | 1.484951 | -1.369705 | OHLC cannot order the policy events inside the selected bar. |
| GBPUSD\|2022-05-16T08:45:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | -0.443887 | SAME_BAR |  | 1.612539 | -0.650784 | OHLC cannot order the policy events inside the selected bar. |
| GBPUSD\|2022-05-16T09:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | -0.43839 | SAME_BAR |  | 1.59257 | -0.642724 | OHLC cannot order the policy events inside the selected bar. |
| GBPUSD\|2022-05-16T09:15:00+00:00 | PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | M15 | TIMEOUT | -0.441397 | SAME_BAR |  | 1.603491 | -0.647132 | OHLC cannot order the policy events inside the selected bar. |
| USDJPY\|2022-05-26T01:00:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | SAME_BAR |  | 0.289433 | -1.80515 | OHLC cannot order the policy events inside the selected bar. |
| USDJPY\|2022-05-26T01:30:00+00:00 | PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | M15 | SL | -1.0 | SAME_BAR |  | 0.294243 | -1.835147 | OHLC cannot order the policy events inside the selected bar. |

## Unanswered Questions Status

| question | status | detail |
| --- | --- | --- |
| Does favorable movement before failure exist? | ANSWERED_YES | J46 nonpositive rows often had MFE above early fixed-R thresholds; the opportunity exists, but fixed-R capture failed robustness. |
| Did fixed-R locks fail by cutting winners? | ANSWERED_YES | Pairwise truncation counts show lock/BE exits below J46 outcomes across all lock ladders. |
| Did fixed-R locks rescue losers enough to compensate? | ANSWERED_NO_FOR_REGISTERED_DECISION_METRIC | Half-gain narrowly compensates on common resolved rows, but not after full-corpus unresolved handling and pessimistic same-bar stress. |
| Is the broader path-scaling idea dead? | ANSWERED_NO | Only fixed-R lock-only failed. Structural levels and risk-budgeted reentry remain untested. |
| Can V1 answer whether structural levels work? | NOT_ANSWERABLE_IN_V1 | The V1 event log has no structural level selector; this requires a fresh registered hypothesis. |
| Can V1 answer whether reentry works? | NOT_ANSWERABLE_IN_V1 | V1 intentionally contains no reentry or composite risk accounting. |
| Can V1 answer actual spread/slippage impact? | PARTIALLY_ANSWERED | V1 reports R-cost sensitivity only. Real execution costs need broker/tick/slippage data, especially before any reentry test. |
| Which specific cases explain the aggregate result? | ANSWERED_WITH_CASEBOOK | The report includes largest J46-better, largest lock-better, true-rescue, winner-truncation, missed-MFE, and residual-samebar examples. |
| Is there any remaining V1 ambiguity that blocks the V1 verdict? | ANSWERED_NO | Residual OHLC ordering ambiguity remains a data limitation, but it is handled by registered exclusion/stress policy and no longer blocks the V1 rejection. |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Paired-row diagnostic versus registered decision metric | CLOSED_BY_SEPARATION | Half-gain is slightly positive on common resolved rows, but full-corpus unresolved exclusion and pessimistic stress remain the decision lenses. |
| Residual selected-bar same-bars | CLOSED_BY_REGISTERED_POLICY | J46 V1 same-bars=713; samebar-pessimistic all-enabled best-lock-minus-J46=-0.155922. |
| Lower-timeframe coverage skew | CLOSED_AS_DIAGNOSTIC_ONLY | M1/M5 results are useful diagnostics but not final evidence because lower-timeframe availability is not uniform across the full corpus. |
| Cost realism | CLOSED_AS_SENSITIVITY_ONLY | V1 uses R-cost sensitivity because historical OHLC lacks reliable commission, spread, and slippage. |
| Structural-level and reentry questions | OUT_OF_SCOPE_FOR_V1 | V1 has no structural selector, no reentry engine, and no composite risk accounting; these require a fresh pre-registered hypothesis. |
| V1 promotion verdict | CLOSED_REJECTED | Fixed-R lock-only remains NO_PROMOTION_VERDICT and is rejected for exit-policy promotion. |

## Opened Questions

| question | status | answer |
| --- | --- | --- |
| Is any V1-specific question still blocking the V1 verdict? | NO | No. V1 fixed-R lock-only is rejected, and residual same-bar uncertainty is handled by registered policy. |
| Can V1 explain what worked? | YES | MTF resolution worked as measurement infrastructure; J46 remained robust; target and M1/M5 lock hints are diagnostic only. |
| Can V1 explain what failed? | YES | Fixed-R locks add small common-row benefit in one ladder but create extra same-bar exposure and truncate winners; promotion metrics stay below J46. |
| Can V1 decide structural locks? | NO_OUT_OF_SCOPE | No. Structural locks require a fresh registered hypothesis with pre-declared levels and no parameter sweep. |
| Can V1 decide reentry? | NO_OUT_OF_SCOPE | No. Reentry requires structural pullback references plus pre-registered risk and cost accounting. |
| Should work auto-advance to V2? | NO | No. A future V2 must be separately registered; V1 does not promote it automatically. |

## Limitations

| limitation | impact | treatment |
| --- | --- | --- |
| OHLC order inside selected bars | Cannot know whether lock trigger, stop, and target happened first inside a single M1/M5/M15 bar. | Headline excludes unresolved SAME_BAR rows; decision stress scores SAME_BAR as -1R before any promotion. |
| Historical cost model | No reliable per-trade spread/commission/slippage in the OHLC corpus. | Use R-cost sensitivity only; do not claim measured live execution economics. |
| Same dataset | Forensics can explain V1 failure but cannot promote a tuned variant from the same corpus. | NO_PROMOTION_VERDICT remains; no parameter optimization. |
| No structural levels | V1 cannot decide whether liquidity/OB/FVG/swing-level locks would work. | Any structural test needs a fresh registered hypothesis before data inspection. |
| No reentry accounting | V1 cannot evaluate the owner thesis that lock + reentry changes the payoff distribution. | Reentry stays blocked until a structural lock earns a separate test and cost/risk rules are registered. |

## Deeper Dive Candidates

| rank | candidate | reason | status |
| --- | --- | --- | --- |
| 1 | Structural liquidity lock hypothesis | Fixed-R anchors are too blunt; the remaining thesis is that locks should occur at market levels known at decision time. | FRESH_HYPOTHESIS_REQUIRED |
| 2 | Truncation casebook | Sample the largest J46-better deltas to see if locks cut real runners or only ambiguous/noisy bars. | OPTIONAL_MANUAL_AUDIT |
| 3 | Tick-order audit for M1/M5 same-bars | Could reduce remaining OHLC ordering uncertainty, but it requires tick coverage and should not be assumed. | DATA_QUALITY_LANE |
| 4 | Risk-budgeted reentry | The owner thesis includes reentry, but reentry should wait until a structural lock/pullback reference exists. | BLOCKED_UNTIL_STRUCTURAL_LOCK_EARNS_IT |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Archive fixed-R V1 lock-only as rejected. | The failure mode is now explained: small common-row rescue benefit, material truncation, extra same-bar exposure, and no robustness under the registered stress treatment. |
| 2 | If continuing path-scaling, register exactly one structural-level lock hypothesis. | The remaining plausible thesis is structural timing, not more fixed-R sweeps. |
| 3 | Keep the V1 MTF resolver and residual same-bar policy as shared infrastructure. | The measurement layer worked and should prevent future path studies from fabricating order. |
| 4 | Do not implement reentry yet. | Reentry needs a trusted structural pullback/lock level and strict risk accounting. |

## Synthesis

- The failure is not evidence that the market never offers path opportunity. J46 nonpositive outcomes often had favorable MFE before final failure.
- The failure is evidence that fixed-R lock ladders are the wrong first abstraction: half-gain barely improves common resolved rows, but the improvement is too small to survive full-corpus unresolved handling, same-bar stress, and winner-truncation diagnostics.
- This is a logic/design failure of fixed-R lock-only, plus a measurement limitation around OHLC same-bars. It is not a live execution failure, prompt failure, or AI failure.
- The next credible research step is a freshly registered structural-level hypothesis. Without that, more fixed-R tweaking would become parameter optimization.
