# VNEXT Full Historical Replay Data Requirements - 2026-05-24

## Controller Verdict

The completed `vnext_replay_truth_engine_and_saturated_ablation_2026_05_24` package is not the full moonshot replay. It is a logged-event replay truth package. It consumed six event/shadow logs and measured vNext runtime behavior on 1,635 already-observed event groups. It did not generate candidates mechanically from every historical bar across every local symbol/timeframe.

This is the next required work: full historical vNext candidate generation over all available OHLC/M1/M5/tick/Sierra data, then path-aware simulated R, ablation, MIXED resolution, and kill/repair/promote decisions from the generated candidate universe.

## Verified Current Replay Scope

- Current pushed HEAD: `2d40b1f38 research: package vnext replay ledgers for lfs`.
- Replay final report: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_FINAL_REPORT_2026-05-24.md`.
- Replay package rows: 1,635 event groups, 23,042 source event rows, 3,270 saturated replay rows, 2,094,510 ablation rows, 1,534 MIXED rows.
- Data inventory was broad: 18,062 inventory rows, 92.55GB inventoried, 26.78GB hashed, 149 large files deferred.
- Performance replay source logs consumed only:
  - `shadow_logs/candidate_features_log.jsonl`
  - `shadow_logs/candidate_path_follow.jsonl`
  - `shadow_logs/candidate_path_contract_audit.jsonl`
  - `shadow_logs/candidate_ltf_path_order.jsonl`
  - `shadow_logs/pending_limit_lifecycle.jsonl`
  - `shadow_logs/trade_index_lifecycle_audit.jsonl`

## What The Logged-Event Replay Found

- Current shadow/default path: `-59.0R`, 100 entry-touched trades, 69 terminal trades, 4 target-first wins, 65 stop-first losses, max drawdown `-63.5R`.
- Hypothetical activated vNext path: `+1.5R`, only 1 entry-touched trade, 1 terminal win, max drawdown `0.0R`.
- This means vNext protected the slice but overblocked. It did not prove a production profit engine.
- Blocking came from deterministic converted guards and AVOID pressure, not paid AI failure. Paid AI replay was not run.
- M15 path blindness is real: 578 groups had M15 vs lower-path comparison; 162 disagreed, rate `0.280276816609`.
- MIXED was classified, not fully resolved: 927 ambiguous but replay-resolvable, 172 source-required, 291 neutral/no-effect, 90 replay attribution only, 50 useful context, 2 resolvable into AVOID.

## Local Data Available Now

### Core Seven Full-Path Historical OHLC

Core full-path symbols with M1/M5/M15/H1/H4/D1 coverage are:

- `GBPJPY`
- `GBPUSD`
- `NAS100`
- `US30_cash`
- `USDJPY`
- `XAGUSD`
- `XAUUSD`

Primary full-path source paths:

- M1/M5: `data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars/`
- M15: `data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1/`
- H1/D1: `data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1/`
- H4 support: `data/historical_2026/`

Core date coverage:

- FX core (`GBPJPY`, `GBPUSD`, `USDJPY`): M1/M5 from `2022-01-03` to `2026-04-30`; M15 from mid-April 2022 to `2026-04-30`; H1/D1 from `2022-01-03` to `2026-04-30`.
- Metals (`XAUUSD`, `XAGUSD`): M1/M5 from `2022-01-03 01:00` to `2026-04-30`; M15 from `2022-01-03`/`2022-02-01` to `2026-04-30`; H1/D1 from `2022-01-03` to `2026-04-30`.
- Indices (`NAS100`, `US30_cash`): M1/M5/M15/H1/D1 from `2022-10-20` to `2026-04-30`.

### Expanded Markets Already Present

Expanded historical symbols with M15/H1/H4/D1 coverage but missing M1/M5 for full path simulation:

- `AUDJPY`, `AUDUSD`, `BTCUSD`, `CHFJPY`, `ETHUSD`, `EURGBP`, `EURJPY`, `EURUSD`, `GER40`, `JP225`, `NZDUSD`, `SPX500`, `UK100`, `UKOIL_cash`, `USDCAD`, `USDCHF`, `USOIL_cash`

Expanded coverage is mostly `2026-01-02` to `2026-04-24`; some key symbols (`EURUSD`, `GER40`, `UK100`, core symbols in `historical_2026`) start `2025-10-01`. This is enough for higher-timeframe candidate generation, but not enough for full M1/M5 fill/no-fill/path truth unless M1/M5 is exported.

### Recent Tick Data

Repo-local MT5 tick parquet exists for:

- `GBPJPY`, `GBPUSD`, `NAS100`, `US30_cash`, `USDJPY`, `XAGUSD`, `XAUUSD`

Tick coverage is mostly `2026-04-28` to `2026-05-15` (`NAS100` and `US30_cash` start `2026-04-27`). This is useful for recent forward/live path calibration and intrabar ordering. It does not cover the full 2022-2026 replay.

### Sierra Data

Sierra `.scid` files exist under `C:/SierraChart/Data`, including:

- `XAUUSD.scid`
- `EURUSD.scid`
- `MNQM26-CME.scid`, `NQM26-CME.scid`, `ESM26-CME.scid`, `MESM26-CME.scid`
- `GCM26-COMEX.scid`, `MGCM26-COMEX.scid`
- `6JM26-CME.scid`, `6BM26-CME.scid`, `6EM26-CME.scid`
- `YMM26-CBOT.scid`, `MYMM26-CBOT.scid`
- oil, rates, VIX, and other proxy contracts

Sierra depth files were deleted to recover disk. That removes historical depth-book replay unless redownloaded. The `.scid` files remain usable for time-and-sales/OHLC-style path/proxy conversion where the parser supports them.

### Row-Bearing Shadow Logs Not Fully Consumed

The logged-event replay consumed six logs. Other row-bearing logs still exist and should feed either candidate generation context, source repair, or validation diagnostics:

- `shadow_logs/structure_detector_backfill_2022_2023.jsonl` - 14,878 rows
- `shadow_logs/fvg_ob_confluence_audit.jsonl` - 7,310 rows
- `shadow_logs/prefill_delivery_path_resolutions.jsonl` - 7,266 rows
- `shadow_logs/fvg_ob_confluence_resolutions.jsonl` - 7,229 rows
- `shadow_logs/v2b_forward_pair_resolutions.jsonl` - 7,229 rows
- `shadow_logs/prefill_delivery_path_audit.jsonl` - 7,145 rows
- `shadow_logs/v2b_forward_pair_resolution_audit.jsonl` - 6,943 rows
- `shadow_logs/live_candidate_opportunity_clusters.jsonl` - 6,853 rows
- `shadow_logs/missed_opportunity_shadow.jsonl` - 6,759 rows
- `shadow_logs/live_candidate_strategy_rollups.jsonl` - 6,647 rows
- `shadow_logs/opportunity_lifecycle_audit.jsonl` - 6,142 rows
- `shadow_logs/j46_j49_exit_comparator_audit.jsonl` - 5,128 rows
- `shadow_logs/live_structural_strategy_metadata.jsonl` - 5,125 rows
- `shadow_logs/regime_decay_outcome_join.jsonl` - 5,124 rows
- `shadow_logs/strategy_follow_evaluations.jsonl` - 2,185 rows
- `shadow_logs/ai_narrowing_policy_shadow_evaluations.jsonl` - 274 rows

These logs are not a substitute for full historical candidate generation. They are additional evidence layers that must be joined into the replay audit and used to explain behavior.

## Data Still Needed

### Required For Full Core Replay

1. Export/read-only refresh for core seven from `2026-05-01` through current date for M1/M5/M15/H1/H4/D1. Current full historical exports stop at `2026-04-30`, while local ticks/shadow logs continue into May.
2. Use existing tick parquet for `2026-04-27/28` to `2026-05-15` where available.
3. Use M1/M5 as the default path-truth layer for 2022-2026 because full tick history is not local.

### Required For Expanded-Market Full Replay

Export M1/M5 from MT5 read-only for every expanded symbol available in broker history:

- `EURUSD`, `GER40`, `UK100`, `SPX500`, `USDCAD`, `CHFJPY`, `AUDJPY`, `AUDUSD`, `EURGBP`, `EURJPY`, `NZDUSD`, `USDCHF`, `JP225`, `BTCUSD`, `ETHUSD`, `UKOIL_cash`, `USOIL_cash`

If a broker symbol is unavailable, the replay must record the exact symbol availability failure and continue with the markets that can be exported. Missing expanded M1/M5 is not a reason to shrink the whole replay back to seven symbols.

### Required For Sierra/Proxy Path Use

1. Convert supported `.scid` files into replay-readable OHLC/path inputs with source hashes.
2. Map futures/proxies explicitly:
   - NQ/MNQ -> NAS100/NAS100 proxy
   - YM/MYM -> US30/US30_cash proxy
   - GC/MGC -> XAUUSD/gold proxy
   - SI/SIL -> XAGUSD/silver proxy
   - 6J -> USDJPY proxy
   - 6B -> GBPUSD proxy
   - 6E -> EURUSD proxy
3. Treat Sierra proxy as path/source evidence, not broker-native CFD truth, unless the source contract explicitly says otherwise.
4. Depth-specific claims must be parked or redownloaded. The deleted `.depth` files are not available now.

### Non-Generatable Historical Truth

These must not block simulated historical replay:

- broker tickets/deals/fills/commission/swap/slippage for trades that were never placed
- paid AI completions for every historical candle without explicit budget approval
- historical live orchestrator state that was not logged

These belong to forward/demo calibration or minimal stratified AI sampling, not to the first mechanical full historical replay.

## Required Full Replay Pipeline

The next session must build or wire a single replay driver with this chain:

1. Load historical OHLC by symbol/timeframe.
2. Enumerate every eligible M15 candle close across every available symbol and session.
3. Build production-like `raw_data`.
4. Compute MSO/market state.
5. Run pre-AI vNext routing.
6. Generate mechanical candidate geometry for `ob_retest`, `fvg_fill`, `breaker_re_entry`, and every runtime-supported converted route family that can be generated from local data.
7. Run L2 verification deterministically.
8. Build vNext post-L2 candidate events.
9. Run direct/route/risk/pending/pre-AI vNext surfaces in current-shadow and hypothetical-activated modes.
10. Simulate pending lifecycle and entry/SL/TP path ordering using best available source priority: tick/Sierra where source-valid, then M1, then M5, then M15 proxy with an explicit uncertainty label.
11. Compute simulated R, expectancy, win rate, trade frequency, no-fill rate, stop-first rate, drawdown, daily drawdown, market/session/side/timeframe/family breakdowns, and prop-firm challenge metrics.
12. Run ablations by vNext surface: AI routing, AVOID filters, FOLLOW pressure, MIXED context, source-repair guards, no-fill rules, gate/risk rules, entry variants, exit/trailing rules, market/session/timeframe selectors.
13. Resolve MIXED rows by observed generated-candidate outcomes where possible; leave only genuinely source-required or neutral context as MIXED.
14. Emit repair/export ledger for every missing data class with exact symbol/timeframe/date/source requirement.
15. Emit a final decision map: promote, kill, repair, keep-shadow, or requires forward/demo calibration.

## Existing Code Surfaces To Reuse

- Historical OHLC scaffolding: `scripts/historical_data_loader.py`
- MT5 export scaffolding: `scripts/export_mt5_research_ohlcv.py`, `scripts/export_mt5_historical.py`, `scripts/inspect_mt5_history_availability.py`
- Sierra conversion/inspection: `scripts/inspect_sierra_scid.py`, `scripts/convert_sierra_scid_to_ohlcv.py`
- vNext runtime APIs: `src/components/gtos_vnext_runtime.py`
- Current logged-event replay builders: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/build_vnext_replay_*`
- Live orchestration flow reference: `src/components/orchestrator.py`
- Runtime tests: `tests/test_gtos_vnext_runtime.py`, `tests/test_gtos_vnext_master_conversion_ledger.py`

## Immediate Next Work

Start a fresh full historical replay implementation session. Do not continue the logged-event replay session. Do not rerun Stage05/Stage09 unless validating packaging. The next deliverable is a full historical candidate-generation replay harness and data acquisition/coverage ledger, not another summary of the logged-event package.

The first implementation checkpoint must prove this with disk artifacts:

- source coverage ledger by symbol/timeframe/date/source
- candidate-generation ledger from historical bars, not only shadow logs
- path-source ledger showing tick/Sierra/M1/M5/M15 mode per candidate
- vNext decision ledger for current-shadow and hypothetical-active modes
- simulated R and no-fill/stop-first/target-first outcome ledger
- MIXED-resolution delta ledger

No arbitrary top-N scope, no seven-symbol-only cap if expanded data is available, no broker-realized execution blocker for simulated replay, and no default-off graveyard conclusion without ablation evidence.
