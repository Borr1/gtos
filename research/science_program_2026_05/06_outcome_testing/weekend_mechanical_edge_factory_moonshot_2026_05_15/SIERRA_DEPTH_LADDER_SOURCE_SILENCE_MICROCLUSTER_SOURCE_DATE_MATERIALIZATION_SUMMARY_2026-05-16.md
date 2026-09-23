# Sierra Source-Silence Microcluster Source-Date Materialization

Generated UTC: `2026-05-16T01:42:47Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source-date materialization/acquisition routing only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `source_join_input_rows`: `10382`
- `proxy_target_input_rows`: `23`
- `exact_feature_control_rows`: `831`
- `group_split_input_rows`: `27225`
- `split_acquisition_input_rows`: `253`
- `weakening_source_date_input_rows`: `31`
- `source_date_materialization_rows`: `31`
- `source_date_pool_rows`: `154`
- `source_date_acquisition_rows`: `155`
- `source_date_spec_rows`: `17`
- `bucket_rows`: `15`
- `question_rows`: `203`

## Spec Status

- `SPEC_SOURCE_DATE_HAS_WEAKENING_MATERIALIZATION`: `13`
- `SPEC_SOURCE_DATE_ONLY_CARRIED_NON_EXACT_ACQUISITION`: `4`

## Same-Resource Continuation

- Execute local-depth replay/proxy for carried non-exact local-depth rows.
- Search/acquire exact `.depth` source-date files for carried route-C proxy rows.
- Broaden source/proxy denominators for target-only and source-underpowered rows.
- Carry source-date materialized rows into the next split/proxy packet without waiting.
