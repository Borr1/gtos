# LTO-005 Pending-Limit Lifecycle Audit - 2026-05-05

**Schema:** `lto005_pending_limit_lifecycle_audit_v1`
**Generated:** `2026-06-02T00:14:12.027283+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Lifecycle groups considered: `62`
- Audit rows available: `313`
- Audit rows appended this run: `0`
- Source JSONL issues: `0`
- Complete: `0`
- Complete with documented limitations: `48`
- Action required: `14`

## Final States

`{'BROKER_FILLED_AWAITING_EXIT_OR_ACCOUNT_TRUTH': 14, 'NO_FILL_CANCELLED_SL_TOO_CLOSE': 1, 'NO_FILL_CANCELLED_WRONG_SIDE': 3, 'NO_FILL_CANCELLED_SYSTEM_OR_MANUAL': 4, 'NO_FILL_STILL_PENDING': 6, 'NO_FILL_CANCELLED_TARGET_REACHED_WITHOUT_ENTRY_TOUCH': 3, 'LEGACY_PENDING_LIFECYCLE_TRUTH_UNRECOVERABLE': 31}`

## Candidate And Trade-Record Matches

- Candidate match statuses: `{'NO_SHADOW_CANDIDATE_MATCH': 14, 'MATCHED_BY_CANDIDATE_ID_OR_SYMBOL_SIDE_PRICE_GEOMETRY': 17, 'NOT_APPLICABLE': 31}`
- Trade-record match statuses: `{'NO_TRADE_RECORD_MATCH': 31, 'SOURCE_ONLY_NO_LIFECYCLE_GROUP': 31}`

## Raw Trade ID Uniqueness

- Status counts: `{'UNIQUE_IN_LIFECYCLE_LOG': 29, 'LEGACY_COLLIDES_ACROSS_SYMBOLS': 2, 'UNKNOWN_NO_LIFECYCLE_GROUP': 31}`
- Collision examples: `[{'raw_trade_id': 'lim_2026-05-04_0715', 'symbol': 'NAS100', 'collision_symbols': ['XAUUSD'], 'pending_intent_global_key': 'NAS100|lim_2026-05-04_0715|2026-05-04T07:15:25.698504+00:00|LONG|27736.8|27673.5|27831.7'}, {'raw_trade_id': 'lim_2026-05-04_0715', 'symbol': 'XAUUSD', 'collision_symbols': ['NAS100'], 'pending_intent_global_key': 'XAUUSD|lim_2026-05-04_0715|2026-05-04T07:15:27.990093+00:00|SHORT|4668.45|4680.26|4650.73'}]`

## Documented Limitation Counts

`{'CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_LIFECYCLE_GROUP': 14, 'LEGACY_JOIN_BACKFILL_ROW_SOURCE_NOT_CAPTURED_SUPERSEDED_BY_AUDIT': 28, 'ACCOUNT_TRUTH_SOURCE_BLOCKED_NO_BROKER_ACTUAL_R': 17, 'LEGACY_LIFECYCLE_ROW_CANDIDATE_ID_NOT_CAPTURED_RECOVERED_FROM_CANDIDATE': 4, 'LEGACY_LIFECYCLE_ROW_DECISION_TIME_NOT_CAPTURED_RECOVERED': 4, 'LEGACY_LIFECYCLE_ROW_SOURCE_SYMBOL_NOT_CAPTURED': 4, 'LEGACY_RAW_TRADE_ID_NOT_GLOBALLY_UNIQUE': 2, 'STALE_INTERNAL_PENDING_INTENT_NOT_PERSISTED_NO_BROKER_ORDER': 6, 'LEGACY_SOURCE_PREDATES_PENDING_LIFECYCLE_LOGGER': 31, 'PENDING_LIFECYCLE_GROUP_UNRECOVERABLE_PRE_LOGGER': 31, 'SOURCE_SYMBOL_NOT_CAPTURED': 31, 'TRADE_RECORD_EXECUTION_FIELD_NULL_NO_BROKER_FILL_CLAIM': 31, 'TRADE_RECORD_PENDING_LIFECYCLE_FIELD_NOT_EMBEDDED': 31}`

## Action Required Counts

`{'LIFECYCLE_DECISION_TIME_UNRECOVERABLE': 14}`

## Source JSONL Issues

`[]`

## Unjoinable Lifecycle Examples

`[{'raw_trade_id': 'lim_BTCUSD_2026-06-01_120031', 'symbol': 'BTCUSD', 'pending_intent_global_key': 'BTCUSD|lim_BTCUSD_2026-06-01_120031|2026-06-01T12:00:31.953328+00:00|SHORT|72474.4|72808.13535714|71473.19'}, {'raw_trade_id': 'lim_BTCUSD_2026-06-01_221513', 'symbol': 'BTCUSD', 'pending_intent_global_key': 'BTCUSD|lim_BTCUSD_2026-06-01_221513|2026-06-01T22:15:13.626168+00:00|LONG|70971.73|70660.84|71904.4'}, {'raw_trade_id': 'lim_ETHUSD_2026-06-01_120031', 'symbol': 'ETHUSD', 'pending_intent_global_key': 'ETHUSD|lim_ETHUSD_2026-06-01_120031|2026-06-01T12:00:31.636663+00:00|SHORT|1980.32|2005.32|1905.32'}, {'raw_trade_id': 'lim_ETHUSD_2026-06-01_213009', 'symbol': 'ETHUSD', 'pending_intent_global_key': 'ETHUSD|lim_ETHUSD_2026-06-01_213009|2026-06-01T21:30:09.228459+00:00|SHORT|1998.62|2023.62|1923.61'}, {'raw_trade_id': 'lim_EURJPY_2026-06-01_131526', 'symbol': 'EURJPY', 'pending_intent_global_key': 'EURJPY|lim_EURJPY_2026-06-01_131526|2026-06-01T13:15:26.955530+00:00|SHORT|185.696|185.80421429|185.371'}, {'raw_trade_id': 'lim_GBPJPY_2026-06-01_164510', 'symbol': 'GBPJPY', 'pending_intent_global_key': 'GBPJPY|lim_GBPJPY_2026-06-01_164510|2026-06-01T16:45:10.633322+00:00|SHORT|214.721|214.895|214.198'}, {'raw_trade_id': 'lim_NAS100_2026-06-01_131516', 'symbol': 'NAS100', 'pending_intent_global_key': 'NAS100|lim_NAS100_2026-06-01_131516|2026-06-01T13:15:16.970229+00:00|SHORT|30285.7|30404.1975|29930.2'}, {'raw_trade_id': 'lim_NAS100_2026-06-01_171515', 'symbol': 'NAS100', 'pending_intent_global_key': 'NAS100|lim_NAS100_2026-06-01_171515|2026-06-01T17:15:15.738179+00:00|SHORT|30492.4|30574.19|30247.03'}, {'raw_trade_id': 'lim_NAS100_2026-06-01_174509', 'symbol': 'NAS100', 'pending_intent_global_key': 'NAS100|lim_NAS100_2026-06-01_174509|2026-06-01T17:45:09.602405+00:00|LONG|30594.12|30495.86446429|30888.89'}, {'raw_trade_id': 'lim_UKOIL_cash_2026-06-01_131527', 'symbol': 'UKOIL_cash', 'pending_intent_global_key': 'UKOIL_cash|lim_UKOIL_cash_2026-06-01_131527|2026-06-01T13:15:27.410067+00:00|SHORT|96.806|97.506|94.705'}, {'raw_trade_id': 'lim_US30_cash_2026-06-01_131518', 'symbol': 'US30_cash', 'pending_intent_global_key': 'US30_cash|lim_US30_cash_2026-06-01_131518|2026-06-01T13:15:18.599116+00:00|SHORT|50983.37|51191.44321429|50359.15'}, {'raw_trade_id': 'lim_US30_cash_2026-06-01_184506', 'symbol': 'US30_cash', 'pending_intent_global_key': 'US30_cash|lim_US30_cash_2026-06-01_184506|2026-06-01T18:45:06.367829+00:00|SHORT|51058.46|51159.96|50753.96'}, {'raw_trade_id': 'lim_USDJPY_2026-06-01_130013', 'symbol': 'USDJPY', 'pending_intent_global_key': 'USDJPY|lim_USDJPY_2026-06-01_130013|2026-06-01T13:00:13.945880+00:00|LONG|159.489|159.404|159.745'}, {'raw_trade_id': 'lim_USOIL_cash_2026-06-01_131518', 'symbol': 'USOIL_cash', 'pending_intent_global_key': 'USOIL_cash|lim_USOIL_cash_2026-06-01_131518|2026-06-01T13:15:18.753764+00:00|SHORT|93.162|93.912|90.912'}]`

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
