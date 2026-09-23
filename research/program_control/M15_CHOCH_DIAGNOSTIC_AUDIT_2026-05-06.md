# M15 CHoCH Diagnostic Audit - 2026-05-06

**Schema:** `m15_choch_diagnostic_audit_report_v1`
**Generated:** `2026-05-08T08:02:23.798673+00:00`
**Status:** `OK_DIAGNOSTIC_ONLY_NO_GATE_CHANGE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective

Expand diagnostics for `m15_choch_exists` failures by joining the decision-time L2 reason to later path and opportunity evidence. This does not loosen the gate or change live execution.

## Counts

- M15 CHoCH failures considered: `73`
- Audit rows appended: `23`
- Joined to latest path: `59`
- Waiting for path: `14`

## Later Path Outcomes

`{'ENTRY_TOUCHED_THEN_TP1': 5, 'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH': 27, 'ENTRY_TOUCHED_THEN_SL': 8, 'ENTRY_TOUCHED_TP1_SL_M15_AMBIGUOUS': 18, 'WAITING_FOR_PATH_ROW': 14, 'NO_FILL_NO_TP1_REACHED_YET': 1}`

## Gate Interpretation

`{'M15_GATE_FAILED_BUT_ORIGINAL_LIMIT_PATH_REACHED_TP1_REVIEW_ONLY': 5, 'FAST_CONTINUATION_RESEARCH_DOOR_NOT_GATE_CHANGE': 27, 'M15_GATE_FAILED_AND_ORIGINAL_LIMIT_PATH_LOST': 8, 'M15_GATE_FAILED_WITH_M15_PATH_ORDER_AMBIGUOUS': 18, 'M15_GATE_FAILURE_AWAITS_PATH_EVIDENCE': 14, 'M15_GATE_FAILURE_OBSERVATIONAL_ONLY': 1}`

## Opportunity Counting

`{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 16, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 56, 'UNKNOWN': 1}`

## Ambiguity Status

DIAGNOSTICS_EXPANDED_ONLY. This audit can identify fast-continuation and original-limit path outcomes after an m15_choch_exists failure, but it does not answer promotion or gate-loosening questions.

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
