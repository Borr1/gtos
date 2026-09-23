# Market Sweep Watch 2026-05-11 12:10Z

Created: 2026-05-11T12:22:00Z

## Scope

Live supervision note for the seven followed instruments:

- XAUUSD
- US30_cash
- USDJPY
- GBPJPY
- GBPUSD
- XAGUSD
- NAS100

This note records observed liquidity sweep / reclaim / rejection behavior from
MT5 OHLC/tick data and operator screenshot evidence. It is observation-only and
does not authorize discretionary order placement.

## GBPJPY

- Operator screenshot at 2026-05-11T12:10:56Z showed GBPJPY M15 with the prior
  limit setup still visible and `ACTIVE: none`.
- The old GBPJPY FVG pocket was 213.496-213.570, midpoint 213.533.
- Recent bars swept below/through that pocket to 213.464, reclaimed near the
  213.53 area, then displaced upward into the 213.82-213.86 region.
- MT5 OHLC cross-check at 2026-05-11T12:11:46Z showed M15 window
  high 213.861, low 213.464. The 13:45 broker-time M15 bar was
  O=213.552 H=213.670 L=213.464 C=213.527 V=2974.
- Post-screenshot live watch: GBPJPY stayed above the pocket. At
  2026-05-11T12:21:45Z, recent M1/M5 closes were around 213.744 with no
  position and no pending order.

## Metals

- XAGUSD accelerated after the stale capture daemon was restarted. At
  2026-05-11T12:21:45Z, recent M1 bars showed O=81.544 H=81.838 L=81.534
  C=81.831 V=310 on the latest minute, following a prior M5 range
  80.806-81.838.
- XAUUSD also accelerated. At 2026-05-11T12:21:45Z, recent M1 bars showed
  O=4675.350 H=4680.270 L=4675.280 C=4678.280 V=640 on the latest minute.
- Follow-up at 2026-05-11T12:28:55Z confirmed a larger metals expansion:
  - XAGUSD M15 O=81.096 H=82.717 L=81.071 C=82.521 V=4060.
  - XAUUSD M15 O=4668.430 H=4695.410 L=4667.450 C=4687.800 V=9149.
  - XAGUSD M5 15:20 broker-time bar O=81.442 H=82.692 L=81.427 C=82.654
    V=1948.
  - XAUUSD M5 15:20 broker-time bar O=4672.350 H=4695.410 L=4671.720
    C=4692.490 V=4688.
- Live snapshot at 2026-05-11T12:35:08Z: XAGUSD bid 83.005 / ask 83.073,
  XAUUSD bid 4694.840 / ask 4695.400. Metals remained elevated after the
  sweep/expansion rather than fully mean-reverting.

## Other Followed Markets

- M5/M15 sweep scan at 2026-05-11T12:12:57Z flagged:
  - XAUUSD: sell-side rejection above recent high near 4677.34 on M5.
  - US30_cash: high-volume downside activity near 49496.06-49542.96.
  - USDJPY: sell-side rejection near 157.144/157.147 and a later M15
    buy-sweep reclaim near 157.069.
  - GBPUSD: repeated M5/M15 buy-sweep reclaims around 1.36006-1.36038 and
    earlier lows near 1.35857-1.35859.
  - XAGUSD: heavy volume and rejection behavior near 81.322/81.436, followed
    by later upside continuation.
  - NAS100: M15 sell-side rejection near 29280.24 and later M5 buy-sweep
    reclaim near 29188.99-29193.24.
- NAS100 2026-05-11 09:15 candidate check: trade record
  `knowledge_base/trade_records/NAS100/2026-05-11_london_0915.json` is an
  internal candle-polled limit intent with `broker_pending_order_created: false`.
  Therefore broker orders 0 is expected and not a broker-order mismatch.

## Infrastructure Note

- At 2026-05-11T12:18Z, `US30_cash` and `XAGUSD` tick capture states were stale.
- Only the stale tick-capture daemons were restarted:
  - `US30_cash` old PIDs 12636/15660.
  - `XAGUSD` old PIDs 16228/12896.
- Post-restart verification at 2026-05-11T12:19:51Z:
  - `US30_cash` age 45.8s OK.
  - `XAGUSD` age 63.3s OK.
  - `GBPJPY` age 25.4s OK.
- Trading orchestrators, broker orders, account state, prompts, config, and risk
  logic were not touched during the tick-capture intervention.

## Tick-Capture Lock Marker Fix

- Follow-up verification at 2026-05-11T12:23Z showed `US30_cash` and `XAGUSD`
  had become stale again. Their restart attempts were blocked by lock files
  pointing at live orchestrator PIDs, not tick-capture PIDs:
  - `US30_cash` lock pointed at PID 4248.
  - `XAGUSD` lock pointed at PID 10884.
- Root cause: tick-capture lock adoption used marker `--symbol SYMBOL`, which
  also appears in `run_agent.py --symbol SYMBOL` orchestrator command lines.
- Applied an infrastructure-only patch:
  - `src/components/tick_capture.py` now uses daemon-specific marker
    `-m src.components.tick_capture --symbol SYMBOL`.
  - `src/components/mt5_daemon_runtime.py` now verifies a live lock-holder PID's
    argv against the marker before treating it as a real daemon conflict. If the
    PID is live but positively mismatched, the lock is reclaimed.
  - Added focused tests in `tests/test_mt5_daemon_runtime.py` for live
    mismatched PID reclaim and conservative unknown-argv behavior.
- Verification:
  - `python -B -m py_compile src/components/mt5_daemon_runtime.py
    src/components/tick_capture.py tests/test_mt5_daemon_runtime.py` passed.
  - `python -m pytest tests/test_mt5_daemon_runtime.py::TestAcquireSingleInstanceLock
    -q -p no:cacheprovider --basetemp=.pytest_tmp/daemon_lock` passed
    `9 passed`.
- Relaunched only the affected tick-capture daemons:
  - `US30_cash` new Python PID 2924.
  - `XAGUSD` new Python PID 4148.
- Post-fix lock files verified:
  - `.tick_capture_US30_cash.lock` = 2924.
  - `.tick_capture_XAGUSD.lock` = 4148.
  - `.tick_capture_USDJPY.lock` = 9736.

## NY Open Monitor False-Critical

- 2026-05-11T13:00:31Z live monitor reported `crit=1` at the NY KZ open.
- Direct parse showed no broker/order/account issue, no instrument heartbeat
  issue, no daemon issue, and no global alert. The only critical source was
  `strategy_follow_evaluations.jsonl` with `freshness_issue:
  stale_during_active_kz`.
- Diagnosis: monitor freshness logic marked the shadow strategy-follow lane
  critical immediately at KZ start, before the first full active-KZ M15
  evaluation row could reasonably exist.
- Applied monitoring-only fix in `scripts/_live_monitor_iter.py`:
  - Added `STRATEGY_FOLLOW_KZ_START_GRACE_S = 1200`.
  - Added `kz_elapsed_s(...)`.
  - Suppressed only the `strategy_follow_evaluations.jsonl` active-KZ stale
    critical while all active KZ symbols are still inside the start grace.
  - The monitor still raises the critical after grace if the lane remains stale.
- Verification:
  - `python -B -m py_compile scripts/_live_monitor_iter.py` passed.
  - `python scripts/_live_monitor_iter.py` at 2026-05-11T13:04Z returned
    `crit=0 anom=0 pids=7 open_pos=0`.
