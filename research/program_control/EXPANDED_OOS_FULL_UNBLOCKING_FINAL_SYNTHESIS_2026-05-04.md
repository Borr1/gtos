# Expanded OOS Full-Unblocking Final Synthesis - 2026-05-04

**Status:** `LOCAL_FULL_UNBLOCKING_PASS_SYNTHESIZED_NOT_PROMOTABLE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

The May 4 full-unblocking pass now has adapter/converter status, a working converted-source replay path, replay or label-status artifacts for all first-wave families, candidate survival, expansion, data-quality, opened-slice, cost, and source-mismatch tables. It still produces no live-trading promotion: evidence is source-transfer/control/diagnostic, label-limited, or not computable for DSR/PBO.

## Completion Standard Audit

| Requirement | Status | Evidence | Numbers |
| --- | --- | --- | --- |
| Adapter/converter status table for every first-wave source family | MET | research/program_control/EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_2026-05-04.json | {"families_with_ohlcv_status": 11, "required_first_wave_families": 11} |
| At least one working end-to-end converted-source replay path | MET | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_PROGRESS_CHECKPOINT_2026-05-04.json | {"opened_replay_rows": 9} |
| Replay or label-status artifacts for every first-wave family | MET_AS_STATUS_ARTIFACTS_NOT_OUTCOME_REPLAYS | research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json | {"combined_replay_or_label_status_count": 11, "families": 11, "families_with_new_label_status_artifact": 5, "families_with_prior_replay_or_label_status": 6} |
| Candidate survival table by evidence class | MET_BY_THIS_SYNTHESIS | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {} |
| Instrument/source expansion scorecard | MET_BY_THIS_SYNTHESIS | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {} |
| Data-quality table | MET_BY_THIS_SYNTHESIS | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {} |
| Opened/burned/reserved slice ledger | MET_BY_THIS_SYNTHESIS | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {} |
| Cost ledger | MET | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {"new_ai_api_cost_usd": 0, "new_databento_cost_usd": 0} |
| Failure/decay/source-mismatch attribution | MET_BY_THIS_SYNTHESIS | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json | {} |
| Final synthesis with NO_PROMOTION_VERDICT | MET_BY_THIS_ARTIFACT | research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md | {"promotion_verdict": "NO_PROMOTION_VERDICT"} |

## Candidate Survival By Evidence Class

| Candidate | Evidence Class | Result Status | Decision |
| --- | --- | --- | --- |
| CAND-001-J46-J49-LIVE-BASELINE | COMPARATOR | COMPARATOR_ONLY_NO_NEW_BROKER_R | Kept as frozen comparator; no new broker-realized R labels were created. |
| CAND-002-V2-OB-BOUNDARY | SAME_MARKET_SOURCE_TRANSFER_AND_FUTURES_PROXY_TRANSFER | SOURCE_TRANSFER_DIAGNOSTIC_MIXED_NOT_PROMOTABLE | Small-n XAUUSD source-transfer diagnostic is positive, but YM/SI lower-timeframe replays produce no resolved entry labels; not validation. |
| CAND-003-V2-FVG-PATH | DISCOVERY_ONLY | NOT_OPENED_REQUIRES_COMPATIBLE_V2_EVENT_LOGS | No first-wave converted-source survival claim; requires registered V2 event-log batch. |
| CAND-004-V3-FVG-ONLY-RESCUE | DISCOVERY_ONLY | NOT_OPENED_DEPENDS_ON_V2_EVENT_LOGS_AND_LIFECYCLE_FIELDS | Prerequisite resolved V2 rows and lifecycle/pre-fill fields are absent. |
| CAND-005-NAS100-DEPTH-THINNESS | FUTURES_PROXY_TRANSFER | DEPTH_PARITY_SOURCE_STATUS_ONLY_LABEL_LIMITED | NQ/YM source parity is clean for diagnostics; labels remain insufficient for any filter. |
| CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR | SIMULATION_COMPARATOR | SIMULATION_COMPARATOR_ONLY_NO_LIVE_RISK_CHANGE | No risk/execution change allowed or made in this goal. |

## Instrument / Source Scorecard

| Family | Status | Replay/Label | Depth | Rationale |
| --- | --- | --- | --- | --- |
| NAS100/NDX100 with NQ/MNQ | PROMISING_DIAGNOSTIC | PATH_WORKS_NO_FROZEN_COHORT_MATCH | EXACT_CACHED_MBP10_MATCH_NQ | NQ depth parity exact; replay path works but no frozen cohort match. |
| US30/US30_cash with YM/MYM | NEUTRAL_DIAGNOSTIC | M15_ACTIONS_BUT_V2_MTF_ALL_NO_ENTRY | EXACT_CACHED_MBP10_MATCH_YM | YM depth parity exact, but V2 MTF replay produced all no-entry. |
| XAUUSD with XAUUSD.scid and GC/MGC | PROMISING_SMALL_N_SOURCE_TRANSFER | SMALL_N_DIAGNOSTIC_POSITIVE_NOT_PROMOTABLE | GC_NEAR_MATCH_SMALL_FIELD_DELTAS | Same-market source transfer is positive at n=5 only; GC depth is near-match, not exact. |
| XAGUSD with SI/SIL | BLOCKED_SOURCE_MISMATCH | M15_POSITIVE_BUT_PROXY_AND_MTF_NOT_PORTABLE | SI_SOURCE_OR_DEPTH_DEFINITION_BLOCKED | M15 positive did not survive MTF fill reconstruction; SI depth source-definition is blocked. |
| USDJPY with 6J | NEUTRAL_PATH_ONLY | PATH_WORKS_NO_ACTIONS | NOT_AUDITED_IN_DEPTH_BATCH | 6J inverse replay path works but produced no actions. |
| GBPUSD with 6B | NEUTRAL_PATH_ONLY_DEPTH_CAUTION | PATH_WORKS_NO_ACTIONS | SAMPLING_POLICY_ALIGNMENT_REQUIRED | 6B replay path works with no actions; depth needs sampling-policy alignment. |
| EURUSD with EURUSD/6E | BLOCKED_NO_REGISTERED_COHORT | NOT_OPENED | NOT_AUDITED_IN_DEPTH_BATCH | Converted rows exist, but no frozen raw-OHLC cohort matches this family. |
| S&P with ES/MES | BLOCKED_NO_REGISTERED_COHORT | NOT_OPENED_CONTROL_EXPANSION | NOT_AUDITED_IN_DEPTH_BATCH | Converted rows exist, but no frozen raw-OHLC cohort matches this family. |
| CL macro/liquidity proxy/control | CONTROL_ONLY | NOT_OPENED_CONTROL | NOT_AUDITED_IN_DEPTH_BATCH | Converted control rows exist, but there is no direct trade-label cohort. |
| ZN macro/rates proxy/control | CONTROL_ONLY | NOT_OPENED_CONTROL | NOT_AUDITED_IN_DEPTH_BATCH | Converted control rows exist, but there is no direct trade-label cohort. |
| VIX/VXM controls | CONTROL_ONLY | NOT_OPENED_CONTROL | NOT_AUDITED_IN_DEPTH_BATCH | Converted control rows exist, but there is no direct trade-label cohort. |

## Opened / Burned / Reserved Ledger

| Slice | Status | Rows | Actions | Resolved | Holdout Impact |
| --- | --- | --- | --- | --- | --- |
| sierra_nq_to_nas100_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 76 | 0 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_xauusd_scid_to_xauusd_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 76 | 30 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_xauusd_scid_v2_mtf_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 76 | 30 | 5 | Not eligible as future pure holdout for that source/date/question. |
| sierra_ym_to_us30_cash_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 50 | 6 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_ym_us30_cash_v2_mtf_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 50 | 6 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_6j_to_usdjpy_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 96 | 0 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_6b_to_gbpusd_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 90 | 0 | 0 | Not eligible as future pure holdout for that source/date/question. |
| sierra_si_to_xagusd_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 72 | 6 | 4 | Not eligible as future pure holdout for that source/date/question. |
| sierra_si_xagusd_v2_mtf_pilot_20260504 | OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC | 72 | 6 | 0 | Not eligible as future pure holdout for that source/date/question. |
| EURUSD with EURUSD/6E | NOT_OPENED_BY_LABEL_STATUS_AUDIT | 0 | 0 | 0 | No outcome rows opened by label-status audit. |
| S&P with ES/MES | NOT_OPENED_BY_LABEL_STATUS_AUDIT | 0 | 0 | 0 | No outcome rows opened by label-status audit. |
| CL macro/liquidity proxy/control | NOT_OPENED_BY_LABEL_STATUS_AUDIT | 0 | 0 | 0 | No outcome rows opened by label-status audit. |
| ZN macro/rates proxy/control | NOT_OPENED_BY_LABEL_STATUS_AUDIT | 0 | 0 | 0 | No outcome rows opened by label-status audit. |
| VIX/VXM controls | NOT_OPENED_BY_LABEL_STATUS_AUDIT | 0 | 0 | 0 | No outcome rows opened by label-status audit. |
| sierra_nq_to_nas100_pilot_20260504::reserved_holdout | RESERVED_NOT_OPENED_BY_PILOT | 0 | 0 | 0 | Reserved by registry and not opened by the pilot replay slice. |

## Source Mismatch Attribution

| Factor | Classification | Interpretation | Evidence |
| --- | --- | --- | --- |
| No registered raw-OHLC cohorts for EURUSD/6E and ES/MES | LABEL_SPEC_BLOCKER_NOT_DATA_MISSING | Converted rows exist, but opening outcomes would require a separate pre-registered cohort/question. | research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json |
| CL/ZN/VIX are control/context families | CROSS_INSTRUMENT_CONTROL_ONLY | These sources can support future context questions but cannot validate original-instrument edge. | research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json |
| 6B depth mismatch | SAMPLING_POLICY_ALIGNMENT_CAN_UNBLOCK | Sampling-clock alignment can likely unblock 6B source diagnostics; it is not a source rejection. | research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json |
| SI depth mismatch | SOURCE_OR_DEPTH_DEFINITION_BLOCKED | Common-second masking does not fix SI; source/continuous-contract definition must be resolved before replay use. | research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json |
| Futures proxy transfer | NOT_BROKER_TRUTH | NQ/YM exact depth parity and GC near-match can guide diagnostics, not live MT5 validation. | research/program_control/EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_2026-05-04.json |

## Promotion Readiness

Status: `NOT_READY`. Reason: No true temporal OOS resolved-pair evidence, no broker-truth validation from proxy futures/control families, and no computable DSR/PBO/effective-N promotion statistics. P-values reported: `0`. Live changes allowed: `False`.

## Remaining Research Triggers

- Pre-register any new EURUSD/ES strategy cohort before opening outcomes.
- Use CL/ZN/VIX only after a named cross-instrument question is registered.
- Add 6B common-second/declarative sampling alignment before using Sierra 6B depth diagnostics.
- Resolve SI continuous-contract/source definition before treating Sierra SI/SIL depth as equivalent.
- Continue forward shadow collection for actual broker-R and pending-limit lifecycle fields.
