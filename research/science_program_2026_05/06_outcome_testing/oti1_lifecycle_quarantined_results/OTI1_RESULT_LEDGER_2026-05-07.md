# OTI1 Result Ledger - 2026-05-07

**Lane:** `OTI1`  
**Artifact type:** `result_ledger`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

## Summary

| Measure | Value |
| --- | --- |
| Allowed OTB1R packets | 9 |
| Raw rows audit-only | 62 |
| Unique duplicate groups, packet units | 54 |
| Unique duplicate groups, source IDs unpooled | 11 |
| Sanitized source projection rows | 8 |
| Source hash resolution issues | 0 |
| Broker actual-R inspected | False |
| Synthetic path-R inspected | False |

## Lifecycle Truth Counts

| Lifecycle state | Unique duplicate groups |
| --- | --- |
| still_pending | 32 |
| wrong_side | 22 |

## Fill/No-Fill Counts

| Fill/no-fill state | Unique duplicate groups |
| --- | --- |
| no_fill_cancelled_wrong_side | 22 |
| no_fill_still_pending | 32 |

## Reason Counts

| Reason | Unique duplicate groups |
| --- | --- |
| new_day | 8 |
| not_applicable | 24 |
| price_beyond_sl | 22 |

## Packet Results

| Packet | Experiment | Raw rows | Unique groups | Lifecycle counts | Fill counts | Covariate claim |
| --- | --- | --- | --- | --- | --- | --- |
| OTG0-PKT-011 | G10-EXP-PREFILL-003 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | NO_COVARIATE_CLAIM_USED |
| OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | NO_COVARIATE_CLAIM_USED |
| OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | 2 | 1 | {'still_pending': 1} | {'no_fill_still_pending': 1} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-055 | EXP-G5-NEWS-005 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | 8 | 7 | {'wrong_side': 3, 'still_pending': 4} | {'no_fill_cancelled_wrong_side': 3, 'no_fill_still_pending': 4} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |
| OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | 4 | 4 | {'still_pending': 3, 'wrong_side': 1} | {'no_fill_still_pending': 3, 'no_fill_cancelled_wrong_side': 1} | BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER |

## Statistics Status

| Statistic | Status / reason |
| --- | --- |
| Effective N | descriptive duplicate-group counts are computable, but validation effective-N is not: the same lifecycle source groups are intentionally reused across multiple experiment packets, preregistered null/alternative/sample-floor fields are absent, and covariate/source-complete claims are blocked where applicable |
| Raw p | experiment preregistry rows have null=null and alternative=null for these lifecycle packets |
| DSR | DSR requires a return or Sharpe series; OTI1 lifecycle/no-fill labels are not R returns |
| PBO | PBO requires registered variants/folds; OTI1 has one frozen descriptive lifecycle metric and no variant trials |

## Source Projection And Lifecycle Log Evidence

| Evidence | Value |
| --- | --- |
| Source projection file | research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl |
| Source projection rows | 8 |
| Source hashes resolved | True |
| Projection forbidden issues | 0 |
| Excluded source key values stored | False |

All counts are discovery/quarantine only and use unique `duplicate_group_id` units, not raw rows.
