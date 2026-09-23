# OTI1 Completion Audit - 2026-05-07

**Lane:** `OTI1`  
**Artifact type:** `completion_audit`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

## Objective Restated

Run OTI1 quarantined lifecycle/no-fill outcome testing on only the 9 G12-accepted OTB1R lifecycle packets, with metric freeze before label inspection, duplicate_group_id denominators, label-family separation, covariate blockers, descriptive quarantine results, exact not-computable statistics, scoped artifacts, and no promotion/live changes.

## Completion Status

| Check | Value |
| --- | --- |
| Can mark OTI1 complete | True |

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Complete GTOS preflight | generate_live_state.py ran and mandatory context/control docs were read before OTI1 edits | DONE |
| Freeze metric before packet label inspection | research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json | DONE |
| Use only 9 accepted OTB1R lifecycle packets | 9 accepted OTB1R packets loaded; OTG0-PKT-017 excluded | DONE |
| Use unique duplicate_group_id counts | 54 packet-level unique groups; 62 raw rows audit-only | DONE |
| Do not inspect broker actual-R/synthetic path-R/win-loss R | builder reads only primary_lifecycle_rows and top-level sanitized projection hash evidence, then scans row keys for forbidden fields | DONE |
| Exhaust source projections and hash ledgers | 8 sanitized projection rows; source_hash_resolution_issues=0 | DONE |
| Exhaust cited lifecycle logs as evidence without using R values | hashed and line-counted 3 local lifecycle logs | DONE |
| Separate lifecycle truth from covariate/source-complete claims | result ledger has lifecycle counts; blocker ledger has covariate blockers | DONE |
| Report descriptive results even when validation stats blocked | result ledger reports lifecycle/fill/reason counts | DONE |
| Report effective-N and DSR/PBO status | statistics_status reports descriptive effective-N and exact not_computable reasons | DONE |
| Produce result ledger | OTI1_RESULT_LEDGER_2026-05-07.md/json | DONE |
| Produce methodology report | OTI1_METHODOLOGY_REPORT_2026-05-07.md/json | DONE |
| Produce duplicate denominator report | OTI1_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md/json | DONE |
| Produce label-family separation report | OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.md/json | DONE |
| Produce ambiguity-resolution ledger | OTI1_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md/json | DONE |
| Produce blocker ledger | OTI1_BLOCKER_LEDGER_2026-05-07.md/json | DONE |
| Produce completion audit | OTI1_COMPLETION_AUDIT_2026-05-07.md/json | DONE |
| Preserve NO_PROMOTION_VERDICT | NO_PROMOTION_VERDICT | DONE |
| No master registry/source validation flag edits | builder writes only under OTI1 output directory | DONE |
| No paid/API/Databento/network/live trading surface changes | external_fetches_api_databento_calls=0 and live_trading_surfaces_touched=false | DONE |

## Residual Risks

- Lifecycle-truth-only counts are discovery/quarantine only and are not validation evidence.
- Covariate/source-complete claims remain blocked until source/as-of proofs are packet-bound.
- Cross-packet source reuse means pooled packet counts are not independent validation trials.

## Source Evidence Check

| Check | Value |
| --- | --- |
| Source projection rows | 8 |
| Source hash resolution issues | 0 |
| Projection forbidden issues | 0 |
| Cited lifecycle logs hashed | 3 |
