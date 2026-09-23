# XAUUSD 2026-04-15/16 Sierra SCID Alternate Source-Control Route Goal Prompt

Date: 2026-05-10
Owner lane: source/control alternate-source recovery
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`.

This route follows the accepted G12 NOFILL read-only tick recovery audit. The MT5 bid/ask tick recovery route recovered `20/22` grouped windows covering `28/31` candidate rows. The two remaining exact MT5 requests are:

- `OWNER-TICK-0020`: `XAUUSD`, `2026-04-15`, candidate `XAUUSD_2026-04-15T14:15:05.007998+00:00`.
- `OWNER-TICK-0021`: `XAUUSD`, `2026-04-16`, candidates `XAUUSD_2026-04-16T09:30:05.013547+00:00` and `XAUUSD_2026-04-16T13:16:01.126537+00:00`.

The G12 audit found local `C:\SierraChart\Data\XAUUSD.scid` coverage for both remaining UTC dates (`72,119` rows on `2026-04-15`; `70,048` rows on `2026-04-16`), which rules out a market-closed explanation but does not by itself satisfy the MT5 bid/ask tick parquet contract.

Your task is to parse and audit that SCID source read-only, then produce either:

1. a source-hashed alternate-source packet with exact admissibility boundaries, if the SCID evidence satisfies a frozen alternate-source contract; or
2. exact field-mismatch/source-contract blockers plus owner/manual export instructions, if SCID cannot satisfy the required fields.

Do not infer GTOS source-state truth from price. Do not score outcomes. Do not open validation. Do not commit raw SCID-derived exports.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\research_current_state.md`.
9. Read the accepted G12 audit artifacts under `research\science_program_2026_05\06_outcome_testing\g12_nofill_readonly_tick_recovery_export_source_control_audit\`.
10. Read the target route artifacts under `research\science_program_2026_05\06_outcome_testing\nofill_readonly_tick_recovery_export_source_control_route\`.
11. Read existing Sierra SCID tooling before writing new parsing code: `scripts\inspect_sierra_scid.py`, `scripts\convert_sierra_scid_to_ohlcv.py`, and their focused tests.

## Required Source Pursuit

- Locate `C:\SierraChart\Data\XAUUSD.scid`. If that exact file is absent or sandbox-blocked, search approved Sierra roots and prior worktree/source artifacts, then request access and continue if the action is source-control safe.
- Hash the raw SCID file with SHA256, size, header metadata, record count, first/last timestamp, and parser code hash.
- Parse only the required source windows read-only. Do not copy or commit raw SCID rows, raw CSV exports, or large raw market-data files.
- Recompute row counts for full UTC days `2026-04-15` and `2026-04-16`.
- Recompute row coverage around the three candidate timestamps above and record nearest preceding/following SCID records, timestamp resolution, OHLC fields, volume fields, bid volume, ask volume, and any record-status anomalies.
- Compare the SCID schema and records against the MT5 tick contract required by the recovery route: `time_utc`, `time_msc`, `bid`, `ask`, `last`, `volume`, `flags`, `source_symbol`, `broker_symbol`, and `source_file_sha256`.
- Explicitly decide, field by field, whether each required MT5 field is present, derivable without leakage, derivable only as a proxy, or absent. Do not silently substitute SCID `open/high/low/close` for bid/ask ticks unless the route freezes that as a separate alternate-source evidence class and marks it non-equivalent to MT5 tick recovery.
- Verify SCID cannot introduce hidden broker/account/order/history/deal/position values, broker actual-R, result/cost/R/win-rate/expectancy labels, validation labels, or live trading effects.
- Verify that `2026-04-16` candidate rows remain contamination/embargo excluded unless a separate future clean-denominator audit says otherwise.
- Preserve the source-state boundary: SCID market data cannot recreate pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, or final lifecycle truth.

## Required Artifacts

Write a route directory under:

`research\science_program_2026_05\06_outcome_testing\xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route\`

Include at minimum:

- context anchor JSON/MD,
- raw SCID source-hash/header audit,
- SCID day/candidate coverage ledger,
- MT5 tick-contract field-comparison audit,
- alternate-source admissibility decision ledger,
- source-state/no-leak boundary audit,
- owner/manual export fallback manifest for `data\ticks\XAUUSD\2026-04-15.parquet` and `data\ticks\XAUUSD\2026-04-16.parquet`,
- source-hashed alternate packet if and only if admissible under a frozen alternate-source contract,
- exact field-mismatch blocker ledger if not admissible,
- next G12 audit prompt pack with one-line starter and full prompt file path recommendation,
- completion audit,
- builder, verifier, and focused tests.

## Hardening Requirements

This route must be curious, truthful, active, and creative inside the allowed evidence class.

Do not stop at "SCID is not MT5" without proving exactly which fields fail and whether a narrower alternate-source packet is still useful. Do not stop at "file not found" without searching approved roots and requesting source-safe access. Do not stop at small row counts without explaining whether the source contract is count-based, field-based, or coverage-based. Do not convert discovery/source-control evidence into validation or performance claims.

If a same-evidence-class repair is possible in this route, do it. If the next action crosses evidence class, freeze an exact next prompt. If the source is truly unusable, prove why and state the exact manual/export data required.

## Completion Standard

Mark complete only when the route:

- proves raw SCID source hash/header/coverage for both remaining dates or records exact source-access failure after approved pursuit,
- reconciles all three remaining candidate timestamps,
- completes a field-by-field MT5 tick-contract comparison,
- emits either an admissible source-hashed alternate packet or exact field-mismatch blockers,
- preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`,
- commits no raw SCID-derived exports or large raw tick files,
- runs verifier and focused tests,
- produces a non-passive next G12 audit prompt pack,
- and records no validation execution, result scoring, broker actual-R, MT5 account/order/history/deal/position values, paid/API/Databento route, registry edit, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary change, credential touch, or live trading behavior change.
