# OTB2 Data Recovery Manifest - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

## Local Source Projection

| Source | Exists | SHA256 prefix | Path |
| --- | --- | --- | --- |
| strategy_follow_candidates | True | f671a3d9859e396c | shadow_logs/strategy_follow_candidates.jsonl |
| candidate_ltf_path_order | True | 7baf33c9c4e30a6e | shadow_logs/candidate_ltf_path_order.jsonl |
| candidate_path_contract_audit | True | 75bd8cfab2fd8bbd | shadow_logs/candidate_path_contract_audit.jsonl |
| prefill_delivery_path | True | 2f369103c6c3f829 | shadow_logs/prefill_delivery_path.jsonl |
| news_calendar | True | 569ee7742e395740 | data/news_calendar.json |

## Recovery Counts

- Strategy candidates projected: `86`
- LTF candidate IDs projected: `86`
- Base path rows built: `86`
- Default V2 event log exists: `False`

## Result-Bearing Sources Rejected Or Context-Only

| Path | Exists | Use | Result keys detected |
| --- | --- | --- | --- |
| shadow_logs/candidate_path_follow.jsonl | True | REJECTED | hit_sl, hit_tp1, path_label |
| shadow_logs/candidate_path_contract_audit.jsonl | True | REJECTED | hit_sl, hit_tp1, path_label |
| data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl | False | NOT_AVAILABLE | NONE |
| data/external/validation/expanded_oos_full_unblocking/sierra_6b_to_gbpusd_pilot_20260504/raw_ohlc_prequential_events_20260503T205250Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_6j_to_usdjpy_pilot_20260504/raw_ohlc_prequential_events_20260503T205250Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_nq_to_nas100_pilot_20260504/raw_ohlc_prequential_events_20260503T202913Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_si_to_xagusd_pilot_20260504/raw_ohlc_prequential_events_20260503T205250Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_si_xagusd_v2_mtf_pilot_20260504/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260503T205337Z.jsonl | True | REJECTED | gross_r, mae_r, mfe_r, net_r_by_cost, outcome |
| data/external/validation/expanded_oos_full_unblocking/sierra_xauusd_scid_to_xauusd_pilot_20260504/raw_ohlc_prequential_events_20260503T204511Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_xauusd_scid_v2_mtf_pilot_20260504/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204606Z.jsonl | True | REJECTED | gross_r, mae_r, mfe_r, net_r_by_cost, outcome |
| data/external/validation/expanded_oos_full_unblocking/sierra_ym_to_us30_cash_pilot_20260504/raw_ohlc_prequential_events_20260503T204727Z.jsonl | True | REJECTED | outcome, realized_r |
| data/external/validation/expanded_oos_full_unblocking/sierra_ym_us30_cash_v2_mtf_pilot_20260504/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204759Z.jsonl | True | REJECTED | gross_r, mae_r, mfe_r, net_r_by_cost, outcome |
| research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json | True | REJECTED | NONE |
| research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_PRE_REGISTERED_VARIANTS_2026-05-03.json | True | REJECTED | NONE |
| research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json | True | REJECTED | NONE |
| research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_CASEBOOK_2026-05-03.jsonl | True | REJECTED | path_synthetic_r |
