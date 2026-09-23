# Pending Limit Lifecycle Telemetry Integration Ticket

Date: 2026-05-03
Scope: research/tooling specification only
Promotion verdict: `NO_PROMOTION_VERDICT`
Status: `FILED_NOT_IMPLEMENTED`

## Purpose

P2-I asks for shadow telemetry specs or isolated logger tests that reduce future forward-validation ambiguity. The highest-value gap is pending-limit lifecycle truth: future V2b/V3/orderflow joins need to know whether a LIMIT_PLACED row became a broker-realized fill, an internal trigger, a no-trigger expiry, a wrong-side abort, an SL-too-close abort, or only a research path counterfactual.

This ticket does not implement live hooks. It turns the 2026-05-02 telemetry spec into a concrete integration plan, acceptance-test matrix, and approval boundary.

## Evidence Read

- `research/databento_orderflow_capture_2026-05-02/PENDING_LIMIT_INTENT_TELEMETRY_SPEC_V0_2026-05-02.md`
- `research/operations/l6_l7_integration_ticket_2026-04-29.md`
- `tests/test_slippage_shadow_logger.py`
- `src/components/execution.py:68` defines `PendingLimitIntent`.
- `src/components/execution.py:539` stores new pending-limit intents.
- `src/components/execution.py:565` checks each candle for pending-limit fills.
- `src/components/execution.py:581` increments and persists `candles_elapsed`.
- `src/components/execution.py:602` expires intents after 48 hours.
- `src/components/execution.py:620` handles triggered-but-no-tick retry.
- `src/components/execution.py:638` cancels wrong-side fills.
- `src/components/execution.py:650` cancels SL-too-close fills.
- `src/components/execution.py:680` calls `open_trade(... trigger="limit_fill")`.
- `src/components/orchestrator.py:825` calls `check_limit_fill` inside kill-zone processing.
- `src/components/orchestrator.py:2061` calls `check_limit_fill` outside kill-zone processing.

## Integration Boundary

This ticket touches live-flow files if implemented later:

- `src/components/execution.py`
- `src/components/orchestrator.py`
- new helper, likely `src/components/pending_limit_lifecycle_logger.py`
- tests under `tests/`

Even though the logger should be additive and fail-open, it observes the live pending-limit branch. Implementation should therefore require an explicit main-thread approval/smoke-test window. Until then, this file is only an operations/research artifact.

## Proposed Logger Contract

New helper:

```python
record_pending_limit_lifecycle(entry: dict, log_path: str = "shadow_logs/pending_limit_intent_checks.jsonl") -> None
```

Required behavior:

- Append-only JSONL.
- Fail-open: any exception is swallowed after a warning.
- No return value used by trading code.
- No mutation of `PendingLimitIntent`, `TradeState`, `session_state`, or MT5 request objects.
- JSON serializable only.
- Parent directory auto-created.
- One row per check while an intent is active, including no-trigger rows.

## Required Event States

| State | Meaning | Current branch |
|---|---|---|
| `still_pending_no_trigger` | Candle did not touch limit. | `check_limit_fill` after trigger test fails. |
| `expired_48h` | Intent exceeded wall-clock expiry. | `execution.py:602`. |
| `triggered_tick_missing_retry` | Candle touched limit but MT5 tick was unavailable. | `execution.py:620`. |
| `cancelled_wrong_side` | Price was already beyond SL. | `execution.py:638`. |
| `cancelled_sl_too_close` | Remaining SL cushion failed `sl_absolute_min`. | `execution.py:650`. |
| `order_send_success_filled` | `open_trade(... trigger="limit_fill")` returned a `TradeState`. | `execution.py:680`. |
| `order_send_failed_retry` | Triggered order send failed; intent remains for retry. | after `open_trade` returns `None`. |
| `manual_or_system_cancelled` | `cancel_limit_intent(reason)` cleared the intent. | `execution.py:713`. |

## Minimal Row Schema

| Field | Required | Notes |
|---|---|---|
| `schema_version` | yes | `pending_limit_lifecycle_v1`. |
| `timestamp_utc` | yes | Logger write time. |
| `symbol` | yes | Canonical GTOS symbol. |
| `broker_symbol` | optional | If cheaply available from orchestrator. |
| `trade_id` | yes | Pending intent id before any clear. |
| `source_branch` | yes | `inside_kz_process_candle`, `outside_kz_pending_check`, or `execution_cancel_limit_intent`. |
| `check_context` | yes | `inside_kz`, `outside_kz`, or `cancel`. |
| `checked_candle_time_utc` | yes for checks | Candle fed into `check_limit_fill`. |
| `checked_candle_open` | yes for checks | Exact M15 OHLC used by live branch. |
| `checked_candle_high` | yes for checks | Exact M15 OHLC used by live branch. |
| `checked_candle_low` | yes for checks | Exact M15 OHLC used by live branch. |
| `checked_candle_close` | yes for checks | Exact M15 OHLC used by live branch. |
| `direction` | yes | LONG/SHORT from intent. |
| `limit_price` | yes | Stored intent limit. |
| `stop_loss` | yes | Stored intent SL. |
| `take_profit_1` | yes | Stored intent TP1. |
| `risk_pct` | yes | Stored intent risk pct. |
| `candles_elapsed_before` | yes | Before `check_limit_fill` mutates it. |
| `candles_elapsed_after` | yes | After the check branch. |
| `trigger_condition_met` | yes | Candle high/low vs limit. |
| `tick_available` | yes if triggered | `False` for no-tick retry. |
| `tick_bid` | optional | Null when no tick. |
| `tick_ask` | optional | Null when no tick. |
| `current_price_used` | optional | Ask for LONG, bid for SHORT. |
| `wrong_side_abort` | yes | Boolean. |
| `sl_too_close_abort` | yes | Boolean. |
| `order_send_attempted` | yes | Boolean. |
| `order_send_success` | yes | Boolean. |
| `trade_state_ticket` | optional | Filled ticket if order succeeded. |
| `intent_after_check` | yes | One of the event states above. |
| `record_path` | optional | Orchestrator trade-record path, if known. |
| `raw_data_m15_count` | optional | Inside-KZ path only. |
| `latest_m15_time_utc` | optional | Inside-KZ path only. |
| `last_limit_check_candle_time_before` | optional | Outside-KZ duplicate guard state. |
| `reason` | optional | Cancellation/expiry/retry reason. |

## Implementation Shape

1. Add the helper module and unit tests first, without importing it from live files.
2. Add an optional `telemetry_context: dict | None = None` argument to `ExecutionEngine.check_limit_fill`.
3. Snapshot `PendingLimitIntent` before mutation so `candles_elapsed_before`, risk, limit, SL, TP, and trade id survive branches that clear the intent.
4. Emit exactly one lifecycle row for every non-noop active-intent check.
5. Pass `telemetry_context` from:
   - `orchestrator.py:825` with `source_branch="inside_kz_process_candle"`.
   - `orchestrator.py:2061` with `source_branch="outside_kz_pending_check"`.
6. Add a separate row from `cancel_limit_intent(reason)` when a manual/system cancellation occurs.
7. Keep the existing `record_slippage` entry-fill logger separate; join later by `trade_id`/ticket.

## Acceptance Tests

Required isolated tests before live wire-in:

| Test | Expected |
|---|---|
| No-trigger candle | one row, `still_pending_no_trigger`, `order_send_attempted=false`, intent remains. |
| 48h expiry | one row, `expired_48h`, intent cleared. |
| Triggered no tick | one row, `triggered_tick_missing_retry`, intent remains. |
| Wrong-side abort | one row, `cancelled_wrong_side`, intent cleared. |
| SL-too-close abort | one row, `cancelled_sl_too_close`, intent cleared. |
| Successful fill | one row, `order_send_success_filled`, ticket present, intent cleared. |
| Order-send failure | one row, `order_send_failed_retry`, intent remains. |
| Manual cancel | one row, `manual_or_system_cancelled`, reason preserved. |
| Logger disk failure | no exception reaches `check_limit_fill` or `cancel_limit_intent`. |
| Outside-KZ duplicate guard | no duplicate row for the same outside-KZ candle after orchestrator guard returns early. |

Integration tests after wire-in:

- Inside-KZ pending check passes `raw_data_m15_count` and `latest_m15_time_utc`.
- Outside-KZ pending check passes `_last_limit_check_candle_time` context.
- A mocked fill also produces the existing slippage row with `trigger="limit_fill"`; lifecycle and slippage rows remain separate.

## Label Policy For Future Joins

Future orderflow/path joins should keep these label lanes separate:

| Lane | Promotion use |
|---|---|
| `broker_actual_r` | Allowed only when MT5/deal/close evidence exists. |
| `internal_limit_filled` | Research fill label, not broker actual R by itself. |
| `internal_trigger_order_failed` | Execution-plumbing failure label. |
| `internal_no_trigger_or_expired` | No-fill lifecycle label. |
| `internal_cancelled_wrong_side_or_sl_too_close` | Abort lifecycle label. |
| `counterfactual_path_only` | Research OHLC path touched level; never actual R. |

Only `broker_actual_r` can enter promotion-grade actual-R claims.

## Interaction With L-6 / L-7

- L-6 token-usage logging is independent and should remain first if the next approval window is cost/AI observability focused.
- L-7 close-side slippage is independent but complementary: it explains realized close quality after a broker position exists.
- Pending-limit lifecycle telemetry explains whether a position should exist at all. It is the blocker for LIMIT_PLACED label truth and V3 reentry lifecycle truth.

## Open Blockers

1. No live-code hook is implemented in this ticket.
2. CEO/main-thread approval is still required before touching `execution.py` or `orchestrator.py`.
3. Historical LIMIT_PLACED rows without lifecycle telemetry remain unrecoverable as broker actual-R evidence.
4. The outside-KZ path has a duplicate-candle guard in orchestrator; logger placement must preserve that guard.

## NO_PROMOTION_VERDICT

This ticket does not validate any path-scaling, orderflow, execution, or risk improvement. It only specifies future fail-open telemetry needed to make forward validation less ambiguous.
