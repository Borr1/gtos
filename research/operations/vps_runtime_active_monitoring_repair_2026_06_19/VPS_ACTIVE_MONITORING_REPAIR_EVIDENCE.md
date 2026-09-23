# VPS Active Monitoring Repair Evidence - 2026-06-19

Generated from the VPS working tree on `vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

## Objective

Keep active monitoring running, fix confirmed defects instead of only reporting them, and verify the ultimate book runtime remains live on both FTMO and redacted_account.

## Confirmed Issue

The live manager correctly managed active tickets and had already closed the crypto tickets, but stale local trade records for XAU positions could remain lifecycle-open after a restart if the broker had already closed them and no live `ExecutionEngine.active_trade` observed the transition.

Impact:

- Runtime-learning and trade-record evidence could report stale open lifecycle state for closed book tickets.
- The closed XAU records were not packet-joined before packet logging started, even though their placement rows existed in `placed_decisions.jsonl`.
- No broker/account/order/deal/position mutation was required; this was local evidence and lifecycle-state repair.

## Code Repair

Changed `src/components/ultimate_book/book_owner.py`:

- Reuses one confirmed open-position snapshot across management.
- Adds `_open_book_positions_snapshot()` with broker-link gating when exposed by the MT5 wrapper.
- Adds `_active_engine_tickets()`.
- Adds `_reconcile_absent_trade_records()` so stale local records are marked `closed` with `broker_closed_absent_on_reconcile` only when another broker-open book position confirms the snapshot is real.
- Keeps an empty open-position snapshot conservative: it does not mass-close local records.

Tests added in `tests/ultimate_book/test_book_owner.py`:

- `test_absent_trade_record_reconcile_marks_stale_record_closed`
- `test_absent_trade_record_reconcile_skips_empty_snapshot`

## Subagent Findings

Process/config subagent:

- Supervisor, both book workers, monitor, and both MT5 terminals were alive.
- Heartbeats were fresh.
- `GTOS_W7_BookSupervisor` was running.
- Halt/kill/autostart flags were absent.
- Non-zero scheduled-task result `0x800710E0` was interpreted as recurring trigger refusal while an `IgnoreNew` task instance is already running, not a live process failure.

Config/profile subagent:

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- Kelly-lite, conservative Kelly, running count, smooth stress derisk, A8 metals gate, and W7 dropped-symbol filter were active.
- FTMO profile verifier: `ok=true`, `issue_count=0`, `active_symbol_count=46`.
- redacted_account profile verifier: `ok=true`, `issue_count=0`, `active_symbol_count=46`, supported `36/46`, allowed missing `10`: `AVAUSD`, `CORN_c`, `COTTON_c`, `DASHUSD`, `XAGAUD`, `XAGEUR`, `XAUAUD`, `XAUEUR`, `XPDUSD`, `XTZUSD`.

Packet/chronology subagent:

- Runtime-learning packets parsed and validated with zero hash/redaction issues.
- Active managed tickets before repair:
  - FTMO `159993636` JP225, `ticket_policy_joinable`
  - FTMO `160080305` UK100, `ticket_policy_joinable`
  - redacted_account `246763216` UK100, `ticket_policy_joinable`
  - redacted_account `246920173` JP225, `ticket_candidate_decision_policy_joinable`
- Crypto tickets were already closed and joinable.
- Legacy active index records remain `ticket_policy_joinable` because their original candidate/decision placement rows predate the current durable placement ledger. This was not fabricated into candidate truth.

## Live Reload Evidence

Reload scope: book workers only. MT5 terminals and monitor stayed alive. No broker order/position mutation command was issued.

Command shape executed:

```powershell
$before = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*run_book.py*' -or $_.CommandLine -like '*monitor_books.py*--loop*' }
$configHashBefore = (Get-FileHash config\agent_config.yaml -Algorithm SHA256).Hash
$runBookPids = @($before | Where-Object { $_.CommandLine -like '*run_book.py*' } | ForEach-Object { [int]$_.ProcessId })
foreach ($pidToStop in $runBookPids) { Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 55
$after = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*run_book.py*' -or $_.CommandLine -like '*monitor_books.py*--loop*' }
$configHashAfter = (Get-FileHash config\agent_config.yaml -Algorithm SHA256).Hash
```

Before reload:

- Config hash: `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`
- FTMO launcher/worker: `5732` / `7364`
- redacted_account launcher/worker: `9068` / `5080`
- Monitor launcher/worker unchanged: `9520` / `2404`

After reload:

- Config hash: `C9E3CE8C6E84F86CC8F70BA3CEF99A4EC99887F68515D3F2AB09B54F7F78533C`
- Supervisor: `1456`
- FTMO launcher/worker: `4744` / `6992`
- redacted_account launcher/worker: `848` / `5872`
- Monitor launcher/worker: `9520` / `2404`
- MT5 FTMO terminal: `4524`
- MT5 redacted_account terminal: `6060`

## Post-Reload Packet Evidence

Runtime-learning packets after patched worker start:

- Line `2687`: FTMO `XAUUSD` `position_closed`, action `broker_closed_absent_on_reconcile`, join `ticket_candidate_decision_policy_joinable`, lifecycle `closed`, management checked `2026-06-19T02:09:50.921063+00:00`.
- Line `2694`: redacted_account `XAUUSD` `position_closed`, action `broker_closed_absent_on_reconcile`, join `ticket_candidate_decision_policy_joinable`, lifecycle `closed`, management checked `2026-06-19T02:09:53.710472+00:00`.
- Lines `2716` to `2719`: current index positions continued `position_managed` normally after repair.

Closed records after repair:

- FTMO XAU `160183955`: candidate `W7_BOOK::metal_reversion::XAUUSD::2026-06-18::LONG::metal_session_reversion`, decision bar `2026-06-18T15:30:00+00:00`, placed `2026-06-18T15:49:55.312805+00:00`, close action `broker_closed_absent_on_reconcile`, closed `2026-06-19T02:09:50.921063+00:00`.
- redacted_account XAU `246849001`: same candidate, decision bar `2026-06-18T15:30:00+00:00`, placed `2026-06-18T15:49:58.268328+00:00`, close action `broker_closed_absent_on_reconcile`, closed `2026-06-19T02:09:53.710472+00:00`.

Current active broker snapshot after reload:

- FTMO equity `96121.78`, balance `96270.01`, orders `0`.
- FTMO open positions:
  - `159993636` `JP225.cash` SELL `2.36`, SL `72269.15`, TP `70302.64`, comment `W7:idxrev`.
  - `160080305` `UK100.cash` BUY `1.82`, SL `10352.66`, TP `10471.47`, comment `W7:idxrev`.
- redacted_account equity `98574.98`, balance `98651.72`, orders `0`.
- redacted_account open positions:
  - `246763216` `UK100` BUY `0.19`, SL `10357.02`, TP `10473.39`, comment `W7:idxrev`.
  - `246920173` `JP225` SELL `2.21`, SL `72700.0`, TP `70791.0`, comment `W7:idxrev`.

No XAU or crypto position was open in the post-reload broker snapshot.

## Verification Commands

Passed:

```powershell
python -m py_compile src\components\ultimate_book\book_owner.py src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_placement_ledger.py -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py -q
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
pytest $(rg --files tests\ultimate_book | rg 'market_expansion') -q
pytest tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python research\operations\vps_runtime_ultimate_monitoring_repair_2026_06_18\verify_vps_runtime_ultimate_monitoring_repair.py
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
python scripts\generate_live_state.py
```

Key pass counts:

- `tests/ultimate_book/test_book_owner.py`: `33 passed`
- `tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_placement_ledger.py`: `12 passed`
- Combined focused book suite: `37 passed`
- `tests/ultimate_book/test_market_expansion_runtime_generator.py`: `10 passed`
- All `tests/ultimate_book/*market_expansion*`: `53 passed`
- Dynamic target/limit-flow lifecycle subset: `7 passed`
- VPS monitoring-repair verifier: `ok=true`, `issue_count=0`
- Runtime-learning parity verifier: `ok=true`, `issue_count=0`
- Market-expansion conditioned-policy verifier: `ok=true`, `issue_count=0`
- Route artifact audit: `ok=true`

## Rollback

Code rollback:

```powershell
git revert HEAD
```

Runtime rollback after code revert:

```powershell
$runBookPids = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*run_book.py*' } | ForEach-Object { [int]$_.ProcessId })
foreach ($pidToStop in $runBookPids) { Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue }
```

The supervisor will restart both book workers from the reverted working tree. Broker flattening is not part of this rollback. Market-expansion policy rollback remains the previously documented config rollback to `robust6_every_split_positive` or market-expansion off; this repair did not change those config keys.

## Residual Limitations

- Legacy active FTMO JP225/UK100 and redacted_account UK100 records remain `ticket_policy_joinable` because the original candidate/decision rows are not present in the current durable placement ledger. The system should not fabricate candidate truth for these tickets.
- redacted_account remains intentionally narrower than FTMO for unavailable instruments; unsupported redacted_account symbols fail closed.
- Packet append-order timestamp regressions are sub-second cross-namespace append ordering, not packet validation failures.
- Scheduled task `LastTaskResult=0x800710E0` is noisy while `IgnoreNew` refuses overlapping triggers; process and heartbeat state remain the runtime health authority.

## Follow-Up Slippage Runtime Merge Repair

Active monitoring found a read-side evidence defect after the writer-side LFS redirect repair: `shadow_logs/slippage.jsonl`
is still the configured canonical path, but live appends are redirected to `shadow_logs/slippage_runtime.jsonl` when
the canonical file is an LFS pointer. Coverage tooling that read only `slippage.jsonl` could see the two early XAU rows
appended after the pointer header and miss the five redirected runtime rows.

Repairs:

- `src/components/slippage_shadow_logger.py` now exposes slippage read helpers that merge the canonical path and the
  runtime redirect path while skipping non-JSON LFS pointer header rows.
- `scripts/build_cost_slippage_exit_coverage.py`, `scripts/build_broker_r_reconciliation_coverage.py`,
  `scripts/backfill_broker_actual_r_audit.py`, and `scripts/audit_live_shadow_followup_coverage.py` use the merged
  slippage stream for cost/R evidence.
- No live reload was required because this is read-side evidence tooling. No broker/account/order/deal/position state
  was mutated.

Verification:

```powershell
python -m py_compile src\components\slippage_shadow_logger.py scripts\build_cost_slippage_exit_coverage.py scripts\build_broker_r_reconciliation_coverage.py scripts\backfill_broker_actual_r_audit.py scripts\audit_live_shadow_followup_coverage.py
pytest tests\test_slippage_shadow_logger.py tests\test_cost_slippage_exit_coverage.py tests\test_broker_r_reconciliation_coverage.py tests\test_live_shadow_followup_coverage_audit.py -q
python scripts\build_cost_slippage_exit_coverage.py --output-json research\operations\vps_runtime_active_monitoring_repair_2026_06_19\SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.json --output-md research\operations\vps_runtime_active_monitoring_repair_2026_06_19\SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.md
python scripts\build_broker_r_reconciliation_coverage.py --trade-records-root pipeline_state\ultimate_book --output-json research\operations\vps_runtime_active_monitoring_repair_2026_06_19\BROKER_R_RUNTIME_MERGE_COVERAGE.json --output-md research\operations\vps_runtime_active_monitoring_repair_2026_06_19\BROKER_R_RUNTIME_MERGE_COVERAGE.md
python scripts\audit_live_shadow_followup_coverage.py --output-json research\operations\vps_runtime_active_monitoring_repair_2026_06_19\LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.json --output-md research\operations\vps_runtime_active_monitoring_repair_2026_06_19\LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.md
```

Results:

- Focused tests: `54 passed`.
- Cost/slippage coverage now reports `slippage_rows=7`, `entry_spread_rows=7`, and `entry_slippage_rows=7`.
- Broker-R coverage now reports `slippage_rows=7`.
- Follow-up coverage item `LIVE-FOLLOW-012` now reports `shadow_logs/slippage.jsonl` as `line_count=7` with
  `error=null`, representing the merged pointer-path plus runtime-redirect stream.

## Broker Profile Market Detail Audit

Active monitoring added a direct MT5 symbol-detail parity audit for every current ultimate-book canonical
symbol on both broker profiles.

New verifier:

```powershell
python scripts\audit_broker_profile_market_details.py --output-json research\operations\vps_runtime_active_monitoring_repair_2026_06_19\VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.json --output-md research\operations\vps_runtime_active_monitoring_repair_2026_06_19\VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.md
```

Focused verification:

```powershell
python -m py_compile scripts\audit_broker_profile_market_details.py tests\test_broker_profile_market_detail_audit.py
pytest tests\test_broker_profile_market_detail_audit.py -q
```

Results:

- Focused tests: `4 passed`.
- Audit result: `ok=true`, `issue_count=0`, `warning_count=291`, `active_symbol_count=46`.
- FTMO: `46/46` supported, `46` positive ticks without `symbol_select`, zero missing `symbol_info`, zero hard issues.
- redacted_account: `36/46` supported, `36` positive ticks without `symbol_select`, zero missing `symbol_info`, zero hard issues.
- redacted_account unsupported set remains the known allowed direct-broker gaps:
  `AVAUSD`, `CORN_c`, `COTTON_c`, `DASHUSD`, `XAGAUD`, `XAGEUR`, `XAUAUD`, `XAUEUR`, `XPDUSD`, `XTZUSD`.
- Warning classes are review-only: optional profile fallback metadata available in live `symbol_info`, plus swap/tick-value
  drift. Live pretrade cost packets prefer direct MT5 `symbol_info`, so these warnings are not current runtime breaks.
- No broker/account/order/deal/position mutation, reload, or `symbol_select` call was used.

## Active Supervision Repair Checkpoint - Live Symbol Swap-Cost Source Guard

Active supervision found a live-facing cost-gate weakness: required swap-cost conversion could still be satisfied from
profile/config fallback fields when direct MT5 `symbol_info` was unavailable. The repair makes the pretrade cost packet
carry field-level source provenance and makes required swap-cost conversion fail closed unless side-aware swap fields
and `swap_mode` come from live `symbol_info`, unless an explicit override disables that requirement.

Code changes:

- `src/components/broker_net_cost_engine.py` records symbol-spec field sources and refuses required swap-cost conversion
  when it would depend on profile/config fallback.
- `src/components/permissions.py` passes a read-only live `mt5.symbol_info` snapshot into the cost packet from the
  live gate path.
- `tests/test_broker_net_cost_engine.py` covers default fail-closed behavior and the explicit override path.

Runtime activation:

- Controlled book-worker reload proof: `VPS_ACTIVE_SUPERVISION_REPAIR_RELOAD_PROOF_20260619T040949Z.json`, `ok=true`.
- Process mutation scope was limited to `python.exe run_book.py` workers; supervisor and MT5 terminals remained running.
- Config hash was unchanged before/after reload, broker snapshots were read-only, and broker open-position tickets were
  unchanged across the reload.

Fresh supervision artifacts:

- Latest broker snapshot: `VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_20260619T041215Z.json`, `ok=true`.
- Latest packet chronology audit: `VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_20260619T041215Z.json`,
  `ok=true`, full packet log parsed, slippage merged stream rows `8`, canonical slippage mixed LFS-pointer content
  explicitly recorded.
- Latest profile detail audit: `VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_20260619T041215Z.json`, `ok=true`,
  `issue_count=0`.
- Completion/handoff audit: `VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json`, verification status
  `verified_post_generation_route_verifier_and_tests_green`.

Focused verification:

```powershell
pytest tests\test_broker_net_cost_engine.py -q
pytest tests\test_broker_profile_market_detail_audit.py -q
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_placement_ledger.py -q
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
$files = rg --files tests\ultimate_book | rg 'market_expansion'; pytest $files -q
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
python research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py
python scripts\audit_goal_route_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19 --full-jsonl
```

Results: cost tests `17 passed`; broker profile tests `4 passed`; runtime-learning/placement tests `12 passed`;
book-owner tests `33 passed`; market-expansion generator tests `10 passed`; full market-expansion slice `53 passed`;
conditioned-policy verifier `ok=true`; packet-parity verifier `ok=true`; route verifier `ok=true issue_count=0`;
goal-route artifact audit `ok=true`.
