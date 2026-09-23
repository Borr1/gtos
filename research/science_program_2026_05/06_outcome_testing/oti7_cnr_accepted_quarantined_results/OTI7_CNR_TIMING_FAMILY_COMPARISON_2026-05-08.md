# OTI7 CNR Timing Family Comparison - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

| family | rows | countable | status counts | mean R | total R |
| --- | --- | --- | --- | --- | --- |
| CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1 | 51 | 27 | {'SCORED_STOP_FIRST': 32, 'SCORED_TARGET_FIRST': 6, 'UNSCOREABLE_MISSING_SOURCE_GEOMETRY': 4, 'UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY': 9} | -0.829271 | -31.512311 |
| CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1 | 51 | 27 | {'SCORED_STOP_FIRST': 32, 'SCORED_TARGET_FIRST': 6, 'UNSCOREABLE_MISSING_SOURCE_GEOMETRY': 4, 'UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY': 9} | -0.829271 | -31.512311 |

In the accepted G12 CNR rows, E0 and E1 share the same as-of executable quote timestamps. Their row-level counts therefore match exactly in this first quarantined audit; this is a packet-field limitation, not validation evidence that the timing families are equivalent.
