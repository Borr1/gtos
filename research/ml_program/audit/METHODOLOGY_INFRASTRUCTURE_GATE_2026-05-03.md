# Methodology Infrastructure Gate

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

- Lane 1 items addressed: `['M-7', 'M-12', 'M-13']`.
- Primary pipelines checked: `5`.
- Promotion p-values allowed: `[]`.
- M-7 status: `implemented_and_audited_current_pipelines`.
- M-12 status: `implemented_in_research_infra`.
- M-13 status: `implemented_as_hardened_claim_gate_and_audited_current_pipelines`.

## Hardened Claim Columns

- `methodology_status`
- `dsr_status`
- `pbo_status`
- `effective_n_status`
- `promotion_p_value_allowed`
- `not_computable_reason`
- `latest_artifact_path`

## Pipeline Audit

| pipeline | methodology | DSR | PBO | effective-N | promotion p-value allowed | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| K54 v2 historical modeler | fail | fail | fail | fail | False | n/a |
| K54 v3 master bundle | fail | fail | pass | fail | False | n/a |
| K54 v4 Q1.5 dispatcher::PRIMARY_Hybrid_5 | fail | pass | pass | pass | False | FAIL |
| K54 v4 Q1.5 dispatcher::FALLBACK_1_Master | fail | pass | pass | pass | False | FAIL |
| K54 v4 Q1.5 dispatcher::FALLBACK_2_Hybrid_4 | fail | pass | pass | pass | False | FAIL |
| K54 v4 Q1.5 dispatcher::arch_a_pure | fail | fail | pass | pass | False | n/a |
| Q1 DLinear baseline | fail | fail | fail | fail | False | FAIL |
| Phase 3 claim diagnostics | discovery_only | not_computable | not_computable | not_computable | False | n/a |

## Trial-Budget Example

- Example cumulative trial budget: `{'existing_program_trials': 200, 'new_trials': 16, 'cumulative_trial_count': 216, 'avg_pair_correlation': 0.5, 'effective_n': 1.9907834101382489}`.

## Ambiguity Ledger

- K54 v2 historical JSON still contains Stouffer fields; this report treats them as archived and not promotion evidence.
- A common gate cannot prevent a future hand-written markdown file from lying; queue control and tests must require hardened claim rows for new lift reports.
- Existing J46-J49/S79 validated numbers are historical references; this report is a future-claim guard and does not reopen their promotion posture.

## Next Steps

- Require new lift-claim reports to include the hardening columns emitted by src.research_infra.methodology_gate.
- Keep Phase 3 discovery reports at promotion_p_value_allowed=false until unseen/registered matrices exist.
- Use M-16 next for CPCV path bias-variance bookkeeping.

## NO_PROMOTION_VERDICT

This report is a methodology-control artifact. It does not validate, promote, or modify live trading behavior.
