# NOFILL USDJPY Sequence Event-Order Proof Packet

Promotion verdict: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

| Row | Exact timestamp rows | Predicates on one row | Decision |
| --- | --- | --- | --- |
| NOFILL-CAT-ROW-0130 | 1 | entry_touch,protective_level | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES |
| NOFILL-CAT-ROW-0143 | 1 | entry_touch,protective_level | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES |
| NOFILL-CAT-ROW-0165 | 1 | entry_touch,protective_level | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES |
| NOFILL-CAT-ROW-0178 | 1 | entry_touch,protective_level | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES |

Official/source-contract limit:

The official MT5/MQL5 source contract authorizes chronological order across MqlTick rows and millisecond time_msc. It does not expose an event sequence inside a single MqlTick snapshot when bid and ask state jointly satisfy multiple predicates.

File row order is chronological across distinct MqlTick rows, but it does not authorize ordering multiple predicates that are true inside one quote-state row.
