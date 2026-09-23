# XAGUSD Fresh-OB Late-NY Status - 2026-05-06

**Schema:** `xagusd_fresh_ob_late_ny_report_v1`
**Generated:** `2026-05-08T08:02:26.295254+00:00`
**Status:** `OK_FRESH_OB_LATE_NY_TRACKED_NO_OUTCOME_CLAIM`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective

Track the May 5 XAGUSD late-NY newer-OB signature separately from the older duplicate active OB cluster, while preserving near-close unresolved status.

## Counts

- Rows built: `9`
- Rows appended: `0`

## Fresh-OB Status

`{'OLD_OB_DUPLICATE_CARRYOVER': 6, 'FRESH_OB_LATE_NY_NEW_SIGNATURE': 1, 'FRESH_OB_LATE_NY_DUPLICATE_SIGNATURE': 2}`

## Path Outcomes

`{'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH': 5, 'ENTRY_TOUCHED_TP1_SL_M15_AMBIGUOUS': 1, 'ENTRY_TOUCHED_THEN_SL': 3}`

## Near-Close Resolution

`{'NO_RETRACE_CONTINUATION_CONTEXT_NOT_FRESH_OB_SCORE': 5, 'PATH_STATUS_NOT_LATE_CLOSE_UNRESOLVED': 4}`

## Opportunity Counting

`{'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 7, 'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 2}`

## Ambiguity Status

TRACKED_ONLY. The 16:30 XAGUSD newer-OB signature is separated from the older 75.471 duplicate cluster, but entry-touched near-close rows remain unresolved and unscored.

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
