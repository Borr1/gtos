# 2026-05-01 XAGUSD Outside-KZ Internal Limit Miss

## Summary

Live XAGUSD internal pending limit `lim_2026-05-01_0830` should have triggered outside the London kill zone, but the outside-KZ polling path marked a forming M15 candle as checked before its final high was known.

This was not a broker-native MT5 pending order. It was a GTOS internal `PendingLimitIntent`, persisted at:

- `knowledge_base/meta/pending_intent_XAGUSD.pkl`

## Intended Setup

- Symbol: `XAGUSD`
- Direction: `SHORT`
- Internal limit: `74.088`
- Stop loss: `74.688`
- Take profit: `73.188`
- Risk: `1.0%`
- Trade id: `lim_2026-05-01_0830`
- Placed: `2026-05-01T08:30:25.470015+00:00`
- Trade record: `knowledge_base/trade_records/XAGUSD/2026-05-01_london_0830.json`

## What Went Wrong

`SessionOrchestrator._check_pending_limit_outside_kz()` fetched only one M15 candle from MT5 and used the returned bar directly.

On live MT5, `copy_rates_from_pos(..., 0, 1)` can return the currently forming bar. The checker saw the forming candle before it had touched `74.088`, then stored that candle time as `_last_limit_check_candle_time`. Later in the same M15 candle, price traded through the limit, but subsequent polls skipped the candle because its timestamp had already been marked checked.

After the first fix, a second issue appeared on restart: `RealMT5.get_candles()` converted broker-time candle epochs before the broker UTC offset had been detected. This could make closed broker candles look like future UTC candles immediately after process restart.

## Evidence

Broker M15 data observed during incident review:

- `2026-05-01T15:00:00` broker-time candle: high `74.169`, low `73.665`, close `73.969`
- This corresponds to the `12:00 UTC` candle on redacted_account UTC+3 server time.
- The high `74.169` exceeded the internal short limit `74.088`, so the candle should have triggered the internal fill path.

After patch reload, XAGUSD log confirmed the checker caught the trigger:

```text
2026-05-01 20:25:35,767 INFO [src.components.execution] Limit triggered: lim_2026-05-01_0830 candle=2026-05-01T12:00:00+00:00 low=73.66500 limit=74.08800
2026-05-01 20:25:35,768 WARNING [src.components.execution] Limit fill abort (price beyond SL): lim_2026-05-01_0830 current=75.09300 SL=74.68800 -- cancelling
```

## Outcome

No broker trade was opened.

The missed hypothetical short would have hit SL, not TP. By the time the patched checker evaluated the missed candle, current XAGUSD price was `75.093`, already beyond the intended short stop loss `74.688`.

## Fixes Applied

1. `src/components/orchestrator.py`
   - Outside-KZ checker now fetches multiple M15 bars.
   - Added `_latest_closed_m15_candle()` and ignores forming M15 candles.

2. `src/mt5/mt5_real.py`
   - `get_candles()` and `get_candles_range()` now warm broker-offset detection before converting candle timestamps.

3. `tests/test_integration_live.py`
   - Added regression test where a closed trigger candle is followed by a forming non-trigger candle.

## Verification

Focused tests passed after the fix:

```text
python -m pytest tests/test_integration_live.py::TestLimitFillExitDataCaptured -q --basetemp C:\tmp\gtos_pytest_live2 -p no:cacheprovider
9 passed

python -m pytest tests/test_limit_order_flow.py -q --basetemp C:\tmp\gtos_pytest_limit2 -p no:cacheprovider
19 passed
```

Live reload:

- All 7 orchestrators restarted through `scripts/watchdog.ps1`.
- Tick capture daemons and sidecars were left running.
- XAGUSD intent restored, then cancelled by the existing safety abort because price was beyond SL.

