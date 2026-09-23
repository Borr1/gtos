# CODEX_FTMO_FOLLOWER_PERSISTENCE_REPAIR_CHECKPOINT_2026-06-02_1645Z

Recorded at: `2026-06-02T16:45:29Z`

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`

Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`

Runtime boundary: code repair, stale temp cleanup, and FTMO follower relaunch only. No manual broker order, position, deal, SL, or TP mutation was performed.

HEAD before repair checkpoint: `8c12a5e8cc1b56acac285c72afb312833e3fac7e`

## Current Answer

The live candidate/intent lifecycle looked clean after the 16:16Z checkpoint, but the FTMO follower process itself was not clean: it had exited at 16:35Z after a Windows `PermissionError` while replacing the persisted target trade-state JSON. That left the dual-broker shape without the active FTMO management/follow process until repaired.

The active defect is now repaired, tested, and reloaded. The current process shape is back to one full redacted_account brain plus one lightweight FTMO follower.

## Candidate And Intent Lifecycle

Local inspection and the read-only explorer audit agreed:

- `pipeline_state/dual_broker/canonical_trade_intents.jsonl` had 27 rows and no canonical intents after `2026-06-02T16:16:00Z`.
- The `2026-06-02T16:30:00Z` XAUUSD candidate was correctly skipped before intent/order projection: `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`.
- XAUUSD 16:30 refusal causes were explicit: `candidate_quality_spread_r_exceeds_selected_denominator_limit`, `framework_not_activated_in_stage13_full_moonshot_selector`, and `selected_cell_risk_not_verified_or_zero`.
- The 15:00 XAUUSD trade was a real SL close on both brokers, not a follower phantom. redacted_account position `242624062` closed with broker close deal `226436227`, comment `[sl 4491.73]`, profit `-246.24`; FTMO position `155135981` closed with broker close deal `145896564`, comment `[sl 4491.73]`, profit `-242.46`.
- The redacted_account XAUUSD 15:00 record is terminal-exit updated: `exit_type=broker_closed`, `exit_reason=SL`, `residual_volume=0.0`, `open_worst_case_cash_risk_status=released_by_terminal_exit`.
- Trade management/exit events did not become new entry intents. The follower action log after 16:16Z contained XAUUSD `broker_closed` and USDJPY `tp1_partial_vnext_partial_be_runner`, while the canonical intent log remained unchanged after 15:46Z.

## Active Defect Found

At 16:40Z process inspection showed:

- `redacted_account_run_agent=24`
- `ftmo_run_agent=0`
- `unscoped_run_agent=0`
- `ftmo_follower=0`
- `projector=1`
- `terminal64=2`

The follower had last updated its checkpoint at `2026-06-02T16:35:29Z`. The log root cause was:

```text
PermissionError: [WinError 5] Access is denied:
pipeline_state\operator_profile\dual_broker_target_trade_state.5828.tmp
-> pipeline_state\operator_profile\dual_broker_target_trade_state.json
```

This occurred after a valid USDJPY TP1 partial management event and killed the process during target-state persistence. The leftover `.tmp` had the same active tickets and trade-state content as the durable state, with only timestamp differences, so it was removed as stale temp evidence.

## Repair

Changed `scripts/dual_broker_execution_follower.py`:

- `_write_json()` now retries transient `PermissionError` file-lock failures up to 5 times.
- If Windows still refuses the replace, it logs the skipped persistence and returns instead of terminating the live follower.
- Non-permission filesystem errors also log and return, preserving the previous durable state.

Changed `tests/test_dual_broker_execution_follower.py`:

- Added a retry regression for transient `PermissionError`.
- Added a repeated-lock regression proving the previous JSON state is not clobbered and the caller does not raise.

Verification:

- `python -m py_compile scripts\dual_broker_execution_follower.py` passed.
- `python -m pytest tests\test_dual_broker_execution_follower.py -q` passed: `22 passed`.

## Relaunch

Only the FTMO follower was relaunched:

```text
python scripts\dual_broker_execution_follower.py --mode live --profile operator_profile --runtime-namespace operator_profile --source-runtime-namespace redacted_account_live_bee34003 --terminal-path C:\MT5\FTMO\terminal64.exe --intent-log pipeline_state\dual_broker\canonical_trade_intents.jsonl --order-enabled
```

Post-relaunch evidence:

- PID `3888`
- `order_enabled=true`
- `replay_existing=false`
- source namespace `redacted_account_live_bee34003`
- target namespace `operator_profile`
- intent offset `5881061`
- processed intent count `0`
- recovered active engine symbols: `BTCUSD`, `GBPJPY`, `JP225`, `NAS100`, `NZDUSD`, `UK100`, `USDCAD`, `USDJPY`

The follower did not replay stale entry intents. XAUUSD is absent from the recovered symbols because it was already broker-closed.

## Post-Repair State

Post-relaunch process/memory checkpoint at `2026-06-02T16:44:18Z`:

- free memory: `1831.9 MB`
- `redacted_account_run_agent=24`
- `ftmo_run_agent=0`
- `unscoped_run_agent=0`
- `ftmo_follower=1`
- `projector=1`
- `terminal64=2`
- `redacted_account_tick_capture=24`
- `m1_capture=1`
- `notification_worker=1`

Read-only MT5 probe at `2026-06-02T16:44:27Z`:

- redacted_account: `11` positions, `0` orders
- FTMO: `8` positions, `0` orders
- Account identity matched both profiles.
- FTMO symbol specs exist for all 24 configured symbols; 19 had positive ticks without mass-select, 5 remained absent/unselected by the no-mass-select policy.
- redacted_account had 24/24 positive ticks.

FTMO target-state reconciliation:

- target state updated at `2026-06-02T16:44:45Z`
- target active count `8`
- broker positions `8`
- missing target tickets in broker: `[]`
- extra broker tickets not in target state: `[]`

Current FTMO risk snapshot from `DUAL_RISK_EXPOSURE_LEDGER.jsonl`:

- balance `97959.74`
- equity `97968.94`
- margin `13889.57`
- free margin `84070.17`
- positions `8`
- orders `0`

## Remaining

Continue live supervision. No active post-16:16 candidate/intent defect is proven. The process defect found in this cycle was real and has been repaired/reloaded. The remaining architectural design question is whether future broker-local management should be made even more autonomous per account, but the current lightweight follower is now again active and managing the target account from broker-local state.
