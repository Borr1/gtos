# Phase 3 Methodology Diagnostics

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

- Claims checked: `5`.
- Promotion p-values allowed: `[]`.
- Promotion p-values forbidden: `['path_v2_structural_selector', 'path_v2b_rolling_status', 'path_v3_risk_bank_replay', 'nas100_cached_orderflow_forensics', 'proxy_mapping_weekend_forensics']`.
- Missing artifacts: `[]`.
- Bad/missing promotion verdicts: `[]`.

## Claim Diagnostics

| claim | class | artifact | verdict ok | DSR | PBO | effective-N | guard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| path_v2_structural_selector | same_dataset_discovery | True | True | not_computable | not_computable | proxy_required | DO_NOT_REPORT_PROMOTION_P_VALUES |
| path_v2b_rolling_status | prospective_blocked_no_resolved_pairs | True | True | not_computable | not_computable | not_computable | DO_NOT_REPORT_PROMOTION_P_VALUES |
| path_v3_risk_bank_replay | same_dataset_discovery_variants | True | True | not_computable | not_computable | proxy_required | DO_NOT_REPORT_PROMOTION_P_VALUES |
| nas100_cached_orderflow_forensics | label_limited_orderflow_diagnostic | True | True | not_computable | not_computable | not_computable | DO_NOT_REPORT_PROMOTION_P_VALUES |
| proxy_mapping_weekend_forensics | price_transfer_not_alpha | True | True | not_applicable | not_applicable | not_applicable | DO_NOT_REPORT_PROMOTION_P_VALUES |

## Ledger Hardening

- Stale ledger status: `STALE_MARKERS_FOUND`.
- Stale hits: `[{'marker': 'V2b has no post-cutoff prospective rows', 'replacement': 'V2b has post-cutoff rows but no resolved post-cutoff OB-boundary/J46 pairs'}, {'marker': 'validation_status=BLOCKED_NO_PROSPECTIVE_ROWS', 'replacement': 'validation_status=BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS'}]`.

Recommended columns:

- methodology_status
- dsr_status
- pbo_status
- effective_n_status
- promotion_p_value_allowed
- not_computable_reason
- latest_artifact_path

Misuse guards:

- Discovery-only claims must say not_computable instead of showing raw p-values.
- Blocked prospective claims must report the blocker state before any statistic.
- Transfer-quality proxy claims must not be mixed with alpha/return claims.
- Label-limited orderflow diagnostics must separate actual broker R from synthetic/path labels.

## DSR Reference

- Rows: `15`.
- Verdict counts: `{'BORDERLINE': 1, 'FAILS': 9, 'SURVIVES': 5}`.
- Note: Reference only; do not transplant ML-program DSR rows onto Phase 3 discovery claims.

## Non-Claims

- This harness does not validate or promote Phase 3 claims.
- `not_computable` is an explicit result, not a failure of the tool.
- Existing DSR rows are reference material only unless the claim shares the same registered trial design.
