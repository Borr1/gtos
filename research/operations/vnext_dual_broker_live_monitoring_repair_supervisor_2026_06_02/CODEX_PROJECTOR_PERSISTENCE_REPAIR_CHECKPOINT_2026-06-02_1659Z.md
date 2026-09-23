# CODEX_PROJECTOR_PERSISTENCE_REPAIR_CHECKPOINT_2026-06-02_1659Z

Recorded at: `2026-06-02T16:59:18Z`

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`

Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`

Runtime boundary: code repair and projector reload only. No manual broker order, position, deal, SL, TP, or account mutation was performed.

## Current Status

The active live process shape is healthy and remains the memory-conscious dual-broker architecture:

- redacted_account: 24 Python `run_agent.py` workers, all scoped to `redacted_account_live_bee34003`.
- FTMO: 0 `run_agent.py` workers and 1 lightweight execution follower scoped to `operator_profile`.
- Bridge: 1 projector and 1 FTMO follower.
- Data capture: 24 redacted_account tick captures, 1 redacted_account M1 capture.
- Notifications: 1 redacted_account notification worker; FTMO duplicate notifications remain suppressed by design.
- MT5 terminals: 2 terminals, redacted_account normal path and FTMO portable path.
- Memory after reload: `1804.05 MB` free physical, `22.02%`.

The remaining process footprint item is 24 redacted_account `cmd.exe` parent wrappers using about `117.55 MB`. They are parent wrappers around the 24 actual redacted_account Python workers, not duplicate/unscoped Python workers. I did not restart the full redacted_account fleet just to remove them because no current live defect requires a broad all-symbol restart while trades are open.

## Broker And Target-State Proof

Read-only MT5 probe at `2026-06-02T16:54:55Z` passed:

- redacted_account: 11 positions, 0 orders, account identity matched.
- FTMO: 8 positions, 0 orders, account identity matched.
- Both broker profiles have 24 configured symbols with symbol info found.
- FTMO used the no-mass-select policy; 19 symbols had positive ticks and 5 stayed unselected/absent until lazy-select is needed.

FTMO target-state reconciliation after follower refresh:

- target active trade count: 8
- broker FTMO positions: 8
- missing target tickets in broker: `[]`
- extra broker tickets not in target state: `[]`
- target state updated at `2026-06-02T16:57:20.429849+00:00`

The currently ticket-bound FTMO target positions are `155073142`, `155108218`, `155108230`, `155108232`, `155129060`, `155129494`, `155129522`, and `155142189`. USDJPY, BTCUSD, and JP225 residuals are already marked as TP1/BE-managed by ticket.

## Candidate And Intent Delta

No new post-checkpoint entry flow was found:

- Canonical intent log last write is still `2026-06-02T15:46:19.3835818Z`.
- The latest canonical intent remains the ETHUSD `market_entry` at `2026-06-02T15:46:19Z`.
- No redacted_account trade-record JSON files were modified after the previous `16:45:29Z` checkpoint.
- No FTMO trade-record JSON files were modified after the previous `16:45:29Z` checkpoint.
- Projector action log is moving and reporting cycles with `projected=0`, `errors=0`, `skipped=0`, `tracked_files=250`.

## Defect Repaired

The prior active follower defect proved that a Windows `PermissionError` during `os.replace()` can kill a live bridge process. The projector still had the same single-shot JSON state persistence pattern:

- `scripts/dual_broker_trade_record_projector.py` used `tmp.write_text(...)` then a single `os.replace(...)` for `trade_record_projector_state.json`.
- No projector crash was observed in this cycle.
- This is a same-class live bridge persistence defect because it shares the exact failure mode that had already killed the FTMO follower.

Repair:

- Projector `_write_json()` now retries transient `PermissionError` file-lock failures up to 5 times.
- If Windows still refuses the replace, it logs the skipped persistence and returns instead of terminating the live projector.
- Non-permission filesystem errors also log and return.

Focused tests added:

- transient `PermissionError` retries and writes the intended state
- repeated file lock preserves the previous durable state and does not raise

## Verification

Commands:

- `python -m py_compile scripts\dual_broker_trade_record_projector.py` passed.
- `python -m pytest tests\test_dual_broker_trade_record_projector.py -q` passed: `11 passed`.
- `python research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py` passed: `failure_count=0`.

Pytest emitted the expected protected-production-path warning from live heartbeat and target-state movement during the test run. The focused tests themselves passed.

## Reload

Only the projector was reloaded. Before reload:

- projector Python PID: `11372`
- projector `cmd.exe` wrapper PID: `5576`

After reload:

- projector Python PID: `11320`
- projector `cmd.exe` wrapper count: `0`
- projector state updated at `2026-06-02T16:58:57.404392+00:00`
- projector stdout/stderr reload logs are present and empty of errors.

No redacted_account workers, FTMO follower, tick captures, M1 capture, notification worker, or MT5 terminals were restarted for this repair.

## Remaining

- Continue delta live supervision for new candidates/intents/fills/partials/modifies/closes.
- Treat the 24 redacted_account `cmd.exe` worker parents as a process-footprint optimization item; remove only through a controlled full-worker reload when there is a live-safe reason to restart the redacted_account fleet or after a launcher/watchdog repair proves a direct-Python replacement path.
- Keep V3 disposition unchanged unless current evidence supports activation: packages remain consumed/default-off; active live policy remains `momentum_exhaustion` primary with `partial_be_runner` exception selection.
