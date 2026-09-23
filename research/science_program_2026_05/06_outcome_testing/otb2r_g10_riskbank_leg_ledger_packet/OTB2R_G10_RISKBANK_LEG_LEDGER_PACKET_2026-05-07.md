# OTB2R G10 Risk-Bank Leg-Ledger Packet - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`

Scope: research/tooling only; input-only proof-or-impossibility packet.

Safety flags: `validation_safe=false`; `outcome_review_opened=false`; `outcome_scoring_run=false`; `broker_actual_r_inspected=false`; `blocked_otb2r_packet_outcomes_inspected=false`.

## Verdict

The packet can carry forward 86 source-hashed, duplicate-unique, coverage-bound G10 rows with decision/path windows, cost model, same-bar policy, and source-hash lineage. It cannot populate the required leg-level risk-bank ledger fields from current local input-only sources. The correct result is `IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS` for those fields, not an imputation.

## Evidence Chain

| Stage | Status | Summary |
| --- | --- | --- |
| prereg_and_mechanism | RISK_BANK_REQUIREMENTS_DEFINED_OUTCOMES_CLOSED | G10-EXP-RISKBANK-005 is frozen as synthetic_path_r research only; rows without leg-level risk-bank ledger are excluded and outcome_review_opened=false. |
| otg0_packet_control | SYNTHETIC_REPLAY_EXISTING_DATA_AUDIT_CLASS | OTG0 required setup, as-of/path windows, same-bar policy, cost model, duplicate group, label separation, and broker_actual_r_absent=true before synthetic path review. |
| otb2_original_packet | READY_BUT_LATER_REJECTED_BY_G12 | Initial OTB2 built a G10 input packet, but G12 rejected invalid clearing because raw path source/hash and coverage blockers remained. |
| otb2r_rebuild | PACKET_READY_FOR_G12_REAUDIT | OTB2R rebuilt 86 rows from sanitized projections with 86/86 source-hash and coverage-valid rows, 86 unique duplicate groups, and terminal-order guessing disabled. |
| g12_otb_reaudit | ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT | G12 accepted only OTG0-PKT-013 from OTB2R; the other OTB2R packets stayed blocked. |
| oti2_quarantined_result | RESULT_QUARANTINED_DISCOVERY_ONLY_PRIMARY_RISKBANK_NOT_COMPUTABLE | OTI2 confirmed the accepted packet hashes/coverage, but the risk-bank primary metric remained not_computable because leg/reentry/risk-bank fields were absent. |
| g12_oti_post_test_audit | ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE_WITH_RESIDUAL_EXACT_QUESTION | G12 accepted OTI2 only as quarantined discovery evidence and asked for a future frozen packet with leg-level reentry/risk-bank/cost fields. |
| g0_next_lane | OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET_RANK_1 | G0 routed the central blocker to this input-only proof/impossibility packet, with no outcome scoring and no promotion flags. |

## Field Coverage Matrix

| Field | Coverage | Populated | Total |
| --- | --- | --- | --- |
| leg_id | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| reentry_state | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| structural_lock_event | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| risk_bank_before_action_r | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| risk_bank_after_action_r | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| realized_closed_leg_r | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| open_leg_stop_if_hit_r | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| estimated_remaining_cost_r | IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS | 0 | 86 |
| cost_model_version | POPULATED_INPUT_ONLY | 86 | 86 |
| duplicate_group_id | POPULATED_INPUT_ONLY | 86 | 86 |
| source_hash | POPULATED_INPUT_ONLY | 86 | 86 |
| decision_asof_utc | POPULATED_INPUT_ONLY | 86 | 86 |
| path_start_utc | POPULATED_INPUT_ONLY | 86 | 86 |
| path_end_utc | POPULATED_INPUT_ONLY | 86 | 86 |
| same_bar_ambiguity_policy | POPULATED_INPUT_ONLY | 86 | 86 |
| same_bar_ambiguity_state | POPULATED_INPUT_ONLY | 86 | 86 |
| terminal_order_tick_order_evidence | INPUT_ONLY_POLICY_EVIDENCE_ONLY_NO_TERMINAL_ORDER_CLAIM | 86 | 86 |
| same_bar_policy_inputs | POPULATED_INPUT_ONLY | 86 | 86 |

## Row Summary

| Metric | Value |
| --- | --- |
| records | 86 |
| unique duplicate_group_id | 86 |
| source_hash failures | 0 |
| same_m1_ambiguity_flagged | 34 |
| terminal_order_claim_allowed | False |

## Negative Evidence

Search saturation found strict leg/risk-bank field names in specs, tests, blockers, or `SOURCE_NOT_CAPTURED` markers, but not as packet-bound input values for `OTG0-PKT-013`. See the negative-evidence saturation ledger for scope-by-scope command evidence.

## Future Required Source

A future `riskbank_leg_ledger_v1` source/logger must emit leg_id, reentry state, structural lock, before/after risk-bank values, closed/open leg R, numeric remaining costs, duplicate group, source hash, and same-bar/tick-order policy inputs before a G10 risk-bank score can be computed.