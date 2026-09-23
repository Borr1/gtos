# B7.2 V238 Final-Risk And Fillability Atomicity

Generated UTC: 2026-07-12T18:00:15Z.

Status: implementation batch selected from completed V237R2 evidence. This is
a targeted truth-repair checkpoint. It does not certify hostile-five-day,
broad-history, final-selection, broker-live, or total-reservoir behavior.

## 1. Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V237R2_B7_2_EXACT_MEMBER_ATOMIC_AUTHORITY_TRANSFER_20260513_20260515_5SYMBOL_REPAIRED_ONLY_COMPACT`

V237R2 covered 2026-05-13..15 for `GER40`, `JP225`, `NAS100`, `US30_cash`,
and `XAUUSD`:

| Metric | V237R2 |
| --- | ---: |
| source / decision / candidate / scorecard rows | 50 / 6,624 / 8,790 / 276 |
| order events / logical terminal orders / fills | 41 / 21 / 18 |
| missed rows | 8,769 |
| W/L/F | 8 / 10 / 0 |
| net / gross / final R | +2.13064803 / +3.60123918 / +3.60123918 |
| cash PnL / risk cash / risk pct sum | -$1,181.37730315 / $6,652.47638865 / 6.75% |
| expected cost | 1.47059115R |
| REFUSED-cost / source-gap executed | 0 / 0 |
| executable missed rows / R | 0 / 0.0R |
| diagnostic scoreable missed rows / R | 2,349 / -857.87372696R |
| stress +0.05 / +0.10 / +0.20R per trade | +1.23064803 / +0.33064803 / -1.46935197R |
| MC iterations / total net / worst drawdown | 200 / +2.13064803R / -7.75244043R |

V237R2 restored opportunity rather than suppressing it: fills increased from
two in V236 to 18 and the added-context cohort contributed +4.25111207R net.
It is not accepted as a clean truth checkpoint because eight filled trades
carry nonzero actual risk beside zero public final-risk aliases, and one filled
US30 order carries a conflicting/missing execution-fillability atom.

## 2. Current Process State

No replay, pytest, compile, or replay-finalization process is active. V237R2 is
complete and must not be duplicated. The next run is a targeted successor only
after both truth defects and the associated risk-expression contract are
focused-test green.

## 3. Baseline Comparison

| Run | Window | Trades | W/L/F | Net R | Gross/Final R | Cash PnL |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| V89D | hostile 5d | 56 | 41/15/0 | +34.84520454 | +39.93441037 | +$8,178.90660707 |
| V90 | hostile 5d | 51 | 37/14/0 | +28.84201157 | +33.36349114 | +$6,371.80465431 |
| V92 | hostile 5d | 51 | 37/14/0 | +29.35570236 | +33.93212860 | +$6,228.63096022 |
| V219 | hostile 5d | 23 | 14/9/0 | -2.82440031 | -0.79141028 | +$204.17530212 |
| V236 | hostile 5d | 2 | 1/1/0 | -0.92559780 | -0.79425689 | -$92.57809253 |
| V237R2 | targeted 3d/5-symbol | 18 | 8/10/0 | +2.13064803 | +3.60123918 | -$1,181.37730315 |

The comparator windows differ. V237R2 proves local transfer behavior only and
is not compared directly with the global source-bound reservoir.

## 4. Current Dirty Implementation Surface

Already dirty route-owned code/tests:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- route broad harness and verifier
- focused scheduler/runtime/broad/verifier tests
- current root-cause map and Fable execution matrix

This batch also affects:

- `src/components/selector_v4.py`
- `src/components/ultimate_candidate_package.py`
- focused selector/package tests

Unrelated Context OS changes, historical deletions, and `.context/LIVE_STATE.md`
remain outside this checkpoint.

## 5. Reconciled Snapshot Findings

| Agent | Disposition | Current conclusion |
| --- | --- | --- |
| Averroes | INCORPORATED | V236/V237 summary and bounded finalization contracts are closed. |
| Hume | INCORPORATED | Exact-member circular authority construction is repaired and V237R2 proves transfer. |
| Confucius | INCORPORATED | Target lifecycle validity was not the choke; no lifecycle relaxation was made. |
| Descartes | PARTIAL | Candidate-level risk/fillability contradictions were real. V237R2 proves candidate transfer but exposes finalizer-to-order risk alias drift and an incomplete selector-package fillability sibling. |

All findings were checked against current code. No new agent wave is active for
this changing integration batch.

## 6. Current Root-Cause Chain

| Stage | Status | Current truth |
| --- | --- | --- |
| source-bound -> candidate | PARTIAL / LATER B7 | Supply is not the current choke; 74 known materialization gaps remain a later source batch. |
| candidate -> selector | PARTIAL | The candidate has the exact 0.92 US30 atom, but selector package evaluation retains the value without its provenance tuple. |
| selector -> scheduler | TRANSFER RESTORED / TRUTH PARTIAL | V237R2 restores scorecard/order conversion, but selected scorecard quality recomputation detects the incomplete selector-package sibling. |
| scheduler -> risk | PARTIAL | Finalizer selection works, but its probe exports a final value beside stale pre-final runtime aliases. |
| risk -> order | OPEN ROOT DEFECT | `simulate_order()` merges the stale finalizer runtime alias over the fresh packet, producing contradictory nested final risk. |
| order -> lifecycle -> fill | VALUE TRANSFERRED / TRUTH PARTIAL | 18 fills execute honestly by path class, but one immediate-marketable US30 fill reports missing/conflicting fillability. |
| fill -> exit | DEFERRED UNTIL TRUTH GREEN | Selected-policy-only gross is +3.60123918R; no harvest tuning belongs in this batch. |
| exit -> ledger | OPEN CONSUMER DEFECT | The ledger normalizer prioritizes stale nested runtime risk and overwrites the correct outer final risk with zero. |

## 7. Highest-Leverage Same-Root Batch

Batch: `B7_2_FINAL_RISK_AND_EXECUTION_FILLABILITY_ATOMICITY`

Correctness repairs:

1. Materialize one canonical executable final-risk atom after the selected
   finalizer probe is merged into order-time risk authority.
2. Bind nested and public `final_approved_risk_pct`,
   `runtime_final_risk_pct`, and `approved_risk_pct` to that atom while
   preserving scheduler/selected/dynamic values as pre-final provenance.
3. Make the public-risk consumer validate the canonical atom and refuse to
   prefer a stale nested zero over a positive executed decision.
4. Carry execution fillability through selector package evaluation as one
   value/source/source-time/boundary/class tuple plus the nested predecision
   envelope; never emit the executable numeric alias alone.
5. Recompute selected scorecard/order/trade quality from that complete atom and
   add verifier assertions for executed risk and fillability consistency.

Performance analysis, not outcome-fit policy:

6. Explain the 0.5/0.625/1.0 finalizer sizing from predecision scheduler,
   dynamic-budget, ladder, and guard authority. Do not tune by symbol/session or
   realized outcome. Patch only if the sizing contract itself is semantically
   wrong.

## 8. Exact Files And Classification

| File/component | Classification |
| --- | --- |
| `src/research_infra/v4_timewarp_simulated_live_research_loop.py` | correctness: canonical final-risk merge and consumer; diagnostic provenance |
| `src/components/selector_v4.py` | correctness: atomic fillability producer |
| `src/components/ultimate_candidate_package.py` | correctness: package packet atom preservation |
| route verifier | verifier: executed risk/fillability invariants |
| focused runtime/selector/package/verifier tests | proof |

## 9. Expected Measurable Effect Before Replay

- Candidate -> scorecard: same selected candidate count unless the corrected
  atom exposes a genuinely invalid candidate.
- Scorecard/order -> fill: US30 2026-05-14 14:15 must retain 0.92 and its exact
  source tuple; no extra fill is required for this truth repair.
- Missed positive/negative R: unchanged except rows whose incomplete atom is
  correctly reclassified.
- Trade count and R: expected behavior-neutral for pure atomicity fixes. Any
  change must be explained by a previously false executable claim.
- Cash PnL: expected unchanged until a separately justified risk-expression
  policy repair is included.
- Executed risk: actual `risk_pct`, nested final trio, and public final trio must
  agree for every fill. Scheduler/selected/dynamic provenance may differ and
  must remain visible.
- REFUSED/source-gap execution remains zero.
- Full-risk/reduced-risk distribution remains explicit; no blanket promotion.

## 10. Targeted Proof Contract

Helped:

- zero executed final-risk trio mismatches;
- zero executed fillability atomic failures;
- the exact US30 row carries 0.92 with its 14:00 source time and closed-M15
  boundary through candidate, scorecard, order, and trade;
- scheduler/selected/dynamic risk provenance remains available;
- trade count and opportunity are not suppressed to manufacture success;
- REFUSED/source-gap execution remains zero.

Failed:

- any filled trade still has contradictory final risk;
- any filled trade has a numeric execution-fillability claim without a complete
  predecision tuple;
- the fix merely nulls or blocks the affected fills without proving the source
  claim invalid;
- provenance fields are collapsed into the final risk and pre-final allocation
  history is lost.

Next deeper flaw:

- once truth is green, inspect whether finalizer sizing is double-promoting raw
  `trade` rows or otherwise ranking conviction inversely; then prove that causal
  risk-expression repair on a targeted slice before returning to hostile five
  days and objective non-May regimes.

This smoke proves or disproves the local repair; it does not prove total
reservoir conversion or final/live readiness.

## 11. Implementation And Proof Barrier

Checkpoint UTC: 2026-07-12T18:56:31Z.

Implemented across the same-root chain:

- canonical executable final-risk atom at runtime authority, finalizer merge,
  terminal order controls, and public ledger projection;
- selected-policy owner-approved calibration atom precedence over incomplete
  stale prefixed aliases, without overriding a complete valid signed atom;
- complete execution-fillability tuple propagation through package selector
  and replay quality surfaces; numeric-only aliases remain diagnostic;
- explicit partial full-risk promotion provenance after dynamic-budget caps;
- route verifier scan for execution-bound risk/fillability atomicity.

Focused proof is green: `17 passed` across package, selector, scheduler,
runtime/order materialization, stop-cap, selected-policy precedence, and route
verifier tests. `py_compile` passes for every touched production, verifier, and
test module.

Historical V237R2 control scan, before regeneration:

- execution-bound order/trade rows: `38/18`;
- missing canonical risk atom: `38/18`;
- stale outer and nested runtime/approved risk aliases: `18` order events and
  `8` filled trades;
- incomplete execution fillability: `2` order events and `1` filled trade.

V238 targeted proof slice:

- date: `2026-05-14`;
- symbols: `XAUUSD`, `JP225`, `GER40`, `US30_cash`;
- profile: `repaired_package_conversion_v3`;
- purpose: cover four historical final-risk conflicts plus the exact US30
  14:15 fillability failure while retaining full package scoring;
- success: zero atomicity scan findings, no REFUSED/source-gap execution, and
  no opportunity suppression used to manufacture the result.

Storage checkpoint:

- free space observed before cleanup: `15 GiB`;
- preserve all V237R2 artifacts, current route summaries/manifests, code,
  configs, tests, root-cause map, Fable matrix, and this brief;
- demote only V236's superseded raw candidate, missed-opportunity, and decision
  ledgers after confirming its completed summary remains; expected recovery is
  about `5.7 GiB`;
- no Git clean, cache deletion, current-route evidence deletion, or iCloud
  eviction is part of this checkpoint.

## 12. V238 Result And V238R2 Residual Proof

V238 completed at `2026-07-12T19:13:05Z` over the exact one-day/four-symbol
target. This is a bounded truth-repair proof, not broad market evidence.

Behavior:

- candidates / scorecards / logical orders / fills: `2469 / 92 / 7 / 6`;
- net / gross / final R: `-2.81768013 / -2.26948297 / -2.26948297`;
- cash PnL / risk cash / risk percent: `-$980.11471440 / $2439.92967918 / 2.45%`;
- wins / losses / flats: `3 / 3 / 0`;
- diagnostic scoreable missed rows / R: `609 / -143.51033091R`;
- executable scoreable missed rows / R: `0 / 0R`;
- REFUSED/source-gap executed rows: `0 / 0`;
- stress at `+0.05R/+0.10R/+0.20R` per trade:
  `-3.11768013/-3.41768013/-4.01768013R`;
- Monte Carlo total / worst drawdown: `-2.81768013/-3.34698405R`.

Truth scan after correcting the verifier's sizing-balance semantics:

- execution-bound order rows valid: `12/12`;
- execution-bound trade rows valid: `5/6`;
- the prior two risk-cash findings were false positives because trade
  `balance_before` is the later close-sequencing balance while sizing cash is
  bound to `risk_authority.balance_before` at order time;
- one real residual remained: US30 at `2026-05-14T14:15:00Z` retained a stale
  `predecision_limit_fillability_cross_surface_atomic_conflict` on the trade
  despite its accepted order carrying the complete `0.92`, `14:00`,
  closed-M15 atom.

Same-root residual repair:

- risk-expression fillability is now produced and propagated as one complete
  value/source/source-time/boundary/class atom rather than a numeric sibling;
- trade tracing consumes the accepted order/position atom before later risk
  diagnostics, so a value-only diagnostic sibling cannot invalidate immutable
  fill authority;
- verifier risk-cash binding uses the order-time risk-authority balance and
  preserves trade-time account-balance semantics;
- focused residual proof is green: `5 passed`; compile remains green.

V238R2 must rerun the identical slice and is behavior-neutral by expectation.
Success requires `12/12` execution-bound order events and `6/6` trades valid,
zero atomicity findings, the same six fills and R within deterministic
tolerance, and zero REFUSED/source-gap execution. Any behavior change must be
traced to the newly completed risk-expression atom rather than accepted as a
headline improvement.

## 13. V238R2 Denominator Drift And V238R3 Source-Restored Proof

V238R2 cleared the implemented atomicity contract (`8/8` execution-bound order
events and `4/4` trades valid), but it is not an accepted behavior comparator.
The Mac-local cutover retained the hostile-window manifest while omitting two
referenced tick ledgers. That changed broker-cost authority before selector
admission:

- JP225 lost the historical predecision tick quote (`10.0` spread price,
  `0.08101814R` spread) and fell back to the broker-profile ceiling (`50.0`,
  `0.40509070R`), changing `PASSED` to `REFUSED`;
- GER40 likewise lost its hostile-window tick quote and changed from `PASSED`
  to `REFUSED` under the profile ceiling;
- source-universe tick rows changed from `10` to `9`, trades from `6` to `4`,
  and net R from `-2.81768013R` to `-0.59129050R` by removing two losing
  trades. This is denominator drift and must not be reported as policy gain.

The exact retained V238 source ledgers were restored into the active data
surface and verified against the manifest:

- JP225 SHA-256:
  `623839433d08a379db2f6e4f0006317bc7ae77a2d19c5d3c7f69beaeb61bdd05`;
- GER40 SHA-256:
  `d72d2a338bbb484f312199ac0dda2afa47694fa0abdafb4a7add88fb45253cf1`.

V238R3 reruns the identical date/symbol/profile configuration. It must restore
the hostile-window tick source for every requested symbol, the two historical
tick cost packets, the six-trade denominator, and clear atomicity on every
execution-bound order/trade row. Out-of-window discovery rows are not part of
the behavioral denominator.

## 14. V238R3 Final Disposition

V238R3 passes the B7.2 atomicity checkpoint on the restored denominator:

- historical hostile-window tick sources are present for XAUUSD, JP225,
  GER40, and US30_cash and retain their manifest hashes;
- candidates / scorecards / logical orders / fills are
  `2469 / 92 / 7 / 6`;
- net/gross/final R is
  `-2.81768013/-2.26948297/-2.26948297R`, exactly matching V238;
- W/L/F is `3/3/0`; cash PnL is `-$980.11471440`;
- `12/12` execution-bound order events and `6/6` trades are atomic;
- executed REFUSED/source-gap rows are `0/0`.

The canonical final-risk and execution-fillability sub-batch is closed. The
economic-value gate is not: the target is still losing. The next same-root
batch is causal finalizer/risk-expression, scheduler rank/reallocation, and
selected-policy/exit loss-transfer analysis before hostile-five-day and
non-hostile regime proof.

## 15. V239 Terminal Projection And Finalizer Truth Batch

The full physical verifier against V238R3 found one same-root terminal truth
failure after the atomicity checkpoint closed. Terminal missed rows were built
from the stale pre-scheduler candidate, while candidate-ledger rows were later
backfilled with scheduler, POI, displacement, and finalizer truth. That split
caused four downstream defect families rather than four independent policies:

- `1894` terminal missed rows requiring POI state lost their exact POI state;
- `314` candidate/scorecard instances were not reconciled to an exact missed
  terminal projection;
- one GER40 LONG instance with `expected_net_r=0.646438955` was marked as
  provisionally finalized even though the signed route floor is `0.7`;
- order-attempt identity and executable-order binding were conflated for one
  blocked order, while counterfactual immediate-market routes were incorrectly
  required to invent an order-stage marketability blocker.

The same-root batch is implemented across producer and consumers:

- all terminal missed paths consume the exact canonical scheduler-backfilled
  candidate instance when, and only when, the canonical instance key matches;
- exact POI state and displacement quality are projected to terminal rows;
- provisional reduce-risk authority uses the strict materialized signing path,
  so below-floor quality is rejected before scheduler and cannot be stamped
  finalized;
- immediate-marketable budget release returns its packet to the owning risk
  builder instead of binding undefined final-risk variables;
- legacy runtime-final risk precedence remains available only when a canonical
  final-risk atom is absent;
- verifier semantics now separate attempt identity from executable binding,
  exempt already-terminal rows from the hard-clean execution exception, and
  permit a scheduler-selection blocker for counterfactual immediate routes.

Focused proof is green: `1174 passed`, zero failures, with only the unchanged
unknown `asyncio_mode` warning. Compile also passes.

V239 will rerun the exact V238R3 denominator:

- date: `2026-05-14`;
- symbols: `XAUUSD`, `JP225`, `GER40`, `US30_cash`;
- profile: `repaired_package_conversion_v3`;
- tick-source lookup enabled with the restored JP225 and GER40 historical
  source ledgers;
- full candidate and packet-sidecar ledgers retained; missed rows compacted.

Success requires zero POI projection, displacement coverage, invalid-finalized
authority, candidate/scorecard missed reconciliation, and executable-binding
transfer defects; atomic final-risk/fillability must remain green; executed
REFUSED/source-gap rows must remain zero. Any changed trade or R must reconcile
to the stricter causal predecision authority validation. This is a bounded
truth-repair proof and does not establish broad market value or total reservoir
conversion.

## 16. V239 Result And V239R2 Compact-Terminal Closure

V239 was exactly behavior-neutral to V238R3: `2469 / 92 / 13 / 7 / 6`
candidate, scorecard, order-event, terminal-order, and trade rows; W/L/F
`3/3/0`; net/gross/final R
`-2.81768013/-2.26948297/-2.26948297`; cash `-$980.11471440`; and zero
added or removed trades. The stricter finalizer validation therefore did not
manufacture improvement through suppression.

The physical verifier reduced the terminal defects but exposed the final two
serialization semantics:

- runtime projected POI truth correctly, but compact missed-ledger writing
  omitted that complete atom on `1894` required rows;
- the six filled displacement instances were correctly absent from `missed`,
  but the verifier did not yet accept `trade` as their terminal surface.

The compact serializer now consumes the same candidate-instance POI projection
helper as full terminal rows. Displacement verification now requires exact
candidate and scorecard parity plus one exact terminal surface, either missed
or trade; missing both still fails. The complete harness/verifier subset is
green at `432 passed`; the later final four-file same-root barrier supersedes
this count at `1325 passed`, with only the unchanged `asyncio_mode` warning.

V239R2 reruns the identical restored denominator. It is expected to remain
behavior-neutral while physically producing `1946/1946` required missed POI
states, terminal displacement coverage for all `314` scorecard instances
(`308` missed plus `6` trades), zero authority/atomicity/transfer defects, and
zero REFUSED/source-gap execution. It remains a bounded truth proof, not broad
economic validation.

## 17. V239R2 Residual And V239R3 All-Terminal Closure

V239R2 restored the compact POI atom exactly: `1946/1946` required missed
rows have POI state and causal lifecycle, with zero required-state gaps. It
remained behavior-neutral at six trades and `-2.81768013R`.

The physical verifier then exposed the last two terminal-form mismatches:

- `47` nonrankable POI rows carried the correct lifecycle reason in the
  canonical blocker-resolution object, but a later missed-row sync rewrote the
  flat primary blocker to a generic selector-materialization alias;
- one selected candidate ended as an unfilled terminal order, which is neither
  a missed candidate nor a filled trade but is still a valid exact terminal
  displacement surface.

The canonical blocker-resolution primary reason, family, source, and
co-blockers now own the flat terminal aliases. Displacement parity now requires
candidate and scorecard agreement plus one exact terminal surface across
missed, unfilled order, or filled trade. Missing all terminal forms still
fails. The integrated scheduler/timewarp/harness/verifier barrier is green at
`1325 passed`, zero failures, with the unchanged `asyncio_mode` warning.

V239R3 reruns the identical restored one-day/four-symbol denominator. Success
requires zero POI precedence defects, all `314` displacement instances bound
to exactly represented terminal surfaces, zero earlier terminal/authority/
atomicity defects, no behavior drift, and no REFUSED/source-gap execution.

## 18. V239R3 Accepted Result

V239R3 is accepted as the bounded terminal-truth checkpoint. Behavior remains
exactly neutral: `2469 / 92 / 13 / 7 / 6` candidate, scorecard, order-event,
terminal-order, and trade rows; W/L/F `3/3/0`; net/gross/final R
`-2.81768013/-2.26948297/-2.26948297`; cash `-$980.11471440`; risk cash
`$2439.92967918`; risk percent `2.45`; expected cost `0.54819716R`.

The physical verifier is green at `ok=true`, issue count `0`:

- POI state/lifecycle bad counts: `{}` with `1946/1946` required missed POI
  rows complete;
- displacement bad counts: `{}` with `313` exact candidate and scorecard
  instances partitioned across `307` missed and `6` order terminals, of which
  `5` also reached trade;
- final-risk/fillability atomicity: `12/12` execution-bound order rows and
  `6/6` trades valid;
- order-executable transfer and scheduler authority bad counts: `{}`;
- executed REFUSED/source-gap rows remain `0/0`.

This closes terminal projection, strict finalizer validation, compact POI
serialization, terminal-form displacement, and blocker-precedence truth. It
does not close economic value: the bounded cohort still loses. The next batch
is causal scheduler/risk-expression/selected-policy/exit loss transfer on this
clean denominator before hostile-five-day and non-hostile regime proof.
