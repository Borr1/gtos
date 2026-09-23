# Future Instrumentation Schema Spec - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_type": "future_instrumentation_schema_spec",
  "field_rules": {
    "estimated_remaining_cost_r": "Numeric non-negative conservative remaining cost estimate, with cost_model_version and cost components.",
    "leg_id": "Stable child-leg key, unique under setup_id; initial leg and reentry legs must be explicit child rows.",
    "open_leg_stop_if_hit_r": "Array of numeric worst-case R for every currently open leg after the proposed action.",
    "realized_closed_leg_r": "Numeric closed-leg R net of already charged completed-leg costs in this label lane.",
    "reentry_state": "Enum: not_armed, armed_pending, filled, cancelled, expired, blocked_risk_bank, blocked_ambiguity, blocked_source_missing.",
    "risk_bank_after_action_r": "Numeric invariant value after proposed action; must be >= -1.0 for admissible reentry.",
    "risk_bank_before_action_r": "Numeric invariant value before proposed action.",
    "source_hash": "Hash only sanitized as-of/input fields and policy metadata; never hash result labels into input packet rows.",
    "structural_lock_event": "Object with source row id, lock type, lock price/level, lock as-of UTC, and source hash.",
    "terminal_order_claim_status": "Enum: tick_order_observed, m1_order_observed, same_bar_ambiguous_bounded, no_terminal_order_claim."
  },
  "forbidden_primary_fields": [
    "broker_actual_r",
    "actual_r",
    "path_synthetic_r",
    "outcome_r",
    "win_loss",
    "trade_result",
    "post_entry_path_label",
    "unblocked_blocked_packet_outcome"
  ],
  "minimum_verification_gates": [
    "row source_hash recomputes 100%",
    "unique duplicate_group_id denominator reported separately from leg rows",
    "all risk_bank_after_action_r values numeric or row blocked_source_missing",
    "terminal_order_claim_status never escalates beyond source evidence",
    "validation_safe=false until separate promotion dossier",
    "outcome_review_opened=false until packet readiness audit explicitly opens a quarantined result lane"
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "purpose": "Provide packet-bound, input-only leg/reentry/risk-bank state rows so G10-EXP-RISKBANK-005 can become scoreable without broker actual-R, blocked-packet pooling, or terminal-order guessing.",
  "required_top_level_fields": [
    "packet_id",
    "experiment_id",
    "hypothesis_id",
    "setup_id",
    "leg_id",
    "leg_sequence_index",
    "parent_setup_duplicate_group_id",
    "action_asof_utc",
    "decision_asof_utc",
    "path_start_utc",
    "path_end_utc",
    "reentry_state",
    "structural_lock_event",
    "risk_bank_before_action_r",
    "risk_bank_after_action_r",
    "realized_closed_leg_r",
    "open_leg_stop_if_hit_r",
    "estimated_remaining_cost_r",
    "cost_model_version",
    "same_bar_ambiguity_policy",
    "same_bar_ambiguity_state",
    "terminal_order_claim_status",
    "tick_order_source_id",
    "duplicate_group_id",
    "source_hash",
    "sanitized_source_hash_components",
    "label_family",
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened"
  ],
  "schema_version": "riskbank_leg_ledger_v1_proposed",
  "validation_safe": false
}

```