# G12 NOFILL Historical Source Expansion Packet Hash Repair Reaudit Goal Prompt

Date: 2026-05-10
Owner lane: G12 source/control repair reaudit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 repair reaudit of `NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD`.

The prior G12 audit accepted the source/control packet controls except for three strict parser/verifier hash mismatches. The repair route reports all three blockers closed while preserving the target packet semantics: exactly `2` admitted rows, `37` blocked candidates, and `9` rejects.

This G12 route must verify that claim independently. It must not admit rows, remove rows, change packet semantics, open validation, score outcomes, compute R, compute win rate, compute expectancy, compute costs, open slippage/execution-quality labels, read broker actual-R, read MT5 account/order/deal/position/history values, promote, edit registries, call paid/API routes, push remote, restart live processes, change prompts/config/risk/permissions/safety/selectors/canaries/MT5 behavior, touch credentials, or change live trading behavior.

Expected terminal decisions:

- `ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT`
- `ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS`
- `REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS`
- `BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record exact HEAD and prompt path in a context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read target/G12/repair artifacts, and continue from disk.

## Controlling Inputs

Repair route:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_DECISION_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_EXACT_G12_BLOCKER_CLOSURE_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_RECOMPUTED_SOURCE_HASH_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_PACKET_SHA_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_TARGET_VERIFIER_TEST_RERUN_REPORT_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_NOLEAK_SAFE_FLAG_CHECK_2026-05-10.json`
- `NOFILL_HIST_SRCEXP_HASH_REPAIR_COMPLETION_AUDIT_2026-05-10.json`
- repair builder, verifier, and focused tests

Target source-expansion packet after repair:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-10.json`
- target builder, verifier, and focused tests

Prior G12 audit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_HASH_PARSER_HASH_AUDIT_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json`

## Hardening Standard

Operate at maximum practical reasoning depth while staying narrowly inside G12 source/control repair reaudit.

Required adversarial checks:

- Recompute builder, focused-test, and verifier SHA256 from disk and prove they match the repaired manifest.
- Prove all packet row `parser_code_hash` fields now bind the repaired builder hash or the explicitly accepted parser-code hash convention.
- Recompute target packet hash and prove packet manifest matches.
- Prove semantic no-row-change:
  - exactly `2` admitted rows,
  - same row IDs and candidate IDs,
  - same symbols/timestamps: `NAS100 2026-05-08T15:45:00Z`, `US30_cash 2026-05-08T13:45:00Z`,
  - exactly `37` blocked candidates,
  - exactly `9` rejects,
  - duplicate denominators still `2/2/2`,
  - no new source rows, labels, or validation rows.
- Rerun target verifier and target focused tests from current disk.
- Rerun repair verifier and repair focused tests from current disk.
- Recheck safe flags and no-leak boundaries.
- Verify no live-surface or prompt/config/risk/safety changes were made by the repair.

If the repair did more than hash/derived-manifest updates, stop and classify precisely. Do not force acceptance.

## Required Reaudit Artifacts

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/`

Required artifacts:

1. Context anchor.
2. Decision ledger.
3. Exact blocker closure reaudit.
4. Repaired source-hash/parser-hash recomputation audit.
5. Semantic no-row-change reaudit.
6. Packet hash/manifest reaudit.
7. Target verifier/test rerun audit.
8. Repair verifier/test rerun audit.
9. No-leak/safe-flag/live-surface audit.
10. Future route eligibility ledger.
11. Next prompt pack for the correct next route.
12. Completion audit.
13. Builder, verifier, and focused tests for this G12 route.

## Verification Requirements

Required verification:

- Parse all generated JSON/JSONL/Markdown artifacts.
- Recompute strict SHA256 for target builder/test/verifier and prove closure of the prior `3` blockers.
- Recompute target packet hash.
- Confirm exact packet counts `2 / 37 / 9`.
- Confirm no validation/result/cost/live flags opened.
- Run target verifier and target focused pytest.
- Run repair verifier and repair focused pytest.
- Run new G12 verifier and focused pytest.
- Run `python -m py_compile` for new Python files. If Windows `__pycache__` friction blocks bytecode writing, use AST syntax fallback and record it explicitly.
- Run committed-diff forbidden live-surface scan.
- Run final `python scripts\generate_live_state.py` and read freshness.

## Completion Rules

Do not mark complete unless all are true:

- The prior three exact parser/verifier hash blockers are independently closed or exact remaining blockers are recorded.
- Packet semantics are unchanged.
- Target verifier/tests pass.
- Repair verifier/tests pass.
- G12 verifier/tests pass.
- A next route prompt pack exists.
- Scoped commits include artifacts, builder, verifier, tests, and research-state refresh if the map changes.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.
