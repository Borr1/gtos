# OTI2 Risk-Bank Method Freeze - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Outcome review opened:** `false`  
**Validation safe:** `false`  
**Frozen before synthetic path outcome inspection:** `true`

## Scope

This freeze applies only to the single G12-accepted OTB2R packet:

- Packet: `OTG0-PKT-013`
- Experiment: `G10-EXP-RISKBANK-005`
- Packet path: `research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json`
- Allowed records: `86`
- Allowed duplicate denominator: `86` unique `duplicate_group_id` values
- Forbidden packets: every other OTB2R packet and all blocked OTB2/OTB2R packets

## Frozen Prereg Metric

Source prereg: `research/science_program_2026_05/03_experiment_specs/G10_EXPERIMENT_PREREG_SPECS_2026-05-06.json`

Primary metric: `synthetic_path_r under invariant-respecting risk-bank re-entry`.

Safety metric: minimum aggregate worst-case R across all open/closed legs after estimated costs.

Risk-bank invariant:

```text
realized_closed_leg_r + sum(open_leg_stop_if_hit_r) - estimated_remaining_cost_r >= -1.0R
```

This result lane is descriptive only. It may not promote, validate, or change live trading behavior.

## Frozen Denominator And Duplicate Policy

The countable denominator is unique `duplicate_group_id`, not child legs, retries, path rows, or raw log rows.

Frozen denominator for this packet: `86/86` unique duplicate groups.

No row may be duplicated into an independent observation. Any duplicate-group drift discovered after outcome opening is a blocker and must be reported in the blocker ledger.

## Frozen Exclusions

Rows are excluded from any primary score if any of the following applies:

- packet row is not from `OTG0-PKT-013`;
- `duplicate_group_id` is missing or duplicated;
- source hash cannot be recomputed from sanitized source projections;
- coverage does not bind through `path_end_utc`;
- broker actual-R, live trade result, or blocked-packet outcome is required;
- leg-level risk-bank ledger cannot be derived or is internally inconsistent;
- risk-bank invariant is breached after estimated costs;
- same-bar terminal ordering is unresolved and no conservative lower-bound policy is available;
- unfilled re-entry legs are counted as filled.

Rows excluded from primary scoring may still appear in descriptive coverage and ambiguity ledgers.

## Frozen Same-Bar Ambiguity Rule

Terminal order claim allowed: `false`.

Same-minute or same-bar terminal ordering is never guessed. If the packet or path-order source marks `same_m1_ambiguity_flagged`, the primary terminal-order result is conservative-bounded or excluded from primary resolved scoring. It remains visible in ambiguity reporting.

## Frozen Cost And Slippage Assumptions

Cost model version: use the packet-level or row-level `cost_model_version`.

Cost accounting is synthetic-path-only:

- no broker actual-R;
- no account-history realized R;
- no live trade result labels;
- charge estimated remaining costs as declared by the frozen packet/projection evidence when available;
- if row-level numeric cost cannot be recovered from accepted local evidence, use `0.0R` for descriptive gross synthetic path summaries and mark net validation statistics `not_computable_due_missing_numeric_cost_ledger`.

## Frozen Sample-Floor Rule

The G10 risk-bank sample floor for validation-style statistics is `150` prospectively frozen resolved path rows after duplicate dedupe.

This packet has a frozen duplicate denominator of `86`, so validation-style claims are blocked unless a controlling artifact establishes a different pre-frozen floor before outcome opening. Descriptive quarantine summaries are still required.

## Frozen Label-Family Boundary

Primary label family: `synthetic_path_r`.

The result artifacts must not inspect, join, report, overwrite, or pool:

- `broker_actual_r`;
- account-history realized R;
- live trade outcomes;
- blocked-packet outcomes;
- lifecycle/no-fill rows as R labels.

Broker actual-R requires a separate future preregistration and is outside this lane.

## Frozen Not-Computable Criteria

Report exact `not_computable` reasons after exhausting packet evidence. These criteria are frozen before outcome inspection:

- `dsr_not_computable_no_unseen_validation_split`;
- `dsr_not_computable_effective_n_below_150_floor`;
- `pbo_not_computable_no_strategy_variant_matrix`;
- `pbo_not_computable_no_train_test_or_cpcv_blocks`;
- `validation_stats_not_computable_result_quarantined_discovery_only`;
- `net_metric_not_computable_missing_numeric_cost_ledger`;
- `primary_resolved_score_not_computable_unresolved_same_bar_terminal_ordering`.

Descriptive statistics may still be reported as quarantine/discovery summaries when the label family and packet boundary are respected.

## Non-Authorized Surfaces

This freeze authorizes no master-registry edit, `validation_safe=true` flip, `outcome_review_opened=true` flip, prompt edit, live risk edit, execution edit, selector edit, permissions/safety-gate edit, MT5 call, canary call, paid/API/Databento/network call, credential access, remote push, or order-behavior change.
