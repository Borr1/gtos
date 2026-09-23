# G12 XAUUSD Sierra SCID Alternate Source-Control Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source-control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`.

Verify that the route read `C:\SierraChart\Data\XAUUSD.scid` read-only, hashed the raw SCID file, recomputed the `2026-04-15` and `2026-04-16` full-day row coverage, reconciled the three remaining candidate timestamps, compared SCID fields against the MT5 tick contract field by field, and emitted a source-hashed SCID market-activity packet only as context while preserving exact MT5 bid/ask tick blockers and owner/manual export requirements.

Expected target facts from the route are: raw SCID SHA256 `c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b`; SCID rows exist for both full UTC days; all three candidate windows have nearest-record coverage; SCID is admissible only as same-market SCID context, not as MT5 tick recovery; MT5 tick-contract blockers remain because `bid`, `ask`, and `flags` are absent, while `time_msc`, `last`, `volume`, and `broker_symbol` are proxy/non-equivalent. Verify these facts independently; do not rely on the route summary.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\research_current_state.md`.
9. Read the target route directory `research\science_program_2026_05\06_outcome_testing\xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route\`.
10. Read the upstream G12 and target NOFILL read-only tick recovery artifacts.
11. Read `.context\00_core\goal_session_research_discipline.md` for the proof-or-impossibility and owner-access pursuit standard, but do not let this G12 audit expand into validation/result/live behavior.

## Audit Requirements

- Recompute the raw SCID SHA256, size, header, record count, first/last timestamps, and parser code hashes.
- Recompute full-day row counts for `2026-04-15` and `2026-04-16`.
- Recompute candidate coverage for:
  - `XAUUSD_2026-04-15T14:15:05.007998+00:00`
  - `XAUUSD_2026-04-16T09:30:05.013547+00:00`
  - `XAUUSD_2026-04-16T13:16:01.126537+00:00`
- Verify nearest preceding/following SCID records, timestamp resolution, OHLC, volume, bid volume, ask volume, and anomaly summaries.
- Verify the MT5 field comparison for `time_utc`, `time_msc`, `bid`, `ask`, `last`, `volume`, `flags`, `source_symbol`, `broker_symbol`, and `source_file_sha256`.
- Verify the route does not substitute SCID OHLC or bid/ask volume for MT5 bid/ask quotes.
- Verify 2026-04-16 candidate rows remain contamination/embargo excluded.
- Verify SCID does not recreate pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, final lifecycle truth, broker actual-R, or result labels.
- Verify no raw SCID-derived exports, raw CSV, raw parquet, or large market-data files are tracked or staged.
- Run the route verifier and focused tests.
- Produce a G12 decision ledger, source-hash/header/coverage reaudit, candidate-window reproducibility audit, MT5-field-blocker reaudit, no-leak/raw-data staging audit, completion audit, and exact next-step recommendation.

## Hardening Requirements

Do not stop at surface acceptance. If any source-hash, row-count, candidate-window, or field-comparison claim is incomplete but repairable inside this G12 audit write scope without opening validation/live/forbidden surfaces, repair and record the repair. If the issue belongs to the target route, reduce it to an exact repair prompt. If the route is correct, accept it narrowly and explicitly close the SCID alternate route as context-only evidence.

Do not keep these two dates as an open-ended research drag. The G12 answer should be definitive for this evidence class: either the SCID context-only packet is accepted with MT5 tick blockers still open, or the route has exact repair blockers. Manual MT5 export may remain as a fallback, but the broader research should be routed back to source expansion/replay infrastructure once this audit is accepted.

Do not convert SCID context into result labels, denominator movement, validation evidence, R scoring, win-rate/expectancy, broker actual-R, pending lifecycle truth, or live trading behavior.

## Completion Standard

Mark complete only if the G12 audit proves the target route is source/control only, the source hash/header/coverage and field comparison are independently reproducible, the alternate packet is context-only and non-equivalent to MT5 tick recovery, exact manual MT5 export blockers remain open, raw market-data staging/tracking is clean, verifier/tests pass, a non-passive next-step recommendation exists, and terminal flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
