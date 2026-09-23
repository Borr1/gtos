# OTB2R Same-Bar Ambiguity Policy - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

Policy version: `otb2r_same_bar_ambiguity_policy_v1`

Same-bar terminal ordering is never guessed. If M1 path-order evidence flags same-minute ambiguity, the row remains flagged for later bounded replay. If only OHLC coverage exists, any intrabar terminal ordering is bounded/ambiguous rather than resolved.

Terminal order claim allowed: `False`

## Policy Counts

| Policy | Rows |
| --- | --- |
| M1_PATH_ORDER_LOG_AVAILABLE__SAME_MINUTE_AMBIGUITY_FLAGGED_NOT_GUESSED | 86 |

## State Counts

| State | Rows |
| --- | --- |
| not_flagged_or_not_applicable | 52 |
| same_m1_ambiguity_flagged | 34 |
