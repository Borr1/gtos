# LTO-004 Opportunity Lifecycle Audit - 2026-05-05

**Schema:** `lto004_opportunity_lifecycle_audit_v1`
**Generated:** `2026-06-02T00:03:39.091184+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Candidates considered: `540`
- Audit rows available: `8516`
- Audit rows appended this run: `279`
- Complete: `0`
- Complete with documented limitations: `404`
- Action required: `136`

## Lifecycle States

`{'NEW_COUNTABLE': 48, 'DUPLICATE_ACTIVE_SETUP': 162, 'NEW_AFTER_COOLDOWN': 62, 'REOPENED_AFTER_TERMINAL': 4, 'BLOCKED_SAME_SYMBOL_OVERLAP': 264}`

## Counting Statuses

`{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 114, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 162, 'BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP': 264}`

## Reset Policy Statuses

`{'RESET_ALLOWED_ENTRY_THEN_TERMINAL_TP_OR_SL': 361, 'NO_RESET_NO_ENTRY_TOUCH': 80, 'NO_RESET_TERMINAL_ORDER_AMBIGUOUS': 23, 'NO_RESET_ENTRY_TOUCHED_NOT_TERMINAL': 23, 'NO_RESET_NO_ELIGIBLE_TERMINAL_EVENT': 53}`

## Cluster Comparison

`{'MATCHED_COMPUTED_OPPORTUNITY_INDEX': 404, 'MISMATCH_OR_MISSING_CLUSTER': 136}`

## Documented Limitation Counts

`{'NO_EXPLICIT_EXPIRY_OR_INVALIDATION_RESET_SOURCE_IN_LIFECYCLE_V1': 540, 'COOLDOWN_WINDOW_NOT_EXPLICIT_IN_ASSIGNMENT_V1': 62, 'CANDIDATE_PATH_ROW_MISSING_BUT_LTF_ORDER_RECOVERED': 50, 'LTF_PATH_ORDER_ROW_NOT_AVAILABLE': 5}`

## Action Required Counts

`{'LIVE_CLUSTER_ROW_MISSING': 136}`

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
