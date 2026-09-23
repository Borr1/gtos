# OTR061 XAU Tick Recovery Goal Prompt

Date: 2026-05-07
Lane: OTR061 / data recovery and source proof
Packet: OTG0-PKT-061
Experiment: G6-EXP-002-CONTINUATION-NO-RETRACE
Promotion posture: NO_PROMOTION_VERDICT

## Objective

Attempt to unblock OTG0-PKT-061 by recovering or proving impossible the missing XAUUSD tick/quote/path window for `2026-05-06T07:10:00Z` through at least `2026-05-06T11:15:00Z`. This is a data-recovery/source-proof lane only. It must not score outcomes unless a later G12 audit authorizes a result lane.

The goal is not complete until it either produces a source-hashed recovery packet suitable for G12 re-audit, or proves the exact recovery impossibility from all approved local/heavy-data paths and approved read-only historical extraction routes.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Record HEAD, freshness, local-data roots searched, and access requests in the completion audit.

If a search path or historical data route needs access, request access. Do not silently treat permission denial as data absence.

## Controlling Inputs

Read directly:

- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md/json`

Known blocker to verify:

- Absolute file checked by G12: `C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-06.parquet`
- G12 finding: file starts at `2026-05-06T17:16:17.131Z`, so the required morning UTC window has zero approved tick rows.
- Required recovery window: `2026-05-06T07:10:00Z` through at least `2026-05-06T11:15:00Z`.

## Approved Search And Recovery Routes

Search local roots first:

- Worktree `data/`
- Absolute main repo `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\external`
- `C:\Users\MSI\Documents\ai-trading-agent\exports`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs` for provenance only, not result labels
- `C:\tmp` targeted by packet id, symbol, timestamp, source hash, and lane names
- Candidate Sierra root `C:\SierraChart` if present
- Targeted `C:\Users\MSI\Documents` searches for `XAUUSD`, `2026-05-06`, `.parquet`, `.scid`, `.csv`, `.jsonl`, and Databento/Sierra/MT5 cache names

Read-only historical extraction may be proposed or attempted only if safe in the local environment:

- MT5 historical tick extraction for XAUUSD and the exact window is allowed as a read-only data-recovery action if the session can do it without placing orders, reading broker actual-R/account history, or changing live state. Request access if needed.
- SierraChart/local `.scid` or export recovery is allowed if files exist; parser/source-hash/as-of proof is required.
- Databento/API/vendor recovery requires a pre-call manifest, free-credit/zero-paid-spend proof or explicit cap, and owner approval before any paid/network call.

## Required Output Decision

Terminal states:

- `RECOVERY_PACKET_READY_FOR_G12_REAUDIT`: recovered tick/quote/path data covers the required window, source files are hashed, no forbidden labels are used, and a `continuation_no_retrace_decision_price_path_v1` packet proposal is emitted.
- `BLOCKED_PERMISSION_OR_ACCESS`: exact path/tool/source exists or may exist but access was denied; record the exact access request.
- `BLOCKED_SOURCE_NOT_FOUND_AFTER_SATURATION`: all approved local roots and read-only routes were searched; no source exists. Record search patterns and exact negative evidence.
- `BLOCKED_VENDOR_RECOVERY_REQUIRED`: local routes failed and only vendor/API recovery remains; produce a pre-call manifest and cost/credit rule.

## Required Artifacts

Write only under:

- `research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/`

Required:

- `OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.md/json`
- `OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.md/json`
- `OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07.md/json`
- `OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.md/json` if recovered
- `OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07.md/json` if vendor/API/access is needed
- `OTR061_COMPLETION_AUDIT_2026-05-07.md/json`
- Builder/verifier script and focused tests.

## Verification

Before marking complete:

- JSON parse every generated JSON/JSONL artifact.
- Run `python -B -m py_compile` on generated Python.
- Run focused pytest for generated tests if any.
- Scan outputs for `NO_PROMOTION_VERDICT`.
- Confirm no `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no broker actual-R/account-history/live trade result/blocked-packet outcome fields were opened.
- Confirm no live prompt/risk/execution/permission/safety/selector/MT5 order/canary/credential/remote-push/order behavior diff.
- Regenerate `.context/LIVE_STATE.md` and update `.context/00_core/research_current_state.md` if the durable blocker map changes.

## Forbidden

No outcome scoring, no broker actual-R, no account history, no live order state, no order placement, no live config change, no prompt/risk/execution/permission/safety/selector/canary change, no paid/API/Databento call without pre-call manifest and approval, no source validation flip, and no promotion language.

## Stop Condition

The goal is complete only when the missing XAUUSD 2026-05-06 07:10-11:15 UTC tick window is either recovered into a source-hashed G12-reaudit-ready packet proposal, or recovery is proven blocked/impossible with exact searched paths, access status, and next unblocker.
