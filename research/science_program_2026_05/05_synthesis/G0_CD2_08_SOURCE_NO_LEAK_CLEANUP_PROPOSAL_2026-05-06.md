# G0 CD2-08 Source / No-Leak Cleanup Proposal - 2026-05-06

**Lane:** `G0`  
**Assignment:** `CD2-08 - Source/no-leak field cleanup pass`  
**Status:** `G0_ROW_CLEANUP_PROPOSAL_READY_FOR_G12_REVIEW`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**HEAD inspected:** `48389494`  

This is a G0-owned cleanup proposal only. It does not edit master registries, mark any source validation-safe, open outcomes, or change live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid data, credentials, remote state, or order behavior.

## Objective Restated

Produce a row-cleanup proposal for G12 review that separates:

- real `source_contract_v2.source_id` references,
- literature or local context references,
- future placeholders and cross-lane hypothesis dependencies,
- forbidden outcome/future field lists currently placed in `no_leak_fields`.

Scope is limited to:

- all `HYP-G11-*` rows,
- `HYP-G7-XG5-MACRO-ATTN-010`,
- `HYP-G7-XG8-VOL-MACRO-011`,
- `HYP-G7-XG11-SOURCE-FRESH-012`.

## Inputs Read

- `research/science_program_2026_05/04_goal_prompts/G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.json`
- `research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md`
- `research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.md`
- `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json`
- `research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G7_MACRO_CROSS_ASSET_HYPOTHESIS_ROWS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G5_HYPOTHESIS_ROWS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G5_SOURCE_CONTRACT_ROWS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G8_OPTIONS_VOL_SOURCE_CONTRACT_ROWS_2026-05-06.json`
- `research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json`

## Evidence Summary

- `science_hypothesis_v1.no_leak_fields` is defined as decision-time/as-of feature names, not excluded outcome fields.
- Master registry state at inspected HEAD: `96` hypotheses, `86` source contracts, `0` source contracts with `validation_safe=true`, and `0` survivor backlog rows.
- G0 wave-2 reconciliation records `8` no-leak semantic blockers, all G11 hypothesis rows where forbidden outcome/future fields appear under `no_leak_fields`.
- Target-row scan found `11` scoped rows:
  - `8` G11 rows with suspect `no_leak_fields`.
  - `3` G7 cross-domain rows with unresolved `source_ids`: one hypothesis ID and two future placeholders.
- All proposed source IDs below already exist as `source_contract_v2` rows. All remain `validation_safe=false`.

## Cleanup Rules Proposed For G12

1. `source_ids` should contain only concrete IDs that resolve to rows in `SOURCE_CONTRACT_REGISTRY_2026-05-06.json`.
2. Literature IDs such as `LIT-G5-*` should move to `evidence_refs` or be represented only through `SRC-G5-ACADEMIC-LIT-001` when a source-contract row is required for mechanism-context documentation.
3. Hypothesis IDs such as `HYP-G5-XG7-MACRO-ATTN-009` should move to `neighbor_lane_dependency`, not `source_ids`.
4. Future placeholders such as `future_G8_options_vol_rows` and `future_G11_source_governance_rows` should move to `blocked_dependency_refs` or `neighbor_lane_dependency` until replaced by explicit source-contract rows.
5. `no_leak_fields` should be a whitelist of decision-time/as-of feature names. Current forbidden outcome/future names should move to a red-team-only note such as `forbidden_outcome_fields_for_g12_review`. If G12 does not want a schema extension, keep those names inside `promotion_blockers` / `test_method` wording and remove them from `no_leak_fields`.
6. `validation_safe` must remain `false` for every referenced source unless a later source-specific blocker-clearing dossier exists.

## G11 Row Cleanup Proposals

### `HYP-G11-PROVENANCE-GATE-001`

- Current issue: `no_leak_fields` contains `outcome_r`, `win_loss`, `future_price`, `post_entry_path`, and `trade_result`.
- Proposed `no_leak_fields`: `source_id`, `source_contract_version`, `source_cache_path`, `source_cache_time_utc`, `capture_timestamp_utc`, `publication_asof_rule_id`, `access_legal_state_asof`, `allowed_feature_role_asof`, `validation_safe_flag_asof`, `blocker_count_asof`, `review_freeze_timestamp_utc`.
- Proposed `source_ids`: `SRC-G11-LOCAL-G0-REGISTRIES`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-COVERAGE-GATE-002`

- Current issue: `no_leak_fields` contains `actual_r`, `trade_outcome`, `future_return`, and `post_signal_continuation`.
- Proposed `no_leak_fields`: `candidate_symbol`, `coverage_manifest_date_utc`, `broker_actual_history_days_asof`, `external_proxy_history_days_asof`, `session_window_coverage_asof`, `missingness_rate_asof`, `source_family_count_asof`, `friction_manifest_available_asof`, `candidate_registry_freeze_timestamp_utc`, `coverage_gate_version`.
- Proposed `source_ids`: `SRC-G11-LOCAL-INSTRUMENT-EXPANSION`, `SRC-G11-OBSERVER-SOURCE-REGISTRY`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-SOURCE-TRANSFER-003`

- Current issue: `no_leak_fields` contains `actual_r`, `take_profit_hit`, `stop_loss_hit`, and `post_entry_path`.
- Proposed `no_leak_fields`: `symbol`, `broker_source_id`, `proxy_source_id`, `date_block_id`, `alignment_window_start_utc`, `alignment_window_end_utc`, `timestamp_alignment_rule_id`, `cross_corr_asof`, `lead_lag_seconds_asof`, `missingness_rate_asof`, `spread_divergence_asof`, `rollover_state_asof`, `source_transfer_gate_version`.
- Proposed `source_ids`: `SRC-G11-SIERRA-SCID-DEPTH`, `SRC-G11-DATABENTO-GLBX-MDP3`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-PUBLIC-LAG-004`

- Current issue: `no_leak_fields` contains `post_release_revision`, `future_release_value`, `actual_r`, and `trade_outcome`.
- Proposed `no_leak_fields`: `source_id`, `series_id`, `observation_period_end_utc`, `release_timestamp_utc`, `source_cache_time_utc`, `decision_timestamp_utc`, `release_lag_hours_asof`, `vintage_id_asof`, `join_rule_id`, `stale_source_flag_asof`.
- Proposed `source_ids`: `SRC-G11-PUBLIC-CFTC-FRED-BIS`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-OPTIONS-VOL-005`

- Current issue: `no_leak_fields` contains `future_vol_index`, `post_event_outcome`, `actual_r`, and `trade_result`.
- Proposed `no_leak_fields`: `source_id`, `instrument_family`, `vol_index_symbol`, `vol_source_publication_timestamp_utc`, `source_cache_time_utc`, `license_state_asof`, `history_coverage_days_asof`, `gex_source_state_asof`, `vrp_formula_version_asof`, `timestamp_rule_verified_asof`, `decision_timestamp_utc`.
- Proposed `source_ids`: `SRC-G11-CBOE-OPTIONS-VOL`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-OBSERVER-EXPANSION-006`

- Current issue: `no_leak_fields` contains `actual_r`, `win_loss`, `post_signal_path`, and `tp_sl_hit`.
- Proposed `no_leak_fields`: `observer_symbol`, `observer_day_utc`, `observer_enabled_state_asof`, `source_freshness_state_asof`, `spread_atr_burden_asof`, `session_eligibility_state_asof`, `lifecycle_log_coverage_asof`, `selector_disabled_flag_asof`, `outcome_review_opened_flag_asof`, `observer_registry_version`.
- Proposed `source_ids`: `SRC-G11-OBSERVER-SOURCE-REGISTRY`, `SRC-G11-LOCAL-INSTRUMENT-EXPANSION`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11-FRICTION-GATE-007`

- Current issue: `no_leak_fields` contains `future_return`, `actual_r`, `post_entry_path`, and `trade_result`.
- Proposed `no_leak_fields`: `symbol`, `friction_manifest_time_utc`, `spread_atr_percentile_asof`, `min_lot_size_asof`, `tick_value_asof`, `session_density_asof`, `weekend_gap_policy_state_asof`, `contract_spec_timestamp_utc`, `candidate_registry_freeze_timestamp_utc`, `friction_gate_version`.
- Proposed `source_ids`: `SRC-G11-LOCAL-INSTRUMENT-EXPANSION`, `SRC-G11-OBSERVER-SOURCE-REGISTRY`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

### `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008`

- Current issue: `no_leak_fields` contains `actual_r`, `trade_result`, `post_entry_path`, and `future_orderflow`.
- Proposed `no_leak_fields`: `proposed_experiment_id`, `source_id`, `source_contract_version`, `schema_name`, `timestamp_provenance_state_asof`, `proxy_transfer_status_asof`, `label_separation_status_asof`, `budget_approval_state_asof`, `live_license_state_asof`, `g4_feature_field_name`, `g11_gate_version`, `review_timestamp_utc`.
- Proposed `source_ids`: `SRC-G11-SIERRA-SCID-DEPTH`, `SRC-G11-DATABENTO-GLBX-MDP3`, `SRC-G11-AUCTION-NASDAQ-LBMA`, `SRC-G4-DATABENTO-GLBX-MDP3`, `SRC-G4-SIERRA-DEPTH-SCID`, `SRC-G4-NASDAQ-NOII-CROSSES`, `SRC-G4-LBMA-ICE-AUCTION`.
- Move current field list to `forbidden_outcome_fields_for_g12_review`.

## G7 Cross-Domain Row Cleanup Proposals

### `HYP-G7-XG5-MACRO-ATTN-010`

- Current `no_leak_fields` are already as-of feature names; no no-leak rename is proposed in CD2-08.
- Current unresolved `source_ids`: `HYP-G5-XG7-MACRO-ATTN-009`.
- Proposed `source_ids`: keep `SRC-G7-FED-FOMC-001`, `SRC-G7-LOCAL-GTOS-MACRO-001`, `SRC-G5-NEWS-CALENDAR-LOCAL-001`.
- Proposed dependency move: `HYP-G5-XG7-MACRO-ATTN-009` -> `neighbor_lane_dependency`.
- G5 literature references connected to the dependency row (`LIT-G5-FOMC-001`, `LIT-G5-FOMC-DECAY-001`) should remain outside `source_ids`; put them in `evidence_refs` or route them through `SRC-G5-ACADEMIC-LIT-001` as context-only mechanism evidence.

### `HYP-G7-XG8-VOL-MACRO-011`

- Current `no_leak_fields` are already as-of feature names; no no-leak rename is proposed in CD2-08.
- Current unresolved `source_ids`: `future_G8_options_vol_rows`.
- Proposed `source_ids`: keep `SRC-G7-FRED-RATES-001`, `SRC-G7-ICE-DXY-001`; add `SRC-G8-CBOE-VOL-CSV-001`, `SRC-G8-VRP-FORMULA-005`.
- Proposed dependency move: `future_G8_options_vol_rows` -> `blocked_dependency_refs` with explicit dependencies on G8 hypothesis rows such as `HYP-G8-VIX1D9D-STRESS-002`, `HYP-G8-VRP-004`, and `HYP-G8-VVIX-TAIL-007`.
- Keep all G8 source blockers intact: Cboe publication timestamp unknown, parser/no-lookahead tests missing, formula not frozen, and validation-safe remains false.

### `HYP-G7-XG11-SOURCE-FRESH-012`

- Current `no_leak_fields` are already source-governance as-of feature names; no no-leak rename is proposed in CD2-08.
- Current unresolved `source_ids`: `future_G11_source_governance_rows`.
- Proposed `source_ids`: keep `SRC-G7-LOCAL-GTOS-MACRO-001`; add `SRC-G11-LOCAL-G0-REGISTRIES`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`, `SRC-G11-PUBLIC-CFTC-FRED-BIS`.
- Proposed dependency move: `future_G11_source_governance_rows` -> `blocked_dependency_refs` or `neighbor_lane_dependency` with explicit dependencies on `HYP-G11-PROVENANCE-GATE-001` and `HYP-G11-PUBLIC-LAG-004`.
- Keep all G11 source blockers intact: release-aware joins missing, macro cadence too slow for direct M15/H1 role, and validation-safe remains false.

## Literature Reference Cleanup Around G5

G0 wave-2 reconciliation flagged G5 literature IDs such as `LIT-G5-AMH-001`, `LIT-G5-PRED-001`, `LIT-G5-FOMC-001`, and `LIT-G5-FOMC-DECAY-001` because they are not `source_contract_v2` rows. The cleanup proposal is:

- Do not treat `LIT-G5-*` as decision-time market sources.
- Move `LIT-G5-*` values out of `source_ids` into `evidence_refs` on the owning G5 mechanism/hypothesis rows.
- If a registry-resolving source ID is needed for literature context, use the existing `SRC-G5-ACADEMIC-LIT-001` source contract, which remains context-only and `validation_safe=false`.
- Do not inherit G5 literature IDs into G7 cross-domain `source_ids`.

## G12 Review Questions

1. Should `forbidden_outcome_fields_for_g12_review` become an optional schema field, or should forbidden examples live only in `promotion_blockers` / `test_method` language?
2. Should G12 prefer `neighbor_lane_dependency` for hypothesis IDs and `blocked_dependency_refs` for future placeholders, or a single dependency field?
3. Should G11 rows add `source_ids` in the next registry cleanup, even though `science_hypothesis_v1` does not require that field?
4. Should `SRC-G5-ACADEMIC-LIT-001` be the only registry-resolving source ID for G5 literature references, with individual `LIT-G5-*` IDs kept in `evidence_refs`?

## Non-Actions Confirmed

- No master registry row was edited.
- No source contract was marked `validation_safe=true`.
- No source validation, parser, cache, no-lookahead, or publication-time test was changed.
- No outcome review was opened.
- No live trading prompt, risk, execution, permissions, selector, safety gate, MT5, canary, paid-data, credential, remote, or order behavior file was touched.

## Proposal Checklist

| Requirement | Evidence in this proposal |
| --- | --- |
| Use G0 controlling prompt and CD2 assignment | Inputs Read section lists both controlling files. |
| Read current HEAD `48389494` | Header records inspected HEAD; preflight confirmed it. |
| Read master registries and wave-2 reconciliation | Inputs Read and Evidence Summary list master registry and wave-2 artifacts. |
| Read relevant G11/G7/G5/G12 guidance | Inputs Read lists G11/G7/G5/G12 artifacts used. |
| Cover all `HYP-G11-*` rows | G11 Row Cleanup Proposals covers 8 G11 target rows. |
| Cover the three named G7 rows | G7 Cross-Domain Row Cleanup Proposals covers all 3 named rows. |
| Separate real source contracts from literature refs and placeholders | Cleanup Rules, G7 rows, and Literature Reference Cleanup sections do this. |
| Separate forbidden outcome fields from `no_leak_fields` | Every G11 row has replacement `no_leak_fields` and a move target for forbidden fields. |
| Preserve `NO_PROMOTION_VERDICT` | Header and sections state no promotion and no validation-safe changes. |
| Produce proposal only | Non-Actions Confirmed states no registry/source-validation edits. |
