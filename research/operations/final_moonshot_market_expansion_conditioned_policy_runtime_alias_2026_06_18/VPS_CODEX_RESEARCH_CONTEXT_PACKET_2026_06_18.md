# VPS Codex Research Context Packet

Date: 2026-06-18
Host repo: `C:\Users\MSI\Documents\ai-trading-agent`
Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
Absorbed HEAD before this repair commit: `da35ecc2bae9a278bc4f83724d46aeed83e73967`
Required commit: `96f53b63de04c85643395d6ec62b776802065ddc`
Required commit ancestor check: `true`

This packet is for the research session. It records the VPS-only facts that the Mac route could not know:
direct Windows MT5 access to both FTMO and redacted_account, broker symbol-name differences, profile support gaps,
live reload behavior, and the repairs applied here.

## Preflight Absorbed

Mandatory state was regenerated with `python scripts/generate_live_state.py`. The following files were read
before making claims or changes:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- `.context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_DEPLOYMENT_LEDGER_2026_06_18.md`

## Active Package

Active config parity from `config/agent_config.yaml`:

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_candidate_book_profile=runtime_executable_native_exit_v2`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- `ultimate_book_kelly_lite=true`
- `ultimate_book_kelly_conservative=true`
- `ultimate_book_kelly_running_count=true`
- `ultimate_book_stress_derisk=true`
- `ultimate_book_derisk_mode=smooth`
- `ultimate_book_metals_confluence_gate=true`
- `ultimate_book_drop_w7_symbols=true`

Config/profile hashes after repair:

- `config/agent_config.yaml`: `98AD6D2300DA7AD846210959934AED063EABB481B7CAB7B45771A3D1F7CC1403`
- `config/profiles/operator_profile.yaml`: `AE9312E6C5C8E6B05F8E5EB5F9490166C44A1A3279B4EFF5DF10C3DA2921E2B8`
- `config/profiles/redacted_account.yaml`: `B856F0EE7F13C59DD407949C6937275DA57C3E797AB2BAE256755560BBD21305`

## Expected Edge

Evidence class: `replay_mc_activation_package_not_broker_real_future_pnl`.

| Package | Monthly | Sharpe | MC Pass | Max-DD Fail | Worst Day | MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| A8 active reference | `2.646%` | `0.147757` | `0.99055` | `0.00945` | `-2.66%` | `8.695125R` |
| Candidate-book reference | `4.969%` | `0.277408` | `0.9999` | `0.0001` | `-2.16%` | `8.766924R` |
| Active intended positive12 expansion | `5.09%` | `0.28419` | `0.9999` | `0.0001` | `-2.083%` | `8.842614R` |
| Defensive robust6 expansion | `5.052%` | `0.282076` | `0.9998` | `0.0002` | `-2.075%` | `7.956872R` |

Interpretation: the big lift is A8 active reference to candidate book (`2.646%` to `4.969%` monthly).
The conditioned market-expansion policy adds a smaller incremental lift over the candidate book:
`+0.121%` monthly and `+0.006782` Sharpe. The robust6 fallback gives a slightly lower monthly result than
positive12 but materially lower maxDD than candidate (`-0.810052R` versus candidate).

## Architecture

Runtime topology on the VPS:

1. Windows scheduled task `GTOS_W7_BookSupervisor` starts `scripts/run_book_supervisor.ps1`.
2. The supervisor launches two independent book workers:
   - FTMO: `run_book.py --terminal-path C:\MT5\FTMO\terminal64.exe --namespace operator_profile --profile operator_profile`
   - redacted_account: `run_book.py --terminal-path C:\MT5\redacted_account\terminal64.exe --namespace redacted_account_live_bee34003 --profile redacted_account`
3. Each `run_book.py` process loads `config/agent_config.yaml`, deep-merges the broker profile with
   `apply_profile_overrides`, opens direct MT5 via the Windows terminal, then creates `UltimateBookOwner`.
4. `UltimateBookOwner` owns one cross-symbol book per account. It manages existing positions every tick,
   runs `UltimateBookLiveEngine` on bar advance, passes bridge/admission decisions to `UltimateBookOrderRouter`,
   and persists idempotency and ticket records under `pipeline_state/ultimate_book/<namespace>/`.
5. `UltimateBookLiveEngine` builds active specs from core W7, candidate-book sleeves, and the resolved
   market-expansion policy. It now uses the broker profile resolver and skips unsupported symbols before
   bar fetch or order generation.
6. `symbol_map.build_broker_symbol_resolver` resolves canonical symbols into broker-native symbols from
   `instruments[*].market.mt5_symbol` and exposes `supports(canonical)`.
7. `admission.py` and `bridge.py` enforce the active package: triple gate, candidate book, market expansion,
   Kelly-lite/running-count, smooth stress derisk, A8 metals confluence, W7 drop filter, and selector-v4
   execution-off boundary.
8. Execution runs through `UltimateBookOrderRouter` and the existing `ExecutionEngine`, with ticket-bound
   native exits, time stops, spread/cost gates, broker order lifecycle capture, and notification queues.
9. Monitoring surfaces:
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
   - `pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json`

Important architecture correction: this is not the stale redacted_account-primary/FTMO-follower projector model.
The VPS now runs two independent account-local book workers, each using its own direct MT5 terminal and
profile namespace.

## Direct Broker Parity

Direct read-only probes were run through both portable MT5 terminals.

FTMO:

- Terminal: `C:\MT5\FTMO\terminal64.exe`
- Data path: `C:\MT5\FTMO`
- Company/server: `FTMO Global Markets Ltd` / `FTMO-Server3`
- Login hash: `0000000000000000000000000000000000000000000000000000000000000000`
- Account currency: `USD`
- Margin mode: `2`
- Trade mode: `2`
- Active canonical support: `46/46`
- Direct MT5 unavailable active symbols: none

redacted_account:

- Terminal: `C:\MT5\redacted_account\terminal64.exe`
- Data path: `C:\MT5\redacted_account`
- Company/server: `redacted_account Ltd` / `redacted_account-Server 2`
- Login hash: `0000000000000000000000000000000000000000000000000000000000000000`
- Account currency: `USD`
- Margin mode: `2`
- Trade mode: `2`
- Active canonical support: `36/46`
- Direct MT5 unavailable active symbols: `AVAUSD`, `CORN_c`, `COTTON_c`, `DASHUSD`, `XAGAUD`,
  `XAGEUR`, `XAUAUD`, `XAUEUR`, `XPDUSD`, `XTZUSD`

The machine-readable map for all 46 active canonical symbols is in
`VPS_BROKER_PROFILE_PARITY_AUDIT_2026_06_18.json`.

Key broker-name differences that must be preserved:

- FTMO `GER40` / `GER40_cash` -> `GER40.cash`; redacted_account -> `GER30`
- FTMO `JP225` / `JP225_cash` -> `JP225.cash`; redacted_account -> `JP225`
- FTMO `NAS100` / `US100_cash` -> `US100.cash`; redacted_account -> `NDX100`
- FTMO `SPX500` / `US500_cash` -> `US500.cash`; redacted_account -> `SPX500`
- FTMO `US30_cash` -> `US30.cash`; redacted_account -> `US30`
- FTMO `USOIL_cash` -> `USOIL.cash`; redacted_account -> `USOUSD`
- FTMO `UKOIL_cash` -> `UKOIL.cash`; redacted_account -> `UKOUSD`
- FTMO `EU50_cash` -> `EU50.cash`; redacted_account -> `EUSTX50`
- FTMO `FRA40_cash` -> `FRA40.cash`; redacted_account -> `FRA40`

## Repairs Applied

Issues found and fixed:

1. FTMO profile lacked direct active specs for `AVAUSD`, `CADJPY`, and `NZDJPY`.
2. redacted_account profile lacked direct active specs for `CADJPY`, `NZDJPY`, `LTCUSD`, `XPTUSD`, and `XRPUSD`.
3. redacted_account top-level `mt5` block still pointed at the old `C:\Program Files\MetaTrader 5` install even
   though the VPS runtime uses `C:\MT5\redacted_account`.
4. Symbol-family resolution did not cover several active canonical aliases such as `GER40_cash`,
   `JP225_cash`, `US100_cash`, `US500_cash`, `CADJPY`, and `NZDJPY`.
5. The broker resolver fell back to identity for profile-missing symbols. On redacted_account that could turn
   broker-unavailable active symbols into bogus fetch/order probes.
6. The owner position manager could adopt one broker ticket into two canonical aliases/sleeves when aliases
   shared a broker symbol. Live evidence showed FTMO ticket `159993636` adopted as both `JP225/idxrev` and
   `JP225_cash/mx_jp225_cash_d1_volume_surge_reversal`.

Code/profile/test changes:

- `config/profiles/operator_profile.yaml`: added direct broker specs for `AVAUSD`, `CADJPY`, `NZDJPY`.
- `config/profiles/redacted_account.yaml`: added direct broker specs for `CADJPY`, `NZDJPY`, `LTCUSD`, `XPTUSD`,
  `XRPUSD`; fixed `mt5.terminal_path`, `mt5.terminal_data_path`, and `mt5.portable`.
- `src/utils/config.py`: added/expanded symbol-family key candidates.
- `src/components/gtos_vnext_runtime.py`: added the missing canonical alias mappings.
- `src/components/ultimate_book/symbol_map.py`: resolver now resolves family/profile aliases and exposes
  `supports(canonical)` while preserving identity behavior for minimal test configs.
- `src/components/ultimate_book/book_engine.py`: unsupported profile symbols are skipped before bar fetch.
- `src/components/ultimate_book/book_owner.py`: one ticket cannot be adopted globally into a second
  canonical alias/sleeve during the same management pass; leftover adoption now respects W7 comments and
  durable ledger route.
- `tests/ultimate_book/test_symbol_map.py`: added FTMO/redacted_account broker resolver and support tests.
- `tests/ultimate_book/test_active_broker_profile_parity.py`: added active-book parity and redacted_account
  portable-path tests.
- `tests/ultimate_book/test_book_owner.py`: added the JP225/JP225_cash alias-collision regression.

## Verification

Live workers were stopped for test isolation before pytest.

Commands run successfully:

```powershell
python -m py_compile src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py src\components\ultimate_book\book_engine.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\symbol_map.py src\utils\config.py src\components\gtos_vnext_runtime.py
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
pytest tests\ultimate_book\test_active_broker_profile_parity.py tests\ultimate_book\test_symbol_map.py tests\test_config_symbol_aliases.py tests\ultimate_book\test_market_expansion_runtime_generator.py tests\ultimate_book\test_launcher.py -q
$files = @(rg --files tests/ultimate_book | rg 'market_expansion'); pytest @files -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_book_owner.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
```

Results:

- Runtime alias verifier: `ok=true`, `issue_count=0`.
- Combined broker parity/symbol/launcher/generator run: `49 passed`.
- Full market-expansion test slice: `53 passed`.
- Broad activation-adjacent regression block including owner alias-collision test: `69 passed`.
- Route artifact audit: `ok=true`.

## Reload Evidence

Final reload commands after the owner alias fix:

```powershell
Enable-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor' | Out-Null
Start-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor'
```

Final reload state:

- Scheduled task: `GTOS_W7_BookSupervisor`, `Running`
- LastRunTime: `2026-06-18T15:55:55` local
- LastTaskResult: `267009` while resident/running
- Supervisor PID: `5512`
- FTMO shim/child PIDs: `1656` / `6116`
- redacted_account shim/child PIDs: `3308` / `6740`
- Monitor shim/child PIDs: `6496` / `8412`

Heartbeat samples:

- Supervisor: `{"ts":"2026-06-18T15:55:15.7790239Z","pid":5512}`
- FTMO: `{"ts":"2026-06-18T15:55:18.814176+00:00","pid":6116,"namespace":"operator_profile","healthy":true}`
- redacted_account: `{"ts":"2026-06-18T15:55:21.446012+00:00","pid":6740,"namespace":"redacted_account_live_bee34003","healthy":true}`

Post-fix runtime packet parity from `shadow_logs/ultimate_book_launcher.jsonl`:

- `place=true`
- `halted=false`
- `killed=false`
- `runtime_effect_now=true`
- `bridge.include_candidate_book=true`
- `bridge.include_market_expansion_book=true`
- `bridge.market_expansion_policy=positive_weighted12_after_swap`
- `bridge.market_expansion_sleeves` count `12`
- `bridge.kelly_running_count=true`
- `bridge.stress_derisk=true`
- `bridge.derisk_mode=smooth`
- `bridge.metals_confluence_gate=true`
- `bridge.drop_w7_symbols=true`
- `bridge.broad_selector_apply_to_execution=false`

Alias-adoption proof:

- Before fix, FTMO manage row at `2026-06-18T15:49:55Z` adopted ticket `159993636` as both
  `JP225/idxrev` and `JP225_cash/mx_jp225_cash_d1_volume_surge_reversal`.
- After fix, FTMO manage row at `2026-06-18T15:55:18Z` adopted ticket `159993636` only as
  `JP225/idxrev`; no `JP225_cash` adoption was present.

Live orders observed during the first restart before the owner alias fix:

- FTMO ticket `160183955`: `XAUUSD`, `W7:metal_session`, long `0.39`, entry `4227.70`, SL `4216.70`, TP `0.0`.
- redacted_account ticket `246849001`: `XAUUSD`, `W7:metal_session`, long `0.40`, entry `4227.84`, SL `4216.80`, TP `0.0`.

The second reload after the alias fix placed no additional orders in the sampled first cycle; it adopted and
managed the existing positions.

## Current Strengths

- The active package is now truly broker-profile aware on the VPS. FTMO can run the full 46-symbol active
  surface; redacted_account is reduced to its directly supported 36 symbols instead of pretending unsupported
  names are tradeable.
- The strongest current package is wired through config, bridge, generator, launcher, and runtime packets:
  candidate book plus conditioned market expansion, with selector-v4 execution explicitly off.
- The runtime is direct MT5 on Windows for both brokers, not Mac bridge inference.
- Candidate book and market-expansion policy are resolved by named policies, not manual stale lists.
- Safety layers remain active: triple gate, halt/kill flags, smooth stress derisk, Kelly-lite/running count,
  A8 metals confluence gate, W7 dropped-symbol filter, cost/spread gates, ticket-bound exits, and
  namespaced heartbeats.
- The alias-collision management bug found from live telemetry is repaired and covered by test.

## Weaknesses And Limitations

- The `5.09%` monthly expectancy is replay/MC evidence, not broker-real future PnL. It should be treated as
  an activation expectation, not a guarantee.
- The market-expansion incremental lift is small compared with the candidate-book jump. Positive12 adds only
  `+0.121%` monthly over candidate reference; most of the present edge is still candidate-book driven.
- redacted_account cannot run 10 of the 46 active canonical symbols. This means FTMO and redacted_account are not
  identical books in practice, even though the same policy is loaded.
- Broker costs remain partially empirical. Direct profiles capture spread/swap/tick/lot geometry snapshots,
  but commission/slippage/fill/session behavior still needs prospective broker-real ledgers per symbol.
- Static profile specs can drift. Spread, swap, session, and tradeability need a recurring broker-spec monitor
  and alert surface.
- Bridge packets report the abstract 12-sleeve positive policy on both brokers; the engine now enforces
  profile support before generation. Research must not read the packet alone as proof redacted_account will trade
  all 12 market-expansion symbols.
- Some live state is already near derisk walls. The current system can still open reduced-size entries while
  `derisking_into_maxdd_wall`; this is intended by the current governor but should be stress-reviewed against
  prop-account recovery objectives.
- `.context/00_core/research_current_state.md` was stale versus newer VPS commits before this packet. This
  packet is the current VPS-side context bridge for the research session.
- One LFS pointer-only row remains reported by `LIVE_STATE` (`shadow_logs/slippage.jsonl` class). Do not make
  row-level slippage claims from that file without hydration or a local evidence cache.

## Highest-Value Opportunities

- Build a broker-spec drift monitor that snapshots `symbol_info`, sessions, spreads, swaps, filling modes,
  stops/freeze levels, and availability for both FTMO and redacted_account daily and fails closed on material drift.
- Build a broker-real forward join: every signal -> order attempt -> fill -> modification -> close -> cash PnL
  -> exact R -> slippage/commission/swap attribution, namespaced per broker.
- Re-score candidate and market-expansion sleeves with broker-specific availability and costs instead of one
  shared abstract active surface.
- Add a portfolio optimizer over the realized sleeves, including broker-specific symbol breadth, correlated
  exposure, open-risk headroom, prop drawdown state, and session liquidity.
- Add market-state conditioning beyond the current sleeve rules: volatility regime, session state, spread
  regime, event-risk proxy, funding/swap drag, and existing-position overlap.
- Make the governor more goal-aware: when close to daily/static drawdown walls, decide between no-entry,
  recovery-only entries, or reduced-risk continuation from a formal expected-value objective.
- Promote "missed opportunity" and "skipped unsupported" ledgers so reduced redacted_account breadth and cost-screen
  declines become measurable research inputs rather than only runtime absence.

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

Primary performance rollback:

```yaml
ultimate_book_market_expansion_policy: "robust6_every_split_positive"
ultimate_book_market_expansion_sleeves: []
```

Full market-expansion-off rollback:

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
