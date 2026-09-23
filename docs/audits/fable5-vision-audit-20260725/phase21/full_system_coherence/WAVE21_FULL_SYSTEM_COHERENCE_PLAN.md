# Wave 21 full-system coherence plan

Status: `OWNER_APPROVED_ACTIVE`

Approved by Borhen: 2026-08-09

Integration branch: `wave21/full-system-coherence-20260809`

Starting commit: `c994eb564c3cb97f1498ea7449dcd620192a91dd`

## Objective

Make the trading decision chain coherent and economically useful from raw market state to final
portfolio result, then determine which sleeves and candidate families deserve risk. The work must
answer, with exact examples and counts:

- whether each emitted broad candidate matches its stated family and, only when source-owned, its
  sleeve; W7-native sleeve membership is assessed separately and is never fabricated from a broad family;
- whether a professional trader would recognize the setup, invalidation, target, timing, and entry
  intent as coherent at decision time;
- whether Selector keeps the stronger candidates and rejects the weaker ones for the right reasons;
- whether Scheduler, risk, order construction, fill/lifecycle, exits, costs, and accounting preserve
  or corrupt that decision;
- where every promising rejected candidate and every poor selected trade diverged;
- which sleeves are positive, repairable, regime-specific, research-only, or unsupported on unseen
  evidence;
- how the broad research graph and the W7-native/live graph differ, without transferring authority
  between them.

Profitability is the mission. Evidence is kept only when it changes a decision, finds a defect, or
makes the next experiment reproducible. This route will not build a second architecture around the
existing architecture.

## Current facts that control the start

These are established on the starting commit and will be rechecked rather than rediscovered:

- Raw generation is alive. The three-day repaired run emitted 23,309 candidate occurrences; the
  final one-day run conserved 8,284 occurrences and produced 11 orders, nine fills, two targets,
  four stops, two time-stops, and one ordered-tick-dependent terminal.
- `not_filled_no_trade = 6,563` was an entry-not-touched lifecycle result, not 6,563 cost rejects.
- The cost model no longer substitutes a flat numeric fallback for an incomplete four-component
  packet. Valid zero commission remains zero; missing authority remains nonnumeric.
- The original 0.15R total hard cap was too strict. Complete-packet bounds are now 0.35R spread and
  0.45R total, while the general Selector quality ceiling remains 0.20R.
- The immediate-marketable LIMIT ceiling remains 0.10R: a frozen two-day 0.10R-versus-0.20R
  end-to-end comparison changed 16,662 identical candidates and made the looser arm 4.85357727R
  worse on scoreable modelled net proxy.
- Positive headroom is allocated: a valid 2.0% request with 1.5% available receives 1.5%; zero
  headroom still refuses.
- The stale XAUUSD SHORT displacement family-root veto is repaired. Later XAU candidates were then
  blocked by the separate same-symbol post-loss rule, not by cost or the old alias defect.
- Candidate generation, family supply, and the ten broad families were not killed by these repairs.
- The current broad results are offline `research_timewarp` engineering comparators. They are not
  broker-fill truth or W7/live authority. Twenty of 24 symbols in the held broad window lack
  ordered bid/ask ticks.
- W7 is a separate native graph. Its compatibility fields named Selector/Scheduler are not shared
  V4 decisions and will never be counted as such.

## The shortest causal route

### 1. Freeze the baseline and acceptance rules

Bind the starting commit, exact source bytes, config/profile, source window, expected symbol/session
slots, and current outputs. Freeze and hash the development and never-opened decision estates now,
including prior-access status, stopping rule, and multiplicity unit. Record R2-bound edits as a forward
seal break; do not claim continuity from the old seal. Use identical parent/current test arguments and
compare failure identities.

No threshold or sleeve-policy search starts before the raw candidate and stage trace is trustworthy.

### 2. Close source-to-candidate truth

Use the existing raw loader and generator, not prepared candidate packs. Before generation, reject or
classify stale/future/malformed bars using the smallest available causal completion proof. Preserve
every expected decision slot, including source gaps and genuine zero-emission slots.

Define source slots by source role, symbol, timeframe, parent-row/decision ordinal, and source estate or
schedule authority. Bind every timeframe and cross-asset input the generator actually consumes. For every
emitted occurrence, retain a stable lineage plus deterministic emission ordinal and the source-safe facts
required to reproduce it: symbol, side, decision time, family, timeframe, geometry, source role, and
transform. Conserve source slots, emitted occurrences, Scheduler options, and executions separately.
Do not invent historical broker intent, queue, acknowledgement, or deal state from price movement.

Acceptance: exact raw generator call counts; no prepared substitution; no arbitrary cap; no silent
drop; every expected slot ends as source-terminal, zero-emission, or one-or-more candidate occurrences.

### 3. Audit family and professional setup quality

Before reading outcomes, draw a stratified, outcome-blind review set covering every emitting family,
side, symbol class, session, pretrade cost band, and Selector action. Do not stratify or choose this set by
target, stop, time-stop, realized holding, or final cost. Review chart context and the causal input state
only. A separate, explicitly outcome-aware diagnostic set may later trace downstream failures, but it
cannot validate setup quality. Each predecision occurrence receives a compact judgment:

- family rules satisfied or violated, with the first failing predicate;
- setup geometry coherent or malformed;
- stop at a defensible invalidation or mechanically too tight/wide;
- target plausible for the setup and horizon;
- source-owned entry reference and timing coherent, without assigning final order type or TIF;
- context/session/regime aligned, mixed, or contradictory;
- professional disposition: trade, reduce, wait, reject, or not evaluable;
- exact implementation stage to repair if the system disagrees.

The sample is for human-readable inspection; the full candidate population remains in the mechanical
ledger. Any discovered predicate defect is then measured across the full population before editing.

### 4. Trace Selector through the final decision

Run the actual stages in causal order over a bounded raw window:

`raw source -> market state -> generator -> source-safe transform/final candidate fingerprint ->`
`separately hash-bound proposed-order/geometry/outcome context -> Selector -> one window Scheduler ->`
`risk/headroom -> exact proposed-order materialization with approved size -> causal fill/no-fill ->`
`exit/lifecycle -> post-lifecycle component cost -> accounting`

The candidate fingerprint remains order-agnostic. The proposed-order context is a separate causal
packet, fixed before Selector, that preserves the source-owned MARKET/LIMIT intent and absolute
entry/stop/target, risk-distance, expiry, and horizon. Scheduler and risk may change only approved
risk percentage and size within headroom. They may not rewrite those policy or geometry atoms.

Use the existing compact stage/event surfaces. Add only fields needed to answer a decision. Preserve
one terminal row per occurrence and explicit predecessor joins; do not create a new general-purpose
truth framework.

For each candidate record:

- Selector action, score components, and first decisive reason;
- Scheduler rank, competition set, duplicate handling, occupancy and selection reason;
- requested and approved risk, remaining headroom, and any partial allocation;
- final order geometry and whether it changed any upstream decision input;
- submission boundary, fill/no-fill evidence class, exit, elapsed holding, and terminal reason;
- pretrade estimate separately from post-lifecycle cost and final net result; final economics bind a
  validated fill/exit gross-before-component-cost basis, with embedded physical spread attributed but
  never deducted a second time;
- counterfactual opportunity diagnostics for every nonselected or refused occurrence under one frozen
  hypothetical policy, kept distinct from actual portfolio execution; unfilled actual orders retain
  actual terminal attribution.

Any post-selection mismatch in the immutable proposed-order, geometry, cost-policy, or outcome-model
atoms is a causal-graph failure and terminates not evaluable. It is never patched, accepted by
last-value-wins, or recursively rerun. Normal account PnL updates affect only later decision windows in
the single causal pass. This narrower rule supersedes the earlier generic fixed-point wording after the
cleared `OUTCOME_AUTHORITY_PREREGISTRATION_V1` proved that all verdict-moving order geometry can and must
be fixed before Selector.

### 5. Diagnose before changing policy

Every disagreement maps to its first causal owner:

| Observed failure | First owner |
|---|---|
| Future, stale, mixed-timebase, or incomplete source | loader / market-state boundary |
| Family predicate or geometry invalid at emission | generator / sleeve |
| Valid candidate misidentified or joined to another occurrence | identity / lineage |
| Strong candidate rejected or weak candidate admitted | Selector |
| Inferior winner, duplicate inflation, or lost opportunity | Scheduler |
| Valid opportunity discarded despite positive headroom | risk allocation |
| Final geometry no longer matches the selected setup | order construction |
| Wrong side, time, or causal quote used | fill / lifecycle |
| Cost missing, doubled, forecast reused as realized, or wrong broker/symbol | cost |
| Correct flow but negative unseen expectancy | sleeve / family policy |
| Research behavior differs from what can trade live | graph divergence |

Repair a stage only after reproducing its disagreement on concrete rows. A change must name the
candidates it should alter and the metric that will decide whether it helped.

### 6. Run unseen comparisons and decide sleeves

Use the development and never-opened sets frozen in step 1. Compare one causal change at a time. Preserve
identical source opportunity keys and full terminal populations across arms.

Measure by family, sleeve, symbol, side, session, regime, and cost band:

- emissions, Selector passes, Scheduler selections, approved risk, orders, fills, and terminals;
- gross R, each cost component, net R, uncertainty, drawdown, concentration, and activity;
- selected-versus-rejected ex-ante quality plus explicitly outcome-aware rejected-winner, selected-loser,
  and replacement diagnostics; ex-post outcome alone never proves a bad decision;
- no-fill and time-to-fill behavior separately from rejected behavior;
- equal-risk selection quality separately from sizing value.

Each broad family receives one of five dispositions below. Each W7-native sleeve receives a separate
native-graph disposition; broad-family evidence does not manufacture W7 sleeve authority:

1. `KEEP` — coherent and positive on the relevant unseen evidence;
2. `REPAIR_AND_RETEST` — a reproduced implementation defect explains the result;
3. `REDUCE_OR_CONDITION` — edge exists only in a source-bound regime or risk expression;
4. `RESEARCH_ONLY` — mechanism is useful but present validation is insufficient;
5. `RETIRE_CURRENT_FORM` — coherent flow is negative and no same-class causal repair remains.

Retiring a current form preserves any useful feature, veto, inverse signal, or successor hypothesis.
It does not erase the underlying market intelligence.

### 7. Reconcile with W7 and live truth

Run W7 only through its native graph:

`native sleeve generator -> admit_and_size -> book router/risk -> execution`

Finish the current source-cell and coverage audit; any supported missing source makes the affected
headline not evaluable while partial numbers remain diagnostics. Modelled H4 quote/lifecycle results
remain modelled. Historical account/governor/lot/deal state remains not evaluable unless directly
captured.

Publish a divergence matrix that states which broad conclusions transfer as mechanics and which do
not transfer to W7/live. No compatibility packet is promoted into shared Selector/Scheduler authority.

## Parallel work ownership

The orchestrator owns the integration branch and final decisions. Agents work in isolated branches or
read-only lanes with one owner per write surface:

- source chronology, candidate identity, family fidelity;
- Selector decision quality;
- Scheduler, competition, risk and headroom;
- quote/fill/lifecycle and missing-source acquisition;
- cost and final accounting;
- W7-native replay and live divergence;
- minimal full-flow integration;
- professional outcome-blind trade review;
- independent falsification;
- test/LFS/R2/integration verification;
- session and artifact intelligence.

No agent may resurrect an uncommitted large framework or duplicate a shared contract merely because it
already exists in another worktree. Reuse a small, cleared implementation; otherwise re-derive the
simplest behavior from the current baseline.

## Stop rules against overengineering

- No new schema, receipt, or verifier unless an existing structure cannot express a decision-critical
  fact and the new field changes a named decision.
- No full-suite or long replay while a focused behavioral probe can isolate the root.
- No concurrent heavy replay arms on this 16 GB host.
- No threshold search after a frozen stopping rule fires.
- No relaxing a gate merely because it blocks many rows; examine the quality of blocked and admitted
  rows first.
- No interpreting missing evidence as zero, a loss, a no-op, or a sleeve failure.
- No accepting a blocker while an in-scope source, repair, or bounded experiment remains.
- No live/VPS/config/token/arming/risk-dial/broker mutation in this route.

## Completion criteria

This plan is complete only when:

1. A bounded raw run traverses the actual graph and conserves every expected slot and occurrence to a
   terminal disposition.
2. Candidate/family fidelity and professional setup quality are reviewed outcome-blind and every
   material mismatch has a causal owner.
3. Selector, Scheduler, risk, order, fill, lifecycle, cost, and accounting decisions are traceable on
   both winners and losers, including promising rejected candidates.
4. Every reproduced same-class defect is repaired and behaviorally tested, or has an exact source or
   capture requirement.
5. Frozen unseen A/Bs determine whether each behavior change improves the complete portfolio rather
   than an isolated row.
6. Every active sleeve receives an evidence-backed disposition and the strongest honest economics.
7. Broad and W7-native conclusions remain separate and the live divergence is explicit.
8. Parent/current failure-set A/B, deterministic reruns, source hashes, R2 impact, sparse/LFS, secret,
   and oversized-blob checks pass.
9. Scoped commits are integrated and pushed; live activation remains a separate owner decision after
   the evidence supports it.

The final report answers plainly: whether edge remains, which families supply it, which good candidates
the system takes or misses, why the bad trades pass, where the chain breaks, what was repaired, which
sleeves should change, what remains unknown, and the exact next activation or research action.
