# VPS Runtime Ultimate Monitoring Repair Evidence

Date: 2026-06-18 UTC
Evidence class: production-code integration, runtime observation, broker-profile parity, deployment-readiness verification.
Forbidden surfaces during this checkpoint: no broker/account/order/deal/position mutation, no credential mutation, no paid/vendor calls.

## Current Branch

- Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
- Pre-commit HEAD inspected: `18688ed7c6468c94f26fe79d4d4fe15430ea1d17`
- Remote parity before edits: local branch matched `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`.
- Runtime-learning branch state checked: `origin/vps/runtime-learning-packet-parity-2026-06-18` at `fc61a09fa`.
  Follow-up audit on 2026-06-18 confirmed `fc61a09fa` is not a direct Git ancestor of the active
  ultimate branch. The scoped checkpoint is functionally absorbed through the ultimate-branch integration
  commits (`0d7f8f9c1` plus later hardening in `7c1a51d0f`), not through a literal branch merge. The active
  branch intentionally does not import unrelated runtime-learning branch history.

## Production-Code Repairs

- Runtime-learning packets are now stricter and more joinable:
  - unknown event types rejected;
  - `source_event_hash_sha256` and `packet_hash_sha256` recomputed by validator;
  - `unit_admitted` uses `decision_reason` / `admission_reason` instead of falsely filling `skip_reason`;
  - placed/adopted/managed/closed packets include redacted `ticket_hash_sha256`, broker symbol, decision/candidate/policy context, placement/management timestamps, and joinability status.
- Trade records now persist decision bar, decision day, cluster, broker symbol, placed timestamp, and redacted ticket hash so restart adoption can rehydrate and packetize management with the original decision context.
- Broker net-cost gate now converts adverse side-aware swap to R-cost where MT5 source fields support it:
  - mode 1 points conversion;
  - mode 5/6 annual-interest conversion;
  - required conversion fails closed when source fields are missing or unsupported;
  - total cost now includes spread, expected slippage, and swap-cost R;
  - live config enables the swap-cost requirement with a 1-day gate horizon cap.
- Pytest production-path guard now recognizes the current W7 supervisor and per-book heartbeat files, preventing false failures while live processes write expected telemetry.
- Broker-profile verifier now has an explicit `ultimate-active` surface:
  - it builds the current 46-symbol ultimate-book universe from `active_specs()`;
  - it uses the same alias resolution as production config;
  - it can report intentional broker-alias collisions and direct-VPS-confirmed redacted_account missing instruments without hiding them behind the older 24-symbol verifier.
- Stale redacted_account oil alias wording in `symbol_map.py` was corrected to `USOIL_cash -> USOUSD`.

## Active Config Parity

Verified from `config/agent_config.yaml`, launcher packets, and route verifiers:

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- Kelly-lite active.
- Kelly conservative active.
- Kelly running count active.
- Stress derisk active with `derisk_mode=smooth`.
- A8/metals confluence gate active.
- W7 dropped-symbol filter active.

Config hash before reload, after local config repair:

```text
config/agent_config.yaml SHA256 C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C
```

## Broker Profile Parity

Commands run:

```powershell
python scripts\verify_broker_profile.py config\profiles\operator_profile.yaml --surface ultimate-active --allow-duplicate-broker-aliases
python scripts\verify_broker_profile.py config\profiles\redacted_account.yaml --surface ultimate-active --allow-known-redacted_account-active-gaps --allow-duplicate-broker-aliases
```

Results:

- FTMO active surface: `ok=true`, `active_symbol_count=46`, `issue_count=0`.
- FTMO intentional duplicate alias groups:
  - `GER40/GER40_cash -> GER40.cash`
  - `JP225/JP225_cash -> JP225.cash`
  - `NAS100/US100_cash -> US100.cash`
  - `SPX500/US500_cash -> US500.cash`
- redacted_account active surface: `ok=true`, `active_symbol_count=46`, `issue_count=0` with `missing_symbols_allowed_count=10`.
- redacted_account direct-VPS-confirmed unavailable active symbols:
  - `AVAUSD`
  - `CORN_c`
  - `COTTON_c`
  - `DASHUSD`
  - `XAGAUD`
  - `XAGEUR`
  - `XAUAUD`
  - `XAUEUR`
  - `XPDUSD`
  - `XTZUSD`
- redacted_account intentional duplicate alias groups:
  - `GER40/GER40_cash -> GER30`
  - `JP225/JP225_cash -> JP225`
  - `NAS100/US100_cash -> NDX100`
  - `SPX500/US500_cash -> SPX500`

Interpretation: FTMO has full current active-universe profile support. redacted_account is a reduced active universe by real broker availability, not a naming bug; runtime should skip those symbols fail-closed and report the reduced breadth.

## Verification Commands

```powershell
python -m py_compile src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py src\components\ultimate_book\runtime_learning_packet.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\launcher.py src\components\ultimate_book\symbol_map.py src\components\broker_net_cost_engine.py scripts\verify_broker_profile.py tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_book_owner.py tests\test_broker_net_cost_engine.py tests\test_verify_broker_profile.py
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_book_owner.py tests\test_broker_net_cost_engine.py tests\ultimate_book\test_launcher.py tests\test_verify_broker_profile.py tests\ultimate_book\test_active_broker_profile_parity.py -q
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
$files = rg --files tests/ultimate_book | rg 'market_expansion'; pytest $files -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
```

Results:

- `py_compile`: passed.
- Focused live-facing pytest: `72 passed`.
- Market-expansion conditioned policy runtime alias verifier: `ok=true`, `issue_count=0`.
- Wave E runtime-learning packet parity verifier: `ok=true`, `issue_count=0`.
- Market-expansion runtime generator: `10 passed`.
- All ultimate-book market-expansion tests: `53 passed`.
- Broader ultimate-book/runtime smoke: `44 passed`.
- Route artifact audit: `ok=true`, `json_parse_error_count=0`, `jsonl_parse_error_count=0`.

The market-expansion sweep reported only live monitor/runtime packet files changing while live processes were active; pytest-process protected-path writes remained hard guarded.

## Live Runtime Snapshot Before Reload

Captured read-only at `2026-06-18T18:51:45Z`.

Scheduled task:

- `GTOS_W7_BookSupervisor` state: running.

Processes:

- FTMO MT5 terminal: PID `4524`
- redacted_account MT5 terminal: PID `6060`
- Book supervisor: PID `8932`
- FTMO book launcher/worker: PIDs `6776` / `1004`
- redacted_account book launcher/worker: PIDs `5172` / `4840`

Supervisor heartbeat:

```json
{"ts":"2026-06-18T18:51:25.7783970Z","pid":8932}
```

Runtime packet log path:

- `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`
- Line count at snapshot: `795`
- Latest packet rows showed active candidate book, active market expansion, `positive_weighted12_after_swap`, smooth derisk, W7 drop, Kelly-lite, Kelly running count, and `broker_runtime_change_status=false`.

Launcher log path:

- `shadow_logs/ultimate_book_launcher.jsonl`
- Latest cycles at `18:45:55Z` FTMO and `18:45:57Z` redacted_account showed `place=true`, `halted=false`, `killed=false`, `runtime_effect_now=true`, `no_candidates_this_bar`.

## Live Broker Snapshot Before Reload

Read-only MT5 account/position snapshot at `2026-06-18T18:51:45Z`.

FTMO:

- Balance: `96644.55`
- Equity: `96339.13`
- Floating profit: `-305.42`
- Positions:
  - `JP225.cash` SELL ticket `159993636`, volume `2.36`, open `71142.0`, current `72059.5`, SL `72269.15`, TP `70302.64`, PnL `-133.97`, comment `W7:idxrev`.
  - `UK100.cash` BUY ticket `160080305`, volume `1.82`, open `10420.55`, current `10411.8`, SL `10352.66`, TP `10471.47`, PnL `-21.04`, comment `W7:idxrev`.
  - `BTCUSD` SELL ticket `160212977`, volume `0.35`, open `62487.45`, current `62808.87`, SL `62981.39`, TP `0.0`, PnL `-112.50`, comment `W7:ny_crypto_mom`.
  - `ETHUSD` SELL ticket `160212979`, volume `1.05`, open `1683.1`, current `1686.71`, SL `1700.21`, TP `0.0`, PnL `-37.91`, comment `W7:ny_crypto_mom`.
- Gold/XAU positions: none.

redacted_account:

- Balance: `99023.81`
- Equity: `98824.81`
- Floating profit: `-199.00`
- Positions:
  - `UK100` BUY ticket `246763216`, volume `0.19`, open `10423.53`, current `10406.66`, SL `10357.02`, TP `10473.39`, PnL `-42.33`, comment `W7:idxrev`.
  - `BTCUSD` SELL ticket `246872998`, volume `0.37`, open `62507.58`, current `62847.7`, SL `62996.7`, TP `0.0`, PnL `-125.84`, comment `W7:ny_crypto_mom`.
  - `ETHUSD` SELL ticket `246872999`, volume `11.13`, open `1683.76`, current `1686.53`, SL `1700.41`, TP `0.0`, PnL `-30.83`, comment `W7:ny_crypto_mom`.
- Gold/XAU positions: none.

Interpretation: there was no active gold trade at the snapshot. Existing open positions had broker SLs. Crypto positions use native/software time-stop management with broker TP omitted by design; they were opened at `17:15Z`, so the 20-M15-bar time stop was not due by `18:51Z`.

## Deployment Status

A controlled reload was performed after commit `7c1a51d0fb51ec75c95712590e42e3604b71cd93` so the live workers run the verified package.

Reload command executed:

```powershell
$task = 'GTOS_W7_BookSupervisor'
$stopPids = @(1004,6776,4840,5172,1032,8384,8932)
Disable-ScheduledTask -TaskName $task | Out-Null
$stopped = @()
foreach ($pidToStop in $stopPids) {
  $p = Get-Process -Id $pidToStop -ErrorAction SilentlyContinue
  if ($p) {
    Stop-Process -Id $pidToStop -Force -ErrorAction Stop
    $stopped += $pidToStop
  }
}
Start-Sleep -Seconds 3
Enable-ScheduledTask -TaskName $task | Out-Null
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 12
```

Reload proof:

- Stopped supervisor/book/monitor PIDs: `1004`, `6776`, `4840`, `5172`, `1032`, `8384`, `8932`.
- Scheduled task after reload: `GTOS_W7_BookSupervisor` running.
- MT5 terminal PIDs unchanged and not stopped: FTMO `4524`, redacted_account `6060`.
- New supervisor PID: `1456`.
- New FTMO book launcher/worker PIDs: `2196` / `8848`.
- New redacted_account book launcher/worker PIDs: `8160` / `1284`.
- New monitor launcher/worker PIDs: `5876` / `6548`.
- Config hash before reload: `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`.
- Config hash after reload: `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`.

Post-reload heartbeats:

```json
{"ts":"2026-06-18T18:59:26.9612369Z","pid":1456}
{"ts":"2026-06-18T18:58:52.893400+00:00","pid":8848,"namespace":"operator_profile","healthy":true}
{"ts":"2026-06-18T18:58:55.760857+00:00","pid":1284,"namespace":"redacted_account_live_bee34003","healthy":true}
```

Post-reload runtime packet proof:

- Packet log path: `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
- Line count after reload: `881`.
- Post-reload rows validated: `44`.
- Post-reload packet validation errors: `0`.
- Post-reload event counts: `position_adopted=7`, `position_managed=14`, `unit_admitted=2`, `unit_skipped=21`.
- New `position_managed` rows include `ticket_hash_sha256`, `broker_symbol`, `management_checked_at_utc`, `trade_record_status`, `candidate_id`, decision time/as-of, entry/SL/TP, selected dynamic policy, time-stop bars, selected-cell risk, selector/scheduler hashes, and joinability status.

Post-reload launcher proof:

- `shadow_logs/ultimate_book_launcher.jsonl` line count after reload: `74`.
- FTMO reload cycle at `2026-06-18T18:58:52.893400+00:00` ran management, then evaluated `[16388, 15, 16408]` with `place=true`, `halted=false`, `killed=false`, `runtime_effect_now=true`, and active candidate/market-expansion bridge flags.
- redacted_account reload cycle at `2026-06-18T18:58:55.760857+00:00` ran management, then evaluated `[16388, 15, 16408]` with `place=true`, `halted=false`, `killed=false`, `runtime_effect_now=true`, and active candidate/market-expansion bridge flags.
- No new placement occurred during reload; the cycle skipped already-held symbols and unsupported redacted_account instruments fail-closed.

Post-reload broker snapshot at `2026-06-18T18:59:47Z`:

- FTMO balance `96644.55`, equity `96399.74`, floating `-244.81`, positions `4`, gold/XAU positions `0`.
- redacted_account balance `99023.81`, equity `98891.14`, floating `-132.67`, positions `3`, gold/XAU positions `0`.
- Open tickets were the same broker positions observed before reload; PnL changed only by market movement.

## Follow-Up Runtime Joinability Repair And Reload

At `2026-06-18T19:25Z` through `2026-06-18T19:35Z`, a follow-up repair closed the remaining
runtime-intelligence gap found during live monitoring: older active trade-record files did not all carry the
new runtime-learning join keys after restart.

Additional source repairs:

- `PlacementLedger` now indexes the full durable placement row by ticket and exposes `row_for_ticket()`.
- `UltimateBookOwner._load_trade_record()` now normalizes legacy records from the placement ledger and
  persists missing decision bar, decision day, cluster, candidate id, placement timestamp, broker symbol, and
  ticket hash.
- Close paths now persist observed lifecycle state (`trade_lifecycle_status=closed`, `close_action`,
  `closed_at_utc`) for time-stop, tick-managed, breach-flatten, and operator-flatten exits without touching
  broker state.
- Runtime management packets now include normalized `trade_record_joinability_status`,
  `trade_lifecycle_status`, `placement_observed_at_utc`, cluster, decision bar/day, and candidate id where
  source-bound.
- Reconstructed legacy index records remain honest: they normalize to `ticket_policy_joinable` when the
  original decision/candidate row was not source-bound, instead of fabricating a full decision join.

Additional verification commands:

```powershell
python -m py_compile src\components\ultimate_book\book_owner.py src\components\ultimate_book\placement_ledger.py tests\ultimate_book\test_book_owner.py tests\ultimate_book\test_placement_ledger.py
pytest tests\ultimate_book\test_placement_ledger.py -q
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_runtime_learning_packet.py -q
python -m py_compile src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\placement_ledger.py
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
pytest $(rg --files tests/ultimate_book | rg 'market_expansion') -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python research\operations\vps_runtime_ultimate_monitoring_repair_2026_06_18\verify_vps_runtime_ultimate_monitoring_repair.py
python scripts\audit_goal_route_artifacts.py research\operations\vps_runtime_ultimate_monitoring_repair_2026_06_18 --full-jsonl
```

Additional verification results:

- `py_compile`: passed.
- Placement ledger tests: `6 passed`.
- Book owner tests: `31 passed`.
- Runtime-learning packet tests: `6 passed`.
- Market-expansion runtime generator: `10 passed`.
- All ultimate-book market-expansion tests: `53 passed`.
- Broader ultimate-book/runtime smoke: `44 passed`.
- VPS runtime route verifier: `ok=true`, `issue_count=0`.
- VPS runtime route artifact audit: `ok=true`, `json_parse_error_count=0`, `jsonl_parse_error_count=0`.
- `python3` command is not installed on this Windows VPS; the active `python` / `.venv-gtos\Scripts\python.exe`
  interpreter was used.

Follow-up reload pre-snapshot:

- Config hash before reload:
  `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`.
- Supervisor PID: `1456`.
- FTMO book launcher/worker PIDs: `2196` / `8848`.
- redacted_account book launcher/worker PIDs: `8160` / `1284`.
- Monitor launcher/worker PIDs: `5876` / `6548`.
- Pre-reload heartbeats:

```json
{"ts":"2026-06-18T19:31:41.9332870Z","pid":1456}
{"ts":"2026-06-18T19:32:00.931853+00:00","pid":8848,"namespace":"operator_profile","healthy":true}
{"ts":"2026-06-18T19:32:02.818338+00:00","pid":1284,"namespace":"redacted_account_live_bee34003","healthy":true}
```

Follow-up reload command executed:

```powershell
$targets = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_book.py*' -or $_.CommandLine -like '*monitor_books.py*' } |
  Select-Object -ExpandProperty ProcessId
foreach ($pidToStop in $targets) {
  Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 45
```

Follow-up reload proof:

- Stopped book/monitor PIDs: `2196`, `8848`, `8160`, `1284`, `5876`, `6548`.
- Supervisor stayed live: PID `1456`.
- New FTMO book launcher/worker PIDs: `5732` / `7364`.
- New redacted_account book launcher/worker PIDs: `9068` / `5080`.
- New monitor launcher/worker PIDs: `9520` / `2404`.
- Config hash after reload:
  `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`.
- Post-reload heartbeats:

```json
{"ts":"2026-06-18T19:33:48.9340965Z","pid":1456}
{"ts":"2026-06-18T19:33:46.323049+00:00","pid":7364,"namespace":"operator_profile","healthy":true}
{"ts":"2026-06-18T19:33:49.227414+00:00","pid":5080,"namespace":"redacted_account_live_bee34003","healthy":true}
```

Post-reload packet proof:

- Monitoring path: `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
- New BTC/ETH management rows include `decision_bar_iso=2026-06-18T17:00:00+00:00`,
  `decision_day=2026-06-18`, `cluster=crypto`, `placement_observed_at_utc`, `candidate_id`,
  `ticket_hash_sha256`, and `trade_record_joinability_status=ticket_candidate_decision_policy_joinable`.
- Reconstructed legacy index rows include `cluster=index`, `ticket_hash_sha256`, and
  `trade_record_joinability_status=ticket_policy_joinable`.
- No runtime error patterns matched in `shadow_logs\run_book_console.log*`,
  `shadow_logs\run_book_fn_console.log*`, `shadow_logs\monitor_daemon.*`, or `shadow_logs\book_supervisor.log`.

Read-only broker snapshot after follow-up reload at `2026-06-18T19:34:47Z`:

- FTMO balance `96644.55`, equity `96264.91`, floating `-379.64`, positions `4`, gold/XAU positions `0`.
- FTMO open tickets:
  - `JP225.cash` SELL `159993636`, SL present, record status `ticket_policy_joinable`.
  - `UK100.cash` BUY `160080305`, SL present, record status `ticket_policy_joinable`.
  - `BTCUSD` SELL `160212977`, SL present, record status `ticket_candidate_decision_policy_joinable`.
  - `ETHUSD` SELL `160212979`, SL present, record status `ticket_candidate_decision_policy_joinable`.
- redacted_account balance `99023.81`, equity `98737.40`, floating `-286.41`, positions `3`, gold/XAU positions `0`.
- redacted_account open tickets:
  - `UK100` BUY `246763216`, SL present, record status `ticket_policy_joinable`.
  - `BTCUSD` SELL `246872998`, SL present, record status `ticket_candidate_decision_policy_joinable`.
  - `ETHUSD` SELL `246872999`, SL present, record status `ticket_candidate_decision_policy_joinable`.

## Rollback Proof

Observation-layer rollback:

```yaml
gtos_vnext_runtime:
  ultimate_book_runtime_learning_packet_enabled: false
```

Swap-cost gate rollback:

```yaml
gtos_vnext_runtime:
  selected_cell_swap_cost_model_required: false
```

Market-expansion risk rollback:

```yaml
gtos_vnext_runtime:
  ultimate_book_include_market_expansion_book: false
  ultimate_book_market_expansion_policy: robust6_every_split_positive
```

Full ultimate-book placement pause without position mutation:

```powershell
New-Item -ItemType File -Force pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag
New-Item -ItemType File -Force pipeline_state\ULTIMATE_BOOK_KILL_fn.flag
```

Supervisor stop without touching MT5 terminal processes or broker positions:

```powershell
Disable-ScheduledTask -TaskName GTOS_W7_BookSupervisor
Stop-Process -Id <book-supervisor-and-child-python-pids> -Force
```

Restart after code/config rollback:

```powershell
Enable-ScheduledTask -TaskName GTOS_W7_BookSupervisor
Start-ScheduledTask -TaskName GTOS_W7_BookSupervisor
```

Broker/order/deal/position rollback by forced close was not executed in this checkpoint.
