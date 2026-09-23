# GTOS Local Research Data Catalog Implementation Route Goal Prompt

Date: 2026-05-10
Owner lane: source-control/catalog tooling implementation
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`, the rank-1 follow-up from `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`.

The purpose is to turn the prototype 198-row local research data catalog into a reusable source-control catalog/search/missing-window/acquisition tool so future research sessions do not end with weak blockers like "data is not local" or "the worktree cannot see it".

This is a source-control/catalog tooling lane only. It must not execute validation, score result/cost/R/win-rate/expectancy, promote, edit registries, call paid/API routes, push remote, restart live processes, change live trading prompts, production trading logic, config/risk/permissions/safety/selectors/canaries, touch MT5 order/account/history/deal/position behavior, read broker actual-R, touch credentials, or change live trading behavior.

Expected terminal decisions:

- `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
- `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS`
- `REJECT_IF_TOOL_OPENS_FORBIDDEN_EVIDENCE_CLASS`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record current HEAD plus prompt path in a context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read latest route artifacts, and continue from disk.

## Controlling Inputs

Primary upstream route:

- `research/science_program_2026_05/06_outcome_testing/gtos_research_capability_limitation_closure_control_route/`
- `GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_2026-05-10.jsonl`
- `GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_SCHEMA_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_MARKET_DATA_ACQUISITION_LADDER_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_MISSING_WINDOW_LEDGER_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_WORKTREE_BOOTSTRAP_DATA_ROOT_RESOLVER_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_HISTORICAL_SOURCE_STATE_TRUTH_TAXONOMY_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_IMPLEMENTATION_DEPENDENCY_GRAPH_ROUTE_RANKING_2026-05-10.json`
- `GTOS_CAP_LIMIT_CLOSURE_NEXT_PROMPT_PACKS_2026-05-10.md`
- `GTOS_CAP_LIMIT_CLOSURE_VERIFICATION_RESULT_2026-05-10.json`

Current NOFILL source-expansion examples to use as acceptance fixtures:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/`

## Implementation Requirements

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/`

Build reusable route-local tooling, not live trading code. Prefer route-local Python scripts unless a repo-standard research tooling location already exists and is clearly non-live. The tool must be read-only.

Required capabilities:

1. Resolve data roots from a machine-readable config:
   - current worktree,
   - absolute main repo data root,
   - `data\ticks`,
   - `shadow_logs`,
   - `exports`,
   - `data\external`,
   - `C:\tmp\gtos_otb`,
   - `C:\SierraChart`,
   - other configured candidate roots if present.
2. Emit a catalog JSONL with one row per discovered source/control file.
3. Include at least:
   - root id,
   - absolute path,
   - relative path when inside a known root,
   - source family,
   - symbol if inferable,
   - date or date range if inferable,
   - timeframe if inferable,
   - file extension,
   - size,
   - mtime,
   - hash policy,
   - SHA256 when safe/size-bounded,
   - large-file hash deferral record when not hashing directly,
   - allowed evidence class,
   - forbidden-use notes.
4. Emit a search-result ledger for configured query patterns, including positive and negative evidence.
5. Emit a missing-window ledger for requested symbol/date/timeframe/source windows.
6. Emit an acquisition-request manifest for anything not found locally, with exact owner/export/API/read-only-extraction next action.
7. Separate recoverable market data from non-generatable historical GTOS source-state truth.
8. Never read broker account/order/history/deal/position values, credentials, or broker actual-R.
9. Never copy or modify large data files.
10. Preserve contamination/evidence-class boundaries: catalog presence does not make a file validation-safe.

## Required Artifacts

Required artifacts:

1. Context anchor.
2. Root resolver config/schema.
3. Catalog implementation decision ledger.
4. Catalog schema.
5. Catalog JSONL output from a bounded read-only scan.
6. Search-result ledger.
7. Missing-window ledger.
8. Acquisition-request manifest schema and example.
9. Recoverable-vs-non-generatable classification ledger.
10. Source hash/large-file hash-deferral manifest.
11. Forbidden-route/no-leak audit.
12. Integration guide for future goal prompts.
13. Next prompt pack for G12/source-control audit if needed.
14. Completion audit.
15. Builder/catalog CLI, verifier, and focused tests.

## Hardening Standard

Operate at maximum practical reasoning depth while staying inside source-control/catalog tooling.

Do not stop at a design document if safe route-local implementation is possible. Do not treat unreadable or missing roots as failure unless the catalog records the exact access/path issue. Do not let a missing root invalidate other roots. Do not hash huge files directly unless the tool has a bounded policy; record deferred hash requests instead.

The final tool must make future sessions more capable:

- no final "not local" blocker without searched roots and exact next action,
- no worktree-only blindness,
- no data-use promotion from mere catalog presence,
- no confusion between market data and historical source-state truth,
- no silent large-file copying,
- no credential/broker account/order/history leakage.

## Verification Requirements

Required verification:

- Parse every generated JSON/JSONL/Markdown artifact.
- Run the catalog/builder in read-only mode.
- Run route verifier and focused tests.
- Run `python -m py_compile` for new Python files. If Windows `__pycache__` friction blocks bytecode writing, use AST syntax fallback and record it explicitly.
- Run placeholder scan for `TBD`, `TODO`, `unknown`, `maybe`, `later`, and vague unresolved blockers in generated route artifacts.
- Run forbidden live-surface diff scan.
- Confirm safe flags remain closed.
- Run final `python scripts\generate_live_state.py` and read freshness.

## Completion Rules

Do not mark complete unless all are true:

- A reusable read-only local research data catalog tool exists or an exact implementation blocker is recorded.
- The tool outputs catalog, search, missing-window, acquisition-request, hash/deferral, and no-leak artifacts.
- The catalog separates recoverable market data from non-generatable historical source-state truth.
- Future goal prompts can cite the integration guide and use the catalog before declaring data missing.
- Verifier and focused tests pass.
- Scoped commits include artifacts, tooling, tests, and research-state refresh if the map changes.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.
