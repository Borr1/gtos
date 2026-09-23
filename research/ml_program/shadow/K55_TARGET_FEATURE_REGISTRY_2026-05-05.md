# K55 Target And Feature Registry - 2026-05-05

**Schema:** `k55_target_feature_registry_v1`
**Generated:** `2026-06-01T23:42:40.730719+00:00`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Target version:** `k55_target_v1_account_history_realized_primary_synthetic_path_context_2026_05_05`
**Feature bundle version:** `k55_feature_bundle_v1_lto001_020_orderflow_asof_2026_05_05`
**Inference version:** `k55_shadow_inference_v1_json_linear_or_disabled`

## Target Contract

`{'primary_label': 'broker_actual_r', 'primary_label_required_evidence_class': 'ACCOUNT_HISTORY_REALIZED', 'secondary_context_label': 'synthetic_path_r', 'secondary_context_claim_boundary': 'Synthetic path labels are allowed for context, QA, and pretraining research only. They are not account-realized labels and cannot validate promotion.', 'sample_eligibility_order': ['PRIMARY_ACCOUNT_HISTORY_REALIZED_R_LABEL', 'SYNTHETIC_PATH_CONTEXT_ONLY', 'UNLABELED_FORWARD_CANDIDATE']}`

## Feature Bundle Contract

`{'allowed_feature_timing': 'decision_time_or_asof_only', 'excluded_from_feature_vector': ['broker_actual_r', 'actual_r', 'path_label', 'hit_tp1', 'hit_sl', 'pnl', 'profit', 'realized_r'], 'feature_groups': ['candidate_context', 'mso_context', 'decision_diagnostics_asof', 'mechanical_asof_context', 'regime_decay_asof', 'orderflow_source_asof', 'risk_policy_context']}`

## Model Artifact Policy

`{'default_status': 'MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED', 'accepted_artifact_schema': 'k55_shadow_linear_json_model_v1', 'minimum_checks': ['target_version_matches', 'feature_bundle_version_matches', 'weights_are_numeric', 'threshold_is_numeric', 'feature_keys_pass_no_leak_filter'], 'stale_k54_policy': 'Do not wire stale K54 v3/v4 artifacts directly. K54 v3/v4 failed global gates and their offline feature catalog is not replicated in live MSO. They remain audit context.'}`

## Boundary

K55 shadow rows are research-only and read-only. They cannot change AI prompts, safety gates, risk, execution, order placement, or live promotion without a separate promotion dossier.
