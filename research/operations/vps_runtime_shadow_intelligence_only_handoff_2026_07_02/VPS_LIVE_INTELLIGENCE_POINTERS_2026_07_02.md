# VPS Live Intelligence Pointers - 2026-07-02

Use these hot surfaces for the main research session. They are intentionally not copied into this route because they are live append-only evidence.

## Runtime Logs

- `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`
  - Primary packet ledger for generated/shadow/skipped/managed/closed book units.
  - Post-mode-change rows show `position_managed` with `live_broker_authority_false_observe_only`.
- `shadow_logs/ultimate_book_launcher.jsonl`
  - Per-cycle and per-management launcher summary.
  - New cycle rows carry `runtime_effect_now=false`, `live_broker_authority=false`, and `placed=[]`.
- `shadow_logs/broker_order_lifecycle_capture_v4.jsonl`
  - Broker order lifecycle capture.
  - Use this to confirm no `unit_placed` or broker send after the mode-change cutoff.
- `shadow_logs/execution_manager_v4_decisions.jsonl`
  - Execution-policy and order-send diagnostics.
- `shadow_logs/slippage_runtime.jsonl`
  - Slippage runtime capture.
- `shadow_logs/daily_pnl.json` and `shadow_logs/daily_pnl_history.jsonl`
  - Broker-dollar daily PnL state/history.

## Runtime State

- `pipeline_state/ultimate_book/operator_profile/heartbeat.json`
- `pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json`
- `pipeline_state/ultimate_book/*/trade_records/`
  - Current open records remain ticket/candidate/decision/policy joinable for the two existing `idxrev` index shorts.
- `pipeline_state/ai_companion/control_state.json`
- `pipeline_state/ai_companion/cycle_digest.json`
- `pipeline_state/ultimate_book/runtime_learning_advisory/RUNTIME_LEARNING_DAILY_ADVISORY.json`

## Current Handoff Route

- `research/operations/vps_runtime_shadow_intelligence_only_handoff_2026_07_02/VPS_SHADOW_INTELLIGENCE_ONLY_HANDOFF_2026_07_02.md`
- `research/operations/vps_runtime_shadow_intelligence_only_handoff_2026_07_02/VPS_SHADOW_INTELLIGENCE_ONLY_MODE_CHANGE_AUDIT_2026_07_02.json`
- `research/operations/vps_runtime_shadow_intelligence_only_handoff_2026_07_02/MAIN_RESEARCH_SESSION_STARTER_2026_07_02.md`

## Verification Boundary

Claims allowed from this route:

- The VPS runtime remains up and is still producing management/learning telemetry.
- Actual broker mutation from the ultimate-book path is disabled by config and production code.
- Existing open positions were not closed by this mode change.
- No pending orders were present at the verification snapshot.

Claims not made by this route:

- No future broker mutation from code outside the ultimate-book path.
- No broker-side manual actions by humans or external tools.
- No future cycle candidate will occur; candidate generation remains enabled by design.
