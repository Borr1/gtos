# Pending-Limit Telemetry Clarity - 2026-05-06

Status: `IMPLEMENTED_SHADOW_TELEMETRY_CLARITY`  
Evidence class: `CODE_REVIEW + FOCUSED_TESTS + OPERATIONAL_REPORT_REVIEW`  
Trading behavior impact: none  
Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective

Resolve whether `LIMIT_PLACED` rows are too easy to misread as broker-resting
native pending orders.

The answer is yes for human interpretation. The code already treated
`LIMIT_PLACED` as an internal candle-polled intent, but May 5 monitoring had to
restate that distinction repeatedly. New telemetry fields now make it explicit
in new rows without renaming historical outcomes or changing live order flow.

## Current Semantics Confirmed

`LIMIT_PLACED` means:

- An internal `PendingLimitIntent` was persisted.
- The orchestrator checks later candles for a limit touch.
- No native MT5 pending order is created at `LIMIT_PLACED` time.
- If a later candle touches the limit and viability checks pass, the engine
  opens a broker market order through `open_trade()`.

Code evidence:

- `src/components/execution.py:75` documents candle-level polling.
- `src/components/execution.py:78` now states no broker pending order exists
  until a later `open_trade()` call.
- `src/components/orchestrator.py:1692` calls `set_limit_intent(...)`, not
  native MT5 pending-order placement.
- `src/components/orchestrator.py:1709` logs `LIMIT_PLACED`.
- `src/components/execution.py:561` defines `set_limit_intent(...)` as intent
  storage.
- `src/components/execution.py:614` records lifecycle telemetry from later
  candle checks.

Operational evidence:

- `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md:25`
  already clarified that both May 5 internal limits were not native broker
  orders.
- `research/operations/GTOS_DEEP_ACTIVE_MONITORING_FINAL_2026-05-05.md:39`
  lists May 5 `LIMIT_PLACED` rows as internal no-fill/still-pending with no
  broker order or position.

## Implementation

New additive fields:

- `pending_order_mode`
- `broker_pending_order_created`
- `mt5_order_ticket`
- `native_pending_order_type`

Default values for internal GTOS limit intents:

```json
{
  "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
  "broker_pending_order_created": false,
  "mt5_order_ticket": null,
  "native_pending_order_type": null
}
```

Files changed:

- `src/components/execution.py`
  - Added `INTERNAL_PENDING_ORDER_MODE`.
  - Added explicit native-vs-internal fields to `PendingLimitIntent`.
  - Backfills missing additive fields when loading older schema-compatible
    pending-intent pickles.
  - Emits the new fields into pending-limit lifecycle telemetry rows.
- `src/components/orchestrator.py`
  - Saves the new fields under `record["limit_intent"]` when writing a
    `LIMIT_PLACED` trade record.
- `src/components/pending_limit_lifecycle_logger.py`
  - Adds the fields to the schema-stable lifecycle row.
- `src/research_infra/forward_capture.py`
  - Adds the fields to new `strategy_follow_candidate_v1` rows.
  - Defaults new `LIMIT_PLACED` forward rows to internal intent semantics even
    when an older record lacks the fields.
- Tests:
  - `tests/test_limit_order_flow.py`
  - `tests/test_pending_limit_lifecycle_logger.py`
  - `tests/test_forward_capture_shadow_loggers.py`

## Compatibility

- The existing `LIMIT_PLACED` outcome label is unchanged.
- Historical joins remain backward compatible.
- Old pending-intent pickle files with schema version `1` are not discarded;
  missing additive fields are filled in memory.
- The new fields are telemetry only and do not affect risk, prompts,
  permissions gates, order placement, or execution decisions.

## Verification

Syntax:

```powershell
python -m py_compile src/components/execution.py src/components/orchestrator.py src/components/pending_limit_lifecycle_logger.py src/research_infra/forward_capture.py
```

Focused tests:

```powershell
python -m pytest tests/test_limit_order_flow.py tests/test_pending_limit_lifecycle_logger.py tests/test_forward_capture_shadow_loggers.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase1d_pending_limit_clarity
```

Result: `43 passed in 1.64s`.

The first sandboxed pytest attempt failed before test execution because Windows
denied creation of `C:\tmp\pytest_phase1d_pending_limit_clarity`. The same
command passed after approved escalation.

Final posture: `NO_PROMOTION_VERDICT`
