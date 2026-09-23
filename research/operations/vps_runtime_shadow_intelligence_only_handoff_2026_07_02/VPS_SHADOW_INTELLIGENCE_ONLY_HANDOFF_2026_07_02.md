# VPS Shadow Intelligence-Only Handoff - 2026-07-02

## Decision

The VPS ultimate-book runtime was converted to shadow/intelligence-only operation on 2026-07-02.

The runtime remains active for:

- trade intent generation
- selector/scheduler/risk decisions
- candidate logs
- execution-policy comparison and runtime-learning packets
- market observations
- MT5/account telemetry
- screenshots/logs/diagnostics and handoff export

Broker mutation is disabled:

- no new broker order placement
- no broker close/flatten from the book
- no broker SL/TP modification from book adoption, rehydration, or management
- live broker authority is false

## Code And Config Controls

- `config/agent_config.yaml`
  - `ultimate_book_enabled: true`
  - `ultimate_book_apply_to_execution: false`
  - `ultimate_book_live_activation_allowed: false`
  - `ultimate_book_live_broker_authority: false`
- `config/profiles/redacted_account.yaml`
  - redacted_account overlay also forces apply/live/broker authority false.
- `src/components/ultimate_book/bridge.py`
  - Adds fail-closed `ultimate_book_live_broker_authority`.
  - All four authority gates must pass before `runtime_effect_now=true`.
- `src/components/ultimate_book/book_owner.py`
  - Open-position management emits observe-only rows when broker authority is false.
  - Flatten requests are logged and new entries are latched off, but no broker close is sent.
  - Policy rehydration passes `modify_broker_tp=False`; if a hydrator cannot support read-only rehydration, it is skipped.
- `run_book.py`
  - Startup authority log now includes the broker-authority gate.

## Deployment

The two live book worker groups were restarted under the existing supervisor so they loaded the new code/config.
MT5 terminals, monitor daemon, AI companion, and runtime-learning advisory were not stopped.

Post-reload book workers:

- FTMO: wrapper `2612`, python shim `4864`, active worker heartbeat PID `5720`.
- redacted_account: wrapper `8008`, python shim `428`, active worker heartbeat PID `8652`.

Post-reload startup logs show:

- `authority_gates_ON=False`
- `halted=True` while the temporary deployment halt was active
- `killed=False`

The temporary `pipeline_state/RESEARCH_RUNTIME_HALT.flag` was removed after the new no-mutation authority was verified. Current halt/kill files were absent at the verification point:

- `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`: absent
- `pipeline_state/RESEARCH_RUNTIME_HALT.flag`: absent
- `pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag`: absent
- `pipeline_state/ULTIMATE_BOOK_KILL_fn.flag`: absent

## Verification

Focused tests:

- `python -m pytest tests/ultimate_book/test_book_engine.py tests/ultimate_book/test_book_owner.py tests/ultimate_book/test_breach_flatten.py tests/ultimate_book/test_a8_live_activation_config.py tests/ultimate_book/test_market_expansion_runtime_generator.py -q`
- Result: `124 passed`, one existing pytest config warning.

Runtime-learning packets after halt removal:

- FTMO and redacted_account emitted fresh `position_managed` packets.
- `management_action=live_broker_authority_false_observe_only`
- `runtime_effect_now=false`
- `broker_runtime_change_status=false`

Direct MT5 read-only broker snapshot at `2026-07-02T05:36:16Z`:

- FTMO login `531325516`: balance `94638.26`, equity `94663.63`, positions `1`, pending orders `0`.
  - `US500.cash` SELL ticket `163901804`, volume `1.95`, open `7504.53`, SL `7555.53`, TP `7466.28`, profit about `25.84`, comment `W7:idxrev`.
- redacted_account login `0`: balance `96133.42`, equity `96163.75`, positions `1`, pending orders `0`.
  - `SPX500` SELL ticket `249791692`, volume `0.25`, open `7504.25`, SL `7555.86`, TP `7465.54`, profit about `31.25`, comment `W7:idxrev`.

Monitor one-shot at `2026-07-02T05:35:50Z` showed the same two open index shorts and no new position families.

## Important Note

Before the rehydration fix, adoption/hydration could try to re-apply a broker TP during startup. The temporary halt blocked that request during deployment. The root-cause fix is now in `book_owner._rehydrate_policy`: broker-authority false forces read-only rehydration (`modify_broker_tp=False`) before management begins.
