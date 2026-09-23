# G12 OTI5 + OTR061 Post-Audit Goal Prompt

Date: 2026-05-07
Lane: G12 combined post-test / packet-recovery audit
Scope: OTI5 CUSUM result audit plus OTR061 recovered packet re-audit
Promotion posture: NO_PROMOTION_VERDICT

## Objective

Run one combined G12 audit over:

1. `OTI5_G6_CUSUM_CHANGEPOINT_QUARANTINED_RESULTS` for `OTG0-PKT-063`.
2. `OTR061_XAU_TICK_RECOVERY` packet proposal for `OTG0-PKT-061`.

This goal must decide whether OTI5 is accepted as quarantined discovery evidence, rejected, or blocked; and whether OTR061 is accepted as a source-hashed packet ready for a future continuation/no-retrace quarantined result lane, rejected, or blocked. It must not open any new outcome scoring beyond auditing existing OTI5 results and OTR061 packet-recovery artifacts.

This is a proof-or-impossibility audit, not a shallow red-team pass. Do not stop at a generic blocker. If something looks missing, search the committed artifacts, builders, tests, absolute local data roots, and source hashes until the question is answered or exact impossibility is proven. Every blocker must name the precise missing source, field, schema, parser, timestamp window, owner approval, or evidence artifact.

Be strict, but not timid. Do not reject OTI5 merely because it is discovery-only, negative, below validation floors, or not promotable; those are expected if the method/no-leak/source-hash/duplicate/label-family controls are sound. Do not reject OTR061 merely because it has not scored outcomes yet; the question is whether it is a clean input-only recovered packet for a future result lane. Reject only for actual control failure, leakage, source invalidity, label confusion, bad hash/coverage, unapproved data use, or unsupported claims.

For OTI5 specifically, the audit must learn from the negative result. A negative quarantined result is not a dead-end label. It is first-class evidence about a mechanism that failed under current construction. The goal must explain what went wrong, how the decisions/path states led to loss/no-entry outcomes, whether the failure is structural, methodological, data-limited, or merely an underpowered discovery artifact, and what future hypotheses or capture fields become sharper because of it. Do not "flag failed and move on."

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Record HEAD, freshness, local-heavy-data rule compliance, and any stale-context repair in the completion audit.

If a path is missing in the worktree, inspect the absolute main repo or source path before accepting a blocker. If access is denied, request access.

## Controlling Inputs

Read OTI5 directly:

- `research/science_program_2026_05/06_outcome_testing/oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.md/json`
- `OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl`
- `OTI5_G6_CUSUM_METHOD_FREEZE_2026-05-07.md/json`
- `OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.md/json`
- OTI5 builder/test.

Read OTR061 directly:

- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.md/json`
- `OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.md/json`
- `OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.md/json`
- `OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.md/json`
- `OTR061_COMPLETION_AUDIT_2026-05-07.md/json`
- `OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet`
- OTR061 builder/test.

Read prior controls:

- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`

## Known Claims To Verify From Files, Not Trust From Chat

Treat these as claims that must be independently checked against committed artifacts:

- OTI5 claims `81` source-ready rows for `OTG0-PKT-063`, exactly five G12-blocked rows excluded, `17` primary duplicate groups, `9` resolved synthetic tick-R rows, terminal counts `8 SL`, `1 TP1`, `8 no-entry`, mean resolved synthetic R `-0.72222222`, and DSR/PBO/effective-N `not_computable`.
- OTR061 claims MT5 read-only tick recovery for `XAUUSD` from `2026-05-06T07:10:01.820Z` to `2026-05-06T11:15:59.763Z`, `89,391` rows, SHA256 `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`, decision quote `2026-05-06T07:14:59.889Z`, LONG executable ask `4648.29`, and ordered path coverage from `2026-05-06T07:15:00.634Z` to `2026-05-06T11:14:59.900Z` plus post-horizon tick.
- Both lanes claim `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, no broker actual-R/account-history/live trade result use, no paid/API/Databento calls, no live trading surface edits, and clean scoped verification.

If any claim differs from the files, record the file-grounded truth and decide from that.

## Audit Questions

For OTI5:

- Did it use exactly the G12-accepted frozen 81-row subset and exclude the five blocked rows?
- Was the duplicate denominator frozen before scoring?
- Are result labels synthetic tick-recomputed discovery-only, not broker actual-R?
- Are no-leak/source-hash/feature-asof checks sufficient for quarantined discovery acceptance?
- Are the negative descriptive results correctly reported without promotion language?
- Are DSR/PBO/effective-N correctly `not_computable`?
- Is there any hidden route to compute validation statistics honestly, or is `not_computable` the correct terminal state because of sample floor, no unseen fold matrix, and discovery-only scope?
- Why did the OTI5 construction fail descriptively? Use existing OTI5 row/result ledgers to break down SL, TP1, and no-entry outcomes by packet-bound fields that are already available without new outcome scoring.
- Did the CUSUM/changepoint feature fire too late, fire in the wrong market condition, fail to identify continuation quality, select adverse continuation, or simply lack enough resolved examples? If the files cannot answer one of these, record the exact missing field/capture requirement.
- Are failures concentrated by duplicate group, session/window, side, same-bar/tick ambiguity, feature-asof class, source coverage class, volatility/path state, or exclusion rule?
- What did the losing rows have in common before outcome, and what did the single TP1 row have that the losing rows lacked, without converting this into an unregistered optimized rule?
- Which future hypotheses should be registered from this failure analysis, and which tempting rescue routes must be rejected as post-hoc or source-blocked?

For OTR061:

- Is the recovered MT5 tick export read-only and source-hashed?
- Does it cover the required `2026-05-06T07:10:00Z` to `2026-05-06T11:15:00Z` window?
- Are decision quote and ordered path fields input-only and free of result labels?
- Did the lane avoid account history, broker actual-R, live order state, orders, paid/API/Databento, and live-surface changes?
- Is the packet proposal sufficient for a future G12-approved continuation/no-retrace result lane?
- Does the recovered tick packet now answer the previous `OTG0-PKT-061` data blocker, or is there still a remaining exact source/timestamp/decision-price/path-order gap?

For both:

- Did the lanes search local-heavy-data paths correctly, especially `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`, before accepting or clearing data blockers?
- Are all accepted states scoped to future quarantined audit or quarantined discovery only, with no validation/promotion meaning?

## Required Decisions

Write terminal G12 decisions:

- OTI5: `ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE`, `REJECT_INVALID_RESULT`, or `BLOCKED_WITH_EXACT_NEXT_QUESTION`.
- OTR061: `ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT`, `REJECT_INVALID_RECOVERY`, or `BLOCKED_WITH_EXACT_NEXT_QUESTION`.

If OTR061 is accepted, write a one-line `/goal` prompt for the next continuation/no-retrace result lane. If it is not accepted, write exact next unblocker.

The next-lane prompt must itself be hardened: one physical line, mandatory preflight, controlling OTR061/G12 artifact paths, exact frozen packet ID, proof-or-impossibility wording, local-heavy-data search rule, strict label separation, no broker actual-R/account-history/live result use, no paid/API/Databento unless explicitly approved in a pre-call manifest, no live-surface edits, expected outputs, verification, and stop condition.

## Required Outputs

Write only under:

- `research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/`

Required artifacts:

- `G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.md/json`
- `G12_OTI5_RESULT_METHOD_AUDIT_2026-05-07.md/json`
- `G12_OTI5_NEGATIVE_RESULT_FORENSICS_2026-05-07.md/json`
- `G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.md/json`
- `G12_OTI5_OTR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-07.md/json`
- `G12_OTI5_OTR061_DUPLICATE_LABEL_AUDIT_2026-05-07.md/json`
- `G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md`
- `G12_OTI5_OTR061_COMPLETION_AUDIT_2026-05-07.md/json`
- Builder/verifier script and focused tests.

## Verification

Before completion:

- JSON parse all generated JSON/JSONL.
- `py_compile` generated Python.
- Run focused G12 tests plus OTI5 and OTR061 tests.
- Scan all generated outputs for `NO_PROMOTION_VERDICT`.
- Confirm no generated JSON sets `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no forbidden live-surface diff under `src`, `prompts`, `config`, `scripts/canary`, execution, permissions, risk, safety, selectors, MT5 order behavior, canaries, credentials, remotes, paid/API/Databento.
- Regenerate `.context/LIVE_STATE.md` and update `.context/00_core/research_current_state.md` if the durable research map changes.

## Forbidden

No new outcome scoring except auditing existing OTI5 result artifacts. No broker actual-R, account history, live trade results, blocked-packet outcome sources, live order state, MT5 order calls, paid/API/Databento calls, prompt/risk/execution/permission/safety/selector/canary/order behavior edits, credentials, remote pushes, source validation flips, outcome-review flips, or promotion language.

Failure forensics may use existing OTI5 result rows and already-computed labels to explain failure modes. It must not create new optimized thresholds, re-score excluded rows, inspect blocked-packet outcomes, or present post-hoc rescue ideas as preregistered evidence.

## Stop Condition

The goal is complete only when both OTI5 and OTR061 have terminal G12 decisions, OTI5 has a clear negative-result forensics/learning artifact, any accepted next lane has a one-line prompt with exact controls, and all verification checks pass.

Do not mark complete with a vague "needs more data" answer. Either accept/reject/block each target with file-grounded reasons, or prove impossibility with a saturation ledger of searched paths, missing fields/windows, and exact next action.
