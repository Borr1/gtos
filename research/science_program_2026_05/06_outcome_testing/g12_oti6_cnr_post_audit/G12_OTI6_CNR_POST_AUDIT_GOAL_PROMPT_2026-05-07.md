# G12 OTI6 CNR Post-Audit Goal Prompt

Date: 2026-05-07
Lane: G12 post-result audit / CNR target-already-passed evidence
Target result lane: `OTI6_OTR061_CNR_QUARANTINED_RESULT`
Target packet: `OTG0-PKT-061`
Target record: `OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00`
Promotion posture: `NO_PROMOTION_VERDICT`

## Objective

Run the G12 post-audit over OTI6. Decide whether the OTI6 terminal result is accepted as quarantined discovery/impossibility evidence, rejected as invalid implementation, or blocked with an exact next question.

This is not a live-trading or promotion lane. It is also not a shallow pass/fail audit. OTI6 did not score R because the preregistered `CNR_E0_DECISION_CLOSE_MARKET` LONG entry appears to be already beyond original TP1. The audit must verify whether that is correct, learn what it means, and convert the learning into a precise next preregistration prompt if accepted.

Be strict, but not timid. Do not reject OTI6 merely because synthetic R is null or because the result is non-promotable. Reject only if OTI6 violated source/hash/no-leak/duplicate/label/prereg geometry controls or made unsupported claims. If OTI6 is correct, accept it as useful quarantined evidence that the original no-retrace continuation had already delivered before a valid CNR_E0 market-entry model could enter.

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

Read OTI6 directly:

- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHOD_FREEZE_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/OTI6_CNR_COMPLETION_AUDIT_2026-05-07.md/json`
- OTI6 builder/verifier/tests.

Read upstream controls:

- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json`
- `research/program_control/CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md`
- `research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`

## File-Grounded Claims To Verify

Verify these from files, not chat:

- OTI6 terminal status: `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION`.
- `CNR_E0` entry model: decision-close market entry, LONG uses executable ask.
- Decision quote: `2026-05-06T07:14:59.889Z`, bid `4647.65`, ask `4648.29`.
- Original GTOS geometry: entry `4561.52`, stop `4547.35`, TP1 `4582.77`, base R `14.17`.
- Target already passed: ask is `65.52` price units / `4.62385321R` beyond original TP1 before CNR_E0 can enter.
- Synthetic path-R is `null`; R scoring was blocked before path scoring.
- Recovered path still trends up: first ordered path ask/bid `4648.31/4647.67`, last `4680.18/4679.63`, but this must not be scored as CNR_E0 profit because the original target was already behind the entry.

## Audit Questions

- Did OTI6 correctly apply the preregistered CNR_E0 geometry before R scoring?
- Is `target already passed at decision` the correct terminal status under the preregistration?
- Did OTI6 avoid forcing this row into a win/loss?
- Did OTI6 avoid broker actual-R, account history, live trade results, live order state, paid/API/Databento, MT5 order calls, and live-surface edits?
- Did OTI6 preserve source hashing, label separation, duplicate denominator, no-leak boundaries, and `NO_PROMOTION_VERDICT`?
- Does this result mean the continuation/no-retrace mechanism is dead, or only that the preregistered CNR_E0 decision-close market-entry model is too late for this row?
- What exact next hypothesis should be registered if the learning is accepted?

## Required Terminal Decision

Choose one:

- `ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE`
- `REJECT_INVALID_RESULT_IMPLEMENTATION`
- `BLOCKED_WITH_EXACT_NEXT_QUESTION`

If accepted, write the next one-line `/goal` prompt for a preregistration/control lane only. It should not open scoring. The likely next lane is a `CNR_TIMING_MODEL_PREREGISTRATION` that defines earlier-entry/timing candidates, target models, latency captures, and sample floors before any outcome opening.

## Required Outputs

Write only under:

- `research/science_program_2026_05/06_outcome_testing/g12_oti6_cnr_post_audit/`

Required artifacts:

- `G12_OTI6_CNR_DECISION_LEDGER_2026-05-07.md/json`
- `G12_OTI6_CNR_GEOMETRY_AUDIT_2026-05-07.md/json`
- `G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.md/json`
- `G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_2026-05-07.md/json`
- `G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_2026-05-07.md/json`
- `G12_OTI6_CNR_NEXT_LANE_PROMPT_PACK_2026-05-07.md`
- `G12_OTI6_CNR_COMPLETION_AUDIT_2026-05-07.md/json`
- Builder/verifier script and focused tests.

## Verification

Before completion:

- JSON parse all generated JSON.
- `py_compile` generated Python.
- Run focused G12/OTI6/OTR061 tests.
- Scan generated outputs for `NO_PROMOTION_VERDICT`.
- Confirm no generated JSON sets `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no broker actual-R/account-history/live trade result/live order state/blocked-packet outcome source was read.
- Confirm no paid/API/Databento/MT5 order calls occurred.
- Confirm no forbidden live-surface diff under `src`, `prompts`, `config`, canaries, execution, permissions, risk, safety, selectors, MT5 order behavior, credentials, remotes, paid/API/Databento, or order behavior.
- Regenerate `.context/LIVE_STATE.md` and update `.context/00_core/research_current_state.md` if durable research state changes.

## Forbidden

No new outcome scoring. No alternate target scoring. No earlier-entry scoring. No post-hoc rescue rule treated as evidence. No broker actual-R/account-history/live trade results. No live order state. No paid/API/Databento. No MT5 order calls. No source validation flips. No outcome-review flips. No master registry edits. No live trading surface edits. No promotion language.

## Stop Condition

The goal is complete only when OTI6 has a terminal G12 decision, the target-already-passed learning is accepted/rejected/blocked with file-grounded reasons, any accepted next lane has a hardened one-line prompt, and all verification checks pass. Do not stop with vague "needs more data"; every blocker must name the exact source/field/schema/timestamp/access/prereg item required.
