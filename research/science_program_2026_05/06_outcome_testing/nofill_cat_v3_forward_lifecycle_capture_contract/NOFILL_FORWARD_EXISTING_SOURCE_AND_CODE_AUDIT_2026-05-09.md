# NOFILL Forward Existing Source And Code Audit 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

### src/components/pending_limit_lifecycle_logger.py

- status: `usable_only_after_safe_projection_allowlist`
- source_value: captures pending intent, candle/tick snapshots, checked-candle context, and asof cutoff
- contamination_risk: `['actual_r', 'synthetic_path_r', 'mt5_order_ticket', 'pending_ticket', 'order_send_attempted', 'order_send_success', 'broker_fill_state']`
- contract_rule: never consume raw rows directly; build a source-safe projection and drop every order/account/result-shaped field

### src/research_infra/pending_limit_lifecycle_audit.py

- status: `useful_for_audit_context_not_decision_features`
- source_value: joins lifecycle, candidates, paths, ltf, trade records, account truth, and persisted intents
- contamination_risk: `['account truth', 'trade record execution fields', 'actual R context']`
- contract_rule: use only to audit source coverage and missing-source blockers; do not feed result labels

### scripts/follow_live_candidate_paths.py

- status: `source_projection_candidate_with_m15_limitations`
- source_value: forward observation labels for candidate path evolution from OHLC
- contamination_risk: `['M15 cannot claim same-bar tick order', 'MT5 route must not be run by this contract lane']`
- contract_rule: future implementation may read existing artifacts, but this lane opens no MT5 route

### shadow_logs/candidate_ltf_path_order.jsonl

- status: `event-order_source_candidate_with_result_field_quarantine`
- source_value: M1 first-touch timestamps and ambiguity states
- contamination_risk: `['terminal_event_r and result-shaped fields must be excluded']`
- contract_rule: consume first-touch and ambiguity fields only, never terminal R fields

### shadow_logs/strategy_follow_candidates.jsonl

- status: `decision_context_source_candidate_after_allowlist`
- source_value: decision-time setup geometry, MSO summary, trade parameters, and no-post-outcome guard
- contamination_risk: `['final_outcome_at_log and mt5_order_ticket fields may exist downstream']`
- contract_rule: use an explicit field allowlist for geometry and decision asof fields
