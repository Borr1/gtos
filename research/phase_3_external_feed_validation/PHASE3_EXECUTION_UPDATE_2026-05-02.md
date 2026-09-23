# Phase 3 Execution Update

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Bottom Line

The current research base is valid enough to continue, but nothing in this update authorizes promotion or live-logic changes.

V2b is no longer blocked by an empty post-cutoff event log. A read-only MT5 replay produced post-cutoff V2 rows, but V2b still has zero resolved OB-boundary/J46 pairs. The precise status is `BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS`.

Orderflow is no longer blocked by Databento access for supported CME proxy windows. It remains blocked by label quality, NAS100 winner sparsity, MBP-10 depth sample size, unsupported-symbol proxy mapping, and pending-limit lifecycle telemetry.

## Path-Scaling State

### Forward Replay

Primary artifacts:

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_FORWARD_REPLAY_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.json`

Read-only MT5 export window used for forward replay:

- start: `2026-04-01T00:00:00+00:00`
- end: `2026-05-02T00:00:00+00:00`
- replay scoring window: `2026-05-01T00:00:00+00:00` through `2026-05-02T00:00:00+00:00`

V2 forward replay counters:

| Metric | Value |
|---|---:|
| rows replayed | 204 |
| TAKE rows seen | 22 |
| setup-ok rows | 0 |
| first TAKE clock | `2026-05-01T00:15:00+00:00` |
| last TAKE clock | `2026-05-01T09:30:00+00:00` |
| dominant outcome | `SETUP_NOT_REFINABLE` for all 22 TAKE rows |

V2b validation counters:

| Metric | Value |
|---|---:|
| total rows seen | 264 |
| wanted variant rows seen | 110 |
| rows after cutoff | 264 |
| wanted rows after cutoff | 110 |
| wanted resolved rows after cutoff | 0 |
| rows missing net R | 110 |
| first prospective close | `2026-05-01T00:15:00+00:00` |
| last prospective close | `2026-05-01T09:30:00+00:00` |

Interpretation:

- V2b has not failed.
- V2b is unevaluable because no resolved post-cutoff OB-boundary/J46 comparison pairs exist yet.
- The earlier shorthand "no post-cutoff rows" is now stale. The correct blocker is "no resolved post-cutoff pairs."

### Selector Forensics

Primary artifacts:

- `scripts/analyze_raw_ohlc_path_scaling_v2_selector_forensics.py`
- `tests/test_raw_ohlc_path_scaling_v2_selector_forensics.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.json`

Full event-log selector profile versus J46:

| Variant | paired n | candidate mean R | mean delta vs J46 | all major groups nonnegative | target mean delta | blocked-control mean delta |
|---|---:|---:|---:|---|---:|---:|
| `STRUCT_SWING_PROTECTED_V2` | 4394 | 0.174381 | +0.024514 | false | -0.037788 | +0.114208 |
| `STRUCT_FVG_MID_EDGE_V2` | 4394 | 0.183159 | +0.033292 | false | -0.067228 | +0.125718 |
| `STRUCT_OB_BOUNDARY_V2` | 4394 | 0.173928 | +0.024061 | true | +0.041812 | +0.012090 |
| `STRUCT_COMPOSITE_ANY_V2` | 4394 | 0.107415 | -0.042453 | false | -0.119764 | -0.032036 |

Interpretation:

- FVG has the larger headline mean delta, including the stronger 2026 slice, but its target-cohort delta is negative.
- OB-boundary is the cleaner V2b candidate because every inspected major group is nonnegative.
- This is same-event-log forensics only. It supports the V2b candidate choice but does not validate V2b.

### V3 Design Guardrail

Primary artifacts:

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_RISK_ACCOUNTING_2026-05-02.md`

Current V3 status: `DESIGN_ONLY_BLOCKED_PENDING_V2B_RESOLVED_PAIRS`

V3 invariant:

- For any original setup, aggregate worst-case loss across closed and open legs must never exceed `-1.0R` before estimated remaining costs.

Interpretation:

- V3 may be specified, but V3 outcome mining remains blocked until V2b answers whether the OB-boundary level-quality premise survives on unseen resolved pairs.

## Orderflow State

### Current Supported Candidate Fetch

Primary artifacts:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_EVENT_WINDOW_MANIFEST_CURRENT_CANDIDATES_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_CURRENT_CANDIDATES_TRADES_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_CURRENT_CANDIDATES_TRADES_EXECUTED_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_CURRENT_CANDIDATES_TRADES_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_CANDIDATE_OUTCOME_JOIN_CURRENT_CANDIDATES_TRADES_2026-05-02.md`

Fetch counters:

| Metric | Value |
|---|---:|
| supported candidate events | 58 |
| fetch groups | 13 |
| fetched groups | 12 |
| cached groups | 1 |
| executed | true |
| blocked | false |
| estimated Databento cost | $0.635717 |

Feature and join counters:

| Metric | Value |
|---|---:|
| trades feature rows | 59 |
| primary ok rows | 58 |
| joined synthetic/path targets | 22 |
| joined winners | 12 |
| joined losers | 10 |

Joined synthetic/path target availability by symbol:

| Symbol | n | wins | losses | win rate | mean synthetic R |
|---|---:|---:|---:|---:|---:|
| GBPUSD | 9 | 9 | 0 | 1.000000 | +1.500344 |
| NAS100 | 11 | 1 | 10 | 0.090909 | -0.772727 |
| XAUUSD | 2 | 2 | 0 | 1.000000 | +1.500000 |

### Actual-R Coverage

Primary artifact:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_CURRENT_CANDIDATES_TRADES_2026-05-02.md`

Coverage counters:

| Metric | Value |
|---|---:|
| orderflow candidate rows | 58 |
| synthetic/path target available | 22 |
| actual broker-R available | 1 |

Coverage by symbol:

| Symbol | rows | synthetic labels | actual R |
|---|---:|---:|---:|
| GBPUSD | 21 | 9 | 0 |
| NAS100 | 12 | 11 | 1 |
| US30 | 1 | 0 | 0 |
| XAGUSD | 14 | 0 | 0 |
| XAUUSD | 10 | 2 | 0 |

Interpretation:

- Orderflow labels must remain separated as synthetic/path, actual broker R, and fill/no-fill.
- Actual broker-R coverage is too sparse for promotion-grade scoring.

### NAS100 Readiness

Primary artifact:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_HYPOTHESIS_READINESS_AUDIT_CURRENT_CANDIDATES_TRADES_2026-05-02.md`

NAS100 counters:

| Metric | Value |
|---|---:|
| NAS100 orderflow rows | 12 |
| synthetic/path labels | 11 |
| actual broker-R labels | 1 |
| synthetic winners | 1 |
| synthetic losers | 10 |
| MBP-10 candidate rows | 11 |
| MBP-10 context rows | 32 |

Failed gates:

- `actual_r_coverage_min_20`
- `synthetic_winner_min_10`
- `mbp10_candidate_min_30`

Registration verdict:

- `DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET`

Interpretation:

- NAS100 orderflow is useful for forensics.
- NAS100 is not ready for a registered replay hypothesis because the sample is selected, sparse, winner-poor, and depth-limited.

### Forward Collection Plan

Primary artifact:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_CURRENT_CANDIDATES_TRADES_2026-05-02.md`

Current data reality:

| Metric | Value |
|---|---:|
| candidate-feature rows loaded | 518 |
| current supported candidate count | 58 |
| manifest supported candidates within available data cap | 58 |
| unsupported candidate count | 57 |
| unsupported GBPJPY candidates | 23 |
| unsupported USDJPY candidates | 34 |
| rows after manifest available-end cap | 0 |
| candidates after available-end cap | 0 |

Collection verdict:

- `COLLECT_FORWARD_DISCIPLINED_NOT_REPLAY`

Next collection actions:

1. NAS100 forward label and depth collection: trades + MBP-1 for every new supported NAS100 candidate; MBP-10 only for pre-declared candidate/comparator windows.
2. XAUUSD limit-intent telemetry: blocked by missing live pending-limit lifecycle evidence, not by Databento market data.
3. XAUUSD continuation contrast: wait for both winner and loser labels before spending broad depth credits.
4. Unsupported-symbol proxy mapping: keep GBPJPY and USDJPY blocked until proxy mapping and timestamp policy are registered.
5. MBO queue behavior: keep deferred until MBP-10 leaves an explicit queue-behavior question unanswered.

## Ambiguities Closed Or Reframed

| Ambiguity | Current answer |
|---|---|
| Did V2b fail? | No. It is unevaluable until resolved post-cutoff OB-boundary/J46 pairs exist. |
| Does "post-cutoff rows" mean more shadow logs? | Not only shadow logs. It means post-cutoff replay rows with resolved net R for both the V2b candidate and J46 comparator. Current May 1 replay produced rows, but all wanted V2b rows are missing net R. |
| Is FVG the next V2b candidate because it leads 2026? | No. FVG is a comparison arm. OB-boundary is cleaner across target/control/blocker groups. |
| Can V3 proceed now? | Design only. Outcome mining is blocked until V2b level-quality validation exists. |
| Did Databento access solve orderflow? | It solved supported-window trades access, not labels, depth sample, proxies, or pending-limit telemetry. |
| Can NAS100 orderflow be registered now? | No. Failed gates are actual-R coverage, synthetic winner count, and MBP-10 candidate count. |
| Can the XAUUSD limit row be fixed with another market-data pull? | No. The missing evidence is pending-intent lifecycle telemetry from the live system. |

## Staleness And Artifact Controls

Staleness found and corrected in this update:

- The prior V2b shorthand "no post-cutoff rows" is stale after the May 1 read-only MT5 replay. The exact current blocker is zero resolved post-cutoff V2b/J46 pairs.
- The earlier orderflow forward plan did not include the current-candidates trades fetch. The current plan now points at the executed current-candidates trades fetch and refreshed coverage/readiness artifacts.
- V2b evaluator wording previously collapsed "no prospective rows" and "prospective rows exist but no resolved pairs" into one blocked state. The evaluator now distinguishes both cases.

Controls still required:

- Do not cite raw mutable shadow logs as immutable population counts without a frozen artifact.
- Do not compare orderflow winner/loser labels without separating synthetic/path labels from actual broker R.
- Do not use post-event orderflow fields in any future as-of rule.
- Do not register thresholds on the same NAS100 cluster that motivated the hypothesis.
- Prefer timestamped artifacts over rerunning same-date reports in place.

## Immediate Plan

1. Continue V2b forward replay collection until at least one resolved prospective pair exists, then keep interim reports separate from promotion dossiers.
2. Keep OB-boundary as the registered V2b candidate and FVG as a comparator.
3. Keep V3 reentry design-only and enforce the `-1.0R` aggregate setup risk invariant before any future replay.
4. Forward-collect NAS100 trades + MBP-1 on new supported CANDIDATE rows; use MBP-10 only for pre-declared windows.
5. Add or implement pending-limit telemetry only as fail-open research observability after explicit approval for live-observability code.
6. Register proxy mapping before any paid futures pulls for unsupported symbols.
