# G12 NOFILL Categorical Result Packet V2 Audit Goal Prompt

Promotion posture: `NO_PROMOTION_VERDICT`

## Mission

Run `G12_NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_AUDIT` as the red-team/control owner for the source-safe no-fill categorical V2 rebuild. Independently audit the V2 packet under `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/`, decide whether it is acceptable as input-only categorical lifecycle evidence for future research use, and produce durable G12 artifacts, verifier, focused tests, completion audit, and next prompt pack. This is not an R/performance, validation, promotion, live, broker, or registry-edit lane.

## Mandatory Preflight

Before using summaries or memory, regenerate and read `.context/LIVE_STATE.md` with `python scripts/generate_live_state.py`. Then read `.context/00_core/quick_reference_card.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/local_heavy_data_inventory.md`, `.context/00_READING_ORDER.md`, and the newest relevant session handoff if needed. Record the starting HEAD, current branch, live-state freshness, and the exact controlling input paths in a G12 context anchor.

## Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard safety boundaries. Enforce curiosity, truthfulness, and active creativity: actively search for improvement routes and hidden failure modes; report failures honestly without rescue narratives; and explore non-obvious interpretations without converting imagination into evidence claims. Treat examples, listed files, current timeframe, current instrument, current worktree, first model framing, and first data modality as starting points rather than limits.

Do not stop at a blocker until you have pursued proof-or-impossibility from approved inputs. Search local artifacts, source ledgers, prior worktrees, absolute local heavy-data roots, git history, tests, builders, JSON/JSONL, cached source files, and neighboring lane outputs before accepting a blocker. If access is needed, request it explicitly. If web/source evidence is needed and allowed by the lane, use curl or webfetch and save raw captures plus a source index. Maintain a context anchor, active question stack, searched-root ledger, route-decision ledger, and instruction-coverage checklist so conversation compaction cannot erase requirements. After any resume, compaction, or uncertainty, regenerate LIVE_STATE, re-read this prompt and core context docs from disk, then continue from committed artifacts.

Small `n` can block validation or promotion, but it is not an excuse to stop. If sample/denominator limits matter, state the exact denominator, sample floor, expansion route, or proof of source-safe impossibility. Negative or blocked evidence is first-class: explain why each blocker/reject exists, what it proves, what it does not prove, what would unblock it, and whether a future preregistered lane is justified.

## Controlling Inputs

Primary V2 rebuild directory:

- `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/`
- `NOFILL_CAT_V2_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_CAT_V2_REBUILD_CONTRACT_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json`
- `NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_LEARNING_LEDGER_2026-05-09.md`
- `NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.md` and JSON
- `NOFILL_CAT_V2_G12_NEXT_PROMPT_PACK_2026-05-09.md`
- builder, verifier, focused test, and main verification hardening commit `a9929ae0`

Required upstream context:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/`
- OTI1 pending-intent, OTI2 fill/path V2, OTI3 USDJPY quote/tick, OTI4 opening-drive source correction, and OTI5 duplicate-conflict artifacts when needed to trace row provenance.

## Required Audit Work

1. Reconstruct the V2 universe from artifacts, not from chat: verify exactly `298 = 225 accepted + 8 blocked + 65 rejected` and exactly `225 = 52 prior accepted + 173 source-corrected accepted`.
2. Verify accepted rows have zero overlap with blocked rows and rejected rows, and that blocked/rejected rows receive no categorical label, no denominator inclusion, and no outcome/performance treatment.
3. Verify accepted label counts exactly: `nofill_terminal_before_entry=110`, `source_corrected_no_entry_through_pending_horizon=32`, `opening_drive_source_projection_ready_no_result_label=51`, `fill_path_entry_before_protective_level_no_terminal_observed=22`, `fill_path_entry_before_protective_level_before_terminal_area=4`, `fill_path_entry_before_terminal_area_before_protective_level=3`, and `canonical_duplicate_geometry_source_ready_no_label_assigned=3`.
4. Verify source-lane counts exactly: prior G12 categorical packet audit `52`, OTI1 `32`, OTI2 V2 `29`, OTI3 `58`, OTI4 `51`, and OTI5 `3`.
5. Verify exact residual blockers: `3` OTI4 May 3 source gaps, `4` OTI3 same-tick order ambiguities, and `1` original OTI2 source gap. Pursue each blocker until exact proof, exact unblocking route, or proof of source-safe impossibility is recorded.
6. Verify exact rejects: `26` OTI4 contract-excluded rows and `39` OTI5 noncanonical duplicate projections. Confirm they are excluded for source/contract/duplicate reasons, not hidden performance reasons.
7. Recompute or independently check source hashes where feasible. If any source-hash drift appears, trace the root and record whether it is path-root drift, file-content drift, artifact drift, or true invalidation.
8. Run no-leak scans against accepted, blocked, rejected, source-hash, duplicate, completion, and row-decision artifacts. Confirm there are no broker actual-R, live trade result, hidden outcome label, post-decision forbidden field, validation-safe flip, outcome-review opening, or live-effect flags.
9. Audit duplicate denominator and sample-floor posture. State what is countable as categorical lifecycle evidence, what remains discovery/control only, and what cannot be used for validation or promotion.
10. Explain what each categorical label proves and does not prove. Be explicit that input-only lifecycle labels are not expectancy, win rate, broker actual-R, validation, promotion, or live-gate evidence.
11. Build G12 decision artifacts that are machine-checkable and human-readable. If accepted, acceptance must be narrow: input-only categorical lifecycle evidence with blocked/rejected families preserved. If blocked or rejected, explain exact row-level reasons and next unblocker.

## Required Outputs

Create a new directory:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/`

Write at minimum:

- `G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_2026-05-09.md`
- `G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.md` and JSON
- `G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_2026-05-09.md` and JSON
- `G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.md` and JSON
- `G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.md` and JSON
- `G12_NOFILL_CAT_V2_LEARNING_LEDGER_2026-05-09.md`
- `G12_NOFILL_CAT_V2_NEXT_PROMPT_PACK_2026-05-09.md`
- `G12_NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.md` and JSON
- `verify_g12_nofill_cat_v2_audit_2026_05_09.py`
- `test_g12_nofill_cat_v2_audit_2026_05_09.py`

The next prompt pack must state the exact next lane. If G12 accepts the V2 packet, the likely next lane is a quarantined categorical-result synthesis/forensics lane that summarizes the 225 accepted input-only categorical labels without converting them into R/performance or validation. If G12 finds a blocker, produce the exact owner/access/source/capture/router prompt needed instead.

## Verification Requirements

Run JSON/JSONL parse checks, source-hash checks where feasible, no-leak scans, duplicate/sample-floor checks, exact count/overlap checks, `python -m py_compile` on generated Python files, focused pytest, and a committed-diff forbidden-surface check. Regenerate `.context/LIVE_STATE.md` before closeout and update `.context/00_core/research_current_state.md` only if the lane materially changes the research map. Commit only scoped G12 audit artifacts and any necessary research-state refresh.

## Forbidden

Do not touch live trading prompts, `src/` trading logic, risk, execution, permissions, safety gates, selectors, MT5 order/account/history code, canaries, credentials, remote pushes, order behavior, production config, paid/API/Databento calls, broker actual-R, account history, live trade result labels, hidden outcome labels, master registries, or promotion dossiers. Do not set `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`. Do not score R/performance, win rate, expectancy, or blocked-packet outcomes. Preserve `NO_PROMOTION_VERDICT`.

## Stop Condition

The goal is complete only when every required count, overlap, source/no-leak, duplicate/sample-floor, blocker/reject, and label-meaning question has a committed artifact answer; every ambiguity is either resolved, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement; verification passes; and the completion audit states `can_mark_goal_complete=true`.
