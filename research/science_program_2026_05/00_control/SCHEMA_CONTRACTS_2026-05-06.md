# Science Program Schema Contracts - 2026-05-06

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## science_mechanism_v1

Required fields:

- `mechanism_id`
- `science_domain`
- `market_behavior`
- `expected_signature`
- `required_data`
- `known_decay_mode`
- `existing_gtos_overlap`
- `killed_route_check`
- `promotion_verdict`

Field notes:

- `mechanism_id`: Stable ID, e.g. SCI-MICRO-OFI-001.
- `science_domain`: Primitive science source family, not a public trading-strategy label.
- `market_behavior`: Observable GTOS-relevant behavior the mechanism should create.
- `expected_signature`: Point-in-time signature expected before the decision/outcome.
- `required_data`: Exact source rows required to observe it.
- `known_decay_mode`: Why the effect may vanish, crowd, reverse, or become regime-specific.
- `existing_gtos_overlap`: Active, shadow, killed, blocked, or untested GTOS route.
- `killed_route_check`: Artifact/grep/handoff check proving this is not reopening a killed route.

## science_hypothesis_v1

Required fields:

- `hypothesis_id`
- `mechanism_id`
- `null`
- `alternative`
- `symbols`
- `timeframes`
- `entry_or_filter_or_exit_role`
- `label_class`
- `no_leak_fields`
- `sample_floor`
- `test_method`
- `promotion_blockers`
- `promotion_verdict`

Field notes:

- `null`: Concrete null that can fail without subjective interpretation.
- `alternative`: Expected direction and cohort where the mechanism should help.
- `label_class`: One of broker_actual_r, synthetic_path_r, lifecycle_no_fill, observation_only, or context_only.
- `no_leak_fields`: Feature names that are decision-time/as-of only.
- `sample_floor`: Minimum n/effective-N before any result can be accepted.
- `promotion_blockers`: Reasons this cannot leave research/shadow status.

## experiment_prereg_v1

Required fields:

- `experiment_id`
- `hypothesis_id`
- `frozen_at_utc`
- `outcome_review_opened`
- `metric`
- `cohort`
- `exclusions`
- `duplicate_policy`
- `cost_slippage_assumptions`
- `dsr_pbo_effective_n_policy`
- `label_separation_policy`
- `reproducibility_key`
- `promotion_verdict`

Field notes:

- `frozen_at_utc`: Must be present before outcome review.
- `outcome_review_opened`: Must be false at registration time.
- `duplicate_policy`: How repeated setup/path rows are deduped.
- `dsr_pbo_effective_n_policy`: DSR/PBO/effective-N calculation or not_computable reason.
- `label_separation_policy`: Prevents broker actual-R, synthetic path-R, lifecycle, and observation labels from mixing.

## source_contract_v2

Required fields:

- `source_id`
- `url_or_vendor`
- `access_legal_state`
- `cost_rule`
- `publication_asof_timestamp_rule`
- `cache_path`
- `allowed_feature_role`
- `validation_safe`
- `validation_safe_blockers`
- `promotion_verdict`

Field notes:

- `publication_asof_timestamp_rule`: Exact publication/as-of convention; report date alone is not enough for macro sources.
- `allowed_feature_role`: Decision-time feature, context-only, forensic-only, or blocked.
- `validation_safe`: False until source legality, timestamp, cache, parser, and no-lookahead tests pass.

## goal_status_v1

Required fields:

- `lane_id`
- `lane_status`
- `files_written`
- `tests_run`
- `blockers`
- `next_questions`
- `commit_sha`
- `promotion_verdict`

Field notes:

- `commit_sha`: Set after scoped commit in the lane worktree; null while not run.
- `promotion_verdict`: Always NO_PROMOTION_VERDICT unless a separate owner-approved promotion dossier exists.

## Enforcement Notes

- `source_contract_v2.validation_safe` must stay false while access/legal state is blocked, paid approval is missing, or blockers remain.
- `experiment_prereg_v1.outcome_review_opened` must be false when frozen.
- `science_hypothesis_v1.label_class` must keep broker actual-R, synthetic path-R, lifecycle/no-fill, observation-only, and context-only labels separated.
- Every row carries `NO_PROMOTION_VERDICT`.
