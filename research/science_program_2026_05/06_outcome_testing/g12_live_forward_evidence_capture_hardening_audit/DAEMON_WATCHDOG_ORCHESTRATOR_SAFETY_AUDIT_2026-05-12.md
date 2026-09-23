# Daemon, Watchdog, Live Monitor, and Orchestrator Safety Audit - 2026-05-12

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Finding

PASS. Runtime-facing changes are limited to observation/control robustness and the timeout-trailing late-fill anchor. I found no change to order entry, order placement, AI decisions, risk sizing, safety gates, broker account/order-history reads, prompt/config risk, or execution logic.

## Tick Capture

- `src/components/tick_capture.py:134` adds `DEFAULT_FLUSH_INTERVAL_SEC = 60.0`.
- `src/components/tick_capture.py:547` to `:569` keep `fetch_new_ticks` querying in broker-time epoch using `last_msc`, with no UTC-offset subtraction in the query path.
- `src/components/tick_capture.py:590` accepts `flush_interval_sec`.
- `src/components/tick_capture.py:617` initializes `last_flush_at`.
- `src/components/tick_capture.py:657` flushes a non-empty buffer after the interval.
- `src/components/tick_capture.py:659` to `:661` only resets the flush timer after a successful flush.
- `src/components/tick_capture.py:811` exposes `--flush-interval-sec`.
- `src/components/tick_capture.py:839` narrows the daemon argv marker to `-m src.components.tick_capture --symbol {canonical_symbol}`.
- `src/components/tick_capture.py:937` passes the flush interval into the loop.

Tests:

- `tests/test_tick_capture.py:366` verifies last-msc queries use the broker-time epoch.
- `tests/test_tick_capture.py:438` verifies sparse ticks persist through time-based flush.

## MT5 Daemon Lock Reclaim

- `src/components/mt5_daemon_runtime.py:198` defines command-line marker lookup.
- `src/components/mt5_daemon_runtime.py:274` states unknown command-line inspection must not be treated as a negative match.
- `src/components/mt5_daemon_runtime.py:309` defines `acquire_single_instance_lock`.
- `src/components/mt5_daemon_runtime.py:333` documents positive mismatch as required before reclaim.
- `src/components/mt5_daemon_runtime.py:364` inspects the existing live PID command line.
- `src/components/mt5_daemon_runtime.py:369` reclaims only when the live PID is positively identified as marker-mismatched.

Tests:

- `tests/test_mt5_daemon_runtime.py:104` verifies reclaim on positive argv mismatch.
- `tests/test_mt5_daemon_runtime.py:130` verifies conservative refusal when argv inspection is unknown.

## Watchdog

- `scripts/watchdog.ps1:184` defines `Wait-ForOrchestratorLock`, which checks the live lock claimant has `run_agent.py` and the target symbol.
- `scripts/watchdog.ps1:211` defines `Start-DetachedCommand`.
- `scripts/watchdog.ps1:218` to `:238` launch hidden detached daemons via Win32 Process and hidden ProcessStartInfo fallback.
- `scripts/watchdog.ps1:634` increases live-maintenance step timeout to 600 seconds.
- `scripts/watchdog.ps1:806` to `:813` starts orchestrators detached and waits for lock claim.
- `scripts/watchdog.ps1:842` to `:850` applies the same detached launch/claim pattern to displacement.
- `scripts/watchdog.ps1:906` to `:917` applies it to tick-capture daemons.
- `scripts/watchdog.ps1:947` to `:954` applies it to heartbeat.
- `scripts/watchdog.ps1:994` to `:1004` applies it to notification queue.

This is launch/monitoring behavior only. It is not a live restart request in this G12 lane; no watchdog was run by this audit.

## Live Monitor KZ Grace

- `scripts/_live_monitor_iter.py:47` defines `STRATEGY_FOLLOW_KZ_START_GRACE_S = 1200`.
- `scripts/_live_monitor_iter.py:111` computes seconds elapsed since active KZ start.
- `scripts/_live_monitor_iter.py:341` to `:347` detects active KZ grace before the first full M15 evaluation.
- `scripts/_live_monitor_iter.py:405` still marks stale strategy-follow evaluations once grace is over.
- `scripts/_live_monitor_iter.py:420` to `:424` records grace details in the live-monitor status.

## Orchestrator Timeout Anchor

- `src/components/orchestrator.py:3264` still calls `handle_timeout_trailing`.
- `src/components/orchestrator.py:3268` switches the timeout clock to `_timeout_trailing_anchor_time(kz_end)`.
- `src/components/orchestrator.py:3278` still closes only through the existing `close_position("timeout_2h")` path.
- `src/components/orchestrator.py:3282` defines `_timeout_trailing_anchor_time`.
- `src/components/orchestrator.py:3298` to `:3314` uses the later of KZ end and actual `entry_time`, with fallback to KZ end on missing/unparseable entry time.

Tests:

- `tests/test_orchestrator.py:156` verifies late fills use entry time.
- `tests/test_orchestrator.py:163` verifies pre-KZ-end fills keep KZ end.
- `tests/test_orchestrator.py:176` verifies a late fill is not closed before its post-fill window.
- `tests/test_orchestrator.py:204` verifies the timeout still closes after the post-fill window.

## Boundary

These runtime-facing changes do not touch `config/agent_config.yaml`, prompts, permissions gates, `src/components/execution.py`, order-send behavior, risk sizing, AI calls, selector activation, or canary decision logic.
