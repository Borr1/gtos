# Subagent B - V3 Versus Live Behavior Alignment And Limitations

Generated: 2026-06-04

Scope: Selector V3, Scheduler V3, and Execution Policy V3 versus the redacted_account/FTMO live behavior and hard-halt evidence now present on disk and `origin/main`.

Current anchors:

- Local HEAD inspected: `7d749d5bc research: refresh absolute moonshot master post v3`
- `origin/main` inspected after fetch: `11a51c049 research: package hard halt live evidence`
- Local branch relation after fetch: local `main` was ahead 44 and behind 33 before any merge.
- Production code was not modified by this subagent.

## Evidence Used

Primary V3 artifacts:

- `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_COMPLETION_AUDIT.json`
- `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_DEFAULT_OFF_PACKAGE.json`
- `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json`
- `research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_COMPLETION_AUDIT.json`
- `research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json`
- `research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01/V3_COMPLETION_AUDIT.json`
- `research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01/V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json`
- `research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json`

Primary live/VPS/hard-halt artifacts from `origin/main`:

- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_COMPLETION_AUDIT.json`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_VERIFICATION_RESULT.json`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_CANDIDATE_PACKET_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_RISK_EXPOSURE_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/DUAL_ANOMALY_LEDGER.jsonl`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/SUBAGENT_FINDINGS_CANDIDATES_SELECTORS_V3_2026-06-02.md`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/SUBAGENT_FINDINGS_EXECUTION_RISK_LIFECYCLE_2026-06-02.md`
- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/TRADE_FAILURE_REVIEW_2026-06-03.md`
- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json`

Evidence gap: `origin/main` does not contain `shadow_logs/gtos_vnext_runtime_decisions.jsonl` or `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`. Several June 2 line-level runtime findings therefore depend on the preserved subagent finding files rather than direct raw-log reinspection from this checkout. The missing raw logs are themselves a production-research gap.

## Bottom Line

The hard-halt live loss was not proof that the full V3 system failed in live. The evidence says the opposite: Selector V3, Scheduler V3, and Execution Policy V3 were loaded as default-off packages and were not live authority.

The live system matched V3 only at the broad policy-family compatibility layer: current production still used `momentum_exhaustion` primary with `partial_be_runner` exception selection, and V3 knew those families. The live system diverged from V3 at the authority layer: selector rules, money-risk scheduler authority, live activation, production packet completeness, broker-cost truth, exposure kill controls, and dual-broker lifecycle control were not the full V3 live operating system.

The required rebuild is not another report. It is a V3-live alignment engine that joins every live candidate/trade through Selector V3, Scheduler V3, Execution Policy V3, broker truth, and hard-halt outcomes, then promotes only the parts that can survive exact broker-net replay and strict production controls.

## V3 Artifact State

Selector V3:

- Full evidence rows: `289,928`
- Selector-scheduler-execution join rows: `289,928`
- Runtime selector rules: `2,027`
- Action counts:
  - `trade`: `46,430`
  - `reduce_risk`: `125,906`
  - `avoid`: `19,425`
  - `capture_repair`: `43,100`
  - `no_trade_by_evidence`: `55,063`
  - `source_required`: `4`
- Exact broker-real R rows: `0`
- Proxy-R rows: `289,917`
- Candidate ID mismatch rows: `180,186`
- Runtime package state: `enabled_by_default=false`, `apply_to_execution_default=false`

Scheduler V3:

- Full denominator rows: `289,928`
- Decision rows: `289,928`
- Money-risk rows: `289,928`
- Conflict rows: `289,928`
- Correlation rows: `290,372`
- Blocked-edge recovery rows: `179,575`
- Decision counts:
  - `ACCEPTED`: `67,365`
  - `ACCEPTED_REDUCED_RISK`: `8,716`
  - `REJECTED`: `142,570`
  - `DELAY`: `59,309`
  - `QUEUE`: `10,933`
  - `REPLACE`: `756`
  - `REQUIRE_SOURCE`: `279`
- Result classes:
  - `source_bound_proxy`: `289,909`
  - `exact_broker_real`: `8`
  - `missing_result`: `11`
- Runtime package state: default-off, no live activation.

Execution Policy V3:

- Policy variants: `1,353`
- Lane11 inherited variants: `890`
- V3-added variants: `463`
- Evaluation rows: `107,201`
- Routing rows: `7,861`
- Source-gap rows: `7,587`
- Policy family counts:
  - `partial_be_runner`: `793`
  - `trailing_runner`: `123`
  - `time_stop`: `42`
  - `no_trade`: `42`
  - `momentum_exhaustion`: `38`
  - `fixed_comparator`: `26`
  - `be_after_trigger`: `21`
  - `source_capture_route`: `258`
- Runtime package state: current production policy remains `momentum_exhaustion` primary with `partial_be_runner` exception; V3 did not change live execution behavior.

## Live State Observed By VPS/Halt Evidence

V3 promotion route:

- `VPS_V3_FTMO_COMPLETION_AUDIT.json` records:
  - Selector V3: `package_loaded_default_off`
  - Scheduler V3: `package_loaded_default_off`
  - Execution Policy V3: `package_loaded_default_off`
  - redacted_account: existing process group continued; no reload performed in that route.
  - FTMO: staged terminal verified; no `run_agent` activation in that route.
- `VPS_V3_FTMO_VERIFICATION_RESULT.json` records `ok=true`, `redacted_account_processes_active=true`, `ftmo_run_agent_not_active=true`, and `packet_default_off_no_broker_effect=true`.

Dual live supervisor route:

- Final architecture: one full redacted_account vNext runtime plus lightweight FTMO execution follower/projector bridge.
- Final process counts recorded:
  - redacted_account `run_agent_count`: `24`
  - redacted_account tick captures: `24`
  - FTMO `run_agent_count`: `0`
  - FTMO execution follower: `1`
  - Dual broker projector: `1`
  - M1 capture: `1`
  - MT5 terminals: `2`
- `DUAL_CANDIDATE_PACKET_LEDGER.jsonl` records June 2 trade-record outcome counts:
  - `LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN`: `10`
  - `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`: `66`
  - `REJECTED_GATE3_CIRCUIT_BREAKER`: `24`
  - `LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE`: `2`
- Rejection counts recorded:
  - `same_symbol_position_conflict_multi_ticket_lifecycle_unsupported`: `21`
  - `mt5_disconnected`: `2`
  - `cross_instrument_correlation_excess`: `1`
- `DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl` records execution policy counts for that day:
  - `partial_be_runner`: `94`
  - `momentum_exhaustion`: `6`
  - `missing`: `2`

Hard-halt broker truth:

- redacted_account at halt: balance/equity `99,965.20`, open positions `0`, pending orders `0`.
- Broker grouped trades: `91`; deals: `205`; orders: `207`.
- Source attribution:
  - `GTOS_SYSTEM`: `82` trades, `+$988.47`
  - `MANUAL_OR_TEST`: `8` trades, `-$5.17`
  - `OTHER`: `1` trade, `-$1,018.10`
- Current vNext activation window from 2026-05-29 through halt:
  - `77` GTOS trades
  - net `-$859.69`
  - wins/losses `31/46`
  - win rate `40.26%`
- Daily recent vNext activation:
  - 2026-05-29: `8` trades, `-$34.04`
  - 2026-06-01: `11` trades, `-$601.06`
  - 2026-06-02: `47` trades, `+$889.41`
  - 2026-06-03: `11` trades, `-$1,114.00`
- Worst recent GTOS symbols:
  - `XAUUSD`: `12` trades, `-$1,327.23`
  - `NDX100`: `15` trades, `-$1,151.56`
  - `ETHUSD`: `6` trades, `-$696.18`
  - `GBPJPY`: `2` trades, `-$543.61`
  - `UKOUSD`: `3` trades, `-$297.35`
  - `AUDJPY`: `1` trade, `-$274.05`
- Exit anatomy:
  - SL-like exits: `54`, net `-$9,280.84`
  - Raw comment partial/TP-like trades: `22`, net `+$5,638.03`
  - Final-classified partial/TP winners in review: `13`, net `+$4,677.44`

## Alignment Findings

### 1. Live Did Not Run Selector V3 As Authority

Evidence:

- `SELECTOR_V3_DEFAULT_OFF_PACKAGE.json` records `enabled_by_default=false` and `apply_to_execution_default=false`.
- `VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl` records Selector V3 as loaded from disk with `runtime_effect_now=false`.
- `VPS_V3_FTMO_COMPLETION_AUDIT.json` records Selector V3 state as `package_loaded_default_off`.
- `SUBAGENT_FINDINGS_CANDIDATES_SELECTORS_V3_2026-06-02.md` records config evidence: `selector_v3_enabled: false`, `selector_v3_apply_to_execution: false`.

Finding:

The live selector authority remained the current vNext/moonshot production path plus the earlier Lane03-style default-off package context, not Selector V3 as a production gate. Any claim that V3 selector decisions caused the June 2/June 3 live outcomes is not supported by the tracked evidence.

Required rebuild direction:

Build `V3_LIVE_SELECTOR_ALIGNMENT_LEDGER.jsonl` with one row per live candidate/trade:

- live candidate ID and broker ticket if any
- live selector decision and refusal reason
- Selector V3 matched rule or `no_matching_rule`
- Selector V3 action
- required source fields present/missing
- live/V3 divergence class
- broker-net result when available

Production activation must require this ledger to prove that V3 would have rejected, reduced, delayed, or admitted each hard-halt trade for exact reasons.

### 2. Live Execution Families Matched V3 Comparators, But V3 Did Not Control Routing

Evidence:

- Current system map says production execution policy is `momentum_exhaustion` primary with `partial_be_runner` exception selection.
- `V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json` records the same production policy status and keeps V3 default-off.
- `VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl` records `momentum_exhaustion` and `partial_be_runner` as supported/matched scenarios, with live activation blocked by package state.
- `DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl` records June 2 policy counts: `partial_be_runner=94`, `momentum_exhaustion=6`, `missing=2`.

Finding:

The live system used policy families that V3 understands, but not the V3 routing/variant engine as authority. The hard-halt loss therefore exposes that the current production partial/momentum policy stack is insufficient under weak selection, loose exposure, cost gaps, and symbol/session clusters. It does not prove that V3's expanded 1,353-variant package failed.

Required rebuild direction:

Build `V3_LIVE_EXECUTION_ALIGNMENT_LEDGER.jsonl` over every hard-halt GTOS trade and candidate:

- live selected policy
- V3 recommended policy family and variant
- V3 source feasibility
- live exit path
- broker-net R
- cost/swap drag
- divergence reason
- whether V3 would keep, change, reduce, time-stop, trail, or reject

Execution V3 cannot be promoted from family-level compatibility. It needs live-event alignment by ticket and candidate.

### 3. Scheduler V3 Was Not Live Authority; Live Exposure Was Too Loose

Evidence:

- `SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json` records default-off package state and forbids static max-trades/count-cap/top-N authority.
- `VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl` demonstrates only synthetic scenarios for source-required/admit/reduce/reject and records live activation not allowed by package.
- `TRADE_FAILURE_REVIEW_2026-06-03.md` records `config/profiles/redacted_account.yaml` had `risk.max_concurrent: null`, with old count cap bypassed when vNext aggregate budget logic approved the row.
- `DUAL_RISK_EXPOSURE_LEDGER.jsonl` records large live exposure snapshots, including redacted_account positions rising to `13` and margin reaching `80,094.63` with margin free `20,615.65`.
- Hard-halt review records `47` GTOS trades on 2026-06-02 and several two-minute clusters, including a June 1 cluster net `-$673.03`, a June 2 10:46 cluster net `-$782.24`, a June 2 16:31 cluster net `-$522.56`, and a June 2 17:45 cluster net `-$311.25`.

Finding:

The live risk/exposure layer was not Scheduler V3 as a final money-risk, cluster-risk, symbol-risk, and session-risk governor. The observed live behavior accepted too many correlated or weak trades in short windows. The V3 scheduler research contains the correct direction, but the live system did not enforce it.

Required rebuild direction:

Build Scheduler V4 as production authority, not a report:

- non-bypassable account exposure ceiling
- daily loss stop
- session loss stop
- symbol loss stop
- correlated cluster cap
- new-trade minimum edge threshold after cost
- broker `order_calc_profit` open-risk requirement for every open position
- position-count emergency ceiling as a fail-safe, even when money-risk is primary
- hard halt latch that blocks new entries until cleared

Then replay all hard-halt trades through Scheduler V4 and prove which trades would be accepted, reduced, queued, delayed, or rejected.

### 4. Live Selector Thresholds Were Too Weak For Broker-Net Reality

Evidence:

- `TRADE_FAILURE_REVIEW_2026-06-03.md` identifies weak selector thresholds in live examples:
  - USDCAD expectancy `0.0465R`, profit factor `1.0909`, win rate `37.21%`
  - JP225/CHFJPY expectancy `0.0476R`, win rate `28.57%`
  - NDX100 examples around `0.0346R` and `0.0252R`
- Hard-halt symbol results show large losses concentrated in `XAUUSD` and `NDX100`: combined `-$2,478.79`.
- The same review shows June 2 net profit relied heavily on one `GER30` winner of `+$1,318.24`; excluding it, the recent window was approximately `-$2,177.93`.

Finding:

The production selector allowed low-expectancy, cost-sensitive, and symbol-concentrated trades. Selector V3 has much richer action classes, but its broad denominator is still proxy-heavy and not broker-net calibrated. The live loss proves the next selector cannot use generic positive proxy expectancy as enough authority.

Required rebuild direction:

Selector V4 must train/evaluate on broker-net and hard-halt outcomes where available, with source-bound proxy kept separate. Minimum gates:

- minimum broker-net or cost-stressed expectancy by symbol/session/mechanism
- minimum profit factor
- minimum sample/stability threshold
- drawdown and losing-streak sensitivity
- symbol kill/reduce states for `XAUUSD`, `NDX100`, `ETHUSD`, `GBPJPY`, `UKOUSD`, `AUDJPY` until repaired
- deconcentration limits so one large winner cannot mask a broken family
- live recent performance decay/penalty
- source-required instead of trade when selected-cell/risk/cost fields are incomplete

### 5. Broker Cost And Swap Broke The Local-Risk Interpretation

Evidence:

- Hard-halt review records `10` recent entries with unresolved entry commission/swap after history lookup.
- ETHUSD ticket `242689402` had entry cash risk around `$254.66`, close net loss `-$673.62`, swap `-$391.16`, commission `-$7.73`, and broker profit `-$274.73`.
- Lane18 improved broker truth capture, but hard-halt evidence still shows cost/swap gaps and broker-net mismatch were live blockers.

Finding:

The live system could not rely on selected-cell risk alone. Broker cost/swap/commission can dominate the expected R for certain symbols and holding patterns. V3 artifacts separate exact broker-real R from proxy R, but production still needs broker-cost-aware selection and execution.

Required rebuild direction:

Add a production cost gate and cost-calibrated R model:

- block or reduce symbols where swap/commission/spread can exceed configured tolerated R drag
- require broker history cost join for recent comparable trades before increasing risk
- add policy-specific holding-time cost stress
- add no-trade if cost fields are stale, missing, or generic
- maintain exact broker-net R as the primary production feedback metric

### 6. Live Logs And Packets Still Lack Required V3-Grade Fields

Evidence from `SUBAGENT_FINDINGS_CANDIDATES_SELECTORS_V3_2026-06-02.md`:

- Runtime decision JSONL had `296` backward timestamp transitions.
- Safety-gate blocked rows contradicted candidate-generation state: all `197` `broader_origin_safety_gate_blocked` rows had `candidate_count=1` while nested source packet said no candidate generated.
- One selected-cell risk ledger gap actively blocked a US30_cash candidate.
- `strategy_follow_evaluations.jsonl` had `2,261` June 2 rows with stale baseline label `LIVE_AI_J46_J49_BASELINE_COMPARATOR`, `side=UNKNOWN`, `source_hash=null`, and `dedupe_key=null`.
- Strategy follow evals had `141` backward timestamp transitions.
- Candidate LTF path recovery had `1,405` June 2 rows, all post-decision/no-execution; `984` same-M1 ambiguous and `149` source-blocked.
- Candidate path follow M15/OHLC-only had `1,487` rows; `776` ambiguous and `709` OHLC-only.
- Pending candidate lifecycle had `256` June 2 rows with `decision_time_utc=null`, `decision_spread_value_source_safe=null`, and `source_hash=null`.
- Pending lifecycle failed order-send diagnostics had `46` `triggered_order_send_failed_retry` rows with `order_result_retcode=null`.
- June 2 trade records retained false AI labels: `316` redacted_account and `138` legacy rows had `ai_decision=CANDIDATE`, `ai_grade=A+`, `ai_confidence=100`.

Finding:

The live packet layer was not V3-grade. It lacked stable chronology, source hashes, decision timestamps, spread source safety, retcodes, exact policy identity, and accurate labels. This blocks exact replay and allows stale or misleading live evidence to survive.

Required rebuild direction:

Implement a unified `LiveDecisionPacketV4` schema that is required for every candidate, skip, reject, placed order, modify, close, follower action, and emergency action. It must include:

- monotonic event sequence
- event time, broker time, local write time
- source hash and source path
- selected-cell proof
- selector rule identity
- scheduler decision identity
- execution policy variant identity
- spread/cost source status
- MT5 request/retcode/comment/request_id/retcode_external
- broker ticket/deal/order/position identity
- account namespace
- source-bound proxy versus broker-real result flag
- stale label blocker

Packets that cannot meet this schema must be `source_required` or `capture_repair`, not trade authority.

### 7. Dual-Broker Follower Was Operationally Useful But Not Full Broker-Local Intelligence

Evidence:

- `DUAL_COMPLETION_OR_CONTINUATION_AUDIT.json` records final architecture as redacted_account full runtime plus lightweight FTMO execution follower/projector bridge.
- FTMO `run_agent_count` was `0`; FTMO execution follower count was `1`.
- Known non-blocking followup in the audit: determine whether FTMO should have independent broker-local exit management.
- `SUBAGENT_FINDINGS_EXECUTION_RISK_LIFECYCLE_2026-06-02.md` records six active FTMO target trades lacked cash-risk provenance before repair/reload.
- `DUAL_ANOMALY_LEDGER.jsonl` records repaired issues around FTMO target tick deferral, target lifecycle recovery, null result hazards, follower persistence crash, and dual bridge context projection.

Finding:

The FTMO side was a copier/follower bridge, not a complete second vNext brain with independent selector/scheduler/execution/broker-local lifecycle truth. That is acceptable as an interim architecture, but it is not the final moonshot dual-account operating system.

Required rebuild direction:

FTMO must get broker-local validation for:

- symbol mapping and contract geometry
- spread/tick/session state
- `order_calc_profit` risk for every copied intent
- local SL/TP feasibility
- partial/residual state
- broker-local BE/trailing/time-stop modifies
- close/deal/cost reconciliation
- follower replay dedupe and crash recovery

If FTMO is only a follower, the system must label it as follower-only and block independent conclusions about FTMO strategy quality.

### 8. Emergency Halt Was Not Atomic

Evidence:

- `TRADE_FAILURE_REVIEW_2026-06-03.md` records that the first emergency close was not enough because agents were still running.
- JP225 ticket `242752405` appeared or continued after initial close.
- Final halt required direct process shutdown and scheduler disable.
- Final halt flags recorded:
  - `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
  - `pipeline_state/RESEARCH_RUNTIME_HALT.flag`
  - `knowledge_base/meta/AUTOSTART_DISABLED.flag`

Finding:

The live system lacked a single atomic halt path that closes exposure, blocks new entry, stops producers/followers, and proves zero process restart authority. This is a production control failure independent of selector/execution edge.

Required rebuild direction:

Build one `hard_halt` command and verifier:

- atomically sets halt flags
- disables scheduler entry authority
- blocks watchers from restart loops
- stops producers/followers
- closes or preserves positions according to explicit owner mode
- verifies MT5 positions/orders
- verifies no new trade records after halt time
- writes immutable halt proof with process IDs and broker state

## V3 Limitations Exposed By Live Evidence

These are not reasons to discard V3. They are the rebuild list required before V3 becomes production authority.

1. V3 is still default-off. The live system loaded V3 packages but did not run them as authority.
2. Selector V3 has `0` exact broker-real R rows in its broad denominator and `289,917` proxy-R rows.
3. Scheduler V3 has only `8` exact broker-real result rows and `289,909` source-bound proxy rows.
4. Selector V3 has `180,186` candidate ID mismatch rows that require lineage repair before exact live replay claims.
5. Execution Policy V3 has `7,587` source-gap rows and many variants remain source/feasibility gated.
6. Source Capture Repair shows large unresolved/non-reconstructable surfaces: `3,471,773` non-reconstructable gap rows in later lanes and `2,823` read-only export requirement rows in the source-capture route.
7. V3 lacks a hard production-loss response loop tied to hard-halt evidence.
8. V3 does not yet encode broker-net recent underperformance as a live selector/scheduler penalty.
9. V3 does not yet prove exact behavior for every June 2/June 3 hard-halt trade because raw runtime logs are not fully tracked on `origin/main`.
10. V3 does not yet provide atomic dual-broker production control with independent FTMO broker-local lifecycle authority.

## Required Rebuild Directions

### A. V3 Live Alignment Replay

Create a route that consumes:

- hard-halt broker trade groups
- dual supervisor ledgers
- V3 selector package
- V3 scheduler package
- V3 execution package
- raw VPS runtime logs imported as evidence, if available

Output one row per live candidate/trade with:

- active live selector/scheduler/execution decision
- V3 selector decision
- V3 scheduler decision
- V3 execution decision
- broker-net result
- divergence class
- missing source fields
- required repair

Completion is not valid until all `77` recent GTOS trades and the June 2 candidate/reject/skip surface are accounted.

### B. Selector V4

Use hard-halt broker truth as mandatory negative intelligence:

- kill/reduce broken symbol/session/mechanism families
- require cost-stressed expectancy
- reject micro-edge rows
- add concentration and recent-loss penalty
- preserve avoid/reduce/capture/trade classes
- separate exact broker-real from proxy evidence in all decisions

### C. Scheduler V4

Make live scheduling account-risk first and fail-closed:

- account exposure ceiling
- cluster exposure ceiling
- symbol exposure ceiling
- session and daily loss stops
- position-count emergency cap
- no new risk when open-risk provenance is incomplete
- no new risk after hard halt

### D. Execution Policy V4

Policy routing must include:

- broker-net cost drag
- swap exposure
- time-in-trade hazard
- symbol-specific failure streams
- partial/BE/trailing/time-stop variants
- stop-loss cascade detection
- policy disable/reduce after live underperformance

### E. Evidence Layer Repair

Promote packet completeness to production authority:

- no source hash, no trade authority
- no selected-cell risk proof, no trade authority
- no spread/cost source, no trade authority
- no MT5 retcode on failed order send, repair blocker
- no chronological event sequence, replay blocker
- stale labels become verifier failures

### F. Dual Broker Operating System

Either make FTMO a full broker-local runtime or explicitly prove follower-only limitations:

- local risk calculation
- local spread/session/tick validation
- local lifecycle and residual management
- local broker-cost reconciliation
- local emergency halt proof

## Final Assessment

The live hard-halt was caused by a production system that was still too loose at selector, scheduler, cost, source-packet, exposure, and emergency-control layers. V3 contains much of the correct architecture, but it was not live authority. The next work should not assume V3 is ready because its replay packages are strong, and it should not discard V3 because live lost money. The correct path is to force exact alignment between V3 decisions and the hard-halt live surface, then rebuild Selector V4, Scheduler V4, Execution Policy V4, and the evidence layer from that proof.
