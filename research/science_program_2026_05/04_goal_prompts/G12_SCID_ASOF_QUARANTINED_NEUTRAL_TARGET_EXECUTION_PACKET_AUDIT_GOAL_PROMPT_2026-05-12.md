# G12 SCID As-Of Quarantined Neutral Target Execution Packet Audit Goal Prompt

Date: 2026-05-12
Owner lane: independent G12 audit
Evidence class: `G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY`
Target packet: `research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/`

## Objective

Independently audit the SCID as-of quarantined neutral-target execution packet and decide whether it can be accepted as source-safe neutral target execution packet control evidence only.

This audit must be real G12 work, not a surface checklist. Reconstruct the evidence chain from disk, independently recompute the packet facts that can be recomputed from accepted inputs, attack no-leak/source/as-of/duplicate/denominator weaknesses, and accept the packet only if it survives. Do not invent objections merely because the packet is neutral rather than strategy-performance evidence. The evidence class is intentionally neutral target behavior, not edge, validation, R, PnL, win rate, expectancy, promotion, or live behavior.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the target packet completion audit and output manifest from disk.
9. Read the predecessor acceptance/control artifacts needed to prove this packet was allowed:
   - G12 target/horizon repair audit acceptance.
   - SCID as-of candidate input packet acceptance.
   - G0 sealed/stress validation design.
   - accepted SCID segment/source hash manifests.

Do not rely on chat memory. If context compaction, interruption, or uncertainty occurs, regenerate `LIVE_STATE`, reread this prompt and the core doctrine files, reread the target packet completion audit, and resume from disk artifacts.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active audit instructions, not background reading.

In this lane, their application is:

- G12 posture is skeptical, independent, and acceptance-focused.
- Builder/discovery anti-conservatism is not imported as blind acceptance.
- Audit skepticism must not become conservative theater. Reject only for concrete source, no-leak, recomputation, denominator, evidence-class, artifact, or verifier failures.
- Do not reject because neutral targets are not strategy performance. That is the declared evidence boundary.
- Pursue every same-audit-class ambiguity until it is recomputed, ruled out, or converted into an exact repair requirement.
- Separate warnings from terminal blockers. A warning is not a blocker unless it changes source validity, row eligibility, target computation, no-leak status, denominator correctness, or evidence-class interpretation.

The final completion audit must explicitly record:

- whether `goal_session_research_discipline.md` was read after preflight;
- whether `research_operating_doctrine.md` was read after preflight;
- lane posture: `G12_INDEPENDENT_AUDIT_ACCEPTANCE_FOCUSED`;
- anti-boxing/saturation questions pursued;
- exactly what was independently recomputed;
- exact blocker, warning, and accepted-evidence boundaries;
- proof-or-impossibility stop condition used;
- doctrine requirements deliberately not answered because they cross into validation, promotion, AI/API, broker account/order evidence, or live behavior.

## Hard Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open or change:

- validation execution beyond source-safe audit recomputation;
- strategy edge interpretation;
- R, PnL, win-rate, expectancy, profit-factor, cost, slippage, or broker-realized performance scoring;
- promotion, registry edit, live restart, live behavior, or trading logic;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- credentials, remotes, or remote push;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, or `.bin` market-data blob commits;
- prompts/config/risk/safety/execution/canary/selector/source trading surface changes.

## Required Independent Recomputations

Do not accept artifact counts only because the target packet says them. Build a G12 audit route that recomputes or independently verifies the following from target and predecessor artifacts:

1. Parse every target JSON/JSONL artifact and record row counts.
2. Recompute prerequisite acceptance status from predecessor artifacts.
3. Recompute source hash bindings for all required accepted inputs, including accepted SCID segments and packet source manifests.
4. Recompute the target packet universe:
   - `3,014` candidate rows;
   - `2,432` sealed rows;
   - `582` stress rows;
   - `365` discovery exclusions;
   - `7` denominator groups;
   - `7,567` source-control bar rows.
5. Recompute the terminal grid:
   - target families exactly `neutral_close_to_close_return_m15_horizons_v1` and `neutral_high_low_excursion_m15_horizons_v1`;
   - horizons exactly `[1, 4, 16, 32]`;
   - exactly `24,112` candidate/horizon/family terminal statuses;
   - exactly one terminal status for every candidate, horizon, and target-family combination.
6. Recompute target values from source-control bar inputs for all computable rows, or perform a full deterministic row-hash recomputation if the target route already exposes sufficient target-row hashes.
7. Recompute not-computable classifications and reason counts. Fail if any row is silently dropped, imputed, forward-filled, or given a target value without accepted source bars.
8. Recompute aggregate distributions and key partition/symbol/session matrices from row results and not-computable ledgers, including at minimum total rows, computable rows, not-computable rows, denominator-group counts, session counts, symbol/source-proxy counts, and the declared neutral label `positive_return_fraction_not_win_rate`.
9. Recompute concentration/duplicate denominator facts and verify no discovery-exposed, rejected, impossible, blocked, or out-of-partition rows leak into the accepted packet denominator.

If a full recomputation is too slow, checkpoint and continue. Speed is not a completion excuse. A sampled audit is acceptable only as an additional diagnostic, not as a substitute for required full-count/row-grid verification.

## Required No-Leak And Evidence-Class Checks

Verify all of the following:

- The pre-target freeze packet exists and predates target computation artifacts.
- Descriptors were frozen before target values and use only source bars ending at or before the entry reference/as-of time.
- Target computation uses only future accepted source-control bars allowed by the frozen neutral target/horizon rulebook.
- No side, intended entry, stop, target, POI, OB/FVG/breaker family, lifecycle/fill/cancel, broker/account/order/history/deal/position, path-label, post-hoc strategy label, or hidden performance field enters source-safe descriptors or denominators.
- `positive_return_fraction_not_win_rate` remains explicitly neutral and must not be renamed, interpreted, or counted as strategy win rate.
- The packet does not convert neutral target behavior into validation-safe strategy performance.
- All not-computable rows fail closed with exact reasons and stay outside computable neutral target aggregates except for availability/failure-anatomy accounting.
- All `365` discovery exclusions remain excluded.
- Sealed and stress rows remain separate; stress rows do not silently enter sealed-only counts.
- The four adversarial baselines remain present as controls when referenced and are not promoted into strategy evidence.
- Dirty live/runtime/shadow files are recorded as unrelated when applicable and not staged or committed.
- The committed diff for the G12 audit contains no forbidden live-surface paths.
- The route commits no raw market-data blobs and preserves LFS/large-file rules.

## Required G12 Artifacts

Build a dedicated audit route under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/`

Emit versioned artifacts including at minimum:

- context anchor with HEAD, target packet commit, controlling prompt path, preflight status, and dirty-state scope;
- decision ledger with terminal decision and exact evidence boundary;
- prerequisite acceptance audit;
- source hash and input binding audit;
- full terminal-grid recomputation audit;
- row-target recomputation or deterministic row-hash audit;
- not-computable reason audit;
- aggregate/matrix recomputation audit;
- no-leak/evidence-class audit;
- duplicate/concentration/denominator audit;
- dirty-state/raw-blob/live-surface diff audit;
- saturation and self-red-team ledger;
- next prompt pack:
  - if accepted, emit a G0 synthesis/control prompt that can decide whether the neutral behavior evidence opens a future strategy-field source-expansion or preregistered result-design lane;
  - if rejected, emit an exact repair prompt with every blocker tied to file, row family, source, parser, hash, no-leak rule, or evidence-class breach;
- standalone verifier;
- focused tests;
- completion audit with `can_mark_goal_complete=true` only if all required checks pass.

## Required Saturation And Self-Red-Team Pass

Before marking complete, explicitly answer and pursue same-audit-class issues exposed by these questions:

- What exact mistake would let neutral target behavior be mistaken for strategy performance?
- What exact mistake would let stress rows, discovery rows, rejected rows, or excluded rows leak into sealed denominators?
- Which descriptor fields are most likely to be post-target or hidden-label leaks?
- Which target computations are most vulnerable to off-by-one as-of interval bugs?
- Which not-computable reason could hide an imputation or silent row drop?
- Which duplicate/proxy/denominator choice could double-count opportunity?
- Which aggregate label could be misread as win rate, expectancy, or edge?
- What would a skeptical but fair G12 reviewer reject, and did this audit independently test it?
- What exact future lane owns any valid next step that crosses out of this audit evidence class?

If any answer reveals an allowed audit-class gap, pursue it before completion. If it crosses into validation, strategy scoring, AI/API, broker evidence, paid/vendor access, raw data commits, live behavior, or G0 synthesis, freeze it as an exact next prompt instead.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY`
- `REJECT_NEUTRAL_TARGET_PACKET_REPAIR_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

Acceptance means only this:

The packet is accepted as quarantined source-safe neutral target execution packet control evidence. It remains `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. It does not authorize validation execution, strategy-edge claims, R/PnL/win-rate/expectancy/performance claims, promotion, live behavior, AI/API, broker evidence, or raw market-data commits.

## Completion Standard

Mark the goal complete only after:

1. Mandatory preflight and mandatory context use are recorded.
2. The audit route artifacts are emitted.
3. Full target packet parsing and recomputation checks pass or exact blockers are recorded.
4. No-leak, denominator, source-hash, dirty-state, raw-blob, and live-surface checks are complete.
5. Standalone verifier passes.
6. Focused tests pass.
7. Scoped commits are created.
8. `.context/00_core/research_current_state.md` is refreshed if the research state changes materially.
9. Final `python scripts/generate_live_state.py` is run and freshness is recorded.
10. No unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; independently recompute the 3,014-candidate, 2,432-sealed, 582-stress, 24,112-status neutral target packet and all source/no-leak/denominator/not-computable/aggregate facts; pursue every same-audit-class ambiguity until accepted, rejected with exact repair, proven impossible, or reduced to exact owner/access/source/capture requirement; emit audit route, verifier, focused tests, next G0-or-repair prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
