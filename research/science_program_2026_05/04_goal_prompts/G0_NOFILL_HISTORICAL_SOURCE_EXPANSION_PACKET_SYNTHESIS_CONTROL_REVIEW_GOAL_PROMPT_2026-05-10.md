# G0 NOFILL Historical Source Expansion Packet Synthesis Control Review Goal Prompt

Date: 2026-05-10
Owner lane: G0 source/control synthesis and next-route selection
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW`.

The purpose is to synthesize the accepted G12 hash-repaired NOFILL historical source-expansion packet evidence and decide the next strongest source-safe route without opening validation, result scoring, or live behavior.

This route must not become a passive summary. It must use the newly accepted local data catalog tooling as mandatory active-worktree preflight, inspect the accepted packet chain, reconcile the two admitted source-bound rows, the `37` blockers, the `9` rejects, duplicate denominators `2/2/2`, source hashes, parser hashes, packet hash, no-leak posture, and closed validation gates, then produce an exact next-route decision.

Expected terminal decisions:

- `ACCEPT_AS_G0_SOURCE_EXPANSION_SYNTHESIS_FOR_NEXT_ROUTE`
- `ACCEPT_WITH_EXACT_SOURCE_EXPANSION_OR_CATALOG_REFRESH_FOLLOWUPS`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_CAPTURE_REQUIREMENTS`
- `REJECT_IF_SYNTHESIS_OPENS_FORBIDDEN_EVIDENCE_CLASS`

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

Do not rely on chat memory. If context compaction, restart, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the target artifacts, and continue from disk.

## Mandatory Catalog Refresh

Before accepting any data-absence, missing-window, prior-worktree, or local-heavy-data claim, run the accepted catalog builder in this active worktree:

`python research\science_program_2026_05\06_outcome_testing\gtos_local_research_data_catalog_implementation_route\build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py`

Then inspect the refreshed:

- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_2026-05-10.jsonl`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_2026-05-10.json`

Record a catalog-refresh ledger in this G0 route with active-worktree row/hash/deferral counts and any implications for the `37` source blockers.

Catalog presence is source-control metadata only. It is not validation-safe evidence, not a global proof of absence, and not permission to consume result/cost/broker/account/order/history/deal/position data.

For every one of the `37` blockers, record row-level catalog search evidence before assigning a final route class. The ledger must include searched symbols, dates, time windows, source families, roots consulted, positive evidence if found, negative evidence if not found, and the exact next acquisition/export/read-only extraction/source-capture action. A blocker cannot remain as generic `missing_data`, `not_local`, `worktree_absent`, or `n_too_small`.

## Controlling Inputs

Accepted upstream source packet and G12 repair chain:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/`

Accepted infrastructure inputs:

- `research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/`
- `research/science_program_2026_05/06_outcome_testing/g12_gtos_local_research_data_catalog_source_control_audit/`

Key accepted facts to reconcile:

- `2` admitted source-bound rows: `NAS100` at `2026-05-08T15:45:00Z`, `US30_cash` at `2026-05-08T13:45:00Z`.
- `37` blockers with exact source requirements.
- `9` rejects.
- Duplicate denominators `2/2/2`.
- Repaired packet hash: `5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341`.
- G12 repair verdict: `ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT`.
- Local data catalog G12 condition: rerun the catalog builder in the active consuming worktree before citing current paths or hashes.

## Required Outputs

Create a new route under:

`research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/`

Required artifacts:

1. Context anchor.
2. Decision ledger with terminal decision.
3. Evidence-chain reconciliation ledger.
4. Active-worktree catalog-refresh ledger.
5. Two-admitted-row source/control synthesis.
6. `37`-blocker route ledger with exact action class for every blocker.
7. `9`-reject learning ledger.
8. Duplicate/denominator and contamination/embargo readiness review.
9. No-leak/forbidden-route ledger.
10. Sealed-validation readiness and gap ledger.
11. Source-expansion opportunity ranking.
12. Parallelization decision ledger that says whether the next stage is one bottleneck route or multiple independent routes, with exact write-scope separation if parallelism is recommended.
13. Next-route prompt pack with one-line starter message(s), using the strongest prompt-file pattern and all hardening instructions.
14. Saturation/self-red-team pass.
15. Instruction-coverage checklist.
16. Completion audit with `can_mark_goal_complete`.
17. Builder, verifier, and focused tests.

## Synthesis Requirements

The synthesis must answer these questions with artifact-backed evidence:

1. What exactly did the accepted repaired source packet prove?
2. What did it not prove?
3. Are the two admitted rows sufficient for any validation lane? If not, why exactly and what source-safe expansion route is next?
4. Of the `37` blockers, which are recoverable market data, which are recoverable by owner export/read-only extraction, which are recoverable by source contract, and which are non-generatable historical GTOS source-state truth?
5. Do the refreshed catalog ledgers change any blocker route?
6. Are the `9` rejects permanently excluded from clean denominators or reusable in forensics/stress/source-contract fixtures?
7. What exact route should run next to maximize research output without crossing evidence-class boundaries?
8. Does the next route need one worktree or parallel routes?
9. What exact owner access/export/capture requirement remains, if any?
10. What remains forbidden?
11. Which blocker families can be pursued in parallel after this G0 synthesis without duplicating work or creating merge conflicts?
12. If sample size is too small for validation, what exact source-expansion/acquisition route increases eligible source-safe rows rather than stopping?
13. What did the negative/rejected evidence teach about future NOFILL, CNR, geometry, microstructure, behavioral, or ML hypothesis routes without opening scoring?

## Hardening Requirements

Do not stop at blocker labels. Within this G0 source/control synthesis evidence class, pursue every ambiguity until accepted, repaired, proven impossible from approved routes, or reduced to an exact owner/source/access/capture requirement.

Apply curiosity, truthfulness, and active creativity:

- Curiosity: look for overlooked source expansion paths, catalog-ledger implications, prior artifact reuse, alternate local roots, and clean partition opportunities.
- Truthfulness: do not inflate two rows into validation evidence, do not fake historical GTOS source-state truth from price data, and do not hide negative/rejected evidence.
- Activity/creativity: if the obvious next route is too narrow, design a stronger route that expands source-safe rows, clears blockers, or freezes sealed partitions without leaking outcomes.

Use the catalog tooling aggressively, but correctly. Worktree absence is not data absence. If data is not found, record searched roots and exact acquisition/capture requirement.

Small sample size is not a terminal reason to stop. If the current `2` admitted rows are insufficient for validation, the route must convert that fact into an exact expansion plan that uses catalog search, local-heavy-data roots, owner exports, read-only extraction, or forward source capture as appropriate. Only non-generatable historical GTOS source-state truth may remain impossible, and that must be proven with the accepted taxonomy.

The next-route recommendation must be executable immediately by the orchestrator. It must name route id, worktree folder suggestion, branch suggestion, write scope, required prompt file or prompt-pack path, one-line starter, expected terminal decisions, required counts to preserve, and what remains forbidden.

## Forbidden In This Route

- validation execution,
- result/cost/R/win-rate/expectancy scoring,
- broker actual-R,
- MT5 account/order/history/deal/position values,
- hidden result labels,
- promotion,
- registry edits,
- paid/API/Databento routes,
- remote push,
- live restart,
- live trading prompts,
- production trading logic,
- config/risk/permissions/safety/selectors/canaries,
- credentials,
- live trading behavior changes.

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Completion Standard

You may mark the goal complete only if:

- all required artifacts exist,
- the catalog builder was rerun in the active worktree and its implications were recorded,
- every accepted upstream count is reconciled or exact deviation is explained,
- all `37` blockers and `9` rejects have terminal G0 route classifications,
- each `37`-blocker classification includes active-worktree catalog search evidence or an exact reason catalog search is not applicable,
- the next route is exact enough to run without re-litigating the synthesis,
- a parallelization decision is recorded and justified,
- at least one one-line next starter is produced,
- verifier and focused tests pass,
- JSON/JSONL artifacts parse,
- forbidden-surface scans pass,
- research context is refreshed,
- commits are scoped to this G0 route and required context refresh only,
- completion audit says `can_mark_goal_complete=true`,
- and no unsafe flags or live/validation/scoring surfaces are opened.
