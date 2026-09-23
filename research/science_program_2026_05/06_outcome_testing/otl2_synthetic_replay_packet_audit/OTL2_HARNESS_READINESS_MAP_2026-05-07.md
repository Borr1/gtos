# OTL2 Harness Readiness Map - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

## Existing Harnesses

| Harness/code path | Readiness | Useful controls | Blocking gaps |
|---|---|---|---|
| `scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py` | `PARTIAL_SCHEMA_SOURCE_BLOCKED` | Risk-bank invariant, bounded same-row fill/stop/target ambiguity, synthetic-vs-broker label separation, V3 variant spec pointer. | Default event log source is absent; output records are replay results, not frozen packet inputs; no row-level `ordered_path_source_id`, `path_start_utc`, `path_end_utc`, `source_hash`, `duplicate_group_id`, or `cost_model_version`. |
| `scripts/run_raw_ohlc_path_scaling_v2_levels.py` | `PARTIAL_POLICY_SOURCE_BLOCKED` | MTF resolution policy, same-bar policy, cost model summary, V2 structural selector behavior. | Event log directory absent; summary/results are not safe OTL2 input packets; no generic OTL2 packet writer. |
| `scripts/build_raw_ohlc_prefill_delivery_path.py` | `LIFECYCLE_PREFILL_PARTIAL_NOT_OTL2_READY` | Can reconstruct prefill coverage rows from setup close to fill/expiry using M1/M5/M15 fallback and reports lower-TF availability. | Imports historical outcome rows; default event log absent; original POI bounds unavailable; no `source_hash`; prefill rows are lifecycle/coverage artifacts, not synthetic replay packets. |
| `src/research_infra/prefill_delivery_path_audit.py` | `AUDIT_HELPER_PARTIAL` | Audits source capture, duplicate countability, no-leak status, and label boundary for prefill path rows. | G10 missing-field audit still reports source hash/source symbol/ordered path/pending-native fields missing; not a synthetic replay result harness. |
| `src/research_infra/continuation_no_retrace.py` | `DIAGNOSTIC_ONLY_BLOCKED` | Captures candidate entry models, stop/TP model, duplicate counting rule, and path context. | G10 missing-field audit says exact entry and ordered post-entry path are source-blocked for current continuation/no-retrace rows; only 2 primary countable rows reported in the G12 duplicate review. |
| G3 DC/TDA harness | `MISSING_FOR_OTL2` | Preregs and source contracts exist as research-control rows. | No OTL2 packet builder found for DC overshoot, DC threshold grid, or TDA persistence summaries with path labels and no-leak tests. |
| G4 cascade harness | `MISSING_FOR_OTL2` | Mechanism/prereg rows define sweep/cascade/generic baseline intent. | No registered source contracts for OTL2 packets 044/049; no source-valid flow/depth packet or matched-group writer. |
| G5 AMH/crowding/predatory harness | `MISSING_OR_SOURCE_BLOCKED_FOR_OTL2` | Source contracts and preregs define monitoring/crowding/stress ideas. | Google Trends/crowding extraction is not implemented; literature refs unresolved; stress proxy source missing. |
| G6 momentum/reversion harness | `MISSING_FOR_OTL2` | G6 rows define OB/generic, opening drive, exhaustion/changepoint, and gold round-number hypotheses. | No source contracts registered for these OTL2 packets; no packet builder found for comparator/round-number/changepoint synthetic replay. |
| G7 macro/fix harness | `SOURCE_ASOF_BLOCKED_FOR_OTL2` | Local G7 source docs and cached LBMA/ICE pages exist. | FRED cache not validation-ready for G7; DXY local CSV not accepted; LBMA parser/timestamp-normalization missing; no packet writer found. |

## Harness Decision

No existing harness is ready to implement OTL2 tests for the 16 synthetic packets. The closest code path is V3 risk-bank replay, but it is a discovery replay over missing/default event-log inputs and output result artifacts, not a frozen packet-input builder.

## Minimal Builder Required Before Outcomes

The next implementation lane should build a packet-input generator that writes one non-result packet file per experiment with:

- `packet_id`, `experiment_id`, `hypothesis_id`;
- `setup_id`, `symbol`, `session`, `side`, `decision_asof_utc`;
- `ordered_path_source_id`, `path_start_utc`, `path_end_utc`, `source_symbol`, `source_hash`;
- `entry_sl_tp_or_level_packet`;
- `same_bar_ambiguity_policy`;
- `cost_model_version`;
- `duplicate_group_id` and primary-countable status;
- `label_family=synthetic_path_r`;
- `broker_actual_r_absent_from_primary_metric=true`;
- `outcome_review_opened=false`;
- `promotion_verdict=NO_PROMOTION_VERDICT`.

Only after that packet-input generator passes schema/no-leak/source/as-of tests should any OTL2 result/quarantine implementation read outcome rows.
