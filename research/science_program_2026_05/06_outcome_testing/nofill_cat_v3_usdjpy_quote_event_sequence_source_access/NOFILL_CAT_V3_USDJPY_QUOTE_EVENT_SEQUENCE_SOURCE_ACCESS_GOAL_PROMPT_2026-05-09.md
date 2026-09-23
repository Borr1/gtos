# NOFILL CAT V3 USDJPY Quote-Event Sequence Source-Access Goal Prompt

Date: 2026-05-09
Route: `USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS`
Evidence class: `source_access_contract`
Promotion posture: `NO_PROMOTION_VERDICT`

## Starter Message

```text
/goal Run USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS from C:\tmp\gtos_otb\NOFILLUSDJPYSEQ as a maximum-effort source-access proof-or-impossibility lane for NOFILL-CAT-ROW-0130, 0143, 0165, and 0178. Start with mandatory GTOS preflight, read the prompt file at research\science_program_2026_05\06_outcome_testing\nofill_cat_v3_usdjpy_quote_event_sequence_source_access\NOFILL_CAT_V3_USDJPY_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS_GOAL_PROMPT_2026-05-09.md, then search all approved local/heavy/prior-worktree/source-contract routes for broker-native USDJPY quote-event sequencing, sub-row/sub-ms timestamps, or sequence IDs that can order the same-tick entry/protective predicates. Do not stop at "source impossible" until approved routes are saturated, exact official/source-contract limits are documented, and any needed owner/access/source request is precise. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; no result scoring, no account/order/history/deal/position labels, no broker actual-R, no hidden labels, no paid/API/Databento, no MT5 order/account/history calls, no live trading prompt/src/risk/execution/safety changes, no registry edits, no remote push.
```

## Objective

Resolve the rank-2 G0 no-fill CAT V3 next route for the four USDJPY same-tick event-order source-impossible rows:

- `NOFILL-CAT-ROW-0130`
- `NOFILL-CAT-ROW-0143`
- `NOFILL-CAT-ROW-0165`
- `NOFILL-CAT-ROW-0178`

The current canonical state says these rows are source-impossible from approved routes because one source quote row/timestamp satisfies multiple touch predicates and the available source lacks a sub-row sequence field. This goal must not simply repeat that conclusion. It must pursue every approved source-safe path to either:

1. find broker-native USDJPY quote-event ordering evidence that clears one or more rows;
2. prove exact impossibility from approved local/source routes with source-contract evidence; or
3. reduce the blocker to an exact owner/access/source/capture request.

This is not a result lane. Do not score R, win rate, expectancy, DSR/PBO, validation, promotion, or live performance. Do not consume account/order/history/deal/position labels, broker actual-R, or hidden result/path labels.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered file in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Record preflight status, HEAD, research freshness, and data-root visibility in the context anchor.

If this worktree cannot see heavy local data, search absolute roots from `.context\00_core\local_heavy_data_inventory.md`. Worktree absence is not data absence.

## Controlling Inputs

Read these before source pursuit:

- `research\science_program_2026_05\06_outcome_testing\g0_nofill_cat_v3_categorical_evidence_synthesis_control_review\G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.json`
- `research\science_program_2026_05\06_outcome_testing\g0_nofill_cat_v3_categorical_evidence_synthesis_control_review\G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md`
- `research\science_program_2026_05\06_outcome_testing\nofill_cat_v3_source_control_rebuild\`
- `research\science_program_2026_05\06_outcome_testing\g12_nofill_cat_v3_source_control_audit\`
- `research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\`
- `research\science_program_2026_05\06_outcome_testing\g12_nofill_remaining_residual_source_closure_audit\`
- `research\science_program_2026_05\06_outcome_testing\nofill_cat_v2_residual_blocker_clear_source_access_lane\`
- `research\science_program_2026_05\06_outcome_testing\oti3_usdjpy_price_only_quote_or_tick_contract\`
- `research\science_program_2026_05\06_outcome_testing\oti2_fill_path_categorical_contract_v2\`
- `research\science_program_2026_05\06_outcome_testing\nofill_cat_v2_pending_lifecycle_source_contract_builder\`
- official/source-contract docs already captured in the relevant lanes, especially MQL5 `copy_ticks_range`, `MqlTick`, and any raw saved docs

Also inspect relevant local paths and prior worktrees before declaring impossibility:

- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY`
- `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- `C:\Users\MSI\Documents\ai-trading-agent\exports`
- `C:\tmp`
- `C:\SierraChart` if present and relevant
- this worktree's local copies of the same roots

## Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard boundaries. Enforce:

- Curiosity: actively look for source routes that may have been missed, including local heavy files, raw captures, prior worktrees, generated manifests, source docs, parser code, timestamp precision quirks, and quote flags.
- Truthfulness: do not fake a sequence field or infer sub-row ordering from unavailable source data. If impossible, prove why exactly.
- Active creativity: explore non-obvious source-safe routes such as file row order, parquet metadata, MT5 flags, tick capture daemon raw fields, generated JSONL ordering, broker timestamp precision, Sierra/proxy limitations, code history, and official docs; but do not convert proxy or post-outcome fields into evidence.
- Same-evidence-class continuation: do not stop at blocker taxonomy. Source-access proof, local-heavy search, source-doc audit, parser-field audit, and exact access request all belong in this goal.
- Hostile edge review lens: attack the chance of leakage, proxy misuse, timestamp overclaim, duplicate laundering, and hidden account/order evidence.
- Context-compaction rule: maintain a context anchor, active question stack, searched-root ledger, and completion checklist.

## Allowed Source Routes

Allowed:

- read committed research artifacts and raw captures;
- read local tick parquet/CSV/JSON/JSONL files;
- inspect parser/source code and historical commits for tick field handling;
- inspect official/source-contract docs already captured locally;
- if absolutely needed, request owner approval for read-only MT5 `copy_ticks_range` on USDJPY for the exact frozen windows, with a pre-call manifest that forbids account/history/order/deal/position calls and hashes any export;
- fetch official public source docs only if the lane needs missing source-contract facts and local captures are insufficient, saving raw captures and a source index.

Forbidden:

- no MT5 order/account/history/deal/position calls;
- no broker actual-R, live trade result, hidden label, path result, or blocked-packet outcome use;
- no paid/API/Databento calls;
- no live trading prompt, `src` trading logic, risk, execution, permissions, safety, selector, canary, credential, remote, registry, or order-behavior changes;
- no result scoring, validation, promotion, or live-effect claims.

## Required Work

For each target row:

1. Reconstruct the row identity, symbol, side, decision timestamp, active interval, entry/protective/terminal predicates, source row/timestamp, duplicate key, and current blocker.
2. Identify the exact source rows/ticks that caused same-tick ambiguity.
3. Search local and prior-worktree sources for any broker-native row order, quote-event sequence, sub-row/sub-ms timestamp, `time_msc` distinction, flag transition, bid/ask update state, raw capture order, or parser-retained sequence field.
4. Test whether file row order is source-authorized or merely an artifact of a collapsed quote-state row. Do not assume row order is event order unless source-contract evidence supports it.
5. Red-team proxy sources such as Sierra or futures equivalents. Record whether they can support source-control context, but do not use them to order a broker CFD same-tick quote event unless the contract proves validity.
6. Record all searched roots, glob patterns, candidate files, row counts, timestamp precision, fields present, hashes, and negative evidence.
7. Produce a terminal decision for each row:
   - `SOURCE_SEQUENCE_CLEARED_INPUT_ONLY`
   - `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES`
   - `EXACT_OWNER_ACCESS_OR_SOURCE_REQUEST`
   - `REJECTED_SCOPE_VIOLATION`
8. If any row is cleared, keep it input-only source/control evidence and do not assign result/performance labels.
9. If any row remains impossible, specify the exact missing source capability, such as broker-native quote-event sequence ID, sub-row timestamp, event ID, raw quote-stream update order, or vendor field, and prove why approved routes lack it.

## Required Artifact Set

Create a versioned folder under:

`research\science_program_2026_05\06_outcome_testing\nofill_cat_v3_usdjpy_quote_event_sequence_source_access\`

Produce at least:

- `NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_2026-05-09.json`
- `NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_2026-05-09.json`
- `NOFILL_USDJPY_SEQ_DECISION_LEDGER_2026-05-09.jsonl`
- `NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_2026-05-09.json`
- `NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_ACCESS_REQUEST_OR_IMPOSSIBILITY_LEDGER_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_2026-05-09.md`
- `NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_2026-05-09.json`
- builder/verifier/focused tests if they materially improve auditability

The completion audit must include `can_mark_goal_complete=true` only if every target row has a terminal decision and the lane has either found source-safe sequence evidence, proven exact impossibility from approved routes, or created an exact owner/source/access request.

## Verification

Run all applicable checks:

- JSON/JSONL parse for generated artifacts;
- exact target-row coverage: 4/4 rows;
- source hash recomputation for consumed files;
- unsafe flag scan: no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`;
- `NO_PROMOTION_VERDICT` coverage;
- no forbidden result/account/order/history/broker actual-R/hidden-label keys in generated artifacts;
- no-leak and duplicate-denominator checks;
- `python -m py_compile` for any generated Python;
- focused pytest if tests are created;
- committed-scope forbidden live-surface diff check.

If Windows pycache/temp permissions interfere, use `--basetemp`, `-p no:cacheprovider`, or syntax-parse fallback and record the difference between environment friction and code failure.

## Stop Conditions

The goal is complete only when each of the four rows has a terminal source/control decision:

- source sequence cleared input-only;
- source impossible from approved routes with exact source-contract proof;
- exact owner/access/source request with enough detail for the owner to provide it;
- or rejected for explicit scope violation.

Do not stop merely because prior lanes called the rows impossible. This lane exists to verify whether that impossibility is truly saturated.

## Commit Scope

Commit only scoped artifacts in this route and, if materially changed, `.context\00_core\research_current_state.md` or `.context\LIVE_STATE.md` refreshes required by the repo process. Do not stage unrelated runtime dirt.

Use a commit message like:

`research: pursue no-fill usdjpy quote-event sequence source access`
