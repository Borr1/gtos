# B7.5 Cross-Window Truth And Lifecycle Pre-Replay Brief

Generated: 2026-07-15T21:15:59Z.

This is the durable B7.5 execution and closure brief. It began before the
cross-window and causal-risk replays and now records their completed evidence.
Section 26 is the current R3 closure; no replay is active or authorized before
canonical certification and the next separately sealed economic experiment.

## 1. Latest Completed Replay

Current latest completed prefix:

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3`

The June 4 full 24-symbol reconciliation completed under shared execution
digest
`163329e9cf863e812db626f99d53469172f95b1512e49457eb0b3841464d9b67`
and tick-enriched source-plan digest
`a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001`.

- candidates / scorecards / order events / terminal orders / physical fills:
  `6981 / 96 / 12 / 6 / 6`;
- missed rows: `6975`;
- physical scoreable / unscoreable: `5 / 1`;
- physical W/L/F and net/gross/final R: `4/1/0`,
  `+4.03591467 / +4.43627912 / +4.43627912R`;
- physical cash / risk cash / risk percent:
  `+$2204.18020365 / $3027.86901650 / 3.00%`;
- headline W/L/F and net/gross/final R: `3/1/0`,
  `+2.12544422 / +2.43627912 / +2.43627912R`;
- headline cash: `+$992.62016070`;
- executed broker-cost REFUSED / source-gap rows: `0 / 0`;
- full/reduced physical fills: `0 / 6`;
- flow terminal-R sources: four ordered-tick and two ordered-M1, with one of
  the M1 rows terminal-unscoreable.
- canonical pre-risk quality source maps: `96 / 96` scorecards; R1 carried
  only `7 / 96` and failed R2 also carried `7 / 96`.

## 2. Process State

No replay is active. R3 exited `0`, its parity/flow/comparison/proof consumers
are materialized, and direct quality-source, cost, physical-summary,
stop-hazard, order-transfer, and selected-policy scans have `bad_counts={}`.
R3 is the only current replay authority. R2 remains failed serialization
evidence and R1 remains its exact behavioral comparator; neither is to be
rerun.

## 3. Baseline Comparison

- V89D / V90 / V92 are historical May 13-17 comparators only: `56 / 51 / 51`
  trades and `+34.84520454 / +28.84201157 / +29.35570236R`. They are not B7.5
  denominators and are not config-identical.
- V249 May hostile proof: 20 physical fills at `+1.16150430R`; 18 headline
  fills at `+0.28044419R`.
- V258 June broad proof: 42 physical fills at `+15.08858577R`; four headline
  fills at `+1.59506223R`.
- January R4: 61 physical fills, `24/37/0`, `-2.76396743R`; four headline
  fills, `3/1/0`, `+0.98832036R`.
- January plus April: 117 physical fills, `47/70/0`, `-4.81212578R`; ten
  headline fills, `5/5/0`, `-1.56722011R`.

The January/April cross-window proof is truth-green and economically failed.
It does not prove full-reservoir conversion or justify date/symbol/session
outcome filters.

## 4. Current Dirty Scope

Active route-owned changes:

- `analyze_b7_5_extended_history_behavior.py`;
- `B7_5_EXTENDED_HISTORY_BEHAVIOR_SUMMARY.json`;
- `B7_5_EXTENDED_HISTORY_BEHAVIOR_DOSSIER.md`;
- `build_denominator_to_deployment_execution.py`;
- `verify_denominator_to_deployment_execution.py`;
- `tests/test_analyze_b7_5_extended_history_behavior.py`;
- this brief, current root-cause map, continuation cursor, and Fable matrix.

The route builder has pre-existing generated-ledger dirt. It is not evidence of
the next behavior repair and will not be staged indiscriminately.

## 5. Frozen Audit Reconciliation

- Risk/cap audit: `VALID_OPEN`. Current code still sets
  `pressure_requires_base_fragility=false`. January/April/June all show zero
  base-fragile capped fills; the cap is pressure-only and changes ranking,
  budget, order size, and cash. No blanket full-risk promotion is allowed.
- Proof/parity audit: `PARTIAL_CURRENT_FIX`. The source-window contract is now
  bound to the R4 digest, but exact replay-window parity still sums explicitly
  non-additive member-axis signal values and emits an invalid executable-R
  percentage. Row-ledger hashes and unit-separated cross-window proof remain
  open.
- Exit audit: `DEFERRED`. Fixed profit harvest improves April/May/June but
  harms January. It is a valid default-off challenger, not selected authority.
  Raw-fixed replacement is rejected because its sign flips by window.
- Lifecycle audit: `VALID_OPEN`. Twenty-two selected April order intents are
  suppressed by later terminal-path uncertainty. Current source-bound path
  reconstruction classifies fifteen as executable entry fills (ten passive
  queue-confirmed and five explicitly authorized immediate-marketable entries)
  and seven as pending then expiry (one queue-realism failure and six untouched
  entries) unless causal same-symbol replacement changes the fresh partition.
  Suppression also hides same-symbol exposure and admitted risk.
- Selector/scheduler audit: `RUNNING_FROZEN_SNAPSHOT`. Reconcile once returned;
  do not block the truth batch or implement an unconfirmed claim.

## 6. Root Mismatch Map

| Stage | Status | Current evidence |
| --- | --- | --- |
| source-bound | PARTIAL | 82 sleeves and 1101 axes preserved; source-window presence is 711/390 January and 707/394 April, but signal R is non-additive. |
| candidate | PARTIAL | 990/981 axes generate candidates; exact package-candidate instance match remains unavailable in the compact parity projection. |
| selector | FIXED/UNDER AUDIT | Raw/effective action and quality provenance are preserved; frozen causal comparison still running. |
| scheduler | PARTIAL | Reallocation exists; pressure-only risk cap changes ranking and one April replacement. |
| risk | OPEN | Cap enforcement is correct, but the pressure predicate is non-discriminative and nearly universal. |
| order | OPEN | Selected intent is conflated with later terminal scoreability for 22 April instances. |
| lifecycle | OPEN | Missing intent/pending/fill state hides risk reservation, expiry, and same-symbol conflicts. |
| fill | OPEN | Entry-fill authority is incorrectly discarded when terminal ordered-tick R is unresolved. |
| exit | PARTIAL | Momentum exhaustion and PH challenger have mixed cross-window deltas; no policy promotion yet. |
| ledger/proof | OPEN | Non-additive source R is mislabeled as a denominator; row/event/instance/axis units and post-run pair hashes need exact binding. |

## 7. Fixed, Partial, Open

Fixed and preserved:

- full 82-sleeve/1101-axis scoring;
- immutable candidate/action/risk/order provenance;
- broker-calibrated cost authority;
- zero executed REFUSED/source-gap rows;
- compact candidate and terminal-blocker truth repairs;
- January and April source/config digest binding in replay summaries;
- deterministic four-window behavior analyzer and focused verifier tests.

Partial or open:

- non-additive source-transfer semantics and post-run pair binding;
- candidate-instance-to-source-axis exact materialization proof;
- selected-intent / entry-fill / terminal-R authority separation;
- same-symbol and risk-budget consequences of suppressed pending state;
- pressure-only stop-hazard cap discrimination;
- cross-window exit challenger selection;
- B7 economic generalization, B8 shadow/canary, final/live authority.

## 8. Next Same-Root Batches

### Batch A: B7.5 cross-window transfer truth

Files/components:

- `build_source_bound_execution_parity.py`;
- `analyze_b7_5_extended_history_behavior.py`;
- `build_b7_5_extended_history_source_window_contract.py` if the source
  disposition needs an explicit non-additive field;
- route builder, verifier, manifest, and focused tests.

Classification: correctness and proof-consumer repair. Behavior-neutral.

Required result:

- source-window presence and non-additive diagnostic signal R are distinct from
  executable R;
- no executable-R/source-R percentage is emitted when additive authority is
  false;
- January/April summaries bind the current pair contract and artifact hashes;
- candidate, scorecard row, order event, order instance, terminal order,
  physical fill, headline fill, and axis units remain separately named;
- all four windows remain broker/live/final false.

### Batch B: selected-intent, entry-fill, terminal-R lifecycle separation

Files/components:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`;
- same-symbol/lifecycle consumers if current code proves they need adaptation;
- focused runtime and route-verifier tests.

Classification: executable correctness repair with behavior impact.

Required result:

- every selected order intent enters exactly one materialized lifecycle
  partition;
- independently valid immediate/passive entry fills survive unresolved terminal
  R, while terminal/headline R remains unscoreable;
- unresolved entry paths become pending and expire or replace causally;
- accepted risk is reserved and released exactly once;
- same-symbol decisions see the real pending/open state;
- cost refusal, source-gap, and signed-authority constraints remain intact.

## 9. Expected Effects Before Replay

Batch A must not change candidate, scorecard, order, fill, trade, risk, or R
behavior. Any behavioral delta fails the batch.

Batch B expectations are structural, not outcome-fit:

- candidate-to-scorecard transfer: unchanged unless corrected same-symbol state
  causally changes later scheduler materialization;
- scorecard-to-order intent: all selected instances are explicitly partitioned;
- order-to-entry fill: 15 April diagnostic instances retain independent entry
  truth; seven unresolved entry paths enter pending/expiry handling;
- missed positive/negative R: terminal R stays diagnostic/unscoreable without
  ordered-tick authority;
- trade/headline R: no promotion from M1 terminal outcomes;
- risk: reservations and releases become nonzero for the repaired lifecycle;
- REFUSED/source-gap execution: remains zero;
- full/reduced distribution: retains signed selector and dynamic-budget
  authority; no blanket promotion.

## 10. Proof Criteria

Batch A helps only if focused tests and canonical verifier prove the corrected
non-additive semantics, pair binding, hashes, and unit reconciliation with zero
behavior change. It fails on any stale hash, invalid percentage, missing window,
or broker/live/final leakage.

Batch B first uses focused sequence tests and the smallest targeted April
bucket containing the proven parent/child overlaps. It helps only if lifecycle,
risk, and same-symbol state become causal while terminal/headline authority
remains honest. It fails if unresolved terminal paths produce headline R,
cost/source failures execute, risk is double-counted, or opportunity is merely
suppressed. A broader January/April proof follows only after targeted success.

This smoke proves or disproves the local repair; it does not prove total
reservoir conversion.

## 11. Batch A Closure And Batch B Selection - 2026-07-15T22:04:01Z

Batch A is DONE and behavior-neutral. The source-window contract, paired replay
summaries, analyzer, and verifier now separate immutable behavioral execution
authority from mutable post-run parity/verifier authority. January and April
share behavioral digest `84e6de36...35c3249`; their replay-time legacy full
digest remains `44a8c046...c8c27`. Current source-window and proof-consumer
digests are independently hash-bound. Non-additive member-axis signal is not an
executable-R denominator, no percentage is emitted, and row/event/instance/axis
units remain explicit.

Focused proof: compile passed; 12 builder/analyzer tests and the exact real
source-contract verifier test passed; direct source-contract and behavior
verifier issue lists are empty; scoped diff check passed. No replay ran and no
candidate, order, fill, risk, or economic row changed. Cross-window economics
remain physical `117`, `47/70/0`, `-4.81212578R` and headline `10`, `5/5/0`,
`-1.56722011R`.

Batch B is selected next. It must separate `order_intent_materialized`,
`entry_fill_executable`, and `terminal_r_scoreable` across runtime state,
risk reservation/release, same-symbol lifecycle, ledgers, and verifier. The
smallest April parent/child overlap proof is required before any broad replay.

## 12. Batch B Implementation Barrier And Targeted Proof - 2026-07-15

The same-root implementation batch now separates order intent, executable entry
fill, and terminal-R scoreability across ordered-path inference, pending/open
account state, accepted-risk reservation, order/trade ledgers, summary/flow/
comparison consumers, and the canonical verifier. Pending snapshots strip
postdecision fill, queue, terminal, exit, and R fields before later scheduler or
same-symbol decisions consume them. Executed entries with missing ordered-tick
terminal sequence close exposure as unscoreable without balance/PnL mutation;
expired orders release their reservation, while filled entries consume rather
than release the accepted daily risk budget.

Focused proof is green: Python compilation passed; runtime/microstructure tests
passed `849`; harness/flow/comparator/history tests passed `206`; verifier tests
passed `334`; total affected tests passed `1389`. The only warning is the
pre-existing unknown `pytest-asyncio` configuration option.

The smallest causal replay target is XAUUSD on `2026-04-10`, repaired profile,
full candidate surface for that symbol/day, no candidate cap. The prior April
R4 ledger contains one existing 07:15 queue-confirmed fill, a 09:15/09:30
same-candidate parent/child pair previously suppressed as diagnostics, and a
14:30 opposite-side immediate-marketable entry previously suppressed by
terminal sequence uncertainty.

Target prefix:

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_10_ENTRY_FILL_TERMINAL_LIFECYCLE_TARGETED_R1`

Success requires exactly one pending and one terminal order event for every
materialized intent; no selected signed cost-passed intent suppressed solely by
terminal-R uncertainty; independently valid fills retained; untouched or
queue-failed entries expired/replaced causally; terminal-unscoreable trades
closed with null generic R/PnL and excluded from headline/stress/MC; accepted
risk consumed on fill or released once on expiry; causal pending/open state
visible to later same-symbol decisions; and zero executed REFUSED/source-gap
cost rows. A changed selected-intent count is not itself failure when caused by
the newly truthful pending/open state. This targeted smoke proves or disproves
the local lifecycle repair; it does not prove total reservoir conversion.

## 13. Batch B Targeted Closure - 2026-07-16

The final targeted proof prefix is:

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_10_ENTRY_FILL_TERMINAL_LIFECYCLE_TARGETED_R5`

It completed under current shared execution digest
`cb862b32d4b386b51598506c82ee4fae34f55653d643ecfa7ca7c06258de3e3a`
and unchanged targeted source-plan digest
`0030f7239c869ca2352b55594c5ba2473e723f7c3653ff440fe7142ad6e37be0`.

- decisions / candidates / scorecards / order events / terminal orders / fills:
  `2208 / 248 / 92 / 6 / 3 / 3`;
- missed rows: `245`, of which `38` have diagnostic opportunity R and `207`
  remain path-auditable but R-unscoreable;
- diagnostic missed positive / negative / net R:
  `+23.14442178 / -18.18443444 / +4.95998734R`;
- physical scoreable / terminal-unscoreable fills: `1 / 2`;
- physical W/L/F and net/gross/final R: `0/1/0`,
  `-1.10438795 / -1.0 / -1.0R`;
- physical cash / risk cash / risk percent:
  `-$690.24246875 / $1717.40733284 / 1.725%`;
- full/reduced fills: `1 / 2`;
- raw expected cost / summed row execution-cost authority:
  `0.24378323 / 0.24378324R`;
- ordered-tick headline fills and R: `0 / 0.0R`;
- executed broker-cost REFUSED / source-gap rows: `0 / 0`.

R5 is identity-neutral to R2: candidates `248/248`, scorecards `92/92`, order
events `6/6`, trades `3/3`, and missed rows `245/245`, with zero added or
removed trade identities. The truth repair reclassifies two physical fills as
terminal-R-unscoreable instead of inventing scoreable outcomes. All three
accepted intents have exactly one pending and one filled terminal order event;
all fills consume accepted risk without releasing it. The canonical lifecycle
scan reports `bad_counts={}`.

The final focused barriers are green: runtime/microstructure `849`, route
harness/flow/comparator/history `206`, and verifier `335`, for `1390` affected
tests. Compilation passes. The only warning remains the pre-existing unknown
`pytest-asyncio` configuration option.

Disposition: the targeted selected-intent / entry-fill / terminal-R lifecycle
separation is DONE. It is a correctness proof, not a performance claim. This
smoke proves the local repair; it does not prove total reservoir conversion.

## 14. Full-April Lifecycle Proof Contract

The next behavior-changing proof is a full configured-symbol April regeneration
under the R5 lifecycle code, unchanged package policy, no candidate cap, compact
relational ledgers, and April source-plan digest
`4987d98cf023963305eb4d34f5940e59491fbac56a2683fb55816e8b5d8e46d2`.
Before launch, bind the fresh all-symbol shared execution digest and complete
the bounded storage checkpoint without deleting active route evidence.

The bound all-symbol shared execution digest is
`0f1299727da8126f467f85ccd45068ee09547ea5ca4cfcf3358eaf5372fda671`;
its contract is valid and has no missing code paths.

The successor must be compared to
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_TERMINAL_BLOCKER_STAGE_REPAIR_R4_RELATIONAL_COMPACT_FULLGRID`.
Success is not positivity by suppression. It requires:

- all R4 candidate and scorecard identities preserved unless truthful pending
  or open same-symbol state causally changes a later decision;
- every selected signed intent partitioned into pending then exactly one filled,
  expired, cancelled, or replaced terminal event;
- independently executable fills retained even when terminal R is unscoreable;
- terminal-unscoreable fills excluded from headline/stress/MC R while their
  physical risk and broker-calibrated costs remain reported;
- risk consumed on fill and released exactly once only on non-fill terminal
  disposition;
- zero executed REFUSED/source-gap rows;
- exact added/removed candidate, scorecard, order, fill, trade, and missed
  identities with causal reasons;
- full-risk/reduced-risk distribution and same-symbol/reallocation effects
  reported separately;
- canonical lifecycle, transfer, cost, provenance, route verifier, prompt audit,
  artifact audit, compile, tests, and scoped diff check green.

Failure is any fabricated terminal R, double risk release/consumption, hidden
opportunity loss, unexplained identity drift, or execution of a cost/source-gap
row. A negative full-April result does not invalidate this truth repair; it
selects the next causal policy batch from the corrected broad evidence.

## 15. Bounded Storage Checkpoint - 2026-07-16

No replay, test, verifier, or git-maintenance process was active during the
check. Current free space is `49.05 GiB`. The route's top-level artifacts occupy
`76.33 GiB`; the active April R4 comparator prefix occupies `13.31 GiB`, while
each April 10 targeted prefix is about `0.17 GiB`.

Required artifacts preserved for the next proof:

- April R4 summary, source, decision, scorecard, order, oracle, trade, missed,
  bucket, comparison, flow, parity, and candidate-instance projection surfaces;
- April 10 R2 baseline and R5 lifecycle proof artifacts;
- January/April source-window contract and bound source-plan digests;
- current runtime, microstructure, harness, analyzer, comparator, verifier,
  tests, root-cause map, cursor, Fable matrix, and this pre-replay brief.

No active evidence was deleted. A same-shape full-April successor and its proof
consumers fit within measured headroom, so storage is not the critical path.
Recheck free space after replay materialization and before route-wide builders.

## 16. Full-April R5 Result And Next Same-Root Batch - 2026-07-16

The full-April lifecycle successor completed; no replay is active. Final prefix:

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_ENTRY_FILL_TERMINAL_LIFECYCLE_REPAIR_R5_RELATIONAL_COMPACT_FULLGRID`

It materialized `67056` decisions, `135289` candidates, `1920` scorecards,
`148` order events, `74` terminal intents, `69` fills, `5` expiries, and
`135215` missed rows. Of the fills, `56` are terminal-R-scoreable and `13`
are entry-fill-executable but terminal-R-unscoreable. Scoreable behavior is
`22/34/0`, gross/final `+1.43286779R`, net `-2.33891543R`, and cash
`-$1779.57123999`. The six ordered-tick headline fills are `2/4/0` and
`-2.55554047R`. Executed broker-cost REFUSED/source-gap rows remain `0/0`.

The lifecycle repair is truth-green but not economically positive. Compared
with April R4 it added fifteen trade identities, removed two, and changed
scoreable net R by `-0.29075708R`. This proves the full-April lifecycle effect;
it does not prove full-reservoir conversion.

The selected next batch is
`B7_5_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_AND_FINAL_SUMMARY_TRUTH`:

- **Behavior correctness:** restore the scheduler's causal default that stop
  pressure can amplify only actual base fragility. April R5 capped `58/69`
  fills, but none had `unit_risk_atr < 0.35`; close entry, high fill
  probability, and a larger target are not independently a stop hazard.
- **Ledger correctness:** normalize terminal order/trade truth before summary
  accumulation. The serialized trade ledger reports `6/63` full/reduced rows,
  while the pre-normalized summary reports `4/65`.
- **Cost truth:** split scoreable physical expected cost (`3.77178321R`) from
  terminal-unscoreable fill expected cost (`0.96410350R`) instead of comparing the
  all-fill `4.73588671R` aggregate with scoreable-only net R.
- **Proof:** enforce causal cap semantics and exact final-summary/trade-ledger
  parity in focused tests and the route verifier.

Expected effects before replay: candidate generation is unchanged; pressure-
only non-fragile rows become eligible for their signed risk tier and scheduler
headroom, genuinely base-fragile rows remain capped, and REFUSED/source-gap
execution remains zero. Order/fill/trade counts may change through truthful
risk-budget and reallocation effects. Improvement is not accepted if it comes
from suppressing opportunity.

The first behavioral proof after focused tests is a paired targeted replay on
one hostile and one non-hostile day containing existing pressure-capped rows.
It helps if causal risk authority changes only the non-fragile cohort, summary
and ledger agree exactly, and executable value improves without cost/source
authority leakage. It fails if base-fragile rows are promoted, risk provenance
is lost, or the result improves only by blocking trades. No broad replay runs
until that targeted contract is green.

## 17. Causal Risk-Expression Targeted Proof Binding

Focused scheduler, runtime, harness/finalizer, and verifier proof passes
`16/16`. The reconciled April R5 summary now exactly matches its final trade
ledger: `6/63` full/reduced fills, scoreable/unscoreable expected costs
`3.77178321/0.96410350R`, all-fill expected cost `4.73588671R`, and physical
summary parity `bad_counts={}`. The historical R5 scan records `58` pressure-
only non-base-fragile capped trades and no malformed cap execution.

Both target runs bind unchanged code/config digest
`0ea02453988e18921f880d9227c736471a1dd3e78209560b1da7a6d83af7dc10`
and repaired profile hash
`fb84f087043ac89461be0ef592528eb49bd3ef3e12b775b75ebb94e11f81f67a`.

- Hostile target `2026-05-15`, source plan
  `1c6cdfa3c4f53c4aa81b0f0d1940c4baa403a0cad0d40d339a4f9c57aa107332`.
  The prior window had four pressure-capped rows; the cap protected about
  `$1599.65` versus their full-risk cash counterfactual.
- Non-hostile target `2026-06-04`, source plan
  `396908d4392fcf78bda52f19b31792407ec01af3f47f42cf9870f59337aa3281`.
  The prior window had four pressure-capped winners; the cap withheld about
  `$4471.71` versus their full-risk cash counterfactual.

Each replay uses all configured symbols, the full uncapped candidate surface,
relational compact ledgers, broker-calibrated costs, and zero broker authority.
The pair succeeds structurally only if non-fragile pressure caps disappear,
actual base-fragile caps remain causal, serialized summary parity stays exact,
and REFUSED/source-gap execution stays zero. Mixed economic deltas are valid
evidence; neither day is allowed to select a date-specific rule.

## 18. Recoverable Pause Checkpoint - 2026-07-16

The current same-root batch is internally consistent and the goal session is
paused. No replay, builder, verifier, test, audit, git-maintenance, or subagent
process is active. Three sleeping Context OS MCP sidecars remain as background
app infrastructure under the historical heavy-repo path; they are not
unfinished batch work. The bound June 4 comparator was intentionally not
started.

Completed implementation:

- restored `pressure_requires_base_fragility=true` in the repaired replay
  profile, so pressure can amplify only an actual causal stop-fragility base;
- normalized final order/trade authority before summary, relational, and
  serialization consumers diverge;
- split scoreable and terminal-unscoreable physical expected/total costs;
- made completed-run finalization reconcile physical statistics from the final
  serialized trade ledger;
- added verifier coverage for causal stop-hazard caps and exact physical
  summary/trade-ledger parity.

Changed code and tests:

- `run_broad_live_as_if_replay_harness.py`;
- `verify_denominator_to_deployment_execution.py`;
- `tests/test_broad_replay_repair_config.py`;
- `tests/test_denominator_to_deployment_verifier.py`.

Focused verification is green: Python compilation passed; `16/16` focused
tests passed with only the pre-existing unknown `pytest-asyncio` configuration
warning. Deterministic April R5 reconciliation reports `6/63` full/reduced
fills, scoreable/unscoreable expected cost `3.77178321/0.96410350R`, and exact
serialized-summary parity. Direct April stop-hazard and summary scans have
`bad_counts={}`.

The hostile May 15 targeted replay completed at prefix
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_05_15_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_TARGETED_R1`
under shared digest `0ea02453...c10` and source-plan digest
`1c6cdfa3...7332`. It materialized `2304` decisions, `8174` candidates, `96`
scorecards, `12` order events, six terminal fills, and `8168` missed rows. Five
fills are scoreable at W/L/F `3/2/0`, gross/final `+1.16268960R`, net
`+0.76586373R`, and cash `+$782.81183897`; one fill is terminal-R-unscoreable.
Physical risk is `$3373.95846882` / `3.375%`, with full/reduced rows `4/2`.
Executed REFUSED/source-gap rows remain `0/0`. Physical summary parity and
stop-hazard execution-authority scans both have `bad_counts={}`.

Against V249 restricted to the same May 15 day, headline behavior changes from
six trades, W/L/F `3/3/0`, `-0.32039441R`, and `-$959.44958301` to five trades,
W/L/F `3/2/0`, `+0.76586373R`, and `+$782.81183897`. The exact delta is
`+1.08625814R` and `+$1742.26142198`, with two added, three removed, and four
shared trade identities. One added scoreable transfer is itself a
`-1.09345695R` loser, so this is not positivity by suppressing every new trade.
It is still only a hostile-day bounded proof, not B7.5 generalization or total
reservoir conversion.

Untested at pause:

- the bound `2026-06-04` non-hostile targeted comparator;
- the paired hostile/non-hostile causal acceptance decision;
- the current-batch route-wide builder, canonical verifier, prompt hardening,
  artifact audit, and full scoped test barrier.

Exact resumption action: do not rerun May 15 and do not start a new repair
batch. Run only
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_TARGETED_R1`
under the same shared digest and source-plan digest
`396908d4...3281`; then parse the paired proof and decide this batch before any
broad replay or successor phase. Broker/live/final remain false.

## 19. June R1 Pair Decision And Suppressed-Pressure R2 Contract - 2026-07-16

The bound June R1 replay completed under shared digest
`0ea02453988e18921f880d9227c736471a1dd3e78209560b1da7a6d83af7dc10`
and source-plan digest
`396908d4392fcf78bda52f19b31792407ec01af3f47f42cf9870f59337aa3281`.
It materialized `238` source rows, `2304` decisions, `6981` candidates, `96`
scorecards, `12` order events, six terminal fills, and `6975` missed rows.
Four fills are terminal-R-scoreable at W/L/F `3/1/0`, gross/final
`+3.25441433R`, net `+3.03331648R`, and physical cash `+$1567.68886163`;
two fills are terminal-R-unscoreable. Physical risk is `$3011.87074087` /
`3.0%`, and all six fills use the reduced-risk tier. Executed REFUSED and
source-gap rows remain `0/0`; physical-summary and stop-hazard-cap scans both
have `bad_counts={}`.

The manifest-bound paired analyzer classifies R1 as `DEEPER_FLAW_EXPOSED`, not
as a correctness or candidate-denominator failure. V258 and R1 each contain
exactly `6981` June 4 source-window candidates with zero added or removed
identities and exact projection-to-`trade union missed` parity. Against V258
on the same source window, R1 adds two trades, removes one, and shares four.
Headline net R is unchanged at `+2.15749037R` while headline cash rises
`+$800.11065680`; physical net R falls `-1.96378776R` while physical cash rises
`+$1612.01421486` because risk expression changes. The prior pressure-capped
XAUUSD winner
`broadorigin_730290b8b2d3fc07f83c9320@@2026-06-04T07:45:00+00:00`
remains a candidate but does not reach scorecard. This is economically mixed
and exposes a deeper allocation question; it does not justify restoring the
non-causal pressure cap or adding a date rule.

R1 also exposed a latent producer-consumer correctness bypass. The scheduler
correctly records a high pressure score as diagnostic when base fragility is
absent, but the downstream stop-hazard materialization preflight previously
reconstructed that suppressed score as active stop pressure. The observed R1
gates all passed, so this bypass did not cause the recorded R1 trade delta, but
the code path could block a valid reduced-risk immediate-limit order in another
window. The same-root repair now:

- keeps `pressure_score_materialized` as diagnostic provenance while excluding
  a base-fragility-suppressed score from active stop pressure;
- treats configured `cap` or `block` as inactive when the authoritative gate
  status is passed and no effective cap/block exists;
- rejects conflicting short/long boolean aliases for
  `pressure_requires_base_fragility` instead of silently choosing one;
- makes the canonical verifier fail any final block caused solely by the
  suppressed diagnostic score.

Focused compile and six producer/consumer/verifier tests pass, and the paired
analyzer's seventeen focused tests pass. The only warning is the pre-existing
unknown `pytest-asyncio` configuration option.

The repair changes code authority, so R1 cannot be reused as the final
same-contract pair. The replay-free shared execution digest for R2 is:

`199fa37cdf521d4c21e00686763437a85549297b9a700ee3281512785eb95500`

The repaired profile hash remains
`fb84f087043ac89461be0ef592528eb49bd3ef3e12b775b75ebb94e11f81f67a`;
the June and May source-plan digests remain respectively
`396908d4392fcf78bda52f19b31792407ec01af3f47f42cf9870f59337aa3281`
and
`1c6cdfa3c4f53c4aa81b0f0d1940c4baa403a0cad0d40d339a4f9c57aa107332`.

Run order is fixed:

1. `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_TARGETED_R2`;
2. `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_05_15_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_TARGETED_R2`.

The predicted observable is behavioral identity with the corresponding R1
run because every observed suppressed-pressure materialization gate passed.
Candidate, scorecard, order, fill, trade, missed, scoreable/unscoreable cost,
risk, cash, and R surfaces must remain exact unless the repaired latent path
was reached through an alias not visible in the prior nested audit. Any delta
must be traced before acceptance. Both R2 runs must share the new digest;
summary parity, causal-cap scans, suppressed-pressure final-block scans, and
REFUSED/source-gap invariants must remain green. No April broad replay or B8
movement is authorized until this R2 pair is materialized and classified.
Broker/live/final authority remains false.

### June R2 Negative-Control Gate

June R2 completed with exit code `0` and is behavior-identical to June R1.
Source rows, decisions, candidates, scorecards, order events, terminal fills,
trades, missed rows, scoreable/unscoreable partitions, cash, risk, cost, and R
all match exactly. The source-universe ledgers are byte-identical at SHA-256
`a1ef75eb226f73619f0e308a16b7f9d0ca6e43b6fc5d80e1519729f6a7516e71`.
Both projections have `6981` rows and share exact hashes for sorted candidate
identity keys (`d56c444fda3c70a7d00c6b8e1d67c952f8aced35b22592b1de76b65ec9139680`),
core candidate/time/symbol/side identity
(`5bcb0226b864332ebc0ac1b05a7b0c933122973b5fa963b818c6e82e7c69e83f`),
and candidate/scorecard presence
(`e77a42a989afa18149ac12ba205408458a24d3571429b52254b9a067fafadf65`).
The R1-to-R2 comparator reports zero summary deltas and zero added or removed
trades. Physical-summary, causal-cap, and order-executable-transfer scans all
have `bad_counts={}`; no suppressed-pressure-only final block exists.

This proves the repair is behavior-neutral on June's observed path while
closing the latent bypass contract. It does not by itself prove a behavioral
gain. The authorized next run is May R2 under the same shared digest
`199fa37cdf521d4c21e00686763437a85549297b9a700ee3281512785eb95500`
and May source-plan digest
`1c6cdfa3c4f53c4aa81b0f0d1940c4baa403a0cad0d40d339a4f9c57aa107332`.
May R2 must preserve the R1 source-universe SHA-256
`a46731c1818f49dc43a3a5772f4e5c309a02af8add66ff424efbb4f1262db611`
and the `2304 / 8174 / 96` decision/candidate/scorecard surface. The same
physical, cap, transfer, flow, projection, and R1-to-R2 comparisons are required
before rebuilding the paired R2 analyzer. Broker/live/final remains false.

## 20. Same-Digest R2 Pair Closure And Allocation Trace - 2026-07-16

May R2 completed with exit code `0` under the same shared digest as June R2.
It is behavior-identical to May R1: all summary deltas are zero; all six trade
identities are unchanged; source rows, decisions, candidates, scorecards,
orders, fills, missed rows, costs, cash, risk, and R match exactly. The May R1
and R2 source-universe ledgers are byte-identical at
`a46731c1818f49dc43a3a5772f4e5c309a02af8add66ff424efbb4f1262db611`.
Both candidate projections contain `8174` rows and share exact sorted hashes:

- identity keys: `65b2fec08d8f044f32e2a818e6fcef0d9b4732d97b724769a525dcaafcebdfe0`;
- core candidate/time/symbol/side identity:
  `93fcdf6eb872edff47a1a095bd2fdbaf96eb10860aef2bce5e5903b9ee6c522b`;
- candidate/scorecard presence:
  `837daf25ba40e784df4137ee3fb465bd4c678f612e0eb0f34a036f3acf2726f1`.

May physical-summary, causal-cap, and order-executable-transfer scans all have
`bad_counts={}`. The candidate projection has exact parity to six trade plus
`8168` missed identities. V249 lacks a retained candidate/missed surface, so
the May-to-V249 baseline comparison remains explicitly trade-identity bounded;
the independently materialized May R1-to-R2 candidate proof prevents that
historical limitation from being mistaken for current candidate uncertainty.

The final R2 paired analyzer is complete-manifest valid with fingerprint
`66209f4d021aae0cfd619e1a02faa26b1e8d62b1c7b54c664d8ad1b8ab3b8904`.
It contains eight pressure-cohort rows, `6990` identity-transition rows, and
two missed-comparison rows. Structural and evidence issue counts are zero.
Its decision remains `DEEPER_FLAW_EXPOSED` for the same two June signals:

- physical net R is `-1.96378776R` versus V258 on June 4, despite physical cash
  increasing `+$1612.01421486` through larger risk expression;
- XAUUSD identity
  `broadorigin_730290b8b2d3fc07f83c9320@@2026-06-04T07:45:00+00:00`
  remains in the exact candidate denominator but stops before scorecard instead
  of retaining the prior filled winner.

The suppressed-pressure materialization repair is therefore complete and
behavior-neutral on both observed paths. It is not the cause of the remaining
economic signal. No full-April replay is authorized yet. The strongest next
action is to trace the XAU identity through its exact V258/R2 selector,
scorecard-competition, scheduler, risk-finalizer, same-symbol, and missed rows;
separate an actual allocation defect from expected causal replacement or
comparator-state effects; then implement only the first proven causal repair.
The predicted observable and successor replay are not bound until that trace
is complete. Broker/live/final remains false.

## 21. June XAU Ordered-Tick Replacement-Value Discriminator - 2026-07-16

The exact R2 trace resolves the pre-scorecard divergence. The prior V258
XAUUSD short at `2026-06-04T07:45:00Z` was not removed by candidate generation,
the repaired stop-hazard rule, or scorecard competition. In R2, an earlier
XAUUSD short
`broadorigin_27432b7392759e5a5dbe7658@@2026-06-04T07:30:00+00:00`
filled passively at `07:34:12Z` with `0.625%` account risk and remained open at
`07:45Z`. The later candidate was then correctly fail-closed before scorecard
because the unsigned replay path had no signed same-side scale-in/new-entry
authority. Its prior `+1.96378776R` is therefore diagnostic displaced value,
not executable R that may be added to the current path.

The remaining uncertainty is the terminal value of the earlier fill. R2 could
only label it terminal-R-unscoreable because its active source catalog lacked
the required ordered ticks. A preserved FTMO owner-authorized export for June
1-5 has now been rehydrated at the exact manifest path without modifying the
manifest. The manifest has zero export errors, SHA-256
`ebdbb1bd0ddb151b1f72e7acd8d372cf5394db395161ea4934ba0ffec31c676d`,
and binds `1,167,336` XAUUSD ticks from
`2026-06-01T01:05:00.306Z` through `2026-06-05T23:49:59.856Z`. The physical
tick file exactly matches manifest SHA-256
`ca81d8319f3ca21f4955e5e70fa106a25dcb7e7f26e235895b3378a6b3f689fe`.
The replay-free source plan reports covered June 4 ordered-tick authority,
matching file hashes, no unresolved M1 day, and no integrity failure.

The smallest executable discriminator is bound as:

- prefix:
  `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_REPLACEMENT_VALUE_TARGETED_R1`;
- window: `2026-06-04` only;
- active symbol: `XAUUSD` only;
- profile: `repaired_package_conversion_v3`;
- candidate cap: `0`, one-day chunk, relational compact ledgers, tick lookup
  enabled, zero broker authority;
- shared execution contract:
  `2a87ca1f7b1c9bbd8e16d4ce1823073224be7cd9f22bb9b714330bde69322e00`;
- source plan:
  `59c93b3301fdd9f5a538bcfebf4071552fe94b4c90f0288ef643d7087edc86db`.

The causal hypothesis is that the apparently lost `07:45` winner is a
replacement-value question created by the truthful `07:30` fill, not a
stop-hazard or candidate-denominator defect. The predicted observable is that
the XAU-only replay preserves the two exact candidate identities and their
same-symbol chronology while the ordered ticks convert the `07:30` fill from
terminal-R-unscoreable to an ordered-path scoreable outcome. This target is
terminal-path evidence only: it may diagnose the XAU sequence but cannot by
itself establish full-portfolio economics because the active symbol universe
is deliberately bounded.

Decision rule:

- if the exact sequence is preserved and the earlier fill becomes scoreable,
  compare its physical net R, cash, risk, MFE/MAE, and chronology with the
  displaced candidate's diagnostic value before deciding whether any
  allocation challenger is warranted;
- if the earlier fill is a scoreable loss or materially inferior outcome,
  bind a same-risk serial replacement/reserve challenger under the unchanged
  `0.625%` XAU ceiling;
- if the exact sequence is not preserved, do not infer economics from the
  XAU-only run; escalate to the same June day under all 24 symbols and the new
  tick source;
- zero executed REFUSED/source-gap rows, exact physical-summary parity, source
  integrity, signed authority, and same-symbol risk chronology remain hard
  gates. No policy is changed before this discriminator is read.

Broker/live/final authority remains false.

## 22. XAU-Only Result And Full-Portfolio Tick Reconciliation - 2026-07-16

The bound XAU-only ordered-tick replay completed with exit code `0`. Its
execution and source-plan bindings match exactly, the June 4 tick window is
covered with both physical XAU tick components hash-valid, and physical-summary,
stop-hazard-cap, and order-executable-transfer scans all have `bad_counts={}`.
Executed REFUSED/source-gap fills remain zero.

The early exact identity is preserved with the same side, entry geometry,
`0.625%` risk, and passive fill event. Ordered ticks refine its M1 timestamps
from `07:34:00Z` / `08:48:00Z` to `07:34:12.004Z` / `08:48:10.204Z` and convert
the previously unscoreable fill into a scoreable winner:

- gross/final: `+1.18186479R`;
- expected cost: `0.109446387846R`;
- physical net: `+1.07241840R`;
- cash: `+$670.26150000`;
- MFE/MAE: `+2.098318358R / -0.669945018R`;
- close: `selected_policy_replay:giveback_close`.

This establishes that the earlier replacement was profitable under ordered
path truth. It does not close the allocation question. The XAU-only universe
did not preserve the full-portfolio downstream path: the `07:45` identity
reached a scorecard instead of stopping before scorecard, and an additional
`14:30` XAUUSD short filled and lost `-1.10446455R`. The XAU-only total of two
trades and `-0.03204615R` is therefore not a full-portfolio economic result.
Per the predeclared rule, exact portfolio reconciliation is required.

The full-portfolio successor is bound as:

- prefix:
  `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_TARGETED_R1`;
- window: `2026-06-04` only;
- active symbols: all configured 24;
- profile and execution options: unchanged from June R2, including uncapped
  candidates and relational compact ledgers;
- shared execution contract:
  `199fa37cdf521d4c21e00686763437a85549297b9a700ee3281512785eb95500`;
- source plan with the XAU June ticks:
  `a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001`.

The predicted observable is exact June R2 candidate, scorecard, order, fill,
and missed identity outside terminal-path enrichment for the early XAU fill.
The `07:45` candidate must retain the full-portfolio same-side signed-authority
block. If no other behavior changes, the expected physical result is five
scoreable and one unscoreable fills, gross/final `+4.43627912R`, scoreable cost
`0.33054424R`, net `+4.10573488R`, cash `+$2237.95036163`, and unchanged
`3.0%` total risk. This would reduce the same-day V258 equal-risk deficit from
`-1.96378776R` to `-0.89136936R` while increasing the cash advantage. These
are predictions, not evidence, until the serialized full-portfolio ledgers
materialize.

Any added/removed trade, changed candidate identity, changed late-candidate
authority, or unexpected risk/cost delta must be traced before acceptance.
Physical-summary parity, tick integrity, causal-cap truth, signed transfer,
and zero executed REFUSED/source-gap rows remain hard gates. No allocation
policy or broker/live/final authority is enabled by this replay.

### 22.1 Pre-Completion Arithmetic Correction

Before the full-portfolio replay completed, the XAU-only trade comparison
showed that the same `14:30` XAUUSD loss is also terminal-path enriched by the
new tick source: its net changes from `-1.03464434R` to `-1.10446455R` and cash
from `-$651.77021036` to `-$694.91709416`, while its gross/final remains
`-1.0R`. Section 22's first prediction included the newly scoreable `07:30`
winner but omitted this already observed cost refinement.

The corrected pre-completion prediction, if identities and all non-XAU values
remain unchanged, is physical gross/final `+4.43627912R`, scoreable cost
`0.40036445R`, net `+4.03591467R`, cash `+$2194.80347783`, unscoreable cost
`0.04580000R`, and unchanged `3.0%` risk. Headline would become three wins and
one loss at `+2.12544422R` and `+$991.30998839`. The V258 same-day physical
delta would be `-0.96118957R` and `+$2239.12883106`. This correction is bound
from completed XAU-only rows before the full result and is not a read of the
running portfolio replay.

## 23. Full-Portfolio Ordered-Tick Reconciliation Closure - 2026-07-16

The bound 24-symbol replay completed with exit code `0`. Sections 22 and 22.1
remain the preregistered lineage; their predictions are superseded by the
serialized result. The completion-manifest-last proof packet is:

- `B7_5_XAU_ORDERED_TICK_FULL_PORTFOLIO_RECONCILIATION_PROOF_SUMMARY.json`;
- `B7_5_XAU_ORDERED_TICK_FULL_PORTFOLIO_RECONCILIATION_PROOF_ROW_LEDGER.jsonl`;
- `B7_5_XAU_ORDERED_TICK_FULL_PORTFOLIO_RECONCILIATION_PROOF_DOSSIER.md`;
- `B7_5_XAU_ORDERED_TICK_FULL_PORTFOLIO_RECONCILIATION_PROOF_COMPLETION_MANIFEST.json`.

The analyzer decision is `FULL_PORTFOLIO_RECONCILIATION_COMPLETE` with zero
structural issues. Candidate, trade, and missed identity partitions are exact
versus June R2: `6981 / 6 / 6975` with zero added or removed rows. Scorecard
and order-event counts remain `96 / 12`. One terminal row becomes scoreable
and no terminal-scoreability row regresses.

Observed physical behavior is six fills, five scoreable plus one unscoreable,
W/L/F `4/1/0`, gross/final `+4.43627912R`, scoreable net `+4.03591467R`,
cash `+$2204.18020365`, risk cash `$3027.86901650`, and `3.0%` summed risk.
Headline behavior is four trades, `3/1/0`, `+2.12544422R`, and
`+$992.62016070`. The `0.40036445R` scoreable and `0.04580000R` unscoreable
cost partitions reconcile to the six serialized fills. Physical-summary,
causal-cap, and order-transfer scans all have `bad_counts={}`; executed
REFUSED/source-gap rows remain `0/0`.

The flow consumer now preserves per-row terminal provenance instead of calling
all fills M1 proxy: four fills are ordered-tick and two are ordered-M1; five
are scoreable and the remaining M1 row is terminal-unscoreable. This is a
consumer-label repair only and does not change replay behavior.

Versus June R2, physical delta is `+1.00259819R`, `+$636.49134202`, and
`+$15.99827563` risk cash at unchanged `3.0%` risk. Headline delta is
`-0.03204615R` and `-$23.34542185`. The corrected preregistered cash prediction
was low by `+$9.37672582` physical and `+$1.31017231` headline because actual
row cash translation differed slightly from the pre-completion arithmetic.

The late `07:45` XAU identity remains missed, but the hydrated tick path changes
the causal disposition. Its broker-calibrated spread is `0.126612R` versus a
`0.10R` ceiling and total cost is `0.151024R` versus a `0.15R` ceiling, so cost
refuses the candidate before lifecycle/same-symbol authority is evaluated. Its
ordered-tick diagnostic opportunity is only `+0.37626090R`, not the old M1
proxy `+1.96378776R`. The earlier `07:30` fill is independently proven as a
scoreable `+1.07241840R` winner. The evidence therefore does not support the
suspected allocation-correctness defect or restoration of the old cap.

Economics remain mixed rather than promoted. Versus V258 same day, physical
delta is `-0.96118957R` but `+$2248.50555688` cash with `+1.975` percentage
points more risk; headline delta is `-0.03204615R` and `+$776.76523495`.
This is bounded same-day simulated reconciliation, not broad performance,
account return, payout, drawdown, or broker-real evidence. It authorizes no
policy preference or change, final selection, live execution, or broker
mutation.

The strongest successor is not another run of this prefix. First complete and
commit canonical route certification. Then bind a sealed multi-window
equal-risk selection versus dynamic-risk cash-expression experiment across the
completed January, April, May, and June evidence, preserving candidate and
missed identities, terminal scoreability, cost, stress, and drawdown surfaces.

## 24. Sealed Proof-Consumer R2 Regeneration - 2026-07-16

Canonical verification of the completed R1 packet reduced the remaining
issues to three behavior-neutral truth contracts:

- zero-trade scheduler scorecards carried matching pre-risk, reported, and
  finalizer-probe quality values and matching source maps, but omitted the
  canonical pre-risk source map;
- a nonterminal pending order intent was incorrectly required to carry future
  terminal-fill realism, while a terminal-R-unscoreable filled trade was
  incorrectly required to invent net-R arithmetic; and
- a supported selected policy on the one terminal-R-unscoreable UKOIL fill
  bypassed the canonical selected-policy diagnostic envelope.

The repairs are fail-closed. Provenance is copied only across three exact,
finite, matching quality surfaces; pending intent waives only a missing future
fill-realism class and retains every forbidden-class/authority check;
terminal-R-unscoreable arithmetic still requires broker-calibrated entry cost;
and selected-policy replay emits a diagnostic-only envelope with null R and all
terminal/headline/live authorities false. Hostile stale-R, quality-gate, cost,
and pending-authority cases are covered. The complete affected three-file
barrier is `1365` passed with the one unchanged unknown `asyncio_mode` warning.

One regeneration is sealed as:

- prefix:
  `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R2`;
- window and universe: `2026-06-04`, all configured 24 symbols;
- profile/options: exact completed R1 profile and compact execution options;
- shared execution contract:
  `77066a99723153258d45232a7ad3943961231720986281bfc5a2763436999bb1`;
- source-plan contract:
  `a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001`;
- effective profile hash:
  `fb84f087043ac89461be0ef592528eb49bd3ef3e12b775b75ebb94e11f81f67a`.

Acceptance requires exact R1 candidate, scorecard, order, trade, missed,
scoreability, risk, R, cash, cost, and identity results. The only authorized
row deltas are the 89 canonical zero-trade provenance maps and the explicit
diagnostic selected-policy envelope on the already unscoreable UKOIL row.
Physical/headline economics must remain `+4.03591467R / +2.12544422R`, physical
cash `+$2204.18020365`, risk `3.0%`, and five scoreable plus one unscoreable
fills. Any identity or economic delta stops certification and reopens causal
analysis. Broker/live/final and policy-change authority remain closed.

## 25. R2 Serialization Failure And Sealed R3 - 2026-07-16

R2 completed with exact R1 economics and trade identity: six common trades,
zero added or removed, zero delta in physical/headline R, cash, risk, cost,
scoreability, candidate, scorecard, order, or missed-row counts. The UKOIL
terminal-R-unscoreable diagnostic envelope serialized correctly. R2 is not
accepted as final proof because the 89 provenance maps remained null.

The producer timing root is exact: both donor maps materialize at the final
package-authority annotation boundary, after the first quality-normalization
hook. The fail-closed backfill itself was correct but ran too early. It now
runs again immediately after final package-authority normalization. A hostile
late-donor unit test and a projection across all 96 R2 scorecards prove 96
valid canonical maps with no value synthesis or overwrite; the complete
harness suite passes `195` tests.

The only authorized successor is:

- prefix:
  `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3`;
- shared execution contract:
  `163329e9cf863e812db626f99d53469172f95b1512e49457eb0b3841464d9b67`;
- source-plan contract:
  `a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001`;
- window, universe, profile, options, expected behavior, and closed authority
  boundaries: unchanged from Section 24.

R3 must reproduce the exact R1/R2 economics and identities while serializing
all 96 valid pre-risk provenance maps and the same null-R/no-authority UKOIL
diagnostic envelope. R2 is retained as failed serialization evidence, not as
accepted route authority.

## 26. Proof-Consumer R3 Closure - 2026-07-16

R3 completed with exit code `0` and met the sealed contract. The generic
R1-versus-R3 comparison has six common trades, zero duplicates, zero added or
removed identities, and no nonzero summary delta after flow materialization.
Candidate / scorecard / order-event / physical-trade / missed counts remain
`6981 / 96 / 12 / 6 / 6975`. Physical and headline economics remain exactly
`+4.03591467R / +2.12544422R`; physical cash remains `+$2204.18020365`, risk
cash `$3027.86901650`, and risk `3.0%`. Five fills remain scoreable and one
remains terminal-R-unscoreable.

The intended truth deltas are now physical. All `96 / 96` scorecards carry a
valid canonical pre-risk map for expected net R, probability, and source
completeness. The UKOIL unscoreable fill carries
`diagnostic_terminal_r_unscoreable`, null replay/final/net R, `bound=false`,
and explicit no-authority status. Direct selected-quality, cost, physical
summary, stop-hazard, order-transfer, and selected-policy scans all have empty
bad counts. Source-bound parity materializes `6981` candidate-instance rows,
`5942` parity rows, and `1101` leakage buckets; flow materializes `379`
buckets and preserves four ordered-tick plus two ordered-M1 terminal sources.

The completion-manifest-last proof packet is
`B7_5_XAU_ORDERED_TICK_FULL_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3_*` and
its decision is `FULL_PORTFOLIO_RECONCILIATION_COMPLETE` with zero structural
issues. This is bounded same-day simulated correctness and reconciliation
evidence. It does not change the mixed comparison versus V258, authorize a
policy, establish broad profitability, or enable broker/live/final mutation.
Canonical route certification and the scoped commit are next; after that, the
strongest economic successor remains the sealed multi-window equal-risk versus
dynamic-risk cash-expression experiment.

## 27. Canonical Route Certification - 2026-07-16

R3 is route-certified. The final builder manifest selects R3 as current
quality/parity authority, preserves V254T as the broader holdout gate, and
binds `231` files. The final canonical verifier reports `ok=true` and
`issue_count=0`; `FOCUSED_TEST_RESULT.json` records the exact final barrier and
is `passed`. Python compilation and all `1918` affected tests pass with the one
unchanged unknown `asyncio_mode` warning. Prompt hardening, both parent
verifiers, the full route artifact audit, and the parent artifact audit are
green.

This certification changes no trading result and promotes no policy. B7.5
truth/correctness and the bounded June reconciliation checkpoint are complete;
cross-window economic generalization remains failed/mixed. The next executable
economic route is a separately predeclared multi-window equal-risk selection
versus dynamic-risk cash-expression experiment. Broker/live/final remain
closed until that evidence and later activation gates support them.

The scoped implementation, proof, and certification packet is committed as
`beec3ce52` (`certify B7.5 June proof-consumer reconciliation`).
