# G12 NOFILL Historical Source Expansion Packet Audit Goal Prompt

Date: 2026-05-10
Owner lane: G12 source/control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 source/control audit of `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`.

The target route built a local tick/shadow source-expansion packet with `2` admitted source-bound rows, `37` exact blocked candidates, and `9` rejects. G12 must independently determine whether those admitted rows are accepted as source-control input evidence for a future sealed-validation packet lane, whether any blocker/reject status is wrong or under-pursued, and whether any repair/source requirement remains.

This is not validation execution. It must not score outcomes, compute R, compute win rate, compute expectancy, compute costs, open slippage/execution-quality labels, read broker actual-R, read MT5 account/order/deal/position/history values, promote, edit registries, call paid/API routes, push remote, restart live processes, change prompts/config/risk/permissions/safety/selectors/canaries/MT5 behavior, touch credentials, or change live trading behavior.

Expected terminal decisions:

- `ACCEPT_AS_G12_SOURCE_CONTROL_PACKET_FOR_FUTURE_SEALED_VALIDATION_ROUTE`
- `ACCEPT_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENT`
- `REJECT_INVALID_SOURCE_EXPANSION_PACKET`

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

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read target route artifacts, and continue from disk.

## Controlling Inputs

Target source-expansion packet route:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_DECISION_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_SOURCE_INVENTORY_SEARCH_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_CONTAMINATION_PURGE_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_55_FIELD_BINDING_CHECKLIST_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_FUTURE20_EXTRACTION_FAIL_CLOSED_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_FORBIDDEN_REDACTED_STATUS_AUDIT_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_NOLEAK_AUDIT_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json`
- `NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.json`
- target builder, verifier, and focused test files in the same directory

Parent accepted route chain:

- `g0_nofill_historical_partition_source_binding_synthesis_control_review/`
- `g12_nofill_historical_sealed_validation_partition_source_binding_audit/`
- `nofill_historical_sealed_validation_partition_and_source_binding/`
- `g12_nofill_cat_v3_source_control_audit/`
- `nofill_cat_v3_source_control_rebuild/`

Approved local evidence class for audit only:

- current committed target route artifacts
- hash-recomputed local source files cited by the target route
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`

Do not admit new packet rows in this G12 route. If G12 discovers a possible omitted row, record it as an exact repair/source-expansion requirement for a separate builder route.

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, activity, and creativity, while staying in G12 source/control audit only.

Do not rubber-stamp the two rows. Independently recompute or adversarially verify:

- the two admitted rows are exactly `NAS100 2026-05-08T15:45:00Z` and `US30_cash 2026-05-08T13:45:00Z`,
- packet SHA256 and row count,
- source hashes for tick/shadow/parser/builder/verifier artifacts,
- source-date contamination and one-day same-symbol/source-lane embargo exclusion,
- duplicate keys and duplicate groups,
- 55/55 field presence and accepted field categories,
- future-20 extraction or fail-closed statuses,
- forbidden/redacted status-only fields,
- no result/cost/R/win-rate/expectancy/slippage/execution-quality/broker actual-R/account/order/deal/position/history leakage,
- `37` blocked candidates and `9` rejects have exact, defensible reasons,
- route-level impossibility is not hiding a source-safe route that should have been pursued.

If any issue appears, pursue it inside G12 audit evidence until cleared, proven impossible from approved routes, or reduced to exact repair/source/capture requirements. Do not stop at shallow blocker labels.

## Required Audit Artifacts

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/`

Required artifacts:

1. Context anchor.
2. Decision ledger.
3. Source packet row recomputation audit.
4. Source hash and parser hash audit.
5. Contamination/purge/embargo audit.
6. 55-field binding audit.
7. Future-20 extraction/fail-closed audit.
8. Forbidden/redacted/no-leak audit.
9. Duplicate denominator audit.
10. Blocker/reject exactness audit for the `37` blocked and `9` rejected candidates.
11. Saturation/adversarial issue ledger.
12. Exact repair/source requirement ledger.
13. Future-route eligibility ledger describing what may happen after G12 acceptance, while keeping validation closed.
14. Next prompt pack for the correct next route.
15. Completion audit.
16. Builder, verifier, and focused tests.

## Verification Requirements

Required verification:

- Parse all generated JSON/JSONL/Markdown artifacts.
- Recompute or directly verify the candidate packet row count is `2`.
- Verify packet rows remain source/control only and contain no forbidden result/cost/live fields.
- Recompute strict source hashes where possible; classify only mutable context drift separately.
- Verify target builder/verifier/test files exist and are committed.
- Run target verifier and target focused pytest.
- Run new G12 verifier and focused pytest.
- Run `python -m py_compile` for new Python files. If Windows `__pycache__` friction blocks bytecode writing, use AST syntax fallback and record it explicitly.
- Run committed-diff forbidden live-surface scan.
- Run final `python scripts\generate_live_state.py` and read freshness.

## Completion Rules

Do not mark complete unless all are true:

- G12 terminal decision is explicit.
- Two admitted rows are independently audited.
- `37` blocked and `9` rejected candidates are audited for exactness.
- No validation execution, result/cost scoring, promotion, registry edit, paid/API route, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary/MT5 order-account-history behavior, credential, or live trading behavior change occurs.
- Verifier and focused tests pass or failures are reduced to exact environmental friction with alternate verification.
- Scoped commits include artifacts, builder, verifier, tests, and research-state refresh if the map changes.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.
