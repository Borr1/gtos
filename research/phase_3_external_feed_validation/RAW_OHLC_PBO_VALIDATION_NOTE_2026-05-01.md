# Phase 3 Raw-OHLC PBO Validation Note

**Date:** 2026-05-01
**Scope:** Research/tooling only
**Verdict:** PBO calculation is valid as a post-hoc selection-risk diagnostic, not as promotion proof.

## What Is Being Calculated

The implementation used by the truth-layer and raw-OHLC follow-up reports is `cscv_pbo()` in `scripts/analyze_truth_layer_posthoc_pbo.py`.

Input matrix:

- Rows are calendar-month periods.
- Columns are candidate strategies or cohort composites.
- Cell value is summed resolved R for that period.
- Missing resolved activity in a period is treated as zero return for that candidate.

Procedure:

1. Split the full period sequence into balanced contiguous subperiods.
2. Enumerate every combination of half the subperiods as in-sample.
3. Use the remaining half as out-of-sample.
4. Select the strategy with the highest mean in-sample return.
5. Rank that selected strategy by its out-of-sample mean return.
6. Convert the OOS rank to a logit.
7. Count the split as overfit when the selected in-sample winner lands below median out-of-sample.

Because OOS ranks are sorted worst-to-best, `logit < 0` means the selected in-sample winner landed in the bottom half out-of-sample. PBO is the share of CSCV splits where that happens.

## Validation Performed

New tests were added in `tests/test_truth_layer_posthoc_pbo.py`:

- Constant winner matrix returns PBO `0.0`.
- Regime-flip matrix where the in-sample winner becomes the OOS loser returns PBO `1.0`.
- Non-divisible period counts keep all periods via balanced contiguous subperiods.
- Too-small matrices are blocked instead of producing a fake value.

New raw follow-up tests were added in `tests/test_raw_ohlc_replay_followup_analysis.py`:

- The report separates targets, negative controls, and blocked dominance controls.
- PBO variants are surfaced explicitly, including target-family versus negative-control family and target-family versus blocked-control family.

Verification command:

```powershell
python -m pytest tests\test_raw_ohlc_replay_followup_analysis.py tests\test_truth_layer_posthoc_pbo.py -q
```

Result: `8 passed`.

## Current Raw-OHLC PBO Reads

Default target plus negative-control run:

| Variant | Strategies | Periods | PBO | Interpretation |
|---|---:|---:|---:|---|
| all_enabled_individual_cohorts | 8 | 50 | 0.462413 | High selection risk if we pick the best individual cohort after seeing results. |
| target_child_selection | 5 | 50 | 0.546037 | High selection risk if we pick the best of the five target children. |
| negative_control_child_selection | 3 | 50 | 0.673660 | Negative-control child universe is unstable, as expected. |
| target_family_vs_negative_control_family | 2 | 50 | 0.000000 | The pre-registered target-family composite is stable versus negative controls in this same-dataset diagnostic. |

Blocked-control-inclusive run:

| Variant | Strategies | Periods | PBO | Interpretation |
|---|---:|---:|---:|---|
| all_enabled_individual_cohorts | 11 | 51 | 0.451340 | Still high if we select among all individual cohorts after seeing results. |
| target_child_selection | 5 | 51 | 0.531760 | Still high for child-picking. |
| negative_control_child_selection | 3 | 51 | 0.658217 | Negative-control child selection remains unstable. |
| target_family_vs_negative_control_family | 2 | 51 | 0.000000 | Target family remains stable versus negative controls in the diagnostic. |
| blocked_control_child_selection | 3 | 51 | 0.334499 | Blocked controls are less unstable than ordinary controls, which is why they stay blocked as dominance controls. |
| target_family_vs_blocked_control_family | 2 | 51 | 0.529720 | Target family does not cleanly dominate blocked controls by CSCV rank stability. |

## Interpretation

The PBO artifact is not saying "the edge failed." It is saying "do not choose the best-looking individual child after looking at this dataset." That warning is valid.

The strongest same-dataset read is family-level, not child-level:

- Picking an individual target child is overfit-prone.
- The five-target family separates from negative controls.
- Blocked dominance-watchlist controls are also positive, which means broad-market dominance artifacts remain a real confound.
- Therefore the next honest lane is a frozen family-composite validation, not a new round of child selection.

## What This Does Not Prove

This PBO does not prove promotion readiness because:

- The candidate universe was formed after prior discovery work.
- The same historical corpus has now been inspected repeatedly.
- The metric is monthly summed R, while the original cohort selection used several diagnostics, not this exact PBO metric alone.
- Missing-period zero returns can create rank/tie sensitivity for sparse cohorts.
- Older data can be useful only if we can prove it was untouched by selection decisions at the time of the claim.

The user correctly flagged the 2022 question. If the earlier API backtests truly did not inspect 2022 data, then 2022 could have been a cleaner holdout at that earlier point. After this Phase 3 raw-OHLC work, 2022 is no longer untouched for these exact cohorts. The cleanest validation now is future/prospective data or a demonstrably untouched broker/data slice frozen before evaluation.

## How To Beat The PBO Properly

Valid ways:

- Pre-register the candidate universe, periodization, metric, and selection rule before the next evaluation.
- Evaluate the target family composite, not the best child selected after seeing results.
- Use prospective or untouched data that was not part of discovery.
- Keep negative controls and blocked dominance controls in the report.
- Report DSR, PBO, effective_N, coverage, and the full ambiguity ledger together.

Invalid ways:

- Dropping GBPUSD after seeing that it hurt the headline.
- Promoting only the best child cohort because it looked strongest in the matrix.
- Treating same-dataset DSR or same-dataset PBO as promotion-grade.
- Adding or removing controls after seeing whether they help the story.

## Bottom Line

The PBO code is behaving correctly for the diagnostic it claims to be. The high individual-cohort PBO is not a bug to engineer away. It is evidence that the next test must freeze the family-level decision rule and move to an untouched/prospective validation lane.
