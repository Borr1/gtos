# G7 CD2-01 Prereg Update Proposal - 2026-05-06

**Lane:** `G7`  
**Assignment:** `CD2-01 - Macro-vol-source freshness triad`  
**Status:** `PREREG_UPDATE_PROPOSAL_ONLY_NO_MASTER_EDIT`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

This proposal translates the CD2-01 compatibility ledger into concrete future edits for G0/G12 review. G7 does not edit the master registry, lane registries, source contracts, or validation state here. Every proposed row remains outcomes-closed and research-only.

## Proposal Boundary

| Boundary | Frozen decision |
|---|---|
| Registry ownership | G0/G12 or a later explicitly assigned owner must apply any accepted row edit. G7 writes this proposal only. |
| Validation state | All source contracts remain `validation_safe=false`. |
| Outcome state | All experiment preregs remain `outcome_review_opened=false`. |
| Label state | Source-freshness audits are `context_only` or `observation_only`; no broker actual-R, synthetic path-R, lifecycle/no-fill, or trade-outcome labels are opened. |
| Promotion state | `NO_PROMOTION_VERDICT` stays mandatory. |

## Proposed Hypothesis Row Updates

### `HYP-G7-XG8-VOL-MACRO-011`

**Current issue:** G7 wrote this as a placeholder blocked until G8 outputs existed. G8 now has rows, but Cboe vol-index and VRP source timing remain unresolved.

**Proposed replacement fields:**

| Field | Proposed value |
|---|---|
| `entry_or_filter_or_exit_role` | `cross_domain_research_context_only_source_freshness_blocked` |
| `label_class` | `context_only` until source timing passes; later synthetic/path labels require separate outcome prereg. |
| `no_leak_fields` | `candidate_decision_timestamp_utc`, `macro_source_id`, `macro_source_publication_timestamp_utc`, `macro_feature_asof_utc`, `vol_source_id`, `vol_source_publication_timestamp_utc`, `vol_feature_asof_utc`, `source_cache_time_utc`, `parser_version`, `source_hash`, `symbol`, `session`, `side`. |
| `sample_floor` | `Source audit first: 100% as-of pass over joined macro and vol source rows before any outcome review. Later interaction cohort requires >=500 deduped multi-symbol rows, >=80 vol-macro stress rows, effective_N >=3, and chronological folds.` |
| `test_method` | `Build source-freshness join manifest first. Exclude observation-date-only COT/FRED/BIS rows, Cboe same-day daily rows without official publication time, and VRP rows whose realized window overlaps the decision. Only after source audit passes may a separate outcome prereg compare interaction cohorts.` |
| `promotion_blockers` | `G7 FRED cache absent`, `BIS exact table not selected`, `COT release-aware FX mapping unresolved`, `Cboe publication timestamp unknown`, `VRP formula/no-lookahead not frozen`, `source_contract_v2 validation_safe=false`, `no live risk gate change`. |
| `source_ids` | `SRC-G7-CFTC-COT-001`, `SRC-G7-BIS-STATS-001`, `SRC-G7-FRED-RATES-001`, `SRC-G8-CBOE-VOL-CSV-001`, `SRC-G8-VRP-FORMULA-005`, `SRC-G11-PUBLIC-CFTC-FRED-BIS`, `SRC-G11-CBOE-OPTIONS-VOL`. |

### `HYP-G7-XG11-SOURCE-FRESH-012`

**Current issue:** G7 source IDs refer to future G11 governance rows because G11 had not completed.

**Proposed replacement fields:**

| Field | Proposed value |
|---|---|
| `mechanism_id` | Keep `G7-MECH-BIS-FX-CARRY-005` unless G0 creates a dedicated source-governance mechanism. |
| `entry_or_filter_or_exit_role` | `source_governance_dependency_only` |
| `label_class` | `observation_only` |
| `no_leak_fields` | `source_id`, `source_contract_version`, `source_publication_timestamp_utc`, `source_observation_timestamp_utc`, `source_cache_time_utc`, `source_hash`, `parser_version`, `decision_timestamp_utc`, `g11_rule_version`, `freshness_status`, `exclusion_bucket`. |
| `sample_floor` | `Audit 100% of G7 macro source-contract rows and every future candidate source row before outcome review; no return sample floor because this is source governance.` |
| `test_method` | `Apply G11 source-governance compatibility rules to each G7 macro source contract and candidate normalized source row. Report retained/excluded counts only, grouped by source family and exclusion bucket. Do not join to outcome labels.` |
| `promotion_blockers` | `All G7/G11 source contracts validation_safe=false`, `source audit only`, `no outcome labels`, `G11 no_leak field cleanup pending`, `no parser/cache/no-lookahead tests yet`. |
| `source_ids` | `SRC-G7-LOCAL-GTOS-MACRO-001`, `SRC-G11-LOCAL-G0-REGISTRIES`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`, `SRC-G11-PUBLIC-CFTC-FRED-BIS`, `SRC-G11-CBOE-OPTIONS-VOL`. |

### `HYP-G11-PUBLIC-LAG-004`

**Current issue:** G0 flagged G11 no-leak semantics. The current `no_leak_fields` list names forbidden outcome/future fields rather than decision-time/as-of feature fields.

**Proposed replacement fields:**

| Field | Proposed value |
|---|---|
| `no_leak_fields` | `source_id`, `series_id`, `source_family`, `observation_date`, `reporting_period_end_utc`, `source_release_timestamp_utc`, `first_available_utc`, `vintage_timestamp_utc`, `cache_time_utc`, `source_hash`, `parser_version`, `decision_timestamp_utc`, `feature_asof_utc`. |
| `test_method` | `Build two source-feature tables: observation-date join and release-aware join. Compare coverage and regime-context deltas only; do not read trade outcomes or actual R.` |
| `promotion_blockers` | Add `current no_leak field semantics require G12 cleanup before registry edit`; retain release-aware join and killed COT-route blockers. |

### `HYP-G8-VRP-004`

**Current issue:** VRP is preregistered but formula/source timing is not frozen. CD2-01 needs a strict rule before any macro-vol interaction can depend on VRP.

**Proposed replacement fields:**

| Field | Proposed value |
|---|---|
| `no_leak_fields` | Keep existing fields and add `implied_source_id`, `implied_source_publication_timestamp_utc`, `implied_source_cache_time_utc`, `realized_variance_source_id`, `realized_variance_window_id`, `vrp_formula_version`, `source_hash`, `parser_version`. |
| `sample_floor` | `Formula/source audit first with 100% no-lookahead pass. Later outcome review requires >=400 deduped candidate rows, >=80 per instrument family, effective_N >=3, and formula locked before outcomes open.` |
| `test_method` | `Freeze implied source, realized estimator, tenor mapping, annualization, source as-of rule, and realized-window boundary before any candidate outcome join. Exclude rows where implied source is same-day date-only Cboe data without publication proof or realized window ends after decision.` |
| `promotion_blockers` | Retain all current blockers and add `Cboe daily CSV same-day publication unknown` and `macro-vol interaction cannot use VRP until formula source audit passes`. |

## Proposed Experiment Prereg Updates

### `EXP-G7-XG8-VOL-MACRO-011`

| Field | Proposed value |
|---|---|
| `metric` | `Phase 0 source audit: macro/vol retained-row count, exclusion-bucket count, and as-of pass rate. Phase 1 outcome metric remains closed until source audit passes and a separate outcome prereg is approved.` |
| `cohort` | `Candidate source rows with both G7 macro context and G8 volatility context after CD2-01 source-freshness fields are present. No outcome rows included in Phase 0.` |
| `exclusions` | `Observation-date-only COT/FRED/BIS rows`, `FRED/BIS revised values without vintage`, `Cboe daily same-day intraday joins without official publication timestamp`, `VRP rows with realized-window overlap`, `rows missing cache hash/parser version`, `any live risk gate edit`. |
| `duplicate_policy` | `One source-audit row per source_id, source_version, decision_timestamp_utc, symbol, setup_id, and cache_hash; later outcome rows cluster by vol-macro episode/day/symbol.` |
| `dsr_pbo_effective_n_policy` | `Phase 0 source audit: not_computable. Later outcome review requires effective_N >=3, chronological folds, and G1 DSR/PBO rules if a performance claim is attempted.` |
| `label_separation_policy` | `Source audit rows are context_only/observation_only. Options/vol context, macro context, synthetic_path_r, lifecycle_no_fill, and broker_actual_r remain separate experiments.` |
| `reproducibility_key` | `EXP-G7-XG8-VOL-MACRO-011|CD2-01_source_audit_v1|outcomes_closed|NO_PROMOTION_VERDICT` |

### `EXP-G7-XG11-SOURCE-FRESH-012`

| Field | Proposed value |
|---|---|
| `metric` | `retained_source_rows`, `excluded_source_rows_by_bucket`, `source_contract_field_completeness`, `publication_asof_rule_coverage`, `cache_hash_coverage`; no performance metric. |
| `cohort` | `All G7 source contracts plus future G7 macro source rows after G11 source-governance fields are available.` |
| `exclusions` | `source without publication timestamp`, `source without cache path/hash`, `legal/access unresolved`, `source_id placeholder`, `no parser version`, `any outcome label`. |
| `duplicate_policy` | `One audit row per source_id, source_contract_version, cache_hash, parser_version, and decision_time bucket; superseded cache versions retained as stale_not_used.` |
| `dsr_pbo_effective_n_policy` | `Not applicable; report not_computable because this is source-governance retained/excluded counting only.` |
| `label_separation_policy` | `Observation_only source-governance labels contain no outcome fields and cannot be pooled with return labels.` |
| `reproducibility_key` | `EXP-G7-XG11-SOURCE-FRESH-012|CD2-01_G11_source_governance_v1|outcomes_closed|NO_PROMOTION_VERDICT` |

### `EXP-G11-PUBLIC-LAG-004`

| Field | Proposed value |
|---|---|
| `metric` | `observation_date_vs_release_asof_feature_delta`, `coverage_delta`, `freshness_exclusion_count`; no trade outcome metric. |
| `cohort` | `CFTC, FRED, and BIS features with observation dates plus release/as-of or vintage timestamps. Rows lacking release/as-of are source-blocked, not silently dropped after outcome review.` |
| `exclusions` | `series lacking release/as-of timestamp`, `revised values without vintage dates`, `cache after decision without historical as-of proof`, `any row joined to trade outcome`. |
| `duplicate_policy` | `Deduplicate by source_id, series_id, observation_date, release_timestamp, vintage_timestamp, parser_version, and cache_hash.` |
| `label_separation_policy` | `Regime/source context only; do not read actual R, synthetic path-R, lifecycle/no-fill outcome, win/loss, or trade outcome.` |

### `EXP-G8-VRP-004`

| Field | Proposed value |
|---|---|
| `metric` | `Formula reproducibility, implied-source as-of pass rate, realized-window no-lookahead pass rate, tenor/annualization completeness, and source coverage. Candidate outcomes remain closed.` |
| `cohort` | `Index/metals candidate context timestamps with implied-vol row first-available before context time and realized-variance window ending strictly before decision time.` |
| `exclusions` | `Cboe daily same-day row without publication proof`, `realized window includes decision or later bars`, `unknown annualization`, `unknown tenor mapping`, `missing source hash`, `missing volatility baseline controls`. |
| `duplicate_policy` | `For formula audit, one row per formula_version, source_id, realized_window_id, and decision timestamp; later candidate joins dedupe by active setup lifecycle and cluster by calendar block.` |
| `dsr_pbo_effective_n_policy` | `Formula audit not_computable. Any later model ablation requires DSR, PBO, and effective-N after duplicate/time clustering; blocked if formula changed after outcome review opened.` |
| `reproducibility_key` | `EXP-G8-VRP-004|CD2-01_vrp_formula_source_audit_v1|outcomes_closed|NO_PROMOTION_VERDICT` |

## Source Contract Update Proposals

These are not source-contract edits. They are fields a later source-contract owner should add or verify before any `validation_safe` change.

| Source | Required additions before review |
|---|---|
| `SRC-G7-CFTC-COT-001` | `release_schedule_url`, `release_timestamp_utc`, `us_eastern_timezone_conversion_rule`, `holiday_release_override`, `contract_mapping_version`, `cache_hash`, `parser_version`. |
| `SRC-G7-FRED-RATES-001` | Successful raw cache; `series_id`; `release_id`; `release_timestamp_utc`; `vintage_timestamp_utc` or ALFRED/realtime fields; `daily_close_availability_rule`; `cache_hash`; `parser_version`. |
| `SRC-G7-BIS-STATS-001` | Exact BIS dataflow/table/series; `release_date`; revision/vintage policy; date-only intraday block rule; SDMX/bulk parser; `cache_hash`; `parser_version`. |
| `SRC-G8-CBOE-VOL-CSV-001` | License/internal-use review; official or conservative publication timing rule; CSV parser; symbol/index mapping; same-day intraday block test; `cache_hash`; `parser_version`. |
| `SRC-G8-VRP-FORMULA-005` | `vrp_formula_version`; implied source priority; realized estimator; tenor mapping; annualization; no-lookahead test manifest; formula freeze timestamp. |
| `SRC-G11-PUBLIC-CFTC-FRED-BIS` | Correct no-leak field semantics; release-aware source manifest schema; retained/excluded bucket taxonomy. |
| `SRC-G11-CBOE-OPTIONS-VOL` | Split public daily vol-index CSVs from paid/licensed GEX/option-chain routes; do not let public VIX/GVZ CSV existence imply aggregate GEX validation. |

## Acceptance Checklist For A Later Registry Edit

A future G0/G12-controlled registry update should not accept these proposals unless all checks below pass:

| Check | Required evidence |
|---|---|
| No placeholders | `future_G8_*` and `future_G11_*` references are replaced by actual `source_contract_v2` IDs or moved to evidence refs. |
| Correct no-leak fields | `no_leak_fields` list as-of feature fields only, not forbidden outcome fields. |
| Outcomes closed | Every affected prereg keeps `outcome_review_opened=false`. |
| Source safety unchanged | Every affected source remains `validation_safe=false` unless parser/cache/no-lookahead/legal blockers are explicitly cleared in a separate source review. |
| Publication/as-of fields present | Proposed rows include source publication timestamp, cache time, parser/hash, decision timestamp, and feature_asof rule. |
| Cboe same-day protected | Cboe daily rows cannot join same-day intraday decisions unless official publication timing is proven. |
| VRP no-lookahead protected | Realized-variance windows cannot include decision or post-decision bars. |
| Label separation preserved | Source audit, vol context, macro context, synthetic path-R, lifecycle/no-fill, and broker actual-R remain separate. |
| No live-surface change | No prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior touched. |
| Promotion boundary preserved | Every edited artifact carries `NO_PROMOTION_VERDICT`. |

## NO_PROMOTION_VERDICT

This proposal is a source-freshness prereg cleanup artifact only. It opens no outcomes, validates no lift, promotes no source, and changes no live trading behavior.
