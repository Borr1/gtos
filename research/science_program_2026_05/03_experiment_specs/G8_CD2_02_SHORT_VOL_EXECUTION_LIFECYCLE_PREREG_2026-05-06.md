# G8 CD2-02 Short-Vol Execution Lifecycle Prereg - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

## Scope

This is a G8-owned second-pass prereg for `CD2-02 - Short-vol stress versus execution lifecycle`.

It answers the G0 assignment question: can short-tenor volatility context join pending-limit no-fill, spread, and close-side cost rows without label mixing around `HYP-G8-VIX1D9D-STRESS-002`, `G10-HYP-PENDING-001`, `G10-HYP-PREFILL-003`, and `HYP-G11-FRICTION-GATE-007`?

Answer: yes for pending-limit lifecycle rows only after as-of source blockers clear; yes for spread only as an as-of context covariate; no for close-side cost, synthetic path-R, or broker actual-R in this lifecycle-only prereg.

## Controlling Evidence Read

- `research/science_program_2026_05/04_goal_prompts/G8_G8_OPTIONS_VOL_GOAL_PROMPT_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G8_OPTIONS_VOL_DOMAIN_SYNTHESIS_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G10_EXECUTION_RISK_DOMAIN_SYNTHESIS_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G11_DATA_SOURCES_EXPANSION_SYNTHESIS_2026-05-06.md`
- `research/operations/COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-05.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md`

## Frozen Experiment Row

Machine-readable prereg sidecar:

- `research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json`

Key fields:

- `experiment_id`: `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001`
- `hypothesis_id`: `HYP-G8-VIX1D9D-STRESS-002`
- `outcome_review_opened`: `false`
- Primary label class: `lifecycle_no_fill`
- Primary cohort: future/prospective `NAS100`, `US30`, and `US30_cash` lifecycle rows
- Primary metric: pending-limit lifecycle outcome rates by preregistered VIX1D/VIX9D context state
- Minimum floor: `250` deduped lifecycle rows and at least `40` rows per short-vol bucket

## Join Decision Matrix

| Join | Decision | Rationale |
|---|---|---|
| VIX1D/VIX9D context -> pending-limit lifecycle no-fill rows | Allowed only after blockers clear | This preserves the G8 hypothesis label class `lifecycle_no_fill` and G10 pending/prefill lifecycle labels. Cboe source rows must be proven available before candidate context time. |
| VIX1D/VIX9D context -> same-day intraday candidate rows | Blocked by default | Cboe CSV same-day publication time is not proven. Until it is, same-day joins are leaky unless a documented `publication_asof_utc <= candidate_decision_time_utc` exists. |
| VIX1D/VIX9D context -> spread rows | Allowed as context only | Decision-time or request-time spread can be a covariate if timestamped before or at lifecycle capture. It is not a PnL/cost label in this prereg. |
| VIX1D/VIX9D context -> close-side cost rows | Blocked in this prereg | Close-side slippage/cost coverage is currently missing and belongs to a separate broker_actual_r or cost prereg. |
| VIX1D/VIX9D context -> synthetic path-R rows | Blocked in this prereg | Synthetic path-R is a separate label family and cannot be averaged or ranked with lifecycle no-fill. |
| VIX1D/VIX9D context -> broker actual-R rows | Blocked in this prereg | Broker actual-R evidence is sparse and must remain under a separate actual-R prereg. |
| G11 friction gate fields -> CD2-02 features | Blocked pending G12 cleanup | G0 flagged `HYP-G11-FRICTION-GATE-007` no-leak fields as semantic inversion risk. Use G11 only as source/friction-readiness context here. |

## Required Fields

Short-vol context:

- `source_id`
- `source_row_date`
- `source_cached_at_utc`
- `publication_asof_utc`
- `vix1d_close_asof`
- `vix9d_close_asof`
- `vix1d_minus_vix9d_asof`
- `join_mode`: `previous_trading_day` or `same_day_verified`
- `source_stale_or_unverified_flag`

Lifecycle row:

- `setup_id` or `trade_id`
- `symbol`
- `session`
- `candidate_decision_time_utc` or `decision_asof_utc`
- `pending_created_utc`
- `source_capture_utc`
- `lifecycle_state_before_outcome`
- `fill_no_fill_label`
- `broker_fill_state`
- `order_send_attempted`
- `order_send_success`
- `fill_time_utc`
- `spread_timestamp_utc`
- `spread_asof`
- `same_bar_or_path_ambiguity_flag`

## Label Separation Rules

1. The primary table may contain only lifecycle labels and as-of context fields.
2. Spread is allowed only as an as-of context or covariate, never as close-side cost or broker actual-R.
3. Entry slippage is a child diagnostic only after an observed order attempt.
4. Close-side slippage, commission, swap, close deal price, and broker actual-R are excluded from this prereg.
5. Synthetic path-R is excluded from this prereg and needs a separate frozen experiment if reopened.
6. G11 friction-gate rows cannot be consumed as valid no-leak feature definitions until G12 resolves the semantic inversion blocker.

## Non-Claims

- No validation result is produced.
- No outcome review is opened.
- No source is marked validation-safe.
- No live trading prompt, risk, execution, permissions, safety gate, selector, MT5, canary, paid-data, credential, remote, or order behavior is changed.
- This prereg does not approve a short-vol filter, execution filter, or cost model.

Final verdict: `NO_PROMOTION_VERDICT`.
