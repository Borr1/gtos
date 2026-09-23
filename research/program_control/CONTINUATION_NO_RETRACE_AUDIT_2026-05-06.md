# Continuation/No-Retrace Shadow Audit - 2026-05-06

**Schema:** `continuation_no_retrace_audit_report_v1`
**Generated:** `2026-05-08T08:02:25.344459+00:00`
**Status:** `OK_SHADOW_ONLY_SOURCE_BLOCKED_FOR_R_SCORING`
**Strategy:** `CONTINUATION_NO_RETRACE_M15_FAIL_V1`
**Preregistration:** `continuation_no_retrace_prereg_v1`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective

Build append-only shadow rows for the preregistered continuation/no-retrace lane without changing the live retest strategy or loosening `m15_choch_exists`.

## Counts

- Eligible candidates: `66`
- Candidate rows appended: `15`
- Resolution rows: `66`
- Resolution rows appended: `17`
- Distance proxy available: `65`

## Later Path Outcomes

`{'ENTRY_TOUCHED_THEN_TP1': 5, 'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH': 27, 'ENTRY_TOUCHED_TP1_SL_M15_AMBIGUOUS': 18, 'ENTRY_TOUCHED_THEN_SL': 3, 'WAITING_FOR_PATH_ROW': 12, 'NO_FILL_NO_TP1_REACHED_YET': 1}`

## Aggregate Counting

`{'COUNTABLE_PRIMARY_ONLY': 11, 'EXCLUDED_DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 54, 'OPPORTUNITY_COUNTING_STATUS_NOT_JOINED': 1}`

## Source Blockers

`{'EXACT_DECISION_ENTRY_PRICE_NOT_CAPTURED': 66, 'ORDERED_POST_ENTRY_M1_OR_TICK_PATH_NOT_CAPTURED': 66}`

## Skipped

`{'not_eligible': 68}`

## Ambiguity Status

SHADOW_LANE_BUILT. Current rows can diagnose fast-continuation path context and duplicate-aware countability, but exact synthetic R remains source-blocked until executable decision price and ordered post-entry path data are captured.

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
