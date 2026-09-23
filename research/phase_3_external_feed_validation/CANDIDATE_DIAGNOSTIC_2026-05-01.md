# Phase 3 Candidate External-Feed Diagnostic

**Status:** diagnostic only; promotion verdict suppressed.
**Created UTC:** 2026-05-01T01:17:00.809921+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\candidate_join\phase3_candidate_calendar_macro_join_union_v2_20260501T010216Z.jsonl`
**Bundle:** `calendar_macro_bundle_v1`
**Target:** `candidate__synthetic_realized_r`

**Scope note:** this file evaluates recent live/shadow CANDIDATE rows. It is not a 2022-2026 historical AI-candidate replay.

## Methodology Gate

- Verdict: `SUPPRESSED_DIAGNOSTIC_ONLY`
- Promotion allowed: `False`
- Actual realized-R rows: 0
- Diagnostic target rows: 29
- Required before any alpha claim: DSR-corrected p < 0.01, PBO < 0.4, effective_N >= 3, cumulative trial budget N = 200.
- Suppression reasons: diagnostic_only_not_promotion_evaluation, cpcv_pbo_not_computed, dsr_corrected_p_not_computed, effective_n_not_computed, trial_budget_protected_bundle_level_only, actual_candidate_realized_r_absent, resolved_target_rows_below_30

## Coverage

- Rows read: 72
- Target available: 29
- Target missing: 43
- External validation matched: 66
- External validation missing: 6

## Baseline Diagnostic Target

| n | sum R | mean R | median R | win rate | min R | max R |
|---:|---:|---:|---:|---:|---:|---:|
| 29 | 9.3602 | 0.3228 | 0.7591 | 55.2% | -1.0000 | 1.5114 |

## Source Availability

| source field | all rows available | target rows available |
|---|---:|---:|
| `fred__available` | 66 | 29 |
| `lbma_calendar__available` | 2 | 2 |
| `cftc_cot__available` | 2 | 2 |
| `wgc__available` | 0 | 0 |
| `flashalpha_gex__available` | 0 | 0 |

## Target By Symbol

| symbol | rows | target n | mean R | win rate |
|---|---:|---:|---:|---:|
| `NAS100` | 11 | 11 | -0.7727 | 9.1% |
| `GBPUSD` | 21 | 9 | 1.5003 | 100.0% |
| `GBPJPY` | 20 | 4 | 1.0893 | 100.0% |
| `USDJPY` | 17 | 3 | -1.0000 | 0.0% |
| `XAUUSD` | 2 | 2 | 1.5000 | 100.0% |
| `US30` | 1 | 0 | n/a | n/a |

## Frozen Numeric Screens

These are lead-generation diagnostics only. They do not create per-feature alpha claims.

| field | n | distinct | Spearman r | upper-lower mean R | note |
|---|---:|---:|---:|---:|---|
| `fred__DGS10__value` | 29 | 5 | 0.1867 | 0.8955 | eligible |
| `fred__DGS2__value` | 29 | 4 | 0.2663 | 0.8955 | eligible |
| `fred__DFII10__value` | 29 | 5 | 0.2889 | -0.3900 | eligible |
| `fred__T10YIE__value` | 29 | 4 | -0.2230 | -1.4207 | eligible |
| `fred__VIXCLS__value` | 29 | 5 | -0.5635 | -1.4554 | eligible |
| `fred__GVZCLS__value` | 29 | 5 | 0.3096 | -0.2809 | eligible |
| `fred__DTWEXBGS__value` | 29 | 3 | -0.0959 | n/a | eligible |
| `lbma_calendar__minutes_to_next_fix` | 2 | 2 | n/a | 0.0000 | below_min_numeric_n |
| `lbma_calendar__minutes_since_previous_fix` | 2 | 2 | n/a | 0.0000 | below_min_numeric_n |
| `cftc_cot__disagg_combined__managed_money_net` | 2 | 1 | n/a | n/a | below_min_numeric_n |
| `cftc_cot__disagg_combined__managed_money_long` | 2 | 1 | n/a | n/a | below_min_numeric_n |
| `cftc_cot__disagg_combined__managed_money_short` | 2 | 1 | n/a | n/a | below_min_numeric_n |
| `cftc_cot__disagg_combined__open_interest` | 2 | 1 | n/a | n/a | below_min_numeric_n |

## Readout

This artifact moves Phase 3 forward by making the candidate-level join evaluable without relaxing the methodology gate. The useful information is coverage, target availability, fold diversity, and frozen-source diagnostic leads. The current artifact is not enough for promotion because actual realized-R is absent and PBO/DSR/effective_N are not computed.
