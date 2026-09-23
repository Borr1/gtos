# vNext Replacement Monitoring Checklist - 2026-05-26

Monitoring log path: `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`

## Required Surfaces

| Surface | Snapshot field | Runtime effect | Rollback trigger |
|---|---|---|---|
| vnext_apply_status | vnext_apply_status | log_only | global apply false when production overlay expected, or true before Stage12 pass |
| router_decisions | router_decision | log_only | dynamic router absent or selected policy not be_after_trigger on applied rows |
| label_effects | label_effects | log_only | AVOID/MIXED/LEGACY still inert when contract says execution effect |
| avoid_mixed_legacy_distribution_and_execution_effect | label_effects | log_only | old-live behavior dominates without explicit rollback reason |
| dynamic_exit_transitions | dynamic_exit_transition | log_only | J46/J49 remains active on applied replacement rows |
| ltf_pending_monitor_health | ltf_pending_monitor_health | log_only | same-bar or path-ambiguous rows receive execution effect |
| prop_budget_projection | prop_budget_projection | log_only | prop defer/reduce/abandon action ignored or auto-abandon attempted |
| source_capture_completeness | source_capture_completeness | log_only | source missing, source window incomplete, or join id missing on applied rows |
| old_live_fallback_leakage | old_live_fallback_leakage | log_only | any detected leakage |
| malformed_ai_responses | ai_malformed_monitoring | log_only | AI schema/malformed rows affect execution or budget cap is absent |

## Minimum Snapshot Fields

`schema_version`, `phase`, `symbol`, `kill_zone`, `candle_time_utc`, `vnext_apply_status`, `router_decision`, `label_effects`, `execution_effects`, `dynamic_exit_transition`, `ltf_pending_monitor_health`, `prop_budget_projection`, `source_capture_completeness`, `old_live_fallback_leakage`, `ai_malformed_monitoring`, `ml_assistant_roles`, `warnings`.

## Pass Criteria

- Every candidate/block path writes a replacement monitoring snapshot.
- Production overlay never applies before Stage12 pass.
- Applied replacement rows show dynamic exit replacement, source completeness, LTF/pending health, prop projection, and old-live leakage status.
- ML roles remain `monitor_only` with `replacement_ml_apply_to_execution=false`.
- Paid AI remains uncalled until a non-null route-state budget cap exists.

## Rollback Criteria

- Any `old_live_fallback_leakage` detected.
- Any applied row has source missing, incomplete source window, or same-bar ambiguity without ordered proof.
- Any monitoring snapshot omits a required field.
- Any AI malformed-response state affects execution.
- Any prop account abandon/restart action occurs without explicit owner handoff.
