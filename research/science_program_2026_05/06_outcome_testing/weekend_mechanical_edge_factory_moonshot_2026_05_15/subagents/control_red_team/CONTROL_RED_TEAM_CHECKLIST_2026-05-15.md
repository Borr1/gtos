# Mechanical Challenger Control Red-Team Checklist

Date: 2026-05-15
Worker: D
Scope: weekend mechanical edge factory adversarial controls and overfit red-team design
Evidence class: `MECHANICAL_CHALLENGER_CONTROL_RED_TEAM_DESIGN_ONLY`

Safe flags:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Boundary

This artifact is a reusable control design for mechanical challengers. It does not score a challenger, open outcome review, promote a rule, change live behavior, call AI/API/vendor services, touch broker/order/account/deal/position evidence, or edit prompt/config/risk/safety/execution/selector/canary surfaces.

The parent should treat every sprint challenger as one of four evidence classes until proven otherwise:

- `DESCRIPTIVE_DIAGNOSTIC`: useful market intelligence only.
- `NEUTRAL_TARGET_MOVEMENT`: target/path movement measured without trade construction, R, fills, or costs.
- `MECHANICAL_STRATEGY_PROJECTION`: a frozen entry/exit/risk model with synthetic fills and explicit costs, still not broker-realized.
- `PROMOTION_CANDIDATE`: forbidden inside this sprint unless a separate promotion dossier is opened and accepted.

READY8/R1-R7 precedent is strict: accepted READY8 evidence is neutral target movement only. R6 ADV controls explain or weaken a material subset of movement. R7 freezes packet design only and does not open scoring. The same discipline applies to every new challenger.

## Immediate Parent Enforcement

Enforce these before interpreting any headline:

1. Freeze the rowset, as-of input fields, duplicate key, target spec, split policy, and cost assumptions before opening outcomes.
2. Reject any claim that compares different denominators unless it is explicitly labeled incomparable and routed to repair.
3. Require duplicate-effective-N reporting. Default interpretive floor is `>=30` independent duplicate keys; below that, classify as underpowered intelligence only.
4. Require concentration reports by symbol, session, regime, side, canonical economic group, source segment/hash, date/week, and target horizon. A branch dominated by one axis is not a broad edge.
5. Apply adversarial control envelopes before ranking. READY8-derived branches must subtract ADV-001/ADV-003 style control drift first; non-READY8 challengers must define equivalent random/generic-movement/descriptor-placebo controls.
6. Run neighbor-window and shuffled-label/placebo tests before saying residual signal.
7. Run leave-one-symbol, leave-one-session, leave-one-regime, and leave-one-source/date-window stress before saying robust.
8. Use purged and embargoed time splits for any learned threshold, selector, model, or optimized rule. If feasible, add combinatorial purged cross-validation and PBO.
9. Track multiple-testing debt. No raw p-value, best branch, or leaderboard win is meaningful without trial count, DSR where applicable, and a full ledger of tried branches.
10. Keep neutral target movement separate from R/PnL/win-rate/expectancy. A movement edge is not a trade edge until entry, stop, target, sizing, fillability, spread, slippage, commission, time-in-trade, and execution failures are modeled.

## Reusable Checklist

### 0. Evidence Contract

- Route id, author, generation timestamp, and safe flags are present.
- Evidence class is explicit and matches the artifacts.
- Forbidden surfaces are closed: live behavior, promotion, broker/account/order/deal/position evidence, paid/API calls, prompt/config/risk/safety/execution/canary/selector edits, raw market blob commits, registry edits, remote pushes.
- Full machine-readable ledgers exist for all material branches. Ranked summaries sit on top of full ledgers, not in place of them.
- Completion audit maps prompt requirements to file or command evidence.

### 1. Source, As-Of, And Leakage

- Source files, hashes, parser version, timezone convention, and bar/tick construction policy are recorded.
- Input features are available at decision time; post-event/path/target/fill/PnL fields are excluded from decision inputs.
- Publication-time lag is modeled for external/macro/calendar fields.
- If a source gap exists, rows fail closed until exact source repair is accepted.
- Adjacent bars/ticks are not used to infer missing OHLC/tick truth.

### 2. Denominator Identity

- Candidate identity key and duplicate denominator key are defined separately.
- Duplicate policy states whether duplicates are collapsed, clustered, bootstrapped, or retained only for source diagnostics.
- Same-denominator comparison exists against incumbent/live, naive baseline, generic movement baseline, and relevant mechanical challengers.
- Denominator-role exclusions are separate from source fail-closed rows.
- Every result reports raw N, duplicate-effective-N, candidate count, unique source segments, and unique economic groups.

### 3. Outcome Class Separation

- Neutral target movement outputs use terms like return, high-low excursion, target hit, path status, or terminal status.
- Strategy outputs require a frozen entry/exit/risk/fill/cost model.
- R/PnL/win-rate/expectancy language is blocked unless a strategy projection artifact exists.
- Broker-realized language is blocked unless broker/order/deal/position truth is explicitly in scope and accepted.
- A positive neutral movement branch can only become a retest or design candidate, not a live filter.

### 4. Adversarial Controls And Placebos

- Generic movement control: same symbol/session/regime/time horizon with no challenger predicate.
- Descriptor placebo: irrelevant or intentionally non-causal descriptor with matched availability.
- Neighbor-window placebo: shift event window before/after by fixed offsets while preserving symbol/session/regime/horizon.
- Shuffled-label control: permute pass/control labels within symbol/session/regime/time block.
- Shuffled-time control: permute timestamps within block when path dependency is not the tested mechanism.
- Wrong-horizon/wrong-target placebo: test whether signal is just broad volatility or drift.
- Duplicate artifact control: test if repeated row construction creates apparent lift.
- ADV control envelope: subtract or compare against the strongest matched control drift before residual interpretation.

### 5. Concentration And Robustness

- Concentration is measured before and after duplicate collapse.
- Report max share by symbol, session, regime, side, economic group, source file/segment hash, date/week, horizon, and target family.
- Run leave-one-symbol, leave-one-session, leave-one-regime, leave-one-economic-group, leave-one-source-segment, and leave-one-date-window stress.
- Branches killed by one held-out axis are concentration-sensitive, not broad.
- Branches that only work in one cluster can still survive as specialized intelligence if the cluster is preregistered and retested.

### 6. Split Discipline

- Discovery/development, sealed validation, stress, and forward-shadow partitions are labeled.
- Learned thresholds/models/selectors use purged and embargoed splits.
- Embargo length is at least the maximum lookahead horizon plus any source-publication delay.
- CPCV/PBO is required for optimized selectors when effective N and partition count allow it.
- If CPCV/PBO is underpowered, record exact insufficiency and fall back to leave-block/time split plus forward capture.

### 7. Source Bias And Fail-Closed

- Missingness is not random by assumption; report source availability by symbol/session/regime/source segment.
- Matched controls compare rows with similar source completeness and latency.
- Fail-closed rows are included in denominator sensitivity, not silently dropped.
- Repaired rows are marked repair-candidate until source-hash and parser recomputation are accepted.
- Source-bias candidates are not converted into source-quality filters until prospective capture verifies mechanism direction.

### 8. Cost, Friction, And Execution

- Cost stack is explicit: spread, commission, slippage, financing/swap if held, rejected fills, missed fills, partial fills, latency, and min distance/stop constraints.
- Stress levels include baseline, adverse realistic, and hostile friction.
- Entry geometry uses tradable bid/ask path where available; OHLC-only fills are marked synthetic.
- If stop/target path ordering is ambiguous, fail closed or use conservative path ordering.
- A challenger that loses under modest costs is execution intelligence or avoid logic, not an edge.

### 9. Multiple Testing And Overfit Debt

- Every tested branch, threshold, feature family, target family, horizon, symbol subset, regime subset, and transformation is logged.
- Report raw p only as a diagnostic. Use DSR-corrected p where Sharpe/expectancy-style claims are made.
- PBO is required for optimized model/selector families where combinatorial splits are feasible.
- Min effect size, confidence interval, and stability across splits matter more than the best single branch.
- Leaderboards must rank by control-adjusted, duplicate-adjusted, cost-stressed, split-stable evidence, not raw lift.

### 10. Failure Intelligence

Every failed or weakened branch must be classified as at least one:

- generic movement / false opportunity
- duplicate-denominator artifact
- source-bias artifact
- concentration artifact
- underpowered branch
- wrong horizon
- wrong target family
- mixed mechanism needing split
- inverse/avoid-filter candidate
- execution/friction failure
- data/source/capture gap
- forward-capture requirement
- exact owner/access/source/capture impossibility

Failure does not erase information. It routes the branch to repair, split, avoid logic, source capture, or exact kill.

## Parent Review Template

For each challenger, the parent should require a one-page review with:

- Evidence class and safe flags.
- Frozen denominator and duplicate policy.
- Raw N, duplicate-effective-N, and largest concentration shares.
- Same-denominator baseline delta and ADV/placebo-adjusted residual.
- Leave-one axis survival table.
- Purged/embargoed split or exact reason it is underpowered.
- Fail-closed count and denominator sensitivity.
- Cost/friction stress result if strategy projection is claimed.
- Multiple-testing debt and DSR/PBO status where applicable.
- Exact final label: killed, underpowered, source-routed, avoid-filter candidate, neutral target retest candidate, mechanical strategy projection candidate, or promotion-dossier-required.
