# G12 NOFILL Close Audit Goal Prompt - 2026-05-08

## Starter Message

Use the one-line starter message from the owner, but treat this file as the controlling prompt.

## Goal

Run `G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_AUDIT_V1` as the G12 red-team/audit owner for the merged `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1`.

The goal is not to score performance, rescue a result, or promote anything. The goal is to audit whether the closure packet is valid input-only source/control evidence, whether the 297 source-closed rows are genuinely source-closed under no-leak/as-of rules, whether the 1 source-blocked row is exactly blocked or locally resolvable, and what next route is justified.

## Mandatory GTOS Preflight

Before relying on memory or summaries:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. If any context is stale, read the newer research artifacts directly and record the stale-context condition in the context anchor.

## Controlling Inputs

Primary NOFILL close packet:

- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_G12_AUDIT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/source_requests/NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/build_nofill_lifecycle_closure_source_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/verify_nofill_lifecycle_closure_source_packet_2026_05_08.py`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/test_nofill_lifecycle_closure_source_packet_2026_05_08.py`

Upstream packet/audit context:

- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/`
- `research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/`
- `research/science_program_2026_05/06_outcome_testing/g12_cnr_t3_lifecycle_audit/`
- `research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/`
- `research/science_program_2026_05/06_outcome_testing/g12_oti8_cnr061_post_result_audit/`
- `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/oti5_g6_cusum_changepoint_quarantined_results/`
- `research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/`

If a listed file is missing, do not guess. Search the repo and prior worktree roots, record the search, and write the exact missing-input blocker if it cannot be found.

## Owner Hardening Standard

This is a maximum-effort research audit, not a superficial signoff.

Operate with the three required research virtues:

- Curiosity: actively ask what could be wrong, missing, stale, overcounted, under-searched, source-boxed, or newly useful for the system.
- Truthfulness: do not fake, rescue, soften, or overstate. If a row is blocked, say why. If a result is negative or narrow, keep it narrow. If a source does not prove a claim, say so.
- Active creativity: do not stay boxed by the first artifact, timeframe, worktree-local files, current model framing, existing GTOS edge, or standard strategy categories. Search non-obvious source/control explanations while keeping evidence strict.

Apply these rules:

- Go to proof-or-impossibility. Do not stop at a generic "blocked" if local evidence, source hashes, absolute data roots, prior worktree artifacts, code history, or approved read-only search could answer it.
- Treat prompt examples and listed files as starting points, not boundaries.
- Search absolute local heavy-data roots before accepting missing data. Worktree absence is not data absence.
- If access is needed, request it and write the exact command/source/fields/time range/cost/safety boundary required.
- If web/curl/webfetch becomes relevant, use it only for source-contract/public-source evidence and save a raw/source index. This lane should not need broad web research unless an artifact cites an external source whose contract must be checked.
- Preserve a context anchor, active question stack, searched-root ledger, route-decision ledger, blocker ledger, and instruction-coverage checklist so conversation compaction cannot erase requirements.
- After any resume, compaction, or uncertainty, regenerate `LIVE_STATE`, re-read this prompt and the core context docs, re-read latest lane artifacts, then continue from committed state.
- Small `n` blocks validation/promotion only. It is not an excuse to stop. If sample size matters, name the exact denominator and the source-safe expansion or extraction path.
- Negative or non-promotable evidence must produce learning: what failed, what was proven, what remains unknown, and what exact future capture/test would close the unknown.

## Audit Questions

Answer these from files and source checks, not assumptions:

1. Does the packet universe exactly match the 298 G12_NOFILL accepted rows, with six T3 `stop_after_original_horizon` rows and 94 G12-blocked CNR061 rows excluded?
2. Was the context anchor written before the frozen source contract, and was the contract frozen before row classification?
3. Do the packet rows avoid R/performance, broker actual-R, account history, live/order, hidden result, and post-outcome fields?
4. Do all packet rows preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`?
5. Are the 297 source-closed rows truly closed only as input/source evidence, not as performance evidence?
6. Is the sole source-blocked XAUUSD tick-window row truly unresolved after local-heavy-data search, or can it be cleared from an already-existing source-hashed local file without new extraction?
7. Does the read-only extraction request manifest for `NOFILL-CLOSE-ROW-0127` contain the exact symbol, time window, fields, parser, source/as-of rule, forbidden calls, and no-leak constraints needed for a later extraction lane?
8. Do OTI1 lifecycle rows have sufficient projected symbol/session/side metadata, and are fill/cancel/still-open labels source-safe?
9. Do OTI2/OTI5 no-entry and terminal-sequence rows remain source-only and avoid terminal-order claims that require hidden path labels?
10. Did OTI3 source recovery use the correct USDJPY M1 source and avoid the prior local-source boxing error?
11. Did OTI4 tick terminal projections use source-hashed tick files only, while retaining opening-drive/prereg field blockers?
12. Do duplicate denominator and sample-floor ledgers prevent repeated rows from becoming validation evidence?
13. Is every exact blocker actionable, non-generic, and tied to a specific field/source/path/extraction requirement?
14. What does this packet unlock next, and what remains forbidden?

## Required Outputs

Write all outputs under:

`research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/`

Required artifacts:

- `G12_NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.md` and `.json`
- `G12_NOFILL_CLOSE_NEXT_PROMPT_PACK_2026-05-08.md`
- `G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- A builder/verifier/test if useful for machine-checkable reproduction.

The decision ledger must give one of these terminal verdicts:

- `ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE`
- `ACCEPT_WITH_EXACT_SOURCE_BLOCKER`
- `BLOCKED_WITH_NEXT_EXACT_QUESTION`
- `REJECT_INVALID_CLEARING`

If mixed, make row-level decisions and a packet-level decision.

## Verification Requirements

Before marking complete:

- JSON/JSONL parse for every new machine-readable artifact.
- Recompute or verify source hashes cited by the packet/audit when local files are available.
- Run no-leak scan for forbidden R/performance/account/live/hidden/result fields.
- Verify exact counts: 298 total rows, 297 source-closed, 1 source-blocked, 6 T3 rows excluded, 94 G12-blocked CNR061 rows excluded.
- Verify `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Run `py_compile` for new scripts.
- Run focused pytest if a test is created or already relevant.
- Run a forbidden live-surface diff over `src`, `prompts`, `config`, canary, MT5 order/account, execution, risk, permissions, safety, selectors, paid/API/Databento, credentials, remotes, and order-behavior paths.
- Regenerate `LIVE_STATE` at closeout and record whether research context is fresh.

## Hard Boundaries

Do not:

- score R/performance;
- inspect broker actual-R, account history, live trade results, live orders, or hidden outcome labels;
- score blocked CNR061 rows;
- execute MT5 order/account calls;
- use paid/API/Databento calls;
- change source registries, master registries, live prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, credentials, remotes, or order behavior;
- mark any source `validation_safe=true`;
- set `outcome_review_opened=true`;
- claim promotion, validation, or live effect.

Read-only local file search is allowed. Read-only extraction is not part of this G12 audit unless the owner explicitly authorizes a separate extraction lane; if extraction is needed, produce the exact request and stop at that boundary.

## Stop Condition

This goal is complete only when the audit has either accepted, blocked, or rejected the NOFILL close packet with machine-checkable evidence, exact row/source counts, exact blockers, learning notes, next-lane prompt guidance, and preserved research-only safety flags. Chat-only conclusions are not complete.
