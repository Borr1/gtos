# Fable Execution Matrix - 2026-07-09

Generated UTC: 2026-07-09T03:09:42Z.

Purpose: current B0-B8 execution control surface after commit
`e12cb4028 repair B7 default confidence provenance`. This supersedes stale
active pointers that still referenced V205/V204. It does not replace the
detailed 2026-07-08 matrix; it updates the dependency ladder from current disk
evidence before the next replay.

## Sources Read

- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_IMPLEMENTATION_SEQUENCE_20260705.md`
- `.context/context_os/fable_ultimate_plan/FABLE_ULTIMATE_SYSTEM_ROOT_CAUSE_AUDIT_20260705.md`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260708.md`
- `.context/context_os/ULTIMATE_SYSTEM_CONTINUATION_DIRECTIVE.md`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/DENOMINATOR_TO_DEPLOYMENT_EXECUTION_SUMMARY.json`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/OUTPUT_MANIFEST.json`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/VERIFICATION_RESULT.json`
- V208/V205/V198/V97/V92/V90/V89D hostile summaries and V104/V128/V150 non-hostile summaries.

## Current Disk And Process State

- HEAD: `e12cb4028 repair B7 default confidence provenance`.
- VPS freshness floor: `FETCH_HEAD=redacted_host87668c5d503b52925d10be7dfb66540`; required floor `b112d22c351b13e2af045bb8feb82f1e235246f4` is ancestor-ok.
- No replay, route builder, verifier, parity builder, or pytest process is running. Active Python processes are Context OS MCP stdio servers only.
- Route verifier: `ok=true`, `issue_count=0`, `final_package_selected=false`, `live_trading_enabled=false`.
- Current route manifest broad-quality prefix: `BROAD_LIVE_AS_IF_REPLAY_V208_B7_DEFAULT_CONFIDENCE_SCORECARD_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`.
- Stale pointer repair required before replay: `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json` and `.context/context_os/CONTINUATION_CURSOR.json` still pointed at V205/V204 before this matrix.
- Dirty worktree outside this checkpoint includes Context OS code/docs, `scripts/generate_live_state.py`, `src/components/broader_origin_generators.py`, unrelated deleted old science-program JSONL ledgers, and other pre-existing Context OS dirt. Do not stage unrelated dirty files with this B7 checkpoint.

## Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V208_B7_DEFAULT_CONFIDENCE_SCORECARD_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

Scope: one-day bounded proof slice, 2026-05-13, full 24-symbol configured surface, repaired profile only.

Numbers:

- candidates / decisions / scorecards / order-ledger rows / filled trades: `8864 / 2304 / 96 / 9 / 2`
- summary order rows: `6`
- missed rows / bucket rows: `8858 / 412`
- W/L/F: `2/0/0`
- net/gross/final R: `+0.52110312 / +0.65111456 / +0.65111456`
- cash PnL: `+130.31196876`
- risk cash / risk pct: `500.10039132 / 0.5`
- expected cost R: `0.13001144`
- missed diagnostic opportunity net R: `-1350.99364762`
- missed executable scoreable net R: `0.0`
- executed broker-cost REFUSED/source-gap rows: `0/0`
- source-bound parity rows / leakage bucket rows: `8130 / 1101`
- flow diagnostic bucket rows: `601`
- default-confidence hidden gaps after repair: candidate `0`, scorecard `0`, order `0`, trade `0`

Interpretation: V208 is a behavior-neutral B1/B5 proof-surface repair versus V207. It proves default-confidence provenance and route summary-count truth in a one-day slice. It does not prove B7.2 hostile five-day value transfer, broad reservoir transfer, final package selection, or live readiness.

## Baseline Comparison Anchors

### Hostile 2026-05-13..2026-05-17

| Prefix | Candidates | Scorecards | Order Events | Trades | Net R | Gross/Final R | Cash PnL | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 25006 | 288 | 243 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | predecision stop-hazard attribution baseline |
| V90 | 25006 | 288 | 233 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | transfer-rank lifecycle authority baseline |
| V92 | 25006 | 288 | 239 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | Fable hostile comparator |
| V97 | 25006 | 288 | 196 | 47 | +13.89627731 | +18.23890670 | +4461.09800786 | dynamic-scope comparator |
| V198 | 25006 | 288 | 178 | 75 summary rows / 74 filled | -3.84033809 | +1.79005938 | -3530.29276461 | tick-hydrated current-runtime transfer; failed value transfer |
| V205 | 25006 | 288 | 172 | 73 summary rows / 72 filled | -5.20239659 | +0.16828289 | -3907.50669036 | hostile value-transfer proof before V206-V208 repairs |

V205 same-window denominator evidence: source-bound R available `425161.75241648R`, package axes `1101`, candidate-generated axes `894`, scorecard/order axes `43`, filled axes `37`.

### Non-Hostile 2026-06-01..2026-06-05

| Prefix | Candidates | Scorecards | Order Events | Trades | Net R | Gross/Final R | Cash PnL | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V104 | 35191 | 480 | 111 | 46 | +14.73101491 | +18.36174510 | +2850.02330565 | passive-distance hard-block comparator |
| V128 | 35191 | 480 | 212 | 55 | +1.12099062 | +6.22739670 | +3007.28429755 | router-refusal derived immediate authority comparator |
| V150 | 6633 | 480 | 13 | 3 | +0.84449709 | +1.09529478 | +211.19447407 | targeted broad-quality parity prefix |

## Subagent Finding Disposition

- Dalton: INCORPORATED. Cost-refused rows remain honest non-executable unless dated B6 calibration evidence changes the packet; do not loosen REFUSED.
- Fermat: INCORPORATED. Full-risk sizing was not lost where the risk decision is `trade`; the earlier leak was public action/risk namespace projection.
- Kant: INCORPORATED. Current stop-loss losers were ordered-tick selected-policy stop outcomes, not profit-harvest damage.
- Meitner: INCORPORATED. V198/V205 failure is concentrated in risk/order/fillability and full-tier stop-loss exposure, not in broker/source authority leaks.
- Pascal: INCORPORATED. Removed V92/V97 winners remain visible as candidate/missed rows; dominant removed-winner blockers include honest broker-cost REFUSED and cost-passed scheduler/risk transfer classes.
- Kuhn: INCORPORATED THROUGH V199/V201/V206. Stop/exit pressure became a stop-pressure/risk-transfer repair lane; V208 closed the resulting default-confidence proof gap.
- No new subagent finding is pending for this checkpoint. New subagents should be assigned only after V209 artifacts exist, so they can inspect current five-day evidence instead of stale one-day or V205 artifacts.

## B0-B8 Batch Status

| Batch | Status | Evidence | Remaining Gap / Next Step |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `audit_provenance_and_flags_v114.py`, `AUDIT_PROVENANCE_AND_FLAGS_V114.json`, `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`; V208 parity/flow preserve the baseline proof surface. | Preserve as baseline; no new instrumentation before V209. |
| B1 provenance truth contract | DONE | Raw/effective/original selector and risk provenance from V114/V121; V204 missed selector-origin verifier green; V208 default-confidence provenance hidden gaps are `0/0/0/0`. | Preserve through V209 five-day run. |
| B2 fillability and reallocation truth chain | DONE/CONDITIONAL | Unresolved-first fill-floor, fallback explicit-reason, fail-closed REFUSED/source-gap/non-executable authority; V208 cost/source execution leaks `0/0`. | Monitor V209 fillability/reallocation buckets; no threshold retune before evidence. |
| B3 risk-expression ladder and loss-bucket demotion | DONE/CONDITIONAL | Signed full/reduced/diagnostic ladder surfaces and diagnostic bucket treatment exist; V208 kept risk provenance with no live/final authority. | V209 must report full-risk/reduced-risk distribution and whether value change comes from selection/risk expression or suppression. |
| B4 fill-simulation realism | DONE/CONDITIONAL | Tick-hydrated V197 and later proof surfaces; no skipped-tick behavior truth accepted; V208 did not bypass realism. | V209 must keep fill-realism split and classify proxy/diagnostic fills. |
| B5 verifier and comparison precision | DONE | V208 route verifier `ok=true`, `issue_count=0`; route builder summary count contract repaired. | Extend only if V209 exposes a new proof-surface field. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | Broker-calibrated cost authority remains enforced; V208 cost-authority bad counts are empty. | Reopen only for dated stale-floor/mapping evidence; REFUSED remains non-executable. |
| B7 full proof ladder | PARTIAL/ACTIVE | V208 one-day proof-surface slice is clean and behavior-neutral. V205/V198 hostile five-day value-transfer failed under earlier code. | Next dependency step is V209 B7.2 hostile five-day value-transfer proof under V208 code, then B7.3 non-hostile five-day if V209 artifacts are clean. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`; hard-halt boundary remains. | Blocked until B7.1-B7.5 pass, production-return dossier assembled, live-shadow passes, and owner canary action occurs. |

## Requirement-Level Matrix

### B0 Truth Instrumentation Baseline

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Baseline provenance collapse, stale full-risk, expiry/fallback, R identity, raw-failure poisoning, and reallocation starvation counts | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json`; V114 pre-replay/root-cause files. | Preserve as before/after reference. |
| Broker-cost refusal histogram by symbol/session/sub-reason/spread-floor source | DONE | `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`; B6 calibration artifacts. | None for V209. |

### B1 Provenance Truth Contract

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Raw selector action/reason preserved separately from effective/materialized action | DONE | `src/components/selector_v4.py`; `src/research_infra/v4_timewarp_simulated_live_research_loop.py`; V204 verifier green. | V209 must keep provenance collapse at zero. |
| Propagate original action into scheduler rows, risk authority, order/trade/missed rows | DONE | V204 missed-row selector-origin projection closure. | Monitor V209 missed rows. |
| Gross/net/final R identity naming | DONE | V208 split profile reports net/gross/final separately. | Monitor V209 R identity checks. |
| Default-confidence provenance is visible, not hidden | DONE | V208 candidate/scorecard/order/trade hidden gaps `0/0/0/0`; focused tests passed before commit. | Preserve in V209. |

### B2 Fillability And Reallocation Truth Chain

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Unresolved fill-floor failures are executable authority, raw failures remain diagnostic | DONE | Prior B2 code/tests; V208 no unresolved fill-floor execution leak. | V209 bucket audit. |
| Reallocation can choose next valid candidate after top veto | DONE/CONDITIONAL | V161/V196/V201 lineage; V208 no verifier issue. | V209 must report reallocation and missed-positive/negative R. |
| Fallback/expiry emits explicit reasons and does not silently starve orders | DONE/CONDITIONAL | V121L/V204 lineage; V208 flow diagnostic exists. | V209 expired/unfilled reasons must be explicit. |
| REFUSED/source-gap/unfillable rows are non-executable but scoreable/missed | DONE | V208 executed REFUSED/source-gap `0/0`. | Preserve. |

### B3 Risk-Expression Ladder

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Full/reduced/diagnostic tiers are explicit and verifier-scanned | DONE/CONDITIONAL | B3/V121-V123 lineage; V208 verifier green. | V209 must split full-risk vs reduced-risk PnL. |
| EV-band/open-reduced promotion requires signed authority | DONE/CONDITIONAL | Selector/risk lineage and current verifier. | Reopen only if V209 shows ambient open-reduced leakage. |
| Hardcoded loss buckets are diagnostic, not proof of suppression | DONE/CONDITIONAL | `config/agent_config.yaml` replay profile lineage. | V209 must not pass via date/symbol/session suppression. |

### B4 Fill Realism

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Immediate marketable fill source-time/as-of truth is enforced | DONE/CONDITIONAL | V122/V197 lineage; V208 did not bypass. | V209 must be tick-hydrated when tick source exists. |
| Passive-limit queue realism and diagnostic first-touch/proxy classification | DONE/CONDITIONAL | V122I/V122J/V197 lineage. | V209 report fill-realism class split. |
| Same-bar ambiguity closed conservatively with provenance | DONE/CONDITIONAL | B4 lineage. | Monitor V209. |

### B5 Verifier And Comparison Precision

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Off-configured fallback predicate precision and raw/effective leak detection | DONE | Verifier green through V208. | Preserve. |
| Cost scan scoped to executable rows and diagnostic rows cannot carry executable PnL | DONE | V208 cost-authority bad counts empty. | Preserve. |
| Proof prefix cannot be capped/narrowed without bounded-smoke label | DONE/CONDITIONAL | Verifier/harness lineage; V208 full 24-symbol one-day. | V209 must use full 24-symbol surface and no top-N cap. |
| Comparison outputs include transfer, risk, fill-realism, added/removed fields | DONE/CONDITIONAL | Existing comparison artifacts for V205 vs V92/V97/V198/V201. | Generate same set for V209. |

### B6 Broker-Cost Calibration Audit

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Refusal histogram joined to measured tick-spread floors | DONE WITH LABEL | V123 B6 calibration audits. | Reopen only for new dated calibration evidence. |
| REFUSED packets cannot execute | DONE | V208 executed REFUSED/source-gap `0/0`, verifier green. | Preserve in V209. |

### B7 Full Proof Ladder

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| 7.1 one-day structural proof-surface integrity | PARTIAL/DONE FOR CURRENT SLICE | V208 one-day 2026-05-13: 2 trades, +0.52110312R, verifier green, no cost/source execution leak. | V208 is not full 7.1 market truth; it is sufficient to stop the one-day proof-surface loop and move to 7.2. |
| 7.2 hostile 2026-05-13..17 value-transfer proof | OPEN/SELECTED | V205/V198 hostile five-day failed under earlier code; V208 code has not run five-day. | Run V209 hostile five-day fullgrid under V208 code. |
| 7.3 non-hostile 2026-06-01..05 proof | OPEN | V104/V128/V150 comparators exist. | Run after V209 artifacts are parsed and no hard truth leak appears. |
| 7.4 broad 2026-06-01..19 proof | OPEN | V110B/V111 comparators exist. | Blocked until 7.2 and 7.3 are understood. |
| 7.5 extended history proof | OPEN | No post-V208 extended proof. | Blocked until 7.1-7.4. |

### B8 Live Path

| Requirement | Status | Evidence | Gap / Next |
| --- | --- | --- | --- |
| Production-return dossier | OPEN | B8 plan only. | Blocked by B7. |
| Live-shadow with SimulatedBroker for at least 5 trading days | OPEN | No B8 shadow proof. | Blocked by B7. |
| Canary micro-live and broker-statement reconciliation | OPEN | Live/broker/final false. | Owner action only after B7+B8 gates. |

## Selected Next Same-Root Batch - V209

Batch: `B7_2_hostile_five_day_value_transfer_after_v208`.

Reason: V208 closed the current one-day proof-surface/verifier blocker. The next dependency-ordered Fable step is B7.2 hostile five-day value-transfer proof under the now-clean V208 code path. No new selector/scheduler/risk/order policy patch is selected before this run; the needed action is broader proof, not another one-day tuning loop.

Affected components:

- `run_broad_live_as_if_replay_harness.py` with full 24-symbol configured surface.
- `analyze_broad_live_as_if_replay_flow.py` for flow buckets/dossier after replay.
- `build_source_bound_execution_parity.py` for source-bound to executed parity and leakage buckets after replay.
- `build_denominator_to_deployment_execution.py` and `verify_denominator_to_deployment_execution.py` after artifacts exist.
- `compare_broad_replay_prefixes.py` or the route comparison tool for V209 vs V92/V97/V198/V205.

Patch type before replay: diagnostic/control repair only. Behavior-changing evidence comes from replaying current code over the five-day hostile window.

Expected measurable effect before replay:

- Candidate -> scorecard transfer: expected same full 24-symbol candidate universe class as hostile V205/V198 (`25006 -> 288`) unless V208 code exposes a new source/proof issue.
- Scorecard -> order transfer: expected to shift versus V205 if V206-V208 stop-pressure/default-confidence repairs transfer beyond the one-day slice.
- Order -> fill transfer: expected to preserve broker-cost/source-gap execution at `0/0`; trade count may drop if stop-pressure rows are honestly demoted.
- Missed positive/negative R: must be reported; positive by suppressing opportunity is rejected.
- Trade count/net/gross/final R/W/L/F: no target positivity claim; success is cleaner value transfer and exact attribution versus V92/V97/V198/V205.
- Full-risk vs reduced-risk distribution: must show whether V206 risk-expression changes reduced negative full-risk stop-pressure exposure.
- Cost/source execution: must remain `0/0`.

Replay helped if V209 has no verifier/truth leaks, no capped/narrowed authority, no executed REFUSED/source-gap rows, and improves or exactly explains transfer versus V205/V198 with added/removed trades and missed-positive/negative R. Replay failed if it is negative with unexplained removed winners, if trade count collapses without scoreable missed attribution, or if any proof-surface/verifier issue reopens.

Broker/live/final remain closed.

## V217 Update - B7 Signed-Transfer Selected-Policy Precondition

Timestamp: `2026-07-09T16:06:26Z`

Latest bounded proof:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V217_B7_SIGNED_TRANSFER_SELECTED_POLICY_PRECONDITION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
- Scope: `2026-05-13..2026-05-14`, symbols `XAUUSD, USDCAD, USDJPY`, repaired profile only.
- Behavior: `1651` candidate rows, `192` scorecard rows, `8` order rows, `3` filled trades, W/L/F `3/0/0`, net/gross/final R `+1.10761535 / +1.35101129 / +1.35101129`, cash PnL `+277.0648589`, risk cash `750.86709783`, expected cost R `0.24339594`.
- V217 vs V216: trade count delta `0`, net R delta `0.0`; same candidate/order/fill behavior under the bounded slice.
- Truth effect: V216 had signed-transfer allowed markers on bad scorecard/missed rows; V217 has `0` scorecard/missed signed-transfer allowed rows and preserves blocked diagnostics: scorecard selected-policy gate blocked rows `36`, missed selected-policy gate blocked rows `50`.
- Source-bound parity artifacts: `2942` parity rows and `1101` leakage bucket rows.
- Route builder: `OUTPUT_MANIFEST.json` is V217-bound under `broad_quality_parity_prefix`; broad holdout gate remains V211.
- Route verifier: `ok=true`, `issue_count=0`, verified `2026-07-09T16:06:26Z`; `broad_live_as_if_order_executable_transfer_contract_scan.bad_counts={}`.
- Broker/live/final: `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B1 provenance truth contract | DONE for current focused route proof | V217 route verifier `ok=true`; no confidence/source proof regression reported. | Keep enforced in broader B7 runs. |
| B5 verifier/comparison precision | DONE for latest V217 quality-parity binding | V217 builder bound the latest quality prefix; verifier issue count `0`; order-executable transfer bad counts `{}`. | Keep verifier as gate after each material batch. |
| B7 signed-transfer selected-policy precondition | DONE for bounded targeted proof | V217 closes the V216 contract failure without changing the filled trade set. | Broaden proof before any reservoir-transfer claim. |
| B7 broad value transfer | PARTIAL | V217 is a two-day, three-symbol proof slice; V211 remains the current hostile five-day holdout gate prefix. | Choose next broader objective B7 proof from current evidence, normalized to same-window source-bound R. |
| B3 risk-expression ladder | PARTIAL | V217 filled trades remain all `open-reduced-risk`. | Include full-risk/reduced-risk distribution in the next broader B7 proof; do not promote blindly. |
| B8 live path | OPEN | Live/final remain false. | Blocked until B7/B8 gates pass. |

Next dependency-safe action:

Run route audits and `git diff --check`; if clean, select the next B7 broader proof from Fable dependency order. Do not do another local tuning replay unless the audits expose a truth/verifier failure.

Prompt hardening / control clauses:

- Required active context: future prompts using this matrix must read `goal_session_research_discipline.md` and `research_operating_doctrine.md`; those active instructions are not background and must be operationalized through instruction-coverage and completion audit.
- Do not rely on chat memory. Use current disk artifacts, manifests, verifier outputs, ledgers, source completeness, branch decision, and implementation decision evidence.
- Full same-evidence-class pursuit applies: literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been exhausted or exactly blocked.
- Builder posture: no conservative brake; use constructive active creativity while keeping broker/live/final claims closed until proof passes.
- Result materialization standard: every behavior-changing patch must report exact-R or proxy-R, source-capture/source completeness, branch decision, implementation decision, focused test or verifier result, and artifact outputs.
- Forbidden surfaces: no production-change claim, live trading, broker operation, paid API/vendor action, broker account/order/history/deal/position mutation, prompt/config/risk/execution/safety/canary/selector change, or final/live claim without the explicit proof gate.
- No arbitrary top-N: preserve full ledger scope, all material rows, and full 82-sleeve authority; no top 3/5/10 or number-limited cutoff proof.

## Addendum - 2026-07-09T13:39:39Z V213 Parsed, V214 Targeted Batch Selected

V213 completed as a targeted B7 signed soft-transfer finalizer consumer proof,
but it is behavior-identical to V212 and does not close the B7 transfer leak.

Completed V213 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V213_B7_SIGNED_SOFT_TRANSFER_FINALIZER_CONSUMER_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

V213 scope and behavior:

- scope: `2026-05-13..2026-05-14`, `XAUUSD`, `USDCAD`, `USDJPY`,
  repaired profile only;
- source / candidate / decision / scorecard / order-event / trade / missed /
  bucket rows: `29 / 1651 / 4608 / 192 / 8 / 3 / 1647 / 92`;
- W/L/F: `3 / 0 / 0`;
- net/gross/final R: `+1.10761535 / +1.35101129 / +1.35101129`;
- cash PnL: `+277.0648589`;
- risk cash / risk pct sum: `750.86709783 / 0.75`;
- expected cost R: `0.24339594`;
- broker/live/final: `false / false / false`;
- executed broker-cost REFUSED/source-gap rows: `0 / 0`;
- target exact transfer remains `2/3` candidate, `2/3` scorecard,
  `2/3` missed, `0/3` order/trade.

V213 root evidence:

- Einstein status audit: B0/B1/B4/B6 remain preserved; B2/B3/B7 remain
  active; V213 must not trigger broad replay before focused repair proof.
- Schrodinger V213 parser: V212 and V213 selected counters are identical;
  `45` scorecard executable-probe rows remain `final_blocked`, `27` missed
  rows are already `package_candidate_and_signed_new_entry_authority_executable`,
  and only `4` risk-admitted orders materialized.
- Franklin authority audit: `origin_preserved_after_scheduler_risk_cap` is not
  router-refusal authority and must not be promoted into that family. The
  valid route for this repair is signed order-executable / explicit
  package-executable replay materialization.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | V114/V111 baselines remain reference surfaces; V213 did not alter B0. | Preserve. |
| B1 provenance truth contract | DONE | V210/V211 proof green; V213 signed authority fields are visible on candidate/missed rows. | Preserve and rerun verifier after V214 artifacts. |
| B2 fillability and reallocation truth chain | PARTIAL/ACTIVE | V213 keeps REFUSED/source-gap execution `0/0`, but signed/order-executable rows still final-block before order/trade. | Patch signed order-executable soft-transfer consumer; do not loosen REFUSED. |
| B3 risk-expression ladder | PARTIAL/ACTIVE | V213 accepted orders remain open-reduced-risk and selected-composition transfer is still reduced-risk dominated. | Preserve reduced/full provenance and repair causal transfer before sizing claims. |
| B4 fill-simulation realism | DONE/CONDITIONAL | V213 uses ordered-tick/fillability realism and no broker/live authority. | Preserve. |
| B5 verifier and comparison precision | PARTIAL FOR LATEST ARTIFACTS | V211 verifier is green, but V213 is newer than the latest accepted manifest/verifier. | Run route builder/verifier after V214 proof artifacts exist. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | V213 cost authority remains broker-calibrated; REFUSED/source-gap rows do not execute. | Preserve. |
| B7 full proof ladder | PARTIAL/ACTIVE | V211 failed hostile five-day value transfer; V212/V213 targeted slices are local-positive but target transfer remains `0/3` order/trade. | Run V214 targeted signed order-executable soft-transfer proof before any broad replay. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Blocked until B7 ladder and B8 production-return/shadow/canary gates pass. |

Selected next same-root batch:
`V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY`.

Files changed for V214:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T133939Z_V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY.md`
- this matrix.

Patch type:

- correctness repair: signed order-executable authority may rederive a stale
  broad package-executable false alias only inside the finalizer's causal
  signed soft-transfer path;
- performance repair: allows valid signed, cost-passed, source-complete,
  order-executable reduced-risk rows to compete instead of staying
  final-blocked by stale broad alias truth;
- diagnostic/proof repair: trace fields distinguish signed order-executable
  candidacy from rederived package-executable authority.

Focused verification:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
  passed;
- signed soft-transfer focused pytest: `4 passed`;
- focused finalizer pytest set: `5 passed`.

Expected measurable effect before V214:

- candidate -> scorecard transfer: near V213, not suppressed;
- scorecard -> order transfer: target signed order-executable rows should
  advance or expose a more precise downstream blocker;
- order -> fill transfer: ordered-tick/fillability realism preserved;
- missed positive/negative R: rows still missed must carry exact downstream
  cause, not stale broad package-executable alias only;
- trade count/net R: may increase; positivity is not required for this bounded
  proof;
- W/L/F and full-risk/reduced-risk distribution must be reported;
- executed cost-refused/source-gap rows must remain `0 / 0`.

V214 helped if the V213 target rows improve from `0/3` order/trade or the
remaining blocker moves to a precise downstream order/fill/lifecycle/exit
cause with broker/live/final still false. V214 failed if the same target rows
remain final-blocked only by `not_reallocation_candidate` / stale broad
package-executable alias causes, or if rederived authority reaches REFUSED,
source-gap, unfillable, or outcome-field rows.

Broker/live/final remain closed.

## Addendum - 2026-07-09T14:19:08Z V214 Parsed, V215 Targeted Batch Selected

V214 completed as the targeted signed order-executable rederived-authority
proof. It confirmed the stale broad package-executable alias was a real
transfer blocker, but the implementation was too permissive and admitted a
negative signed-transfer cohort.

Completed V214 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

V214 scope and behavior:

- scope: `2026-05-13..2026-05-14`, `XAUUSD`, `USDCAD`, `USDJPY`,
  repaired profile only;
- source / candidate / scorecard / order / trade / missed / bucket rows:
  `29 / 1651 / 192 / 28 / 13 / 1637 / 95`;
- W/L/F: `8 / 5 / 0`;
- net/gross/final R: `-1.76172422 / -0.52207133 / -0.52207133`;
- cash PnL: `-128.7023959`;
- expected cost R: `1.23965289`;
- broker/live/final: `false / false / false`;
- executed broker-cost REFUSED/source-gap rows: `0 / 0`;
- V214 minus V213: trade count `+10`, net R `-2.86933957`,
  gross/final R `-1.87308262`, cash PnL `-405.7672548`;
- added V214 cohort: `11` trades, `-2.08087572R`;
- removed V213 cohort: `1` trade, `+0.78846385R`;
- target XAUUSD advanced to order/trade and `+0.02R`; target USDCAD remained
  candidate/missed only.

V214 root evidence:

- Singer: incorporated. The V214 loss is admission/selection quality, not exit
  damage; added losers had weak MFE and common finite negative reallocation
  quality scores.
- Helmholtz: incorporated. `signed_order_executable_route_candidate=true` is
  necessary but not sufficient; original scheduler passthrough must remain
  valid separately, while non-original micro-rescue needs signed displacement
  allowance or another explicit contract.
- Anscombe: incorporated/deferred. V214 keeps final/live/cost-source boundaries
  closed, but latest verifier binding remains partial until a latest accepted
  behavior artifact is wired through the route verifier.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | V114/V111 baselines remain reference surfaces; V214 did not alter B0. | Preserve. |
| B1 provenance truth contract | DONE | V210/V211 proof green; V214 propagated signed authority fields through order/trade/missed surfaces. | Preserve. |
| B2 fillability and reallocation truth chain | PARTIAL/ACTIVE | V214 kept REFUSED/source-gap execution `0/0`, but signed transfer bypassed finite negative selected-policy reallocation quality. | Patch quality-gate consumer before replay. |
| B3 risk-expression ladder | PARTIAL/ACTIVE | V214 filled trades remain entirely `open-reduced-risk`; risk expression must stay visible and cannot be treated as cosmetic. | Preserve provenance and re-evaluate after V215. |
| B4 fill-simulation realism | DONE/CONDITIONAL | V214 uses ordered-tick/fillability realism and no guarded-market fallback execution. | Preserve. |
| B5 verifier and comparison precision | PARTIAL FOR LATEST ARTIFACTS | Existing verifier is green for older route prefixes; V214 behavior report is not yet verifier-bound. | Bind latest accepted V215/V214 behavior after targeted proof. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | V214 cost authority remains broker-calibrated; REFUSED/source-gap rows do not execute. | Preserve. |
| B7 full proof ladder | PARTIAL/ACTIVE | V214 opened transfer but admitted a negative cohort; this is a targeted B7 admission-quality leak. | Run V215 targeted selected-policy reallocation-quality guard proof before any broad replay. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Blocked until B7 ladder and B8 production-return/shadow/canary gates pass. |

Selected next same-root batch:
`V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD`.

Files changed for V215:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T141908Z_V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD.md`
- this matrix.

Patch type:

- correctness repair: selected-policy quality gate reads scheduler stop-hazard
  aliases and finite executable reallocation-quality scores;
- correctness/performance repair: signed soft-transfer can override stale or
  missing reallocation-quality fields, but not a finite quality score below
  floor;
- correctness repair: non-original signed package micro-rescue now requires
  signed soft-transfer displacement allowance; original scheduler passthrough
  remains separately valid;
- diagnostic/proof repair: signed displacement and micro-rescue block reasons
  are propagated for trade/order/missed proof.

Focused verification:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
  passed;
- signed/selected-policy focused pytest cluster: `7 passed, 606 deselected,
  1 warning`.

Expected measurable effect before V215:

- candidate -> scorecard transfer: near V214, not suppressed;
- scorecard -> order transfer: finite negative selected-policy quality
  signed-transfer rows should move to missed/diagnostic with explicit gate
  failure;
- order -> fill transfer: likely lower than V214 if the negative cohort is
  correctly blocked; original passthrough should remain;
- missed positive/negative R: must carry selected-policy reallocation-quality
  or micro-rescue block reasons;
- trade count/net R: likely closer to V213, but not accepted unless the cause
  is causal predecision quality rather than broad suppression;
- W/L/F and full-risk/reduced-risk distribution must be reported;
- executed cost-refused/source-gap rows must remain `0 / 0`.

V215 helped if finite negative selected-policy reallocation-quality rows stop
executing through signed soft-transfer, original scheduler passthrough still
executes when independently valid, and broker/live/final/cost-source boundaries
stay closed. V215 failed if negative-quality signed-transfer rows still execute,
if original passthrough is wrongly blocked, or if opportunity collapses without
explicit missed-opportunity attribution.

Broker/live/final remain closed.

## Addendum - 2026-07-09T15:00:00Z V215 Parsed, V216 Alias-Precedence Guard Selected

V215 completed and repaired the V214 negative signed-transfer cohort for the
targeted two-day slice, but a subagent audit found one remaining production
hole in the same root chain: explicit selected-policy reallocation quality
could be masked by older nonnegative scheduler/replacement aliases.

Completed V215 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

V215 scope and behavior:

- scope: `2026-05-13..2026-05-14`, `XAUUSD`, `USDCAD`, `USDJPY`,
  repaired profile only;
- source / candidate / scorecard / order / trade / missed / bucket rows:
  `29 / 1651 / 192 / 8 / 3 / 1647 / 92`;
- W/L/F: `3 / 0 / 0`;
- net/gross/final R: `+1.10761535 / +1.35101129 / +1.35101129`;
- cash PnL: `+277.0648589`;
- expected cost R: `0.24339594`;
- broker/live/final: `false / false / false`;
- executed broker-cost REFUSED/source-gap rows: `0 / 0`;
- V215 minus V214: trade count `-10`, net R `+2.86933957`,
  gross/final R `+1.87308262`, cash PnL `+405.7672548`;
- V215 removed `11` V214 trades totaling `-2.08087572R` and restored one
  V213 trade totaling `+0.78846385R`;
- V215 missed rows carry `29`
  `finite_selected_policy_reallocation_quality_score_below_floor` reasons.

Descartes disposition:

- INCORPORATED: production alias precedence fixed in
  `selected_policy_executable_quality_gate_fields`; explicit
  `selected_policy_executable_quality_reallocation_score` is authoritative
  before older scheduler/replacement aliases.
- INCORPORATED: added direct conflicting-alias test.
- INCORPORATED: repaired the non-original signed micro-rescue test so it reaches
  the finalizer risk/micro-rescue path and passes.
- DEFERRED TO B5 LATEST-BINDING: route verifier should add a fatal latest
  artifact scan for finite negative selected-policy reallocation quality under
  signed soft-transfer reliance.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | V114/V111 baselines remain reference surfaces. | Preserve. |
| B1 provenance truth contract | DONE | V210/V211 proof green; V215 keeps signed/quality fields visible. | Preserve. |
| B2 fillability and reallocation truth chain | PARTIAL/ACTIVE | V215 behavior repaired V214 negative cohort; alias-precedence code changed after V215. | Run V216 targeted proof before accepting latest behavior. |
| B3 risk-expression ladder | PARTIAL/ACTIVE | V215 filled trades remain `open-reduced-risk`; B3 remains open for broader proof. | Preserve split reporting. |
| B4 fill-simulation realism | DONE/CONDITIONAL | V215 uses ordered-tick/fillability realism. | Preserve. |
| B5 verifier and comparison precision | PARTIAL FOR LATEST ARTIFACTS | V215 behavior report exists, but verifier lacks finite-negative selected-policy signed reliance scan. | Patch/bind after V216 artifacts. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | V215 cost authority remains broker-calibrated; REFUSED/source-gap rows do not execute. | Preserve. |
| B7 full proof ladder | PARTIAL/ACTIVE | V215 passes targeted local behavior but production alias-precedence fix requires V216 neutral proof. | Run V216 targeted proof. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Blocked until B7 ladder and B8 gates pass. |

Selected next same-root batch:
`V216_B7_SELECTED_POLICY_QUALITY_ALIAS_PRECEDENCE_GUARD`.

Focused verification:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
  passed;
- signed/selected-policy/micro-rescue focused pytest cluster: `9 passed,
  605 deselected, 1 warning`.

Expected measurable effect before V216:

- candidate -> scorecard/order/fill transfer should be behavior-neutral versus
  V215 because artifact scan found no V214/V215 conflicting-alias rows;
- executed finite-negative selected-policy quality rows must remain `0`;
- alias-conflict executed rows must be `0`;
- cost-refused/source-gap execution remains `0 / 0`;
- broker/live/final remain false.

V216 helped if it is neutral or correctly demotes any newly exposed
conflicting-alias row with explicit selected-policy reallocation-quality
failure. V216 failed if any finite negative selected-policy quality row executes
through signed soft-transfer or if original passthrough is wrongly blocked.

Broker/live/final remain closed.

## Addendum - 2026-07-09T11:34:46Z V211 B7.2 Hostile Five-Day Proof Complete

V211 completed under the patched B1/B5 harness and is verifier-clean, but it
does not pass the B7.2 value-transfer objective.

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

V211 scope and behavior:

- scope: `2026-05-13..2026-05-17`, hostile five-day bucket, 24-symbol
  fullgrid, repaired profile only;
- candidates / decisions / scorecards / order-ledger rows / simulated order
  rows / filled trades: `25006 / 11424 / 288 / 50 / 27 / 18`;
- missed rows / bucket rows / flow buckets: `24979 / 555 / 880`;
- W/L/F: `11 / 7 / 0`;
- net/gross/final R: `-3.47466796 / -1.91290882 / -1.91290882`;
- cash PnL: `-868.32556257`;
- risk cash / risk pct sum / average risk pct: `4503.6890717 / 4.5 / 0.25`;
- expected cost R: `1.56175914`;
- expired/not-filled orders: `5`;
- missed diagnostic opportunity net R: `-4008.89784855`;
- missed executable scoreable net R: `0.0`;
- cost REFUSED/source-gap executed rows: `0/0`;
- guarded-market fallback applied count: `0`;
- order-level risk decisions: `open-reduced-risk=27`, full-risk executed
  trades `0`.

V211 proof status:

- flow analyzer succeeded: `880` flow bucket rows;
- source-bound parity succeeded: `18901` parity rows and `1101` leakage
  bucket rows;
- route builder succeeded with V211 quality/holdout prefixes in
  `OUTPUT_MANIFEST.json`;
- verifier succeeded after route-artifact materialization repair:
  `ok=true`, `issue_count=0`, `final_package_selected=false`,
  `live_trading_enabled=false`;
- materialization repair evidence: `verify_denominator_to_deployment_execution.py`
  now accepts a successful binary read probe for zero-local-block route
  artifacts; focused tests passed for the dataless placeholder and retry
  contract.

Same-window comparison summary:

| Comparator | Net R Delta | Trade Delta | Added Trades Net R | Removed Trades Net R | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| V209 | `0.0` | `0` | `0.0` | `0.0` | V211 is behavior-identical to V209; B1/B5 patch was proof-surface neutral on hostile five-day behavior. |
| V205 | `+1.72772863` | `-55` | `-3.06056973` | `-4.43715602` | Improvement is mostly removal of worse executable exposure, not restoration of the old positive cohort. |
| V198 | `+0.36567013` | `-57` | `-3.39267937` | `-3.40720716` | Same suppression/reallocation character. |
| V97 | `-17.37094527` | `-29` | `-3.49466796` | `+13.74825578` | V211 removed a positive V97 cohort and added negative reduced-risk ordered-tick trades. |
| V92 | `-32.83037032` | `-33` | `-3.17850255` | `+29.69389019` | Major value-transfer regression versus Fable hostile comparator. |
| V90 | `-32.31667953` | `-33` | `-3.17850255` | `+29.1801994` | Major value-transfer regression versus transfer-rank lifecycle authority baseline. |
| V89D | `-38.3198725` | `-38` | `-4.26313181` | `+34.14936711` | Major value-transfer regression versus predecision stop-hazard attribution baseline. |

V211 leakage summary:

- `candidate_generated_not_scheduler_selected`: `276` bucket rows,
  `3807` candidate trace rows, `354857.6686863841R` effective source-bound R;
- `candidate_generated_selector_reduce_risk_not_scheduler_selected`: `46`
  bucket rows, `6342` candidate trace rows, `51324.829237351R` effective
  source-bound R;
- `candidate_generated_broker_cost_refused_not_executable`: `198` bucket rows,
  `3909` trace rows, `401311.56713520584R` diagnostic source-bound R, net
  blocked counterfactual `-1364.05226673R`; this remains correctly
  non-executable, not the next loosening target;
- selected/executed V211 trades are concentrated in `GER40`, `JP225`,
  `NAS100`, `SPX500`, `UK100`, `US30_cash`, and `XAUUSD`, while removed
  V92/V97/V90/V89D winners are materially positive in `XAUUSD`, `USDJPY`,
  `USDCAD`, and `XAGUSD`.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | V211 parity/flow/verifier artifacts exist and are readable under the materialization contract. | Preserve. |
| B1 provenance truth contract | DONE | V211 verifier green after B1/B5 provenance patch; no hidden default-confidence blocker reopened. | Preserve through next repair. |
| B2 fillability and reallocation truth chain | PARTIAL/ACTIVE | Cost/source execution leaks remain `0/0`; fill realism is honest, but scorecard/order transfer collapsed and selected transfers are net negative. | Patch transfer/reallocation consumers rather than loosening broker-cost REFUSED. |
| B3 risk-expression ladder | PARTIAL/ACTIVE | V211 executed/order risk decisions are all `open-reduced-risk`; removed positive cohorts were also reduced-risk in comparators, so this is a composition/authority-expression issue, not just sizing cosmetics. | Repair signed risk-expression and scheduler admission/selection handoff together. |
| B4 fill-simulation realism | DONE/CONDITIONAL | V211 fill realism is ordered-tick based; no guarded-market fallback applied. | Preserve; do not restore optimistic unknown fills as proof. |
| B5 verifier and comparison precision | DONE | V211 route verifier `ok=true`, comparisons materialized, read-probe materializer tests passed. | Preserve. |
| B6 broker-cost calibration audit | DONE WITH LABEL / CONDITIONAL | REFUSED/source-gap rows remain non-executable and blocked counterfactual REFUSED bucket is net negative. | Do not loosen without new dated broker-cost evidence. |
| B7 full proof ladder | PARTIAL/FAILED B7.2 VALUE TRANSFER | V211 is verifier-clean but negative and behavior-identical to V209; it underperforms V89D/V90/V92/V97 due to removed positive cohorts and added negative reduced-risk ordered-tick transfers. | Next batch is B7 transfer/composition repair: source-bound/scorecard -> scheduler -> signed risk expression -> order/fillability selection. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Still blocked by B7. |

Selected next same-root batch:
`B7_TRANSFER_COMPOSITION_REPAIR_AFTER_V211`.

Patch type before replay:

- correctness/performance repair across transfer consumers;
- no broad replay until focused tests and the smallest targeted proof can show
  scorecard/order transfer, selected-composition, and risk-expression behavior
  changed for the V211 leakage slice.

Expected measurable effect before the next replay:

- candidate -> scorecard transfer should remain complete enough to preserve the
  full 82-sleeve authority surface;
- scorecard -> order transfer should increase for cost-passed, source-complete,
  fillable, signed candidates without admitting REFUSED/source-gap rows;
- order -> fill transfer should remain honest under ordered-tick/fillability
  rules;
- missed positive R should move from scheduler/risk transfer buckets into
  either executed trades or explicit non-executable reasons;
- missed negative R should stay blocked when the reason is causal and
  predecision;
- trade count should increase only through valid transfer, not by restoring
  optimistic unknown-fill rows;
- full-risk/reduced-risk distribution should show signed top-quality package
  candidates can escape ambient `open-reduced-risk` collapse when all full-risk
  conditions pass;
- cost-refused/source-gap execution must remain `0/0`.

The next replay helped if it restores positive scorecard/order transfer and
added transfers are net positive versus V211/V209 without sacrificing
broker-cost/fillability truth. It failed if positivity comes only from
suppression, if all valid candidates remain `open-reduced-risk`, or if removed
winner cohorts still cannot be traced to a causal non-executable reason.

## Addendum - 2026-07-09T12:06:20Z V212 Targeted B7 Transfer-Composition Proof Selected

The next replay is not a broad B7.2 rerun. It is the smallest targeted replay
proof for the current same-root B7 transfer-composition patch.

Pre-replay brief:
`.context/context_os/PRE_REPLAY_BRIEF_20260709T120620Z_V212_B7_TRANSFER_COMPOSITION_TARGETED_SOFT_TRANSFER.md`

Patch evidence before replay:

- scheduler soft-transfer admission now keeps signed, cost-passed,
  source-complete, order-executable package candidates selectable when the
  blocker is a soft selector/materialization reason such as
  `selector_open_reduced_risk_package_fill_floor_authority` or
  `same_decision_cluster_burst_guard`;
- reduced signed executable rows now carry/verifier-enforce risk pct
  basis/provenance and full-risk fill-floor proof fields;
- focused validation is green: `py_compile` passed, scheduler soft-transfer
  tests `5 passed`, verifier/runtime risk-expression tests `5 passed`.

Targeted replay prefix:
`BROAD_LIVE_AS_IF_REPLAY_V212_B7_TRANSFER_COMPOSITION_TARGETED_SOFT_TRANSFER_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Scope:

- dates: `2026-05-13..2026-05-14`;
- symbols: `XAUUSD`, `USDCAD`, `USDJPY`;
- profile: `repaired_package_conversion_v3`;
- purpose: prove local transfer behavior for the V211 missed soft-transfer
  target rows, not full-reservoir transfer or live readiness.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B2 fillability and reallocation truth chain | PARTIAL/PATCHED, TARGETED PROOF PENDING | Soft transfer predicates and reduced-risk proof propagation are patched and focused tests pass. | Run V212 targeted proof; inspect target row scorecard/order/trade transfer and downstream blockers. |
| B3 risk-expression ladder | PARTIAL/PATCHED, TARGETED PROOF PENDING | Reduced signed executable rows now require risk pct basis/provenance and full-risk fill-floor proof in verifier/focused tests. | V212 must preserve these fields in replay artifacts. |
| B7 full proof ladder | PARTIAL/ACTIVE | V211 failed value transfer; current patch addresses the selected transfer-composition leak, not broker-cost refusal. | Run V212 targeted proof before any broad rerun. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Still blocked by B7. |

V212 helped if at least one target soft-transfer class moves from
scheduler/missed space into scorecard/order transfer, or if the replay exposes
the next precise consumer blocker with risk/fill-floor proof fields present.
V212 failed if the same soft-transfer reasons remain terminal without a new
causal downstream blocker, if proof fields are missing, or if REFUSED/source-gap
rows execute.

## Addendum - 2026-07-09T03:46:28Z B1/B5 Reopened And Patched

Subagent Hegel found that the V208 green verifier was too permissive for default-confidence provenance:

- scorecard top-level rows could still carry `scheduler_default_missing_confidence_0_55` without the warning/flag contract being enforced;
- compact missed-opportunity rows could carry `confidence=0.55` while omitting the confidence source map and default flag;
- candidate/order/trade surfaces were already clean under the helper.

Status correction:

- B1 selected-package provenance: `DONE` becomes `PARTIAL -> PATCHED, FOCUSED TEST GREEN`.
- B5 verifier precision: `DONE` becomes `PARTIAL -> PATCHED, FOCUSED TEST GREEN`.
- B7.2 V209 hostile five-day replay: currently running/usable as exposure only because it was launched before this B1/B5 patch. It cannot be accepted as final B7 proof unless the completed artifacts pass the patched verifier contract, or the replay is rerun under the patched harness.

Patch evidence:

- `run_broad_live_as_if_replay_harness.py`: compact/default-confidence provenance projection now preserves `candidate_decision_quality_field_sources`, warning list, degraded-default flag, and nested quality envelope on missed/scorecard-compatible replay rows.
- `verify_denominator_to_deployment_execution.py`: scorecard top-level rows and missed rows now fail on hidden default confidence or confidence values with no confidence-source map.
- `tests/test_denominator_to_deployment_verifier.py`: added scorecard/missed verifier regressions.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: added compact missed-row projection regression.

Validation:

- `python3 -m py_compile` on touched harness/verifier/tests passed.
- `pytest -q tests/test_denominator_to_deployment_verifier.py::test_default_confidence_provenance_allows_visible_warning_flag tests/test_denominator_to_deployment_verifier.py::test_default_confidence_provenance_flags_hidden_nested_default tests/test_denominator_to_deployment_verifier.py::test_confidence_source_omission_flags_present_confidence_without_source tests/test_denominator_to_deployment_verifier.py::test_scorecard_scan_flags_top_level_default_confidence_without_warning tests/test_v4_timewarp_simulated_live_research_loop.py::test_compact_missed_rows_preserve_default_confidence_provenance` passed: `5 passed, 1 warning`.

Next dependency action:

1. Let the already-running V209 finish; do not duplicate it.
2. Parse V209 as a pre-patch exposure run.
3. Run patched verifier/analyzers against V209. If it fails only the repaired B1/B5 provenance contract, mark V209 as superseded and rerun the smallest required post-patch proof slice before accepting B7.2.

## Addendum - 2026-07-09T06:01:44Z V209 Parsed, Verifier Deterministic, B1/B5 Proof Still Open

V209 completed and is now classified as a pre-patch exposure run, not an
accepted B7.2 proof.

Completed V209 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V209_B7_2_HOSTILE_5D_VALUE_TRANSFER_AFTER_V208_20260513_20260517_FULLGRID`

V209 numbers:

- scope: 2026-05-13..2026-05-17, 24-symbol fullgrid, repaired profile only;
- source / candidate / decision / scorecard / order-event / trade / missed /
  bucket rows: `276 / 25006 / 11424 / 288 / 50 / 18 / 24979 / 555`;
- W/L/F: `11/7/0`;
- net/gross/final R: `-3.47466796 / -1.91290882 / -1.91290882`;
- cash PnL: `-868.32556257`;
- risk cash / risk pct: `4503.6890717 / 4.5`;
- cost R: `1.56175914`;
- full-risk / reduced-risk filled trades: `0 / 18`;
- executed broker-cost REFUSED/source-gap rows: `0 / 0`.

V209 same-window transfer:

- same-window source-bound/package R: `425333.0444635402R`;
- package axes: `1101`;
- candidate-generated axes: `894` (`81.19891%` of package axes);
- scorecard/order axes: `10` (`1.118568%` of generated axes);
- filled axes: `9` (`90%` of scorecard/order axes).

V209 comparator result:

- versus V92: `-32.83037032R`, `-33` trades, added `16`, removed `49`;
  added transfers were net-negative and removed transfers were net-positive.
- versus V97: `-17.37094527R`, `-29` trades, added `17`, removed `46`;
  added transfers were net-negative and removed transfers were net-positive.
- versus V198: `+0.36567013R`, `-57` trades; slight improvement by removing
  worse trades, still losing.
- versus V205: `+1.72772863R`, `-55` trades; improvement mostly by removing
  worse trades, still losing.

Verifier/proof status:

- A B5 verifier infrastructure gap was found while parsing V209: required
  route artifacts can be APFS `compressed,dataless` and the previous helper
  could hang on large raw ledgers. `verify_denominator_to_deployment_execution.py`
  now treats large zero-block route artifacts as bounded materialization
  failures instead of hanging, while allowing small compressed source/config
  files to remain readable.
- Focused validation for that verifier repair:
  `python3 -m py_compile verify_denominator_to_deployment_execution.py tests/test_denominator_to_deployment_verifier.py`
  passed; `pytest -q tests/test_denominator_to_deployment_verifier.py::test_route_artifact_dataless_placeholder_detection tests/test_denominator_to_deployment_verifier.py::test_materialize_file_provider_artifact_fails_fast_for_dataless`
  passed: `2 passed, 1 warning`.
- After artifact-locality repair/hydration, the patched route verifier
  completed deterministically and failed only the expected pre-patch B1/B5
  missed-row confidence-source contract:
  `broad_live_as_if_missed_opportunity_semantics_bad:{'missed:candidate_decision_quality:confidence_present_without_confidence_source': 24979}`.
- Candidate quality parity itself is clean in V209:
  candidate rows `25006`, package rows `23887`, scheduler backfill rows `6241`,
  missing counts `{}`, scheduler missing counts `{}`, scheduler parity mismatch
  counts `{}`.
- Order-executable transfer verifier scan is clean: `bad_counts={}` with
  scorecard rows `288`, order rows `50`, trade rows `18`, missed rows `24979`.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B1 provenance truth contract | PARTIAL/PATCHED, NOT YET PROVEN BY POST-PATCH REPLAY | Code/tests are patched, but V209 was launched before the patch and all `24979` missed rows still omit confidence source. | Run the smallest post-patch proof slice and require missed confidence-source omissions `0`. |
| B5 verifier/comparison precision | PARTIAL/PATCHED, VERIFIER NOW DETERMINISTIC | Dataless artifact fail-fast patch and focused tests pass; patched verifier no longer hangs and exposes the V209 missed-row B1 gap. | Keep fail-fast verifier; rerun route verifier after post-patch proof artifacts exist. |
| B7.2 hostile five-day value-transfer proof | OPEN/SUPERSEDED V209 EXPOSURE | V209 gives useful behavior exposure but fails the patched proof contract. | Do not accept V209. After B1/B5 post-patch proof is green, rerun hostile five-day B7.2 under patched harness. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Still blocked by B7. |

Selected next dependency batch:
`V210_B1_B5_POST_PATCH_MISSED_CONFIDENCE_SOURCE_PROOF`.

Patch type:

- verifier/proof-surface correctness repair already applied;
- next replay is a focused proof slice, not policy tuning and not a broad
  value-transfer claim.

Expected measurable effect before replay:

- candidate -> scorecard transfer: roughly same one-day fullgrid class as V208;
- missed rows should preserve `candidate_decision_quality_field_sources.confidence`
  or explicit default-confidence warning/flag;
- `confidence_present_without_confidence_source` must be `0`;
- executed broker-cost REFUSED/source-gap rows must remain `0/0`;
- behavior may be neutral; proof target is B1/B5 truth, not headline R.

Proof helped if the post-patch slice passes the patched verifier with missed
confidence-source omissions at zero. Proof failed if any missed/scorecard/order
or trade row still carries confidence without source. Only after this focused
proof is green should the route return to B7.2 hostile five-day value transfer.

Broker/live/final remain closed.

## Addendum - 2026-07-09T07:43:29Z V210 Green, B1/B5 Closed, V211 Selected

V210 completed as the smallest post-patch B1/B5 proof slice and is accepted as
a bounded truth/proof repair, not a full reservoir-transfer claim.

Completed V210 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V210_B1_B5_POST_PATCH_MISSED_CONFIDENCE_SOURCE_PROOF_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

V210 scope and behavior:

- scope: `2026-05-13`, 24-symbol fullgrid, repaired profile only;
- source / candidate / decision / scorecard / order-event / trade / missed /
  bucket rows: `180 / 8864 / 2304 / 96 / 9 / 2 / 8858 / 412`;
- W/L/F: `2 / 0 / 0`;
- net/gross/final R: `+0.52110312 / +0.65111456 / +0.65111456`;
- cash PnL: `+130.31196876`;
- risk cash / risk pct: `500.10039132 / 0.5`;
- cost R: `0.13001144`;
- filled trade risk decisions: `open-reduced-risk=6` order-level risk decisions,
  `0` full-risk filled trades in the one-day slice.

V210 same-window transfer:

- same-window source-bound/package R: `149486.17602471R`;
- package axes: `1101`;
- candidate-generated axes: `853` (`77.475023%` of package axes);
- scorecard/order axes: `4` (`0.468933%` of generated axes);
- filled axes: `2` (`50%` of scorecard/order axes);
- actual executable R inside window: `+0.52110312R`
  (`0.000349%` of same-window source-bound R).

V210 proof status:

- direct missed-row scan: `8858` missed rows,
  `confidence_present_without_source=0`;
- flow analyzer succeeded and wrote `601` flow bucket rows;
- source-bound parity succeeded: `8130` parity rows and `1101` leakage
  bucket rows;
- route builder succeeded with V210 prefixes in `OUTPUT_MANIFEST.json`
  under `broad_quality_parity_prefix` and `broad_holdout_gate_prefix`;
- route verifier succeeded: `ok=true`, `issue_count=0`,
  verified at `2026-07-09T07:38:32Z`;
- verifier B1/B5 scans: missed semantics `bad_counts={}`, candidate scan
  missing/parity mismatch counts `{}`, executed broker-cost/source-gap rows
  remain non-executed, and broker/live/final remain false.

Status correction:

| Batch | Current Status | Evidence | Next |
| --- | --- | --- | --- |
| B1 provenance truth contract | DONE for focused post-patch proof | V210 direct missed scan has `confidence_present_without_source=0`; route verifier `ok=true`, `issue_count=0`; candidate scan parity clean. | Keep B1 contract enforced in future B7 runs. |
| B5 verifier/comparison precision | DONE for current route proof surface | Dataless artifact fail-fast tests pass; verifier completed deterministically on V210 with no issues; manifest carries V210 quality/holdout prefixes. | Keep verifier as gate for V211 and later proofs. |
| B7.2 hostile five-day value-transfer proof | OPEN | V209 is exposure only because it launched before the B1/B5 missed-row patch. | Run V211 hostile five-day fullgrid under patched harness and compare same-window transfer to V92/V97/V198/V205/V209. |
| B8 live path | OPEN | `final_package_selected=false`, `live_trading_enabled=false`, `live_execution_activation_allowed=false`. | Still blocked by B7. |

Selected next dependency batch:
`V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF`.

Patch/replay type:

- no policy tuning before V211;
- V211 is a B7.2 value-transfer proof rerun of the hostile five-day bucket
  under the patched B1/B5 harness/verifier contract;
- expected behavior is behavior-equivalent or behavior-near V209 except for
  proof-surface fields; if trade selection moves materially, inspect added and
  removed trades before accepting the run.

Expected measurable effect before V211:

- candidate -> scorecard transfer should be in the same class as V209
  (`25006 -> 288`) unless the patched provenance surface exposes a replay
  materialization difference;
- missed confidence-source omissions must remain `0`;
- executed broker-cost REFUSED/source-gap rows must remain `0/0`;
- full-risk vs reduced-risk distribution must be reported separately;
- added/removed trades versus V92/V97/V198/V205/V209 must show whether changes
  came from conversion, selection, scheduler/reallocation, risk expression,
  order/fillability, lifecycle/exit, or only blocking trades.

V211 helped if it is verifier-clean and either improves honest executable
transfer or exactly identifies the next limiting B7 leak with same-window
counts. V211 failed if proof-surface issues reopen, if net behavior remains
negative with unexplained removed winners, if scorecard/order transfer remains
collapsed without missed-positive/negative attribution, or if a positive result
comes only from suppressed opportunity.

Broker/live/final remain closed.
