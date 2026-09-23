# Pending Limit Intent Telemetry Spec V0

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

The XAUUSD 2026-04-17 13:30 LIMIT_PLACED row cannot be promoted into actual realized R from current evidence. Local logs show the internal intent was placed and later discarded, while M1 research data shows the internal limit level would have been touched and the counterfactual path would have reached TP. The missing evidence is not another Databento pull; it is forward telemetry from the pending-limit lifecycle.

Current code evidence:

- `src/components/execution.py:539` stores `PendingLimitIntent`.
- `src/components/execution.py:565` checks each candle for a pending-limit trigger.
- `src/components/execution.py:614` logs a trigger only after the candle high/low crosses the limit.
- `src/components/orchestrator.py:823` checks inside-kill-zone pending intents from the latest M15 candle.
- `src/components/orchestrator.py:2056` checks outside-kill-zone pending intents from the latest closed M15 candle.

This spec is the minimum forward research telemetry needed to make future LIMIT_PLACED labels auditable. It does not authorize a live-code change by itself.

## Required Event Rows

Write one research telemetry row for every pending-intent check while an intent is active, including no-trigger checks.

Required fields:

| Field | Purpose |
|---|---|
| `schema_version` | Versioned parser compatibility. |
| `timestamp_utc` | Wall-clock time when the check happened. |
| `symbol` | GTOS symbol. |
| `trade_id` | Pending intent id, for join back to trade record. |
| `origin_candle_close_utc` | Candle close that created the limit intent, if known. |
| `check_context` | `inside_kz` or `outside_kz`. |
| `checked_candle_time_utc` | M15 candle time used by `check_limit_fill`. |
| `checked_candle_open/high/low/close` | Exact candle OHLC fed into the trigger check. |
| `direction` | LONG or SHORT. |
| `limit_price` | Stored pending limit. |
| `stop_loss` | Stored SL. |
| `take_profit_1` | Stored TP1. |
| `candles_elapsed_before` | Counter before this check. |
| `candles_elapsed_after` | Counter after this check. |
| `trigger_condition_met` | Boolean result of candle-vs-limit check. |
| `tick_available` | Whether MT5 tick was available if triggered. |
| `tick_bid` | Bid at trigger, if available. |
| `tick_ask` | Ask at trigger, if available. |
| `current_price_used` | Ask for LONG, bid for SHORT. |
| `wrong_side_abort` | Whether price was already beyond SL. |
| `sl_too_close_abort` | Whether remaining SL cushion failed. |
| `order_send_attempted` | Whether `open_trade(... trigger="limit_fill")` was attempted. |
| `order_send_success` | Whether MT5 execution returned a trade state. |
| `intent_after_check` | `still_pending`, `filled`, `expired`, `cancelled_wrong_side`, `cancelled_sl_too_close`, or `cleared_unknown`. |
| `record_path` | Trade record path associated with the pending intent. |
| `raw_data_m15_count` | Number of M15 candles available to the orchestrator at check time. |
| `latest_m15_time_utc` | Latest M15 candle time in raw_data. |
| `source_branch` | `inside_kz_process_candle` or `outside_kz_pending_check`. |

## Optional Diagnostic Fields

Add these if cheap and fail-open:

- `spread_at_trigger`
- `mt5_server_time`
- `broker_symbol`
- `kz_name`
- `session_state_trades_today`
- `last_limit_check_candle_time_before`
- `pending_intent_loaded_from_disk`
- `pending_intent_persisted_after_check`

## Output Policy

Recommended path:

`shadow_logs/pending_limit_intent_checks.jsonl`

Rules:

- Append-only JSONL.
- Fail-open: telemetry failures must not block trading or pending-limit checks.
- No prompt edits.
- No parameter changes.
- No change to fill/trigger behavior.
- Log every check, not only triggers. The no-trigger rows are the critical missing evidence.

## Label Policy

Future orderflow joins should classify LIMIT_PLACED rows into separate label types:

1. `broker_actual_r`: real MT5 deal/execution/exit evidence exists.
2. `internal_intent_filled`: pending intent triggered and order_send succeeded.
3. `internal_intent_triggered_order_failed`: trigger occurred but execution failed.
4. `internal_intent_no_trigger`: intent existed but every logged check was no-trigger.
5. `internal_intent_discarded`: intent was discarded before fill.
6. `counterfactual_path_only`: research OHLC path touched a level, but no live trigger/fill evidence exists.

Only `broker_actual_r` can be used for actual-R promotion claims.

## Ambiguity Ledger

- Historical logs do not include no-trigger candle OHLC, so the XAUUSD 2026-04-17 row remains unreplayable from local live evidence.
- M1 OHLC counterfactuals can prove a market path would have touched a level, but they cannot prove the live pending-fill branch saw the same candle state.
- MT5 tick availability at the trigger moment can still block execution even when candle OHLC crosses the limit.
- This telemetry will close future pending-intent ambiguity, but it does not recover missing historical evidence.

## Open Questions

1. Did the XAUUSD 2026-04-17 13:30 row fail because the live M15 candle stream was empty/stale, because the active candle was not the one seen in research M1 data, or because another branch returned before the fill check?
2. How often do pending intents see no-trigger checks before eventual fill, expiry, or discard?
3. How often does candle-trigger evidence disagree with tick availability or wrong-side/proximity viability checks?
4. Does fill/no-fill behavior carry independent orderflow information, or is it only execution plumbing?

## Next Steps

1. Keep the XAUUSD 2026-04-17 13:30 row out of orderflow promotion-grade scoring.
2. If the CEO approves a later live-observability change, add fail-open JSONL telemetry with the required fields above.
3. Update future candidate outcome joins to separate actual broker R, internal fill states, and counterfactual path labels.
4. Re-run the limit-intent reconciliation audit only after new telemetry rows exist.
