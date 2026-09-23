# Phase 3 Deferred Tasks And Next Steps Ledger

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Purpose

This ledger consolidates the work that was deferred while Sierra Chart / primitive data source work was prioritized. It reconciles:

- current Phase 3 path-scaling state,
- V2/V2b/V3 next work,
- orderflow and Sierra/Databento data-source next work,
- `research/ml_program/MASTER_BACKLOG.md`,
- stale or superseded items that should not be blindly reopened.

This is not a live-trading change request. No prompt, config, risk, or execution behavior is changed by this document.

## Source Evidence Read

Primary current-state sources:

- `.context/LIVE_STATE.md` regenerated 2026-05-02.
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `.context/02_session_handoffs/SESSION_53_PHASE_3_PATH_SCALING_V1_V3_FRESH_SESSION_HANDOFF.md`
- `research/ml_program/MASTER_BACKLOG.md`
- `research/ml_program/literature/HYPOTHESIS_BACKLOG.md`
- `research/ml_program/PRE_REGISTERED_HYPOTHESES.md`
- `research/ml_program/models/k54_v3/report.md`
- `.context/02_session_handoffs/SESSION_45_PHASE_2_CLOSE_AND_K54_V4_FAIL.md`

Primary Phase 3 / orderflow / Sierra sources:

- `research/phase_3_external_feed_validation/PHASE3_STATUS_NUMBERS_AND_PLAN_2026-05-02.md`
- `research/phase_3_external_feed_validation/PHASE3_EXECUTION_UPDATE_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_FINAL_DISPOSITION_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_RISK_ACCOUNTING_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_RESEARCH_CLOSURE_SYNTHESIS_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md`
- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_NQM26_DEPTH_PROBE_2026-05-02.md`

## Current Ground Truth

1. Path scaling remains a research branch, not a promoted trading policy.
2. V0 and V1 are research-closed. Fixed-R lock-only did not beat J46 globally.
3. V2 is discovery-closed with structural signal present. The swing headline is concentration-blocked; OB-boundary is the cleanest V2b candidate.
4. V2b has post-cutoff rows but `0` resolved post-cutoff OB-boundary/J46 pairs. It is unevaluable, not failed.
5. V3 is design-only and blocked from outcome mining until V2b answers level quality.
6. Orderflow is not dead. It is label-constrained and symbol-specific. NAS100 adverse-selection is the strongest branch, but not a registered replay or live filter.
7. Sierra Chart parser proof is complete for tiny delayed `NQM26-CME` samples. It is enough to prove file readability, not enough for market conclusions.
8. K54 v3 and K54 v4 failed as primary ML architectures. K-family work should remain shadow/refinement or wait for larger valid cohorts, not continue architecture iteration on the same cohort.
9. The master backlog is still broad: 180 items, 145 `PENDING`, 11 `DEFERRED`.

## Priority Stack To Resume

| Rank | Track | Resume action | Blocked by | Output artifact |
|---:|---|---|---|---|
| 1 | V2b forward validation | Keep collecting/replaying post-cutoff OB-boundary/J46 pairs, with swing/FVG/fixed-R comparators and no-leak diagnostics. | Resolved post-cutoff pairs currently `0`. | Rolling V2b interim reports, not promotion dossiers. |
| 2 | V2 confluence/disagreement | Study FVG/OB both-fire, FVG-only, OB-only, neither, sequence, and Composite-vs-best-single behavior. | Same-dataset only until forward rows exist. | Forward-only confluence ledger after V2b resolved rows exist. |
| 3 | Pre-fill delivery/reversal idea | Add pre-fill delivery-path fields before testing the two-leg delivery-leg plus reversal-leg hypothesis. | Current V2 event log is post-fill only. | Delivery-path capture spec / replay extension. |
| 4 | V3 architecture | Build risk-bank invariant tests and reentry ledger schema; do not mine outcomes. | V2b level-quality result and pending-limit lifecycle telemetry. | V3 unit tests plus spec update. |
| 5 | Sierra active depth | Capture at least 30 active-session minutes of `NQM26-CME` delayed depth with nonblank Market Depth Historical Graph. | Market must be active; current sample is weekend/closed. | New Sierra depth probe report. |
| 6 | Databento/Sierra parity | Compare Sierra `.depth` fields to Databento MBP/MBO over the same UTC window. | Active Sierra sample and matching Databento event window. | Parity report with `NO_PROMOTION_VERDICT`. |
| 7 | NAS100 orderflow forward | Follow A1: trades + MBP-1 for each new NAS100 candidate; MBP-10 only for pre-declared comparator windows. | Actual-R and winner-side sample size. | NAS100 forward collection reports. |
| 8 | Pending-limit telemetry | Draft minimal telemetry for pending intent/fill/expiry/no-trigger. | Requires explicit approval before live observability changes. | Research-only telemetry spec, then optional implementation ticket. |
| 9 | Methodology infrastructure | Implement M-7, M-12, M-13 style gates across primary evaluation pipelines. | Must preserve historical claim ledger and effective-N accounting. | `dsr_diagnostics` / PBO / weighted-SE infrastructure. |
| 10 | Execution observability | Integrate L-6/O-6 token logging, L-7/O-7 close-side slippage, and O-8 trade-record enrichment when approved. | Main-thread code approval. | Shadow/telemetry PRs, no trading-behavior change. |

## Path Scaling Work

### V2b: immediate work

Current counters from the V2b forward artifact:

- post-cutoff event rows: `264`
- wanted OB-boundary/J46 rows: `110`
- resolved wanted rows: `0`
- validation status: `BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS`

Next work:

1. Continue post-cutoff replay/collection until at least one resolved OB-boundary/J46 comparison exists.
2. Keep OB-boundary as the registered V2b candidate.
3. Keep FVG and swing as comparators, not replacement primaries.
4. Emit lower-timeframe availability, ambiguity flags, same-bar policy, cost sensitivity, and no-leak diagnostics.
5. Do not claim validation until the registered sample floors are met: all-enabled paired n `>=150`, target paired n `>=75`, and concentration cap `<=45%`.

### V2 confluence/disagreement: deferred work now reopened

Current V2 confluence facts:

- full resolved paired events: `4394`
- 2026 paired events: `474`
- entry consistency violations: `0`
- full FVG minus OB mean: `+0.009231R`
- 2026 FVG minus OB mean: `+0.132135R`
- full both FVG+OB fire: `1256`
- 2026 both FVG+OB fire: `305`
- full FVG-then-OB sequence: `1075 / 1256`
- 2026 FVG-then-OB sequence: `282 / 305`
- full Composite minus best single mean: `-0.296092R`
- 2026 Composite minus best single mean: `-0.234958R`

Next work:

1. Build a forward-only confluence ledger once V2b resolved rows exist.
2. Track buckets: both improve, FVG-only improves, OB-only improves, neither improves.
3. Track lock-firing sequence: FVG then OB, OB then FVG, same-time.
4. Track whether FVG is a delivery confirmation and OB is a tail-preserving floor.
5. Keep Composite as an overlock warning unless arbitration survives forward evidence.

### Delivery-leg plus reversal-leg hypothesis

Status: `DATA_GAP_SPEC_ONLY`.

The idea is coherent, but the current event log cannot score it because it does not retain the full pre-fill delivery path from setup decision to pending-limit touch.

Required fields before any scoring:

- `original_poi_type_and_bounds`
- `pending_limit_created_utc`
- `setup_decision_close_utc`
- `pre_fill_m1_or_m5_path_rows_until_fill_expiry_or_cancel`
- `as_of_delivery_direction_structures_before_fill`
- `delivery_leg_candidate_entry_sl_tp_and_costs`
- `reversal_leg_candidate_entry_sl_tp_and_costs`
- `mutual_exclusion_or_aggregate_risk_budget_policy`
- `broker_fill_or_pending_intent_lifecycle_state`

### V3: design-only work allowed

Current V3 status: `DESIGN_ONLY_BLOCKED_PENDING_V2B_RESOLVED_PAIRS`.

Allowed now:

1. Build unit tests for the aggregate worst-case rule:
   `realized_closed_leg_r + sum(open_leg_stop_if_hit_r) - estimated_remaining_cost_r >= -1.0R`.
2. Define leg ledger fields and ambiguity flags.
3. Define pending/fill/expiry state transitions.
4. Draft reentry trigger families as design-only.

Forbidden now:

1. No V3 outcome replay.
2. No generic trailing stop.
3. No reentry scoring without pending-limit lifecycle telemetry.
4. No promotion claim from V3 without a separate future promotion dossier.

## Orderflow, Databento, Sierra Work

### Current data reality

From `ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.md`:

- current candidate-feature rows loaded: `518`
- current supported candidate count: `58`
- current unsupported candidate count: `57`
- unsupported symbols: `GBPJPY=23`, `USDJPY=34`
- current supported candidate events by symbol in manifest: `GBPUSD=21`, `NAS100=12`, `US30_cash=1`, `XAGUSD=10`, `XAUUSD=10`
- actual broker-R remains sparse in current diagnostics.

From aggressive orderflow/current-state summaries:

- surgical candidate-window trades feature rows: `59`
- primary ok rows: `58`
- joined synthetic/path targets: `22`
- synthetic winners/losers: `12 / 10`
- actual broker-R available: `1 / 58`
- expanded MBP-10 rows: `324`, ok `320`, no-data `4`
- NAS100 MBO candidate/context rows: `12 / 47`
- NAS100 synthetic winners/losers: `1 / 10`

### Orderflow next actions

| Priority | Action | Status | Next step |
|---:|---|---|---|
| 1 | A1 NAS100 forward label/depth collection | `COLLECT_FORWARD_NOT_REPLAY` | Collect trades + MBP-1 for every new NAS100 candidate; MBP-10 only for pre-declared windows. |
| 2 | A2 XAUUSD limit-intent telemetry | `BLOCKED_BY_MISSING_LIVE_TELEMETRY` | Draft telemetry spec; do not spend more Databento on the audited historical row. |
| 3 | A3 XAUUSD continuation contrast | `WAIT_FOR_LABEL_CONTRAST` | Wait for both winner and loser labels before broad depth spending. |
| 4 | A4 unsupported symbol proxy mapping | `BLOCKED_BY_PROXY_MAPPING` | Validate one proxy before pulling futures orderflow for it. |
| 5 | A5 MBO queue behavior | `DEFERRED_NOT_REGISTERED` | Keep MBO deferred unless MBP-10 leaves a precise queue/order-identity question unanswered. |

### Sierra next actions

Current Sierra proof:

- `NQM26-CME.2026-05-02_delayed.depth` size `16792` bytes
- header magic `0x44444353`
- header size `64`
- record size `24`
- version `1`
- records `697`
- byte remainder `0`
- non-empty batches `1`

Next work:

1. Capture an active-session `NQM26-CME` delayed depth file for at least `30` minutes.
2. Rerun `research/sierrachart_data_source_research_2026-05-02/tools/sierra_depth_probe.py`.
3. Export or locate the matching Sierra intraday data needed for price alignment.
4. Build Databento parity for the same UTC window.
5. Only after parity, decide whether Denali real-time depth is useful.

## ML / K54 / K55 Work

Current facts:

- K54 v3 failed as a primary architecture: 1 of 6 testable gates passed; realized-R lift `-0.1076R/trade`; feature stability top-50 Jaccard `0.1685`.
- K54 v4 failed as primary: all three architectures failed 4 of 7 testable gates; Q1 closes with K-family reframed as K55-shadow/refinement only.
- Q2 sequence models are deferred until cohort n `>=5000` with regime-balanced labels.

Allowed next work:

1. K55 shadow/refinement only, not primary ML replacement.
2. NAS100/US30 or top-confidence refinements only as shadow until forward evidence clears gates.
3. Cohort expansion and data-quality work before any new K54 architecture iteration.
4. Free-feed/cross-asset features that are substrate-immune or as-of joinable.

Do not do next:

1. Do not iterate K54 v5/v6 on the same cohort.
2. Do not reopen sequence models before the n `>=5000` trigger.
3. Do not treat K54 top-percentile as an independent alpha until it is separated from mechanical OB concentration.

## Master Backlog Mechanical Snapshot

Parsed from `research/ml_program/MASTER_BACKLOG.md`.

| Status | Count |
|---|---:|
| PENDING | 145 |
| DEFERRED | 11 |
| DONE | 5 |
| FAILED | 4 |
| FILED | 2 |
| DSR_VALIDATED | 2 |
| DSR_FAILED | 2 |
| DONE_NULL | 1 |
| ANSWERED_BY_NA8 | 1 |
| COMPLETED | 1 |
| PARTIAL | 1 |
| SHIPPED + EXT_PENDING | 1 |
| SHIPPED + EXT_DESIGN | 1 |
| DESIGN_DONE | 1 |
| DESIGN_DONE_PENDING_INTEGRATION | 1 |
| DONE-FAIL | 1 |
| Total | 180 |

## All Pending IDs By Section

Descriptions remain in `MASTER_BACKLOG.md`; this table preserves the full open ID set without duplicating the whole backlog text.

| Section | Count | Pending IDs |
|---|---:|---|
| M methodology | 10 | M-5, M-6, M-7, M-10, M-11, M-12, M-13, M-14, M-15, M-16 |
| K K54 architecture | 14 | K-5, K-6, K-7, K-8, K-9, K-10, K-11, K-12, K-13, K-14, K-15, K-16, K-17, K-18 |
| V vol-conditioning | 9 | V-1, V-2, V-3, V-4, V-5, V-6, V-7, V-8, V-9 |
| A asset specialists | 18 | A-1, A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-9, A-10, A-11, A-12, A-13, A-14, A-15, A-16, A-17, A-18 |
| R risk policy | 9 | R-1, R-2, R-3, R-4, R-5, R-6, R-7, R-8, R-9 |
| E edge mechanism | 5 | E-1, E-2, E-3, E-4, E-5 |
| X reopened tracks | 7 | X-1, X-2, X-3, X-4, X-5, X-6, X-7 |
| C cheap A/B tests | 8 | C-2, C-3, C-4, C-5, C-6, C-7, C-8, C-9 |
| D data extraction | 12 | D-1, D-2, D-3, D-4, D-5, D-6, D-7, D-8, D-9, D-10, D-11, D-12 |
| P architecture/system flow | 9 | P-1, P-2, P-3, P-5, P-6, P-7, P-8, P-9, P-10 |
| L LLM/AI | 6 | L-1, L-2, L-3, L-4, L-5, L-8 |
| S K55 shadow | 5 | S-1, S-2, S-3, S-4, S-5 |
| Q sequence models | 0 | none |
| Z long-horizon quantum | 4 | Z-1, Z-2, Z-3, Z-4 |
| O operational ops | 3 | O-3, O-5, O-8 |
| U open research questions | 14 | U-1, U-2, U-4, U-6, U-8, U-9, U-10, U-11, U-12, U-13, U-14, U-15, U-16, U-17 |
| RR recurring | 7 | RR-1, RR-2, RR-3, RR-4, RR-5, RR-6, RR-7 |
| B composite bundles | 5 | B-2, B-3, B-4, B-5, B-7 |

## All Deferred IDs

| ID | Tier | Deferred reason / trigger |
|---|---|---|
| K-1 | T2 | Volume-bar resampling deferred by MT5 retail `volume=0`; substituted by tick-count-time bars; re-run on paid LOB feed or at least 30 days ticks across 7 instruments. |
| K-2 | T2 | Dollar-bar resampling deferred for same volume substrate gap as K-1. |
| K-3 | T2 | Imbalance-bar resampling deferred; tick-direction tags require depth/LOB data not present in MT5 retail substrate. |
| Q-2 | T3 | Time-LLM shelved by Q-1 DLinear no-go; re-run at cohort n `>=5000` with regime-balanced labels. |
| Q-3 | T3 | Chronos shelved by Q-1 DLinear no-go; same re-run trigger. |
| Q-4 | T3 | iTransformer shelved by Q-1 DLinear no-go; same re-run trigger. |
| Q-5 | T3 | PatchTST shelved by Q-1 DLinear no-go; same re-run trigger. |
| Q-6 | T3 | TCN shelved by Q-1 DLinear no-go; same re-run trigger. |
| Q-7 | T3 | LSTM baseline shelved by Q-1 DLinear no-go; same re-run trigger. |
| Q-8 | T3 | Sequence model architecture decision deferred until Q-1 reruns cleanly at n `>=5000`. |
| Q-9 | T3 | Chen-Pelger-Zhu 2024 RNN macro-encoder shelved by Q-1 DLinear no-go; same re-run trigger. |

## Other Unclosed Non-Pending Items

| ID | Status | Meaning for next work |
|---|---|---|
| B-6 | `PARTIAL` | Methodology bundle partly done. Remaining high-priority pieces: M-7, M-12, M-13. |
| L-6 | `DESIGN_DONE` | Token-usage logger designed but not shipped. Integration overlaps O-6. |
| O-1 | `FILED` | `_trade_index.json` frozen-at-2026-04-04 ticket exists; needs main-thread triage. |
| O-2 | `FILED` | NDX100 vs NAS100 alias documentation ticket exists. |
| O-6 | `DESIGN_DONE_PENDING_INTEGRATION` | HALLUC-2 token logger integration pending. |
| O-7 | `SHIPPED + EXT_PENDING` | Entry slippage shipped; close-side extension pending. |

## Section-Level Backlog Interpretation

| Section | Current interpretation |
|---|---|
| M | Highest priority for research quality. M-7/M-12/M-13 should be done before any new lift claim gets treated as serious. |
| K | Do not dispatch K-18 literally as a new K54 primary model on the current cohort. Treat K items as feature ideas, shadow/refinement, or future cohort-expansion inputs. |
| V / P-1 / B-2 | Portfolio-wide vol-conditioning is not immediate after H-PM01/NA8. Keep as Phase 5 or symbol-specific work, especially NAS100-only. |
| A | Asset-specialist work remains valuable, especially index gamma/proxy features, JPY carry/funding, gold real-price/COT/LBMA. Needs as-of data joins. |
| R / B-3 | Risk-policy bundle remains important but must layer over DSR-surviving J46/S79 and not override safety gates. |
| E | Edge-mechanism validation remains useful: stop clusters, latent liquidity, OB decay, uncorrelated edge discovery. |
| X | Reopened microstructure tracks are mostly waiting on proper clock/depth/tick data; X-6 reconciliation should be treated as methodology history unless a specific claim depends on it. |
| C | C-9 is the current active path-scaling program. C-7 Path-9 deep-dive is a discovery branch. C-2 through C-6/C-8 remain possible existing-data tests. |
| D | Data extraction is a core unblocker: D-6, D-11, and proxy/feed work should be prioritized before broad model work. |
| L / B-5 | LLM/tooling should start with observability and grounding, not new prompt behavior. Component 3B/Bull-Bear-Judge remains shadow-only unless separately approved. |
| S | K55 shadow is the only appropriate K-family deployment shape now. |
| Q | Fully deferred until n `>=5000`; do not spend effort here now. |
| O | O-8 plus slippage/pending telemetry directly improves label truth and V3 readiness. |
| U / RR | Research questions and recurring audits remain support work; pull them when they unblock a ranked track. |

## Staleness And Artifact Warnings

1. Some same-date Phase 3 reports used older shorthand saying V2b had no post-cutoff rows. The current precise blocker is no resolved post-cutoff OB-boundary/J46 pairs.
2. `PHASE3_VALID_BASE_AUDIT_2026-05-02.md` contains older row wording; use `PHASE3_EXECUTION_UPDATE_2026-05-02.md` and `research_current_state.md` for the corrected state.
3. Master backlog individual K-items can look open even though composite B-1/K54 primary failed. Do not use raw `PENDING` status alone to restart K54 architecture work.
4. Mutable shadow logs are not immutable population counts. Any future claim must pin source files, timestamps, hashes where possible, and data caps.
5. Databento estimated costs are tool estimates; vendor final billing can differ. Do not report spending as exact unless checked against vendor billing.
6. Sierra samples currently prove parser readability only. They do not prove active-market depth quality, parity, or lead-lag.

## What Is Needed From The Owner

No immediate strategic decision is required to continue research/tooling.

Helpful owner actions:

1. Keep Sierra Chart configured for `NQM26-CME` depth recording during an active CME session and preserve the resulting `.depth` file.
2. Approve any live-code telemetry only if we move from research spec to implementation. Pending-limit telemetry, close-side slippage, token logging, and K55-shadow hooks touch live code paths even if fail-open.
3. If choosing paid data work, prefer narrow pre-declared windows, not broad pulls.

## Stop Conditions

Stop and re-scope if any of these happen:

1. A task requires changing live decision logic, prompt behavior, risk settings, or execution behavior without explicit approval.
2. A proposed result depends on same-dataset selected thresholds but is being framed as validation.
3. An orderflow hypothesis mixes synthetic/path labels with actual broker R.
4. A V3 replay starts before V2b has resolved pairs or before risk-bank tests exist.
5. A K54 architecture iteration restarts on the same current cohort without a new cohort/data-quality trigger.

## Bottom Line

The right next program shape is parallel but disciplined:

1. V2b forward validation and V2 confluence forensics.
2. Sierra/Databento parity and NAS100 orderflow forward collection.
3. Pending-limit/execution telemetry specs.
4. Methodology infrastructure.
5. Only then V3 replay and higher-risk architecture comparisons.

Everything remains `NO_PROMOTION_VERDICT` until unseen, pre-registered evidence clears the methodology gates.
