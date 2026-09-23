# Main Research Session Starter - VPS Shadow Intelligence Mode

Start here:

1. Read `VPS_SHADOW_INTELLIGENCE_ONLY_HANDOFF_2026_07_02.md`.
2. Read `VPS_SHADOW_INTELLIGENCE_ONLY_MODE_CHANGE_AUDIT_2026_07_02.json`.
3. Regenerate `.context/LIVE_STATE.md`.
4. Confirm current config still has:
   - `ultimate_book_apply_to_execution: false`
   - `ultimate_book_live_activation_allowed: false`
   - `ultimate_book_live_broker_authority: false`
5. Inspect recent packet rows from `shadow_logs/ultimate_book_runtime_learning_packets.jsonl` after `2026-07-02T05:33:00Z`.
6. Confirm current broker state with read-only MT5/account telemetry before making any trade or lifecycle claim.

Research focus:

- Mine the shadow candidate stream and skipped-candidate reasons without broker mutation.
- Compare would-units versus realized-disabled policy state.
- Track whether AI companion controls would have been useful while no broker authority is active.
- Join candidate, decision, policy, trade-record, and broker-real observations for the two legacy open index positions.
- Watch for any `unit_placed`, order-send diagnostic, SL/TP modify, close, or flatten event after the mode-change cutoff; that would be a bug unless it is external/manual.

Operational boundary:

- Do not re-enable live broker authority unless the owner explicitly asks for live broker mutation again.
- Do not use flatten flags for this shadow mode; flatten is a broker mutation.
- Keep supervisor, book workers, monitor, AI companion, and advisory loops running.
