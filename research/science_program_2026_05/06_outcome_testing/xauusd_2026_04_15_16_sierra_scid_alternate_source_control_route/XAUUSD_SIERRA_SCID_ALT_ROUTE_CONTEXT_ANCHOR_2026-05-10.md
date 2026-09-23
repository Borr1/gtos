# Context Anchor

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "context_anchor",
  "candidate_count": 3,
  "changes_live_trading_behavior": false,
  "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
  "credentials_touched": false,
  "current_head": "258a6ab8",
  "generated_at_utc": "2026-05-10T10:47:38Z",
  "lane": "source/control alternate-source recovery",
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
  "preflight_inputs_read": {
    "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md",
    "existing_scid_converter": "scripts/convert_sierra_scid_to_ohlcv.py",
    "existing_scid_inspector": "scripts/inspect_sierra_scid.py",
    "g12_audit_dir": "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit",
    "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
    "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "live_state": ".context/LIVE_STATE.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "quick_reference": ".context/00_core/quick_reference_card.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "research_operating_doctrine": ".context/00_core/research_operating_doctrine.md",
    "target_tick_recovery_route_dir": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "requested_owner_request_ids": [
    "OWNER-TICK-0020",
    "OWNER-TICK-0021"
  ],
  "required_boundaries": {
    "live_boundary": "no prompt/config/risk/permissions/safety/selector/canary/live behavior changes",
    "raw_data_boundary": "raw SCID rows and raw tick files are not copied or committed",
    "result_boundary": "no result/cost/R/win-rate/expectancy labels or validation denominators opened",
    "source_state_boundary": "market data cannot recreate pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, or final lifecycle truth"
  },
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
  "source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
  "upstream_context": {
    "accepted_g12_audit": "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_AUDIT_REPORT_2026-05-10.md",
    "remaining_mt5_requests": [
      {
        "candidate_ids": [
          "XAUUSD_2026-04-15T14:15:05.007998+00:00"
        ],
        "owner_request_id": "OWNER-TICK-0020",
        "source_date": "2026-04-15",
        "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet"
      },
      {
        "candidate_ids": [
          "XAUUSD_2026-04-16T09:30:05.013547+00:00",
          "XAUUSD_2026-04-16T13:16:01.126537+00:00"
        ],
        "owner_request_id": "OWNER-TICK-0021",
        "source_date": "2026-04-16",
        "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet"
      }
    ],
    "target_owner_action_manifest": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_OWNER_ACTION_MANIFEST_2026-05-10.json"
  },
  "validation_safe": false
}
```
