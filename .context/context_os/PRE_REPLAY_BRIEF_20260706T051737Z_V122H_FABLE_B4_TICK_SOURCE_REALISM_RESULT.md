# Pre-Replay Brief - V122H Fable B4 Tick Source Realism Result

Generated: 2026-07-06T05:17:37Z
Status: post-result control brief before any next replay.

## 1. Latest Completed Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`
Window: `2026-06-10..2026-06-10`
Scope: `targeted_one_day_2026_06_10_9_symbol_tick_export_available_not_full_b7_proof`
Status: `broad_live_as_if_replay_materialized_broker_live_closed`

Numbers:
- Candidates/scorecard: `6369` / `96`
- Orders: top-level order ledger rows `29`; terminal/simulated order rows `13`
- Trades: `10`
- Net/gross/final R: `0.07137833` / `0.86997526` / `0.86997526`
- Cash PnL/risk cash/risk pct: `158.91066658` / `4006.86646365` / `4.0`
- W/L/F: `7/3/0`
- Missed rows: `6356`
- Stress raw/+0.05/+0.10/+0.20R: `0.07137833` / `-0.42862167` / `-0.92862167` / `-1.92862167`
- Monte Carlo total/max DD p50/p05/worst: `0.07137833` / `-1.74320136` / `-2.72456294` / `-2.74456294`

This smoke proves a local B4 source-realism repair; it does not prove total reservoir conversion or live readiness.

## 2. Running Replay State

No broad replay, pytest, verifier, or harness process was running at this update. Existing Context OS MCP stdio sidecars remain present.

## 3. Baseline Comparison

V122E same-window comparator had `6369` candidates, `96` scorecard rows, `0` trades, `0R` net/gross/final, and `0` cash PnL under explicit skip-tick/M15 diagnostic mode.

V122H delta versus V122E:
- Candidate rows delta: `0.0`
- Scorecard rows delta: `0.0`
- Terminal order rows delta: `13.0`
- Trade rows delta: `10.0`
- Net/gross/final R delta: `0.07137833` / `0.86997526` / `0.86997526`
- Cash PnL delta: `158.91066658`
- Oracle rows delta: `-35.0`

V89D/V90/V92/V121AG remain hostile five-day comparators in the matrix; do not compare this one-day smoke directly to them or to the global reservoir.

## 4. Dirty Files And Active Changes

Active checkpoint files include:
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260706.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/ACTIVE_SESSION_STATE.json`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- FTMO export/availability scripts and tests
- route verifier/bridge/comparator files and tests from B4/B5 proof precision work

The tree also contains unrelated older route dirt and historical deletions. Stage only scoped files after verification.

## 5. Subagent Findings

- Huygens: incorporated. Bridge/Colima liveness classified; bridge recovered without broad restart.
- Rawls: incorporated. V122E/V122H command semantics verified.
- Avicenna: incorporated. Export/resolver proof, lazy hash validation, actual first/last coverage labeling, and targeted-scope warnings were patched into the B4 flow.

## 6. Mismatch Classes

- Source-bound -> candidate: not the active B4 target; V122H preserved `6369` candidates and `96` scorecards versus V122E.
- Candidate -> selector: B1/B3 truth closed for current stack; V122H still has many rejects and reduced-risk rows but no missing ladder.
- Selector -> scheduler: B2 route-resolution/priority context closed; remaining issue is not raw/effective collapse.
- Scheduler -> risk: ladder provenance is present; V122H trades split full/reduced `3/7` and orders `6/20/3` full/reduced/diagnostic.
- Risk -> order: finalizer probes exist but reallocation selected rows remain `0`; classify after B4 source-realism blockers.
- Order -> lifecycle/fill: V122H proves tick/source-safe fills execute; remaining source realism blockers are missed `m15_proxy`, `source_gap`, and `not_filled` rows.
- Fill -> exit: V122H is slightly positive but stress-fragile. Exit tuning waits unless B4 classification shows a truth violation.
- Ledger/verifier: V122H has zero executed REFUSED/source-gap rows, zero live/final rows, zero missing ladder rows, zero executable M15/first-touch optimistic rows.

## 7. Fixed / Partial / Open

Fixed in this checkpoint:
- Lazy tick hash validation moved to overlapping-window query and reports validation events.
- Tick SourceSpec coverage uses actual manifest first/last tick.
- Targeted FTMO ordered tick export bound to resolver and V122H replay.
- Matrix now marks V122H as completed bounded B4 evidence.

Partial/open:
- Full 24-symbol tick surface not proven.
- Hostile five-day fill-realism proof not run.
- V122H missed rows still dominated by cost-refused diagnostics and source-realism classes.
- B6 broker-cost calibration remains open after B4 classification.

## 8. Highest-Leverage Same-Root Batch Next

Continue B4. Build a source-realism blocker classification from V122H ledgers before another replay:
- `m15_proxy`, `source_gap`, `not_filled`, `ordered_tick_entry_touch`, `source_safe_immediate_marketable` missed rows;
- symbol/session/source/order policy/action/risk tier;
- positive and negative missed R;
- exact source requirement or routing reason.

## 9. Files/Components Affected

Likely files for next B4 classification/repair:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- route analyzer/comparator scripts under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`
- MT5 export/availability scripts if missing tick hydration is proven.

## 10. Patch Types

- Current V122H source-truth edits: correctness + performance repair.
- Matrix/root-map updates: diagnostic/control surface.
- Next B4 classification: diagnostic first; code/config repair only if it exposes routing/source-binding miswire.

## 11. Expected Effects Before Next Replay

No broad replay should run until classification selects the next source/fillability repair or source hydration target.

If the next B4 classification patch is purely diagnostic, expected behavior is neutral. If it fixes routing or hydrates missing ordered ticks, expected measurable effects are:
- candidate -> scorecard: unchanged unless source binding changes scoring;
- scorecard -> order: diagnostic rows may become terminal orders only when ordered source authority exists;
- order -> fill: source-safe or ordered tick fills may rise; M15 proxy executable rows must remain `0`;
- missed positive/negative R: reclassified by exact source/fill reason;
- trade count/R/W-L-F: can move either direction, must be attributed;
- cost-refused/source-gap execution: must remain `0`;
- risk full/reduced distribution: must stay explicitly split.

## 12. Success / Failure Criteria

Helped: classification identifies exact B4 blocker classes and either patches a source-binding miswire or proves the next ordered tick hydration target.

Failed: classification cannot explain why ordered source exists but rows stay diagnostic, or any patch makes M15 proxy/source-gap/first-touch optimistic rows executable.

Next deeper flaw exposed: if source realism is clean but missed positive R remains blocked, move to B6 cost calibration or risk-finalizer reallocation according to the classified rows, not by broad replay guessing.

## 13. V122H B4 Blocker Classification Update

Generated: 2026-07-06T05:28:04Z

Artifacts:
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_B4_SOURCE_REALISM_BLOCKER_CLASSIFICATION.json`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH_B4_SOURCE_REALISM_BLOCKER_BUCKET_LEDGER.jsonl`
- classifier: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/classify_b4_source_realism_blockers.py`
- test: `tests/test_classify_b4_source_realism_blockers.py`

Key result:
- B6 cost refusal/cost authority: `4870` rows, `423` scoreable, `-264.70564042R`, positive `+62.42658513R`, negative `-327.13222555R`.
- B2/B3 scheduler/risk/admission: `133` rows, `-26.27521669R`.
- B4 order geometry guard: `106` rows, `-17.82874179R`.
- B4 source-realism/missing ordered source: `696` rows, `0` scoreable opportunity R.
- Separate non-executable proxy mark for B4 source/missing-source: `48` rows, `-0.0166692602R`, positive `+8.6301837482R`, negative `-8.6468530084R`.
- `m15_proxy` proxy mark: `94` rows, `-10.4640443244R`.

Decision:
- Do not promote proxy/M15/source-gap rows to executable fills.
- B4 has a focused pass plus classification, but hostile five-day fill-realism proof remains open before B4 can close.
- After B4 hostile proof is labeled, proceed to B6 cost calibration because cost refusal is the largest remaining scoreable blocker in V122H.
