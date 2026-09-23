# G12 GTOS Local Research Data Catalog Source-Control Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source-control/catalog tooling audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE` as source-control/catalog tooling only.

The purpose is to decide whether the local catalog/root-resolver/search/missing-window/acquisition tooling is reliable enough for future research sessions to cite before declaring data absent, worktree-blind, recoverable-by-export, or non-generatable historical source-state truth.

This audit must be adversarial and complete. Do not rubber-stamp the implementation because its own verifier passed. Recompute counts, schemas, flags, no-leak boundaries, root coverage, missing-window routing, acquisition-request routing, hash/large-file deferral logic, and integration instructions from source artifacts. Pursue every same-evidence-class ambiguity until accepted, repaired, impossible from approved routes, or reduced to an exact owner/source/access requirement.

This is not a validation, scoring, promotion, registry, live, paid/API, or broker-account lane.

Terminal decision options:

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

Do not rely on chat memory. If context compaction, restart, or uncertainty occurs, regenerate live state, re-read this prompt and the core context docs, re-read the target artifacts, and continue from disk.

## Target Artifacts

Audit this implementation route:

`research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/`

Required target artifacts include:

- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_2026-05-10.jsonl`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_SCHEMA_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_ROOT_RESOLVER_CONFIG_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_ROOT_RESOLVER_CONFIG_SCHEMA_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_HASH_DEFERRAL_MANIFEST_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_FORBIDDEN_ROUTE_NOLEAK_AUDIT_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_INTEGRATION_GUIDE_2026-05-10.md`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_COMPLETION_AUDIT_2026-05-10.json`
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_VERIFICATION_RESULT_2026-05-10.json`
- target builder, verifier, and focused tests.

Expected target summary from the completed route: `1200` bounded catalog rows, `1076` small-file SHA256 hashes, `124` large-file deferrals, `6` configured search queries, `2` positive search evidence rows, `4` negative search evidence rows, `22` recoverable market-data windows, `20` non-generatable GTOS source-state gaps, and `42` manifest-only acquisition/capture requests.

## Required Audit Work

Build a new independent G12 route under:

`research/science_program_2026_05/06_outcome_testing/g12_gtos_local_research_data_catalog_source_control_audit/`

Required outputs:

1. Context anchor with HEAD, prompt path, target route path, and target commits.
2. Decision ledger with terminal decision and exact reasons.
3. Root resolver/config/schema audit.
4. Catalog row/count/schema audit.
5. Search-result and missing-window routing audit.
6. Acquisition manifest and recoverable-vs-non-generatable classification audit.
7. Hash/large-file deferral audit.
8. No-leak/forbidden-route audit.
9. Integration-guide usability audit for future goal prompts.
10. Saturation/self-red-team ledger with explicit attempts to break the route.
11. Exact repair/followup/source-request ledger, even if empty.
12. Completion audit with `can_mark_goal_complete`.
13. Independent verifier and focused tests.

Minimum checks:

- Parse all target JSON/JSONL artifacts.
- Recompute target catalog row count and hash/deferral counts.
- Verify all catalog rows remain source-control/catalog metadata only.
- Verify large-file rows are deferred rather than copied, modified, or weakly consumed.
- Verify root resolver records absolute-heavy-data awareness and does not confuse worktree absence with data absence.
- Verify recoverable market-data windows are not mislabeled as non-generatable source-state truth.
- Verify non-generatable historical GTOS source-state gaps are not faked from price movement.
- Verify acquisition requests are manifest-only and do not call paid/API/Databento or broker account/order/history/deal/position routes.
- Verify no broker actual-R, credentials, account IDs, raw ticket IDs, order/deal/position labels, result/cost/R/win-rate/expectancy fields, validation-safe flips, promotion flags, registry edits, remote pushes, live restarts, prompt/config/risk/permission/safety/selector/canary changes, or live trading behavior changes.
- Rerun target verifier and target focused tests if possible.
- Run new G12 verifier and focused tests.
- Run syntax check via `python -m py_compile`; if Windows `__pycache__` friction blocks bytecode, record it and use AST syntax fallback.
- Regenerate `.context\LIVE_STATE.md` at closeout and verify research freshness.

## Hardening Requirements

Do not stop at a blocker label. If an issue is inside source-control/catalog evidence class, pursue it in the same session until repaired, accepted, rejected, impossible from approved routes, or reduced to an exact owner/source/access requirement.

Apply curiosity, truthfulness, and active creativity:

- Curiosity: look for hidden weakness in root coverage, missing windows, large-file policy, source-state taxonomy, and future prompt usability.
- Truthfulness: do not fake catalog coverage, do not infer historical source-state truth from price data, and do not call catalog presence validation evidence.
- Activity/creativity: if the obvious check is insufficient, create additional source-safe audits or fixture probes inside the scoped G12 route.

Preserve scope exactly:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Forbidden in this route:

- validation execution,
- result/cost/R/win-rate/expectancy scoring,
- promotion,
- registry edits,
- paid/API/Databento routes,
- remote push,
- live restart,
- live trading prompts,
- production trading logic,
- config/risk/permissions/safety/selectors/canaries,
- MT5 order/account/history/deal/position behavior,
- broker actual-R,
- credentials,
- live trading behavior changes.

## Completion Standard

You may mark the goal complete only if:

- every required artifact exists,
- all target and G12 JSON/JSONL artifacts parse,
- expected target counts are independently reconciled or exact deviations are explained,
- verifier and focused tests pass or exact environment-only friction is recorded with an accepted fallback,
- forbidden-surface scans pass,
- completion audit says `can_mark_goal_complete=true`,
- research context is refreshed,
- commits are scoped to this G12 audit route and required context refresh only,
- no unsafe flags are opened,
- and any remaining issue is exact, actionable, and not a lazy missing-data/worktree-blind blocker.
