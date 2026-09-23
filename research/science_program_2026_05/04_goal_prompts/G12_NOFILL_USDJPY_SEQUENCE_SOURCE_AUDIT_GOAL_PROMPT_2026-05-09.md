# G12 NOFILL USDJPY Quote-Event Sequence Source Audit Goal Prompt

Date: 2026-05-09
Owner lane: G12 red-team audit
Worktree: `C:\tmp\gtos_otb\G12USDJPYSEQ`
Branch: `g12-nofill-usdjpy-sequence-source-audit`
Starting HEAD: `aaf2f77a docs: refresh no-fill forward usdjpy research state`

## Goal

Run a maximum-depth G12 audit of the `NOFILL_CAT_V3_USDJPY_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS` lane for rows `NOFILL-CAT-ROW-0130`, `NOFILL-CAT-ROW-0143`, `NOFILL-CAT-ROW-0165`, and `NOFILL-CAT-ROW-0178`.

The audit must decide whether the source-access lane proved `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES` from the current approved/local routes, or whether it missed a source-safe route that can clear any row.

This is not result scoring, validation, promotion, or live implementation. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Mandatory Preflight And Context

Before using memory or prior summaries:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.

Do not rely on chat memory. If context compaction or uncertainty occurs, regenerate live state, reread this prompt and the lane artifacts, then continue from disk.

## Controlling Inputs

Read and cite the USDJPY source-access lane:

- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_2026-05-09.md`
- the lane builder, verifier, and focused test files.

Also read the upstream chain:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_source_control_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`
- `research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/`
- any source files/hash records cited by the USDJPY proof packet.

## Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside hard safety boundaries.

Enforce curiosity, truthfulness, and active creativity:

- Curiosity: actively search for missed local data, broker-export routes, MT5 tick schema details, Sierra/proxy traps, same-tick ordering evidence, stale artifacts, and contradictions.
- Truthfulness: do not fake sequence evidence and do not rescue the rows with proxy data or assumptions. If current approved sources cannot order the predicates, say that clearly.
- Active creativity: think beyond the first folder and current worktree. Use absolute local heavy-data roots, prior worktrees, source manifests, `git log`, `git show`, shadow logs, cached docs, and official platform docs where allowed. But do not convert imagination into evidence.

Do not stop at blocker taxonomy. Within this source-access evidence class, pursue every source-safe route until each target row is cleared, proven impossible from approved routes, or reduced to an exact external access/source requirement. Split only when the next route crosses into result scoring, validation, promotion, registry edit, live behavior, paid/API spend, or a broker/platform access action not available inside the run.

Small-N is irrelevant here: four rows can be source-impossibility evidence if and only if the exact source route is saturated. Do not use small sample size as a reason to avoid source pursuit.

## Audit Requirements

1. Reconstruct each target row:
   - row id;
   - symbol;
   - decisive timestamp;
   - entry predicate;
   - protective/terminal predicate;
   - source file path and SHA256;
   - tick row count at the decisive timestamp;
   - available timestamp precision and quote fields.
2. Independently verify the central claim:
   - the decisive rows are single broker tick snapshots with simultaneous predicates;
   - approved current files expose no sub-millisecond timestamp, monotonic quote-event id, event sequence, or source-safe intra-row ordering field;
   - proxy sources cannot clear broker-native USDJPY same-tick sequence.
3. Search beyond the obvious source folder before accepting impossibility:
   - `C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY`
   - current worktree research artifacts;
   - main worktree source artifacts;
   - `C:\tmp\gtos_otb\*` related worktrees;
   - source manifests/hash records;
   - shadow logs and research exports;
   - Sierra Chart local roots if referenced by local-heavy-data inventory;
   - official MT5/MQL5 docs for `copy_ticks_range`, `MqlTick`, `time_msc`, and tick flags if local cache is insufficient.
4. If a new source route exists, pursue it inside this goal if it remains source-safe. If it requires owner/platform access, write the exact request rather than stopping generically.
5. Decide one terminal G12 verdict:
   - `ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY`
   - `ACCEPT_PARTIAL_SOURCE_CLEARING_WITH_EXACT_REMAINING_BLOCKERS`
   - `RETURN_TO_SOURCE_ACCESS_LANE_WITH_EXACT_MISSED_ROUTE`
   - `REJECT_INVALID_IMPOSSIBILITY_PROOF`

## Required Outputs

Create a new folder:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_usdjpy_sequence_source_audit/`

Produce at minimum:

- `G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_2026-05-09.md`
- `G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_2026-05-09.json`
- `G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_2026-05-09.json`
- `G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_2026-05-09.md`
- `G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_2026-05-09.json`
- `G12_NOFILL_USDJPY_SEQ_EXTERNAL_ACCESS_REQUEST_2026-05-09.md`
- `G12_NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_2026-05-09.md`
- `G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_2026-05-09.md`
- builder/verifier/focused pytest files if useful for reproducibility.

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

Before marking complete:

- JSON parse all generated JSON.
- Run `python -m py_compile` on generated Python.
- Run focused pytest for the audit.
- Recompute cited source hashes.
- Confirm the four target rows remain outside labels, denominators, result use, validation, promotion, and live effect unless a real source-safe clearing route is found.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`.
- Confirm every generated artifact carries or preserves `NO_PROMOTION_VERDICT`.
- Check committed diff scope, not unrelated dirty live-monitoring files.
- Confirm no changes under live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors, MT5 order/account/history behavior, canaries, credentials, remote pushes, paid/API/Databento calls, registry promotion, or order behavior.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or update `.context/00_core/research_current_state.md`.

Commit scoped artifacts with a clear research commit and a docs/context refresh commit. Do not push remote.
