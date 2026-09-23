# SCID Strategy-Field Source Expansion Packet Goal Prompt

Date: 2026-05-12
Owner lane: source-field packet builder only
Evidence class: `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Build the source-safe strategy-field expansion packet that the G0 SCID neutral target synthesis selected as rank 1. The packet must attach or fail-close strategy/source fields to the accepted `3,014` SCID candidate rows without opening validation execution, strategy-edge claims, R/PnL/win-rate/expectancy/performance, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, live behavior, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes.

The goal is to close the exact blocker identified by G0: the neutral future-behavior target grid is source-safe and useful, but it lacks the strategy fields required to turn neutral behavior into preregistered, direction-aware hypotheses. Build those input/source fields first. Do not score them.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G0 synthesis completion audit, route ranking ledger, future source-field requirement ledger, accepted evidence reconciliation, anti-boxing review, and saturation pass from disk.
9. Read the accepted G12 neutral packet audit decision ledger and target packet descriptor freeze/source binding artifacts from disk.

Do not rely on chat memory or compaction memory. If interrupted, regenerate `LIVE_STATE`, reread this prompt and the G0 route artifacts, and continue from disk evidence.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active builder instructions.

In this lane:

- Builder posture is constructive and source-field complete, not result-seeking.
- Anti-boxing means search candidate/source logs, packet builders, manifests, prior route ledgers, source-state artifacts, and local accepted packet files before declaring a field missing.
- Same-evidence-class continuation means every required field must be closed from source, proven impossible from approved artifacts, or converted into an exact prospective capture/source requirement.
- Strategy fields are input/source descriptors only. They are not outcomes, validation labels, performance metrics, or promotion evidence.

The completion audit must record whether both doctrine files were read after preflight, the builder posture applied, searched roots, field closure status, anti-boxing questions pursued, and what was deliberately not answered because it crosses into validation/result scoring/live behavior.

## Hard Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open or change:

- validation execution or result scoring;
- strategy edge claims;
- R, PnL, win-rate, expectancy, profit-factor, performance, cost, slippage, or broker-realized scoring;
- promotion, registry edit, live restart, live behavior, trading logic, trading prompts, risk, safety, execution, canary, selector, or config;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- credentials, remotes, or remote push;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob commits.

## Required Source Fields

For every accepted candidate row, build a field-closure ledger for:

1. canonical candidate id and duplicate/proxy denominator key;
2. symbol, source instrument, source proxy group, session/hour descriptors, partition assignment;
3. intended side/direction if source-safe;
4. intended entry reference and source of entry reference;
5. intended stop reference and source of stop reference;
6. intended target reference and source of target reference;
7. POI type, POI bounds, and POI source;
8. framework/setup family such as OB, FVG, breaker, structural, or source-only unknown;
9. lifecycle/fill/cancel/expiry source status from non-broker-account source-state logs only, if available;
10. lower-timeframe/as-of path availability fields;
11. source-control coverage and not-computable/fail-closed reasons;
12. future orderflow/depth/proxy field requirements needed to explain neutral behavior slices.

Each field must be assigned one status:

- `CLOSED_FROM_SOURCE`
- `FAIL_CLOSED_MISSING_SOURCE_FIELD`
- `PROSPECTIVE_CAPTURE_REQUIRED`
- `FORBIDDEN_IN_THIS_EVIDENCE_CLASS`

Never infer historical intent/order/lifecycle truth from price movement alone.

## Required Source Pursuit Ladder

Do not stop at "missing strategy field" until the approved source-pursuit ladder has been exhausted for that field family.

Search and record, at minimum:

- the accepted SCID as-of packet route and all candidate/bar/descriptor artifacts;
- the G12 neutral target audit and G0 neutral synthesis artifacts;
- the no-API mechanical replay source universe and family path behavior routes;
- prior FPB/source-expansion route artifacts;
- relevant `research/science_program_2026_05/06_outcome_testing/` sibling route ledgers;
- relevant `research/science_program_2026_05/04_goal_prompts/` contracts and emitted prompt packs;
- relevant `shadow_logs/` source-safe candidate, path, lifecycle, registry, diagnostics, nofill, and structural metadata logs;
- relevant `research/program_control/`, `pipeline_state/`, and `knowledge_base/` source-state artifacts;
- absolute local roots and prior worktrees only when the field could be source-safe market/candidate data rather than broker account/order truth.

For every field family, the output must name:

- searched artifact families and paths;
- whether the field was closed from source;
- if not closed, whether the missing truth is recoverable market/source data, non-generatable historical GTOS intent/source-state, or forbidden broker/live/account evidence;
- exact future source/capture/logger field, parser, schema, redaction, as-of rule, and G12 acceptance requirement.

If an allowed same-evidence-class derivation contract can close a field, build it inside this route instead of only naming it. Split only when the next step crosses into G12 audit, validation/result scoring, AI/API, broker account/order evidence, paid/vendor access, raw data commits, live behavior, or another hard forbidden boundary.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/`

Emit at minimum:

- context anchor;
- searched-root/source inventory ledger;
- prerequisite G0/G12 reconciliation ledger;
- candidate strategy-field closure ledger covering all `3,014` rows exactly once;
- field provenance and no-leak allowlist;
- fail-closed missing-field ledger;
- prospective capture/source requirement ledger;
- duplicate/proxy denominator preservation ledger;
- anti-boxing mechanism coverage ledger;
- route decision ledger;
- output manifest;
- standalone verifier;
- focused tests;
- completion audit;
- next G12 audit prompt if the packet is built, or repair prompt if it is not.

The next G12 prompt must be a full controlling prompt file, not just a brief prompt pack. It must require independent row/field/status/source-hash/no-leak/denominator recomputation and fair G12 acceptance/rejection boundaries.

## Verification Requirements

The verifier and focused tests must check:

- exact `3,014` candidate row coverage and no duplicate candidate ids;
- field-status enum validity for every required source field;
- no target-value/result/performance scoring fields introduced;
- no broker account/order/history/deal/position evidence consumed;
- no raw market-data blob commits;
- no prompt/config/risk/safety/execution/canary/selector/source trading-surface edits;
- safe flags remain closed;
- missing fields have exact source/capture requirements, not vague future work;
- output manifest covers every required artifact.

## Required Saturation And Self-Red-Team Pass

Before completion, explicitly answer and pursue same-evidence-class issues exposed by these questions:

- Which field family is most likely to be falsely inferred from price movement rather than source truth?
- Which field family is most likely to hide a post-target or hidden-label leak?
- Which row group has the weakest source-field closure and why?
- Which source artifacts could contain side, setup family, POI, lifecycle, or lower-timeframe path truth but were easy to miss?
- Which fields can be source-derived now through an allowed contract, and which require prospective capture only?
- Which missing fields are market-data recoverable versus non-generatable historical GTOS intent/source-state?
- Which duplicate/proxy denominator choice could make a field appear closed for one projection but not the canonical opportunity?
- What would a skeptical G12 reject if this packet is under-specified, and how does this route preempt that rejection?
- What exact next lane owns any valid question that crosses out of source-field packet evidence class?

If any answer exposes an allowed same-evidence-class gap, pursue it before completion. Do not leave generic "future work" when an exact search, derivation, fail-closed status, or capture requirement can be emitted in this route.

## Allowed Terminal Decisions

Use exactly one:

- `BUILT_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_G12_AUDIT_REQUIRED`
- `REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

## Completion Standard

Mark complete only after:

1. Mandatory preflight and context use are recorded.
2. The accepted G0/G12/target-packet evidence chain is reconciled exactly.
3. Every `3,014` candidate row has a strategy-field closure row exactly once.
4. Every required source field is closed, fail-closed, prospective-capture-required, or forbidden with exact reason.
5. The source-pursuit ladder and saturation/self-red-team pass are complete.
6. The next G12 audit prompt is a full hardened controlling prompt file.
7. No target outcome scoring, validation, edge/performance claim, broker evidence, AI/API, paid/vendor access, raw market-data commit, live behavior, or trading-surface change is opened.
8. Verifier passes.
9. Focused tests pass.
10. Scoped commits are created.
11. `.context/00_core/research_current_state.md` is refreshed if the research state changes materially.
12. Final `python scripts/generate_live_state.py` is run and freshness is recorded.
13. No unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; build the source-safe strategy-field expansion packet for all 3,014 accepted SCID candidates with exact field closure/fail-closed/prospective-capture/forbidden statuses, source-pursuit ladder, saturation pass, and full hardened next G12 prompt; emit packet route, verifier, focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement, and mark complete only when the prompt file's completion standard is fully satisfied.`
