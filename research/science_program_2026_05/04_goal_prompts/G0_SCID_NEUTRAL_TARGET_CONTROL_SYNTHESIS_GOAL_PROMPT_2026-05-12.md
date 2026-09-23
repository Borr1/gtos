# G0 SCID Neutral Target Control Synthesis Goal Prompt

Date: 2026-05-12
Owner lane: G0 synthesis/control route
Evidence class: `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY`
Input G12 audit route: `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/`

## Objective

Synthesize the G12-accepted SCID as-of neutral target execution packet into the strongest next research route without crossing into validation execution, strategy-edge claims, or live behavior.

This is the first G0 synthesis after source-safe neutral future behavior was accepted by G12. Treat it as a high-value route-selection stage. The job is not to be conservative and say "no edge yet"; the job is to extract every source-safe learning, limitation, route implication, and next-lane design that the accepted neutral packet can honestly support, while keeping the evidence boundary exact.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the G12 neutral target audit completion audit, decision ledger, saturation/self-red-team ledger, aggregate/matrix recomputation audit, not-computable audit, no-leak audit, and next prompt pack from disk.
9. Read the target neutral packet completion audit, aggregate matrix, partition/symbol/session matrix, concentration denominator audit, failure anatomy ledger, and interpretation limits from disk.

Do not rely on chat memory. If interrupted or compacted, regenerate `LIVE_STATE`, reread this prompt, reread the core doctrine files, reread the G12 audit completion audit, and continue from disk artifacts.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active route-selection instructions.

In this lane, their application is:

- G0 posture is synthesis/control, not passive summary.
- Be aggressive and creative in extracting next research routes from accepted neutral behavior.
- Do not collapse back into only the current OB-retest edge or current GTOS production box.
- Do not convert neutral behavior into edge, win rate, expectancy, or validation.
- Separate what is accepted, what is suggestive, what is blocked by missing strategy fields, and what exact route can close it.
- Push same-synthesis-class questions until the route ranking, required source fields, hypotheses, and next prompt(s) are explicit.

The completion audit must record:

- whether `goal_session_research_discipline.md` was read after preflight;
- whether `research_operating_doctrine.md` was read after preflight;
- lane posture: `G0_SYNTHESIS_CONTROL_ROUTE_SELECTION`;
- anti-boxing questions pursued;
- outside-current-edge mechanisms considered;
- exact accepted evidence boundary;
- exact route ranking and why each route is or is not next;
- what this G0 deliberately did not answer because it crosses into validation/result scoring/live behavior.

## Hard Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open or change:

- validation execution;
- strategy edge claims;
- R, PnL, win-rate, expectancy, profit-factor, performance, cost, slippage, or broker-realized scoring;
- promotion, registry edit, live restart, live behavior, trading logic, or trading prompts;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- credentials, remotes, or remote push;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, or `.bin` market-data blob commits;
- prompts/config/risk/safety/execution/canary/selector/source trading surface changes.

## Required Synthesis Work

Build a dedicated route under:

`research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/`

The route must do all of the following from committed artifacts:

1. Reconcile the accepted G12 audit decision:
   - terminal decision `ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY`;
   - `3,014` candidates;
   - `2,432` sealed rows;
   - `582` stress rows;
   - `24,112` terminal statuses;
   - `20,292` computable rows;
   - `3,820` fail-closed not-computable rows;
   - `9/9` bounded SCID segments rehashed;
   - zero target-row hash mismatches;
   - zero target-value mismatches.
2. Summarize what the neutral target packet actually tells us:
   - availability by target family and horizon;
   - neutral close-to-close behavior by symbol, session, hour, denominator group, and source proxy group;
   - neutral high/low excursion behavior by the same controls;
   - source coverage/failure anatomy;
   - concentration and small-denominator risks;
   - sealed versus stress differences.
3. Extract source-safe learning without overclaiming:
   - which neutral behavior slices are strongest;
   - which are broad versus concentrated;
   - which are likely baseline/session/volatility effects;
   - which need strategy fields before they mean anything;
   - which are negative/null learning.
4. Perform anti-boxing synthesis across at least these mechanism families:
   - session/hour/time-of-day microstructure;
   - volatility compression/expansion and range-state effects;
   - drift/momentum/reversion path shape;
   - source proxy/instrument group differences;
   - excursion asymmetry and path hazard timing;
   - future strategy-field needs for side, intended entry, stop, target, POI, OB/FVG/breaker family, lifecycle/fill/cancel;
   - future orderflow/depth/proxy fields that could explain neutral differences;
   - adversarial baselines and whether the neutral behavior is likely market-state-only.
5. Decide the strongest next route, with ranked alternatives:
   - strategy-field source expansion packet;
   - preregistered result-design lane;
   - source-field/descriptor expansion lane;
   - broader sealed SCID pool expansion lane;
   - negative-learning/failure-anatomy route;
   - orderflow/proxy source-control route;
   - no-API mechanical strategy-family replay route.
6. For the rank-1 route, emit a full controlling prompt file under `research/science_program_2026_05/04_goal_prompts/`, not only a short prompt pack. It must follow the prompt hardening standard in `.context/00_core/goal_session_research_discipline.md`.
7. If more than one route is legitimately necessary in parallel, emit separate prompt files with non-overlapping evidence classes and explain priority/order.

## Required Outputs

Emit versioned artifacts including at minimum:

- context anchor;
- decision ledger;
- accepted evidence reconciliation;
- neutral behavior synthesis;
- anti-boxing mechanism review;
- concentration and denominator risk review;
- not-computable/failure-anatomy synthesis;
- future source-field requirement ledger;
- route ranking ledger;
- next prompt file(s);
- verifier;
- focused tests;
- completion audit.

## Required Saturation And Self-Red-Team Pass

Before completion, explicitly answer:

- Are we over-reading neutral behavior as strategy edge?
- Are we under-using neutral behavior by treating it as meaningless just because it is not strategy-labeled yet?
- Which slices look strongest, and are they concentrated or broad?
- Which slices are likely explained by session-only, volatility-only, source-proxy-only, or baseline effects?
- Which missing strategy/source fields would convert neutral behavior into a valid next hypothesis?
- Which outside-current-edge mechanism families did we consider, and what did each produce?
- What exact next route gets us closer to actual edge testing fastest without violating evidence boundaries?
- What would a later G12 reject if the next prompt is weak, and how does the emitted next prompt prevent that?

If the saturation pass exposes a same-synthesis-class gap, pursue it before completion. If it crosses into validation, result scoring, broker evidence, AI/API, paid/vendor access, live behavior, or raw data commits, freeze it into the next prompt file instead.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE`
- `REPAIR_G0_SYNTHESIS_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

## Completion Standard

Mark complete only after:

1. Mandatory preflight and context use are recorded.
2. The G12 accepted evidence is reconciled exactly.
3. Neutral behavior synthesis and anti-boxing review are emitted.
4. Route ranking is explicit and justified.
5. Rank-1 next prompt file is emitted and hardened.
6. Verifier passes.
7. Focused tests pass.
8. Scoped commits are created.
9. `.context/00_core/research_current_state.md` is refreshed if the research state changes materially.
10. Final `python scripts/generate_live_state.py` is run and freshness is recorded.
11. No unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; synthesize the G12-accepted 3,014-candidate, 20,292-computable neutral target packet into the strongest ranked next research route without overclaiming; pursue anti-boxing/source-field/failure-anatomy/route-selection questions until the rank-1 next prompt is explicit and hardened; emit G0 route, verifier, focused tests, next prompt file(s), scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
