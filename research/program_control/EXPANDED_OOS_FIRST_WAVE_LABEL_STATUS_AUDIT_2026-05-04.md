# Expanded OOS First-Wave Label-Status Audit - 2026-05-04

**Status:** `FIRST_WAVE_LABEL_STATUS_AUDIT_CURRENT_NOT_TERMINAL`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only.
- No live trading logic, prompts, risk, execution, or safety settings changed.
- No AI/API calls, no new Databento pulls, and no outcome slices opened.

## Summary

| Metric | Value |
| --- | --- |
| target_families_from_matrix | 5 |
| families_with_label_status_artifact | 5 |
| families_replay_ready_under_current_spec | 0 |
| families_label_status_only_no_registered_cohort | 2 |
| families_control_status_only | 3 |
| families_missing_conversion_status | 0 |
| opened_outcome_slices | 0 |
| opened_outcome_rows | 0 |
| status_counts | {"LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT": 3, "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT": 2} |

## Family Status

| Family | Label status | Sources | Matched replay cohorts | Next action |
| --- | --- | --- | --- | --- |
| EURUSD with EURUSD/6E | LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT | EURUSD_6E:268r/g2/M15_AVAILABLE; EURUSD_SCID:276r/g0/M15_AVAILABLE | {"EURUSD_6E": [], "EURUSD_SCID": []} | Register replay/label-status slice before opening EURUSD/6E outcomes. |
| S&P with ES/MES | LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT | SPX_ES:268r/g2/M15_AVAILABLE; SPX_MES:268r/g2/M15_AVAILABLE | {"SPX_ES": [], "SPX_MES": []} | Keep as expansion/control until broker/source mapping and candidate relevance are registered. |
| CL macro/liquidity proxy/control | LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT | CL_PROXY:268r/g2/M15_AVAILABLE | {"CL_PROXY": []} | Use only as macro/liquidity control after a registered cross-instrument question. |
| ZN macro/rates proxy/control | LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT | ZN_CONTROL:268r/g2/M15_AVAILABLE | {"ZN_CONTROL": []} | Use only as rates/control context after a registered cross-instrument question. |
| VIX/VXM controls | LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT | VIX_VXM:247r/g17/M15_AVAILABLE; VIX_VXMM:107r/g47/SPARSE_SOURCE_WARNING | {"VIX_VXM": [], "VIX_VXMM": []} | Keep sparse warning and use only as control context after registered question. |

## Status Reasons

### EURUSD with EURUSD/6E

- `LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT`: Converted source rows exist, but the current frozen raw-OHLC replay cohort spec has no matching cohort for this family. Creating a new strategy cohort would be a separate pre-registered research step, not part of this label-status audit for EURUSD with EURUSD/6E.
- Outcome slice status: `NOT_OPENED_BY_LABEL_STATUS_AUDIT`.

### S&P with ES/MES

- `LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT`: Converted source rows exist, but the current frozen raw-OHLC replay cohort spec has no matching cohort for this family. Creating a new strategy cohort would be a separate pre-registered research step, not part of this label-status audit for S&P with ES/MES.
- Outcome slice status: `NOT_OPENED_BY_LABEL_STATUS_AUDIT`.

### CL macro/liquidity proxy/control

- `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT`: This family is registered as cross-instrument/control evidence. The current frozen raw-OHLC strategy cohort spec has no direct trade-label cohort for it, so this audit records source/label status without opening outcomes.
- Outcome slice status: `NOT_OPENED_BY_LABEL_STATUS_AUDIT`.

### ZN macro/rates proxy/control

- `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT`: This family is registered as cross-instrument/control evidence. The current frozen raw-OHLC strategy cohort spec has no direct trade-label cohort for it, so this audit records source/label status without opening outcomes.
- Outcome slice status: `NOT_OPENED_BY_LABEL_STATUS_AUDIT`.

### VIX/VXM controls

- `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT`: This family is registered as cross-instrument/control evidence. The current frozen raw-OHLC strategy cohort spec has no direct trade-label cohort for it, so this audit records source/label status without opening outcomes.
- Outcome slice status: `NOT_OPENED_BY_LABEL_STATUS_AUDIT`.

## Completion Impact

- This audit creates replay/label-status artifacts for the five first-wave families that were converted but not opened.
- It does not create replay results, strategy labels, p-values, DSR/PBO/effective-N, or promotion evidence.
- Families without current raw-OHLC cohorts require a separate pre-registered cohort/question before deterministic replay outcomes can be opened.
- Cross-instrument controls remain context/control evidence only and cannot validate the original trading edge.

## Remaining Goal Gaps

- Candidate survival table by evidence class is still incomplete.
- Instrument/source expansion scorecard needs to absorb this audit plus replay/depth statuses.
- Opened/burned/reserved ledger is still partial at goal level.
- No final synthesis exists after the first-wave label-status and depth/sampling audits.
