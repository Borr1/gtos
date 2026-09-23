# NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF Goal Prompt

Date: 2026-05-09
Primary owner: source/control research lane
Worktree: `C:\tmp\gtos_otb\NOFILLMAY3PROOF`
Branch: `nofill-may3-opening-range-source-proof`
Promotion posture: `NO_PROMOTION_VERDICT`

## Mission

Resolve the exact source/control status of the three remaining May 3 OTI4 opening-range rows from the no-fill categorical V2 residual blocker lane:

- `NOFILL-CAT-ROW-0049` / NAS100 / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`
- `NOFILL-CAT-ROW-0050` / XAUUSD / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`
- `NOFILL-CAT-ROW-0051` / XAUUSD / frozen range `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z`

The goal is to go all the way on source/control proof, not to score results. Either find source-safe same-market/broker tick, quote, M1, or lower-OHLC evidence for the frozen range, prove source-safe market-session/no-bar non-trading emptiness for that window, prove impossibility from approved routes, or write the exact remaining source/access/capture requirement.

## Mandatory Preflight

Before relying on any summary or chat memory:

1. Run `python scripts\generate_live_state.py` and read `.context\LIVE_STATE.md`.
2. Read the latest handoff named in `LIVE_STATE.md`.
3. Read `.context\00_core\quick_reference_card.md`.
4. Read `.context\00_core\research_operating_doctrine.md`.
5. Read `.context\00_core\research_current_state.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Skim `.context\00_READING_ORDER.md` and any directly relevant referenced documents.
9. Record current HEAD, branch, working-tree status, and this prompt path in your context anchor.

Do not trust stale handoff text over current committed artifacts. Do not rely on chat memory after compaction. If interrupted, regenerate `LIVE_STATE`, re-read this prompt and your latest context anchor, then continue from disk.

## Controlling Inputs

Read these first and treat them as controlling evidence:

- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_NEXT_PROMPT_PACK_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/`

You may read additional relevant artifacts, builders, verifiers, tests, source hashes, prior worktree outputs, `git log`, and `git show` history when needed.

## Research Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard safety boundaries. Enforce the owner's three virtues:

- Curiosity: search beyond the first obvious file, path, timeframe, data modality, or prior answer.
- Truthfulness: do not rescue, soften, or fabricate. If evidence is absent, say exactly what is absent. If a route is impossible, prove why.
- Active creativity: do not be boxed by the initial framing. Consider broker ticks, local tick parquet, M1/lower OHLC, Sierra-derived artifacts, MT5 read-only source extraction, exchange/session calendars, symbol session metadata, prior source caches, and public/official source documents where the lane allows them.

Prompt examples and listed paths are starting points, not limits. Worktree absence is not data absence. Search absolute local heavy-data roots before declaring anything missing. Small sample size is not relevant to this source lane and must not be used as a stop reason. Negative or blocked evidence is first-class: explain why the route failed, what was searched, what it proves, what it does not prove, and the next exact unblocker.

## Allowed Source Routes

Allowed if done read-only, source-hashed, and recorded:

- Existing local source artifacts in this worktree.
- Absolute local repo data under `C:\Users\MSI\Documents\ai-trading-agent\data`.
- Tick parquet under `C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet` and `C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet`.
- `C:\SierraChart` data roots, including `.scid`, converted M1/CSV, and depth files, only with parser/source/as-of proof and clear statement of whether the source is approved for this lane.
- Targeted searches under `C:\tmp` and `C:\Users\MSI\Documents` for cached prior exports or raw source captures.
- Read-only MT5 source extraction if needed and possible: `copy_ticks_range`, `copy_rates_range`, and symbol/session metadata only. No account, order, deal, position, or history calls.
- Public official/web source evidence only if local evidence cannot prove market-session/no-bar status. Use approved webfetch/curl routes, save raw captures under this lane's `raw/` subdirectory, hash them, and write a source index. Request access if network/webfetch/curl is blocked.

If access is needed, request it directly and precisely. The owner has stated access can be granted; do not silently stop.

## Forbidden Routes

Do not touch or use:

- live trading prompts, `src` trading logic, risk, execution, permissions, safety gates, selectors, canaries, live order behavior, credentials, remotes, or registry edits;
- broker actual-R, account history, orders, deals, positions, live trade result labels, hidden result labels, blocked-packet outcome labels, or post-outcome fields;
- paid/API/Databento calls unless a separate pre-call manifest and owner approval are written first;
- result/R/performance scoring, win rate, expectancy, validation claims, promotion claims, `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.

## Required Work

For each of the three rows:

1. Reconstruct row identity: packet row ID, symbol, decision time, duplicate group, no-fill duplicate key, source row ID, source family, frozen range window, and current blocker statement.
2. Recompute the prior local tick file coverage and timestamp span where possible.
3. Search for same-symbol broker/same-market tick, quote, M1, lower-OHLC, or source contract evidence covering `2026-05-03T13:00:00Z` through `2026-05-03T13:30:00Z`.
4. If no rows exist, determine whether the correct source conclusion is missing local data, broker no-trading/no-bar source proof, exchange/session calendar closure, symbol-session metadata closure, parser gap, or true impossibility.
5. For any claimed market-session/no-bar proof, separate:
   - broker-symbol session metadata,
   - official exchange/session source,
   - empirical local no-row coverage,
   - proxy/source-contract limitations.
6. Hash every consumed source file and raw/public source capture.
7. Preserve duplicate/sample-floor/no-leak/label-family separation. The `65` rejects and all other no-fill rows stay outside this lane's labels and denominators.
8. Write exact terminal status per row from this set only:
   - `SOURCE_CONTROL_CLEARED_INPUT_ONLY`
   - `MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL`
   - `STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE`
   - `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES`
   - `REJECTED_SCOPE_VIOLATION`
9. If blocked, name the exact missing source, field, timestamp window, parser, access permission, or capture requirement. "Need more data" is not acceptable.

## Required Outputs

Write all outputs under:

`research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/`

Required files:

- `NOFILL_MAY3_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_2026-05-09.md`
- `NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_2026-05-09.json`
- `NOFILL_MAY3_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `NOFILL_MAY3_SOURCE_PROOF_PACKET_2026-05-09.json`
- `NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_2026-05-09.md`
- `NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_2026-05-09.json`
- `NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.md`
- `NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.json`
- `NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md`
- `NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md`
- `NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json`
- builder script, verifier script, focused pytest file, and optional `raw/` source capture/index if public/web/official source evidence is used.

Also update `.context/00_core/research_current_state.md` after completing the lane, and regenerate `.context/LIVE_STATE.md` before final status. Keep `.context/LIVE_STATE.md` committed only if the lane's local convention requires it; otherwise explain if it remains generated dirt.

## Verification

Before marking complete:

- JSON/JSONL parse all generated machine-readable outputs.
- Verify exactly `3` target rows are covered and no other row is accepted/scored by this lane.
- Verify all consumed source hashes recompute.
- Verify no forbidden keys/flags appear in generated JSON: no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`, no result/R/performance labels.
- Verify no broker account/order/history/live-result fields were read or carried.
- Verify no overlap with `65` rejects, six T3 rows, or G12-blocked CNR061 rows.
- Run `python -m py_compile` on builder/verifier/test.
- Run focused pytest for this lane.
- Run a committed-diff live-surface check over `src`, `prompts`, `config`, `scripts/canary`, MT5 order/account/history paths, risk, execution, permissions, safety, selectors, credentials, remote/push, and order-behavior paths.
- Regenerate `LIVE_STATE.md` and confirm research context freshness or document the exact stale-state reason.

## Completion Standard

Do not complete because the first local file has zero rows. Complete only when each of the three rows has a terminal source/control status backed by machine-checkable evidence, proof of approved-route impossibility, or an exact source/access/capture request. The completion audit must show instruction coverage, searched roots, source hashes, route decisions, row statuses, false-flag safety checks, verification commands, and the next prompt pack.

