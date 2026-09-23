# V122G/V122H Fable B4 Tick Source-Realism Pre-Replay Brief

Generated: `2026-07-06T04:46:36Z`

## 1. Latest Completed Replay
- Latest broad replay: `BROAD_LIVE_AS_IF_REPLAY_V121AG_EFFECTIVE_STOP_HAZARD_CAP_TRANSFER_REPAIR_20260513_20260517`.
- Window: `2026-05-13..2026-05-17`, hostile bucket only, not full-reservoir proof.
- Trades: `45`; net/gross/final R: `21.82482975` / `25.17869106` / `25.17869106`.
- Cash PnL: `12465.17720161`; risk cash `26023.79295971`; risk pct sum `24.5125`.
- W/L/F: `27/18/0`.
- Exact-window denominator: source-bound R `407295.6072920759`; package axes `1101`; candidate axes `886`; scorecard/order axes `33`; filled axes `29`; actual executable R `21.29589138`.

## 2. Running Processes
- No broad replay is running at this checkpoint.
- The V122F tick export completed cleanly; no bridge restart was used.
- Context OS sidecars may remain alive and are not replay processes.

## 3. Baseline Comparison
- V89D: `56` trades, `34.84520454R`, W/L/F `41/15/0`.
- V90: `51` trades, `28.84201157R`, W/L/F `37/14/0`.
- V92: `51` trades, `29.35570236R`, W/L/F `37/14/0`.
- V121AG: `45` trades, `21.82482975R`, W/L/F `27/18/0`.
- V122C June 3 B3 proof: `14` trades, `-1.8242459R`, missing ladder rows `0`, executed REFUSED/source-gap `0`.
- V122E June 10 B3 proof: `6369` candidates, `96` scorecard rows, `51` orders, `0` trades, `6318` missed rows; diagnostic M15/skip-tick path was the blocker.

## 4. Dirty Files / Active Changes
Active B4/B5 scoped code changes:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `scripts/export_mt5_research_ohlcv.py`
- `scripts/export_mt5_research_ticks.py`
- `scripts/inspect_mt5_tick_availability.py`
- `tests/test_mt5_research_export_symbol_defaults.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/compare_broad_live_as_if_replay_runs.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_compare_broad_live_as_if_replay_runs.py`
- `tests/test_denominator_to_deployment_verifier.py`

Generated source/proof artifacts:
- `data/mt5_research_exports/tick_availability/v122f_b4_bridge_liveness_xauusd_1m_20260706T043259Z.json`
- `data/mt5_research_exports/bridge_ftmo_ticks_v122e_20260610_full_plus_expiry/manifest.json`
- `data/mt5_research_exports/bridge_ftmo_ticks_v122e_20260610_full_plus_expiry/ticks/<symbol>/v122e_full_plus_expiry_ticks.jsonl`

Unrelated pre-existing dirty files and historical deletions remain ignored.

## 5. Subagent Findings
- Huygens: incorporated. Colima port forwarding is expected; earlier failure was Wine-side RPyC timeout. Bridge recovered; `terminal_info()` is connected and trading disabled. Bridge-only restart recipe recorded but not used.
- Rawls: incorporated. V122E command pattern confirmed; V122G should be the same one-day full-grid proof without `--skip-tick-source`.
- Avicenna: incorporated. Export/manifest visibility confirmed. Source-truth issues patched before replay: lazy tick SHA validation and actual first/last tick coverage.
- Earlier Jason/Bohr/Hume findings remain incorporated as recorded in the V122F map.

## 6. Mismatch Classes
- Source-bound -> candidate: not the active B4 blocker; current hostile broad transfer remains `886/1101` generated axes.
- Candidate -> selector: B1/B3 raw/effective and risk-ladder truth closed for current stack.
- Selector -> scheduler: B2 priority/context and route-resolution repairs closed.
- Scheduler -> risk: ladder provenance closed; executable distribution depends on ordered fill source.
- Risk -> order: selected bridge is bounded-smoke and verifier-green.
- Order -> lifecycle/fill: V122G tests whether non-June M15/skip-tick diagnostic paths can bind to ordered tick truth.
- Fill -> exit: exit tuning remains deferred until ordered-source fill authority exists.
- Ledger/verifier: B5 proof machine green; V122G adds source-truth guardrails.

## 7. Fixed / Partial / Open
- Fixed: MT5 bridge liveness probe succeeded; XAUUSD one-minute tick proof has `73` ticks.
- Fixed: 9-symbol FTMO tick export completed with `errors=[]`.
- Fixed: resolver sees all 9 tick sources, and lazy tick queries validate each overlapping file hash before loading rows.
- Fixed: tick coverage now uses actual first/last ticks, not requested export bounds.
- Replaced: first V122G attempt was interrupted before behavior proof because eager hash validation scanned old non-overlapping selected-order tick files. Its partial summary is labeled `interrupted_partial_not_final_proof` and is not behavioral evidence.
- Partial: this is a targeted 9-symbol B4 proof, not full 24-symbol or B7 proof-ladder closure.
- Open: hostile five-day fill-realism proof after targeted proof; B6 broker-cost calibration; B7 proof ladder; B8 live path.

## 8. Highest-Leverage Same-Root Batch
Active batch: `B4_FILL_SIMULATION_REALISM_SOURCE_TICK_AUTHORITY`.

Reason: V122D/V122E showed non-June rows reaching scorecard/order surfaces but staying diagnostic under explicit skip-tick/M15 proxy. The same-root repair is ordered tick source authority, not selector tuning.

## 9. Files / Components
- Tick export/availability: `scripts/export_mt5_research_ticks.py`, `scripts/inspect_mt5_tick_availability.py`, `scripts/export_mt5_research_ohlcv.py`.
- Fill-source/fill-realism authority: `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
- Harness: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`.
- Tests: `tests/test_v4_timewarp_simulated_live_research_loop.py`.

## 10. Patch Types
- Tick source SHA validation: correctness/proof repair; validation occurs at overlapping lazy-window query time, so old non-overlapping tick files cannot stall a targeted proof.
- Tick actual first/last coverage: correctness/proof repair; behavior-changing if prior requested-window metadata let stale tick gaps appear covered.
- Export/default mapping: source-hydration correctness repair.
- Existing B5 patches: proof-machine repair; replay behavior-neutral.

## 11. Expected Measurable Effect Before Replay
- Candidate -> scorecard transfer: expected same or near V122E unless source availability changes scoring.
- Scorecard -> order transfer: should reveal whether diagnostic orders become ordered-tick executable or remain explicitly non-executable.
- Order -> fill transfer: may increase only through ordered tick authority; M15 proxy remains diagnostic.
- Missed positive/negative R: diagnostic rows remain scoreable/missed, not discarded.
- Trade count/net/gross/final R/W-L-F: unknown until targeted replay; a worse result is acceptable if it removes false fill authority.
- Cost-refused/source-gap execution: must remain `0`.
- Risk distribution: report full/reduced/diagnostic separately; no full-risk promotion from missing tick truth.

## 12. Proof Criteria
V122H helps if:
- Summary `tick_source_mode` is not `skipped_by_explicit_repair_smoke_flag`.
- Ordered tick truth appears in source/oracle/order surfaces for the 9 covered symbols.
- Executable fills use ordered tick authority.
- No M15 proxy or first-touch optimistic row becomes executable.
- Executed REFUSED/source-gap/live/final rows remain `0`.

V122H fails or exposes the next blocker if:
- Valid ordered ticks exist but replay still routes all eligible rows to diagnostic M15 proxy.
- Source binding loses tick authority after resolver selection.
- A symbol outside the 9-symbol export is needed for material transfer; then the next B4 action is full-surface tick hydration, not selector tuning.
