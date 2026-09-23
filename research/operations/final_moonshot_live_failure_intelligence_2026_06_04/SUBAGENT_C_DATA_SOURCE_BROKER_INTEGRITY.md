# Subagent C - Data, Source, Broker, Account Integrity Audit

Generated: 2026-06-04

Scope: read-only audit of current disk plus `origin/main` for data/source/broker-account integrity after V3 live deployment, dual-broker setup, hard halt, and final moonshot research preparation.

## Anchors

- Local checkout `HEAD`: `e94b0e63b context: harden vps v3 production integration prompt`.
- Remote live authority after fetch: `origin/main = 11a51c049 research: package hard halt live evidence`.
- Local branch state: `main...origin/main [ahead 44, behind 33]`.
- `LIVE_STATE` status: `STALE_UPDATE_RESEARCH_CURRENT_STATE`; `.context/00_core/research_current_state.md` captured `7d749d5bc`, not the newer live/hard-halt commits.
- This audit did not merge, pull into the worktree, change production code, touch broker state, restart processes, push, or run live scripts.

Interpretation: `origin/main` currently carries the latest live/VPS/hard-halt evidence. This local checkout carries many absolute-moonshot research artifacts, but it is not a clean materialized copy of the latest live branch. Any final moonshot route launched from this checkout must first reconcile or explicitly read remote live evidence.

## Current Authority Surfaces

Remote live/halt evidence on `origin/main`:

- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/`
- `data/m1/`
- `data/ticks/`
- `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
- `pipeline_state/RESEARCH_RUNTIME_HALT.flag`
- `knowledge_base/meta/AUTOSTART_DISABLED.flag`

Local research/source authority on disk:

- `research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/`
- `research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01/`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/`
- `research/operations/vnext_mt5_local_cache_preservation_2026_06_01/`
- V3 packages under:
  - `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/`
  - `research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/`
  - `research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01/`

## Finding 1 - Local Checkout Is Not Live-Data Complete

Local disk after preflight:

- `data/m1/` does not exist in this checkout.
- `data/ticks/` exists locally but has zero audited tick files.
- Local `config/profiles/redacted_account.yaml` failed `scripts/verify_broker_profile.py` with `issue_count=270`.
- Local `config/profiles/operator_profile.yaml` passed with `issue_count=0`.

Remote `origin/main`:

- `data/m1/` exists and includes 126 CSV files.
- `data/ticks/` exists and includes 109 tick/state/corrupt-quarantine files.
- Remote `config/profiles/redacted_account.yaml` is account-specific and includes:
  - `server: redacted_account-Server 2`
  - `login_sha256: 0000000000000000000000000000000000000000000000000000000000000000`
  - `terminal_path: C:\Program Files\MetaTrader 5\terminal64.exe`
  - `terminal_data_path: host-local\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075...`
  - `max_concurrent: null`
  - `max_concurrent_policy: disabled_for_vnext_selected_cell_aggregate_drawdown_budget`

Impact:

- Local research sessions cannot audit live M1/tick data from disk unless they merge/materialize `origin/main` or read remote blobs directly.
- Local production-profile inspection is stale for redacted_account. Any claim based on the local `redacted_account.yaml` is invalid for current VPS/live truth.
- Final moonshot research must have a first-class "evidence authority resolution" step before any replay, feature build, label build, or ML training consumes live data.

## Finding 2 - Hard-Halt Broker Truth Is Current and Material

Remote source:

- `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json`
- `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json`
- `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json`
- `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/TRADE_FAILURE_REVIEW_2026-06-03.md`

Broker truth extraction:

- Account login: `0`.
- Server: `redacted_account-Server 2`.
- Balance/equity at extraction: `$99,965.20` / `$99,965.20`.
- Open positions: `0`.
- Pending orders: `0`.
- Grouped trades: `91`.
- Deals: `205`.
- Orders: `207`.
- Window: `2026-04-27T00:00:00+00:00` to `2026-06-04T05:16:10.304657+00:00`.

Full account attribution:

| Source | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| GTOS_SYSTEM | 82 | +$988.47 | 34 | 48 |
| MANUAL_OR_TEST | 8 | -$5.17 | 2 | 6 |
| OTHER | 1 | -$1,018.10 | 0 | 1 |

Recent GTOS activation window from `2026-05-29` through halt:

| Day | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| 2026-05-29 | 8 | -$34.04 | 3 | 5 |
| 2026-06-01 | 11 | -$601.06 | 4 | 7 |
| 2026-06-02 | 47 | +$889.41 | 19 | 28 |
| 2026-06-03 | 11 | -$1,114.00 | 5 | 6 |

Recent GTOS total:

- Trades: `77`.
- Net P/L: `-$859.69`.
- Wins/losses: `31` / `46`.
- Broker SL/comment/reason exits: `54`.
- Broker SL/comment/reason exit net: `-$9,280.84`.

Worst recent symbols:

| Symbol | Trades | Net P/L | Wins | Losses |
|---|---:|---:|---:|---:|
| XAUUSD | 12 | -$1,327.23 | 2 | 10 |
| NDX100 | 15 | -$1,151.56 | 3 | 12 |
| ETHUSD | 6 | -$696.18 | 2 | 4 |
| GBPJPY | 2 | -$543.61 | 0 | 2 |
| UKOUSD | 3 | -$297.35 | 1 | 2 |
| AUDJPY | 1 | -$274.05 | 0 | 1 |
| USDCAD | 3 | -$191.60 | 1 | 2 |
| NZDUSD | 2 | -$149.99 | 1 | 1 |
| UK100 | 2 | -$130.57 | 1 | 1 |
| USOUSD | 3 | -$58.31 | 1 | 2 |

Largest recent loss:

- Ticket/position `242689402`, `ETHUSD` BUY.
- Entry: `2026-06-02T22:46:08.184000+00:00`.
- Close: `2026-06-03T01:18:08.272000+00:00`.
- Net P/L: `-$673.62`.
- Exit comment: `[sl 1876.36]`.

Largest recent win:

- Ticket/position `242667071`, `GER30` BUY.
- Entry: `2026-06-02T20:31:12.177000+00:00`.
- Close: `2026-06-02T21:50:22.620000+00:00`.
- Net P/L: `+$1,318.24`.
- Exit comment: `closeger30`.

Impact:

- Broker truth must dominate local trade records and Telegram/projection rows.
- The live failure cannot be diagnosed from candidate/replay ledgers alone. Every replay/selector/scheduler/execution result must be joined to broker position/deal/order truth where available.
- Final moonshot must build a broker-truth normalized label layer from these broker JSONs, not just local proxy R.

## Finding 3 - Hard Halt Flags Are Present on Remote

Remote flags:

- `origin/main:pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
- `origin/main:pipeline_state/RESEARCH_RUNTIME_HALT.flag`
- `origin/main:knowledge_base/meta/AUTOSTART_DISABLED.flag`

All three contain:

```text
GTOS HARD PRODUCTION HALT
created_utc=2026-06-03T05:03:03.8169605Z
reason=CEO ordered full halt after unacceptable live performance; no live trading until reconciliation and explicit reactivation approval.
```

Impact:

- Any final moonshot runtime, replay, or live-supervisor route must treat these halt flags as authoritative until a separate reactivation package explicitly supersedes them.
- This is also data integrity: the account was flattened and runtime stopped; later local runtime data cannot be assumed continuous after the halt.

## Finding 4 - Remote M1 Capture Exists, but Is Not Local

Remote M1 inventory under `origin/main:data/m1`:

| Namespace | CSV files | Symbols | Dates | Data rows | Empty/header-only files |
|---|---:|---:|---:|---:|---:|
| root | 78 | 24 | 4 | 41,297 | 0 |
| redacted_account_live_bee34003 | 48 | 24 | 3 | 31,726 | 0 |

Remote root dates:

- `2026-05-29`
- `2026-05-31`
- `2026-06-01`
- `2026-06-02`

Remote namespaced dates:

- `2026-06-01`
- `2026-06-02`
- `2026-06-03`

Remote smallest M1 files:

- Several `2026-05-29` root files have only 4 to 5 data rows: `JP225`, `NAS100`, `SPX500`, `UK100`, `US30_cash`, `XAGUSD`, `XAUUSD`, `GER40`, `UKOIL_cash`, `USOIL_cash`.
- `data/m1/redacted_account_live_bee34003/GER40/2026-06-01.csv` has 4 data rows.

Remote M1 state:

- `origin/main:pipeline_state/m1_capture_state_redacted_account_live_bee34003.json`
- `symbol_count=24`.
- `last_error_count=0`.
- All `24` symbols have `last_cycle_status=ok`.
- All `24` symbols have `last_no_new_row_reason=latest_closed_m1_bar_not_new`.
- Updated at `2026-06-03T05:01:22.713448+00:00`.
- Alias differences:
  - `GER40 -> GER30`
  - `NAS100 -> NDX100`
  - `UKOIL_cash -> UKOUSD`
  - `US30_cash -> US30`
  - `USOIL_cash -> USOUSD`
- `GER40` has an old closed bar at `2026-06-02T19:58:00+00:00` with age `32602.713` seconds; this appears session-related, but final moonshot should classify it explicitly instead of treating it as normal freshness.

Impact:

- The remote M1 data is useful live-failure evidence, but it is short-window capture, not historical depth.
- Final moonshot must restore/materialize it locally before any daily microscope or ML dataset assumes M1 coverage.
- M1 freshness classification must remain session-aware and broker-alias aware.

## Finding 5 - Remote Tick Capture Exists With Corruption Evidence

Remote tick inventory under `origin/main:data/ticks`:

| Namespace | Files | Symbols | Parquet | JSON | State files | Corrupt-quarantine files |
|---|---:|---:|---:|---:|---:|---:|
| root | 12 | 6 | 6 | 6 | 0 | 12 |
| redacted_account_live_bee34003 | 97 | 24 | 60 | 37 | 24 | 26 |

Namespaced state summary:

- `24` state files.
- Total ticks written across state files: `5,537,821`.
- State saved range: `2026-06-02T20:00:39.115805+00:00` to `2026-06-03T05:01:24.715866+00:00`.
- Highest tick counters:
  - `NAS100`: `1,037,331`
  - `BTCUSD`: `1,028,830`
  - `ETHUSD`: `789,176`
  - `XAUUSD`: `444,091`
  - `GBPJPY`: `204,586`
- Lowest tick counters:
  - `UKOIL_cash`: `52,464`
  - `USDJPY`: `59,372`
  - `USDCHF`: `63,831`
  - `USOIL_cash`: `71,336`
  - `UK100`: `76,318`

Corrupt quarantine metadata:

- Namespaced corrupt metadata files: `13`.
- Affected symbols:
  - `AUDUSD`: 1
  - `CHFJPY`: 1
  - `EURGBP`: 1
  - `EURJPY`: 1
  - `EURUSD`: 2
  - `GBPJPY`: 1
  - `GBPUSD`: 1
  - `NAS100`: 1
  - `NZDUSD`: 1
  - `SPX500`: 1
  - `UK100`: 2
- Reasons include:
  - `malloc of size ... failed`
  - one `Parquet file size is 4 bytes, smaller than the minimum file footer (8 bytes)` on `CHFJPY`

Supervisor repair evidence:

- `origin/main:research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_DATA_CAPTURE_HEALTH_LEDGER.jsonl`
- Initial state: `m1_capture=1`, `tick_capture=24`, status `current_namespaced_capture_processes_present`.
- GBPUSD tick capture repair: before `tick_capture_count=23`, after `tick_capture_count=24`, `missing_tick_symbols=[]`.
- GBPJPY tick capture relaunch: after `tick_capture_count=24`, status `pass_after_gbpjpy_tick_capture_relaunch`.

Impact:

- Tick capture had real runtime fragility under live load. The system recovered, but corruption happened across many symbols.
- The final system must use atomic parquet writes, rotation/segment sizing, memory-pressure detection, write-ahead temporary files, footer validation, post-write metadata validation, and automatic gap backfill.
- Strict tick replay must mark corrupt-gap intervals and not treat quarantined parquet paths as reliable tick truth.

## Finding 6 - Dual Broker Profile Identity Was Verified on Remote

Remote supervisor ledger:

- `origin/main:research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_ACCOUNT_PROFILE_LEDGER.jsonl`

Repeated read-only checks verified both profiles:

redacted_account:

- Profile: `config\profiles\redacted_account.yaml`
- Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Runtime namespace: `redacted_account_live_bee34003`
- Account match fields all true:
  - company
  - currency
  - login SHA-256
  - server
  - terminal data path
  - terminal path prefix

FTMO:

- Profile: `config\profiles\operator_profile.yaml`
- Terminal: `C:\MT5\FTMO\terminal64.exe`
- Runtime namespace: `operator_profile`
- Account match fields all true:
  - company
  - currency
  - login SHA-256
  - server
  - terminal data path
  - terminal path prefix

VPS V3/FTMO verification:

- `origin/main:research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_VERIFICATION_RESULT.json`
- `ok=true`.
- Broker profile verifiers:
  - `ftmo`: `ok=true active_symbol_count=24 alias_count=24 issue_count=0`
  - `operator_profile`: `ok=true active_symbol_count=24 alias_count=24 issue_count=0`
  - `redacted_account`: `ok=true active_symbol_count=24 alias_count=24 issue_count=0`
- Read-only MT5 probe:
  - redacted_account terminal initialized with matching login hash and `4` open positions at that earlier VPS check.
  - FTMO portable terminal initialized with matching login hash, `positions_total=0`, `orders_total=0`.

Impact:

- Remote profile/account identity was strong after VPS fixes.
- Local profile state is not equivalent to remote live state.
- Final moonshot must namespace every broker/account artifact by account namespace and must never merge redacted_account and FTMO data by canonical symbol alone.

## Finding 7 - FTMO Prep Was Locally Complete, Then VPS Authority Took Over

Local FTMO prep route:

- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/COMPLETION_AUDIT.json`
- `VERIFICATION_RESULT.json`
- `MT5_CAPTURE_PROGRESS.json`

Local FTMO prep counts:

- Active aliases resolved: `24/24`.
- Symbol specs: `24`.
- Session history rows: `24`.
- Runtime audit rows: `7`.
- Implementation rows: `15`.
- Profile verifier: `ok=true`.
- Route verifier: `ok=true`.
- Capture status: `capture_loop_complete`.

Recorded non-local requirements:

- VPS production authority rebase/export before activation.
- Owner confirmation of FTMO account phase/stage/add-ons.

Remote VPS V3/FTMO route later covered the production authority and profile/terminal account identity pieces. Account-stage/add-on remains a dashboard/owner fact unless another route captured it later.

Impact:

- FTMO is not a mirror of redacted_account data. It needs its own symbol geometry, sessions, spread/cost, stop/freeze, commission/swap, margin, and execution retcode capture.
- Final moonshot needs a dual-broker comparative cost/behavior dataset, not a single-profile assumption.

## Finding 8 - MT5 Local Cache Preservation Is Valuable but Incomplete for Broker Truth

Local route:

- `research/operations/vnext_mt5_local_cache_preservation_2026_06_01/`

Archive proof:

- Archive path: `C:\Users\MSI\Documents\GTOS_MT5_LOCAL_PRESERVATION_2026_06_01\GTOS_MT5_LOCAL_PRESERVATION_2026_06_01.tar.gz`
- Archive bytes on disk: `4,454,594,820`.
- Archive uncompressed bytes: `12,089,217,220`.
- Archived file count: `2,884`.
- Verification: `ok=true`, `issues=[]`.
- Inventory rows: `3,622`.
- Sensitive exclusions: `107`.
- Blocked rows: `0`.
- Missing root rows: `0`.

Coverage:

- External MT5 cache symbol count: `55`.
- Repo-local symbol count: `24`.
- External cache adds:
  - native MT5 market history
  - tick cache
  - broker/server metadata
  - terminal logs
  - MQL5 Files evidence
  - program install reproducibility
- Symbols added by external cache include broker-native and adjacent symbols such as `GER30`, `NDX100`, `UKOUSD`, `USOUSD`, `US30`, `US100.cash`, `US500.cash`, `USTEC`, and others.
- Symbols in repo not in external cache:
  - `GER40`
  - `UKOIL_cash`
  - `USOIL_cash`

Remaining exact requirements:

- Full account orders/deals/positions history with commissions, swaps, close reasons, partial lifecycle.
- Per-symbol `symbol_info` / `symbol_info_tick` / session metadata for all 24 vNext symbols.
- Current commission, swap, margin, tick value, stop level, freeze level, spread samples.
- Server-side history windows not present in local cache.

Impact:

- MT5 cache preservation is enough to prevent loss of local terminal evidence.
- It is not enough to prove broker-real execution economics.
- Final moonshot must use the hard-halt broker JSON plus fresh read-only exports as broker truth, and treat local MT5 cache as preserved auxiliary evidence.

## Finding 9 - Source Capture Repair Quantifies the Remaining Data Debt

Local route:

- `research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/POST_LANE18_COMPLETION_AUDIT.json`

Route row counts:

- Source gap superledger rows: `16,579,491`.
- Repaired rows: `2,949,305`.
- Non-generatable rows: `41,953,158`.
- Read-only export requirement rows: `2,823`.
- Forward capture contract rows: `351`.
- Validation rows: `3`.

Disposition counts:

| Disposition | Rows |
|---|---:|
| filled_now | 716,423 |
| reconstructed_now | 32 |
| proxy_bound_now | 1,074,665 |
| read_only_export_required | 319,006 |
| forward_capture_required | 290,380 |
| non_generatable_historical_truth | 14,178,974 |
| blocked_with_exact_source_requirement | 11 |

Largest read-only export requirements:

- `RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE`: `10,417,228`.
- `broker_cost_and_lifecycle`: `289,600`.
- `m1_coverage_or_structure`: `5,188`.
- `partial_be_runner_parameter_sweep_requires_raw_ordered_bid_ask_tick_path_or_m1_event_sequence...`: `5,010`.
- `tick_coverage_or_structure`: `4,860`.
- `ordered_bid_ask_tick_timeline`: `4,860`.
- `broker_exact_tick_value`: `4,860`.
- `BROKER_SPEC_FIELD_GAP`: `408`.
- `h4/h1/d1 coverage or structure`: `328` each.
- `broker_truth_or_cost_gap`: `216`.
- `commission_schedule`: `144`.
- `swap_long_short_mode_triple_day_rollover`: `120`.

Largest forward capture requirements:

- `market_hours_state`: `289,928`.
- `missing_replay_gap_capture_or_repair`: `1,909`.
- `hybrid_routing_variant_requires_replayed_or_forward_policy_results_by_the_named_routing_dimension`: `182`.
- `broker_order_deal_position_lifecycle`: `120`.
- `BROKER_LIFECYCLE_FIELD_GAP`: `120`.
- `selected_risk_portfolio_broker_news_calendar`: `27`.
- `selected_cell_risk_proof`: `24`.
- `portfolio_state`: `24`.
- `modify_request_retcode_external`: `24`.
- `false_local_close_broker_contradiction_proof`: `24`.
- `correlation_cluster`: `24`.
- `account_baseline_balance_equity`: `24`.

Largest proxy-bound fields:

- `cost_adjusted_r`: `289,928`.
- `correlation_cluster_runtime_snapshot`: `289,928`.
- `broker_real_net_r`: `289,920`.
- `net_r`: `289,600`.
- `spread_to_risk`: `287,810`.
- `tick_coverage_or_structure`: `282,950`.
- `ordered_bid_ask_tick_timeline`: `282,950`.
- `broker_exact_tick_value`: `212,777`.

Exact blocked fields include:

- `mechanism_coverage_absent`
- `row_class_coverage_absent`
- `network_origin_compliance`
- `moonshot_lane08_digital_twin`
- `moonshot_lane06_label_store`
- `moonshot_lane05_feature_store`
- `lane11_policy_engine_terminal_contract`
- `lane10_missing_gap_origin_family_absent`
- `dependency_absent_or_incomplete`
- `compliance`

Impact:

- The final moonshot system cannot honestly claim broker-real scoring or tick-real execution while these buckets remain proxy-bound or source-required.
- The correct next research move is not another broad summary. It is closing these exact source requirements into feature/label/digital-twin inputs or marking them source-bound with downstream behavior.

## Finding 10 - LFS Is Material to Final Research

Local targeted checks:

- `git lfs ls-files -n` returned `3,290` tracked LFS paths.
- Targeted Git attributes show these critical source-capture ledgers are LFS-tracked:
  - `POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz`
  - `POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz`
  - `POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz`
- Local materialized sizes:
  - `POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz`: `1,794,937,536` bytes.
  - `POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz`: `749,813,481` bytes.
  - `POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz`: `104,364,779` bytes.

Broad `git lfs status` timed out on the dirty repo, so this audit used targeted materialization checks instead of a full LFS status.

Impact:

- Heavy LFS ledgers are necessary for source/debt closure and final research reproducibility.
- They are not required for live execution directly, but they are required for full final moonshot research unless a route-local manifest proves a smaller, non-lossy derivative is sufficient.
- Any cleanup must preserve either materialized files, LFS pointers plus remote object availability, or an external archive with hashes.

## Finding 11 - Dual-Broker Supervisor Closed Cleanly, but It Proved Prior Data/Runtime Defects

Remote route:

- `origin/main:research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json`
- `origin/main:research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_VERIFICATION_RESULT.json`

Final live state at supervisor close:

- Architecture: one full redacted_account vNext/moonshot runtime plus lightweight FTMO execution follower/projector bridge.
- redacted_account run agents: `24`.
- redacted_account tick captures: `24`.
- M1 capture: `1`.
- FTMO run agents: `0`.
- FTMO execution follower: `1`.
- Dual broker projector: `1`.
- MT5 terminals: `2`.
- Duplicate runtime symbols detected: `false`.
- Memory commit percent: `52.55`.
- Free memory: `2,069 MB`.
- C drive free: `56.59 GB`.

Final BTC lifecycle parity:

redacted_account:

- Ticket `242690948`, `BTCUSD`.
- State: `source_already_tp1_partial_and_be`.
- Entry `67223.29`, SL `67223.29`, TP `68578.18`, residual volume `0.28`.

FTMO:

- Ticket `155209892`, `BTCUSD`.
- State: `target_tp1_partial_and_be_verified_by_broker_readback`.
- Manual partial close order `155214262`, retcode `10009`.
- SLTP retcode `10009`.
- Residual volume `0.3`.
- Close price used `67810.07`.
- Entry `67171.7`, SL `67171.7`, TP `68371.82`.

Known non-blocking followups in route:

- Decide whether FTMO should have independent broker-local exit management beyond lightweight follower model.
- Full runtime test suite was too heavy/timed out; focused suites and route verifier passed.
- `LIVE_STATE` still stale versus latest commits.

Impact:

- The supervisor repaired concrete runtime/data issues: notification namespace, follower persistence, projector persistence, target state restore, tick capture relaunches, and BTC lifecycle parity.
- The final system needs these repairs treated as regression cases, not just route history.

## Source Integrity Conclusions

1. The current local checkout is not a valid standalone evidence base for the failed live system. It lacks materialized remote M1/tick data and has a stale redacted_account profile. Use `origin/main` or merge/materialize it before final moonshot work.
2. Broker truth exists and is decisive for redacted_account. Use broker JSONs from the hard-halt route as the authority for recent live performance.
3. FTMO profile identity and local symbol-spec/session prep are strong, but FTMO broker-real live data remains sparse compared with redacted_account.
4. M1 capture is present on remote for 24 symbols and namespaced redacted_account, but only short-window. It cannot replace historical M1 depth.
5. Tick capture is present on remote for 24 namespaced symbols, with `5,537,821` tick counter total in state files, but corruption/relaunch evidence proves the tick pipeline needs stronger write integrity.
6. Source Capture Repair quantified massive remaining data debt. Final moonshot must close read-only export, forward capture, and non-generatable buckets explicitly.
7. Heavy LFS ledgers are central to source repair and final research reproducibility. They must be preserved/materialized or replaced only by hash-proven non-lossy derivatives.

## Final Moonshot Capture/Repair Requirements

Data authority:

- Merge/materialize `origin/main` live evidence into the final research worktree or build a remote-blob reader that records exact commit/path/hash.
- Reject stale local profile/data assumptions when local disk diverges from remote live authority.
- Refresh `.context/00_core/research_current_state.md` after live/research reconciliation.

Broker truth:

- Convert hard-halt broker groups/deals/orders into canonical broker-real labels.
- Join broker truth to candidates, selector rows, scheduler rows, execution policy rows, Telegram rows, and trade records by `position_id`, order, ticket, source lifecycle key, symbol, side, entry time, volume, and magic.
- Make broker-real net P/L, commission, swap, fee, close reason, partial lifecycle, and manual/action classification first-class labels.

M1/tick:

- Materialize remote `data/m1` and `data/ticks` before any replay that claims live-failure coverage.
- Repair tick writer architecture: atomic temporary writes, segment rotation, footer validation, memory-pressure guard, post-write row count, parquet metadata verification, and automatic backfill/gap reports.
- Mark corrupt tick intervals as source gaps in replay and ML features.

Broker profile/account:

- Treat redacted_account and FTMO as separate account namespaces at every artifact boundary.
- Preserve broker-native aliases separately from canonical symbols.
- Capture per-account symbol specs, sessions, swaps, commissions, margin, tick value, stop level, freeze level, spread samples, and retcodes.
- Resolve FTMO dashboard/account-stage/add-on constraints into an auditable account profile field.

Source capture:

- Close `319,006` read-only-export rows where possible.
- Close `290,380` forward-capture rows prospectively.
- Keep `14,178,974` non-generatable historical rows source-bound, not silently filled by proxy.
- Promote the `11` exact blocked-source requirements into explicit owner/source/workflow actions.

Research integrity:

- Feature/label/digital-twin/ML routes must record whether each row is broker-real, tick-real, M1-real, proxy-bound, forward-capture-required, read-only-export-required, or non-generatable.
- No final moonshot decision should mix broker-real and proxy R without explicit class separation.
- Any LFS cleanup must preserve the source-capture ledgers or prove exact recoverability by LFS object ID, archive path, hash, and manifest.

## Files Read or Queried

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/*`
- `origin/main:research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/*`
- `origin/main:research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/*`
- `origin/main:data/m1/*`
- `origin/main:data/ticks/*`
- `origin/main:pipeline_state/m1_capture_state_redacted_account_live_bee34003.json`
- `origin/main:pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
- `origin/main:pipeline_state/RESEARCH_RUNTIME_HALT.flag`
- `origin/main:knowledge_base/meta/AUTOSTART_DISABLED.flag`
- `config/profiles/redacted_account.yaml`
- `config/profiles/operator_profile.yaml`
- `research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/POST_LANE18_COMPLETION_AUDIT.json`
- `research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01/LANE18_COMPLETION_AUDIT.json`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/*`
- `research/operations/vnext_mt5_local_cache_preservation_2026_06_01/*`
