# 2026-05-01 XAUUSD Restarted Pending Limit Min-Lot SL

## Summary

XAUUSD internal pending limit `lim_2026-05-01_0815` filled during NY after
multiple orchestrator restarts. The broker trade stopped out quickly, but the
realized loss was only about `$10` because the restarted pending intent no
longer had an account balance available for lot sizing and fell through to the
minimum volume clamp.

This was not a broker-native pending order. It was a GTOS internal
`PendingLimitIntent`.

## Broker-Verified Outcome

MT5 history, queried after the incident:

- Open deal: `2026-05-01T14:00:05Z` true UTC, XAUUSD SHORT, `0.01` lots,
  fill `4626.25`, commission `-$0.07`, order `235112399`, comment
  `GoldAgent_OBRete`.
- Close deal: `2026-05-01T14:00:39Z` true UTC, XAUUSD close at `4636.10`,
  profit `-$9.85`, comment `[sl 4636.02]`.
- Net realized loss: approximately `-$9.92`.

No broker positions or broker pending orders remained after the close.

## Intended Internal Setup

- Direction: `SHORT`
- Original internal limit: `4617.78`
- Original SL: `4636.02`
- Original AI TP1: `4590.42`
- J46-J49 broker TP override: `4567.77`
- Risk pct stored on intent: `1.0%`
- Trade id: `lim_2026-05-01_0815`

The fill happened at the then-current bid around `4626.27`, not at the
original `4617.78` limit, because the internal candle-level checker executes a
market order after a candle has touched the limit condition.

## What Went Wrong

Two separate issues were exposed:

1. `PendingLimitIntent` persistence did not include account balance.
   - `ExecutionEngine.set_limit_intent()` stored `_pending_account_balance`
     only in memory.
   - After watchdog/process restarts, `_load_pending_intent()` restored the
     intent but `_pending_account_balance` reset to `0.0`.
   - On fill, `open_trade(... account_balance=0.0 ...)` produced a zero risk
     amount, then the existing safety clamp converted that to the broker minimum
     `0.01` lots.

2. Broker-closed reconciliation missed the actual SL deal.
   - `RealMT5.get_history_deals()` converted returned deal times from broker
     time to UTC, but it did not shift the query window into broker server time.
   - redacted_account server time was UTC+3, so the close deal was outside the query
     window when `_finalize_exit()` searched for it.
   - The live trade record therefore fell back to detection-time bid and marked
     `broker_deal_reconciled=false`.

## Fixes Applied

1. `src/components/execution.py`
   - Added `account_balance` to `PendingLimitIntent`.
   - Restores `_pending_account_balance` from the intent when available.
   - If an old restored intent lacks balance, falls back to current MT5 account
     balance at fill time instead of silently min-lot sizing.

2. `src/mt5/mt5_real.py`
   - `get_history_deals()` now warms broker-offset detection and shifts query
     bounds by the broker offset before calling MT5 history APIs.

3. `src/components/orchestrator.py`
   - Replaced the non-ASCII SPRT lambda glyph in a log message with ASCII
     `Lambda` to avoid Windows cp1252 console logging errors.

4. Tests
   - Added regression coverage for restored pending-limit balance fallback.
   - Added regression coverage for broker-time history query bounds.

## Verification

Focused regression suites passed:

```text
python -m pytest tests/test_limit_order_flow.py tests/test_mt5.py -q --basetemp C:\tmp\gtos_pytest_xau_incident_full -p no:cacheprovider
34 passed
```

Live reload:

- All 7 live orchestrators restarted through `scripts/watchdog.ps1`.
- Tick capture daemons and sidecars stayed alive.
- Post-reload monitor: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No duplicate orchestrators, tick daemons, heartbeat, displacement, or
  notification workers.
- NAS100 internal pending intent remained active. Its old pickle has
  `account_balance=0.0`, but the hotfix now falls back to current MT5 account
  balance if it ever triggers.

## Notes

The small loss was accidental under-risking caused by a restart persistence bug.
It reduced realized damage on this trade, but it was not correct system
behavior. The intended risk policy is still controlled by the per-instrument
profile and correlation/side-aware risk pipeline.
