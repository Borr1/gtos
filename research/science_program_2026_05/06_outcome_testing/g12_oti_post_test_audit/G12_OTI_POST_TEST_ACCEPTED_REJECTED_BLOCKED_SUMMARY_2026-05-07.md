# G12 OTI Accepted Rejected Blocked Summary - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `False`
**Outcome review opened:** `False`
**Generated:** `2026-05-07T01:17:05Z`

## Decision Counts

| Decision | Count |
| --- | --- |
| ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE | 2 |

## Accepted Lanes

| Lane | Decision | Packets | Residual next exact question |
| --- | --- | --- | --- |
| OTI1 | ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE | ['OTG0-PKT-011', 'OTG0-PKT-016', 'OTG0-PKT-025', 'OTG0-PKT-029', 'OTG0-PKT-045', 'OTG0-PKT-055', 'OTG0-PKT-059', 'OTG0-PKT-071', 'OTG0-PKT-079'] | Before any covariate-conditioned claim, which packet-bound source/as-of proofs clear the OTI1 covariate source-complete blockers while keeping lifecycle_no_fill separate from synthetic_path_r and broker_actual_r? |
| OTI2 | ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE | ['OTG0-PKT-013'] | Which future frozen input packet provides leg-level reentry state, risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, and numeric estimated_remaining_cost_r for G10-EXP-RISKBANK-005 without broker actual-R or blocked-packet outcome pooling? |

## Rejected Lanes

`0`

## Blocked Lane-Level Decisions

`0`

## Blockers Inside Accepted Lanes

| Lane | Status | Detail | Evidence |
| --- | --- | --- | --- |
| OTI1 | not_result_blocking | Covariate/source-complete claims are blocked where source/as-of proof is incomplete; lifecycle result acceptance is unaffected. | research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_BLOCKER_LEDGER_2026-05-07.json |
| OTI2 | not_result_blocking_for_quarantined_discovery | Risk-bank primary metric and validation statistics are not computable until leg-level risk-bank fields and sample floor exist. | research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json |
