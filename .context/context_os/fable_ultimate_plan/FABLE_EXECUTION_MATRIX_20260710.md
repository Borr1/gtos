# Fable Execution Matrix - 2026-07-10

Generated UTC: 2026-07-11T19:02:30Z.

Current checkpoint update: 2026-07-14T05:51:40Z.

Purpose: current execution control surface before the next patch or replay. This
matrix loads the saved Fable implementation sequence and root-cause audit, then
reconciles them against current disk evidence through completed V237R2 and the
active final-risk/fillability atomicity batch. It supersedes stale V208/V209
guidance in the 2026-07-09
matrix where later evidence changes the dependency-safe next action. V249 is
now the route-certified B7.2 hostile-window checkpoint and B7.3 is next.

## Sources Read

- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_IMPLEMENTATION_SEQUENCE_20260705.md`
- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_ROOT_CAUSE_AUDIT_20260705.md`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/ULTIMATE_SYSTEM_CONTINUATION_DIRECTIVE.md`
- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19/ULTIMATE_SYSTEM_FULL_PLAN_GOAL_PROMPT.md`
- `research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19/VPS_SOURCE_OF_TRUTH_UPDATE_20260619.json`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/OUTPUT_MANIFEST.json`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/VERIFICATION_RESULT.json`
- V211 and V217 summary, parity, trade, order, missed, bucket, and flow artifacts.

## Current Disk And Process State

- HEAD: `f0fc2b425`; V249 B7.2 compact-index POI, physical/headline
  authority, manifest, test, and certification changes are committed. There
  are no post-V249 behavior-code changes before B7.3.
- VPS freshness floor: remote ref
  `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` is an
  ancestor-ok floor for `b112d22c351b13e2af045bb8feb82f1e235246f4`.
- No broad replay, route builder, verifier, pytest, parity builder, analyzer,
  or git fetch process is active. V249 completed once and must not be
  duplicated; V250 B7.3 is pre-replay ready.
- V249 is physically route-certified: canonical builder complete, manifest
  binds the repair program, exact rehydration result, and bounded behavior
  comparison summary/dossier, verifier `ok=true`
  with zero issues and zero POI bad counts, prompt/audits/parent verifiers
  green, and the integrated barrier is 1,390 passing tests with one unchanged
  warning.
- Broker/live/final remain closed. Local replay/package authority remains full.
- Broader worktree still contains unrelated pre-existing dirt in Context OS
  docs/code, route builders, generated context, deleted old science JSONLs,
  scheduler/config tests, and source generator code. Do not stage or revert
  unrelated dirt with this checkpoint.

## Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3`

Scope: configured 24-symbol June 4 bounded ordered-tick reconciliation under
shared digest `163329e9...9b67` and source plan `a24fc919...f001`. It is the
current behavior-neutral producer/proof-consumer authority and exact R1/R2
behavioral successor. It does not prove broad profitability, final selection,
or live use.

Numbers:

- source / decision / candidate / scorecard / order-event / terminal-order /
  physical-trade / missed rows:
  `239 / 2304 / 6981 / 96 / 12 / 6 / 6 / 6975`
- physical scoreable / unscoreable and W/L/F: `5 / 1`, `4/1/0`
- physical net/gross/final R: `+4.03591467 / +4.43627912 / +4.43627912`
- physical cash / risk cash / risk pct: `+$2204.18020365 / $3027.86901650 / 3.0%`
- headline: four trades, `3/1/0`, `+2.12544422R`, `+$992.62016070`
- full-risk / reduced-risk physical fills: `0/6`
- executed broker-cost REFUSED/source-gap rows: `0/0`
- canonical pre-risk quality source maps: `96/96`;
- R1/R3 trade identities: six common, zero added/removed/duplicate;
- R1/R3 nonzero summary deltas after flow: `0`;
- source-bound parity / candidate projection / leakage buckets:
  `5942 / 6981 / 1101`; flow buckets: `379`.

Interpretation: R3 closes the late-donor provenance serialization defect while
preserving every economic and identity observable. The UKOIL unscoreable fill
has an explicit null-R/no-authority selected-policy diagnostic envelope.
Quality-source, cost, physical-summary, stop-hazard, order-transfer, and
selected-policy scans are green. Economics remain mixed versus V258; no
policy, broker, live, or final authority is promoted.

## Baseline Comparison Anchors

### Hostile 2026-05-13..2026-05-17

| Prefix | Candidates | Scorecards | Order Events | Trades | Net R | Gross/Final R | Cash PnL | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 25006 | 288 | 243 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | predecision stop-hazard attribution baseline |
| V90 | 25006 | 288 | 233 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | transfer-rank lifecycle authority baseline |
| V92 | 25006 | 288 | 239 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | Fable hostile comparator |
| V97 | 25006 | 288 | 196 | 47 | +13.89627731 | +18.23890670 | +4461.09800786 | dynamic-scope comparator |
| V198 | 25006 | 288 | 178 | 74 filled | -3.84033809 | +1.79005938 | -3530.29276461 | tick-hydrated current-runtime transfer; failed value transfer |
| V205 | 25006 | 288 | 172 | 72 filled | -5.20239659 | +0.16828289 | -3907.50669036 | hostile value-transfer proof before later repairs |
| V211 | 25006 | 288 | 50 | 18 filled | -3.47466796 | -1.91290882 | -868.32556257 | post-B1/B5 hostile proof; all orders reduced-risk |
| V219 | 25006 | 288 | 68 | 23 filled | -2.82440031 | -0.79141028 | +204.17530212 | post-B3 hostile proof; risk expression restored for many orders, still failed |

V211 same-window denominator evidence:

- source-bound R available: `425333.0444635402`
- package axes / candidate-generated axes / scorecard-order axes /
  filled axes: `1101 / 894 / 10 / 9`
- missed positive / missed negative net R: `+867.5847 / -2735.5864`
- risk decisions: all order-level accepted rows `open-reduced-risk`
- executed broker-cost REFUSED/source-gap rows: `0/0`

### Non-Hostile 2026-06-01..2026-06-05

| Prefix | Candidates | Scorecards | Order Events | Trades | Net R | Gross/Final R | Cash PnL | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V104 | 35191 | 480 | 111 | 46 | +14.73101491 | +18.36174510 | +2850.02330565 | passive-distance hard-block comparator |
| V128 | 35191 | 480 | 212 | 55 | +1.12099062 | +6.22739670 | +3007.28429755 | router-refusal derived immediate authority comparator |
| V150 | 6633 | 480 | 13 | 3 | +0.84449709 | +1.09529478 | +211.19447407 | targeted broad-quality parity prefix |

## Subagent Finding Disposition

- Dalton: INCORPORATED. Broker-cost REFUSED rows remain honest
  non-executable unless dated B6 calibration evidence changes the packet.
- Fermat: INCORPORATED. Full-risk sizing is not missing where a row is already
  `trade`; the live gap is reduced-origin rows whose signed ladder evidence is
  still blocked before full-risk promotion.
- Kant: INCORPORATED. Current stop-loss losers are ordered-tick selected-policy
  stop outcomes, not proven profit-harvest damage.
- Meitner: INCORPORATED. V198/V205/V211 failures concentrate in
  risk/order/fillability and stop-loss exposure, not broker/source mutation.
- Pascal: INCORPORATED. Removed V92/V97 winners remain visible as candidate or
  missed rows; dominant blockers include broker-cost REFUSED and cost-passed
  scheduler/risk transfer classes.
- Kuhn: INCORPORATED THROUGH V199/V201/V206. Stop/exit pressure became a
  stop-pressure/risk-transfer lane; later V217 closed selected-policy
  precondition proof.
- Popper, James, Hilbert, Dirac, Halley: INCORPORATED AT CURRENT EVIDENCE
  LEVEL through the V210-V217 proof lane. Their recurring point was to stop
  broad replay loops until the same-root conversion chain is reconciled. This
  matrix applies that by selecting B3 risk-expression chain repair before
  another broad run.
- No pending subagent result is blocking this B3 batch. New subagents should be
  assigned after the next targeted B3 proof or if current code evidence reveals
  a new same-root dependency.

## B0-B8 Batch Status

| Batch | Status | Exact Evidence | Remaining Gap / Next Step |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json`; `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`; current route `VERIFICATION_RESULT.json` green. | Preserve as before/after reference. |
| B1 provenance truth contract | DONE | V210/V217 green verifier lineage; raw/effective/materialized selector and selected-policy fields preserved into route artifacts; `VERIFICATION_RESULT.json` ok. | Preserve through B3/B7 replays. |
| B2 fillability and reallocation truth chain | DONE/CONDITIONAL | REFUSED/source-gap executed counts are `0/0` in V211 and V217; fill realism is ordered tick in V217; reallocation artifacts exist. | Monitor after B3; reopen only if targeted proof shows starvation or executable REFUSED/source-gap leak. |
| B3 risk-expression ladder and loss-bucket demotion | DONE FOR TARGETED PROOF | V218 patched route-resolved full-risk expression authority, added allow/deny focused tests, ran targeted two-day proof: 3 trades, W/L/F `3/0/0`, net/gross/final `+1.10761535 / +1.35101129 / +1.35101129`, cash PnL `+989.52983936`, risk cash/risk pct `2257.97537016 / 2.25`, full-risk/reduced-risk trades `1/2`, executed REFUSED/source-gap `0/0`. | Preserve through B7.2 hostile five-day proof; reopen B3 only if broad proof shows invalid full-risk promotion, refused/source-gap execution, or risk provenance loss. |
| B4 fill-simulation realism | DONE/CONDITIONAL | Tick-hydrated fill realism surfaces; V217 fills are `ordered_tick_entry_touch`; no cost/source authority bypass. | Preserve; do not loosen fill realism during B3. |
| B5 verifier and comparison precision | DONE / V232R2 ROUTE RECERTIFIED | V232R2 exact identity and signed causal partitions pass. The same-window comparison producer now emits decision counts and the verifier normalizes both current and legacy schemas without weakening count or safety checks. Manifest binds V232R2 plus its hashed V232R2-vs-V232 comparison; route verifier `ok=true`, `issue_count=0`. | Preserve through later B7 proofs. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | Broker-calibrated cost authority is active; V211/V217 execute no REFUSED/source-gap rows; V123 calibration artifacts exist. | Do not loosen cost authority. Reopen only for dated calibration evidence. |
| B7 full proof ladder | PARTIAL / B7.4 ROUTE CERTIFIED / B7.5 FULL-PORTFOLIO ORDERED-TICK RECONCILIATION COMPLETE / POLICY UNPROMOTED | The June 4 24-symbol reconciliation preserves all `6981` candidate, six trade, and `6975` missed identities versus June R2. Five scoreable plus one unscoreable fills produce `+4.03591467R`, `+$2204.18020365`, and `3.0%` risk; physical/cap/transfer scans are green. Versus V258 equal-risk delta is `-0.96118957R` while cash delta is `+$2248.50555688` under `+1.975` risk-percentage points. | Complete canonical certification and commit. Then bind a sealed multi-window equal-risk versus dynamic-risk successor; do not promote policy from this mixed same-day result. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Blocked until B7.1-B7.5 pass and owner/live canary gates open. |

## Requirement-Level Matrix

### B0 Truth Instrumentation Baseline

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Baseline provenance, stale full-risk, expiry/fallback, R identity, raw-failure poisoning, and reallocation-starvation counts | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json`; V114/V210/V217 route audit lineage. | Preserve as regression baseline. |
| Broker-cost refusal histogram by symbol/session/sub-reason/spread-floor source | DONE | `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`; V123 B6 calibration artifacts. | None before B3. |

### B1 Provenance Truth Contract

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Raw selector action/reason preserved separately from effective/materialized action | DONE | `src/components/selector_v4.py`; `src/research_infra/v4_timewarp_simulated_live_research_loop.py`; V210/V217 verifier green. | Preserve. |
| Original action propagated into scheduler, risk, order, trade, and missed rows | DONE | V217 trade/order/missed artifacts carry selected-policy and ladder provenance; verifier green. | Preserve. |
| Gross/net/final R identity naming | DONE | V211 and V217 summaries report net/gross/final separately. | Preserve. |
| Default-confidence provenance visible, not hidden | DONE | V208/V210 lineage and route verifier green. | Preserve. |

### B2 Fillability And Reallocation Truth Chain

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Unresolved fill-floor failures are executable authority, raw failures remain diagnostic | DONE/CONDITIONAL | V217 zero executable source/cost leaks and ordered-tick fills. | B3 patch must not bypass unresolved failures. |
| Reallocation can choose next valid candidate after top veto | DONE/CONDITIONAL | V211/V217 parity and flow artifacts exist. | Monitor after B3; no broad replay first. |
| Fallback/expiry emits explicit reasons and does not silently starve orders | DONE/CONDITIONAL | V217 has 1 expired unfilled order with flow/bucket ledgers. | Preserve. |
| REFUSED/source-gap/unfillable rows are non-executable but scoreable/missed | DONE | V211 and V217 executed REFUSED/source-gap rows `0/0`. | Preserve. |

### B3 Risk-Expression Ladder

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Full/reduced/diagnostic tiers are explicit and verifier-scanned | DONE FOR TARGETED PROOF | V218 focused tests passed; V218 targeted replay produced filled full-risk/reduced-risk split `1/2`, order full-risk/reduced-risk split `2/6`, route verifier green. | Preserve through B7.2 hostile five-day proof. |
| EV-band/open-reduced promotion requires signed authority | DONE/CONDITIONAL | Signed-authority validation exists; tampered authority test exists. | Preserve strict signing in B3 patch. |
| Route-resolved fill-floor can satisfy full-risk fillability condition | DONE | `src/research_infra/v4_timewarp_simulated_live_research_loop.py` now allows the bypass only when route-resolved, no unresolved failures, signed authority valid, broker cost passed, source complete, replay-executable, top-ranked/new-order intent, and no selected-policy quality block. Focused allow/deny tests pass. | Preserve; reopen only on verifier or broad-ledger counterexample. |
| Hardcoded loss buckets are diagnostic, not proof of suppression | DONE/CONDITIONAL | Current proof lane uses no hardcoded date/symbol/session suppression as final proof. | Preserve. |
| Full-risk vs reduced-risk behavior reported separately | DONE FOR TARGETED PROOF | `.context/context_os/V218_B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR_BEHAVIOR_REPORT.md` reports risk split, risk cash, cash PnL, trade-level risk decisions, stress/MC, and same-window source-bound transfer. | Extend the same reporting in B7.2 hostile five-day proof. |

### B4 Fill Realism

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Immediate marketable fill source-time/as-of truth enforced | DONE/CONDITIONAL | V217 fill realism class `ordered_tick_entry_touch:3`. | Preserve. |
| Passive-limit queue realism and diagnostic proxy classification | DONE/CONDITIONAL | V122/V197 lineage; no V217 bypass. | Monitor after B3. |
| Same-bar ambiguity closed conservatively with provenance | DONE/CONDITIONAL | B4 lineage and current verifier green. | Monitor. |

### B5 Verifier And Comparison Precision

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Off-configured fallback predicate precision and raw/effective leak detection | DONE | Current verifier green. | Preserve. |
| Cost scan scoped to executable rows and diagnostic rows cannot carry executable PnL | DONE | V211/V217 cost/source execution `0/0`. | Preserve. |
| Proof prefix cannot be capped/narrowed without bounded-smoke label | DONE/CONDITIONAL | V217 explicitly bounded by symbols and dates. | Preserve in targeted proof. |
| Comparison outputs include transfer, risk, fill-realism, added/removed fields | DONE/CONDITIONAL | V211/V217 parity and flow artifacts exist. | Generate after targeted proof if behavior changes. |

### B6 Broker-Cost Calibration Audit

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Refusal histogram joined to measured tick-spread floors | DONE WITH LABEL | V123 B6 calibration audits and broker-cost packet fields. | Reopen only with dated calibration data. |
| REFUSED packets cannot execute | DONE | V211/V217 executed REFUSED/source-gap `0/0`. | Preserve. |
| Synthetic timewarp candidate-cost proxy is diagnostic only | DONE/CONDITIONAL | Current summaries use broker-calibrated replay cost authority. | Preserve. |

### B7 Full Proof Ladder

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| 7.1 bounded structural proof-surface integrity | DONE FOR LOCAL SLICE | V218 targeted run: 3 trades, +1.10761535R, full-risk/reduced-risk trades `1/2`, route verifier green, final/live false. | This is not total market truth. |
| 7.2 hostile 2026-05-13..17 value-transfer proof | DONE / ROUTE CERTIFIED | V249 preserves the full 25,006-candidate surface and exact V245 identities; 20 physical trades produce `+1.16150430R` net while 18 ordered-tick headline trades produce `+0.28044419R`; 14,517/14,517 required POI projections are complete; executed REFUSED/source-gap is `0/0`; route verifier is zero-issue. | Preserve as hostile/stress evidence; do not tune from outcome buckets. |
| 7.3 non-hostile objective regime proof | DONE / ROUTE CERTIFIED / BOUNDED | V250 runs unchanged V249 behavior across all configured symbols for 2026-06-01..05. Headline is 4 trades, 3/1/0, +1.59506223R and stress-positive through +0.20R/trade, but cash is -$67.96685163. Exact-window denominator is 356027.9026815028R; all 13 physical identities have executable traces; verifier and route audit are zero-issue. | Preserve as bounded independent-regime evidence; do not promote four rows to broad truth. |
| 7.4 broad 2026-06-01..19 proof | DONE / ROUTE CERTIFIED | V258 preserves V250/V257 inside June 1-5 and completes all 19 chunks with one source-plan digest and zero cache remainder. Physical behavior is 42 trades, 23/19/0, +15.08858577R; headline is 4 trades, 3/1/0, +1.59506223R. Scorecards 1,440 exceed V110B 1,056; expiry 1 is below V111 28; V110B common overlap is 14; all 43 removed winners have named predecision blockers; parity and canonical verifier are zero-issue. | Preserve as the broad current-truth anchor. The four-row headline remains too thin for final selection. |
| 7.5 extended history proof | PARTIAL / TRANSFER SEMANTICS DONE / TARGETED LIFECYCLE GREEN / BROAD ECONOMIC GATE OPEN | January and April R4 completed under shared digest `44a8c046...c8c27`; paired physical behavior is `117`, `47/70/0`, `-4.81212578R`, while paired headline is `10`, `5/5/0`, `-1.56722011R`. Non-additive source semantics and pair/hash/unit verification are closed. April 10 R5 proves exact intent/fill/terminal-R separation: 248 candidates, 92 scorecards, 3 fills, one scoreable loss, two terminal-unscoreable fills, zero R2 identity drift, and lifecycle `bad_counts={}`. | Run full April under the R5 code and classify every changed intent/fill/risk/same-symbol outcome before pressure-cap or exit-policy repair. |

### B8 Live Path

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Production-return dossier | OPEN | B8 plan only. | Blocked by B7. |
| Live-shadow with SimulatedBroker for at least 5 trading days | OPEN | No B8 shadow proof. | Blocked by B7. |
| Canary micro-live and broker-statement reconciliation | OPEN | Live/broker/final false. | Owner action only after B7 and B8 gates. |

## Completed Same-Root Batch - V218 Historical Plan

Batch:
`B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR`

Completion note: this section records the B3 plan that has now been executed.
The active next batch is V219/B7.2 below.

Reason: Fable dependency order says B3 must be closed before B7 broad proof.
V211 and V217 prove the risk-expression ladder exists but is behaviorally
collapsed to reduced-risk fills. Current code has the exact same-root gap:
route-resolved fill-floor evidence is recorded but cannot satisfy the
full-risk fillability gate because `route_resolution_full_risk_bypass_allowed`
is always false.

Files/components affected:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260710.md`
- after patch/test, `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- after patch/test, `.context/context_os/CONTINUATION_CURSOR.json`

Patch classification:

- Correctness repair: route-resolved fill-floor authority can satisfy the
  full-risk fillability condition only when all causal predecision conditions
  pass: signed authority valid, broker cost passed, source-complete, replay
  executable, no unresolved fill-floor failures, no cost/source executable
  block, top-ranked or transfer-dominant selected rank, and no selected-policy
  quality block.
- Performance repair: valid signed rows can express full risk instead of being
  forced to reduced-risk solely by raw fillability when the route has already
  resolved the fill-floor authority.
- Diagnostic/ledger repair: preserve raw below-floor fillability, emit
  `package_risk_expression_fill_floor_route_resolved_for_full_risk=true`, and
  emit `package_risk_expression_route_resolution_full_risk_bypass_allowed=true`
  only for accepted bypass rows.

Expected measurable effect before replay:

- candidate -> scorecard transfer: neutral in focused unit proof.
- scorecard -> order transfer: neutral in focused unit proof.
- order -> fill transfer: neutral in focused unit proof.
- missed positive/negative R: neutral until targeted replay.
- trade count: neutral until targeted replay.
- net/gross/final R: R-multiple may be neutral if trade set is unchanged;
  cash PnL and risk cash should change when promoted rows fill.
- W/L/F: neutral until targeted replay unless risk controls alter final action.
- cost-refused/source-gap execution: must remain `0/0`.
- risk-reduced/full-risk distribution: must move from all reduced-risk to at
  least one full-risk row in the targeted risk-authority proof when conditions
  pass.

Focused proof before replay:

1. Add/adjust tests so a signed, broker-cost-passed, source-complete,
   route-resolved, no-unresolved-failure row with raw fillability below the
   default full-risk floor is promoted to full-risk.
2. Add/adjust tests so unresolved fill-floor failures still block full-risk and
   preserve `execution_fillability_below_full_risk_floor`.
3. Run py_compile for the touched module/test.
4. Run the focused full-risk expression pytest cluster.
5. Only after focused proof passes, run the smallest targeted replay that can
   show full-risk vs reduced-risk behavior on V217-like rows. Do not run broad
   B7 until B3 targeted proof is parsed.

Success criteria:

- No live/broker/final authority opens.
- Broker-cost REFUSED/source-gap rows stay non-executable.
- Full-risk promotion occurs only for signed, source-complete, cost-passed,
  replay-executable, fill-floor-resolved rows with no unresolved failure.
- Reduced-risk rows preserve exact causes when any causal precondition fails.
- Focused tests prove both allow and deny paths.
- Targeted replay reports full-risk vs reduced-risk distribution, risk cash,
  cash PnL, and unchanged cost/source execution safety.

Failure criteria:

- Any unsigned, cost-refused, source-gap, unfillable, off-authority, or
  unresolved-fill-floor row can execute or promote to full-risk.
- Positive headline behavior comes only from suppressing opportunity.
- The patch changes selector/scheduler admission without ledger provenance.

Broker/live/final remain closed.

## V238R3 Completion Update - B7.2 Atomicity Closed, Economic Value Open

Generated UTC: 2026-07-12T21:09:32Z.

V238R3 reran the exact 2026-05-14 XAUUSD/JP225/GER40/US30_cash slice after
restoring the two manifest-bound hostile-window tick ledgers omitted during the
Mac-local cutover. Their SHA-256 values match the current manifest. This
separates the code repair from V238R2's source-denominator drift.

Current bounded behavior:

- source / decision / candidate / scorecard rows: `28 / 2208 / 2469 / 92`;
- order events / logical orders / filled trades: `13 / 7 / 6`;
- W/L/F: `3 / 3 / 0`;
- net/gross/final R: `-2.81768013 / -2.26948297 / -2.26948297`;
- cash PnL / risk cash / risk percent: `-$980.11471440 / $2439.92967918 / 2.45%`;
- expected cost: `0.54819716R`;
- diagnostic scoreable missed: `609 / -143.51033091R`;
- executable scoreable missed: `0 / 0R`;
- executed REFUSED/source-gap rows: `0 / 0`;
- stress at `+0.05/+0.10/+0.20R` per trade:
  `-3.11768013/-3.41768013/-4.01768013R`;
- Monte Carlo total / worst drawdown: `-2.81768013/-3.34698405R`.

Truth proof:

- execution-bound order atomicity: `12/12` valid;
- trade atomicity: `6/6` valid;
- the US30 14:15 trade preserves `0.92`, source time `14:00`, and the
  closed-M15 predecision boundary;
- JP225 and GER40 use historical FTMO predecision tick spreads and retain their
  original `PASSED` broker-cost packets.

This closes the B7.2 canonical final-risk and execution-fillability atomicity
sub-batch. It does not pass the economic-value gate: the exact target remains
losing, and the four-trade V238R2 headline is rejected because it came from two
missing tick ledgers and cost refusal, not better policy. The next same-root
batch is causal finalizer/risk-expression, scheduler rank/reallocation, and
selected-policy/exit loss-transfer analysis on this clean six-trade cohort,
followed by targeted repair and hostile/non-hostile proof.

## V235R3 Completion Update - B7.2 Local Lifecycle Contract Certified

Generated UTC: 2026-07-12T11:56:15Z.

V235R3 closes the causal POI lifecycle and canonical terminal-blocker batch on
the bounded 2026-05-14 US30 slice. The code batch spans the shared POI lifecycle,
executable-value, and blocker-precedence components plus market-state, origin,
pre-AI, selector, scheduler, execution, pending lifecycle, timewarp, parity, and
route-verifier consumers. Each new field has a producer, executable consumer,
ledger projection, and focused verifier/test.

Proof is behavior-neutral and denominator-preserving:

- rows source/decision/candidate/scorecard/order-event/terminal-order/trade/missed
  are `10/2208/714/92/2/1/1/713`;
- W/L/F is `1/0/0`, net/gross/final R is
  `+0.16752490/+0.20574311/+0.20574311`, and cash PnL is `+$16.75249`;
- `13,016` considered POI instances reconcile as `586` emitted plus `12,430`
  denied, with `107` rankable and `479` diagnostic-not-ready visible rows;
- nonrankable order/trade leakage and executed REFUSED/source-gap rows are zero;
- route verifier is `ok=true`, `issue_count=0`; prompt hardening and standard
  route artifact audit are green;
- the final fixed-snapshot barrier is `2,021 passed, 1 unchanged warning`;
  compile and tracked/untracked whitespace checks pass.

This marks the local structural requirement DONE, not the hostile-five-day gate.
The next dependency-correct action is the scoped commit and active-artifact
storage checkpoint, followed by the current-code 2026-05-13..17 B7.2 value
proof. Broker/live/final remain false.

## V236 Result And V237 Exact-Member Atomic Authority Batch

Updated UTC: 2026-07-12T16:51:28Z.

V236 completed the hostile five-day replay and was recovered into a certified
summary-v2 artifact without rerunning simulation. It produced two fills,
W/L/F `1/1/0`, net/gross/final
`-0.92559780/-0.79425689/-0.79425689R`, cash PnL
`-$92.57809253`, and zero REFUSED/source-gap executions. Relative to V219, its
headline net improvement is almost entirely lower cost after 21 fewer fills;
gross R is approximately unchanged. B7.2 therefore remains failed because this
is positive movement by opportunity collapse, not stronger conversion.

The current same-root repair targets the causally valid router-authorized path,
not all diagnostic candidates. V219 contains 18 such logical orders over
2026-05-13..15 across `GER40`, `JP225`, `NAS100`, `US30_cash`, and `XAUUSD`:
13 fills, five expiries, filled W/L `11/2`, and `+3.22861062R`. Current V236
candidate identity produces 19 causal instances for those 18 contexts because
one GER40 decision has two distinct POIs. The scheduler must rank them rather
than collapse them. Sixteen V219 off-session logical orders remain blocked;
their `-6.05301093R` is evidence against restoring generic off-session authority.

Current code repairs the full affected chain:

- selector-event POI/lifecycle and one atomic execution-fillability atom;
- exact-member source-bound aliases and normalized quality floors;
- declaration-before-validation for immutable signed authority;
- immutable signed order permission separated from finalizer permission;
- all public capped-risk aliases set to the actual approved risk;
- one complete valid authority namespace selected for no-selection scorecards;
- flat verifier namespaces and deterministic finalization/recovery checks.

Compile and the 14-test focused barrier pass. The next action is V237 on the
exact three-day five-symbol cohort. Success requires restored scorecard/order
transfer, exact risk/fillability projection, zero REFUSED/source-gap/off-session
execution, and complete missed accounting. A negative R result can still prove
the truth repair and expose scheduler ranking or exit/harvest as the next root
flaw; a result obtained by further trade suppression fails.

The first V237 process failed before simulation on the first source symbol:
`rows_by_day()` constructed its mapping but did not return it, so derived H1
resolution received `None`. Current diff evidence identified this as an
accidental refactor regression. The return contract is restored and covered by
one direct helper test plus one derived-H1 resolver consumer test; compile and
both tests pass. The partial V237 prefix is not behavioral evidence. V237R2 is
the designated successor proof.

## V237R2 Result And V238 Atomicity Batch

Updated UTC: 2026-07-12T18:00:15Z.

V237R2 completed the exact three-day five-symbol proof with 18 fills, W/L/F
`8/10/0`, net/gross/final `+2.13064803/+3.60123918/+3.60123918R`, expected
cost `1.47059115R`, and zero executed REFUSED/source-gap rows. This is a real
transfer improvement over V236's two-fill suppression surface. The 11 added
contexts contribute `+4.25111207R` net.

The run is not accepted as a clean checkpoint. Eight filled trades have
nonzero actual risk while their public `final_approved_risk_pct`,
`runtime_final_risk_pct`, and `approved_risk_pct` are zero. The finalizer probe
provides a positive final value but a stale runtime-final alias is merged over
the fresh order-time packet; the ledger consumer then prefers that stale nested
zero. Separately, the selected US30 2026-05-14T14:15Z candidate and scheduler
option carry exact 0.92 predecision fillability, but selector package evaluation
retains only the numeric value. The selected scorecard/order quality contract
correctly rejects that incomplete value-only sibling.

The V238 same-root batch must:

- establish one canonical executable final-risk atom at finalizer-to-order
  merge and bind only the final public/nested trio to it;
- retain scheduler, selected-cell, and dynamic-budget risk as pre-final
  provenance;
- preserve execution fillability through selector/package evaluation as one
  value/source/source-time/boundary/class tuple plus its nested envelope;
- add focused producer/consumer/verifier tests for both invariants;
- explain the 0.5/0.625/1.0 sizing derivation before any outcome-driven policy
  tuning.

No hostile-five-day replay is allowed before the smallest targeted V238 proof
is green. Broker/live/final remain false.

## V232 Signed-Finalizer Causal-Partition Checkpoint

Updated UTC: 2026-07-12T00:49:28Z.

Status: `V232R2 TARGETED PROVEN / ROUTE RECERTIFIED`.

`DONE` on the current code snapshot:

- scheduler-produced structured stale-selector dispositions carry exact
  candidate-instance, signed order-executable, broker-cost, source, session,
  and no-outcome authority;
- the finalizer consumes that disposition fail-closed and cannot fall back to
  a legacy not-trade softening path;
- valid signed stale aliases bypass only stale reallocation-pool and synthetic
  score artifacts, then retain the real selected-policy execution-fill gate;
- scheduler-bound and stale-alias terminal partitions reconcile exact identity
  sets and reject duplicates, missing rows, unexpected rows, vacuous applied
  counts, and zero-trade denominator inflation;
- selected-policy quality blocks contribute to aggregate finalizer status;
- compile, diff check, and the five-suite barrier pass `1530` tests with one
  pre-existing pytest configuration warning;
- route-builder current-control binding now consumes the active V231 schema and
  avoids exhaustive scans of superseded dataless raw replay families.

Pre-replay route barrier is `DONE`: the rebuilt manifest binds V231 and its
hashed V231-vs-V230 comparison, verifier is `ok=true` with zero issues, prompt
hardening is green, the standard route artifact audit is green, and the heavy
  integration barrier passes `1531` tests.

V232 completed with V231-identical behavior and zero REFUSED/source-gap
execution, but did not close this checkpoint. It proved `11` contract-valid
signed stale-selector probes were applied, then exposed two consumer defects:

- every probe already had a blocked selected-policy execution-quality gate,
  but five opening-window and six risk-headroom rejections masked that causal
  terminal disposition, leaving quality/other-terminal `0/11`;
- all `107` real scheduler-bound probes were present, but the input identity
  denominator counted `607` synthesized diagnostic candidates as well, yielding
  `714/107` input/probe cardinality and false reconciliation.

V232R2 repairs both roots without weakening authority. Selected-policy quality
owns terminal attribution for an actually applied, contract-valid signed probe
while later risk rejection remains provenance; input and terminal identity sets
share one executable scheduler-binding predicate, so synthesized diagnostics
remain scoreable but outside the executable-bound denominator. Runtime,
verifier, and deny-path tests cover both opening-window and headroom rejects plus
an actual option beside a synthesized diagnostic. Clean commit `12029cc7e` is
integrated as `2cf25a24e`; compile, diff check, and the five-suite barrier pass
`1534` tests with the unchanged pytest configuration warning.

V232R2 pass criteria are exact and behavior-neutral: 11 signed in-session aliases
must be applied probes then quality-blocked; nine signed off-session aliases
must remain terminal; probe-not-applied and applied-other-terminal must be zero;
the scheduler-bound denominator must reconcile `107/107` by candidate-instance
identity while excluding all synthesized diagnostics; no refused
cost or source-gap row may execute. Any behavior change from weakening hard
authority fails. This is a local truth proof only.

V232R2 passes those criteria. It preserves V232/V231's one trade and exact
headline behavior, has zero REFUSED/source-gap execution, reconciles
scheduler-bound input/probe `107/107` across all 92 scorecards, and partitions
signed aliases as `85 = 11 applied quality-blocked + 74 terminal`, with zero
selected, other-terminal, or not-applied rows. All 607 synthesized diagnostics
remain scoreable outside the executable-bound denominator. The deterministic
flow/parity/comparison package contains 186 flow buckets, 2,526 parity rows,
1,101 leakage buckets, 714 candidate-instance projections, and zero added or
removed trades versus V232.

Route recertification is complete. The comparison producer now includes the
`2,208` decision-row denominator, and the verifier consumes the current
`same_window_comparison.v1` candidate payload while retaining legacy-schema
compatibility and exact safety/count checks. The rebuilt manifest contains 196
files and binds the hashed V232R2-vs-V232 comparison. Route verification is
`ok=true` with zero issues, prompt hardening and standard artifact audit pass,
the lifecycle/fillability bridge verifier passes, and the integrated barrier is
`1545 passed` with the unchanged pytest configuration warning. Final/live
remain false.

The aged distant FVG/POI generator-to-consumer batch is now integrated and
focused-green at heavy commit `38af8897c`: stable identity, causal age/touch/
distance/fill/invalidation state, immutable scheduler/lifecycle projection,
generation partition, and exact verifier coverage are present. V233 proved the
generation/identity half and failed terminal lineage; `d7cb566ad` repairs the
exact exposed chain. V233R2 now passes all local causal-POI invariants with
unchanged behavior. The next action is fresh route certification, followed by
the evidence-ranked FVG scorecard-to-order transfer repair. Hostile
five-day, objective non-hostile, broad, extended history, final selection, and
live activation remain later B7/B8 gates.

## B7.2 V231 Targeted-Proof Barrier

Updated UTC: 2026-07-11T21:18:00Z.

Status: `PARTIAL / IMPLEMENTATION GREEN / TARGETED BEHAVIOR PENDING`.

The current same-root batch is
`B7_2_NO_PRIMARY_DISPLACEMENT_AND_QUEUE_FILLABILITY_AUTHORITY`. It is integrated
at `daf297afa` after preserving the heavy worktree's hidden queue implementation
and tests. No subagent return remains unreconciled.

Implemented requirements:

- `DONE`: no-primary candidates use an absolute positive expected-transfer
  score floor; primary-comparator edge delta is evaluated only when a primary
  comparator exists.
- `DONE`: repaired-profile origin-family gating and candidate origin fields
  propagate through harness, timewarp, scheduler, and proof surfaces.
- `DONE`: stale reduce-risk aliases can be restored only by immutable signed
  exact-member, same-instance, atomic predecision fillability proof.
- `DONE`: honest low-fill, off-session, broker-cost, source, risk, and lifecycle
  vetoes remain independent and executable authority stays fail-closed.
- `DONE`: candidate, scorecard-option, and missed displacement projections have
  a verifier contract for nonzero coverage and exact parity.
- `DONE`: direct and local-file M1/tick paths share one penetration-or-repeated-
  touch queue model; first-touch optimism and ordered-tick gaps are diagnostic.
- `DONE`: compile, focused queue/oracle tests, shared microstructure tests,
  scoped diff check, and `1512` integrated tests pass. The sole warning is the
  pre-existing unknown `asyncio_mode` pytest option.
- `OPEN`: V231 must prove the behavior and ledger effect on the exact V230
  one-day US30 comparator slice.

Expected exact movement before replay:

- false no-primary displacement vetoes: `30 -> 0`;
- stale flat reduce-risk false aliases: `17 -> 0`;
- on-session dynamic-router rows becoming rankable or receiving a new exact
  downstream disposition: `11`;
- honest low-fill rows retained: `13`;
- off-session rows retained: `10`;
- unique displacement diagnostics: candidate/scorecard/missed
  `106/106/106`, with zero projection drift;
- REFUSED/source-gap executions: `0/0`;
- candidate generation: expected neutral;
- orders, fills, risk split, and R: behavior-changing only if corrected
  candidates outrank and pass honest downstream execution constraints.

The designated prefix is
`BROAD_LIVE_AS_IF_REPLAY_V231_B7_2_NO_PRIMARY_DISPLACEMENT_QUEUE_AUTHORITY_20260514_US30_REPAIRED_ONLY`.
This is a local repair proof. It cannot close hostile five-day, objective-regime,
broad-history, final-selection, or live gates.

## V220 Failure And V220R2 Repair Update

The first V220 targeted run completed its two-day/three-symbol campaign but did
not produce a certifiable final summary. It is preserved as an explicit partial:

- candidate/scorecard/order/trade/missed rows `1651/192/0/0/1651`;
- twelve risk-finalizer probes rejected selected-policy expected-net calibration
  projection;
- current-summary certification exposed stale/provisional authority precedence;
- diagnostic scoreable missed R `-117.18932322R`;
- broker/live/final remained false and no broker order was attempted.

V220R2 closes the same root across producer, finalizer, consumer, bridge, and
verifier rather than adding a local gate:

- candidate-instance packet fillability precedes weak candidate recomputation;
- normal runtime and scheduler-row finalization use explicit, different signed
  authority precedence appropriate to their stage;
- provisional rows cannot self-finalize from a different nested signature;
- fill-softening and router-refusal families no longer contaminate each other;
- only exact proven close/reverse transitions can bypass lifecycle floors;
- valid designated nested authority wins flattened aliases while conflicting
  unselected current hashes remain fatal;
- bridge source time and unsigned projection are strict producer/consumer
  contracts.

Focused verification is green: scheduler `307`, runtime `725`, materialization
`82`, bridge `130`, verifier `158`, and combined route-facing suites `370`
passed. Touched modules compile and scoped `git diff --check` passes.

V220R2 then completed its bounded campaign but remained an uncertified partial:

- candidate/scorecard/order/trade/missed rows `1651/192/0/0/1651`;
- eight scorecard rows had valid signed authority, signed order authority, and
  derived executable package authority;
- all eight were rejected by stale outer
  `selected_policy_expected_net_calibration_required` projection;
- four also carried stale `execution_fill_probability_source` projection;
- diagnostic scoreable missed R remained `-117.18932322R` and no
  REFUSED/source-gap row executed.

V220R3 closes that same producer-to-consumer root rather than loosening a gate:

- valid selected signed quality, order, identity, lifecycle, and atomic
  fillability authority is projected to option, decision inputs, probe,
  candidate, and packet consumers before risk admission;
- canonical lifecycle intent is applied before signed validation;
- execution-fill tuples bind to one exact candidate instance;
- valid ordinary-trade derived executable authority is projected to every
  consumer before the second canonical pass, so a stale decision-input false
  cannot resurrect.

Current fixed-snapshot verification is green: scheduler `316`, runtime `743`,
materialization `82`, bridge/parity `231`, verifier `223`; all touched Python
modules compile and scoped `git diff --check` passes.

V220R3 then completed and serialized a final summary, proving the prior
projection/certification failure was removed, but executable transfer remained
zero:

- candidate/scorecard/order/trade/missed `1651/192/0/0/1651`;
- diagnostic scoreable missed rows/R `366/-118.10784844R`;
- `159/192` scorecards were directly blocked because a stale outer
  `execution_fillability_missing_source_bound_input` sentinel masked valid
  nested predecision fillability;
- net/gross/final/cash and W/L/F remained zero; stress/MC trade count was zero;
- REFUSED/source-gap executed rows remained `0/0`.

V220R4 repairs the complete nested-source precedence contract. A nested object
uses its own declared source, inherits an outer source only when that outer pair
is authoritative, otherwise binds to canonical nested predecision provenance.
Unsafe declared sources, outcome use, temporal failures, numeric conflicts, and
unsigned aliases remain blocked. Frozen-ledger analysis recovers `1613/1651`
candidate fillability rows and leaves 38 honestly missing; 834 recovered
cost-refused rows remain cost-blocked.

Current fixed-snapshot verification is green: scheduler `317`, runtime `744`,
and materialization/bridge/parity/verifier `536`; touched modules compile and
scoped `git diff --check` passes.

V220R4 completed its bounded campaign with
`29/4608/1651/192/0/0/1651` source/decision/candidate/scorecard/order/trade/missed
rows, but final-summary certification failed. Frozen current-code inspection
found 12 valid signed candidate/missed rows and 8 valid signed scorecard rows.
Those rows were still blocked because a mutable
`selected_policy_expected_net_calibration_required=false` alias overrode the
immutable signed value. Final-blocked serialization also required current
effective alias demotion without mutating the signed payload.

V220R5 repairs that complete authority split:

- immutable exact-instance identity and causal predecision quality project to
  every finalizer and order-materialization consumer;
- admission-time signed cost/order truth remains available as prefixed proof;
- current broker-cost, fill-floor, lifecycle, and order denials retain effective
  fail-closed authority;
- final-blocked serialization canonicalizes the designated signed envelope from
  its own payload/hash and demotes only current effective aliases;
- the verifier rejects any valid signed row later blocked by mutable
  `current_signed_authority_projection_mismatch:*` drift.

Current fixed-snapshot verification is green: the six-file scheduler/runtime/
materialization/bridge/parity/verifier barrier is `1602 passed`; seven direct
authority/current-denial contracts pass; compile and scoped `git diff --check`
pass. Frozen V220R4 projection is valid for candidate/scorecard/missed rows
`12/8/12` with zero calibration mismatch.

V220R5 completed and certified all required artifacts with
`29/4608/1651/192/0/0/1651` source/decision/candidate/scorecard/order/trade/missed
rows. It proved the prior serialization and required-flag repairs but exposed a
later consumer:

- 12 valid exact-instance signed candidates received `0.1%` reduced-risk
  allocation;
- 7 passed immediate-route quality and authority, then failed because order
  preflight re-ran the owner proxy builder and changed the signed selected-policy
  calibration hash;
- 5 were independently blocked and remain closed: 2 by broker-calibrated
  expected-cost ceilings and 3 by immediate-entry unit-risk/ATR quality ceilings;
- diagnostic scoreable missed rows/R remained `366/-118.10784844R`, with zero
  REFUSED/source-gap execution.

V220R6 removes late selected-policy re-derivation for a valid signed envelope.
All seven calibration atoms now come from the immutable exact-instance payload;
unsigned rows retain owner-approved reconstruction, and current cost,
fill-floor, lifecycle, and order denials remain effective. Current verification
is green: nine direct contracts and the `1603`-test six-file barrier pass;
compile and scoped `git diff --check` pass.

V220R6 completed and certified the same bounded surface. The seven policy-hash
failures fell to zero, proving the late policy repair, but all seven routes then
hit `passive_limit_too_close_predecision_guard`. Root inspection showed the
passive guard was downstream of two truth losses: `complete` versus
`source_completeness_present` raw-string mismatch invalidated immediate-fill
authority, and the scheduler/risk marketable-route object was not copied into
order preflight.

V220R7 implemented that combined root but completed with the same certified
`29/4608/1651/192/0/0/1651` source/decision/candidate/scorecard/order/trade/
missed counts as V220R6. The seven signed route permissions were present, but
four scorecard windows containing all seven affected probes still reported
`off_configured_session_immediate_marketable_limit_disabled`, followed by the
passive-only guard.

The next root is shared session namespace shape and route-envelope session
projection. Canonical `hNN_NN` tokens are six characters, while package,
scheduler, replay, bridge, parity, and builder consumers incorrectly required
seven. V220R8 replaces those duplicate checks with one consecutive-hour
contract, projects the selected configured route session only while current
route permission remains true, preserves raw off-session provenance, flattens
the preflight atoms, and adds a verifier rejection for the exact drift. The
full active barrier is `1645 passed`.

V220R8 completed and certified with unchanged zero-order/zero-trade counts. It
proved the session repair: all seven signed routes now have a concrete configured
session and session drift is zero. It then exposed the next atom: generic
`router_refusal_* = false` was consumed before exact current package route true.
Four scorecard windows containing all seven probes reproduce the new verifier
reason `signed_immediate_marketable_exact_route_overridden_by_auxiliary_false`.

V220R9 makes current flat package route atoms authoritative, keeps any explicit
package false terminal, falls back to nested package route, and consults generic
router-refusal fields only when no package route decision exists. The deciding
tier and all route atoms are ledger-visible; the full active barrier remains
`1645 passed`.

V220R9 completed with the same certified zero-order/zero-trade result. The new
ledger atoms proved why: current risk supplied the correct nested route but no
flat aliases, so independent flat-key lookup fell through to stale selected
inputs carrying false/false. V220R10 makes route envelope and coupled flat atoms
one atomic highest-priority projection consumed by both finalizer preflight and
actual order simulation. The full active barrier remained `1645 passed`.

V220R10 reached four order attempts and zero fills. All four exact selected
finalizer probes already had source-safe immediate-fill proof, current route
true, and a configured execution session. `simulate_order` nevertheless copied
only a scalar subset from the finalizer and recomputed stale false route atoms
for actual order handling. Terminal serialization then retained
`risk_finalizer_executable_finalized=true`, while the verifier conflated the
preserved `simulated_order_id` attempt identity with executable binding.

V220R11 closes this same root across runtime and proof: deep-copy the finalizer
route/session/preflight envelope into order-time risk, demote every finalizer
executable flag at terminal blocking, preserve pre-finalization proposal truth,
scan those flags in the verifier, and distinguish attempted-order identity from
explicit executable binding. The V220R10 four-row reproducer is clean and the
full active barrier was `1648 passed`.

V220R11 materially transferred the repaired path: 3 terminal orders, 3
source-safe immediate fills, 3 trades, W/L/F `2/1/0`, and net/gross/final R
`+0.18799082/+0.29037839/+0.29037839` with zero guarded fallback. One later
candidate was honestly blocked after the changed exposure/state. Final summary
failed only because one no-selected scorecard window retained candidate-scoped
signed authority at root and in stale pre-finalizer scheduler inputs.

V220R12 moves those candidate-owned surfaces to `scorecard_reported_*` only at
the final no-selection boundary, preserves finalizer-prefixed immutable payload,
and changes no behavior policy. It completed and certified with the same 3
trades, W/L/F `2/1/0`, net/gross/final R
`+0.18799082/+0.29037839/+0.29037839`, and zero guarded fallback or executed
REFUSED/source-gap rows. Full-tag parity also proved all 1,651 rows belong to
the selected profile and `candidate.trading_day` window.

That parity pass exposed the next same-root contract failure: the immutable
payload signed the atomic execution-fillability value/source/time/boundary but
omitted `execution_fill_probability_authority_class`; runtime projected the
canonical class only after signing. Bridge, parity, and verifier therefore
rejected every old-schema envelope as missing current-stage authority. V220R13
adds the class to the signed payload, required-atom validator, runtime immutable
projection, bridge, parity, verifier, and focused tests while preserving the
separate current raw materialization class. The current full barrier is
`1618 passed, 1 warning` and Python compile passes.

V220R13 exactly reproduced V220R12 behavior and carried the canonical signed
fillability class through all 12 signed candidates, 6 order events, and 3
trades. Full-tag parity passed exact source scope, but only the 3 executed
envelopes were valid: 9 blocked candidate instances had two valid hashes that
differed solely because one stage signed `complete` and another signed
`source_completeness_present`.

V220R14 canonicalizes execution-equivalent complete-source aliases before
payload hashing while preserving distinct missing/degraded/incomplete statuses.
The signing regression and full active barrier pass at `1619 passed, 1 warning`.
Parity remains strict; it is not taught to ignore conflicting signatures.

V220R14 completed with exact V220R13 behavior and full-tag parity certified 12
valid one-envelope candidates, zero cross-stage conflicts, and clean source
scope. Route verification then exposed one same-root producer/consumer gap:
exact filled candidates and selected scorecards retained stale pre-terminal
false aliases, while verifier consumers conflated proposal eligibility, current
terminal replay authority, and unavailable broker-real lifecycle truth.

V220R15 preserved exact behavior but its terminal index consumed raw order/trade
rows before canonical normalization, so the 3 selected candidate and scorecard
rows remained stale. V220R16 canonicalizes terminal row copies before ranking
and projection. The raw-terminal regression, exact V220R15 in-memory
reconciliation proof, Python compile, and full active barrier pass at
`1623 passed, 1 warning`.

V220R16 then completed with exact V220R15 behavior. Source-bound-to-executed
parity and leakage artifacts materialized for prefix
`BROAD_LIVE_AS_IF_REPLAY_V220R16_CANONICAL_TERMINAL_INDEX_RECONCILIATION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
All 3 filled candidate and selected-scorecard instances are now `trade_bound`
with current executable authority sourced from the trade ledger; the 9 other
valid signed proposals remain current-false with explicit terminal blockers.
Candidate context, instance identity, signed payload, and terminal transfer
verifier scans are clean. The only first-pass verifier issue was stale control
prefix ordering, repaired with revision-aware `V220R16` version parsing. The
certification rerun is `ok=true`, `issue_count=0`; compile, prompt hardening,
standard route artifact audit, and the `1624`-test focused barrier pass.

Commit `bdd8bdf40` and bounded storage cleanup are complete. The cleanup removed
103 ignored raw JSONLs above 100 MiB from superseded version families, reclaimed
37 GiB of physical free space, and preserved active/comparator summaries plus
smaller order/trade/flow evidence. The next action is coherent B7.2 hostile
value-transfer root-batch selection before replay. Active inputs and all
V220-V220R16 evidence remain protected by
`.context/context_os/V220R16_ACTIVE_ARTIFACT_REQUIREMENTS_AND_STORAGE_CHECKPOINT_20260711T084538Z.md`.

## V218 Completion Update - B3 Closed For Targeted Proof

Generated UTC: 2026-07-09T17:12:00Z.

V218 completed the selected B3 batch without broad replay drift:

- code/test files changed:
  - `src/research_infra/v4_timewarp_simulated_live_research_loop.py`;
  - `tests/test_v4_timewarp_simulated_live_research_loop.py`.
- proof/control files changed:
  - `.context/context_os/V218_B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR_BEHAVIOR_REPORT.md`;
  - `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`;
  - `.context/context_os/CONTINUATION_CURSOR.json`;
  - this matrix.
- behavior type: behavior-changing risk-expression repair; selection/trade set neutral in the targeted slice.
- focused verification:
  - `py_compile` passed for touched module/test and route builder/verifier/analyzers;
  - focused full-risk expression pytest cluster: `10 passed`;
  - route builder rebound quality parity prefix to V218;
  - route verifier `ok=true`, `issue_count=0`;
  - route artifact audit `ok=true`;
  - prompt hardening audit `ok=true`.
- targeted replay:
  - prefix `BROAD_LIVE_AS_IF_REPLAY_V218_B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`;
  - rows source/candidate/scorecard/order/trade/missed `29/1651/192/8/3/1647`;
  - W/L/F `3/0/0`;
  - net/gross/final R `+1.10761535 / +1.35101129 / +1.35101129`;
  - cash PnL `+989.52983936`;
  - risk cash/risk pct `2257.97537016 / 2.25`;
  - full-risk/reduced-risk filled trades `1/2`;
  - executed broker-cost REFUSED/source-gap rows `0/0`.

Interpretation: B3 now has targeted correctness proof. It did not improve the
R-multiple because the trade set did not change; it did improve honest risk
expression for one signed route-resolved filled trade. This is a bounded proof
slice, not a full-reservoir conversion claim.

## V219 Completion Update - B7.2 Failed After B3

Generated UTC: 2026-07-09T19:38:46Z.

V219 completed the hostile five-day B7.2 proof under the committed B3
risk-expression code:

- prefix `BROAD_LIVE_AS_IF_REPLAY_V219_B7_2_HOSTILE_5D_AFTER_B3_RISK_EXPRESSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`;
- rows source/candidate/scorecard/order/trade/missed `276/25006/288/68/23/24972`;
- W/L/F `14/9/0`;
- net/gross/final R `-2.82440031 / -0.79141028 / -0.79141028`;
- cash PnL `+204.17530212`;
- risk cash/risk pct `15451.27872744 / 15.25`;
- expected cost R `2.03299003`;
- order risk decisions `trade=52`, `open-reduced-risk=16`;
- filled trade risk decisions `trade=17`, `open-reduced-risk=6`;
- filled frameworks `fvg_fill=23`;
- expired unfilled orders `11`;
- executed broker-cost REFUSED/source-gap rows `0/0`;
- stress/MC from flow summary: raw net `-2.82440031`, extra cost
  `0.05/0.10/0.20R` per trade gives `-3.97440031/-5.12440031/-7.42440031`,
  Monte Carlo p50 max drawdown `-5.07770058R`, worst `-8.89294364R`.

Same-window V211 -> V219 delta:

- orders `+18`, trades `+5`, missed rows `-7`, accepted pending `+11`;
- W/L/F delta `+3/+2/0`;
- net R `+0.65026765`;
- gross/final R `+1.12149854`;
- cash PnL `+1072.50086469`;
- expected cost R `+0.47123089`;
- risk expression moved from all reduced-risk to a mix of full-risk and
  reduced-risk orders/trades.

Interpretation: B3 helped correctness and hostile value transfer, but it did not
solve B7.2. The current dominant evidence is no longer "all risk reduced"; it is
scorecard/order/fill transfer collapse and origin-family narrowing versus V89D,
V90, and V92. Candidate and scorecard counts match V92 (`25006/288`), while
V219 drops to `68` orders and `23` filled trades and only fills `fvg_fill`.
Therefore the next batch is not another broad replay or one-day tune; it is a
V219 parity/leakage pass followed by the highest same-root code/config repair.

## Selected Next Same-Root Batch - V220

Batch:
`B7_2_POST_B3_SOURCE_BOUND_TO_EXECUTED_TRANSFER_LEAK_REPAIR`

Reason: Dependency order has reached B7.2 and the hostile proof failed after B3.
The next work must explain and repair why V219 preserves candidate/scorecard
volume but loses V89D/V90/V92 order/trade breadth, especially non-FVG
origin-family transfer and stop/exit loss concentration. Do not patch another
selector symptom or run another broad replay until V219 parity/leakage artifacts
identify the dominant same-root executable leak.

Files/components affected before patch:

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
  and its V219 output artifacts;
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py` if the leak is
  scheduler/ranking/reallocation/origin-family transfer;
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py` if the leak
  is risk/order/fillability/lifecycle/exit transfer;
- route verifier/builder artifacts if parity exposes a proof-surface gap.

Expected measurable effect before replay:

- candidate -> scorecard transfer: already neutral versus V92 at `25006/288`;
  parity should identify which axes reach scorecard/order and which do not.
- scorecard -> order transfer: current leak is material versus V92
  (`68` order rows vs `239`); expected patch should raise valid order transfer
  or explicitly prove non-executability.
- order -> fill transfer: current V219 `68 -> 23` with `11` expired unfilled;
  patch should reduce invalid expiry/lifecycle loss without executing
  REFUSED/source-gap rows.
- missed positive/negative R: V219 parity must refresh same-window positive and
  negative missed R; patch must not improve by hiding missed opportunity.
- trade count: should not fall by suppression; valid non-FVG transfers should be
  recovered if parity shows they are executable.
- net/gross/final R: improvement should come from better conversion,
  scheduler/reallocation, lifecycle/fillability, or exit geometry, not from
  blocking all trades.
- W/L/F: compare against V219 `14/9/0` and V92 `37/14/0`.
- cost-refused/source-gap execution: must remain `0/0`.
- risk-reduced/full-risk distribution: full-risk authority must remain causal
  and predecision; invalid rows stay reduced/missed.

What proves the batch helped:

- parity artifacts explain source-bound -> candidate -> selector -> scheduler ->
  risk -> order -> lifecycle -> fill -> exit transfer for V219;
- same-window transfer or value improves in a targeted proof without suppressing
  opportunity;
- no REFUSED/source-gap executions;
- full-risk promotions are causal and predecision, not hardcoded buckets;
- added/recovered transfers are net positive, or negative results isolate the
  next root leak in scheduler/lifecycle/exit with exact buckets.

What proves the batch failed or exposed the next flaw:

- parity cannot explain the V92/V219 scorecard->order/trade divergence;
- the next patch improves headline R only by suppressing opportunities;
- hostile five-day remains materially negative after a targeted patch and losses
  are concentrated in promoted full-risk rows, exit/stop geometry, lifecycle
  expiry, or scheduler/reallocation starvation;
- trade count drops only by suppression while missed positive R rises;
- verifier/audit detects any authority or provenance leak.

Broker/live/final remain closed.

## V239R3 Completion Update - B7.2 Terminal Truth Closed, Economic Repair Open

Generated UTC: 2026-07-12T22:43:36Z.

The V239 series closed one same-root cross-surface failure across runtime,
compact serialization, and verifier consumers. Terminal rows now use exact
scheduler-backfilled candidate instances; POI state and lifecycle survive
compact missed output; provisional reduce-risk signing uses the strict
materialized validator; attempt identity is distinct from executable binding;
and displacement parity recognizes missed, unfilled-order, and filled-trade
terminal surfaces.

Focused proof: `1325 passed`, zero failures, one unchanged pytest
`asyncio_mode` warning. Physical route verifier: `ok=true`, issue count `0`.

Bounded V239R3 behavior is intentionally neutral to V238R3:

- candidates / scorecards / order events / logical orders / fills:
  `2469 / 92 / 13 / 7 / 6`;
- W/L/F: `3/3/0`;
- net/gross/final R: `-2.81768013/-2.26948297/-2.26948297`;
- cash PnL / risk cash / risk percent:
  `-$980.11471440 / $2439.92967918 / 2.45%`;
- expected cost: `0.54819716R`;
- stress `+0.05/+0.10/+0.20R`: `-3.11768013/-3.41768013/-4.01768013`;
- Monte Carlo total / worst drawdown: `-2.81768013/-3.34698405R`;
- executed REFUSED/source-gap rows: `0/0`.

Truth partitions are now exact: `1946/1946` required missed POI rows carry
state and causal lifecycle; `313` displacement instances reconcile across
candidate and scorecard into `307` missed and `6` order terminals (`5` filled
trades); `12/12` execution-bound order events and `6/6` trades satisfy the
canonical final-risk/fillability atom.

Disposition: terminal truth sub-batch DONE. B7.2 economic value remains OPEN.
The next dependency-correct work is causal risk-expression, scheduler
reallocation, selected-policy and exit loss transfer on the clean V239R3
denominator, then hostile-five-day and objective non-hostile proof. Broker,
live, and final remain closed.

## V243 Completion Update - B7.2 Targeted Causal Path Green

Generated UTC: 2026-07-13T01:16:08Z.

V240 bound ordered-tick selected-policy exits and canonical risk ceilings,
improving the unchanged six-trade V239 denominator by +2.44942267R. V241 then
made the valid GER40 passive long remain pending through its honest lifecycle,
which exposed a missing opposite-pending replacement path. V242 replaced the
strict fill-probability Pareto gate with a causal fill-adjusted expected-transfer
comparator only for signed opposite-side collisions, recovered the GER40 short,
and materialized a real cancel-replace. V243 fixed the remaining pending-order
identity mismatch so exposure context, signed release binding, runtime
cancellation, and terminal ledgers use the same simulated order ID.

V243 bounded result:

- candidates / scorecards / order events / logical orders / fills:
  `2469 / 92 / 14 / 7 / 6`;
- W/L/F: `4/2/0`;
- gross/final/net R: `+0.17993970 / +0.17993970 / -0.36825746`;
- cash PnL / risk cash / risk percent: `+$50.20680045 / $1199.55316609 / 1.20%`;
- broker-calibrated expected cost: `0.54819716R`;
- cancel-replace events / terminal cancellations / applied replacements:
  `2 / 1 / 1`;
- stress `+0.05/+0.10/+0.20R`: `-0.66825746/-0.96825746/-1.56825746`;
- Monte Carlo total / worst drawdown: `-0.36825746/-2.24260760R`;
- executed REFUSED/source-gap rows: `0/0`;
- diagnostic missed rows / R: `609 / -208.70818425R` with no opportunity
  suppression.

This is a targeted structural and local-value proof, not the hostile five-day,
non-hostile regime, broad-history, final-selection, or live gate. Route
certification is next, followed by bounded storage cleanup and the hostile
five-day proof. Broker/live/final remain closed.

## V244 Completion Update - B7.2 Targeted Checkpoint Certified

Generated UTC: 2026-07-13T04:49:54Z.

V244 is behavior-neutral to V243: `2469 / 92 / 14 / 7 / 6` candidates,
scorecards, order events, logical orders, and fills; `4/2/0` W/L/F;
`+0.17993970 / +0.17993970 / -0.36825746R` gross/final/net; and
`+$50.20680045` cash PnL. Added/removed trades and net-R delta are all zero.

The repair closes the two route-certification defects: all 13 execution-bound
order rows and all six trades carry executable-candidate authority sources,
and the replace-pending scorecard projects the authenticated selected candidate
identity. All 2,469 candidate-instance parity rows materialize.

The V244 manifest, physical verifier, prompt hardening, both parent verifiers,
both full artifact audits, compile, and 1,528 focused tests are green. This is
the certified one-day truth checkpoint; hostile five-day and later B7 gates
remain open. Broker/live/final remain closed.

## V245 Completion Update - B7.2 Hostile Five-Day Proof Materialized

Generated UTC: 2026-07-13T08:06:38Z.

V245 ran unchanged V244 behavior code over the full configured 24-symbol
2026-05-13 through 2026-05-17 hostile window:

- prefix
  `BROAD_LIVE_AS_IF_REPLAY_V245_B7_2_HOSTILE_5D_V244_AUTHORITY_CONVERSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`;
- source / decision / candidate / scorecard / order-event / terminal-order /
  trade / missed rows: `310 / 11424 / 25006 / 288 / 45 / 22 / 20 / 24984`;
- W/L/F: `11/9/0`;
- gross/final/net R: `+2.97415738 / +2.97415738 / +1.37913341`;
- cash PnL / risk cash / aggregate risk:
  `+$107.53831449 / $3210.87073032 / 3.20%`;
- broker-calibrated expected cost: `1.59502397R`;
- passive-queue / source-safe-immediate fills: `12/8`;
- expired unfilled / cancelled-replaced terminal orders: `1/1`;
- full-risk / reduced-risk fills: `0/20`;
- executed REFUSED/source-gap rows: `0/0`;
- extra-cost stress at `0.05/0.10/0.20R` per trade:
  `+0.37913341/-0.62086659/-2.62086659R`;
- Monte Carlo p50/p05/worst maximum drawdown:
  `-3.81676154/-6.16433455/-7.23878296R`.

The full candidate and scorecard denominator matches V219. Relative to V236,
V245 adds 18 fills and improves net R by +2.30473121R, so the positive base
case is not manufactured by candidate suppression. Relative to V219 it uses
three fewer fills and improves net R by +4.20353372R while materially reducing
risk; exact identity deltas are unavailable because superseded V219 raw
candidate/trade ledgers were removed under the bounded storage contract, so
that comparison remains aggregate-only.

Window-normalized parity is exact: 1,101 package axes, 894 candidate-generated
axes, 17 scorecard/order-present axes, and 15 filled axes. The dated additive
source-bound R denominator is zero in this exact window; the global
1,249,248.03066685R reservoir remains diagnostic and is not a five-day
denominator. Candidate-instance projection contains 25,006 unique rows, 2,402
valid signed predecision instances, 2,382 final-blocked instances, and 20
order-bound instances. Mixed diagnostic missed R is +804.95137893R positive,
-2,401.66853978R negative, and -1,596.71716085R net.

Disposition: B7.2 hostile materialization is behaviorally positive and truth
complete enough to advance, but it is not robust enough to close B7. All fills
remain reduced-risk and 0.10R-per-trade stress is negative. Selected-policy
exits improve aggregate R, so no outcome-fitted exit patch is justified from
this window alone. Before B7.3, an immutable V245 snapshot audit will reconcile
selector/risk, scheduler/origin, fill/lifecycle, exit, parity, and verifier
findings. If no reproducible hard truth defect remains, unchanged code advances
to the objective non-hostile 2026-06-01 through 2026-06-05 gate. Broker/live/
final remain closed.

## V246/V247 Update - B7.2 Signed Order-Policy Lifecycle Authority

Generated UTC: 2026-07-13T11:53:00Z.

V246 was the smallest JP225/XAGUSD/POI producer proof after the five V245
route-truth findings were patched. It produced 597 candidates, 92 scorecards,
three order events, one terminal order, zero fills, and 596 missed rows. XAGUSD
retained ordered-tick source-gap fill-realism as its terminal blocker, POI
outer replay time and source generation time remained distinct, and JP225
preflight correctly recognized signed `open-reduced-risk` authority. V246 then
exposed one same-root B7.2 consumer defect: late order/lifecycle routing used
mutable `risk_decision=trade` and lost the immutable signed action already
consumed by preflight.

The V247 code batch introduces one validated signed order-policy action
resolver and makes preflight, late route choice, passive queue, soft fallback
envelope, order metadata, and terminal ledgers consume it. Mutable finalizer
risk remains separately preserved. Invalid or tampered authority fails closed
to the mutable action. Compilation, five direct action tests, 20 adjacent
preflight/finalizer tests, and the 1,127-test POI/runtime/verifier barrier pass.

Disposition: B7.2 signed order-policy consumer implementation is CODE-DONE and
TARGETED-PROOF-OPEN. The next run is only the one-day JP225/XAGUSD V247 proof.
It must preserve candidate/scorecard/order/missed counts, produce no fabricated
fill, retain XAGUSD source-gap classification, and show JP225 mutable `trade`
beside valid signed/effective `open-reduced-risk`, canonical passive-queue
authority, and a consumed degraded fallback envelope. A green result permits
V245 producer regeneration/certification; it does not close B7.3, broad-history,
final-selection, or live gates. Broker/live/final remain false.

## V248 Update - B7.2 Terminal Transfer Consumer Proof Open

Generated UTC: 2026-07-13T12:07:53Z.

V247 closes the signed order-policy action and lifecycle route: exact V246 row
counts and identities are preserved, JP225 remains honestly expired with valid
signed open-reduced passive authority, XAGUSD remains ordered-tick source-gap
blocked, and POI time/partition checks are exact. One final transfer consumer
defect remains. Post-terminal scorecards carry canonical terminal binding
status and ID, but the final transfer resolver ignores those aliases and
rewrites the scorecard unbound.

The V248 patch makes canonical terminal order/trade binding aliases first-class
inputs to final transfer resolution while preserving the signed-authority
requirement. Compilation and the 1,129-test adjacent barrier pass, and the exact
V247 scorecard resolves in memory to `order_bound` with its real order ID.

Disposition: B7.2 signed action is TARGETED-PROOF-DONE; terminal transfer alias
consumption is CODE-DONE and TARGETED-PROOF-OPEN. V248 is the final identical
JP225/XAGUSD proof for this same-root chain. No broad or economic claim is
authorized by it. Broker/live/final remain false.

## V249 Update - B7.2 Five-Day Producer Regeneration Ready

Generated UTC: 2026-07-13T12:19:00Z.

V248 passes the complete bounded signed-action and terminal-binding chain. The
JP225 scorecard is `order_bound` to its exact expired order; candidate and
missed identities are unchanged; XAGUSD and POI truth are unchanged; route-
shaped scanners are green. The storage checkpoint protects V245/V248 and
removes only superseded V246/V247 raw JSONL files under a hash manifest.

V249 now regenerates the full 24-symbol hostile five-day producer surface on
current code. It retains a complete compact candidate-index ledger and all
decision, scorecard, order, oracle, trade, missed, source, bucket, and summary
surfaces while omitting duplicate full candidate-packet and packet-sidecar
serialization. This is full-denominator compact proof, not narrowing.

Disposition: B7.2 targeted truth chain DONE; five-day producer regeneration
and route certification IN PROGRESS. B7.3 remains dependency-blocked until
V249 is parsed and certified. Broker/live/final remain false.

## V249 Completion Update - B7.2 Route Certification Open

Generated UTC: 2026-07-13T14:48:06Z.

`BROAD_LIVE_AS_IF_REPLAY_V249_B7_2_HOSTILE_5D_V248_SIGNED_ACTION_TERMINAL_BINDING_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
completed once with the full V245 candidate, scorecard, order, fill, and missed
identity sets intact. Parity artifacts are built and materialized from the
25,006-row authoritative compact candidate index; the projection has 25,006
unique rows, zero duplicates, and exact prefix/window/profile scope.

Physical behavior is 20 trades, 11/9/0 W/L/F, +2.75652827R gross/final,
+1.16150430R net, and +$201.14669730 cash. Ordered-tick headline authority is
18 trades and +0.28044419R net; two M1-only physical rows remain explicit
diagnostics. Relative to V245 there are zero added or removed trades. The
-0.21762911R physical delta and higher cash/risk exposure come from signed
sizing and broker volume quantization, not candidate suppression.

Disposition: V249 replay, comparison, flow, parity, compact POI proof, and
route certification are DONE. The manifest binds the repair program, exact
rehydration result, and bounded behavior comparison summary/dossier; the
physical verifier is `ok=true` with zero issues and the integrated barrier is
1,390 passing tests. B7.2 is closed for this proof step.
B7.3 is the next open dependency. Broker/live/final remain false.

## V249 Route Certification Closure - B7.3 Next

Generated UTC: 2026-07-13T16:17:53Z.

The canonical route rebuild and physical verifier completed on the exact V249
prefix. All 14,517 POI-required compact candidate rows carry complete atomic
state/lifecycle projections after exact identity-neutral rehydration of 14,223
rows; identity order is unchanged and conflicts are zero. Physical trade truth
is reconciled separately from ordered-tick headline authority at 20 versus 18
rows. The verifier completed at `2026-07-13T16:50:42Z` with `ok=true` and zero
issues; prompt hardening, route/parent audits, parent verifiers, and 1,390
integrated tests are green.

Disposition: B7.2 DONE and route-certified. This does not make the system
stress robust or final/live ready. B7.3 must run unchanged V249 behavior code
over the full configured 2026-06-01..05 independent regime and compare against
same-window V104/V110B evidence. No window-specific policy tuning is permitted
between B7.2 and B7.3. Broker/live/final remain false.

## V250 Completion Update - B7.3 Route Certified, B7.4 Next

Generated UTC: 2026-07-13T21:31:31Z.

V250 completed once on unchanged V249 behavior over the full configured
2026-06-01..05 independent-regime surface. Physical behavior is 13 trades,
8/5/0, +7.03578717R net, and -$68.02401535 cash. Ordered-tick headline
authority is four trades, 3/1/0, +1.59506223R, and -$67.96685163 cash; stress
remains positive through +0.20R per trade. This is bounded evidence, not a
final economic claim.

The post-replay truth batch is DONE. Current terminal execution contracts now
survive into parity; all 13 physical trade candidate identities have an
executable trace; the exact five-day executable-gated denominator is
356027.9026815028R; and the deterministic surface contains 22,971 parity rows,
35,191 candidate projections, and 1,101 leakage buckets. The comparator emits
all 9 added, 4 common, and 42 removed exact V104 identities. Every removed
V104 outcome is M1-proxy diagnostic authority: 9 are absent under current
candidate generation, 16 stop at selector admission, 16 at scheduler
allocation, and 1 at order/fillability/lifecycle. These rows do not authorize
weakening broker cost, session, fillability, lifecycle, or signed authority.

The focused barrier is 273 passing tests. The canonical route manifest binds
V250, the physical verifier reports `ok=true` with zero issues, prompt
hardening is green, and the standard route artifact audit reports no missing
required or warning artifacts. Replay behavior did not change. Broker/live/
final remain false.

Disposition: B7.3 is DONE and route-certified as an independent five-day
proof. B7.4 is now the next Fable dependency: commit this truth checkpoint,
write a fresh pre-replay brief, and run unchanged certified behavior once over
2026-06-01..19 before policy tuning or B7.5 extended-history work.

## B7.4 Pre-Replay Serialization Scalability Checkpoint

Generated UTC: 2026-07-13T22:04:30Z.

Commit `46261cecd` closes and preserves V250. Bounded sparse dematerialization
completed without deleting commit/LFS evidence, but the five-day V250 proof
still exposes exact serialization duplication that would make the unchanged
19-day proof unnecessarily unsafe for disk capacity: all 11,520 decision rows
repeat the complete current-FVG partition under the producer audit, all 480
scorecards write the same option trace three times, and the long-window
candidate-index omission mode reports zero top-level candidates instead of the
exact missed/order/trade relational union.

The active batch is `B7_4_BROAD_PROOF_SERIALIZATION_SCALABILITY`. It is
behavior-neutral and dependency-safe: preserve one canonical complete decision
partition and scheduler trace, preserve all finalizer probes and immutable
authority, make the relational candidate surface exact and verifier-scanned,
then run unchanged current behavior once over 2026-06-01..19. No selector,
scheduler, risk, cost, fillability, lifecycle, or exit tuning is permitted in
this batch. Broker/live/final remain false.

## B7.4 Serialization Focus-Proof Closure - Broad Proof Ready

Generated UTC: 2026-07-13T22:40:38Z.

The behavior-neutral serialization batch is DONE. Exact V250 object streaming
certifies all 11,520 decision projections at 53.123186% of prior bytes and all
480 scorecard projections at 47.594139%, with no missing canonical payload.
The V251T one-day XAUUSD integration proof materializes 531 candidates through
an exact 531-row missed/order/trade relational union while candidate and
candidate-index JSONLs remain omitted. All 92 eligible decision projections
and all 92 scorecard projections pass; candidate quality, scheduler parity,
identity, displacement, and projection verifier defects are zero.

The implementation includes every required producer and consumer: compact
decision/scorecard writers, candidate relational fail-closed audit, exact
summary accounting, parity fallback, selected-bridge trace fallback, relational
candidate verifier source, risk-authority preservation, and focused verifier
invariants. Compile and 579 focused tests pass. This checkpoint does not change
candidate generation, selection, scheduling, sizing, orders, lifecycle, fills,
exits, or R.

Disposition: B7.4 focused serialization proof DONE; B7.4 unchanged
2026-06-01..19 broad replay READY and next. The broad replay must provide
non-vacuous order/trade proof, exact-window behavior, parity, stress/MC, and
missed-opportunity accounting before any policy repair or B7.5 work.
Broker/live/final remain false.

## B7.4 Runtime-Input Authority Repair - Targeted Proof Green

Generated UTC: 2026-07-13T23:59:15Z.

V251 was intentionally interrupted after its first five-day chunk because it
kept V250's 35,191 candidates and 480 scorecards but emitted zero orders and
trades. The defect was infrastructure truth, not selector performance: sparse
checkout had retained the 82-row sleeve registry while dematerializing the
1,101-row `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` consumed by executable
member-axis admission. The old loader silently converted that missing input
into an empty authority surface.

The harness now resets stale prefix outputs and validates both runtime inputs
for file presence, nonzero bytes, exact row count, schema, unique identity, and
SHA-256 before `run_campaign`. The contract is present in partial/final
summaries and enforced by the route verifier for current compact-relational
proofs. Missing, empty, corrupt, duplicate, and real hydrated inputs plus the
actual execution-boundary fail-closed path are covered; compile, diff check,
and 588 focused tests pass.

V252T on June 2 XAUUSD proves non-vacuous restoration: 490 candidates, 92
scorecards, seven pre-finalizer new-position selections, one final signed
selection, two order events, one terminal fill, one physical trade, and 489
missed rows. The selected 10:15 SHORT candidate binds
`member_axis:b7675740a77eb12478f575d2`, PASSED broker cost, valid immutable
authority, and 0.10% replay risk. REFUSED/source-gap/unsigned execution is
`0/0/0`. Its +1.96363578R M1-proxy result is diagnostic, not headline, because
June 2 XAUUSD ordered-tick terminal truth is absent.

Disposition: runtime-input authority repair targeted proof DONE. V253 is the
single next B7.4 broad proof. Its June 1-5 nested chunk must reproduce V250's
behavior checksum before the June 1-19 result can be interpreted. This is not
a final/live claim; broker/live/final remain false.

## B7.4 Capacity-Safe Chunk Continuity - Focused Proof Green

Generated UTC: 2026-07-14T01:53:02Z.

V253's first flushed June 1-5 chunk exactly reproduced V250: 35,191
candidates, 480 scorecards, 30 order events, 14 terminal orders, 13 physical
trades, 8/5/0, +7.82542991R gross/final, +7.03578717R net, four headline
trades at +1.59506223R net, and zero REFUSED/source-gap/unsigned execution.
It is not a completed broad proof. The worker retained a 52 GiB Python object
graph, used more than 27 GiB swap, and reduced free disk to 5.1 GiB before the
second chunk could complete. The run was intentionally stopped, deterministically
salvaged as `interrupted_partial_not_final_proof`, and its eight raw JSONL
artifacts were row-counted and SHA-256 bound before bounded deletion.

The harness now executes an explicit capacity-safe chunk contract. It reuses
the same `SimulatedBroker` and `AccountState`, carries a monotonic selected
order sequence, flushes every chunk ledger and partial checkpoint, releases
completed result/source references, evicts only the completed day-scoped
source caches, and performs explicit collection while automatic GC remains
disabled. The route verifier enforces this contract only when the current
summary opts in, preserving historical summary compatibility. Compile, scoped
diff check, and 592 focused harness/parity/verifier tests pass.

Disposition: capacity-safe implementation proof is DONE; behavioral
equivalence is still OPEN. The single next proof is V254T over 2026-06-01..05
with one-day chunks. It must reproduce V250 exactly across transfer counts,
trade identities, W/L/F, gross/final/net R, headline/diagnostic partitions,
missed rows, and safety counts while recording five valid cleanup checkpoints
without cumulative memory growth. Only then may the June 1-19 V254 broad proof
run. Broker/live/final remain false.

## B7.4 Replay Source-Cache Identity Repair - Focused Proof Green

Generated UTC: 2026-07-14T05:51:40Z.

V256 completed all five one-day chunks and exited zero, but it is rejected as
semantic evidence. Its candidate surface fell from V250's 35,191 rows to
29,985, with only 24,879 common identities, 10,312 V250-only identities, and
5,106 V256-only identities. The first day matched exactly; drift accumulated
only after source release and collection. The static 24-symbol source-plan
digest remained invariant, so the defect was below the plan boundary.

The exact root cause was a process-global closed-bar cache keyed by
`id(source_rows)`, row count, and timeframe without retaining or validating the
source tuple. Python reused released tuple IDs after explicit GC, allowing a
later symbol to receive another symbol's candle index. The same unsafe pattern
also existed in the predecision-tick cache and both selected-bridge identity
caches. The same-root batch now retains and validates every exact source object,
does not persist non-tuple row iterables, clears closed-bar, row-time, and
predecision-tick caches before GC, reports before/after cache counts, and makes
capacity contract v2 plus the route verifier require zero remainder after every
chunk.

Focused proof is green: compile passes; 624 B7.4 package/harness/parity/verifier
tests pass; all 820 timewarp tests pass. A real-source lifecycle probe hydrated
all 24 symbols, exercised 96 June 1 decision windows, cleared 96 closed-bar
entries to zero, rebuilt June 2 after GC, and matched cached versus uncached
JP225/USDCAD D1/H4/H1/M15 payloads on all eight checks. No selector, scheduler,
risk, cost, order, lifecycle, fill, or exit policy changed.

Disposition: the cache-identity implementation batch is DONE for focused proof;
five-day equivalence remains OPEN. V257 is the single next B7.4 proof and must
restore V250's exact daily candidate counts `7244/7175/6603/6981/7188`, all
35,191 candidate identities, exact order/trade/missed values, V250 economic
metrics, zero safety leaks, and zero replay-source cache entries after each
chunk. V256's apparent diagnostic R is invalid because its candidate inputs
were cross-symbol contaminated. Broker/live/final remain false.

## B7.4 V257 Cache-Safe Comparator Acceptance

Generated UTC: 2026-07-14T07:38:32Z.

V257 completed all five one-day chunks and is accepted as the exact bounded
correctness comparator. It restored V250's daily candidate counts
`7244/7175/6603/6981/7188`, all 35,191 candidate-instance identities, all 16
ordered identities, all 13 filled identities and economic values, and all
35,177 missed decision/value projections. Order rows are exact after removing
only run-instance timestamps/hashes, prefix-bound simulated IDs, and the M1
source hash that intentionally describes each chunk's requested day scope.

Behavior remains V250-exact: 13 physical rows, 8/5/0,
`+7.82542991/+7.82542991/+7.03578717R` gross/final/net and
`-$68.02401535` cash; ordered-tick headline authority is four rows, 3/1/0,
`+1.59506223R` net and `-$67.96685163` cash. The only truth delta is corrective:
nine M1-proxy diagnostic rows are no longer mislabeled as strict full-package
parity eligible. Headline eligibility and economic values did not change.

Capacity contract v2 and source-authority invariance are valid across all five
chunks. Account/broker continuity and order sequence are monotonic, and
closed-bar, predecision-tick, and row-time caches are zero after every cleanup.
Executed broker-cost REFUSED, source-gap, and unsigned-authority rows remain
zero. The hash-bound acceptance/retention manifest and compact candidate,
missed-value, order-semantic, and trade-semantic projections preserve the proof
after deleting only the three regenerable raw decision/scorecard/missed files.

Disposition: the B7.4 cache-identity and bounded-chunk same-root batch is DONE.
V250 remains the complete parity-built broad-quality anchor until the larger
June 1-19 package is materialized. Route recertification and checkpoint commit
come next, followed by a fresh storage/pre-replay brief and the June 1-19 B7.4
run. This is not total-reservoir, final-selection, or broker-live proof.

## B7.4 V257 Route Recertification Closure

Generated UTC: 2026-07-14T08:30:27Z.

The V257 cache-identity checkpoint is route-recertified. The canonical builder
completed successfully after hydrating its exact compact source and bridge
dependencies. `OUTPUT_MANIFEST.json` now binds the complete V250 broad-quality
anchor rather than the legacy field-parity fallback. The physical route
verifier reports `ok=true` with zero issues; goal-prompt hardening passes; the
active denominator-to-deployment route and parent full-plan route both pass
full JSONL artifact audits; and `git diff --check` is clean.

Focused implementation proof remains green: compile passed, the 624-test B7.4
package/harness/parity/verifier suite passed, all 820 timewarp tests passed,
and the final 12 cache/source/capacity regressions passed. No selector,
scheduler, risk, cost, order, lifecycle, fill, exit, or trading policy changed
during recertification.

Disposition: V257 implementation, exact V250 equivalence, capacity contract v2,
and route recertification are DONE. Commit this scoped checkpoint, then record
the V258 storage/pre-replay contract, dematerialize only bounded hydrated proof
payloads while retaining hash-bound evidence, and run the unchanged June 1-19
B7.4 broad proof. Broker/live/final remain false.

## B7.4 V258 Pre-Replay Storage Gate

Generated UTC: 2026-07-14T08:45:29Z.

The V257 code and route-recertification checkpoint is committed at
`dae7c620b`. A fresh V258 pre-replay brief fixes the exact June 1-19 command,
nested V250/V257 checksum, transfer/economic measurements, anti-suppression
contract, and success/failure criteria before launch.

Storage cleanup dematerialized 137 clean tracked route JSONL working copies
totalling 14,847,342,984 logical bytes. It did not alter the Git index, commit
history, or local LFS objects. The 82-row sleeve registry, 1,101-row exact
member-axis authority ledger, all retained V257 compact proof, every dirty
file, and all untracked evidence remain present. Free space is 25,269,448 KiB;
after the 13,347,782,507-byte V258 raw-output projection, the expected reserve
is 11.668 GiB, above the fixed 8 GiB launch floor.

Disposition: the V258 pre-replay and storage gate is DONE. The unchanged
June 1-19 B7.4 run is next. It must reproduce V250/V257 exactly inside June
1-5, preserve one source-plan digest and zero replay-source cache remainder,
and materialize the complete larger-window behavior/flow/parity/stress/Monte
Carlo package. Broker/live/final remain false.

## B7.4 V258 Source-Authority Failure And Root Repair

Generated UTC: 2026-07-14T09:33:43Z.

The first V258 attempt failed before campaign execution. Its 19-day immutable
source plan resolved zero of 24 symbols because the configured D1/H4/M15
families ended on June 9/10. It produced no candidate, scorecard, order, fill,
missed-value, R, stress, or Monte Carlo behavior and remains an explicit
`failed_partial_not_final_proof` tombstone rather than an economic result.

The complete same-root source batch is now implemented. Read-only FTMO exports
provide 72 D1/H4/M15 files and 24 M1 files through June 19 with zero export or
manifest-hash errors. The resolver searches declared families globally across
roots, composes original and supplemental M1 per symbol-day, retains original
monthly priority where populated, and fails closed on any overlapping-day row
conflict. The exporter retries only the final historical request window with a
bounded delay and retains the newest/most complete response.

Real-data proof is green: 24/24 symbols, 120 static/tick plan rows, 24 tick
authorities, full-plan digest `eeed6163d40b5a33...585fa7`; 456 M1 symbol-days
partition into 368 floor-passing and 88 exact no-session days; 172 populated
old/new overlaps match and zero conflict. The nested June 1-5 plan digest is
exactly V257's `8c6fa609d07832a8...5a4d6b`, so accepted source inputs are
unchanged. Compile, 490 harness/verifier tests, 126 parity/comparator/export
tests, and all 820 timewarp tests pass. No trading policy changed.

Disposition: B7.4 source-authority repair DONE for focused and real-data proof;
the V258 broad retry is next. It must still prove exact nested candidate and
behavior projections during execution and then materialize June 6-19 economic
behavior. Broker/live/final remain false.

## B7.4 V258 Source And Route Recertification Closure

Generated UTC: 2026-07-14T11:05:03Z.

The source-authority checkpoint is physically route-recertified. The canonical
builder completed after hydrating its exact bridge/grid and V250 proof closure;
it binds V250 as broad-quality authority and V254T as holdout gate. The builder
now requires a paired flow bucket whenever a flow summary exists. The verifier
selects the newest physically complete replay, so compact-retained V257 cannot
displace V250 while its large raw proof ledgers are intentionally absent, and
source-package counts are checked against the current builder outputs rather
than stale literals.

Physical verification is `ok=true` with zero issues. Current source-package
counts are 509 total and 484 FTMO blockers. Compile, 492 harness/verifier tests,
126 parity/comparator/export tests, and all 820 timewarp tests pass. Prompt
hardening and both route and parent full-JSONL artifact audits pass. This batch
changes proof authority and storage correctness only; selector, scheduler,
risk, order, lifecycle, fill, exit, and economic behavior are unchanged.

Disposition: the B7.4 source and route checkpoint is DONE. After final scoped
diff/commit and bounded post-proof dematerialization, the unchanged V258 June
1-19 campaign is the next behavioral proof. Broker/live/final remain false.

## B7.4 V258 Post-Recertification Storage Gate

Generated UTC: 2026-07-14T11:19:12Z.

Checkpoint `6d812ee74` is committed. The bounded cleanup dematerialized 130
clean tracked, commit/LFS-recoverable route JSONLs totaling 13.777 GiB. It
retained the 82-sleeve registry, 1,101-axis execution authority, all V257
retained proof, source exports, summaries/manifests, V258 tombstone, and every
dirty or untracked artifact. Free space is 26,697,808 KiB and projected reserve
after V258 is 13.030 GiB, above the 8 GiB floor.

Disposition: storage gate DONE. The exact unchanged V258 June 1-19 campaign is
launch-ready. Broker/live/final remain false.

## B7.4 V258 Behavior And Proof-Consumer Route Certification

Generated UTC: 2026-07-14T23:22:00Z.

V258 completed all 19 one-day chunks over 2026-06-01..19 with the unchanged
certified package and exact nested V250/V257 behavior. It materialized 104,434
candidates, 1,440 scorecards, 108 order events, 43 terminal orders, 42 physical
fills, and 104,391 missed rows. Physical behavior is 23/19/0 and
+15.08858577R net with +$188.99882038 cash. Ordered-tick headline behavior is
3/1/0 and +1.59506223R with -$67.96685163 cash. Executed REFUSED/source-gap
rows remain 0/0; one terminal order expired explicitly.

The complete same-root proof-consumer repair is closed. Diagnostic missed R is
read from its canonical opportunity field without promotion to executable
authority; 19,754 diagnostic-scoreable rows reconcile to -14,229.43645764R and
84,637 rows remain unscoreable. Sparse parity builds in about 5.23 GiB peak RSS
and reports 1,101 axes -> 961 candidate axes -> 484 scorecard/order axes -> 25
filled axes against the exact 80,388.20018256R June-window denominator.

The recovered 95-row V110B trade ledger is hash-bound. The comparison has 14
common, 28 added, and 81 removed exact trade identities. All 43 removed V110B
winners have a named current predecision blocker. V258 scorecards 1,440 exceed
V110B 1,056, and V258 expiry 1 is below V111 28. The compact-flow verifier now
merges declared relational counts with physical ledger counts field by field,
so intentionally omitted candidate ledgers do not become false zero counts.

Canonical OUTPUT_MANIFEST contains 201 entries. The physical verifier reports
ok=true and issue_count=0. Compile passes; 1,457 touched tests pass with the one
pre-existing unknown asyncio_mode warning; prompt hardening, both route and
parent full-JSONL artifact audits, and both parent verifiers pass.

Disposition: B7.4 DONE and route-certified. B7.5 is next: select and bind at
least two non-adjacent reservoir-covered months under identical code/config,
then run window-normalized extended-history proof. Broker/live/final remain
false.

### B7.5 Risk-Status Stage Alias R2 Checkpoint - 2026-07-15

The first January 22-23 exact-row proof is evidence, not accepted current-code
proof. It closed the missing-status and prefinal signed-authority defects, then
exposed seven terminal rows whose top-level pre-scheduler status conflicted
with nested finalizer authority. Nested final authority now owns the canonical
top-level alias; the pre-scheduler packet remains intact as the stage-specific
prefinal surface. Complete focused runtime/verifier coverage is `1,160` passing
tests. This is a correctness repair with no policy-threshold change.

The cold-start target also proved that exact-date economics cannot be compared
directly with warmed full-January adaptive-memory behavior. Two January 22
XAUUSD fills absent from the full-month ledger were previously blocked only
after January 1-21 state accumulated. R2 targets therefore prove status,
fill-floor, signature, cost, source, and relational truth. Full January under
shared digest `b5f44606...1acfce` is the behavioral comparator. B7.5 remains
PARTIAL until both R2 targets, warmed January regeneration, route consumers and
verifier, April unchanged, and cross-window generalization are complete.

### B7.5 Compact Fill-Floor Provenance R3 Barrier - 2026-07-15

R2 closes the mixed-stage risk-status alias and prefinal XAUUSD verifier
contracts on the January 22-23 slice, with zero executed REFUSED/source-gap
rows and unchanged cold-start behavior. It newly exposes a terminal proof
consumer defect: runtime attribution and scorecard probes retain the exact
`expected_net_r` fill-floor cause, while compact missed serialization dropped
that provenance. The compact serializer now preserves all five fill-floor
authority fields across scheduler, pre-risk-finalizer, risk-finalizer, and
finalizer-primary stages. Producer and consumer tests plus the complete
harness/verifier/runtime barrier pass 1,342 tests.

Disposition: implementation is focused-green and behavior-neutral by design;
R3 artifact regeneration remains OPEN. Run January 22-23 once under shared
digest `d2edfc05...e65f`, prove exact compact floor provenance and all R2 safety
contracts, then run January 29-30 for the other two exact rows. Only after both
targets pass may the warmed full-January B7.5 artifact and route consumers be
regenerated. Broker/live/final remain false.

### B7.5 Terminal Blocker Stage R4 Barrier - 2026-07-15

R3 completed with unchanged cold-start economics and closed compact provenance.
Its full transfer scanner then exposed 478 explicit prefinal proposals whose
final missed blocker did not correspond to unresolved package fill-floor
authority, plus one XAUUSD scorecard whose terminal reconciliation retained a
before-terminal executable claim but omitted the equivalent prefinal stage
alias. These are truth-stage defects, not policy evidence.

The coherent producer/consumer repair gives unresolved package authority
canonical primary-blocker precedence while retaining other reasons as
co-blockers, makes missed attribution prefer its recomputed transfer contract,
and preserves true prefinal executable claims/provenance before terminal truth
is projected into candidate and scorecard rows. Current-code projection over
all 15,297 R3 missed rows reduces the 478-row defect set to zero; reconstructed
XAU stage reconciliation has zero proposal reasons. Compile and diff check pass,
and the complete focused barrier passes 1,345 tests.

Disposition: implementation is focused-green and expected behavior-neutral.
The R4 replay-free contract is valid under shared digest
`44a8c046...c8c27` and unchanged January/April source plans. Run January 22-23
R4 once and require exact R3 counts/economics, zero preserved-proposal scanner
errors, complete compact floor provenance, exact status aliases, and zero
executed REFUSED/source-gap rows. Only then proceed to January 29-30. Broker,
live, and final authority remain false.

### B7.5 Terminal Blocker Stage R4 January 22-23 Completion - 2026-07-15

R4 completed the first bounded all-symbol proof with 15,304 candidates, 4,608
decisions, 192 scorecards, 18 order events, seven terminal orders/trades, and
15,297 missed rows. It is behavior-neutral to R3: one ordered-tick headline
winner remains `+0.60931716R`, all seven physical rows remain `+3.15530942R`,
and normalized order/trade identities have zero additions, removals, or
economic changes.

All current proof consumers are green. Candidate quality scans 15,304 rows and
14,128 package rows with no missing or scheduler-parity fields. Transfer,
broker-cost, and path-provenance scanners have empty `bad_counts`; executed
REFUSED/source-gap rows are zero. The exact EURUSD expected-net-R floor row
keeps raw/unresolved `[expected_net_r]` and resolved `[]`. The exact XAU
scorecard and order preserve true prefinal candidate/order authority before
terminal fill-realism truth demotes the proposal.

Disposition: the first R4 slice is DONE as a bounded truth-contract proof. The
second January 29-30 R4 slice remains OPEN and is the next dependency step.
Warmed full-January regeneration, April, cross-window comparison, B7 final
selection, and B8 remain open. Broker/live/final remain false.

### B7.5 Terminal Blocker Stage R4 January 29-30 Completion - 2026-07-15

The second R4 slice is DONE as a bounded truth-contract proof. It produces
10,751 candidates, 4,608 decisions, 192 scorecards, eight order events, three
terminal fills, and 10,748 missed rows. The three diagnostic fills remain
`-1.64391447R`; headline trade count remains zero. Candidate/scheduler quality,
order transfer, broker cost, path provenance, capacity, source binding, and the
two exact expected-net-R floor rows all pass with empty error maps.

The eighth order event is one non-terminal diagnostic XAU row. The prior
warmed-January missed ledger already contains the same exact instance as a
rank-one proposal final-blocked by the same ordered-tick source gap. Therefore
the delta is explicit proof materialization, not an added order or fill.

Disposition: both targeted R4 slices are DONE. Warmed full-January R4
regeneration and its flow/parity/manifest/verifier rebuild are OPEN and next;
April and cross-window comparison remain downstream. The bounded storage check
found 118 GiB free versus a 14 GiB prior January artifact set, so no active
evidence needs deletion before the new-prefix run. Broker/live/final remain
false.

### B7.5 Warmed Full-January R4 Completion - 2026-07-15

The corrected R4 code completed January 1-31 over all configured symbols in 31
capacity-safe one-day chunks under shared digest `44a8c046...c8c27` and the
unchanged January source plan. It materialized 154,390 relational candidates,
69,888 decisions, 2,016 scorecards, 147 order events, 61 terminal fills, and
154,329 missed rows. Candidate quality/scheduler parity, order-executable
transfer, broker-cost authority, and path-provenance scanners all have empty
error maps. Executed REFUSED/source-gap rows remain `0/0`.

The repair is exactly behavior-neutral to the prior warmed January run: 61
common trades, zero added, zero removed, and zero delta in all counts,
economics, axis transfer, or denominator fields. The cold January 29-30
provisional 148th order is absent under warmed adaptive state; its exact XAUUSD
candidate remains rank one in missed and final-blocked by ordered-tick fill
realism, so the accepted warmed order-event count is 147.

All physical behavior remains 61 trades, W/L/F `24/37/0`, net/gross/final
`-2.76396743/+0.94088713/+0.94088713R`, cash `-$1595.02061428`. The
ordered-tick headline remains four trades, W/L/F `3/1/0`, net/gross/final
`+0.98832036/+1.30562064/+1.30562064R`, cash `+$98.24769712`. Missed
diagnostic opportunity remains `26812` scoreable rows at `-24212.54521713R`;
no missed row has executable ordered-tick authority.

Disposition: the warmed January R4 replay and its flow/parity/comparison
consumers are DONE. Canonical route certification is the immediate open step.
After it is green and committed, run April once under the same shared digest
and its bound source-plan digest, then perform the required cross-window B7.5
comparison. Broker/live/final remain false.

### B7.5 Warmed Full-January R4 Route Certification - 2026-07-15

The canonical builder binds the January R4 prefix in a 202-file manifest with
23 prefix artifacts and four declared compact replacements. The canonical
physical verifier reports `ok=true`, `issue_count=0`; candidate quality covers
154,390 rows with zero violations, and order-transfer, broker-cost, and
path-provenance scanners have empty bad-count maps. Compile, prompt hardening,
the standard artifact audit, and scoped diff validation all pass.

Disposition: January R4 route certification is DONE and behavior-neutral.
April 1-30 under the identical shared execution digest and its exact bound
source plan is the next B7.5 dependency. No package policy changes are allowed
between the paired windows. Cross-window generalization, B7 final selection,
and B8 remain open; broker/live/final remain false.

### B7.5 January-April Cross-Window Truth - 2026-07-15

April completed all 30 chunks under the same execution digest as January and
its distinct bound source plan. It materialized 135,289 candidates, 1,920
scorecards, 134 order events, 56 physical fills, and 135,233 missed rows.
Physical behavior is `23/33/0` and `-2.04815835R`; ordered-tick headline is
`2/4/0` and `-2.55554047R`. January plus April headline is `5/5/0` and
`-1.56722011R`. All executed cost packets remain PASSED/source-bound.

The deterministic four-window analyzer and seven focused tests prove the pair
is disjoint, non-adjacent, source/config bound, opportunity-preserving, and
broker/live/final closed. The economic generalization gate remains false.

Frozen audit exposed two current correctness defects before another replay:

1. exact-window parity sums explicitly non-additive member-axis signal values
   after downstream executable gating and emits an invalid executable-R
   percentage;
2. later terminal-path uncertainty suppresses 22 accepted April order intents,
   including 12 with independent entry-fill truth, hiding pending risk and
   same-symbol state.

Disposition: B7.5 remains PARTIAL. First close the behavior-neutral transfer
semantics, post-run pair/hash binding, and row/event/instance/axis unit batch.
Then implement and target-prove selected-intent / entry-fill / terminal-R
lifecycle separation. Pressure-only risk-cap discrimination and the mixed
cross-window exit challenger remain later causal batches. No broad replay or
B8 promotion precedes these repairs; broker/live/final remain false.

### B7.5 Transfer-Semantics Closure - 2026-07-15

The behavior-neutral truth batch is DONE. The execution contract now has two
explicit authorities: a behavioral digest derived only from replay-affecting
code/config/options/package inputs, and a separate post-run parity/verifier
digest. January and April match on behavioral digest
`84e6de36...35c3249`; their original full compatibility digest remains
`44a8c046...c8c27`. The source-window contract, pair payload, analyzer, and
verifier recompute and bind both partitions.

The analyzer is truth-green and economically failed. It emits no executable-R
percentage against non-additive source signal, keeps candidate/event/instance/
axis units separate, and reconciles the exact paired behavior at 117 physical
fills / `-4.81212578R` and ten headline fills / `-1.56722011R`. Compile,
focused tests, direct verifier checks, and scoped diff validation are green.

Disposition: transfer semantics and pair/hash/unit proof are DONE. B7.5 remains
PARTIAL because economic generalization failed. The active dependency is the
selected-intent / entry-fill / terminal-R lifecycle separation, followed by a
targeted April overlap proof. Pressure-cap discrimination and exit selection
remain ordered after lifecycle truth. Broker/live/final remain false.

### B7.5 Selected-Intent / Entry-Fill / Terminal-R R5 Targeted Closure - 2026-07-16

The April 10 XAUUSD R5 targeted replay completed under shared digest
`cb862b32...3e3a` and source-plan digest `0030f723...bea0`. It preserves the
exact R2 candidate/scorecard/order/trade/missed identities (`248 / 92 / 6 / 3 /
245`) while replacing conflated terminal truth with three independent lifecycle
authorities. Three selected intents each emit one pending and one filled
terminal event; one fill is terminal-R-scoreable and two close as
terminal-R-unscoreable with null generic R/PnL. All fills consume accepted risk
without releasing it. The canonical lifecycle scan has no bad rows.

Physical behavior is one scoreable loss plus two unscoreable fills:
`-1.10438795R`, `-$690.24246875`, `$1717.40733284` accepted risk, and
full/reduced distribution `1/2`. Headline remains zero. Raw expected cost is
`0.24378323R`; summed row execution-cost authority is `0.24378324R`. Missed
diagnostic opportunity is 38 scoreable rows at `+4.95998734R` net, with 207
unscoreable rows. Executed REFUSED/source-gap remains `0/0`.

Compilation and `849 + 206 + 335 = 1390` affected tests pass; only the existing
unknown `asyncio_mode` warning remains. This closes the targeted correctness
proof, not B7.5 economics. Full-April regeneration under the same lifecycle code
is now required before any pressure-cap or exit challenger promotion.

### B7.5 Causal Stop-Hazard Risk Expression Pause Checkpoint - 2026-07-16

The full-April R5 lifecycle proof is complete and truth-green but economically
negative. The next same-root batch repairs pressure-only non-fragile stop caps,
normalizes final authority before summary accumulation, partitions scoreable
and terminal-unscoreable costs, and verifies serialized trade-ledger parity.

Implementation and focused proof are complete: Python compilation passes;
`16/16` focused tests pass; deterministic April R5 reconciliation reports
full/reduced `6/63`, scoreable/unscoreable expected cost
`3.77178321/0.96410350R`, and physical summary parity `bad_counts={}`. Direct
April stop-hazard cap authority scan also has `bad_counts={}`.

The bound May 15 hostile target completed with `8174` candidates, `96`
scorecards, six terminal fills, five scoreable trades, W/L/F `3/2/0`,
gross/final `+1.16268960R`, net `+0.76586373R`, cash `+$782.81183897`, and
full/reduced risk rows `4/2`. Executed REFUSED/source-gap rows remain `0/0`;
physical summary and stop-hazard cap scans are green. Relative to V249 on the
same day, headline delta is `+1.08625814R` and `+$1742.26142198` with two added,
three removed, and four shared identities. One added scoreable trade loses
`-1.09345695R`, so the result is not explained by blocking every new transfer.

Disposition: B7.5 remains PARTIAL and the goal session is paused. The June 4
same-contract non-hostile comparator, paired acceptance decision, and
route-wide current-batch certification are UNTESTED. No process is active.
Resume by running only the already-bound June 4 target; do not rerun May, start
a new repair batch, or launch a broad replay first. Broker/live/final remain
false.

### B7.5 Full-Portfolio Ordered-Tick Reconciliation Closure - 2026-07-16

This section supersedes the pause checkpoint as current execution state while
preserving it as historical lineage. June and May R2 negative controls are
behavior-identical to their R1 runs under shared digest `199fa37c...00`. The
final paired proof accepts evidence and structure but classifies economics
`MIXED_UNRESOLVED`; suppressed-pressure materialization is repaired without
changing observed behavior.

The XAU terminal discriminator and 24-symbol successor completed. The full
result has `6981 / 96 / 12 / 6 / 6975` candidate, scorecard, order-event,
trade, and missed rows. Candidate/trade/missed identities are unchanged versus
June R2, with one scoreability enrichment and zero regression. Physical
behavior is five scoreable plus one unscoreable fill, `4/1/0`,
`+4.03591467R`, `+$2204.18020365`, and `3.0%` risk. Four fills use ordered-tick
terminal paths and two use ordered-M1 paths. Physical-summary, cap, transfer,
REFUSED, and source-gap gates are green.

The old `07:45` XAU diagnostic winner is not suppressed by the repaired cap.
The earlier `07:30` fill earns `+1.07241840R` under ticks; the later candidate
is refused on tick-real spread and total cost before lifecycle authority is
evaluated. No allocation-correctness repair is supported.

Versus V258 the same-day result is lower by `0.96118957R` at equal-risk
interpretation but higher by `+$2248.50555688` cash under `+1.975` percentage
points more risk. That is mixed evidence, not a policy win. B7.5 economic
generalization, final selection, B8 canary, broker mutation, and live authority
remain closed. The next route is a predeclared multi-window equal-risk
selection versus dynamic-risk cash-expression experiment after canonical
certification and commit; this completed prefix must not be rerun.

### B7.5 Proof-Consumer R2 Sealed Regeneration - 2026-07-16

Canonical certification exposed three behavior-neutral contracts after the
full R1 reconciliation: 89 zero-trade scorecards omitted an otherwise exact
canonical pre-risk provenance map; nonterminal pending intents and
terminal-R-unscoreable trades needed lifecycle-aware verifier semantics; and
the supported UKOIL selected policy needed an explicit diagnostic-only
terminal-unscoreable envelope. The repairs are fail-closed and the complete
three-file barrier passes `1365` tests.

The only authorized replay is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R2`,
bound to shared digest `77066a99...99bb1` and the unchanged full 24-symbol
source plan `a24fc919...f001`. It must reproduce the R1 identities, economics,
risk, scoreability, and cost exactly. Only the 89 canonical provenance maps and
one null-R/no-authority UKOIL diagnostic envelope may change. Any behavioral
delta reopens the root cause. Policy, broker, live, and final authority remain
closed.

### B7.5 Proof-Consumer R2 Rejected, R3 Sealed - 2026-07-16

R2 reproduced R1 exactly across trades, identities, R, cash, risk, cost, and
scoreability, and serialized the UKOIL diagnostic envelope correctly. It is
not final proof because the 89 missing provenance maps remained null. The
donor maps materialize only at final package-authority annotation, after the
first quality-normalization hook.

The same fail-closed join now runs at that final boundary. A late-donor test
and all-96-row projection are green; the harness suite passes `195` tests. The
only authorized successor is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3`,
bound to digest `163329e9...9b67` and unchanged source plan
`a24fc919...f001`. It must preserve exact R1/R2 behavior and serialize all 96
canonical maps. R2 remains failed serialization evidence; policy, broker,
live, and final authority remain closed.

### B7.5 R3 Canonical Route Certification - 2026-07-16

R3 is route-certified. The final manifest selects R3, keeps V254T as the broad
holdout gate, and binds `231` files. The canonical verifier is `ok=true` with
`issue_count=0`; compilation and `1918` affected tests pass. Prompt hardening,
both parent verifiers, and full route/parent artifact audits are green.

Certification is behavior-neutral. The bounded June result remains
`+4.03591467R`, `+$2204.18020365`, and `3.0%` risk with exact R1/R2 identities,
while the cross-window result remains economically failed/mixed. No policy,
broker, live, or final authority is promoted. The batch is committed; next
bind the multi-window equal-risk versus dynamic-risk cash-expression successor.

The scoped implementation/proof packet is committed as `beec3ce52`. The next
active route is the separately sealed multi-window equal-risk versus
dynamic-risk cash-expression comparison; no policy change precedes it.
