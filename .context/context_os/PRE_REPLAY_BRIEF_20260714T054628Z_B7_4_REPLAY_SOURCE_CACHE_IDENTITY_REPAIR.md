# B7.4 Replay Source-Cache Identity Repair Pre-Replay Brief

Generated UTC: 2026-07-14T05:46:28Z.

## Decision

Run V257 over the exact V250 June 1-5 denominator with all 24 symbols and
one-day chunks. V256 is a completed semantic failure, not accepted behavior:
its static source plan was invariant, but a process-global closed-bar cache
could return another symbol's candles after source release, GC, and Python
object-ID reuse. The whole persistent identity-cache chain is now repaired and
the mechanism passes synthetic, full-module, and real-data lifecycle proof.

No selector, scheduler, risk, cost, order, lifecycle, fill, or exit policy was
tuned. This is a correctness repair and must reproduce V250 rather than create
a new economic result.

## Process State And Latest Run

- No replay, builder, verifier, pytest, or git-maintenance process is active.
- Latest completed run is V256:
  `BROAD_LIVE_AS_IF_REPLAY_V256_B7_4_SOURCE_AUTHORITY_CHUNK_INVARIANCE_V250_COMPARATOR_20260601_20260605_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID`.
- V256 exited zero and completed five cleanup checkpoints, but is rejected for
  semantic chunk invariance.
- V256 counts: 29,985 candidates, 480 scorecards, 54 order events, 26 terminal
  orders, 25 physical trades, and 29,959 missed rows.
- V256 headline: 3 trades, 2/1/0, +0.95532938R gross/final,
  +0.70378422R net, -$155.93195154 cash, 1.10% summed risk.
- V256 all physical rows are 25 trades, 16/9/0, +20.39431097R gross/final,
  +19.39063467R net, but -$317.39307229 cash. The 22 diagnostic fills and
  their R are invalid as behavioral evidence because their candidate inputs
  were contaminated.
- V256 stress remains positive through +0.20R per headline trade
  (+0.10378422R); this does not rescue the invalid input surface.

## Baselines

- V250 same-window current-truth baseline: 35,191 candidates, 480 scorecards,
  30 order events, 14 terminal orders, 13 physical trades, 8/5/0 physical,
  +7.82542991R gross/final, +7.03578717R physical net, -$68.02401535 physical
  cash. Headline is 4 trades, 3/1/0, +1.92353135R gross/final,
  +1.59506223R net, -$67.96685163 cash.
- V256 versus V250 candidate identity: 24,879 common, 10,312 V250-only,
  5,106 V256-only. Order identities overlap on 12/16 V250 ordered candidates;
  trade identities overlap on 9/13 V250 fills.
- V89D `56/+34.84520454R`, V90 `51/+28.84201157R`, and V92
  `51/+29.35570236R` remain historical hostile-window comparators. They are
  not the June 1-5 denominator and are not V257 acceptance targets.

## Dirty And Coordination State

Route-owned implementation/test changes:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_denominator_to_deployment_verifier.py`

Current control artifacts include this brief, the root-cause map, continuation
cursor, Fable matrix, and the V256 retention manifest. The 82-row sleeve and
1,101-row member fixtures were explicitly hydrated into the sparse worktree.
No subagent is active or unreconciled; all prior returns retain their recorded
incorporated/rejected/deferred dispositions.

## Root-Cause Map

| Stage | State |
| --- | --- |
| source-bound -> static source plan | GREEN: all five V256 chunks used one valid 24-symbol plan digest. |
| static source -> replay candle adapter | FIXED / V257 PROOF OPEN: `_CLOSED_BAR_INDEX_CACHE` did not retain or validate its source tuple. Reused tuple IDs returned cross-symbol candle indexes. |
| tick cost source -> predecision query | FIXED / REGRESSION PROVED: the same unsafe identity pattern existed in `_PREDECISION_TICK_QUERY_CACHE`; values now retain and validate the exact `ResolvedSource`. |
| selected bridge config/candle fast paths | FIXED / REGRESSION PROVED: both closure caches now retain and validate their exact config/row source. |
| candidate -> selector -> scheduler | DOWNSTREAM V256 INVALID: 10,312 removed and 5,106 invented candidate identities changed ranking and selection. No policy defect can be inferred from V256. |
| risk -> order -> lifecycle -> fill -> exit | DOWNSTREAM V256 INVALID: 12 extra physical fills and changed risk allocation arose from contaminated candidates. Existing policy remains unchanged. |
| ledger/capacity proof | FIXED / V257 PROOF OPEN: capacity contract v1 ignored global row/tick caches. v2 requires exact before/after counts, zero remainder, and verifier enforcement on every chunk. |

## Same-Root Repair Batch

Correctness repairs:

- closed-bar cache retains and validates the source tuple;
- non-tuple iterables are not persisted in the identity cache;
- predecision tick cache retains and validates the source object;
- selected bridge symbol-config and candle-index caches retain and validate
  their source objects.

Capacity/proof repairs:

- one `clear_replay_source_caches()` boundary clears closed-bar, row-time, and
  predecision-tick caches before explicit GC;
- `BroadSourceResolver.release_completed_chunk_caches()` records before/after
  counts and zero remainder;
- capacity contract schema v2 and the route verifier require all source-derived
  caches to be empty after every chunk.

Focused proof is green: compile passed; 624 B7.4 harness/package/parity/verifier
tests passed; 820 complete timewarp tests passed. A real-data probe hydrated all
24 symbols, exercised 96 June 1 decision windows, observed 96 closed-bar cache
entries before release and zero after, rebuilt June 2, and matched uncached
JP225/USDCAD D1/H4/H1/M15 payloads on all 8 checks. USDCAD H1 remained
1.38407 instead of taking another symbol's price scale.

## Expected V257 Effect

- Candidate -> scorecard: exactly 35,191 -> 480.
- Per-day candidate counts: 7,244 / 7,175 / 6,603 / 6,981 / 7,188.
- Candidate identities: 35,191 common with V250; zero added/removed.
- Scorecard -> order -> fill: 30 events, 14 terminal orders, 13 fills with
  exact V250 candidate/order/trade identities and values.
- Missed rows: 35,177 with exact V250 identity and accounting.
- Physical result: 13 trades, 8/5/0, +7.82542991R gross/final,
  +7.03578717R net, -$68.02401535 cash.
- Headline result: 4 trades, 3/1/0, +1.92353135R gross/final,
  +1.59506223R net, -$67.96685163 cash.
- Risk expression: 2 full-risk and 11 reduced-risk physical fills.
- Executed broker-cost REFUSED/source-gap/unsigned rows: 0/0/0.
- Every chunk: replay source-cache remainder 0 under capacity contract v2.

## Success And Failure

Helped and closed means exact V250 candidate, order, trade, missed, W/L/F, R,
cash, risk, headline/diagnostic, and safety identity/value equivalence, plus five
valid v2 cache cleanup checkpoints.

Failed means any candidate identity drift or any nonzero replay source-cache
remainder. If candidates are exact but order/trade behavior differs, the next
deeper blocker is persistent broker/account/scheduler campaign state rather
than source authority. Do not tune policy until that boundary is isolated.

This comparator cannot improve by suppression because its acceptance target is
exact V250 opportunity and behavior restoration. It is a bounded five-day code
truth proof, not total-reservoir conversion or final/live authority. Full 82-
sleeve replay authority remains active; broker/live/final remain false.
