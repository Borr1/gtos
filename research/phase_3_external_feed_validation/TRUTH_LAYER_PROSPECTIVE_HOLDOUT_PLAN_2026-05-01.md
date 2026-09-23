# Phase 3 Truth-Layer Prospective Holdout Plan

**Date registered:** 2026-05-01  
**Status:** research-only next-step plan  
**Promotion verdict allowed from this artifact:** NO

## Boundary

This plan defines the first unambiguous path from the same-dataset truth-layer diagnostics toward promotion-eligible evidence. It does not change live trading logic, prompts, source code behavior, risk policy, execution behavior, or production configuration.

The currently available evidence remains same-dataset research:

- Controlled hypothesis report: `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESIS_REPORT_2026-05-01.md`
- Methodology readiness report: `research/phase_3_external_feed_validation/TRUTH_LAYER_METHODOLOGY_GATE_READINESS_2026-05-01.md`
- Post-hoc PBO diagnostic: `research/phase_3_external_feed_validation/TRUTH_LAYER_POSTHOC_PBO_DIAGNOSTIC_2026-05-01.md`
- Prospective candidate matrix: `research/phase_3_external_feed_validation/TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`
- Effective-N diagnostic: `research/phase_3_external_feed_validation/TRUTH_LAYER_EFFECTIVE_N_DIAGNOSTIC_2026-05-01.md`

The latest source truth-layer artifact ends at `2026-04-30T17:00:00+00:00`. Prospective holdout rows must have `candle_close_utc > 2026-04-30T17:00:00+00:00`.

## Current Evidence Status

| Gate | Current result | Interpretation |
| --- | --- | --- |
| Locked population diagnostics | Both primary cohorts meet necessary research preconditions | Supports controlled follow-up only |
| Same-dataset DSR diagnostic | USDJPY `p=0.000219939063`; GBPJPY `p=0.00000058104` | Priority signal only; not promotion-usable |
| Post-hoc PBO diagnostic | `0.5553613053613053` across 44 eligible historical cohort candidates and 52 monthly periods | Selection-risk warning; above the `<0.4` promotion threshold |
| Historical matrix effective_N diagnostic | 44-candidate matrix `20.575922`; primary two children alone `1.97964` | Infrastructure gap closed for diagnostics; promotion still blocked until prospective |
| Untouched/prospective validation | Absent | Promotion blocked |

This is not bad news for the research program. It is exactly why the next evidence must be prospective or otherwise untouched. The positive same-dataset signal is strong enough to justify measurement, while the PBO diagnostic says it is not safe to promote from the same dataset. The effective-N diagnostic also confirms that the two primary children alone are not enough to represent independent evidence; the broader registered candidate matrix must stay in scope.

## Frozen Primary Family

Registered family: `truth_layer_jpy_tokyo_d1_v1`

Primary child hypotheses:

- `H-P3-TL-JPY-001`: `USDJPY|tokyo|bearish|D1`
- `H-P3-TL-JPY-002`: `GBPJPY|tokyo|bullish|D1`

Both children must be reported in every prospective report. Selecting only the better child after seeing future results is exploratory and cannot support promotion.

## Frozen Primary Population

The primary prospective population inherits `RESOLUTION_SAFE_HIGH` from `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`:

- exact `cohort_key`
- `would_send_ai == true`
- `mechanical_setup_status == "OK"`
- `truth_confidence == "HIGH"`
- exclude `truth_outcome in {"SAME_BAR", "LOWER_TF_GAPPY"}`
- require selected-source lower-timeframe gaps to be absent or after mechanical resolution
- resolved primary target: `truth_realized_r` on `TP`, `SL`, and `TIMEOUT`
- keep `NO_ENTRY` rows in the population denominator

No entry offsets, stop buffers, take-profit distance, session windows, regime definitions, lower-timeframe source priority, or population filters may be changed inside this family.

## Prospective Collection Rules

Collection may only use mechanical, no-AI truth-layer tooling. Any row with `ai_call_attempted == true` or `ai_call_count > 0` invalidates the report until removed or separately quarantined.

Prospective rows must be generated from data not present in the source truth-layer artifact. The current cutoff is:

`2026-04-30T17:00:00+00:00`

Allowed collection sources:

- future free-feed or MT5 OHLCV exports processed by the same historical opportunity/truth-layer pipeline
- no-lookahead external-feed snapshots if they already exist before the evaluated candle
- live shadow logs only after they have been transformed into the same truth-layer schema without changing live runtime behavior

Forbidden collection sources:

- reusing or relabeling rows from the locked historical truth-layer file as prospective
- paid AI/API calls
- live trading decisions, prompt edits, or production gate changes
- manual cherry-picking of favorable dates, instruments, sessions, or rows

## Reporting Cadence

Interim reports are allowed at approximately 30, 60, and 100 resolved prospective rows per primary child. Interim reports must emit `NO_PROMOTION_VERDICT`.

Promotion-grade evaluation cannot be attempted until all of the following are true:

- each primary child has at least 150 prospective resolved primary-target rows
- at least 3 independent validation folds or paths are available
- every registered primary child is reported
- DSR-corrected `p < 0.01` using at least the project-wide trial floor `N=200`
- PBO `< 0.4` on a pre-registered prospective candidate matrix
- true effective_N `>= 3`
- no duplicate opportunity keys
- no AI calls
- source hashes and row counts are recorded

## PBO Requirement

The two primary child cohorts alone are not enough to compute promotion-grade PBO if no selection matrix exists. To satisfy the project-wide PBO gate, a future promotion attempt must include one of these paths:

1. Freeze a prospective candidate matrix before evaluation, then compute CSCV/PBO on all registered candidates.
2. Declare the future report a confirmation-only family report with no promotion verdict.

The registered prospective candidate matrix is `research/phase_3_external_feed_validation/TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`, generated from the transparent historical diagnostic universe in `scripts/analyze_truth_layer_posthoc_pbo.py`:

- population: `RESOLUTION_SAFE_HIGH`
- candidate unit: `symbol|session|truth_regime`
- eligibility at registration: `min_total_resolved_n >= 150`, `min_valid_year_folds >= 3`, `min_year_resolved_n >= 30`
- current eligible universe size: 44 candidates
- periodization for PBO: calendar month
- missing-period policy: zero return for no resolved trade

This universe was discovered after historical diagnostics, so historical PBO remains post-hoc. For prospective data, the value is that the universe and metric are now frozen before future rows arrive.

## Effective-N Requirement

Calendar-year fold count is not true effective_N. `scripts/analyze_truth_layer_effective_n.py` now computes a dependence-adjusted diagnostic using the eigenvalue participation ratio of the candidate return correlation matrix.

Historical diagnostic result:

- 44-candidate matrix: effective_N `20.575922`
- two primary children only: effective_N `1.97964`

The historical result is not promotion-usable because the matrix was frozen after discovery. A promotion-grade report must use the same registered matrix on prospective rows and compute dependence-adjusted effective_N from path-level return vectors or score vectors.

Minimum implementation requirements:

- registered path definitions
- path-level return vectors for every registered candidate
- correlation matrix across paths or candidates
- ONC or equivalent dependence adjustment
- explicit `effective_N >= 3` check

Until that exists, all reports remain research-only.

## Invalidation Rules

The prospective report is invalidated until fixed if:

- any row has `candle_close_utc <= 2026-04-30T17:00:00+00:00`
- any duplicate `opportunity_key` exists
- any row has AI call evidence
- source file hashes are missing
- the population differs from `TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
- only the better primary child is reported
- dates, sessions, instruments, or underperforming periods are dropped after results are known

Any promotion claim is blocked if:

- evidence remains same-dataset-only
- either primary child has fewer than 150 prospective resolved rows
- DSR-corrected `p >= 0.01`
- PBO `>= 0.4`
- true effective_N `< 3`
- the prospective candidate matrix was not frozen before evaluation

## Next Build Step

The safe tooling artifacts for this boundary are:

- `scripts/evaluate_truth_layer_prospective_holdout.py` for the two primary child cohorts
- `scripts/evaluate_truth_layer_prospective_matrix.py` for the full 44-candidate matrix, prospective PBO, and prospective effective-N diagnostics

They refuse to run unless:

- the input file is separate from the locked historical truth-layer source
- every evaluated row is after `2026-04-30T17:00:00+00:00`
- the hypothesis spec is `TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
- promotion output defaults to `NO_PROMOTION_VERDICT`

That evaluator may produce interim monitoring reports. It must not emit an alpha promotion verdict until DSR, PBO, and true effective_N are implemented and all promotion prerequisites above are satisfied.

Example command once a genuine prospective truth-layer file exists:

```powershell
python scripts/evaluate_truth_layer_prospective_holdout.py --input path\to\future_truth_layer.jsonl --write --quiet
python scripts/evaluate_truth_layer_prospective_matrix.py --input path\to\future_truth_layer.jsonl --write --quiet
```
