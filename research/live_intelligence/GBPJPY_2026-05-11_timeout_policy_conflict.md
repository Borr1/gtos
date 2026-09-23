# GBPJPY 2026-05-11 Timeout Policy Conflict Observation

Created: 2026-05-11T11:35:00Z

## Event

GBPJPY long position `237192029` closed at 2026-05-11T11:30:06Z by
`timeout_2h`, at approximately 213.835, for about +0.615R.

## Current-Code Explanation

This was expected under the live session-end timeout implementation:

- `src/components/orchestrator.py` defines `TIMEOUT_TRAIL_MINUTES = 120`
  with the comment `2 hours after session end`.
- `_manage_timeout_trailing()` computes timeout against `_last_kz_end_time()`,
  not against the trade fill time.
- GBPJPY London kill zone ended at 2026-05-11T09:30:00Z.
- The close fired at 2026-05-11T11:30:06Z.

The position filled late, at 2026-05-11T10:45:05Z, so the actual live hold after
fill was about 45 minutes.

## Policy Interaction

J46-J49/J48 has a separate `time_stop_bars: 12` policy, meaning roughly 12 M15
bars from trade time. That per-trade time-stop did not govern this exit because
the session-end timeout fired first.

## Classification

Not a broker/order/account failure. Not a daemon problem. No restart indicated.

This is a live exit-policy interaction: session-end timeout can override the
newer per-trade J46-J49/J48 time-stop on late outside-KZ fills. Changing it
would alter live exit behavior and should be handled as an explicit policy/code
change, not a monitoring hotfix.

## Fix Applied

Owner approved fixing the timeout behavior during live monitoring.

- Code changed: `src/components/orchestrator.py`
- New rule: timeout anchor is `max(last_kz_end_time, active_trade.entry_time)`.
- Preserved behavior: trades filled before kill-zone end still use the KZ-end
  anchor.
- Fixed behavior: trades filled after kill-zone end get the configured
  post-fill timeout window.
- Regression tests added: `tests/test_orchestrator.py::TestTimeoutTrailingAnchor`.
- Verification: `python -m pytest tests/test_orchestrator.py::TestTimeoutTrailingAnchor -q -p no:cacheprovider --basetemp=.pytest_tmp\basetemp` passed 5/5.
- Additional verification: `python -m pytest tests/test_orchestrator.py::TestKillZoneDetection tests/test_orchestrator.py::TestTimeoutTrailingAnchor -q -p no:cacheprovider --basetemp=.pytest_tmp\basetemp2` passed 15/15.
- Reload: seven orchestrators restarted through `GTOS_Watchdog` at
  2026-05-11T11:46:55Z after confirming no open positions/orders.
- Post-reload health: `_live_monitor_iter.py` at 2026-05-11T11:48Z reported
  `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
