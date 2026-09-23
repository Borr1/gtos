# NOFILL Read-Only Tick Recovery Context Anchor

Route: `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary
- `tick_export_dependent_blocker_count`: `31`
- `grouped_request_count`: `22`
- `recovered_grouped_request_count`: `20`
- `remaining_owner_export_request_count`: `2`
- `recovered_candidate_row_count`: `28`
- `remaining_candidate_row_count`: `3`
- `contamination_embargo_excluded_row_count`: `12`

## Machine Payload

```json
{
  "active_question_stack": [
    "Which of the 22 grouped tick requests are recoverable by source-safe local or read-only market-data extraction?",
    "Which recovered files have hash/schema/timestamp/window/source-symbol proof?",
    "Which windows still require exact owner export after all executable recovery paths?",
    "How do recovered tick files preserve the non-generatable source-state boundary?"
  ],
  "artifact_family": "context_anchor",
  "changes_live_trading_behavior": false,
  "contamination_embargo_excluded_row_count": 12,
  "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
  "credentials_touched": false,
  "current_head": "881ac317 docs: refresh state after approval pursuit rule",
  "generated_at_utc": "2026-05-10T09:46:57Z",
  "grouped_request_count": 22,
  "ignored_extraction_manifest": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_MT5_MARKET_DATA_ONLY_EXTRACTION_2026-05-10.json",
  "input_count": 19,
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recovered_candidate_row_count": 28,
  "recovered_grouped_request_count": 20,
  "remaining_candidate_row_count": 3,
  "remaining_owner_export_request_count": 2,
  "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
  "route_scope": "market_data_source_control_only",
  "schema_version": "nofill_readonly_tick_recovery_export_source_control_route_v1",
  "stop_condition": "31 candidate rows and 22 grouped requests reconciled with recovered hashes or exact remaining export requests",
  "terminal_decision": "ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS",
  "tick_export_dependent_blocker_count": 31,
  "validation_safe": false
}
```
