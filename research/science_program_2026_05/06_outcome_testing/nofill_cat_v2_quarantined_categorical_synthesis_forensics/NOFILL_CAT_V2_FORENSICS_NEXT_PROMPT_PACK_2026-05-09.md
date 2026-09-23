# NOFILL CAT V2 Forensics Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Primary Next Lane

`G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT`

Objective: independently audit the quarantined synthesis forensics artifacts. Verify exact partitions, slice ledgers, label-family analysis, blocker/reject learning, no-leak/source/duplicate controls, future hypothesis separation, and completion audit. Preserve all boundaries.

Inputs:

- `NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.json`
- `NOFILL_CAT_V2_FORENSICS_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_NEXT_PROMPT_PACK_2026-05-09.md`
- `NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_2026-05-09.md`

Audit requirements:

- Verify `298 = 225 accepted + 8 blocked + 65 rejected` and `225 = 52 prior accepted + 173 source-corrected accepted`.
- Verify accepted label and source-lane counts exactly.
- Verify blockers and rejects carry no labels and are excluded from accepted denominator.
- Verify duplicate-key collisions are interpreted as source-control inventory, not result evidence.
- Verify no forbidden result, broker, account, live-order, validation, promotion, or live-effect boundary is opened.
- Verify future hypotheses are preregistered capture/control ideas only.

Forbidden: no R/performance, win-rate, expectancy, DSR/PBO performance claims, validation-safe flip, outcome-review opening, broker actual-R, account history, hidden labels, live prompts, `src/` trading logic, risk, execution, permissions, safety selectors, MT5 order/account/history, canaries, credentials, registry edits, paid/API/Databento calls, remote pushes, promotion, or live behavior.

## Optional Separate Blocker-Clear Lane

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE` may target only the 8 residual blockers. It must not rescore accepted rows or inspect rejected rows for outcomes.

Exact blocker access requirements:

### oti4_may3_source_gaps

- Rows: `['NOFILL-CAT-ROW-0049', 'NOFILL-CAT-ROW-0050', 'NOFILL-CAT-ROW-0051']`
- Requirement: Read-only tick parquet or M1/lower OHLC covering the frozen opening range, source-hashed with as-of provenance.
- Current status: `EXACT_SOURCE_GAP`

### oti3_same_tick_order_ambiguities

- Rows: `['NOFILL-CAT-ROW-0130', 'NOFILL-CAT-ROW-0143', 'NOFILL-CAT-ROW-0165', 'NOFILL-CAT-ROW-0178']`
- Requirement: Higher-resolution or broker-native event-order source that proves intra-tick sequence without account/order labels.
- Current status: `SOURCE_SAFE_ORDERING_IMPOSSIBLE_FROM_CURRENT_TICK_ROWS`

### original_oti2_source_gap

- Rows: `['NOFILL-CAT-ROW-0241']`
- Requirement: Side-aware bid/ask tick or approved lower source covering the active pending window through cancel.
- Current status: `EXACT_ACTIVE_WINDOW_SOURCE_GAP`

A future quantitative result lane requires a separate frozen preregistration, denominator, source fields, sample floor, no-leak proof, and G12 gate before any result scoring.
