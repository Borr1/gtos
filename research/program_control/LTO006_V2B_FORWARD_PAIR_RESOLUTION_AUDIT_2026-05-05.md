# LTO-006 V2b Forward-Pair Resolution Audit - 2026-05-05

**Schema:** `lto006_v2b_forward_pair_resolution_audit_v1`
**Generated:** `2026-06-01T21:25:08.343943+00:00`
**Status:** `OK_WITH_DOCUMENTED_V2B_LIMITATIONS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- V2b pair rows considered: `517`
- Audit rows available: `9288`
- Audit rows appended this run: `264`
- Complete: `0`
- Complete with documented limitations: `466`
- Waiting for path: `51`
- Action required: `0`

## Rolling Status

- Resolved pairs: `466`
- R-counted pairs: `188`
- Broker actual-R counted pairs: `0`
- Synthetic path-R counted pairs: `188`
- Duplicate-aware countable R pairs: `19`
- Sample-floor progress: `{'raw_resolved_pairs': '466/30', 'raw_r_counted_pairs': '188/30', 'duplicate_aware_countable_r_pairs': '19/30'}`
- Ambiguity rate: `0.032882`
- No-leak status: `NO_DECISION_PAIR_LEAKS_DETECTED`

## Concentration

- Symbol counts: `{'NAS100': 76, 'XAUUSD': 29, 'GBPJPY': 47, 'XAGUSD': 60, 'USDJPY': 4, 'US30_cash': 40, 'GBPUSD': 57, 'JP225': 17, 'BTCUSD': 20, 'ETHUSD': 20, 'EURJPY': 18, 'AUDJPY': 8, 'CHFJPY': 21, 'UKOIL_cash': 26, 'USOIL_cash': 24, 'USDCAD': 20, 'EURGBP': 26, 'NZDUSD': 3, 'UK100': 1}`
- Session counts: `{'ny': 139, 'tokyo': 31, 'london': 159, 'moonshot_h22_23': 5, 'off_configured_session': 40, 'moonshot_h23_00': 4, 'moonshot_h00_01': 14, 'moonshot_h01_02': 8, 'moonshot_h02_03': 7, 'moonshot_h03_04': 17, 'moonshot_h04_05': 3, 'moonshot_h05_06': 7, 'moonshot_h06_07': 26, 'moonshot_h07_08': 6, 'moonshot_h08_09': 2, 'moonshot_h09_10': 4, 'moonshot_h10_11': 3, 'moonshot_h11_12': 3, 'moonshot_h12_13': 14, 'moonshot_h13_14': 2, 'moonshot_h15_16': 2, 'moonshot_h16_17': 4, 'moonshot_h17_18': 12, 'moonshot_h18_19': 3, 'moonshot_h19_20': 2}`
- Symbol/session counts: `{'NAS100|ny': 28, 'XAUUSD|ny': 9, 'GBPJPY|tokyo': 14, 'NAS100|london': 21, 'XAGUSD|london': 29, 'XAUUSD|london': 10, 'XAGUSD|ny': 31, 'USDJPY|tokyo': 1, 'GBPJPY|london': 6, 'US30_cash|london': 21, 'GBPUSD|london': 38, 'USDJPY|london': 2, 'GBPUSD|ny': 19, 'US30_cash|ny': 3, 'GBPJPY|ny': 9, 'GBPJPY|moonshot_h22_23': 1, 'JP225|moonshot_h22_23': 3, 'XAUUSD|moonshot_h22_23': 1, 'BTCUSD|off_configured_session': 20, 'NAS100|moonshot_h23_00': 2, 'ETHUSD|off_configured_session': 20, 'EURJPY|moonshot_h23_00': 1, 'GBPJPY|moonshot_h23_00': 1, 'AUDJPY|tokyo': 7, 'CHFJPY|tokyo': 4, 'EURJPY|tokyo': 1, 'JP225|tokyo': 4, 'NAS100|moonshot_h00_01': 4, 'UKOIL_cash|moonshot_h00_01': 3, 'US30_cash|moonshot_h00_01': 2, 'USOIL_cash|moonshot_h00_01': 2, 'USDCAD|moonshot_h00_01': 3, 'UKOIL_cash|moonshot_h01_02': 3, 'USOIL_cash|moonshot_h01_02': 3, 'XAUUSD|moonshot_h01_02': 1, 'NAS100|moonshot_h01_02': 1, 'NAS100|moonshot_h02_03': 2, 'US30_cash|moonshot_h02_03': 2, 'XAUUSD|moonshot_h02_03': 1, 'USDCAD|moonshot_h02_03': 2, 'NAS100|moonshot_h03_04': 4, 'XAUUSD|moonshot_h03_04': 4, 'USDCAD|moonshot_h03_04': 3, 'AUDJPY|moonshot_h03_04': 1, 'EURJPY|moonshot_h03_04': 1, 'GBPJPY|moonshot_h03_04': 2, 'JP225|moonshot_h03_04': 1, 'US30_cash|moonshot_h03_04': 1, 'UKOIL_cash|moonshot_h04_05': 1, 'USOIL_cash|moonshot_h04_05': 1, 'XAUUSD|moonshot_h04_05': 1, 'GBPJPY|moonshot_h05_06': 4, 'EURGBP|moonshot_h05_06': 1, 'EURJPY|moonshot_h05_06': 2, 'CHFJPY|moonshot_h06_07': 3, 'EURGBP|moonshot_h06_07': 4, 'EURJPY|moonshot_h06_07': 3, 'GBPJPY|moonshot_h06_07': 4, 'UKOIL_cash|moonshot_h06_07': 3, 'USDCAD|moonshot_h06_07': 2, 'USOIL_cash|moonshot_h06_07': 3, 'XAUUSD|moonshot_h06_07': 2, 'NZDUSD|moonshot_h06_07': 1, 'US30_cash|moonshot_h06_07': 1, 'CHFJPY|london': 5, 'EURGBP|london': 6, 'EURJPY|london': 3, 'JP225|london': 2, 'US30_cash|moonshot_h07_08': 3, 'NAS100|moonshot_h07_08': 3, 'USDCAD|london': 5, 'NZDUSD|london': 2, 'UKOIL_cash|london': 5, 'USOIL_cash|london': 4, 'NAS100|moonshot_h08_09': 2, 'NAS100|moonshot_h09_10': 2, 'CHFJPY|moonshot_h09_10': 2, 'CHFJPY|moonshot_h10_11': 1, 'EURJPY|moonshot_h10_11': 2, 'US30_cash|moonshot_h11_12': 2, 'NAS100|moonshot_h11_12': 1, 'CHFJPY|moonshot_h12_13': 2, 'JP225|moonshot_h12_13': 2, 'NAS100|moonshot_h12_13': 2, 'UKOIL_cash|moonshot_h12_13': 2, 'USDCAD|moonshot_h12_13': 1, 'USOIL_cash|moonshot_h12_13': 2, 'GBPJPY|moonshot_h12_13': 1, 'US30_cash|moonshot_h12_13': 1, 'USDJPY|moonshot_h12_13': 1, 'CHFJPY|ny': 4, 'EURGBP|ny': 7, 'EURJPY|ny': 5, 'JP225|ny': 5, 'UKOIL_cash|ny': 8, 'US30_cash|moonshot_h13_14': 2, 'USDCAD|ny': 3, 'USOIL_cash|ny': 8, 'EURGBP|moonshot_h15_16': 2, 'EURGBP|moonshot_h16_17': 3, 'GBPJPY|moonshot_h16_17': 1, 'EURGBP|moonshot_h17_18': 3, 'NAS100|moonshot_h17_18': 4, 'USDCAD|moonshot_h17_18': 1, 'GBPJPY|moonshot_h17_18': 2, 'UKOIL_cash|moonshot_h17_18': 1, 'USOIL_cash|moonshot_h17_18': 1, 'US30_cash|moonshot_h18_19': 2, 'GBPJPY|moonshot_h18_19': 1, 'GBPJPY|moonshot_h19_20': 1, 'UK100|moonshot_h19_20': 1}`
- Largest symbol share: `0.147002`

## Label Lanes

`{'SYNTHETIC_PATH_R': 188, 'UNRESOLVED_PATH': 329}`

## Path Outcomes

`{'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH': 80, 'ENTRY_TOUCHED_THEN_SL': 78, 'M15_PATH_AMBIGUOUS_TP1_AND_SL': 214, 'ENTRY_TOUCHED_THEN_TP1': 83, 'ENTRY_TOUCHED_UNRESOLVED': 11, 'UNKNOWN': 51}`

## Duplicate-Aware Counting

`{'COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY': 80, 'DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE': 160, 'BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP': 164, 'NO_OPPORTUNITY_CLUSTER_ROW': 113}`

## Documented Limitation Counts

`{'ACCOUNT_TRUTH_SOURCE_BLOCKED_NO_BROKER_ACTUAL_R': 366, 'FVG_COMPARATOR_EXACT_ENTRY_OR_LOCK_METADATA_SOURCE_NOT_CAPTURED': 512, 'OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA': 195, 'PAIR_R_IS_SYNTHETIC_PATH_R_NOT_BROKER_ACTUAL_R': 188, 'STRATEGY_OUTCOME_NOT_R_COUNTABLE': 461, 'V2B_DECISION_PAIR_SOURCE_HASH_NOT_CAPTURED': 517, 'V2B_DECISION_PAIR_SOURCE_SYMBOL_NOT_CAPTURED': 207, 'V2B_DECISION_PAIR_TRADE_ID_NOT_CAPTURED': 488, 'AMBIGUOUS_PATH_EXCLUDED_FROM_R': 17, 'PAIR_R_NOT_COUNTED_UNRESOLVED_PATH_OR_SOURCE_BLOCKER': 329, 'CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_V2B_PAIR': 51, 'STRATEGY_SPECIFIC_EXACT_FIELDS_SOURCE_NOT_CAPTURED': 51, 'OPPORTUNITY_CLUSTER_ROW_NOT_AVAILABLE_FOR_DUPLICATE_AWARE_COUNTING': 113, 'NO_ACCOUNT_TRUTH_ROW': 72}`

## Action Required Counts

`{}`

## Unresolved Examples

`[{'candidate_id': 'NAS100_2026-05-04T10:30:00+00:00', 'symbol': 'NAS100', 'decision_time_utc': '2026-05-04T10:30:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'USDJPY_2026-05-05T00:45:00+00:00', 'symbol': 'USDJPY', 'decision_time_utc': '2026-05-05T00:45:00+00:00', 'path_outcome_status': 'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'XAUUSD_2026-05-06T08:00:00+00:00', 'symbol': 'XAUUSD', 'decision_time_utc': '2026-05-06T08:00:00+00:00', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'US30_cash_2026-05-06T09:15:00+00:00', 'symbol': 'US30_cash', 'decision_time_utc': '2026-05-06T09:15:00+00:00', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_TP1', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'USDJPY_2026-05-07T07:15:00+00:00', 'symbol': 'USDJPY', 'decision_time_utc': '2026-05-07T07:15:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'USDJPY_2026-05-07T07:30:00+00:00', 'symbol': 'USDJPY', 'decision_time_utc': '2026-05-07T07:30:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'XAGUSD_2026-05-07T16:00:00+00:00', 'symbol': 'XAGUSD', 'decision_time_utc': '2026-05-07T16:00:00+00:00', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_TP1', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'XAGUSD_2026-05-07T16:15:00+00:00', 'symbol': 'XAGUSD', 'decision_time_utc': '2026-05-07T16:15:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'XAGUSD_2026-05-07T16:30:00+00:00', 'symbol': 'XAGUSD', 'decision_time_utc': '2026-05-07T16:30:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'XAGUSD_2026-05-07T16:45:00+00:00', 'symbol': 'XAGUSD', 'decision_time_utc': '2026-05-07T16:45:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'XAGUSD_2026-05-07T17:00:00+00:00', 'symbol': 'XAGUSD', 'decision_time_utc': '2026-05-07T17:00:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'NAS100_2026-05-08T13:15:00+00:00', 'symbol': 'NAS100', 'decision_time_utc': '2026-05-08T13:15:00+00:00', 'path_outcome_status': 'NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'GBPJPY_2026-05-11T01:15:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-11T01:15:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-11T01:45:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-11T01:45:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-11T13:30:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-11T13:30:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-11T15:15:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-11T15:15:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-12T01:15:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-12T01:15:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-12T01:45:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-12T01:45:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-12T02:30:00+00:00', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-12T02:30:00+00:00', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'AMBIGUOUS_EXCLUDED_FROM_R', 'baseline_status': 'AMBIGUOUS_EXCLUDED_FROM_R'}, {'candidate_id': 'GBPJPY_2026-05-31T22:30:00Z', 'symbol': 'GBPJPY', 'decision_time_utc': '2026-05-31T22:30:00Z', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'JP225_2026-05-31T22:30:00Z', 'symbol': 'JP225', 'decision_time_utc': '2026-05-31T22:30:00Z', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'XAUUSD_2026-05-31T22:30:00Z', 'symbol': 'XAUUSD', 'decision_time_utc': '2026-05-31T22:30:00Z', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'JP225_2026-05-31T22:45:00Z', 'symbol': 'JP225', 'decision_time_utc': '2026-05-31T22:45:00Z', 'path_outcome_status': 'M15_PATH_AMBIGUOUS_TP1_AND_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_LTF_PATH_ORDER'}, {'candidate_id': 'JP225_2026-05-31T23:00:00Z', 'symbol': 'JP225', 'decision_time_utc': '2026-05-31T23:00:00Z', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_SL', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}, {'candidate_id': 'BTCUSD_2026-05-31T23:15:00Z', 'symbol': 'BTCUSD', 'decision_time_utc': '2026-05-31T23:15:00Z', 'path_outcome_status': 'ENTRY_TOUCHED_THEN_TP1', 'ob_boundary_status': 'NOT_APPLICABLE', 'baseline_status': 'COMPUTED_FROM_CANDIDATE_PATH'}]`

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
