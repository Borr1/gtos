# B7.2 V240 Causal Authority, Value, Lifecycle, And Exit Brief

Generated: 2026-07-12T23:10:00Z

This is the control brief for the next same-root implementation batch. It is
not behavioral proof. Broker mutation, live broker authority, and final
selection remain false; local replay authority remains full.

## 1. Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V239R3_B7_2_TERMINAL_BLOCKER_PRECEDENCE_AND_ALL_TERMINAL_SURFACES_20260514_4SYMBOL_TARGETED`

Window: 2026-05-14, XAUUSD / JP225 / GER40 / US30_cash, repaired package only.

- source / decision / candidate / physical scorecard rows: 28 / 2,208 / 2,469 / 92
- candidate instances present in scorecards: 314
- order events / logical orders / fills / missed: 13 / 7 / 6 / 2,462
- W/L/F: 3/3/0
- gross/final/net R: -2.26948297 / -2.26948297 / -2.81768013
- cash PnL / risk cash / risk percent sum: -$980.11471440 / $2,439.92967918 / 2.45%
- executed cost-refused / source-gap rows: 0 / 0
- missed headline executable R: 0.0; diagnostic missed R: -143.51033091
- stress net R at +0.05/+0.10/+0.20R: -3.11768013 / -3.41768013 / -4.01768013
- Monte Carlo worst drawdown: -3.34698405R

This one-day slice is a bounded repair proof, not a denominator for the global
source-bound reservoir.

## 2. Process State

No replay, pytest, compile, or git mutation process is active. V239R3 is
complete and must not be duplicated. The five read-only audits of immutable
commit `c5b04aa5d` have returned, were reconciled against current code, and are
closed before this changing integration batch.

## 3. Baseline Comparison

| Run | Window | Trades | W/L/F | Net R | Gross/Final R | Cash PnL |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| V89D | hostile 5d | 56 | 41/15/0 | +34.84520454 | +39.93441037 | +$8,178.90660707 |
| V90 | hostile 5d | 51 | 37/14/0 | +28.84201157 | +33.36349114 | +$6,371.80465431 |
| V92 | hostile 5d | 51 | 37/14/0 | +29.35570236 | +33.93212860 | +$6,228.63096022 |
| V237R2 | targeted 3d/5-symbol | 18 | 8/10/0 | +2.13064803 | +3.60123918 | -$1,181.37730315 |
| V239R3 | targeted 1d/4-symbol | 6 | 3/3/0 | -2.81768013 | -2.26948297 | -$980.11471440 |

Windows differ. The older runs are behavioral anchors only; V240 must first
prove the same exact V239R3 denominator and then broaden.

## 4. Current Dirty Surface

Tracked dirt before implementation is only the regenerated
`.context/LIVE_STATE.md` and user-owned `AGENTS.md`. Neither belongs in the
route checkpoint. The implementation batch owns:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- focused scheduler/runtime tests
- denominator-route verifier and verifier tests
- current root-cause map, this brief, and Fable matrix after proof

## 5. Reconciled Frozen Audits

| Lane | Disposition | Current conclusion |
| --- | --- | --- |
| Euclid, executed risk/exit | VALID_OPEN | Main tick oracle omits ordered-tick authority; selected exits remain diagnostic. Final-risk provenance also contradicts its own approvals. |
| James, scheduler/displacement | VALID_OPEN | Missing primary value becomes zero, eligibility is inverted, selection/reallocation ranks are conflated, and guard rejection is misclassified. |
| Darwin, selector/source transfer | VALID_OPEN | Five open-reduced signing rows use drifted floors; 19 source-required rows cannot obtain the appropriate signed surface. |
| Boole, order/lifecycle | VALID_OPEN | A valid passive route is retroactively changed to never-sent by later guarded-market drift, erasing pending lifecycle and changing same-symbol replacement behavior. |
| Parfit, independent verifier | VALID_OPEN | Four fills exceed their recorded dynamic-approved risk; permission/reason tuples conflict; terminal rows bypass integrity checks; verifier coverage is partly vacuous/stale. |

Rejected/deferred policy claims:

- No origin-family allowlist relaxation is justified by this one-day slice.
- No fillability-floor or stop-hazard threshold relaxation is justified.
- Profit-harvest replacement is deferred; existing selected-policy logic is the
  causal preselected exit surface to make authoritative first.
- Close-side all-in broker costs remain a later cost-authority requirement and
  cannot be fabricated from this replay.

## 6. Root-Cause Chain

| Stage | Status | Same-root failure |
| --- | --- | --- |
| source-bound -> candidate | PARTIAL | Supply exists, but source-required and open-reduced rows do not share one immutable signed admission envelope. |
| candidate -> selector | PARTIAL | Canonical quality is present, while package-scoped stale calibration/permission aliases can outrank it. |
| selector -> scheduler | OPEN | Scheduler recomputes drifted floors instead of validating the selector admission contract. |
| scheduler -> risk | OPEN P0 | Missing comparator value becomes zero; rank meanings conflate; finalizer collapses requested/selected/dynamic/final risk. |
| risk -> order | OPEN P0 | Four fills exceed the recorded dynamic-approved ceiling without valid promotion authority. |
| order -> lifecycle | OPEN | Future fallback drift retroactively invalidates an already valid passive route instead of retaining it pending to expiry. |
| lifecycle -> fill | OPEN | Erased pending state changes opposite-side replacement admission and can create a later fill. |
| fill -> exit | OPEN | Tick source and path index are ordered, but the oracle omits the authority atom, so selected-policy terminal R cannot bind. |
| exit -> ledger/verifier | OPEN | Permission/reason tuples, terminal surfaces, risk ceilings, and non-vacuous scans are not fully enforced. |

## 7. Same-Root V240 Batch

Batch: `B7_2_CANONICAL_PREDECISION_AUTHORITY_RISK_LIFECYCLE_AND_ORDERED_TICK_EXIT`

Correctness repairs:

1. Bind one immutable predecision admission/value/fillability/signing contract;
   scheduler validates its exact floors and supports both reduce-risk actions.
2. Preserve distinct requested, selected-cell, scheduler-approved,
   dynamic-approved, promotion-authorized, and final risk values; final risk may
   exceed an applicable ceiling only through a valid signed promotion atom.
3. Keep valid passive-limit authority executable when guarded-market fallback is
   later declined; materialize accepted-pending before terminal path decisions.
4. Propagate ordered-tick source authority into the path oracle and make the
   already-selected execution policy authoritative only on genuine ordered tick
   truth. Evaluate canonical calibration fields before stale package aliases.
5. Make displacement value fail closed when missing, fix eligibility semantics,
   separate selection/reallocation/finalizer rank, and preserve guard terminal disposition.
6. Reconcile current permission/reason/source tuples atomically and extend the
   verifier across risk ceilings, terminal integrity, passive lifecycle, ordered
   tick authority, and non-vacuous current-prefix coverage.

Performance effect is allowed only through these causal repairs. No
date/symbol/session/outcome bucket is introduced.

## 8. Expected Measurable Effect Before Replay

- candidate -> scorecard: preserve the 2,469 denominator; repair exact signing
  disposition for the 24 audited instances without admitting cost/source/session
  failures.
- scorecard -> order: GER40 11:00 must become accepted-pending rather than
  never-sent; other changes require an exact newly valid signed envelope.
- order -> fill: the retained GER40 pending order is expected to expire unfilled;
  the 11:30 opposite-side short must face normal replacement admission. Fill
  count may fall from 6 to 5 through corrected lifecycle ordering, not suppression.
- missed positive/negative R: all diagnostic rows remain visible; terminal
  reasons must move, not disappear.
- trade R: ordered-tick selected-policy binding should change only rows whose
  causal selected exit differs from fixed-target/time-stop. Row-local diagnostic
  ceiling is +2.44942267R versus V239R3 before lifecycle interactions.
- cash/risk: applicable unpromoted risk ceilings should reduce the four
  contradictory fills from 0.50/0.625% to their approved values; normalized R
  should not be flattered by sizing alone.
- cost-refused/source-gap execution remains 0/0.
- full-risk/reduced-risk: every final classification must agree with the signed
  promotion atom and final percentage; no false full-risk labels.

## 9. Proof Decision

The batch helps if focused tests prove all contracts and the exact targeted
successor has zero authority contradictions, preserves full opportunity
accounting, makes ordered-tick selected exits bind, retains valid passive orders
through expiry, and changes trades/R only through those mechanisms.

It fails if any cost-refused/source-gap/off-session/invalid-signature row
executes, a valid passive route remains never-sent due future drift, a final risk
exceeds an applicable unsigned ceiling, or the result improves by deleting
missed opportunities.

It exposes the next deeper flaw if contracts are green but the corrected
selected-policy/lifecycle behavior remains economically negative. Only then is
the hostile five-day and independent-regime proof justified.

## 10. Current Green Barrier And Targeted Launch

The merged implementation snapshot passes `1,522` focused/full touched tests:
`427` allocator/materialization, `807` replay runtime, and `288` denominator
verifier tests. Compile is green. The only warning is the pre-existing unknown
pytest `asyncio_mode` option.

The physical route verifier correctly fails the pre-repair V239R3 artifacts on
the two contracts introduced by this batch: current final-risk/permission atoms
and ordered-tick oracle authority. Those are expected baseline failures, not
current-code failures. V240 must clear them on the exact same 2026-05-14,
four-symbol, repaired-package denominator.

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V240_B7_2_CANONICAL_AUTHORITY_RISK_LIFECYCLE_ORDERED_TICK_EXIT_20260514_4SYMBOL_TARGETED`

## 11. V240 Result And V241 Lifecycle Consumer Proof

V240 completed on the exact V239R3 denominator. Candidate, scorecard, order,
trade, and missed row counts were unchanged at 2,469 / 92 / 13 / 6 / 2,462.
The six common trades improved from -2.81768013R net and 3/3 W/L to
-0.36825746R net and 4/2 W/L. Gross/final R improved from -2.26948297R to
+0.17993970R, cash PnL improved from -$980.11471440 to +$50.20680045, and
risk fell from 2.45% / $2,439.92967918 to 1.20% / $1,199.55316609. No trade
was added or removed. The exact +2.44942267R delta equals the predeclared
row-local selected-policy ceiling: GER40 11:30 improved by +1.96235324R and
XAUUSD 13:00 by +0.48706943R. All six fills now bind ordered-tick authority
hashes and obey their dynamic-approved risk ceilings. Cost-refused and
source-gap executions remain zero.

The diagnostic missed surface changed by -65.19785334R across 259 still-
scoreable rows because selected-policy terminal truth became authoritative;
row count and scoreability did not shrink. This is truth revaluation, not
opportunity suppression.

V240 exposed one remaining same-root lifecycle consumer defect. The signed
GER40 11:00 authority and scheduler envelope both authorize a degraded passive
limit queue, while final order materialization read the demoted mutable order
alias and serialized `route_available=false` / `contract_unmet`. The consumer
now resolves validated signed order authority and atomic execution fillability;
the verifier now rejects any degraded passive release not consumed by the order
route.

V241 is a targeted exact-denominator lifecycle proof, not a global performance
claim. It helps if GER40 11:00 becomes accepted pending then expires unfilled,
the later opposite-side GER40 decision is reconciled through normal pending
replacement authority, no invalid signature/cost/source row executes, and the
V240 selected-policy/risk truth remains intact. It fails if the row remains
never-sent, if the passive release bypasses queue realism, or if opportunity
rows disappear. Any trade-count or R change must be attributable to corrected
pending lifecycle and replacement handling.

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V241_B7_2_SIGNED_PASSIVE_QUEUE_CONSUMER_AND_LIFECYCLE_20260514_4SYMBOL_TARGETED`

## 12. V241 Result And V242 Pending-Replacement Comparator Proof

V241 closes the signed passive-queue consumer defect. GER40 11:00 is accepted
pending and expires unfilled; guarded-fallback contract-unmet rows fall from one
to zero. Candidate and scorecard counts remain 2,469 / 92. Opportunity remains
fully accounted, with one additional missed row because the displaced GER40
short is now diagnostic rather than silently absent.

V241 also exposes the next causal lifecycle defect. The valid signed GER40
11:30 short is materialized as `replace_pending`, has expected net R 1.03162982,
execution fill probability 0.58382349, and fill-adjusted expected transfer about
0.602R. The pending long has expected net R 0.79276772, execution fill
probability 0.66250496, and fill-adjusted expected transfer about 0.525R. The
replacement gate rejects the economically superior short only because its fill
probability is lower. That removes the V240 +0.85797679R GER40 winner, reducing
V241 to five trades, 3/2 W/L, -0.78241354R gross/final, -1.22623425R net, and
-$163.93576435 cash PnL. This is correctness exposure, not accepted performance.

The V242 repair preserves the strict fill-Pareto rule for generic and same-side
replacement. Only signed, broker-cost-passed opposite-side pending collisions
may accept lower fill probability when predecision fill-adjusted expected
transfer is at least as strong as the pending order and the expected-net delta
still passes its configured floor. The gate records both transfer scores,
delta, minimum delta, and the causal tradeoff decision.

V242 helps if the GER40 short is selected through `replace_pending`, the prior
long is released through an immutable pending-release binding, cancel-replace
events are materialized, the same six V240 fills return without recreating the
V240 passive-route contradiction, and all risk/cost/tick-authority contracts
remain green. It fails if the short is admitted without releasing the pending
long, if lower fill is accepted without transfer dominance, or if any unrelated
trade/opportunity disappears.

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V242_B7_2_OPPOSITE_PENDING_EXPECTED_TRANSFER_REALLOCATION_20260514_4SYMBOL_TARGETED`

## 13. V242 Result And V243 Pending-Order Identity Proof

V242 restores the V240 six-trade behavior through the intended lifecycle path:
14 order events, one terminal `cancelled_replaced_by_scheduler_v4` row, one
applied pending replacement, six fills, 4/2 W/L, +0.17993970R gross/final,
-0.36825746R net, and +$50.20680045 cash PnL. Risk remains 1.20% /
$1,199.55316609, cost remains 0.54819716R, selected contract-unmet rows remain
zero, and refused/source-gap execution remains zero. The GER40 11:30 short is
recovered only after the 11:00 long order is cancelled.

The V242 replacement binding reveals an identity inconsistency: the selected
release ID is the simulated pending-order ID, while the exposure-context pending
set contains the predecessor candidate ID because a shared exposure helper
prioritized `trade_id` for both positions and pending orders. The producer now
uses pending/order/ticket identity before trade/candidate identity for pending
exposure. V243 is behavior-neutral proof for that identity repair.

V243 helps if the V242 event and trade counts/R reproduce exactly, the release
binding pending set contains the same simulated order ID that was cancelled,
the binding hash validates, and the lifecycle release verifier has zero issues.
It fails if replacement behavior changes, if candidate IDs remain in the order
release set, or if the verifier cannot bind the cancellation to the selected
replacement.

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V243_B7_2_PENDING_ORDER_IDENTITY_BINDING_20260514_4SYMBOL_TARGETED`

## 14. V243 Result And Route-Certification Barrier

V243 reproduces V242's behavior exactly while closing the pending-order
identity contract. It produced 2,469 candidates, 92 scorecards, 14 order
events, seven logical orders, six fills, and 2,462 missed rows. W/L/F is
4/2/0; gross/final/net R is +0.17993970 / +0.17993970 / -0.36825746; cash
PnL is +$50.20680045; risk cash and risk percent are $1,199.55316609 and
1.20%; broker-calibrated expected cost is 0.54819716R. Stress at an extra
0.05/0.10/0.20R per trade is -0.66825746/-0.96825746/-1.56825746R and the
200-iteration Monte Carlo worst drawdown is -2.24260760R.

The selected replacement release ID, pending exposure set, signed lifecycle
binding, runtime cancellation, and terminal ledger now carry the same
simulated order ID and authenticated binding hash. One pending replacement and
one terminal cancellation are applied; selected contract-unmet rows are zero;
executed REFUSED/source-gap rows are 0/0. Diagnostic missed accounting remains
visible at 609 scoreable rows and -208.70818425R, so the local improvement was
not manufactured by removing missed opportunities.

This remains an exact one-day/four-symbol repair proof. It does not prove the
hostile five-day, an independent regime, broad-history value, final selection,
or global reservoir conversion. The active barrier is route certification:
the builder must select the V243 prefix, the physical route verifier and focused
tests must pass against that prefix, prompt and route audits must remain green,
and the scoped diff must be clean. After certification and bounded storage
cleanup, the next behavioral proof is the unchanged V243 code over
2026-05-13..17, followed by an objective non-hostile regime. Broker/live/final
remain closed.

## 15. V244 Permission-Source And Scorecard-Identity Proof

Route certification against V243 exposed two real ledger-consumer gaps after a
separate Mac cutover source-root repair reduced verifier failures from 74 to 2.
All 13 execution-bound order rows and all six trades had valid signed order
authority, canonical risk, and atomic fillability, but the outer executable
candidate permission lacked its authority-source field. The replace-pending
scorecard carried both canonical instance keys and a valid signed release
binding but did not project the selected candidate ID at top level, so the
verifier could not authenticate current identity from one atomic scorecard
surface.

The same-root V244 batch now makes ledger namespace materialization consume the
signed order authority source when available, with a predecision-derived source
fallback only when no signed source applies. The selected scorecard quality
contract also projects the exact candidate ID alongside its candidate/decision
instance keys. Portable workspace resolution and explicit summary-backed
zero-row ledger omission are included as correctness repairs for the cutover;
they restore the prior 12,684-row M15-grid and 6,374-row reconstructed proxy
surfaces without changing replay policy.

The focused barrier is 1,528 passed, zero failures, and one unchanged pytest
configuration warning. V244 helps only if it reproduces V243's six trades,
4/2 W/L, +0.17993970R gross/final, -0.36825746R net, and +$50.20680045 cash
without added or removed opportunities; all 13 execution-bound order rows and
six trades must carry nonempty executable candidate authority sources; and the
replace-pending scorecard identity must match its signed release payload. Any
behavior delta, missing source, identity mismatch, REFUSED/source-gap execution,
or new verifier class fails the batch.

Target prefix:
`BROAD_LIVE_AS_IF_REPLAY_V244_B7_2_PERMISSION_SOURCE_AND_SCORECARD_IDENTITY_20260514_4SYMBOL_TARGETED`

## 16. V244 Result And Certified Checkpoint

V244 reproduces V243 exactly: 2,469 candidates, 92 scorecards, 14 order
events, seven logical orders, six fills, 2,462 missed rows, 4/2/0 W/L/F,
+0.17993970R gross/final, -0.36825746R net, +$50.20680045 cash PnL,
$1,199.55316609 risk cash, 1.20% aggregate risk, and 0.54819716R
broker-calibrated expected cost. The same-window comparator records zero added
trades, zero removed trades, and zero net-R delta.

All 13 execution-bound order rows and all six filled trades now carry a
nonempty executable-candidate authority source. The replace-pending scorecard
projects the selected candidate ID together with its canonical instance key
and signed release identity. Candidate-instance parity materializes all 2,469
rows. Executed REFUSED/source-gap counts remain 0/0.

The route manifest binds V244 and its parity/flow/comparison artifacts. The
physical route verifier passes with zero issues; focused compile and 1,528
tests pass with one unchanged pytest configuration warning; prompt hardening,
both parent verifiers, and full denominator/parent artifact audits pass.

This certifies the targeted truth checkpoint only. It does not prove hostile
five-day, non-hostile regime, broad-history, final-selection, or live value.
After bounded storage cleanup, the next proof is unchanged V244 code over
2026-05-13..17. Broker/live/final remain closed.

## 17. Bounded Storage Retention Contract Before Hostile Five-Day Proof

Checkpoint commit `a6304e20c` preserves the V244 implementation, focused tests,
route builder/verifier, current control surfaces, parent verification
dependencies, and manifest-bound proof artifacts. The following remain hot and
must not be deleted during this cleanup:

- every V244 raw and compact replay artifact, including parity, flow, comparison,
  trade, order, scorecard, candidate, decision, packet, missed-opportunity, and
  source-universe surfaces;
- the denominator route manifest, verification result, completion audit, prompt
  audit inputs, current root-cause map, this pre-replay brief, and the Fable
  execution matrix;
- the V243-to-V244 behavior comparison and compact predecessor evidence needed
  to establish behavior neutrality;
- source market-data exports, source-bound package inputs, cost inputs, and all
  materializers needed to regenerate the next replay;
- restored parent/Wave D/F/H, synthesis, acceptance, lifecycle, scheduler, and
  VPS-freshness dependencies required by the green parent verifier.

Cleanup is limited to untracked, superseded raw replay ledgers from V235R3,
V237R2, V238/V238R2/V238R3, V239R3, and V240-V243. Candidate, decision,
packet-sidecar, scorecard, and missed-opportunity raw files may be removed after
confirming they are untracked and not referenced by the current V244 manifest.
Compact summaries, trade/order/bucket evidence, comparisons, and current V244
artifacts remain. No source input, tracked file, live evidence, or active route
authority is a cleanup target.

The bounded cleanup removed exactly 50 untracked files totaling
14,762,358,336 bytes, left all 196 current manifest paths present, preserved all
16 V244 replay files, repaired the migrated checkout's repository-local Git LFS
filters, and pruned only unreachable ordinary Git objects. Approximate free
space after cleanup is 40 GiB.

## 18. V245 Hostile Five-Day Pre-Replay Control

No replay, builder, verifier, pytest, or Git process is active. V244 is the
latest completed replay and must not be duplicated. V245 runs unchanged V244
code across the full configured 24-symbol hostile window; this is the first
broad behavioral test after the certified authority, risk, passive lifecycle,
replacement, identity, and ordered-tick exit repairs.

Same-window anchors:

- V89D: 56 trades, 41/15/0 W/L/F, +34.84520454R net,
  +39.93441037R gross/final, +$8,178.90660707 cash PnL;
- V90: 51 trades, 37/14/0, +28.84201157R net,
  +33.36349114R gross/final, +$6,371.80465431 cash PnL;
- V92: 51 trades, 37/14/0, +29.35570236R net,
  +33.93212860R gross/final, +$6,228.63096022 cash PnL;
- V219: 23 trades, 14/9/0, -2.82440031R net,
  -0.79141028R gross/final, +$204.17530212 cash PnL;
- V236: two trades, 1/1/0, -0.92559780R net,
  -0.79425689R gross/final, -$92.57809253 cash PnL.

The older positive anchors are comparators, not automatic truth authority. V245
helps only if it preserves the full 25,006-candidate / 288-scorecard denominator,
materially restores valid scorecard-to-order and order-to-fill transfer beyond
V236, keeps REFUSED/source-gap execution at zero, preserves full missed-positive
and missed-negative accounting, and attributes behavior to causal predecision
repairs rather than suppression. If contracts remain green but value is still
negative, the completed five-day ledgers become the evidence for the next
same-root losing/conversion batch.

Exact command:

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 --end 2026-05-17 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V245_B7_2_HOSTILE_5D_V244_AUTHORITY_CONVERSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID \
  --profiles repaired_package_conversion_v3 \
  --compact-missed-ledger
```

## 19. V245 Result, Root-Cause Map, And Next Proof Barrier

V245 completed successfully; no replay, builder, verifier, pytest, or Git
maintenance process is active. The exact completed prefix is
`BROAD_LIVE_AS_IF_REPLAY_V245_B7_2_HOSTILE_5D_V244_AUTHORITY_CONVERSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.
It is a bounded hostile-window proof, not full-reservoir or live evidence.

### 19.1 Numbers And Same-Window Comparators

V245 materialized 310 source rows, 11,424 decisions, 25,006 candidates, 288
scorecards, 45 order events, 22 terminal orders, 20 fills, and 24,984 missed
rows. W/L/F is 11/9/0. Gross/final/net R is
+2.97415738/+2.97415738/+1.37913341; broker-calibrated expected cost is
1.59502397R; cash PnL is +$107.53831449; risk cash and aggregate risk are
$3,210.87073032 and 3.20%. Twelve fills are passive-queue-confirmed and eight
are source-safe immediate marketable. One order expired unfilled and one was
cancelled/replaced. Executed REFUSED/source-gap rows are 0/0.

At +0.05/+0.10/+0.20R additional cost per trade, net R is
+0.37913341/-0.62086659/-2.62086659. Monte Carlo p50/p05/worst maximum
drawdown is -3.81676154/-6.16433455/-7.23878296R. The positive headline is
therefore real on the calibrated base case but not yet robust to modest
additional cost.

V245 preserves V219's 25,006 candidates and 288 scorecards while using 12 fewer
terminal orders and three fewer fills. Net R improves by +4.20353372R and
gross/final by +3.76556766R, but cash PnL falls by $96.63698763 because risk
falls by 12.05 percentage points. Relative to V236, V245 adds 20 terminal
orders and 18 fills, improves net R by +2.30473121R and gross/final by
+3.76841427R, and improves cash PnL by $200.11640702. This is not a
candidate/scorecard-collapse result.

V89D/V90/V92 remain old optimistic same-window comparators at 56/51/51 trades
and +34.84520454/+28.84201157/+29.35570236R net. They are not current truth
authority. V245 proves that current causal authority transfers beyond V236; it
does not reproduce the older optimistic behavior.

### 19.2 Window-Normalized Transfer

The exact window contains 1,101 package axes. Candidate generation reaches 894
axes (81.19891%); 17 reach scorecard or order presence (1.901566% of generated);
15 fill (88.235294% of scorecard/order axes). Headline replay has 20 trade rows
because axis attribution and replay-trade identity are different declared
surfaces. The exact dated additive source-bound R denominator is zero in this
window; the global 1,249,248.03066685R source-bound reservoir remains diagnostic
and is not the replay denominator.

Candidate-instance projection is exact at 25,006 unique rows. It records 2,402
valid signed predecision candidate instances, of which 2,382 are final-blocked
and 20 are order-bound. Blocker classes are session authority 788, fill realism
675, execution fillability 503, scheduler selection 344, marketable guard 37,
headroom 34, and stop hazard one. Axis-attributed missed opportunity is mixed:
+804.95137893R positive, -2,401.66853978R negative, -1,596.71716085R net.
These are diagnostic axis counterfactuals, not executable headline R.

### 19.3 Behavior Attribution

All 20 fills are reduced-risk; none is full-risk. Seventeen
`open-reduced-risk` fills contribute +3.37787110R net, while three
`reduce-risk` fills contribute -1.99873769R. A blanket full-risk promotion is
rejected: the available counterfactual applies to 12 trades and changes cash
PnL from +$107.53831449 to -$1,719.32108751 while increasing aggregate risk to
8.25%. Risk expression remains a core B7 question, but it must be repaired from
causal selected-cell/scheduler/dynamic-budget/headroom/stop-hazard authority,
not by globally removing caps.

Selected-policy exits add +1.56527613R over raw fixed-target behavior and
profit-harvest adds +2.12657987R. Seven selected-policy stop-loss exits lose
-7.69724045R, but the aggregate exit overlay is helpful. Exit replacement is
therefore not the next automatic patch; any geometry defect requires a
predecision reproducer.

### 19.4 Root-Cause Chain After V245

| Stage | Status | Current evidence |
| --- | --- | --- |
| source-bound -> candidate | PARTIAL | 894/1,101 axes generate. The remaining 207 need exact non-generation attribution; global source-bound R is not a dated additive denominator. |
| candidate -> selector | PARTIAL | Canonical quality passes for all 25,006 projection rows, but 20,564 terminate at selector, dominated by honest cost refusal plus router/session/EV causes. |
| selector -> scheduler | OPEN | 2,592 candidate instances reach scorecards, 23 are selected/order-bound, and 344 signed rows are classified scheduler-blocked. Non-FVG origin families often score but never order. |
| scheduler -> risk | PARTIAL | Reallocation selects one row; 38 probes are quality-blocked. All filled rows remain reduced-risk, with no proof that global full-risk promotion is valuable. |
| risk -> order | PARTIAL | Twenty-three selected/order-bound instances produce 22 terminal orders with zero REFUSED/source-gap execution. Headroom and risk-order-cap blockers remain explicit. |
| order -> lifecycle -> fill | MOSTLY FIXED | 20/22 terminal orders fill; one expires and one is cancelled/replaced. Queue and immediate-marketability classes are explicit. No broad lifecycle collapse is visible. |
| fill -> exit | PARTIAL | Selected exits improve aggregate R, while stop-loss paths remain the dominant loss source. Geometry requires independent causal evidence before change. |
| exit -> ledger/verifier | PARTIAL | Replay/parity artifacts are complete. Two diagnostic consumer defects were found and fixed: path-safe bounded comparison filenames and producer-declared parity-projection resolution. Route certification still must bind V245. |

### 19.5 Current Dirty Patch And Finding Disposition

Behavior code remains at commit `a6304e20c`. Current code changes are diagnostic
only:

- `compare_broad_replay_prefixes.py`: deterministic bounded artifact stems for
  the macOS filename-component limit;
- `analyze_broad_live_as_if_replay_flow.py`: resolve the parity projection from
  the producer summary's declared artifact path;
- focused tests in `tests/test_compare_broad_replay_prefixes.py` and
  `tests/test_build_source_bound_execution_parity.py`.

The comparison test cluster passes 10 tests; the parity projection cluster
passes four. Previously reconciled V237 agents remain incorporated exactly as
recorded in the root-cause map. There is no uncollected current agent return.
The next audit wave must use immutable commit `a6304e20c` plus the exact V245
artifacts; every return will be reconciled once as VALID_OPEN, ALREADY_FIXED,
STALE, DEFERRED, or REJECTED before implementation.

### 19.6 Next Same-Root Batch And Proof Decision

The immediate batch is
`B7_2_V245_FROZEN_SNAPSHOT_RECONCILIATION_THEN_B7_3_OBJECTIVE_NON_HOSTILE_PROOF`.
Independent lanes inspect selector/signed-risk quality, scheduler/origin
transfer and reallocation, order/fill/lifecycle, exit/stop geometry,
parity/evidence semantics, and verifier/Fable acceptance. Behavior code remains
frozen during the wave. A finding is implemented only with an exact current
reproducer; related producers, consumers, ledgers, tests, and verifier checks
must be patched as one coherent root batch.

If no hard truth defect remains, no hostile-window tuning is justified. The
next behavior run is Fable B7.3: unchanged code and profile over the full
configured 24-symbol 2026-06-01..05 objective non-hostile window, compared
same-window against V104/V110B. It must report candidate -> scorecard -> order
-> fill transfer, missed positive/negative R, added/removed trades, risk tiers,
fill realism, expiry, cost/source execution, stress, and Monte Carlo.

The batch helps if V245 route verification is green, the immutable audit finds
no unclosed hard contract defect or closes every reproduced one with focused
proof, and B7.3 shows structurally consistent authority without opportunity
collapse. It fails if an audit claim is patched without reproduction, if
REFUSED/source-gap rows execute, or if performance improves by suppression or
outcome-fitted risk promotion. A negative B7.3 with green truth contracts
exposes the next cross-regime economic root batch; it does not justify returning
to May-only tuning. Broker/live/final remain false.

## 20. V245 Route-Truth Reconciliation Before B7.3

No GTOS replay, builder, verifier, or test process is active. The V245 replay is
complete and must not be duplicated. Its behavioral numbers and same-window
comparators remain exactly those in section 19.

The V245 route verifier selected the correct producer but exposed five current
contract failures. Exact artifact checks reconcile them as one same-root batch:

1. 1,210 missed rows pass the passive entry-queue subcontract but lack complete
   ordered-tick trade-path authority. Queue admission and terminal execution are
   different stages; the scanner incorrectly equates them.
2. POI source-state rows are exactly one-to-one by candidate, POI, state hash,
   and lifecycle hash. The verifier joins an inner source snapshot time while
   candidate identity correctly uses the outer replay decision. The producer
   must preserve both times explicitly.
3. One XAGUSD diagnostic immediate-marketable row is correctly non-executable
   for ordered-tick source gap, but generic blocker precedence promotes a
   cap-only stop-hazard sizing reason into a terminal stop-hazard blocker.
4. Two GER40 lifecycle order events belong to one top-level selected instance.
   That instance has no finalizer probe because probes cover only applicable
   reallocation decisions; the scanner incorrectly requires global probe
   membership.
5. One JP225 signed open-reduced passive order is accepted then expires. Its
   fallback envelope is marked not applicable because finalizer risk is
   temporarily labelled `trade`, even though immutable signed selector
   authority is open-reduced and the final runtime action is open-reduced.

The implementation batch changes the shared blocker taxonomy, finalizer order
preflight, decision-ledger POI projection, and their verifier consumers/tests.
Expected candidate, scorecard, trade, R, cost, and risk counts are neutral. The
JP225 envelope may change only its explicit passed/degraded/blocked lifecycle
classification; it must not manufacture a fill or erase missed opportunity.
Executed REFUSED/source-gap rows must remain zero.

Proof order is compile plus focused component/runtime/verifier tests, followed
by the smallest targeted JP225/XAG/POI proof because fallback-envelope
applicability is behavior-producing. A broad replay is not authorized merely
because these patches land. The batch helps only if all five contracts close
without suppressing rows, weakening cost/source authority, inventing probes, or
rebinding source time as future data. Broker/live/final remain false.

## 21. V247 Signed Order-Policy Lifecycle Authority Pre-Replay Brief

Generated UTC: 2026-07-13T11:53:00Z.

### 21.1 Current Replay And Process State

No GTOS replay, builder, verifier, or pytest process is active. V245 remains the
latest completed broad replay and must not be duplicated: 25,006 candidates,
288 scorecards, 45 order events, 22 terminal orders, 20 fills, 24,984 missed,
11/9/0 W/L/F, +2.97415738R gross/final, +1.37913341R net,
+$107.53831449 cash PnL, 3.20% aggregate risk, and zero executed
REFUSED/source-gap rows. V89D/V90/V92 remain historical optimistic same-window
comparators at 56/51/51 fills and +34.84520454/+28.84201157/+29.35570236R net;
they are not current truth authority.

V246 is the newest completed targeted proof:
`BROAD_LIVE_AS_IF_REPLAY_V246_B7_2_TERMINAL_ORDER_AND_GENERATION_TIME_TRUTH_20260513_JP225_XAGUSD_TARGETED`.
It contains 597 candidates, 92 scorecards, three order events, one terminal
order, zero fills, and 596 missed rows. It closed XAGUSD blocker precedence and
POI instance/source-time truth, but exposed a downstream JP225 consumer leak:
preflight recognized immutable signed `open-reduced-risk` authority while late
order and lifecycle routing recomputed from mutable `risk_decision=trade`.

### 21.2 Dirty Patch And Finding Reconciliation

The active behavior patch is in
`src/research_infra/v4_timewarp_simulated_live_research_loop.py`, with shared
blocker taxonomy in `src/components/order_blocker_precedence.py`, verifier
consumers in the route verifier, and focused tests in the POI, runtime, and
verifier suites. Route builders/analyzers and current route summaries remain
dirty from prior producer work. Control files are dirty by design. `AGENTS.md`,
`.context/LIVE_STATE.md`, generated proxy ledgers, and unrelated existing dirt
remain unstaged.

No subagent return is uncollected. All immutable V245 audit findings were
reconciled once: the five reproduced findings are incorporated into the
terminal-order/generation-time batch; stale intermediate counts are rejected;
later economic risk/exit questions remain deferred to their Fable dependency.
No new audit wave is authorized before the targeted proof is parsed.

### 21.3 Current Root-Cause Chain

| Stage | Status before V247 | Current evidence |
| --- | --- | --- |
| source-bound -> candidate | PARTIAL, unchanged | V245 reaches 894/1,101 package axes; V247 is not a reservoir proof. |
| candidate -> selector | PARTIAL, unchanged | Cost/session/EV refusal remains scoreable and non-executable. |
| selector -> scheduler | PARTIAL, unchanged | The local defect is action consumption after signed selection, not rank tuning. |
| scheduler -> risk | FIXED for local truth | Mutable finalizer risk and immutable signed selector action are preserved separately. |
| risk -> order | CODE-FIXED, proof open | One shared resolver supplies signed order-policy action to preflight and late routing. |
| order -> lifecycle -> fill | CODE-FIXED, proof open | Passive queue, fallback envelope, replay metadata, and terminal rows consume the same action authority. |
| fill -> exit | OUT OF TARGETED SCOPE | V247 must not fabricate a fill; no exit policy is tuned. |
| exit -> ledger/verifier | CODE-FIXED, proof open | Mutable, signed, and effective action plus authority hash and canonical queue aliases are projected. |

Already fixed in code: shared signed-action resolution, invalid-envelope
fail-closed behavior, preflight consumption, late order/queue/soft-envelope
consumption, and terminal provenance projection. Partially fixed: V245 route
truth remains bound to its old producer rows. Open: targeted V247 producer
proof, then V245 producer regeneration/certification and B7.3 objective-regime
evidence. Newly exposed: none beyond the V246 late-consumer drift addressed by
this batch.

### 21.4 Same-Root Batch, Patch Types, And Expected Effect

The highest-leverage batch is
`B7_2_SIGNED_ORDER_POLICY_ACTION_AUTHORITY_END_TO_END_TARGETED_PROOF` across the
runtime producer/consumers, order metadata, terminal ledger projection,
blocker taxonomy, verifier scanners, and focused tests. This is primarily a
correctness repair; ledger fields are diagnostic proof surfaces with real
runtime consumers; no performance gain is expected from the two-symbol slice.

Compilation passed. Five direct signed-action tests, 20 adjacent
open-reduced/preflight/finalizer tests, and the 1,127-test POI/runtime/verifier
barrier passed with one unchanged unknown `asyncio_mode` warning.

Expected V247 effect before replay:

- candidate -> scorecard and scorecard -> order transfer remain 597 -> 92 ->
  one logical terminal order;
- order -> fill remains zero unless current ordered ticks independently prove a
  different honest result;
- missed positive/negative rows and values remain visible; no opportunity is
  suppressed;
- trade count, net/gross/final R, cash PnL, and W/L/F remain zero in this
  bounded slice;
- executed REFUSED/source-gap rows remain zero;
- there is no filled full-risk/reduced-risk distribution, but JP225 records
  mutable `trade` separately from valid signed/effective
  `open-reduced-risk`;
- JP225 pending and expired rows carry canonical passive-limit queue authority
  plus a valid consumed degraded fallback envelope;
- XAGUSD remains an ordered-tick source-gap diagnostic row.

V247 helps if all action/provenance/queue/envelope fields agree without a
fabricated fill, count loss, cost/source weakening, or POI time regression. It
fails if signed action is lost again or any non-executable row fills. A green
V247 authorizes regeneration of the affected V245 producer artifacts and route
certification; it does not prove economic performance or total reservoir
conversion. A truth-green but different JP225 lifecycle result exposes an
ordered-tick/lifecycle question that must be explained from exact data before
policy tuning. Broker/live/final remain false.

## 22. V248 Terminal-Binding Alias Consumer Pre-Replay Brief

Generated UTC: 2026-07-13T12:07:53Z.

V247 completed with the exact V246 denominator: 597 candidates, 92 scorecards,
three order events, one terminal order, zero fills, and 596 missed rows. Added
and removed candidate identities are 0/0; added and removed missed identities
are 0/0. JP225 now preserves mutable `trade`, valid signed and effective
`open-reduced-risk`, all three passive-queue aliases, and a valid
`degraded_to_passive_limit_queue` envelope through honest expiry. XAGUSD
retains the ordered-tick source-gap fill-realism blocker. Across 184 POI
generation decisions and 15,757 dispositions, partition, instance-time, and
future-source-time failures are all zero.

The route-shaped fallback, stop-hazard, and queue scanners are green. The
order-executable transfer scanner exposes one exact JP225 scorecard defect. The
row already has `package_replay_terminal_binding_status=terminal_order_bound`
and the exact canonical terminal order ID, but final transfer normalization
looks only for direct simulated/package-bound IDs and direct order status. It
therefore clears the binding and reports `unbound_without_final_blocker`.
Warnings produced by intentionally passing the empty trade ledger to the
non-vacuous POI scanner and all missed rows to the order/trade-only path scanner
are rejected as incorrect scanner invocation, not producer defects.

The whole same-root repair is in the central transfer resolver: consume
canonical terminal-bound order and trade aliases and recognize
`terminal_order_bound`/`terminal_trade_bound` after exact terminal
reconciliation. Signed order-executable authority is still required, so this
cannot promote an unsigned row. Production and focused tests compile; four
direct neighboring tests pass; the full POI/runtime/verifier barrier is 1,129
passed with one unchanged `asyncio_mode` warning. Applying current code to the
exact V247 scorecard in memory yields `order_bound`, its real order ID, and no
final blocker.

V248 is the same one-day JP225/XAGUSD slice with prefix
`BROAD_LIVE_AS_IF_REPLAY_V248_B7_2_TERMINAL_BINDING_ALIAS_CONSUMER_20260513_JP225_XAGUSD_TARGETED`.
Expected candidate, scorecard, order, missed, trade, R, cash, W/L/F, and risk
counts are exactly neutral. JP225 must retain the V247 action, queue, envelope,
and expired-order truth while its scorecard becomes `order_bound`. XAGUSD and
POI truth must remain unchanged. Executed REFUSED/source-gap rows stay zero.
The batch helps only if route-shaped transfer/fallback/queue/stop scanners are
green without a fabricated fill or lost opportunity. A green V248 closes this
targeted producer/consumer chain and permits bounded storage recording before
V245 regeneration; it is not economic, broad-history, reservoir, final, or live
proof. Broker/live/final remain false.

## 23. V249 Compact Hostile Five-Day Producer Regeneration

Generated UTC: 2026-07-13T12:19:00Z.

V248 is accepted as the bounded signed-action, passive lifecycle, terminal
binding, blocker-precedence, and POI-time proof. It is exactly neutral to V247
at 597 candidates, 92 scorecards, three order events, one expired terminal
order, zero fills, and 596 missed rows; candidate and missed added/removed
identities are 0/0. The JP225 scorecard now resolves `order_bound` to the exact
terminal order ID. All route-shaped scanners are green; only the intentional
empty-trade non-vacuity conditions remain in this zero-trade slice.

No replay, builder, verifier, or pytest process is active. The bounded storage
checkpoint protects complete V245 and V248 families, preserves V246/V247
summaries plus a per-file hash manifest, removes only 22 listed untracked raw
JSONL files, and leaves 19,559,657,472 bytes free. Protected V245/V248 hashes
are unchanged.

The next batch is the single full configured 24-symbol 2026-05-13 through
2026-05-17 replay:
`BROAD_LIVE_AS_IF_REPLAY_V249_B7_2_HOSTILE_5D_V248_SIGNED_ACTION_TERMINAL_BINDING_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.
It uses `repaired_package_conversion_v3`, the full decision grid, tick-source
resolution, compact missed serialization, a complete compact candidate-index
ledger instead of the redundant multi-gigabyte full candidate packet ledger,
and no duplicate packet-sidecar ledger. Summary candidate counts and every
candidate identity remain materialized; this is storage compaction, not
top-N narrowing or opportunity suppression.

V245 is the exact same-window baseline: 310 source rows, 11,424 decisions,
25,006 candidates, 288 scorecards, 45 order events, 22 terminal orders, 20
fills, 24,984 missed, 11/9/0 W/L/F, +2.97415738R gross/final,
+1.37913341R net, +$107.53831449 cash, 3.20% aggregate risk, 0/20
full/reduced-risk fills, and zero executed REFUSED/source-gap rows. Because the
V248 changes are truth consumers, V249 is expected to be behavior-neutral.
Any trade, R, risk, order, fill, expiry, or opportunity delta must bind to an
exact corrected candidate instance and terminal path.

V249 helps if candidate-index count and identities preserve the full 25,006
surface, route-shaped signed-action/terminal-binding scanners are empty,
REFUSED/source-gap execution remains zero, and no behavior moves without exact
attribution. It fails if compact serialization loses proof, suppresses rows,
or changes behavior through weakened authority. After completion, parse raw
numbers and V245 identity deltas, then run flow/parity, builder, physical
verifier, prompt hardening, artifact audit, compile/tests, and diff check. Do
not start B7.3 until the V249 route is certified. Broker/live/final remain
false.

## 24. V249 Completed Evidence And Route-Certification Brief

Generated UTC: 2026-07-13T14:48:06Z.

V249 completed once over the full configured 24-symbol hostile five-day
surface. No replay process remains active. It preserved the exact V245
denominator: 310 source rows, 11,424 decisions, 25,006 candidates, 288
decision-level scorecards, 45 order events, 22 terminal orders, 20 physical
trades, and 24,984 missed rows. Candidate, missed, scorecard, order, and trade
identity sets are unchanged; added and removed trades are 0/0.

Physical behavior is 11/9/0 W/L/F, +2.75652827R gross/final,
+1.16150430R net, +$201.14669730 cash, $6,994.15658020 risk cash, 6.95%
aggregate risk, and 1.59502397R expected cost. Ordered-tick headline authority
is 18 trades at 10/8/0 and +0.28044419R net. Two M1-only physical trades remain
visible as diagnostics at +0.88106011R net rather than being silently removed.
Six physical fills express full risk and fourteen reduced risk.

Relative to V245, physical gross/final/net R changes by -0.21762911R while
physical cash increases by $93.60838281 and aggregate risk by 3.75 percentage
points. Entries, stops, targets, fills, exits, and trade identities do not
change. Ten common rows change R because signed sizing changes broker volume
quantization; this is a risk-expression truth change, not selection or fill
suppression.

The compact candidate index is now proven as the authoritative parity source.
The projection contains 25,006 exact unique candidate-instance rows, zero
duplicates, zero out-of-window or out-of-profile rows, and exact selected-
prefix binding. Candidate / scorecard-present / scheduler-selected /
order-present / trade-present / missed-present counts are
25,006 / 2,592 / 23 / 23 / 20 / 24,984. The 288 physical scorecard rows are
decision-level scheduler packets whose preserved option traces cover 2,592
distinct candidate instances; this is not candidate-ID fan-out.

V249 is not stress robust: ordered-tick headline stress at +0.05/+0.10/+0.20R
per trade is -0.61955581/-1.51955581/-3.31955581R, and Monte Carlo worst
drawdown is -6.42886010R. This result neither proves the full reservoir nor
opens final/live authority.

The current same-root checkpoint is certification only. Rebuild the route
bound to V249, run the physical verifier and its authority/identity/risk/cost/
fillability/lifecycle/terminal/projection scanners, run prompt hardening and
artifact audits plus compile/focused tests/diff check, and commit the scoped
checkpoint. A green result advances unchanged code to B7.3 independent-regime
proof; a scanner failure must be reproduced against the exact V249 artifact
before patching. Broker/live/final remain false.

## 25. V249 Route Certification Closure And B7.3 Handoff

Generated UTC: 2026-07-13T16:17:53Z.

The V249 route is physically certified. The canonical builder regenerated the
route with the exact V249 prefix and now binds both
`repair_compact_candidate_index_poi_state.py` and the exact
`*_CANDIDATE_INDEX_POI_REHYDRATION_RESULT.json` proof. It also resolves the
macOS-bounded V249-vs-V245 comparison by its structured `repair_prefix` and
binds both the comparison summary and behavior dossier. The physical verifier
completed at `2026-07-13T16:50:42Z` with `ok=true`, `issue_count=0`, and no
POI-state bad counts. Prompt hardening, route and parent artifact audits, and
parent verifiers are green. The integrated POI/runtime/materialization/bridge/
verifier barrier is 1,390 passing tests with one unchanged unknown
`asyncio_mode` warning.

The compact-index repair is exact and replay-neutral: all 14,517 POI-required
candidate instances now retain atomic POI state and lifecycle lineage; 14,223
previously omitted projections were recovered from exact terminal candidate-
instance joins; identity order digest is unchanged; and identity/lineage
conflicts are zero. The verifier also reconciles 20 physical trades separately
from the 18 ordered-tick headline trades instead of treating diagnostics as
headline authority. No candidate, scorecard, order, fill, missed row, trade
identity, or replay result changed.

Disposition: B7.2 is DONE and route-certified for this hostile-window proof.
It is not stress robust, broad-history proof, final selection, or live proof.
The next dependency-safe batch is B7.3: run unchanged V249 behavior code and
`repaired_package_conversion_v3` over the full configured 24-symbol
2026-06-01 through 2026-06-05 independent regime, compared against same-window
V104/V110B artifacts. Required metrics remain the full Fable set: physical and
ordered-tick headline trades, net/gross/final R, cash PnL, W/L/F,
candidate-to-scorecard-to-order-to-fill axes, missed positive/negative R,
added/removed trades and causal reasons, full/reduced risk with tier causes,
cost-refused/source-gap execution, expiry/unfilled reasons, blocked winner and
loser counterfactuals, stress/Monte Carlo, and fill-realism class split.

B7.3 helps only if the unchanged system preserves truth contracts and value
without opportunity collapse, with a structurally consistent full/reduced-risk
distribution relative to B7.2. It fails if improvement is trade suppression,
missed positive R balloons without scoreable causal reasons, REFUSED/source-gap
rows execute, or window-specific configuration changes are introduced. A
truth-correct but economically weak result exposes the next B7 root issue; it
does not authorize hostile-window outcome tuning. Broker/live/final remain
false.
