# Pre-Replay Brief - 2026-07-03T07:58Z

Scope: denominator-to-deployment ultimate-system replay repair in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full across the 82-sleeve surface. This brief replaces the stale V96-era `PRE_REPLAY_BRIEF_20260703T0425Z.md` for the next patch/replay decision.

## 1. Latest Completed Replay Prefix And Numbers

Latest hostile/stress fullgrid replay:

`BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- candidate rows: `25,006`
- scorecards: `288`
- order rows/events: `196`
- filled trades: `47`
- missed rows: `24,908`
- net R: `+13.89627731`
- gross/final R: `+18.23890670`
- cash PnL: `+4461.09800786`
- risk cash / risk %: `9323.67032756` / `9.02307118`
- W/L/F: `23/24/0`
- expired unfilled: `51`
- missed scoreable rows: `7,500`
- missed positive/negative R: `+2059.22271586` / `-9738.85318535`
- missed total scoreable R: `-7679.63046949`
- stress: extra `0.05R` cost `+11.54627731`, `0.10R` `+9.19627731`, `0.20R` `+4.49627731`
- Monte Carlo: p50 max drawdown `-6.14520864R`, worst `-13.84042328R`

Latest non-May objective regime replay:

`BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`

- candidate rows: `35,191`
- scorecards: `480`
- order rows/events: `266`
- filled trades: `62`
- missed rows: `35,058`
- net R: `+2.21033496`
- gross/final R: `+7.10115419`
- cash PnL: `+1181.09009638`
- risk cash / risk %: `11012.25625692` / `11.07042294`
- W/L/F: `28/34/0`
- expired unfilled: `68`
- missed scoreable rows: `10,166`
- missed positive/negative R: `+3325.59256409` / `-12264.37976845`
- missed total scoreable R: `-8938.78720436`
- stress: extra `0.05R` cost `-0.88966504`, `0.10R` `-3.98966504`, `0.20R` `-10.18966504`
- Monte Carlo: p50 max drawdown `-8.66649152R`, worst `-18.03107044R`

## 2. Currently Running Replay

No broad replay is running. Current matching processes are Context OS sidecars only.

Decision: do not start another broad replay before patching the grouped scheduler/finalizer materialization-action contract. The next proof should be targeted to the same two five-day buckets unless the code patch is purely verifier/local.

## 3. Baseline Comparison

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
|---|---|---:|---:|---:|---:|---:|
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V97 | 2026-05-13..17 | 47 | +13.89627731 | +18.23890670 | +4461.09800786 | 23/24/0 |
| V97 | 2026-06-01..05 | 62 | +2.21033496 | +7.10115419 | +1181.09009638 | 28/34/0 |

Same-window V92 vs V97:

- trade delta: `-4`
- net R delta: `-15.45942505`
- gross/final R delta: `-15.69322190`
- cash PnL delta: `-1767.53295236`
- W/L delta: wins `-14`, losses `+10`
- expired unfilled delta: `-11`
- candidate axes: `894 -> 894` (`0`)
- scorecard/order axes: `39 -> 29` (`-10`)
- filled axes: `25 -> 18` (`-7`)
- actual executable R inside replay window: `+17.76833767 -> +13.48984606` (`-4.27849161`)
- added trades: `19`, `+0.99594545R`, `8W/11L`
- removed trades: `23`, `+13.53876156R`, `19W/4L`
- interpretation: added transfers are net positive but weak; removed transfers were strongly positive. V97 regressed because action/rank/materialization churn removed better transfers and admitted weaker stop-first paths.

Denominator boundary: do not compare these five-day replays directly to the full `1,249,248R` source-bound reservoir. Exact replay-window source-bound R is `222,423.262022048R` for V97 hostile and `260,850.564292173R` for V97 non-May. This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## 4. Dirty Files And Active Code Changes

Current dirty tree includes route/context work, source/config/test changes, large replay artifacts, and unrelated tracked historical science JSONL deletions. Do not revert user/other-agent changes and do not stage unrelated dirt.

Active files for the next patch batch:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- route verifier/summary files only if the repair changes required ledger assertions

## 5. Subagent Findings

- Raman: incorporated. Supplied V92 same-window baseline fields.
- Hegel: incorporated. Confirmed V97 comparator should disable only passive-limit fallback-envelope flags, not the older passive-limit-too-close guard.
- Jason: incorporated. Recommended `2026-06-01..05` as the first non-May objective bucket; it was run and parsed.
- Arendt: incorporated. Candidate supply is not the leak. Transfer fails at risk/finalizer materialization; scorecard/order axes drop `39 -> 29`, filled axes `25 -> 18`, and removed V92 trades are strongly positive.
- Lovelace the 2nd: running. Scheduler/finalizer materialization-action contract code audit.
- Avicenna the 2nd: running. Added/removed trade ledger field audit.
- Plato the 2nd: running. Exit/stop geometry damage audit.

## 6. Known Mismatch Classes

- source-bound -> candidate: partially fixed, not current choke. V92 and V97 both generate `894/1101` axes in the hostile window.
- candidate -> selector: partially fixed. Selector action labels changed, but reject count is stable and does not explain the axis loss alone.
- selector -> scheduler: open. V97 admits weak added transfers and loses stronger V92 transfers.
- scheduler -> risk: primary open mismatch. Risk/finalizer materialized rows drop while causal quality gate blocks rise.
- risk -> order: partially fixed. Executed broker-cost REFUSED/source-gap rows are zero and must remain zero.
- order -> lifecycle -> fill: open downstream. Expired unfilled remains material (`51` hostile, `68` non-May), but V97 got worse despite fewer hostile expiries than V92.
- fill -> exit: open downstream. Stop-first losses dominate (`23/47` hostile, `27/62` non-May).
- ledger truth: partially fixed. Exact selected-window denominator exists; missed ledgers are large and require streaming aggregation.

## 7. Fixed, Partial, Open, Newly Exposed

Fixed:

- broker/live/final closed while local replay has full package authority;
- broker-calibrated cost authority primary, candidate cost proxy fallback diagnostic only;
- cost-refused/source-gap rows non-executable but scoreable as missed opportunities;
- exact selected-window denominator prevents invalid full-reservoir comparisons.

Partially fixed:

- package action scope truth is now active, but it changed materialization behavior and exposed weak ranking/action replacement.
- missed opportunity is scored, but opening all missed rows would be wrong because scoreable missed opportunity is net negative in both five-day windows.

Open/newly exposed:

- V97 materialization churn removed strong V92 winners and admitted weak additions.
- Causal quality/marketable-limit veto reasons may be hiding action-contract mismatches.
- `same_direction_scale_in` may be ranked/materialized without valid same-side exposure or may fail to fall back cleanly to new-position authority.
- Stop-first exit damage is severe but may be downstream of bad materialization.

## 8. Highest-Leverage Same-Root Batch

`scheduler_finalizer_materialization_action_contract_repair_v98`

The candidate reservoir reaches replay. The current leak is not supply; it is conversion quality from candidate/selector into scheduler/risk materialized orders.

## 9. Exact Files / Components Affected

- Scheduler option construction, action resolution, score/rank, lifecycle root authority, and package marketable guard in `src/research/moonshot_scheduler_v4_best_trade_allocator.py`.
- Finalizer selection, candidate probe ranking, causal quality gate, reallocation after veto/skip, and risk-authority provenance in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
- Tests listed in section 4.

## 10. Patch Classification

- action-contract and scale-in exposure validation: correctness repair.
- finalizer reallocation/ranking after veto/skip: correctness plus performance repair.
- marketable-limit guard reason split: correctness plus diagnostic repair.
- exit/stop geometry change: deferred until evidence proves it is not only downstream of materialization quality.

## 11. Expected Measurable Effect Before Replay

- candidate -> scorecard transfer: candidate axes stay near `894`; scorecard/order axes recover toward V92 `39` without cost-refused execution.
- scorecard -> order transfer: order-present count recovers through executable package rows only.
- order -> fill transfer: filled axes recover toward V92 `25` if removed winners are restored.
- missed positive R: high-quality materialization-veto/competing-candidate positives fall.
- missed negative R: the large negative cost-refused/not-risk-bearing reservoir stays non-executable.
- trade count: may rise or churn, but added-minus-removed transfer must be net favorable.
- net/gross/final R: hostile V98 should recover a material part of the V92->V97 `-15.459R` regression or expose a narrower downstream blocker.
- W/L/F: must not improve only by suppressing opportunity.
- cost-refused/source-gap execution: must remain `0`.
- risk-reduced/full-risk distribution: materialized/rejected rows must retain provenance and explain risk sizing decisions.

## 12. Proof Criteria

Helped:

- focused tests pass;
- V98 hostile replay restores some removed V92 positive transfers or removes weak V97 additions for causal predecision reasons;
- added transfers are net positive and removed transfers are not strongly positive;
- cost-refused/source-gap execution remains zero;
- June 1-5 result improves or identifies the next regime-specific blocker.

Failed:

- scorecard/order axes stay at `29` or fall;
- V97 weak additions remain while strong V92 removed winners remain absent;
- improvement comes only from suppressing trades;
- cost-refused/source-gap rows execute.

Exposes next flaw:

- materialization transfer improves but stop-first losses remain dominant. Then patch exit/stop geometry with targeted bucket proof before broad historical replay.
