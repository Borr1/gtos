# NOFILL Blocked-Family Source Correction Router Goal Prompt - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
Lane: `NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1`
Worktree: `C:\tmp\gtos_otb\NOFILLROUTER`
Branch: `nofill-blocked-family-source-correction-router`

## Starter Message

Use this exact one-line starter in `/goal`:

`/goal Run NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1 using C:\tmp\gtos_otb\NOFILLROUTER\research\science_program_2026_05\06_outcome_testing\nofill_blocked_family_source_correction_router\NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_GOAL_PROMPT_2026-05-08.md as the controlling prompt; complete mandatory GTOS preflight, split the 246 G12-blocked no-fill categorical rows by blocker family, open only source-correction or contract-revision prompt packs needed to make future categorical lifecycle labels possible, pursue every ambiguity to proof-or-impossibility using local heavy data and prior artifacts before accepting blockers, preserve context in committed artifacts, request access if needed, and do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5 order/account paths, canaries, paid/API/Databento calls, credentials, remotes, registry promotion flags, validation flags, outcome-review flags, live-effect flags, or order behavior.`

## Mandatory Preflight

Before doing any router work:

1. Regenerate and read `.context/LIVE_STATE.md` with `python scripts/generate_live_state.py`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Read `.context/00_READING_ORDER.md` enough to identify relevant Tier 2-4 artifacts.
9. Record the exact HEAD, controlling prompt path, preflight files read, and freshness status in a context anchor before row routing.

If conversation compaction, resume, or uncertainty happens: regenerate `LIVE_STATE`, re-read this prompt, re-read the context anchor/latest lane artifact, re-read the hardening docs above, then continue from committed state.

## Controlling Inputs

Treat these files as controlling inputs, then search beyond them when needed:

- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_NEXT_PROMPT_PACK_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_BLOCKER_REVIEW_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/G12_NOFILL_CAT_SOURCE_HASH_AUDIT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_FAILURE_LEARNING_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design/NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_result_contract_audit/G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md`
- `research/science_program_2026_05/06_outcome_testing/g12_no_fill_correction_reaudit/G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json`

Also inspect the relevant source lanes and tests before assigning sub-lane work:

- OTI4/G6 opening-drive artifacts and G12/OTX post-audits for opening-drive fields.
- OTI1/OTB1R lifecycle artifacts for pending-intent closure rows.
- OTI3/G3 geometry artifacts for lower-timeframe price-only rows.
- OTI5/G6 CUSUM/changepoint artifacts for duplicate/conflict identity questions.
- OTI2/riskbank synthetic-path artifacts for the single separate fill/path plus terminal-order ambiguity row.
- `git log --oneline -- research/science_program_2026_05/06_outcome_testing/` and `git show` for commits that touched the above files.

## Starting Facts That Must Not Drift

- G12 accepted `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1` only as categorical lifecycle evidence for `52` rows labeled `nofill_terminal_before_entry`.
- `246` rows remain blocked before label.
- Blocker counts must reconcile exactly:
  - `BLOCK_RESULT_DUPLICATE_CONFLICT`: `42`
  - `BLOCK_RESULT_LTF_PRICE_ONLY`: `69`
  - `BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD`: `54`
  - `BLOCK_RESULT_MISSING_SOURCE`: `80`
  - `BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED`: `1`
  - `BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS`: `1`
- The single fill/path row may share both separate-contract and terminal-order ambiguity blockers; do not double-count row identities.
- `NOFILL-CLOSE-ROW-0127` has OTR061 terminal first touch `2026-05-06T07:15:00.634000Z` from SHA256 `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff`, but remains blocked until opening-drive prereg fields are source-hashed.
- The six T3 lifecycle rows remain excluded.
- The `94` G12-blocked CNR061 rows remain excluded.
- The accepted `52` categorical lifecycle rows are not performance evidence.
- This lane must not compute R, win rate, expectancy, broker actual-R, account history, live order/deal/position labels, hidden labels, validation, promotion, or live effect.

## Objective

Build a source-correction router, not a result lane.

Your job is to split all `246` blocked categorical no-fill rows into exact blocker families, then decide which source-correction or contract-revision lanes should open next. For each family, pursue the blocker as far as allowed inside this goal:

- read the original row-level packet records;
- trace the source chain back to the lane that produced or blocked the needed fields;
- search local heavy-data roots and prior worktree artifacts before accepting missing-data blockers;
- distinguish source absence, parser absence, as-of invalidity, duplicate-denominator conflict, label-family boundary, and hard forbidden-boundary blockers;
- write exact next prompt packs only for lanes that can be pursued source-safely;
- prove when a family cannot be pursued further without an explicit owner/access/source/capture requirement.

Do not stop at generic "needs data" or "future work." Every blocker must name the exact missing field, source, parser, schema, logger, source-hash path, as-of rule, duplicate rule, or approval required.

## Hardening Requirements

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed to reach proof, exact blocker, or source-safe lane design.

Enforce the three research virtues:

- Curiosity: actively look for routes that could unlock blocked lifecycle evidence or improve future hypotheses. Search beyond obvious files and known strategy categories.
- Truthfulness: do not rescue, soften, or relabel failures. If a row is blocked, say exactly why. If a route is impossible from approved inputs, prove it.
- Active creativity: do not be boxed by the listed files, current timeframe, current worktree, first source modality, or first model framing. Consider tick, M1, M5/M15/H1, source manifests, prior recovered tick lanes, shadow logs, builder code, tests, and historical git artifacts if source-safe.

Anti-boxing rule: examples in this prompt are starting points, not limits. If another local artifact or data root can answer a blocker without violating no-leak/source rules, pursue it or record why it is forbidden.

Small-N rule: small `n` can block validation and promotion but cannot be used as an excuse to stop source research. If a family is too small, define the denominator, search for more eligible rows, and write a source-safe expansion route or proof of impossibility.

Negative/blocker learning rule: blocked families are useful evidence. For every family, write what the blocker teaches about future data capture, source contracts, preregistration wording, duplicate control, and lifecycle label design.

## Local Heavy-Data And Access Policy

Before accepting any data-missing blocker, search targeted absolute roots when relevant:

- `C:\Users\MSI\Documents\ai-trading-agent\data`
- `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`
- `C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports`
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs`
- `C:\Users\MSI\Documents\ai-trading-agent\exports`
- `C:\tmp`
- `C:\SierraChart` only if the route actually needs Sierra data

Hash any source file used in an audit or route decision.

If access is needed, request it explicitly and write an access request manifest. The owner has signaled willingness to grant access, but the goal session must still be precise about what is requested and why.

Do not make paid/API/Databento calls. If you believe a paid/API/Databento source is necessary, write a pre-call manifest with exact source, purpose, fields, expected cost/free-credit state, no-leak/as-of rule, cache path, and owner approval requirement.

Read-only MT5 tick extraction is not authorized by this router unless you write a separate request manifest. No MT5 order/account/history calls are allowed.

Web/curl/webfetch may be used only for official/public source-contract documentation if local source metadata is insufficient. Save raw captures and a source index if used.

## Required Family Routing

Produce route decisions in this order unless direct evidence proves a different dependency order:

1. `OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION`
   - Scope: `80` missing source/opening-drive preregistration rows, including row `NOFILL-CLOSE-ROW-0127` when applicable.
   - Required fields to investigate: `range_high`, `range_low`, `breakout_close_time`, `breakout_side`, source-hashed range bars, as-of provenance, parser/version, decision-time availability.
   - Decide whether the next lane should patch source projection, revise the contract, or prove the family impossible without new forward capture.

2. `OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET`
   - Scope: `54` missing pending-intent closure rows.
   - Required fields to investigate: `entry_touched_at_utc`, fill/cancel/expiry/horizon timestamps, pending intent identity, source-hash path, side-aware touch source, and as-of rule.
   - Must remain lifecycle/no-fill only. No broker actual-R, account history, live order/deal/position labels, or performance.

3. `OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT`
   - Scope: `69` lower-timeframe price-only rows.
   - Required question: can the price-compatible M1 source become categorical lifecycle evidence under a conservative quote contract, or does it need tick/quote replay source? If tick/quote extraction is required, write an exact request manifest.

4. `OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT`
   - Scope: `42` duplicate-conflict rows across `3` conflicted duplicate groups.
   - Required question: are these true duplicate conflicts, geometry/source identity collisions, repeated row projections, or contract-level denominator collisions? Do not relabel or score them.

5. `OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT`
   - Scope: the single separate fill/path plus terminal-order ambiguity row if still needed after the first four families.
   - Required question: can a categorical lifecycle contract separate entry-touch/fill/path terminal order without R/performance or hidden labels?

## Expected Outputs

Write outputs under:

`research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/`

Minimum artifacts:

- `NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_2026-05-08.md` and `.json`
- `NOFILL_ROUTER_NEXT_PROMPT_PACK_2026-05-08.md`
- one prompt pack per source-safe next lane that should run, with a one-line `/goal` starter inside each prompt pack;
- `NOFILL_ROUTER_COMPLETION_AUDIT_2026-05-08.md` and `.json`
- builder/verifier/test files if useful for exact count/source/no-leak checks.

Each prompt pack must carry the full hardening standard from this prompt and `.context/00_core/goal_session_research_discipline.md` without requiring the owner to restate it.

## Verification Requirements

Before completion:

- Verify JSON and JSONL parse for all generated artifacts.
- Verify the `246` blocked-row universe exactly reconciles to the G12 audit and categorical packet.
- Verify blocker family counts exactly match the starting facts, accounting for the single overlapping fill/path plus terminal-order ambiguity row.
- Verify zero overlap with the `52` accepted categorical rows.
- Verify zero overlap with the six T3 rows and the `94` G12-blocked CNR061 rows.
- Verify no generated artifact contains `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Verify all generated artifacts preserve `NO_PROMOTION_VERDICT`.
- Verify no R/performance/win-rate/expectancy/broker actual-R/account history/live order/deal/position/hidden label fields are consumed or emitted except as forbidden-field names in ledgers.
- Run `py_compile` on any generated Python.
- Run focused pytest if tests are generated.
- Run a forbidden live-surface committed-diff check over at least `src/`, `prompts/`, `config/`, `scripts/canary`, MT5/order paths, risk/execution/permissions/safety/selectors, credentials, remotes, and canaries.
- Record unrelated runtime/workspace dirt separately. Do not stage or revert unrelated live-monitoring changes.

## Stop Condition

This goal is complete only when every one of the `246` blocked rows has an exact route decision:

- source-safe next prompt pack,
- contract-revision next prompt pack,
- exact access/source/capture request,
- exact source/as-of/no-leak/duplicate/label-family impossibility, or
- hard forbidden-boundary explanation.

Do not mark complete because a blocker is inconvenient. Do not mark complete with generic "future work." The router completion audit must show which files were read, what roots were searched, what source fields remain missing, what lane should run next, and why no result/promotion lane is allowed yet.

