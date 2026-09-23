# Missed-Fill Entry Geometry Study - 2026-05-12

**Schema:** `missed_fill_opportunity_study_v1`
**Generated:** `2026-05-12T04:40:42.592930+00:00`
**Status:** `MISSED_FILL_STUDY_REGISTERED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Preregistration

- Primary question: When the live system identifies a candidate, how often does price reach the original TP1 area before touching the original limit entry?
- Primary metric: `countable_missed_fill_to_tp_area / countable_primary_opportunities`
- Inclusion rule: Use candidates with latest live_candidate_opportunity_clusters rows. Primary denominator is COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY only; duplicates and active same-symbol overlaps remain raw evidence.
- Miss definition: `candidate_path_follow.path_label == continued_without_entry_touch_to_tp_area or candidate_ltf_path_order.terminal_outcome_status == NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH`
- Claim boundary: This study does not prove market-entry profitability or changed live entry rules. Shifted-entry statistics are range-touch diagnostics only unless a separate tick-order and cost/slippage study is run.

## Current Evidence

- Raw candidates with latest cluster: `202`
- Countable primary opportunities: `24`
- Countable missed-fill-to-TP-area: `7`
- Countable missed-fill rate: `0.291667`
- Countable missed with computable inside-R: `7`
- Countable misses requiring >1R inside to touch: `4`
- Countable misses where TP1 area first touched on decision candle: `5`

## Breakdowns

- By symbol: `{'GBPJPY': {'countable_total': 2, 'countable_missed_fill_to_tp_area': 0, 'countable_missed_fill_rate': 0.0}, 'GBPUSD': {'countable_total': 5, 'countable_missed_fill_to_tp_area': 0, 'countable_missed_fill_rate': 0.0}, 'NAS100': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 0.333333}, 'US30_cash': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 2, 'countable_missed_fill_rate': 0.666667}, 'USDJPY': {'countable_total': 2, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 0.5}, 'XAGUSD': {'countable_total': 5, 'countable_missed_fill_to_tp_area': 2, 'countable_missed_fill_rate': 0.4}, 'XAUUSD': {'countable_total': 4, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 0.25}}`
- By session: `{'london': {'countable_total': 15, 'countable_missed_fill_to_tp_area': 3, 'countable_missed_fill_rate': 0.2}, 'ny': {'countable_total': 6, 'countable_missed_fill_to_tp_area': 3, 'countable_missed_fill_rate': 0.5}, 'tokyo': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 0.333333}}`
- By final outcome: `{'LIMIT_PLACED': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 0.333333}, 'REJECTED_GATE0_5_TRADING_ENABLED': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 0, 'countable_missed_fill_rate': 0.0}, 'REJECTED_GATE1_SAFETY': {'countable_total': 3, 'countable_missed_fill_to_tp_area': 0, 'countable_missed_fill_rate': 0.0}, 'REJECTED_GATE3_CIRCUIT_BREAKER': {'countable_total': 1, 'countable_missed_fill_to_tp_area': 1, 'countable_missed_fill_rate': 1.0}, 'REJECTED_L2': {'countable_total': 14, 'countable_missed_fill_to_tp_area': 5, 'countable_missed_fill_rate': 0.357143}}`

## Shifted Entry Range-Touch Diagnostic

`{'0.25R_inside_limit': {'count': 1, 'rate_of_countable_missed_with_computable_range': 0.142857}, '0.50R_inside_limit': {'count': 2, 'rate_of_countable_missed_with_computable_range': 0.285714}, '0.75R_inside_limit': {'count': 2, 'rate_of_countable_missed_with_computable_range': 0.285714}, '1.00R_inside_limit': {'count': 3, 'rate_of_countable_missed_with_computable_range': 0.428571}}`

## Inside-R Required To Touch

`{'countable_min': 0.229102, 'countable_median': 1.12362, 'countable_max': 4.257703, 'raw_median': 1.081449}`

## Recommendation

`CONTINUE_MONITORING_UNTIL_PRIMARY_TRIGGER`

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Order calls: `0`
- Paid fetch attempted: `False`
- Paid data calls: `0`
