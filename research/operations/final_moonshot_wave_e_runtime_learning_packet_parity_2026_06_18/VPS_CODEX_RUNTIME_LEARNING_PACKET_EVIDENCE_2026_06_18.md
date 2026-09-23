# VPS Codex Runtime-Learning Packet Evidence

Date: 2026-06-18
Branch: `vps/runtime-learning-packet-parity-2026-06-18`
Requested anchor: `ae50753ef48d4d49a45df430f3f1d1e91bb78354`
Evidence class: production-code observation layer and VPS packet parity checkpoint.

## Scope

This VPS checkpoint applied and verified only the Wave E runtime-learning packet parity surface:

- `src/components/ultimate_book/runtime_learning_packet.py`
- `src/components/ultimate_book/book_owner.py`
- `src/components/ultimate_book/book_engine.py`
- `src/components/ultimate_book/launcher.py`
- `src/components/ultimate_book/bridge.py`
- `config/agent_config.yaml`
- runtime-learning focused tests and route verifier artifacts.

No broker/account/order/deal/position mutation was performed for this checkpoint.

## Context And Instruction Coverage

Read after mandatory preflight:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/quick_reference_card.md`
- `.context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_DEPLOYMENT_LEDGER_2026_06_18.md`
- this route's prompt, schema, patch, verification result, value summary, and redaction audit.

Applied posture: scoped production-code observation-layer parity, no arbitrary top-N cutoff, same-evidence-class
pursuit through a failing required pytest regression, and forbidden-surface checks preserved.

## Patch Status

`src/components/ultimate_book/runtime_learning_packet.py` already existed on the requested branch and the active
config keys were present. The first required pytest run exposed a same-class parity failure:

- `tests/ultimate_book/test_book_owner.py::test_profile_missing_symbol_skips_before_engine_factory`
- failure: generation-level unsupported/profile-missing symbols were filtered before `TradeIntent` creation,
  so `UltimateBookOwner` did not report `profile_missing_instrument_config` in `summary["skipped"]`.

Repair applied in this VPS checkpoint:

- `UltimateBookLiveEngine` now preserves `generation_skips` for unsupported profile symbols.
- `UltimateBookOwner.run_cycle()` extends `summary["skipped"]` with those generation-level skips before cycle
  logging and runtime-learning packet emission.

This keeps unsupported-symbol skips visible to launcher logs and `unit_skipped` runtime-learning packets without
creating orders or touching broker state.

## Config Parity

Config file: `config/agent_config.yaml`
Config SHA-256 at verification: `2604fe8f98d161eb54c3a5c3f7eda34c910c752e75b5ff5cdf61577f29c5aa0e`

Verified keys:

- `ultimate_book_runtime_learning_packet_enabled: true`
- `ultimate_book_runtime_learning_packet_log_enabled: true`
- `ultimate_book_runtime_learning_packet_log_path: "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"`
- `ultimate_book_runtime_learning_packet_schema: "ultimate_book_runtime_learning_packet_v1"`
- `ultimate_book_runtime_learning_redaction_policy: "hash_ticket_and_account_identifiers_v1"`

Bridge defaults remain safe/off for the packet writer unless active config enables it.

## Verification

Commands run on the VPS worktree:

```powershell
C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe -m py_compile src\components\ultimate_book\runtime_learning_packet.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\launcher.py src\components\ultimate_book\bridge.py tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_launcher.py
C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe -m pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_launcher.py tests\ultimate_book\test_book_owner.py -q
C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18 --full-jsonl
git diff --check
```

Results:

- py_compile: passed.
- pytest: `46 passed`, with pre-existing `asyncio_mode` warning.
- verifier: `ok=true`, `issue_count=0`, `broker_runtime_change_status=false`, `orderflow_or_depth_used=false`.
- route artifact audit: `ok=true`, no missing required files, JSON/JSONL parse errors `0`.
- `git diff --check`: passed.

## Packet Log Path And Sample

Default log path: `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`

Synthetic redaction sample status:

- `validate_runtime_learning_packet(sample)` returned `ok=true`, `issues=[]`.
- Raw `ticket`, `account_login`, and `server` fields were not present in the packet.
- The packet contained `ticket_hash_sha256`, `account_login_hash_sha256`, `server_hash_sha256`, and
  `password_redacted=true`.
- Sample event type: `unit_skipped`.
- Sample skip reason: `profile_missing_instrument_config`.
- Sample `broker_runtime_change_status=false`.

No live packet sample was forced during this scoped parity verification because the existing live stack was
healthy and the branch prompt explicitly prohibited blind reload. A later intentional deployment/reload can
confirm live packet rows at the same log path.

## Live Process Health And No-Reload Proof

Observed live stack from the active runtime checkout at `C:\Users\MSI\Documents\ai-trading-agent`:

- Supervisor PID `5784`
- FTMO book shim PID `9728`, child PID `1180`
- redacted_account book shim PID `5068`, child PID `9724`
- Monitor shim PID `1352`, child PID `5952`

Heartbeats:

- FTMO: `{"ts":"2026-06-18T16:53:15.792785+00:00","pid":1180,"namespace":"operator_profile","healthy":true}`
- redacted_account: `{"ts":"2026-06-18T16:53:15.734284+00:00","pid":9724,"namespace":"redacted_account_live_bee34003","healthy":true}`

No reload was performed during this scoped branch verification.

## Rollback Proof

Observation-layer rollback only:

```yaml
ultimate_book_runtime_learning_packet_enabled: false
```

Optional disk-write brake while preserving status reporting:

```yaml
ultimate_book_runtime_learning_packet_log_enabled: false
```

This rollback disables only runtime-learning packet writes. It does not change ultimate-book admission, sizing,
order routing, broker positions, or existing runtime halt controls.

## Live-Branch Integration Addendum

Integrated on the active VPS live branch after the scoped parity branch was pushed:

- Target branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
- Starting live HEAD: `a9ca1d86ccf49ad563c7b8f1b63cef08cd9cc716`
- Runtime-learning source branch: `vps/runtime-learning-packet-parity-2026-06-18`
- Runtime-learning source commits: `ae50753ef48d4d49a45df430f3f1d1e91bb78354`, `fc61a09faec63da676e0951dadecd5dff6079dc7`

Merge disposition:

- The runtime-learning branch was not checked out over the live branch because it forked before `a9ca1d86`.
- Conflicts in `book_owner.py` and `book_engine.py` were resolved by preserving the live hardening and adding
  the observation-layer packet path.
- `book_engine.py` now returns both `generation` telemetry and `generation_skips`.
- `book_owner.py` keeps the live `no_tick_transient` retry semantics with `bar_consumable=false` and emits
  runtime-learning packets from the resulting skip rows.
- `bridge.py` preserves the live `kelly_running_count` and `derisk_mode` telemetry while adding packet defaults.

Integrated config SHA-256 before deployment reload:

`7ea8e4a3cfba10ea53c0997d993383a836ba0f76eb087bf38ff89b1b92aa00f2`

Integrated config parity:

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- `ultimate_book_runtime_learning_packet_enabled=true`
- `ultimate_book_runtime_learning_packet_log_enabled=true`
- `ultimate_book_runtime_learning_packet_log_path=shadow_logs/ultimate_book_runtime_learning_packets.jsonl`
- `ultimate_book_runtime_learning_packet_schema=ultimate_book_runtime_learning_packet_v1`
- `ultimate_book_runtime_learning_redaction_policy=hash_ticket_and_account_identifiers_v1`
- `ultimate_book_kelly_lite=true`
- `ultimate_book_kelly_running_count=true`
- `ultimate_book_stress_derisk=true`
- `ultimate_book_metals_confluence_gate=true`
- `ultimate_book_drop_w7_symbols=true`
- `ultimate_book_derisk_mode=smooth`

Integrated verification commands and results:

```powershell
python -m py_compile src\components\ultimate_book\runtime_learning_packet.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\launcher.py src\components\ultimate_book\bridge.py tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_launcher.py
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_launcher.py tests\ultimate_book\test_book_owner.py -q
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18 --full-jsonl
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
pytest $(rg --files tests\ultimate_book | rg market_expansion) -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python -m py_compile src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py src\components\ultimate_book\book_engine.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\runtime_learning_packet.py
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
git diff --cached --check
```

Results:

- Wave E py_compile: passed.
- Runtime-learning focused pytest: `48 passed`.
- Wave E verifier: `ok=true`, `issue_count=0`, `broker_runtime_change_status=false`, `orderflow_or_depth_used=false`.
- Wave E artifact audit: `ok=true`, `file_count=19`, JSON/JSONL parse errors `0`.
- Market-expansion runtime generator: `10 passed`.
- Market-expansion tagged tests: first run had `53 passed` but pytest failed the session snapshot guard because
  live supervisor/book heartbeat files changed during the run. After controlled GTOS process pause, rerun was
  clean: `53 passed`.
- Broader live-readiness test group: `44 passed`.
- Conditioned market-expansion verifier: `ok=true`, `issue_count=0`.
- Conditioned route artifact audit: `ok=true`, JSON/JSONL parse errors `0`.
- `git diff --cached --check`: passed.

Controlled live-process pause for clean tests:

```powershell
Disable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
Stop-Process -Id 1180 -Force
Stop-Process -Id 9724 -Force
Stop-Process -Id 5068 -Force
Stop-Process -Id 5952 -Force
Stop-Process -Id 1352 -Force
Stop-Process -Id 5784 -Force
```

Observed stopped PIDs:

- FTMO book child PID `1180`
- redacted_account book child PID `9724`
- redacted_account shim PID `5068`
- monitor child PID `5952`
- monitor shim PID `1352`
- supervisor PID `5784`

FTMO shim PID `9728` had already exited after child stop. No MT5 terminal, broker account, order, deal, or
position mutation command was run by this verification step.

## Post-Restart Runtime-Learning Discovery And Repair

The first integrated runtime-learning/launcher rows exposed a live-management bug outside the original Wave E
packet scope:

- FTMO ticket `159993636` appeared as both `JP225/idxrev` and
  `JP225_cash/mx_jp225_cash_d1_volume_surge_reversal`.
- Cause: `JP225` and `JP225_cash` can resolve to the same broker symbol on the FTMO profile. The manager
  deduped held tickets only inside one canonical-symbol loop, and the broker-symbol snapshot kept only one
  canonical alias per broker symbol.
- Risk: one broker ticket could be adopted into two execution engines and managed twice under different sleeve
  identities.

Repair applied:

- `UltimateBookOwner.manage_open_positions()` now keeps a pass-wide `claimed_tickets` set so a ticket already
  routed by comment or adoption cannot be adopted again through another canonical alias.
- residual/leftover adoption now respects W7 sleeve comments and placement-ledger pairs before adopting into a
  free engine.
- `_open_book_positions_by_canonical()` preserves every canonical alias for the same broker symbol instead of
  overwriting aliases in a single broker-to-canonical map.
- Added regression test:
  `tests/ultimate_book/test_book_owner.py::test_alias_broker_symbol_does_not_double_adopt_same_ticket`.

Post-repair verification:

```powershell
python -m py_compile src\components\ultimate_book\book_owner.py tests\ultimate_book\test_book_owner.py
pytest tests\ultimate_book\test_book_owner.py::test_alias_broker_symbol_does_not_double_adopt_same_ticket -q
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_launcher.py tests\ultimate_book\test_book_owner.py -q
```

Results:

- py_compile: passed.
- alias regression: `1 passed`.
- full `test_book_owner.py`: `30 passed`.
- broader live-readiness group: `44 passed`.
- runtime-learning focused group after repair: `49 passed`.

Runtime action:

- GTOS supervisor/book/monitor Python processes were paused again for clean pytest snapshot verification.
- No MT5 terminal, broker account, order, deal, or position mutation command was run by this repair step.

## Final VPS Deployment Proof After Alias Repair

Live branch:

- Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`.
- Local HEAD: `72a29a8677178e09369cb25857f596bf840f3dce`.
- Remote HEAD: `72a29a8677178e09369cb25857f596bf840f3dce`.
- Runtime-learning integration commit: `0d7f8f9c1b3cc210505dbbab50396ee458bc61a8`.
- Alias ticket double-adoption repair commit: `72a29a8677178e09369cb25857f596bf840f3dce`.

Config hash evidence:

- Pre-runtime-learning integration config blob SHA-256 at `a9ca1d86c`: `6c910370e1ed88a30294569a163b2444160f8d796047d45d3beedd2f1fdbe130`.
- Post-runtime-learning integration config blob SHA-256 at `0d7f8f9c1`: `0b3711fc102398c152d830a978a00697fd1ba23f187fc00141efc59462a5e2cd`.
- Post-alias-repair config blob SHA-256 at `72a29a867`: `0b3711fc102398c152d830a978a00697fd1ba23f187fc00141efc59462a5e2cd`.
- Live working-tree `config/agent_config.yaml` file SHA-256 after restart: `7EA8E4A3CFBA10EA53C0997D993383A836BA0F76EB087BF38FF89B1B92AA00F2`.

Active config parity:

- `selector_v4_apply_to_execution=false`.
- `ultimate_book_runtime_learning_packet_enabled=true`.
- `ultimate_book_runtime_learning_packet_log_enabled=true`.
- `ultimate_book_runtime_learning_packet_log_path=shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
- `ultimate_book_runtime_learning_packet_schema=ultimate_book_runtime_learning_packet_v1`.
- `ultimate_book_include_candidate_book=true`.
- `ultimate_book_include_market_expansion_book=true`.
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`.
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`.
- Kelly-lite, running-count, stress-derisk, smooth derisk, A8 metals confluence gate, and W7 dropped-symbol filter remain active.

Restart commands executed after the alias repair:

```powershell
Enable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
Start-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
```

Final scheduled task state:

- `GTOS_W7_BookSupervisor`: `Running`.

Final process tree:

- supervisor PID `8932`: `scripts\run_book_supervisor.ps1`.
- FTMO shim/child PIDs `6776` / `1004`: `run_book.py --terminal-path C:\MT5\FTMO\terminal64.exe --namespace operator_profile --profile operator_profile`.
- redacted_account shim/child PIDs `5172` / `4840`: `run_book.py --terminal-path C:\MT5\redacted_account\terminal64.exe --namespace redacted_account_live_bee34003 --profile redacted_account`.
- monitor shim/child PIDs `8384` / `1032`: `.tools\monitor_books.py --loop 300`.

Final heartbeat samples:

```json
{"ts": "2026-06-18T17:14:47.406522+00:00", "pid": 1004, "namespace": "operator_profile", "healthy": true}
{"ts": "2026-06-18T17:14:49.947760+00:00", "pid": 4840, "namespace": "redacted_account_live_bee34003", "healthy": true}
```

Final runtime-learning packet validation:

```json
{"last_event": "position_managed", "last_namespace": "redacted_account_live_bee34003", "last_packet_hash": "d82342b1f7af2b3f557e754025359c7936d85a4dfda2af6a58ed425769b96186", "packet_file": "shadow_logs\\ultimate_book_runtime_learning_packets.jsonl", "raw_key_hits": [], "tail_event_counts": {"position_adopted": 7, "position_managed": 28, "unit_admitted": 4, "unit_skipped": 42}, "tail_namespaces": {"operator_profile": 30, "redacted_account_live_bee34003": 51}, "tail_rows_checked": 81, "tail_validation_errors": 0, "total_rows": 81}
```

Final post-fix management samples:

- FTMO at `2026-06-18T17:12:45.209319+00:00`: adopted `UK100/idxrev/160080305` and `JP225/idxrev/159993636`; managed `UK100/idxrev` and `JP225/idxrev`; duplicate adopted tickets `[]`; runtime-learning emitted `4` packets.
- redacted_account at `2026-06-18T17:12:47.724285+00:00`: adopted `UK100/idxrev/246763216`; managed `UK100/idxrev`; duplicate adopted tickets `[]`; runtime-learning emitted `2` packets.
- The earlier XAUUSD/gold position was observed as `broker_closed` on both brokers at `2026-06-18T16:36:46-48Z`; latest post-fix management samples do not include XAUUSD/gold.

Monitoring paths:

- `shadow_logs/ultimate_book_launcher.jsonl`
- `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`
- `shadow_logs/book_supervisor.log`
- `shadow_logs/run_book_console.log`
- `shadow_logs/run_book_fn_console.log`
- `shadow_logs/monitor_daemon.log`
- `pipeline_state/ultimate_book/operator_profile/heartbeat.json`
- `pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json`

Rollback proof:

- Observation-only packet rollback: set `ultimate_book_runtime_learning_packet_enabled=false` or `ultimate_book_runtime_learning_packet_log_enabled=false` in `config/agent_config.yaml`, then restart `GTOS_W7_BookSupervisor`.
- Full runtime-learning code rollback: `git revert 0d7f8f9c1b3cc210505dbbab50396ee458bc61a8`, then restart `GTOS_W7_BookSupervisor`.
- Alias repair rollback, only if a regression is proven: `git revert 72a29a8677178e09369cb25857f596bf840f3dce`, then restart `GTOS_W7_BookSupervisor`.
- Market-expansion behavior rollback: set `ultimate_book_market_expansion_policy=robust6_every_split_positive`, or set `ultimate_book_include_market_expansion_book=false` for full market-expansion-off, then restart `GTOS_W7_BookSupervisor`.
- No rollback command was executed during final deployment proof because post-fix task state, heartbeats, packet validation, and duplicate-ticket checks were healthy.

## Post-Push Live Placement And Broker-Real Snapshot

After the final evidence push, the live supervisor continued cycling and admitted/placed crypto sleeve trades on both
brokers. This was observed rather than manually forced.

Launcher evidence at `2026-06-18T17:15:47-50Z`:

- FTMO `cycle`: placed `BTCUSD/ny_crypto_momentum` and `ETHUSD/ny_crypto_momentum`.
- redacted_account `cycle`: placed `BTCUSD/ny_crypto_momentum` and `ETHUSD/ny_crypto_momentum`.

Runtime-learning packet validation after those placements:

```json
{"last_event": "position_managed", "last_namespace": "redacted_account_live_bee34003", "last_packet_hash": "f85bab58dcb568c99efa081571a89aa1df51a718930662076c4f29a7df0d19af", "raw_key_hits": [], "tail_event_counts": {"position_adopted": 7, "position_managed": 38, "unit_admitted": 6, "unit_placed": 4, "unit_skipped": 46}, "tail_namespaces": {"operator_profile": 39, "redacted_account_live_bee34003": 62}, "tail_rows_checked": 101, "tail_validation_errors": 0, "total_rows": 101}
```

Read-only MT5 `positions_get()` snapshot at `2026-06-18T17:18:25Z`:

- FTMO open positions:
  - `JP225.cash` SELL, ticket `159993636`, sleeve comment `W7:idxrev`, volume `2.36`, SL `72269.15`, TP `70302.64`.
  - `UK100.cash` BUY, ticket `160080305`, sleeve comment `W7:idxrev`, volume `1.82`, SL `10352.66`, TP `10471.47`.
  - `BTCUSD` SELL, ticket `160212977`, sleeve comment `W7:ny_crypto_mom`, volume `0.35`, SL `62981.39`, TP `0.0`.
  - `ETHUSD` SELL, ticket `160212979`, sleeve comment `W7:ny_crypto_mom`, volume `1.05`, SL `1700.21`, TP `0.0`.
- redacted_account open positions:
  - `UK100` BUY, ticket `246763216`, sleeve comment `W7:idxrev`, volume `0.19`, SL `10357.02`, TP `10473.39`.
  - `BTCUSD` SELL, ticket `246872998`, sleeve comment `W7:ny_crypto_mom`, volume `0.37`, SL `62996.70`, TP `0.0`.
  - `ETHUSD` SELL, ticket `246872999`, sleeve comment `W7:ny_crypto_mom`, volume `11.13`, SL `1700.41`, TP `0.0`.

Gold/XAU status:

- No XAUUSD/gold position was present in the `2026-06-18T17:18:25Z` broker-real read-only snapshot.
- The earlier XAUUSD/gold trades remain classified as broker-closed in launcher evidence.
