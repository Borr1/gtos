# GTOS Research Capability Limitation Closure Control Route Goal Prompt

Date: 2026-05-10
Owner lane: research infrastructure / methodology limitation closure
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build a durable research-infrastructure control route that attacks the current workflow limitations directly instead of handling them ad hoc.

The owner goal is maximum research capability: future GTOS research should not end with weak blockers such as "data is not local", "there is no data", "the worktree cannot see it", or "the category is blocked" unless the session has exhausted or exactly routed every approved acquisition/reconstruction/capture path.

This goal must pursue solutions for all seven limitation families:

1. Market data absence.
2. Historical GTOS intent/source-state absence.
3. Contamination/embargo rejects.
4. Worktree blindness.
5. Evidence-class gate friction.
6. Data catalog weakness.
7. Parser/hash drift.

This is a research/tooling/control lane only. It may build source-safe research utilities, schemas, ledgers, prompt packs, verifiers, and tests. It must not open validation execution, result/cost/R/win-rate/expectancy scoring, promotion, registry edits, paid/API routes, remote push, live restart, live trading prompts, production trading logic, config/risk/permissions/safety/selectors/canaries, MT5 order/account/history/deal/position behavior, broker actual-R reads, credentials, or live trading behavior.

Expected terminal decisions:

- `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
- `ACCEPT_WITH_EXACT_IMPLEMENTATION_OR_ACCESS_ROUTES`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS`
- `REJECT_IF_ROUTE_OPENS_FORBIDDEN_EVIDENCE_CLASS`

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

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read latest lane artifacts, and continue from disk.

## Controlling Context To Inspect

Inspect the current NOFILL source-expansion chain as a concrete example of the limitations:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/`
- `research/science_program_2026_05/04_goal_prompts/G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_HASH_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-10.md`

Also inspect the standing hardening docs:

- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/local_heavy_data_inventory.md`
- `.context/00_core/research_operating_doctrine.md`

Search prior artifacts for recurring examples of data absence, worktree blindness, source-state absence, contamination/embargo, evidence-class gate handoff, parser/hash repair, Windows pycache friction, and dirty-main verifier noise.

## Required Solution Families

### 1. Market Data Absence

Build or specify a reusable data acquisition ladder that prevents "data not local" from becoming a final blocker.

Required outputs:

- source/acquisition ladder ledger,
- exact local root search policy,
- read-only extraction route templates for MT5 tick/bar windows,
- Sierra/vendor/cache search policy,
- network/API/vendor pre-call manifest schema with cost/free-credit/approval/no-leak fields,
- exact blocker vocabulary distinguishing recovered, recoverable-by-owner-action, recoverable-by-approved-extraction, and truly unavailable.

If safe and scoped, build a prototype local source inventory scanner under the route directory that indexes configured roots by symbol/date/source/file/hash without reading forbidden broker/account/order/history values.

### 2. Historical GTOS Intent / Source-State Absence

Freeze a classifier that separates recoverable market data from non-generatable historical GTOS state.

Required outputs:

- source-state truth taxonomy,
- list of non-generatable historical fields,
- recovery search path for existing source-safe logs/artifacts,
- forward-capture requirement mapping for fields that cannot be reconstructed,
- rule that price movement cannot backfill historical intent/order/lifecycle truth.

### 3. Contamination / Embargo Rejects

Design a reusable partition and contamination router so rejected rows are not wasted.

Required outputs:

- contamination/embargo state machine,
- routes for rejected rows: discovery-only, forensics-only, source-contract fixture, stress/control, sealed-validation excluded,
- sealed-partition expansion plan that finds untouched rows/windows/symbols/sessions instead of trying to reuse dirty rows,
- denominator guard so rejects cannot leak into labels, counts, validation, or promotion.

### 4. Worktree Blindness

Design a worktree bootstrap and data-root resolver.

Required outputs:

- worktree preflight checklist,
- absolute data-root resolver schema,
- prior-worktree/cache search policy,
- safe symlink/copy/reference guidance if needed,
- rule that worktree-local absence is only an intermediate state.

### 5. Evidence-Class Gate Friction

Improve the chain without weakening it.

Required outputs:

- evidence-class router describing when to continue inside the same goal and when to split,
- anti-lazy blocker rule,
- "fast narrow audit" template for obvious G12/G0 facts,
- exact handoff artifact requirements that let the next gate start from machine-checkable state,
- guidance for preserving speed without collapsing source proof into result labels.

### 6. Data Catalog Weakness

Design or build the first version of a GTOS local research data catalog.

Required outputs:

- catalog schema by root/source/symbol/date/timeframe/window/file/hash/lineage/as-of/allowed-evidence-class,
- source hash policy,
- search result ledger format,
- missing-window ledger format,
- acquisition request manifest format,
- next implementation prompt pack if the prototype cannot be completed safely inside this goal.

If safe and scoped, build a read-only prototype that scans selected roots and emits a catalog artifact under this route. It must not copy large files, touch credentials, query broker account/order/history, or call paid/API routes.

### 7. Parser / Hash Drift

Create a stable manifest and hash-policy control plan.

Required outputs:

- raw SHA versus LF-normalized text SHA policy,
- binary/text artifact gate,
- mutable-context classification,
- strict parser/test/verifier hash policy,
- generated-artifact regeneration policy,
- verifier self-check pattern that detects stale parser hashes without causing false failures from `.context/LIVE_STATE.md`,
- next repair route template if drift occurs.

## Required Artifacts

Create a route under:

`research/science_program_2026_05/06_outcome_testing/gtos_research_capability_limitation_closure_control_route/`

Required artifacts:

1. Context anchor.
2. Limitation decision ledger covering all seven families.
3. Market-data acquisition ladder and manifest schema.
4. Historical source-state truth taxonomy.
5. Contamination/embargo router and sealed-partition expansion plan.
6. Worktree bootstrap/data-root resolver design.
7. Evidence-class router and fast-audit template.
8. Local research data catalog schema and, if safe, prototype scanner output.
9. Parser/hash drift control policy.
10. Forbidden-route ledger.
11. Implementation dependency graph and route ranking.
12. Next prompt pack(s) for follow-up implementation lanes.
13. Completion audit.
14. Builder/verifier/focused tests or strongest equivalent for generated machine-readable artifacts.

## Hardening Standard

Operate at maximum practical reasoning depth and take as much time as needed inside the hard safety boundaries.

Do not stop at a written plan if safe same-evidence-class tooling can be built. Do not claim a limitation is solved by wording alone unless a concrete prompt/control/tooling route exists. If a solution requires owner approval, source access, external export, or future live capture, write the exact approval/action manifest.

Every limitation must end in one of:

- closed by durable workflow/context/tooling,
- closed by a prototype verifier/catalog/control artifact,
- routed to a named implementation prompt,
- routed to exact owner/access/source/export requirement,
- proven impossible because it would require fabricating non-generatable historical source truth,
- forbidden because it crosses validation/result/live/promotion boundaries.

## Verification Requirements

Required verification:

- Parse every generated JSON/JSONL/Markdown artifact.
- Run verifier and focused tests for the route.
- Run `python -m py_compile` for new Python files. If Windows `__pycache__` friction blocks bytecode writing, use AST syntax fallback and record it explicitly.
- Run placeholder scan for `TBD`, `TODO`, `unknown`, `maybe`, `later`, and unresolved vague blockers in generated route artifacts.
- Run forbidden live-surface diff scan.
- Confirm all seven limitation families are explicitly covered.
- Confirm no artifact opens validation/result/cost/live/promotion flags.
- Run final `python scripts\generate_live_state.py` and read freshness.

## Completion Rules

Do not mark complete unless all are true:

- All seven limitation families have exact solution routes, artifacts, and either closure, prototype, or next implementation prompt.
- No final blocker says only "data not local" or "no data" without the acquisition ladder and exact next action.
- Recoverable market data and non-generatable historical source truth are explicitly separated.
- A local research data catalog path is either prototyped or routed to a precise next implementation prompt.
- Forward capture fixes are specified for historical source-state gaps.
- Parser/hash drift policy is machine-checkable enough for future G12 use.
- Scoped commits include artifacts, verifier/tests where useful, and research-state/context refresh if the map changes.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.
