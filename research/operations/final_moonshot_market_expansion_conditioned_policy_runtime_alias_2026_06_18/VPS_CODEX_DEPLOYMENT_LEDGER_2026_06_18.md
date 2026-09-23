# VPS Codex Deployment Ledger

Date: 2026-06-18
Host repo: `C:\Users\MSI\Documents\ai-trading-agent`
Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
Required commit: `96f53b63de04c85643395d6ec62b776802065ddc`
Pre-deployment code HEAD: `508e929c252aa06cb7291938d816c0ab8d90ad68`
Required commit ancestor check: `true`

## Runtime Package

Active runtime config parity was verified from `config/agent_config.yaml`:

- `ultimate_book_enabled: true`
- `ultimate_book_apply_to_execution: true`
- `ultimate_book_live_activation_allowed: true`
- `selector_v4_apply_to_execution: false`
- `ultimate_book_include_candidate_book: true`
- `ultimate_book_candidate_book_profile: runtime_executable_native_exit_v2`
- `ultimate_book_include_market_expansion_book: true`
- `ultimate_book_market_expansion_policy: positive_weighted12_after_swap`
- `ultimate_book_profile: clean3_w7_ceiling_nom2p00`
- `ultimate_book_kelly_lite: true`
- `ultimate_book_kelly_conservative: true`
- `ultimate_book_kelly_running_count: true`
- `ultimate_book_stress_derisk: true`
- `ultimate_book_derisk_mode: smooth`
- `ultimate_book_metals_confluence_gate: true`
- `ultimate_book_drop_w7_symbols: true`

Config SHA-256 before and after reload:

`98AD6D2300DA7AD846210959934AED063EABB481B7CAB7B45771A3D1F7CC1403`

`.env` also carries `GTOS_UB_DERISK_MODE=smooth`; YAML fallback is present via
`ultimate_book_derisk_mode: smooth`.

## Verification

Commands run successfully before reload:

```powershell
python scripts/generate_live_state.py
python -m py_compile src/components/ultimate_book/admission.py src/components/ultimate_book/bridge.py src/components/ultimate_book/sleeves/candidate_registry.py src/components/ultimate_book/sleeves/market_expansion_d1.py
python research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/verify_market_expansion_conditioned_policy_runtime_alias.py
pytest tests/ultimate_book/test_market_expansion_runtime_generator.py -q
$files = @(rg --files tests/ultimate_book | rg 'market_expansion'); pytest @files -q
pytest tests/ultimate_book/test_candidate_promotion_plumbing.py tests/ultimate_book/test_order_route.py tests/ultimate_book/test_book_engine.py tests/ultimate_book/test_candidate_book_consistency.py tests/ultimate_book/test_active_registry_and_softband_audit.py tests/test_dynamic_target_stop_geometry_v4.py tests/test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests/test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
```

Results:

- Runtime alias verifier: clean, `issue_count=0`.
- Market-expansion generator: `8 passed`.
- All market-expansion tests: `51 passed`.
- Candidate/order/book/dynamic-target/limit-flow regression: `41 passed`.
- Route artifact audit: `ok=true`.

Focused post-reload checks:

```powershell
python -m py_compile run_book.py src/components/ultimate_book/bridge.py src/components/ultimate_book/book_owner.py
$null = [scriptblock]::Create((Get-Content scripts\run_book_supervisor.ps1 -Raw)); 'supervisor_parse_ok'
pytest tests/ultimate_book/test_launcher.py tests/ultimate_book/test_market_expansion_runtime_generator.py -q
```

Result: `22 passed`.

Windows lock probes:

- Windows mutex probe: second same-name mutex returned `ERROR_ALREADY_EXISTS`.
- Windows file-lock probe: second non-blocking lock was blocked.

## Pre-Reload Packet Parity

Pure bridge probe with engine-equivalent `GovernorLimits(derisk_mode="smooth")` admitted a sample
market-expansion intent with these fields:

- `decision_status: admitted_book_authority`
- `runtime_effect_now: true`
- `candidate_use_allowed_now: true`
- `include_candidate_book: true`
- `include_market_expansion_book: true`
- `market_expansion_policy: positive_weighted12_after_swap`
- `market_expansion_sleeves`: 12 resolved sleeves
- `kelly_running_count: true`
- `stress_derisk: true`
- `derisk_mode: smooth`
- `metals_confluence_gate: true`
- `drop_w7_symbols: true`
- `realized_units`: sample `mx_btcusd_d1_donchian_20_breakout` unit

Bridge default config remained safe/off:

- `ultimate_book_enabled: false`
- `ultimate_book_apply_to_execution: false`
- `ultimate_book_live_activation_allowed: false`
- `ultimate_book_include_candidate_book: false`
- `ultimate_book_include_market_expansion_book: false`
- `ultimate_book_market_expansion_policy: explicit_allowlist`
- `ultimate_book_metals_confluence_gate: false`

## Activation Commands

Hard halt / autostart flags were removed from the repo worktree:

```powershell
Remove-Item -LiteralPath pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag,pipeline_state\ULTIMATE_BOOK_KILL_fn.flag -Force -ErrorAction SilentlyContinue
```

Tracked flags deleted in the activation change:

- `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
- `pipeline_state/RESEARCH_RUNTIME_HALT.flag`
- `knowledge_base/meta/AUTOSTART_DISABLED.flag`

Runtime halt snapshot after flag removal:

- `status: runtime_halt_clear`
- `active: false`
- all configured halt paths missing

Final reload command:

```powershell
Enable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor' | Out-Null
Start-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
```

Final stable start was at `2026-06-18T15:05:07Z`.

## Live Process Evidence

Snapshot at `2026-06-18T15:10:33Z`:

- Scheduled task: `GTOS_W7_BookSupervisor`, `Running`
- Last scheduler fire: `2026-06-18T15:08:08Z`
- Next scheduler fire: `2026-06-18T15:13:13Z`
- Last task result after the scheduled fire while resident: `2147946720` (task remained running)

Process tree:

- Supervisor: PID `5140`, command `powershell ... -File C:\Users\MSI\Documents\ai-trading-agent\scripts\run_book_supervisor.ps1`
- FTMO venv shim: PID `1064`, child book PID `4872`
- redacted_account venv shim: PID `7116`, child book PID `6776`
- Monitor venv shim: PID `4824`, child monitor PID `4240`

The apparent two `python.exe` rows per book are the Windows venv shim parent plus the real Python child.
The real child PID is written to `pipeline_state/ultimate_book/<namespace>/run_book.pid` and heartbeat.

Heartbeats:

- `operator_profile`: `{"ts":"2026-06-18T15:10:15.645927+00:00","pid":4872,"healthy":true}`
- `redacted_account_live_bee34003`: `{"ts":"2026-06-18T15:10:17.950803+00:00","pid":6776,"healthy":true}`

## Runtime Log Packet Evidence

Launcher stderr confirmed both books started live:

- FTMO: `triple_gate_ON=True halted=False killed=False`
- redacted_account: `triple_gate_ON=True halted=False killed=False`

`shadow_logs/ultimate_book_launcher.jsonl` emitted live cycle rows with:

- `place: true`
- `killed: false`
- `halted: false`
- `runtime_effect_now: true`
- `bridge.include_candidate_book: true`
- `bridge.include_market_expansion_book: true`
- `bridge.market_expansion_policy: positive_weighted12_after_swap`
- `bridge.kelly_running_count: true`
- `bridge.stress_derisk: true`
- `bridge.derisk_mode: smooth`
- `bridge.drop_w7_symbols: true`
- `bridge.metals_confluence_gate: true`
- `bridge.broad_selector_apply_to_execution: false`

Rows also showed existing `idxrev` positions were adopted and managed:

- FTMO adopted tickets `160080305` and `159993636`.
- redacted_account adopted ticket `246763216`.
- No new order was placed in the sampled rows: `placed: []`.
- The sampled candidate was skipped because the sleeve already held the symbol: `sleeve_already_holds_symbol`.

Monitor snapshot:

- FTMO: 2 open `W7:idxrev` positions, gross risk about `0.34%`.
- redacted_account: 1 open `W7:idxrev` position, gross risk about `0.18%`.

## Runtime Hardening Applied On VPS

During reload verification, Windows process listings showed the venv launcher parent and child with
the same command line. To protect against true duplicate starts and diagnostic false positives:

- `run_book.py` now uses `ctypes.WinDLL(..., use_last_error=True)` for the Windows mutex and also takes
  a per-namespace `msvcrt` file lock at `pipeline_state/ultimate_book/<namespace>/run_book.lock`.
- `scripts/run_book_supervisor.ps1` now matches only real `-File ...run_book_supervisor.ps1` invocations,
  not diagnostic `-Command` shells containing wildcard text.

## Post-Activation Research Push Absorption

After the initial VPS activation, `git fetch origin --prune` found a newer same-branch research-session
commit:

- `7f9d0e545f8f81307759a31203ea06a092ca4a94` - `vps: fix market expansion policy generation parity`

This was material. Before the merge, runtime packets logged market-expansion config parity but launcher
cycle tags did not include the `mx_*` D1 sleeves. The remote fix wires the named policy into:

- `UltimateBookLiveEngine` generation,
- `UltimateBookOwner` manageable-symbol/pair management,
- `BookLauncher` D1 scheduling,
- `ultimate_book_sqrt_n_pooling` bridge plumbing.

The VPS branch merged that commit with the local activation/telemetry/startup hardening in:

- `cbbd687ab` - merge of `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`

Post-merge verification:

```powershell
python -m py_compile src/components/ultimate_book/bridge.py src/components/ultimate_book/book_engine.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/launcher.py run_book.py
pytest tests/ultimate_book/test_market_expansion_runtime_generator.py tests/ultimate_book/test_launcher.py -q
$files = @(rg --files tests/ultimate_book | rg 'market_expansion'); pytest @files -q
python research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/verify_market_expansion_conditioned_policy_runtime_alias.py
python scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
pytest tests/ultimate_book/test_candidate_promotion_plumbing.py tests/ultimate_book/test_order_route.py tests/ultimate_book/test_book_engine.py tests/ultimate_book/test_candidate_book_consistency.py tests/ultimate_book/test_active_registry_and_softband_audit.py tests/test_dynamic_target_stop_geometry_v4.py tests/test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests/test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
```

Results:

- Focused launcher + market-expansion tests: `24 passed`.
- All market-expansion tests: `53 passed`.
- Runtime alias verifier: `ok=true`, `issue_count=0`.
- Route artifact audit: `ok=true`.
- Broader ultimate-book/order/dynamic-target regression block: `41 passed`.

Post-merge reload command:

```powershell
Enable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor' | Out-Null
Start-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
```

Post-merge live proof from `shadow_logs/ultimate_book_launcher.jsonl`:

- FTMO `2026-06-18T15:20:24Z`: `mx_tag_count=12`, `bridge_market_expansion_sleeve_count=12`,
  `market_expansion_policy=positive_weighted12_after_swap`, `place=true`, `halted=false`, `killed=false`.
- redacted_account `2026-06-18T15:20:28Z`: `mx_tag_count=12`, `bridge_market_expansion_sleeve_count=12`,
  `market_expansion_policy=positive_weighted12_after_swap`, `place=true`, `halted=false`, `killed=false`.

Post-merge live child PIDs:

- FTMO book child: `8436`
- redacted_account book child: `4744`
- Supervisor: `7408`

## Monitoring Paths

- `shadow_logs/ultimate_book_launcher.jsonl`
- `shadow_logs/run_book_console.log`
- `shadow_logs/run_book_console.log.err`
- `shadow_logs/run_book_fn_console.log`
- `shadow_logs/run_book_fn_console.log.err`
- `shadow_logs/monitor_daemon.log`
- `shadow_logs/monitor_daemon.err`
- `shadow_logs/book_supervisor.log`
- `pipeline_state/supervisor_heartbeat.json`
- `pipeline_state/ultimate_book/operator_profile/heartbeat.json`
- `pipeline_state/ultimate_book/operator_profile/run_book.pid`
- `pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json`
- `pipeline_state/ultimate_book/redacted_account_live_bee34003/run_book.pid`
- `pipeline_state/*/notification_queue.jsonl`

## Rollback

Immediate operational brake:

```powershell
Set-Content -Path pipeline_state\RESEARCH_RUNTIME_HALT.flag -Value "GTOS ROLLBACK HALT`ncreated_utc=$(Get-Date -Format o)`nreason=operator rollback" -Encoding utf8
Set-Content -Path pipeline_state\GTOS_HARD_PRODUCTION_HALT.flag -Value "GTOS ROLLBACK HALT`ncreated_utc=$(Get-Date -Format o)`nreason=operator rollback" -Encoding utf8
Set-Content -Path knowledge_base\meta\AUTOSTART_DISABLED.flag -Value "GTOS ROLLBACK HALT`ncreated_utc=$(Get-Date -Format o)`nreason=operator rollback" -Encoding utf8
Set-Content -Path pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag -Value "operator rollback" -Encoding utf8
Set-Content -Path pipeline_state\ULTIMATE_BOOK_KILL_fn.flag -Value "operator rollback" -Encoding utf8
Disable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor' | Out-Null
Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -and ($_.CommandLine -like '*run_book.py*' -or $_.CommandLine -like '*monitor_books.py*')) -or ($_.Name -eq 'powershell.exe' -and $_.CommandLine -match '(?i)(^|\s)-File\s+"?[^\"]*run_book_supervisor\.ps1"?($|\s)') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```

Primary performance rollback in `config/agent_config.yaml`:

```yaml
ultimate_book_market_expansion_policy: "robust6_every_split_positive"
ultimate_book_market_expansion_sleeves: []
```

Full market-expansion rollback:

```yaml
ultimate_book_include_market_expansion_book: false
ultimate_book_market_expansion_policy: "explicit_allowlist"
ultimate_book_market_expansion_sleeves: []
```

Full candidate-book rollback:

```yaml
ultimate_book_include_candidate_book: false
ultimate_book_candidate_book_sleeves: []
```

Rollback proof boundary:

- Before activation, the runtime halt snapshot reported `status: runtime_halt_active` with all three hard
  halt/autostart flags present.
- After activation, the runtime halt snapshot reported `status: runtime_halt_clear` with all three
  configured halt paths missing.
- Recreating those same files re-engages the same source-bound halt guard.

## Non-Blocking Missing Mac Raw Artifacts

No missing Mac artifact blocks this VPS runtime package. The deployable compact evidence is present.
If raw audit recomputation is later required, the missing Mac-side raw inputs are:

- `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/CANDIDATE_DAILY_SERIES.json`
- `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/unified_book_mc.py`
- `research/operations/final_moonshot_principal_full_system_audit_2026_06_17/`
