# OTI6 OTR061 Continuation/No-Retrace Quarantined Result Goal Prompt

Date: 2026-05-07
Lane: OTI6 quarantined result / continuation-no-retrace recovered tick packet
Target packet: `OTG0-PKT-061`
Target record: `OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00`
Promotion posture: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Objective

Run the quarantined result lane for the G12-accepted OTR061 recovered XAUUSD tick packet. The goal is to decide what the preregistered `CNR_E0_DECISION_CLOSE_MARKET` continuation/no-retrace model would have produced for this one frozen record, or prove exactly why it cannot be R-scored under the preregistered rules.

This is not a promotion lane and not a live-trading change. It is a file-grounded result/forensics lane. It must learn from the row even if it cannot score R. Do not force a win/loss if the preregistered geometry makes the row invalid. Do not stop at a shallow blocker if the source files can answer the question.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Record HEAD/freshness and any stale-context repair in the completion audit.

## Controlling Inputs

Read and use these exact controls:

- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_COMPLETION_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet`
- `research/program_control/CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md`
- `research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`

You may read `shadow_logs/continuation_no_retrace_candidates.jsonl`, `shadow_logs/continuation_no_retrace_resolutions.jsonl`, and candidate/K55 context rows only to recover preregistered input geometry and prior lifecycle context for this exact record. Keep these as source-hashed inputs/context; do not use broker actual-R/account-history/live trade results.

## File-Grounded Facts To Verify Before Scoring

Verify these from files, not chat:

- Packet: `OTG0-PKT-061`.
- Record: `OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00`.
- Side: `LONG`.
- Recovered tick source SHA256: `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`.
- Recovered tick rows: `89,391`, from `2026-05-06T07:10:01.820Z` through `2026-05-06T11:15:59.763Z`.
- Decision quote: `2026-05-06T07:14:59.889Z`, bid `4647.65`, ask `4648.29`.
- `CNR_E0` executable entry rule for LONG: use ask, so candidate market entry price is `4648.29`.
- Ordered path: `88,060` ticks from `2026-05-06T07:15:00.634Z` to `2026-05-06T11:14:59.900Z`, plus post-horizon tick at `2026-05-06T11:15:00.335Z`.
- Original GTOS geometry from preregistered candidate source: original limit entry `4561.52`, stop `4547.35`, TP1 `4582.77`, base R price `14.17`, original direction `LONG`.

The expected high-risk issue is that the recovered executable market entry `4648.29` is already above original TP1 `4582.77` for a LONG row. The lane must resolve this exactly under the preregistration:

- If `CNR_E0` entry is already on the wrong side of the original TP1, do not score it as a positive R trade. Classify it as preregistered geometry invalid / target already passed at decision quote, with lifecycle context that the no-retrace continuation happened before a valid market-entry model could enter.
- If the files show a different preregistered geometry, record the file-grounded truth and decide from that.

## Required Analysis

1. Recompute the recovered parquet SHA256 and row/window coverage.
2. Reconstruct the decision quote and ordered path from the source-hashed parquet.
3. Recover original preregistered trade geometry from source-hashed candidate/context rows and record its source file/line/hash.
4. Apply the preregistered `CNR_E0_DECISION_CLOSE_MARKET` geometry rule before any R scoring.
5. Determine terminal status:
   - `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_SYNTHETIC_R_COMPUTED` if geometry is valid and ordered path reaches TP1/SL in unambiguous order.
   - `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION` if executable market entry is already beyond original TP1 for LONG or below original TP1 for SHORT.
   - `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_BAD_CONTINUATION_GEOMETRY` if entry/stop/target ordering violates the preregistered geometry.
   - `BLOCKED_WITH_EXACT_NEXT_QUESTION` only if a required source/hash/geometry/path field is truly missing after local-heavy-data saturation.
6. If R is computable, report only quarantined synthetic path-R, never broker actual-R or validation.
7. If R is not computable because the target was already passed, write failure/opportunity forensics: what the row teaches about decision latency, no-retrace timing, target already reached before valid CNR_E0 entry, and what future preregistered capture would be required to test an earlier-entry or alternate-target model.

## Required Outputs

Write only under:

- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/`

Required artifacts:

- `OTI6_CNR_METHOD_FREEZE_2026-05-07.md/json`
- `OTI6_CNR_RESULT_LEDGER_2026-05-07.md/json`
- `OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md/json`
- `OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.md/json`
- `OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.md/json`
- `OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.md/json`
- `OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md/json`
- `OTI6_CNR_COMPLETION_AUDIT_2026-05-07.md/json`
- Builder/verifier script and focused tests.

## Verification

Before completion:

- JSON parse all generated JSON/JSONL.
- `py_compile` generated Python.
- Run focused tests for the OTI6 builder and relevant OTR061/G12 controls.
- Recompute source hashes used in the result.
- Scan generated outputs for `NO_PROMOTION_VERDICT`.
- Confirm no generated JSON sets `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no broker actual-R/account-history/live trade result/live order state/blocked-packet outcome source was read.
- Confirm no paid/API/Databento/MT5 order calls occurred.
- Confirm no forbidden live-surface diff under `src`, `prompts`, `config`, canaries, execution, permissions, risk, safety, selectors, MT5 order behavior, credentials, remotes, paid/API/Databento, or order behavior.
- Regenerate `.context/LIVE_STATE.md` and update `.context/00_core/research_current_state.md` if the durable research map changes.

## Forbidden

No live trading prompt/risk/execution/permission/safety/selector/canary/order behavior edits. No MT5 order calls. No account history or broker actual-R. No live order state. No paid/API/Databento calls. No source validation flips. No outcome-review flips. No master registry edits. No promotion language. No post-hoc threshold rescue. No alternate target, trailing rule, earlier-entry model, or candle-internal entry model may be scored as if preregistered; such ideas can only be written as future hypotheses.

## Stop Condition

The goal is complete only when this one frozen `OTG0-PKT-061` record has a terminal file-grounded OTI6 status, the result/impossibility forensics explain what the row teaches, all required artifacts are written, and verification passes. Do not stop with "needs more data" unless the exact missing data/source/field/schema/parser/timestamp/access item is named after local-heavy-data saturation.
