# Expanded OOS Final Synthesis (2026-05-03)

**Promotion verdict:** `NO_PROMOTION_VERDICT`

Expanded OOS work completed as a non-promotional research control pass. The data/source map and frozen registry are complete; same-instrument temporal OOS is blocked by zero resolved prospective pairs; source/proxy transfer is diagnostic only; cross-instrument work is data-quality/replay-feasibility only.

## Completion Ledger
| Item | Name | Status | Terminal State | Evidence |
| --- | --- | --- | --- | --- |
| P0 | Data-source map | ANSWERED_WITH_EVIDENCE | source inventory complete; no expanded outcome slices opened by P0 | research\program_control\EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.json |
| P1 | Frozen candidate registry | ANSWERED_WITH_EVIDENCE | 6 candidates/comparators frozen; post-open tuning disallowed | research\program_control\EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.json |
| P2 | Replay portability audit | ANSWERED_WITH_EVIDENCE | 8 tools audited; first batch should use MT5 OHLCV roots before Sierra conversion | research\program_control\EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_2026-05-03.json |
| P3 | Same-instrument temporal/prospective OOS | BLOCKED_WITH_REASON | post-cutoff rows exist, but resolved V2b OB-boundary/J46 pairs equal zero | research\program_control\EXPANDED_OOS_P3_TEMPORAL_V2B_STATUS_2026-05-03.json |
| P4 | Regime-transfer validation | DISCOVERY_ONLY_DEFERRED_WITH_TRIGGER | regime metadata exists in discovery logs; no fresh regime OOS replay opened | research\phase_3_external_feed_validation\RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json |
| P5 | Source/proxy transfer and orderflow | DISCOVERY_ONLY_BLOCKED_WITH_REASON | NAS100 depth clue is label-limited and leave-one-date fragile; Sierra parity extractor missing | research\program_control\EXPANDED_OOS_P5_NAS100_ORDERFLOW_SOURCE_TRANSFER_2026-05-03.json |
| P6 | Cross-instrument expansion | ANSWERED_WITH_EVIDENCE_FOR_DATA_QUALITY_ONLY | first-wave source coverage mapped; transfer claims remain non-validation | research\program_control\EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.json |
| P7 | Failure/decay attribution | ANSWERED_WITH_EVIDENCE | current blockers are source/label/replay/pair-resolution issues, not proven edge decay | research\program_control\EXPANDED_OOS_FINAL_SYNTHESIS_2026-05-03.md |
| P8 | Final synthesis and ledgers | ANSWERED_WITH_EVIDENCE | completion ledger, evidence-class table, blocker ledger, and promotion-readiness record written | research\program_control\EXPANDED_OOS_FINAL_SYNTHESIS_2026-05-03.md |

## Evidence Classes
| Class | Status | Key Numbers | Boundary |
| --- | --- | --- | --- |
| TRUE_TEMPORAL_OOS | BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS | rows_after_cutoff=264; wanted_rows_after_cutoff=110; wanted_resolved_rows_after_cutoff=0; lower_tf_start_violations=0 | not computable as validation because resolved prospective pairs are zero |
| FORWARD_SHADOW | DEFERRED_WITH_TRIGGER | post_cutoff_rows=264; resolved_pairs=0 | new rows exist, but outcome-resolved candidate/baseline pairs do not |
| FUTURES_PROXY_TRANSFER | DIAGNOSTIC_ONLY_LABEL_LIMITED | MBO_TOP20 depth_delta=-33.5 flips=1 actual_r_n=1 synthetic_n=11; MBP10_TOP10 depth_delta=-20 flips=1 actual_r_n=1 synthetic_n=11 | mechanism/orderflow proxy only; not MT5 broker-R validation |
| SAME_MARKET_SOURCE_TRANSFER | SOURCE_READY_CONVERTER_REQUIRED | sierra_scid_files=33; first_wave_relevant_scid=26; missing_first_wave_scid=[] | Sierra .scid is inventoried, but no registered GTOS OHLCV converter/parity adapter opened outcomes |
| CROSS_INSTRUMENT_TRANSFER | DATA_QUALITY_AND_REPLAY_FEASIBILITY_ONLY | instrument_families=11; sierra_depth_files=465; sierra_depth_total_gb=59.701 | screening/discovery only; never validation of the original instrument |
| REGIME_TRANSFER | DISCOVERY_ONLY_DEFERRED_WITH_TRIGGER | full_resolved_n=4394; year_2026_n=474 | existing V2 event logs include regime metadata, but no expanded OOS regime replay was opened |
| DISCOVERY_ONLY | ANSWERED_WITH_EVIDENCE_NOT_PROMOTIONAL | v2_full_n=4394; v2_2026_n=474; fvg_minus_ob_mean=0.009231; v3_status=NO_PROMOTION_VERDICT | used for blocker attribution and next-batch design only |

## Candidate Survival
| Candidate | Status | Decision |
| --- | --- | --- |
| CAND-001-J46-J49-LIVE-BASELINE | BASELINE_COMPARATOR_ONLY | kept as comparator; no new validation claim |
| CAND-002-V2-OB-BOUNDARY | BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS | blocked; not failed, not validated |
| CAND-003-V2-FVG-PATH | DISCOVERY_ONLY_NOT_TEMPORAL_OOS | requires registered V2 event batch before scoring |
| CAND-004-V3-FVG-ONLY-RESCUE | DISCOVERY_ONLY_DEPENDS_ON_V2_EVENT_LOGS | not run on expanded OOS because prerequisite resolved V2 rows are absent |
| CAND-005-NAS100-DEPTH-THINNESS | DIAGNOSTIC_ONLY_LABEL_LIMITED | diagnostic only; no live filter |
| CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR | SIMULATION_COMPARATOR_ONLY | no live/risk change in this goal |

## Instrument Expansion
| Family | Status | MT5 | Sierra .scid | Depth | Boundary |
| --- | --- | --- | --- | --- | --- |
| NASDAQ index / NQ | SOURCE_READY_REPLAY_PARTIAL | NAS100, NDX100 | NQM26-CME, MNQM26-CME | NQM26-CME, MNQM26-CME | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Dow / YM | SOURCE_READY_REPLAY_PARTIAL | US30, US30_cash | YMM26-CBOT, MYMM26-CBOT | YMM26-CBOT, MYMM26-CBOT | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Gold / GC | SOURCE_READY_REPLAY_PARTIAL | XAUUSD | XAUUSD, GCM26-COMEX, MGCM26-COMEX | GCM26-COMEX, MGCM26-COMEX | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Silver / SI | SOURCE_READY_WITH_SPARSE_SCID_WARNING | XAGUSD | SIM26-COMEX, SILM26-COMEX | SIM26-COMEX, SILM26-COMEX | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| JPY / 6J | SOURCE_READY_REPLAY_PARTIAL | USDJPY | 6JM26-CME | 6JM26-CME | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| GBP / 6B | SOURCE_READY_REPLAY_PARTIAL | GBPUSD | 6BM26-CME | 6BM26-CME | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| EUR / 6E | SOURCE_READY_REPLAY_PARTIAL | EURUSD | EURUSD, 6EM26-CME | 6EM26-CME | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| S&P / ES | SOURCE_READY_REPLAY_PARTIAL | SPX500 | ESM26-CME, MESM26-CME | ESM26-CME, MESM26-CME | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Crude / CL | SOURCE_READY_REPLAY_PARTIAL | UKOUSD | CLM26-NYMEX | CLM26-NYMEX | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Treasury / ZN | SOURCE_READY_CONVERTER_REQUIRED | - | ZNM26-CBOT | ZNM26-CBOT | data/replay feasibility only; cross-instrument/source transfer is not live validation |
| Volatility controls / VIX | SOURCE_READY_WITH_SPARSE_SCID_WARNING | - | VXM26-CFE, VXMM26-CFE | - | data/replay feasibility only; cross-instrument/source transfer is not live validation |

## Data Quality And Costs
- MT5: 9 manifests, 44 symbol/timeframe aggregates, 22 live symbol specs.
- Sierra: 33 .scid files, 26 first-wave relevant .scid, 465 depth files, 59.701 GB depth.
- Databento: 128 cached files reused; no new paid pull.
- AI/API: no model calls and no Component 3B.

| Source | Cost | Note |
| --- | --- | --- |
| MT5 local read-only exports/spec probes | $0 incremental | 9 manifests; 22 live symbol specs; no AI/API call. |
| Sierra Package 12 local files | $0 incremental in this run | 33 .scid files and 465 depth files (59.701 GB depth) inventoried locally. |
| Databento | $0 new pull in this run | 128 cached files reused; broad paid pulls remain approval-gated. |
| AI/API | $0 | No Component 3B, prompt replay, or paid model evaluation used. |

## Opened, Burned, Reserved Slices
| Slice | Status | Holdout Impact |
| --- | --- | --- |
| P0/P1 registry phase | NO_OUTCOME_SLICES_OPENED | none |
| P3 V2b post-cutoff status artifact | REOPENED_EXISTING_EVENT_LOG_FOR_STATUS_NOT_FRESH_HOLDOUT | not eligible as future pure holdout because it has already been inspected |
| P5 cached NAS100 orderflow diagnostics | REOPENED_CACHED_DIAGNOSTIC_ARTIFACTS | diagnostic/proxy only; not fresh broker-R validation |
| Sierra first-wave .scid/.depth outcome replay | NOT_OPENED | reserved until converter/parity adapter and date slices are pre-registered |
| Reserved holdout | RESERVED_NOT_OPENED | available after exact future source/date rules are registered |

## Blockers And Triggers
| Blocker | Trigger | Evidence |
| --- | --- | --- |
| No resolved prospective V2b OB-boundary/J46 pairs. | Post-cutoff event log with resolved OB-boundary/J46 pairs meeting sample floors. | research\program_control\EXPANDED_OOS_P3_TEMPORAL_V2B_STATUS_2026-05-03.json |
| Sierra .scid/.depth is inventoried but not yet converted into GTOS-compatible replay roots or parity orderflow features. | Registered .scid-to-GTOS OHLCV converter and one-window Sierra/Databento depth parity extractor. | research\program_control\EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_2026-05-03.json |
| NAS100 orderflow has sparse actual broker-R and leave-one-date sign flips. | Actual broker-R coverage >=20 with winner/loser balance, or registered synthetic-label sample floor with leave-one-date stability. | research\program_control\EXPANDED_OOS_P5_NAS100_ORDERFLOW_SOURCE_TRANSFER_2026-05-03.json |
| Cross-instrument transfer cannot validate original-instrument edge. | Use only as hypothesis screening, then register a same-instrument/source temporal OOS slice. | research\program_control\EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.json |
| Execution lifecycle labels are missing for pending-limit fill/no-fill and POI path questions. | Approved pending-limit lifecycle telemetry with fill, expiry, cancellation, and broker-R separation. | research\program_control\EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_2026-05-03.json |
| Bulk Sierra .scid to GTOS OHLCV data-root conversion is not implemented in this audit. | Add a bulk converter only after the first registered Sierra replay batch names symbol/date/timeframe slices. | SRC-SIERRA-SCID |
| Arbitrary new symbols require replay-spec/cohort/config support and GTOS-compatible OHLCV file naming. It cannot consume Sierra .scid or depth files directly. | For first batch, use existing MT5 CSV roots; defer Sierra replay until CSV conversion is registered. | REPLAY-V2-STRUCTURAL |
| Requires a compatible V2 structural event log generated first. | Run only after a registered V2 event log exists for a new batch. | ANALYZE-V2-CONFLUENCE |
| Needs resolved post-cutoff OB-boundary/J46 pairs; current goal must not call unresolved or same-slice rows validation. | For every new batch, write opened/burned slice metadata and cutoff before evaluating. | EVAL-V2B-PROSPECTIVE |
| Original POI bounds and true broker lifecycle states are still absent. | Use as coverage support only; do not score delivery-leg logic without lifecycle telemetry. | PREFILL-PATH-COVERAGE |
| Depends on V2 structural lock metadata; no direct arbitrary-symbol runner without V2 event generation first. | After V2 batch generation, run only frozen V3_FVG_ONLY_RESCUE first; keep other V3 variants diagnostic. | REPLAY-V3-RISK-BANK |
| Not portable to Sierra depth files or other symbols until a Sierra/Databento parity feature extractor exists. | Build Sierra depth parity extractor for one registered NQ/MNQ window before broad first-wave depth claims. | ORDERFLOW-NAS100-CACHED |

## Failure/Decay Attribution
- **Is V2b OB-boundary disproved by the prospective check?** No. The available post-cutoff rows have zero resolved OB-boundary/J46 pairs, so the result is blocked rather than a negative expectancy result.
- **Is NAS100 depth/thinness ready as a filter?** No. Depth is the strongest cached clue, but actual-R labels are sparse and the total-depth sign flips under leave-one-date removal.
- **Did Sierra first-wave data validate or refute any strategy?** No. The files are source-ready, but outcome replay was intentionally not opened without a registered conversion/parity adapter.
- **What is the current decay attribution?** Current evidence points to label availability, source parity, replay portability, and unresolved pair scarcity as blockers; it does not establish edge decay.

## Rejected Ideas
| Route | Status | Reason |
| --- | --- | --- |
| Composite structural selector as broad policy | EXCLUDED_EXCEPT_NEGATIVE_CONTROL | prior confluence deep dive classifies broad Composite as overlock/global underperformer |
| K54 v3/v4 same-cohort architecture iteration | EXCLUDED | current cohort architecture iteration is closed without new source-balanced labels |
| Portfolio-wide vol scaling | EXCLUDED | already failed Lane 6 tail triage |
| V3 OB-lock and FVG-then-OB underperforming variants | EXCLUDED_EXCEPT_DIAGNOSTIC_CONTEXT | not first-line expanded OOS strategy candidates in current owner prompt |
| Component 3B debate | PARKED | owner parked due to extra AI/API cost |
| Prompt cascade rebuild, Reflexion/adaptive loop, live AI behavior changes | EXCLUDED_APPROVAL_REQUIRED | behavior/API-cost changes require explicit separate approval |
| broad Sierra depth replay without parity extractor | DO_NOT_START | first-batch portability audit rejection |
| cross-instrument transfer framed as validation | DO_NOT_START | first-batch portability audit rejection |
| V3 directly on Sierra/depth without V2 event logs | DO_NOT_START | first-batch portability audit rejection |
| Component 3B or AI replay | DO_NOT_START | first-batch portability audit rejection |

## Promotion Readiness
Status: `NOT_READY`. Reason: No true temporal OOS resolved-pair evidence and no source/proxy parity evidence met validation standards. P-values reported: 0. Live changes allowed: False.
