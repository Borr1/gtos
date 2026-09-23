# FTMO Follow Repair Checkpoint - 2026-06-02 13:52Z

## Operator Reminder

Use maximum reasoning on every live-system inspection. Do not accept a surface symptom as the root cause. Trace redacted_account candidate/trade records to canonical intents, follower action rows, target broker pre-trade checks, MT5 positions/deals, risk budget, namespace, and process footprint before concluding.

## Scope

- Incident: FTMO appeared not to follow newly added redacted_account trades.
- Boundaries: no manual broker order/position mutation was performed.
- Runtime target: keep redacted_account full execution unrestricted; keep FTMO as lightweight intent follower, not a duplicate 24-agent fleet.

## Findings

- FTMO was not dead. It copied the 2026-06-02 13:31Z BTCUSD and NZDUSD intents and the 13:46Z NAS100 and USDCAD intents.
- 13:16Z/13:19Z selective misses had two causes:
  - USDCAD and XAGUSD reached the follower but target-side `ExecutionEngine.open_trade()` returned `None` after FTMO pre-trade cost/spread checks. The old follower incorrectly marked those no-order attempts as permanently processed.
  - UKOIL_cash and USOIL_cash were filled on redacted_account but produced no canonical intent because the intent builder treated the non-fatal `condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry` note as fatal.
- No duplicate FTMO run-agent fleet was present. Process checkpoint after repair showed 24 redacted_account run agents, 0 FTMO run agents, 1 FTMO follower, 1 trade-record projector, 2 MT5 terminals.

## Repairs

- `src/components/dual_broker_intent_bus.py`
  - Non-fatal broader-origin condition-challenger join note no longer blocks projection by itself.
  - Added `trade_record_projection_skip_reasons()` so projection skips are explainable from disk.
- `scripts/dual_broker_trade_record_projector.py`
  - Logs `trade_record_projection_skipped` for intent-builder skips.
  - Adds live filled-record max age (`--max-filled-record-age-seconds 120`) so old fills are not copied late after reload.
- `scripts/dual_broker_execution_follower.py`
  - `open_trade() == None` inside the live market-intent window now defers and retries instead of advancing the bus offset.
  - A per-intent target-position baseline prevents duplicate retry opens if MT5 confirms a position after the first `None` return.
  - Stale no-order intents expire after the configured 120-second window.

## Verification

- `python -m py_compile src\components\dual_broker_intent_bus.py scripts\dual_broker_trade_record_projector.py scripts\dual_broker_execution_follower.py`
- `pytest tests\test_dual_broker_intent_bus.py tests\test_dual_broker_trade_record_projector.py tests\test_dual_broker_execution_follower.py -q`
  - Result: 34 passed.
- Read-only oil diagnostic after patch:
  - UKOIL_cash record now builds an intent.
  - USOIL_cash record now builds an intent.
  - No replay/backfill was run.
- Reloaded only:
  - `dual_broker_trade_record_projector.py`
  - `dual_broker_execution_follower.py`
- Duplicate-guard follower-only reload:
  - before: `pipeline_state/codex_ftmo_follower_duplicate_guard_reload_before_20260602T135513Z.json`
  - after: `pipeline_state/codex_ftmo_follower_duplicate_guard_reload_after_20260602T135550Z.json`
- Route checkpoints recorded at 2026-06-02T13:52:17Z and 2026-06-02T13:56:02Z:
  - memory healthy, 23.49% free then 23.32% free
  - FTMO follower present
  - projector present
  - run_agent_ftmo = 0

## Read-Only Broker Snapshots

- 2026-06-02 13:52Z post-repair snapshot:
  - redacted_account: 11 open positions, 0 orders.
  - FTMO: 4 open positions, 0 orders.
  - FTMO open copied positions:
    - BTCUSD ticket 155073141
    - NZDUSD ticket 155073142
    - US100.cash ticket 155084504
    - USDCAD ticket 155084506
- 2026-06-02 13:57Z final snapshot:
  - redacted_account: 8 open positions, 0 orders.
  - FTMO: 2 open positions, 0 orders.
  - Current matched FTMO open copied positions:
  - BTCUSD ticket 155073141
  - NZDUSD ticket 155073142
  - 13:46Z NAS100/USDCAD copy proof remains in follower actions, but those positions were no longer open by the final snapshot.
- redacted_account positions still not copied from the earlier defective window at final snapshot:
  - UKOIL_cash / broker symbol UKOUSD
  - USOIL_cash / broker symbol USOUSD
  - XAGUSD

## Evidence Files

- `pipeline_state/codex_ftmo_follow_repair_reload_before_20260602T134957Z.json`
- `pipeline_state/codex_ftmo_follow_repair_reload_after_20260602T135204Z.json`
- `pipeline_state/codex_ftmo_follower_duplicate_guard_reload_before_20260602T135513Z.json`
- `pipeline_state/codex_ftmo_follower_duplicate_guard_reload_after_20260602T135550Z.json`
- `.context/LIVE_STATE.md`
- `pipeline_state/dual_broker/canonical_trade_intents.jsonl`
- `pipeline_state/operator_profile/dual_broker_execution_follower_actions.jsonl`
- `pipeline_state/dual_broker/trade_record_projector_actions.jsonl`
