# NOFILL Historical Source Expansion Packet Parser Hash Repair Rebuild Goal Prompt

Date: 2026-05-10
Owner lane: source/control repair rebuild
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Repair only the exact parser/verifier hash blockers found by G12 for `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`.

The G12 audit accepted the target packet controls except for `3` strict parser/verifier hash mismatches. This route must refresh the target source-hash manifest and packet parser-code hash bindings so they match current committed target code, rerun target verifier/tests, and produce a repair evidence pack for G12 repair reaudit.

This route must not admit new rows, remove rows, change candidate semantics, open validation, score outcomes, compute R, compute win rate, compute expectancy, compute costs, open slippage/execution-quality labels, read broker actual-R, read MT5 account/order/deal/position/history values, promote, edit registries, call paid/API routes, push remote, restart live processes, change prompts/config/risk/permissions/safety/selectors/canaries/MT5 behavior, touch credentials, or change live trading behavior.

Expected terminal decisions:

- `REPAIR_REBUILD_READY_FOR_G12_REAUDIT`
- `BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY`
- `REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS`

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

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read target/G12 artifacts, and continue from disk.

## Controlling Inputs

G12 audit route:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_HASH_PARSER_HASH_AUDIT_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_TARGET_VERIFIER_TEST_RERUN_REPORT_2026-05-10.json`
- `G12_NOFILL_HIST_SRCEXP_AUDIT_VERIFICATION_RESULT_2026-05-10.json`

Target packet route to repair:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_55_FIELD_BINDING_CHECKLIST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-10.json`
- target builder, verifier, and focused test files in the same directory

Exact G12 repair requirements:

- Builder file current strict SHA256 must replace stale manifest/parser hash:
  - path: `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py`
  - stale manifest hash: `3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4`
  - G12 recomputed hash: `0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b`
- Focused test file current strict SHA256 must replace stale manifest hash:
  - path: `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py`
  - stale manifest hash: `209f51ac1400e2dcb3d9eb0528a2bbcec1c95dfa3749b867d379f8ab18455567`
  - G12 recomputed hash: `472dd4b2be228bac59017b4aabb5934dfe150819fdc8007bcd08a9fa38ab75e1`
- Verifier file current strict SHA256 must replace stale manifest hash:
  - path: `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py`
  - stale manifest hash: `4a750bdf1fdb4c016c01fac04d69bbd40ee991275ad42bdb2ea1430ec5d333da`
  - G12 recomputed hash: `ebeae4746221ff30a968a41ef8a938bb15d6f1a1f9fc346621ccae6dcfbf9ea5`

Recompute these hashes from disk before using the values above. If recomputed hashes differ from the G12 values because files changed after the audit, record the new hashes and explain exactly why; do not hard-code stale assumptions.

## Hardening Standard

Operate at maximum practical reasoning depth, but stay narrowly inside this source/control repair class. This is not a chance to re-design the packet or add rows.

Required posture:

- Repair all exact hash blockers, not just document them.
- Preserve the target packet's semantic facts:
  - exactly `2` admitted rows,
  - rows remain `NAS100 2026-05-08T15:45:00Z` and `US30_cash 2026-05-08T13:45:00Z`,
  - `37` blocked candidates and `9` rejects remain unchanged unless the repair would otherwise be false; if a count changes, stop and classify as `REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS`,
  - no validation/result/cost labels open,
  - source hashes for raw tick/shadow files remain unchanged unless current files truly changed; mutable shadow-log drift must be separated from strict parser/verifier repair.
- Update all derived target artifacts affected by parser hash changes, including packet row `parser_code_hash` fields, source-hash manifest records, packet manifest packet hash, verification result, and any explicit hash summary ledgers.
- Produce a repair evidence pack so G12 can verify the fix without relying on chat memory.

## Required Repair Artifacts

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/`

Required artifacts:

1. Context anchor.
2. Repair decision ledger.
3. Exact G12 blocker closure ledger for the `3` strict hash mismatches.
4. Target artifact mutation ledger listing every target packet file changed and why.
5. Semantic no-row-change diff ledger proving only hash/derived-manifest fields changed.
6. Recomputed parser/verifier/source hash manifest.
7. Recomputed packet manifest and packet SHA ledger.
8. Target verifier/test rerun report.
9. No-leak/safe-flag check.
10. Next G12 repair reaudit prompt pack.
11. Completion audit.
12. Repair builder/verifier/focused tests if useful; at minimum include a verifier and focused tests for the repair route.

## Verification Requirements

Required verification:

- Parse all changed/generated JSON/JSONL/Markdown artifacts.
- Recompute strict SHA256 for builder/test/verifier and prove manifest matches.
- Recompute target candidate packet hash and prove packet manifest matches.
- Prove target packet still has exactly `2` rows and the same row identities.
- Prove blocked/rejected counts remain `37` and `9`.
- Prove `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Rerun target verifier and focused pytest.
- Run repair verifier and focused pytest.
- Run `python -m py_compile` for changed/new Python files. If Windows `__pycache__` friction blocks bytecode writing, use AST syntax fallback and record it explicitly.
- Run committed-diff forbidden live-surface scan.
- Run final `python scripts\generate_live_state.py` and read freshness.

## Completion Rules

Do not mark complete unless all are true:

- All three G12 exact hash repair requirements are closed or proven impossible.
- No packet semantic field changed outside hash/derived-manifest fields.
- No new rows are admitted and no rows are removed.
- Target verifier and target focused tests pass.
- Repair verifier and repair focused tests pass.
- Next G12 repair reaudit prompt pack exists.
- Scoped commits include target repair artifacts, repair evidence pack, verifier/tests, and research-state refresh if the map changes.
- No validation execution, result/cost/R/win-rate/expectancy scoring, promotion, registry edit, paid/API route, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary/MT5 order-account-history behavior, broker actual-R read, credential, or live trading behavior change occurs.
