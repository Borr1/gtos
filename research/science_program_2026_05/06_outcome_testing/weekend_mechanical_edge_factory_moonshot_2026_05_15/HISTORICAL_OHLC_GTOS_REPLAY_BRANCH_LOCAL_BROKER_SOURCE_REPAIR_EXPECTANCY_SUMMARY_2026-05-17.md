# Broker Source Repair Expectancy

Generated UTC: `2026-05-17T11:39:43Z`

Branch-local broker/source repair and expectancy computation. This artifact consumes the numeric shadow scorer repair queue, rejoins numeric and matched-branch source rows, inventories local broker/account/lifecycle/trade sources, attempts direct exact-R joins, computes repaired proxy/expectancy summaries, and emits hard research-only implementation decisions. It does not place orders or change live behavior.

## Counts

- `input_numeric_result_rows`: `17916`
- `input_event_score_rows`: `17916`
- `input_repair_queue_rows`: `17753`
- `input_scope_score_rows`: `290`
- `input_branch_queue_rows`: `386`
- `input_accepted_branch_rows`: `386`
- `local_source_observation_rows`: `1355`
- `local_source_usable_exact_r_rows`: `22`
- `local_source_geometry_rows`: `1117`
- `repair_result_rows`: `17753`
- `exact_r_join_rows`: `17753`
- `exact_r_repaired_value_rows`: `0`
- `source_repaired_proxy_rows`: `17510`
- `source_repaired_proxy_added_from_branch_rows`: `6704`
- `branch_source_attached_rows`: `15917`
- `expectancy_summary_rows`: `1196`
- `implementation_decision_rows`: `290`
- `bucket_rows`: `25`
- `question_rows`: `4`
- `source_manifest_rows`: `164`

## Exact Join Status

- `EXACT_R_NOT_JOINABLE_NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER`: `17753`

## Implementation Decisions

- `IMPLEMENT_SCOPE_AVOID_OR_REDESIGN_FROM_REPAIRED_NEGATIVE_PROXY`: `154`
- `IMPLEMENT_SCOPE_DEFAULT_OFF_PROXY_SCORER_WITH_SOURCE_REPAIR_GUARDS`: `102`
- `SOURCE_OR_BROKER_GEOMETRY_REPAIR_REMAINS_REQUIRED_FOR_SCOPE`: `34`
