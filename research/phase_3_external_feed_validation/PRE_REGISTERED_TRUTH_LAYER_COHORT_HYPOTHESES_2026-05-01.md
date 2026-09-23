# Pre-Registered Phase 3 Truth-Layer Cohort Hypotheses

**Date pre-registered:** 2026-05-01  
**Status:** controlled research setup only  
**Machine-readable spec:** `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`  
**Prospective holdout plan:** `research/phase_3_external_feed_validation/TRUTH_LAYER_PROSPECTIVE_HOLDOUT_PLAN_2026-05-01.md`  
**Prospective candidate matrix:** `research/phase_3_external_feed_validation/TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`  
**Promotion verdict allowed from this artifact:** NO

## Boundary

This registry authorizes a controlled, research-only follow-up for two mechanical truth-layer cohorts:

- `USDJPY|tokyo|bearish|D1`
- `GBPJPY|tokyo|bullish|D1`

It does not authorize alpha promotion, live trading changes, prompt edits, source/config changes, parameter optimization, or paid AI/API calls. The cohorts were selected after reading same-dataset diagnostics, so same-dataset evaluation can only support stability, invalidation, and data-quality decisions.

Any future promotion claim needs a separate untouched holdout or prospective validation pass with DSR, PBO, and effective-N accounting.

## Source Lock

Selection came from the rescued Phase 3 mechanical truth layer and the follow-up stability pass.

| Artifact | Path | SHA256 |
| --- | --- | --- |
| Truth-layer JSONL | `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/truth_layer/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl` | `0530a49f1eafcaa46bf94b9c9267670d815803ed3c067ecd5501a5a9888455ae` |
| Follow-up cohort file | `research/phase_3_external_feed_validation/TRUTH_LAYER_FOLLOWUP_COHORTS_V1.json` | `b24a8305a124f0c6fa90f23f52f4347b3726f280324d4a5ed8d578aabdac6e8c` |
| Source commit | `f55449bdc30cd61a25d8e664d17433c34962cc1c` | n/a |

The two primary cohorts were not chosen from an untouched holdout. They are post-diagnostic selections from the same truth-layer file. This is the key limitation and must be repeated in every report generated from this registry.

## Trial Budget

This registry defines one family: `truth_layer_jpy_tokyo_d1_v1`.

For same-dataset evaluation, the family is diagnostic-only and cannot lower the project-wide DSR burden. If any p-values or lift claims are later reported, they must use at least the project-wide cumulative trial count floor `N = 200` and the Sharpe noise ceiling `3.078`.

For a future untouched holdout or prospective pass, the family consumes one registered Phase 3 truth-layer trial. The two primary cohorts are child hypotheses inside that family. Both child cohorts must be reported. Selecting only the better child after evaluation is exploratory and cannot be promoted.

The watchlist cohorts consume zero trial budget now because they are not authorized for controlled evaluation by this registry.

The wider prospective candidate matrix consumes no promotion trial by itself. It freezes the comparator universe required for future PBO/effective-N accounting across instruments. Future promotion attempts must report the registered matrix instead of narrowing to only the historically strongest cohorts.

## Methodology Gates

Required before any promotion claim:

- DSR-corrected `p < 0.01`
- PBO `< 0.4`
- effective_N `>= 3`
- fold-level results reported, not only pooled results
- no single year, date range, source artifact, or cohort child dominates the family result

The current evaluator is allowed to report locked-population diagnostics only. It does not compute DSR, PBO, or true effective_N, so it must emit `NO_PROMOTION_VERDICT`.

## Locked Population

The primary population for both child hypotheses is `RESOLUTION_SAFE_HIGH`:

- exact `cohort_key`
- `would_send_ai == true`
- `mechanical_setup_status == "OK"`
- `truth_confidence == "HIGH"`
- exclude `truth_outcome in {"SAME_BAR", "LOWER_TF_GAPPY"}`
- require selected-source lower-timeframe gaps to be absent or after mechanical resolution
- primary target: `truth_realized_r` on resolved outcomes `TP`, `SL`, and `TIMEOUT`
- secondary targets: win rate on resolved rows, no-entry rate on population rows, immediate-stop rate on SL rows, year-fold mean R, and early/recent split mean R

`NO_ENTRY` rows stay in the population denominator. Dropping them is parameter research and is forbidden by this registry.

## Forbidden Changes

The controlled follow-up may not:

- change entry offsets, stop buffers, take-profit distance, session windows, or regime definitions
- switch to `HIGH+MEDIUM` or `ZERO_GAP` as the primary scope after seeing results
- drop years, date ranges, NO_ENTRY rows, or underperforming fold cells after seeing results
- include Component 3A AI behavior, prompt behavior, L2 gates, J46-J49, S79/risk policy, execution slippage, or external-feed features
- treat the same-dataset result as out-of-sample validation

Sensitivity views are allowed only if labeled secondary and reported alongside the locked primary population.

## Primary Hypotheses

### H-P3-TL-JPY-001

**Cohort:** `USDJPY|tokyo|bearish|D1`  
**Description:** USDJPY Tokyo bearish D1 mechanical truth-layer cohort.  
**Selection basis:** Stability report showed CLEAN_HIGH n=212, mean R=+0.630181, valid years=3, positive years=3.  
**Required population:** `RESOLUTION_SAFE_HIGH` as defined above.  
**Necessary but not sufficient preconditions:** resolved n >= 150, at least 3 valid calendar-year folds, every valid year fold has positive mean R, and max single-year resolved share <= 45%.

### H-P3-TL-JPY-002

**Cohort:** `GBPJPY|tokyo|bullish|D1`  
**Description:** GBPJPY Tokyo bullish D1 mechanical truth-layer cohort.  
**Selection basis:** Stability report showed CLEAN_HIGH n=430, mean R=+0.493024, valid years=4, positive years=4.  
**Required population:** `RESOLUTION_SAFE_HIGH` as defined above.  
**Necessary but not sufficient preconditions:** resolved n >= 150, at least 3 valid calendar-year folds, every valid year fold has positive mean R, and max single-year resolved share <= 45%.

## Splits

Primary split:

- calendar-year folds
- valid fold minimum: 30 resolved primary-target rows

Secondary split:

- early: `2022`, `2023`
- recent: `2024`, `2025`, `2026`

Underpowered years remain visible. They may not be silently merged or dropped after results are known.

## Watchlist Only

The following cohorts are explicitly not authorized for controlled evaluation in this registry:

- `XAUUSD|ny|bullish|D1`
- `US30_cash|ny|bullish|H4+H1_consensus`
- `NAS100|ny|bullish|D1`
- `XAGUSD|ny|bullish|H4+H1_consensus`

Each needs a separate future pre-registration if it becomes a primary controlled hypothesis.

## Invalidation Rules

The controlled report is invalidated until fixed if:

- duplicate opportunity keys exist in the truth-layer input
- any `ai_call_count_sum > 0` or AI-attempted row appears
- source hashes do not match this registry and the difference is not explicitly re-registered
- primary population filtering is changed after looking at results

Any promotion claim is blocked if:

- either primary child cohort has resolved n < 150
- either child has fewer than 3 valid year folds
- any valid year fold has mean R <= 0
- any single valid year contributes more than 45% of resolved rows
- DSR-corrected p >= 0.01
- PBO >= 0.4
- effective_N < 3
- evidence remains same-dataset-only

## Allowed Next Artifact

The allowed evaluator is `scripts/evaluate_truth_layer_controlled_hypotheses.py`. It may report locked-population diagnostics and precondition flags. It must not emit a PASS/FAIL alpha verdict.
