# Phase 3 Truth-Layer Post-Hoc PBO Diagnostic

**Created UTC:** 2026-05-01T08:29:06.795608+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Spec:** `research\phase_3_external_feed_validation\TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
**Promotion verdict:** `NOT_ALLOWED_POSTHOC_DIAGNOSTIC_ONLY`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- This is a post-hoc selection-risk diagnostic. It is not promotion-grade PBO.
- The original cohorts were selected by diagnostics/stability before this PBO universe was frozen.
- A future promotion-grade PBO needs a pre-registered universe and untouched/prospective data.

## Assumptions

| selection_status | population_scope | candidate_unit | periodization | period_performance_metric | missing_period_policy | selection_metric_mismatch | eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| posthoc_after_same_dataset_cohort_discovery | RESOLUTION_SAFE_HIGH | symbol\|session\|truth_regime | calendar_month | sum_truth_realized_r_on_resolved_rows | zero_return_no_resolved_trade | Original primary cohorts were selected by diagnostics/stability, not by this monthly-sum-R PBO metric. Treat this as selection-risk evidence only. | {"min_total_resolved_n": 150, "min_valid_year_folds": 3, "min_year_resolved_n": 30} |

## PBO Result

| period_count | candidate_universe_n | eligible_universe_n | pbo | pbo_status | promotion_usable | promotion_usable_reason |
| --- | --- | --- | --- | --- | --- | --- |
| 52 | 95 | 44 | 0.5553613053613053 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | False | Universe and metric were frozen after cohort discovery. |

## Primary Cohorts

| cohort_key | eligible_for_posthoc_pbo_universe | rank_by_total_sum_r | rank_by_mean_r | population_rows | resolved_r_n | sum_r | mean_r | win_rate | valid_year_folds | positive_valid_year_folds | max_year_resolved_share | active_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|tokyo\|bearish\|D1 | True | 10 | 1 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 3 | 3 | 0.330189 | 11 |
| GBPJPY\|tokyo\|bullish\|D1 | True | 2 | 4 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 4 | 4 | 0.413953 | 26 |

## Top Eligible By Total Sum R

| cohort_key | population_rows | resolved_r_n | sum_r | mean_r | win_rate | valid_year_folds | positive_valid_year_folds | max_year_resolved_share | active_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAS100\|ny\|bullish\|D1 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 3 | 3 | 0.581616 | 21 |
| GBPJPY\|tokyo\|bullish\|D1 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 4 | 4 | 0.413953 | 26 |
| GBPUSD\|london\|bearish\|D1 | 1396 | 727 | 179.6955 | 0.247174 | 0.503439 | 5 | 4 | 0.264099 | 21 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 5 | 4 | 0.243615 | 31 |
| XAUUSD\|ny\|bullish\|D1 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 3 | 3 | 0.453376 | 20 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 3 | 3 | 0.45625 | 18 |
| GBPJPY\|london\|bullish\|H4+H1_consensus | 1292 | 530 | 161.2745 | 0.304292 | 0.516981 | 4 | 3 | 0.456604 | 27 |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | 1552 | 657 | 150.0429 | 0.228376 | 0.493151 | 4 | 3 | 0.461187 | 28 |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | 1476 | 655 | 135.492 | 0.206858 | 0.485496 | 5 | 4 | 0.300763 | 29 |
| USDJPY\|tokyo\|bearish\|D1 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 3 | 3 | 0.330189 | 11 |
| XAGUSD\|london\|bullish\|H4+H1_consensus | 584 | 584 | 118.5 | 0.202911 | 0.481164 | 5 | 3 | 0.241438 | 26 |
| XAGUSD\|london\|bullish\|D1 | 249 | 249 | 100.5655 | 0.403878 | 0.558233 | 3 | 3 | 0.35743 | 15 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 458 | 252 | 97.5805 | 0.387224 | 0.563492 | 4 | 4 | 0.34127 | 15 |
| GBPJPY\|ny\|bullish\|H4+H1_consensus | 1201 | 449 | 79.2424 | 0.176486 | 0.492205 | 5 | 2 | 0.438753 | 28 |
| XAUUSD\|london\|bullish\|D1 | 395 | 395 | 71.6689 | 0.18144 | 0.470886 | 5 | 4 | 0.41519 | 19 |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | 285 | 285 | 67.1006 | 0.235441 | 0.491228 | 3 | 2 | 0.378947 | 19 |
| USDJPY\|london\|bearish\|D1 | 404 | 154 | 66.0 | 0.428571 | 0.571429 | 3 | 3 | 0.337662 | 10 |
| NAS100\|london\|bullish\|H4+H1_consensus | 662 | 662 | 53.685 | 0.081095 | 0.429003 | 4 | 3 | 0.321752 | 24 |
| XAUUSD\|london\|bearish\|H4+H1_consensus | 388 | 388 | 52.0 | 0.134021 | 0.453608 | 4 | 1 | 0.332474 | 22 |
| GBPJPY\|london\|bullish\|D1 | 792 | 318 | 51.6575 | 0.162445 | 0.459119 | 4 | 2 | 0.342767 | 23 |

## Top Eligible By Mean R

| cohort_key | population_rows | resolved_r_n | sum_r | mean_r | win_rate | valid_year_folds | positive_valid_year_folds | max_year_resolved_share | active_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|tokyo\|bearish\|D1 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 3 | 3 | 0.330189 | 11 |
| XAUUSD\|ny\|bullish\|D1 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 3 | 3 | 0.453376 | 20 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 3 | 3 | 0.45625 | 18 |
| GBPJPY\|tokyo\|bullish\|D1 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 4 | 4 | 0.413953 | 26 |
| USDJPY\|london\|bearish\|D1 | 404 | 154 | 66.0 | 0.428571 | 0.571429 | 3 | 3 | 0.337662 | 10 |
| XAGUSD\|london\|bullish\|D1 | 249 | 249 | 100.5655 | 0.403878 | 0.558233 | 3 | 3 | 0.35743 | 15 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 458 | 252 | 97.5805 | 0.387224 | 0.563492 | 4 | 4 | 0.34127 | 15 |
| NAS100\|ny\|bullish\|D1 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 3 | 3 | 0.581616 | 21 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 5 | 4 | 0.243615 | 31 |
| GBPJPY\|london\|bullish\|H4+H1_consensus | 1292 | 530 | 161.2745 | 0.304292 | 0.516981 | 4 | 3 | 0.456604 | 27 |
| US30_cash\|london\|bearish\|D1 | 173 | 173 | 49.5 | 0.286127 | 0.514451 | 3 | 2 | 0.393064 | 9 |
| USDJPY\|london\|bearish\|H4+H1_consensus | 425 | 181 | 49.2944 | 0.272345 | 0.524862 | 3 | 1 | 0.392265 | 11 |
| GBPUSD\|london\|bearish\|D1 | 1396 | 727 | 179.6955 | 0.247174 | 0.503439 | 5 | 4 | 0.264099 | 21 |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | 285 | 285 | 67.1006 | 0.235441 | 0.491228 | 3 | 2 | 0.378947 | 19 |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | 1552 | 657 | 150.0429 | 0.228376 | 0.493151 | 4 | 3 | 0.461187 | 28 |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | 1476 | 655 | 135.492 | 0.206858 | 0.485496 | 5 | 4 | 0.300763 | 29 |
| XAGUSD\|london\|bullish\|H4+H1_consensus | 584 | 584 | 118.5 | 0.202911 | 0.481164 | 5 | 3 | 0.241438 | 26 |
| XAUUSD\|london\|bullish\|D1 | 395 | 395 | 71.6689 | 0.18144 | 0.470886 | 5 | 4 | 0.41519 | 19 |
| GBPJPY\|ny\|bullish\|H4+H1_consensus | 1201 | 449 | 79.2424 | 0.176486 | 0.492205 | 5 | 2 | 0.438753 | 28 |
| GBPJPY\|london\|bullish\|D1 | 792 | 318 | 51.6575 | 0.162445 | 0.459119 | 4 | 2 | 0.342767 | 23 |

## Synthesis

- This report quantifies selection-risk pressure over a transparent post-hoc universe.
- It cannot rescue same-dataset evidence into a promotion claim.
- If the PBO diagnostic is weak, the next step is still prospective validation; if it is strong, it only prioritizes the frozen cohorts.
