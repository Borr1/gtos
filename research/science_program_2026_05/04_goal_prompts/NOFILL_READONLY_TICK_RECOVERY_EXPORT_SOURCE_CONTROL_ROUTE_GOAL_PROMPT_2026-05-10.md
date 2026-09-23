# NOFILL Read-Only Tick Recovery Export Source-Control Route Goal Prompt

Date: 2026-05-10
Owner lane: source-control market-data recovery/export route
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`.

Use the accepted G12 audit of the NOFILL source-state gap closure route as the control input. Pursue the `31` market-data-only tick/export-dependent blocker rows and `22` grouped owner/export requests to proof-or-impossibility inside the market-data source-control evidence class. Recover already-local tick files when source-safe, hash every consumed source file, and create exact owner/export or read-only extraction requests for missing windows. Do not infer, backfill, or admit missing historical GTOS source-state truth from price movement.

This route must be aggressive in market-data recovery and strict at evidence boundaries. Do not stop at the existing owner/export manifest if a source-safe local file, prior worktree artifact, approved tick root, Sierra/vendor/cache source, or approved read-only market-data extraction route can recover the window. Conservatism applies to no-leak validity, forbidden broker/account/order/history/deal/position surfaces, source-state inference, validation, promotion, and live behavior, not to search breadth or recovery effort.

Standing owner intent for this route: the owner approves pursuing every source-safe market-data recovery action inside this prompt's evidence class. Do not stop at `OWNER_EXPORT_REQUIRED`, `approval_needed`, or `access_needed` if the needed action can be executed by searching local roots, using prior worktree/source artifacts, hashing existing files, running approved read-only market-data extraction, or requesting runtime approval for a source-safe command. Ask for the exact permission when the tool requires it, then continue. A remaining owner/export request is valid only after the route proves the source-safe recovery/extraction ladder is unavailable, impossible, outside this route, requires manual external export, or would cross a forbidden surface.

Expected terminal decisions:

- `ACCEPT_AS_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
- `ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS`
- `BLOCKED_BY_FORBIDDEN_EVIDENCE_CLASS`

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\research_current_state.md`.
9. Read `research\science_program_2026_05\06_outcome_testing\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_NEXT_ROUTE_RANKING_LEDGER_2026-05-10.json`.
10. Read `research\science_program_2026_05\06_outcome_testing\g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit\G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_2026-05-10.json`.
11. Rerun the accepted local catalog builder in this active worktree before any data-absence claim:

`python research\science_program_2026_05\06_outcome_testing\gtos_local_research_data_catalog_implementation_route\build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py`

Record active-worktree catalog row/hash/deferral counts and search implications for every requested symbol/date/window. Catalog presence is source-control metadata only.

## Required Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.json`

## Requirements

- Independently verify all `31` tick/export-dependent blocker rows and all `22` grouped market-data owner/export requests.
- Search current worktree, absolute main repo roots, prior worktrees, approved tick roots, configured local-heavy roots, Sierra/vendor/cache roots if available, and accepted catalog outputs before declaring any window absent.
- Apply a row/window-level recovery ladder: existing source-safe local file -> prior worktree/source artifact -> approved tick root -> Sierra/vendor/cache source -> approved read-only market-data extraction route -> exact owner/export request.
- Do not create a final owner/export request until the earlier recovery ladder steps are ledgered as recovered, not applicable, or absent.
- If local tick data is found, copy nothing unless necessary; hash the exact source file, record path, size, schema, symbol, date, and field coverage.
- File presence is not enough. For every recovered tick source, verify timestamp column semantics, UTC/window coverage, row count inside the requested UTC window, bid/ask/last/volume/flags field availability where applicable, min/max timestamp, and symbol/broker-symbol compatibility. Record whether the file fully covers, partially covers, or does not cover each requested row/window.
- If approved read-only market-data extraction is available and source-safe, attempt it or produce an exact extraction command/manifest with approval/access status. Read-only market-data extraction must not read MT5 account/order/history/deal/position values, broker actual-R, results, costs, or hidden labels.
- If read-only extraction requires runtime approval, request the approval and continue; do not mark the goal complete merely because approval was needed. If approval is denied or the extraction cannot run in the environment, ledger that exact fact with command/source/window/error details and the remaining owner action.
- If local/read-only recovery is still missing, write an exact owner/export request with symbol/source symbol, UTC window, fields, format, target path template, no-leak constraints, and hash requirement.
- Preserve the source-state boundary: recovered ticks do not admit any row until pending lifecycle/write-clock/order-observability/source-state truth exists through source-safe logs or prospective capture.
- Keep contamination/embargo rows excluded from clean denominators.
- Produce a context anchor, G12 input ingestion ledger, active catalog refresh/search ledger, row/window recovery ladder ledger, source hash manifest, recovered/absent window ledger, grouped request reconciliation ledger, owner action manifest, no-leak audit, large-file/staging policy audit, next G12 audit prompt pack with one-line starter, full next G12 controlling prompt under `research/science_program_2026_05/04_goal_prompts/`, builder, verifier, focused tests, and completion audit.
- If any requested full-day source file covers multiple blocker rows, reconcile row coverage without double-counting and preserve the `31` row / `22` grouped request distinction.
- If a file is too large for full hash under route constraints, create a large-file deferral record with path, size, mtime, source, partial/schema proof, and exact next hash action. Do not silently consume un-hashed large files as accepted source evidence.
- Do not commit recovered raw tick/parquet/CSV market-data files, especially files near or above GitHub's large-file limit. Commit manifests, hashes, schemas, coverage ledgers, and extraction/export requests only. If a recovered file must be materialized locally, place it in an approved data/cache path and record it in manifests; verify it is not staged.
- Check alias compatibility explicitly for broker/source symbols such as `US30` versus `US30_cash`; do not treat an alias as equivalent unless the source contract or catalog evidence supports it.
- If a requested window has zero market ticks because of non-trading/session closure, record market-session/source-control proof separately from missing-data proof.

## Forbidden

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

## Completion Standard

Mark complete only when all `31` rows are either source-hashed as recovered market-data files with verified requested-window coverage, covered by large-file deferral records with exact next hash action, proven market-session empty with source-control evidence, or have exact export/read-only-extraction requests after all executable source-safe recovery/extraction/approval paths were pursued; all `22` grouped requests reconcile without duplicate or missing row coverage; the active catalog rerun and recovery ladder are ledgered; no source-state truth is inferred; contamination/embargo rows remain excluded; next G12 audit prompt pack, one-line starter, and full controlling prompt file exist; all JSON/JSONL artifacts parse; verifier/tests pass; staged/committed diff contains no raw large market-data files; research context is refreshed; commits are scoped; and completion audit says `can_mark_goal_complete=true` with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
