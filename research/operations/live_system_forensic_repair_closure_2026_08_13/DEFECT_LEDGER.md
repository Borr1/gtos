# Defect Ledger

Evidence cutoff for this checkpoint: 2026-08-13T16:06:39Z.

## D-001 — Benign packet-tail boundary globally paused new entries

- Severity: critical control-plane defect.
- Earliest causal root: `src/components/ai_companion/supervisor.py::_read_jsonl_tail` read at most 16 MiB from a large JSONL file but attempted to parse the first byte-capped fragment as a complete record. It also treated an unterminated concurrent final write as durable corruption.
- Trigger evidence: `shadow_logs/ultimate_book_runtime_learning_packets.jsonl` was 895,581,995 bytes. Its last 16 MiB contained 1,038 physical lines, fewer than the requested 1,200 rows; the first 1,292-byte fragment was the only parse failure and the final row was valid.
- Downstream consequence: AI companion reported `packet_parse_errors=1`, issued global `pause_new_entries` with reason `ai_companion_runtime_integrity_issue`, and changed live entry authority despite no corrupt newline-terminated packet.
- Repair: discard only a byte-cap-created head fragment; ignore only an unterminated malformed tail fragment; continue reporting malformed newline-terminated records.
- Source changes: `src/components/ai_companion/supervisor.py`, `tests/ai_companion/test_supervisor.py`.
- Verification: AI companion suite `24 passed`; direct live-file tail read returned 1,037 rows and zero errors.
- Deployment: stopped only the prior AI companion process tree and allowed the existing main supervisor to reload it. Main book workers, monitor, terminals, and broker positions were untouched.
- Post-change proof: new AI companion leaf PID `14500`; heartbeat at 2026-08-13T15:55:53Z and again at 2026-08-13T16:06:32Z was `ok=true`, `control_count=0`; packet-parse issue count was zero and the clearing proposal removed the global pause.
- Status: repaired, deployed, verified live; pending scoped commit/push and continued-cycle observation.

## D-002 — F5 launcher leaked inherited risk-critical environment

- Severity: medium latent configuration/coherence defect; current exposure was bounded by independent controls.
- Earliest causal root: `C:host-local/redacted_host/run_f5_ftmo.ps1` imported only Telegram keys from the armed `.env` but did not clear machine/user environment inherited by the scheduled task.
- Trigger evidence: healthy F5 heartbeat reported `GTOS_PROFILE=redacted_account`, while its CLI declared `--profile operator_profile`.
- Current-impact determination: no wrong-account or wrong-size placement occurred. Explicit CLI profile precedence in `src/utils/config.py`, fail-closed account identity in `run_book.py`, broker identity magic `0`, and observed `f5_intended_risk_usd=10.0` proved the active worker used FTMO identity and the $10 final sizing contract.
- Residual risk: the authority heartbeat was contradictory and any future internal `resolve_profile(None)` path could consume the inherited redacted_account profile.
- Repair: clear `GTOS_PROFILE`, `GTOS_UB_DERISK_MODE`, and `GTOS_MT5_TERMINAL_PATH` before setting the dedicated F5 activation-token directory and launching with explicit arguments.
- Source/test changes: external live wrapper plus `C:host-local/redacted_host/repo/tests/ultimate_book/test_risk_unit_floor.py`.
- Verification: risk-unit-floor/F5 wrapper suite `40 passed`.
- Deployment safety: broker read at the boundary found zero GTOS/F5 positions and zero GTOS/F5 pending orders. Only scheduled task `GTOS_F5_FTMO` was stopped and started; old leaf PID `11928` exited.
- Post-change proof: new leaf PID `14664`; heartbeat at 2026-08-13T16:06:39.616923Z was healthy, broker effect true, allocation profile `clean3_w7_ceiling_nom2p00`, dedicated activation-token directory present, and all three cleared variables null.
- Status: repaired, deployed, verified live; wrapper still needs durable Git placement and scoped commit/push reconciliation.

## D-003 — Daily-loss accounting omitted entry-side commission and broker fees

- Severity: critical safety-accounting defect class; small realized impact in the audited window, unsafe direction under larger flow or a mid-day anchor loss.
- Earliest causal root: both `.tools/monitor_books.py::snap` and `GovernorStateBuilder.reconstruct_day_start_balance` restricted account cash reconstruction to `DEAL_ENTRY_OUT` and omitted `fee`. MT5 charged four commissions on `DEAL_ENTRY_IN` today.
- Trigger evidence: the exact FTMO reset window contained 11 BUY/SELL deals. Exit-only logic reported `-$6.76`; every trading deal's `profit + commission + swap + fee` conserved to the broker balance at `-$7.82`. The omitted entry-side loss was `-$1.06`.
- Downstream consequence: the monitor understated daily loss; after loss/corruption of the persisted day anchor, a restarted live governor would also reconstruct a low day-start balance and overstate daily-loss headroom.
- Repair: added `src/utils/broker_accounting.py` as the shared strict BUY/SELL cash contract; both monitor and governor now include all trade sides and all four cash fields, exclude non-trading balance operations, and fail closed on unaccountable rows or history-fetch failure.
- Source/test changes: `.tools/monitor_books.py`, `src/components/ultimate_book/governor_state.py`, `src/utils/broker_accounting.py`, `tests/test_broker_accounting.py`, and governor tests; equivalent governor/accounting repair deployed into the active F5 worktree.
- Verification: main focused suites `33 passed`; F5 accounting/governor/wrapper suites `65 passed`. A post-repair one-shot monitor reported FTMO realized today as approximately `-$8` (rounded display). Direct live adapter reconstruction returned day-start balance `$108,331.37` and trading cash `-$7.82`.
- Deployment safety: both broker accounts had zero positions and zero pending orders immediately before reload. Only the two main book leaves, monitor leaf, and F5 scheduled worker were reloaded.
- Post-change process proof: main FTMO leaf `11400`, redacted_account leaf `10356`, monitor leaf `14256` cycle 0 with zero alerts, and F5 leaf `7896` were fresh and healthy after reload.
- Broker-day proof: `BROKER_DAY_TRUTH.json` passed all identity and conservation checks at 2026-08-13T16:24:43.523393Z. FTMO balance `$108,323.55`, equity `$108,323.55`, trading cash `-$7.82`, persisted firm reference `$108,337.43`, firm-window equity delta `-$13.88`; redacted_account balance/equity `$96,229.28`, zero trading cash, zero firm-window equity delta. Both accounts had zero current positions/orders.
- Status: repaired, deployed, verified live; pending broader regression, scoped commits, and push.
