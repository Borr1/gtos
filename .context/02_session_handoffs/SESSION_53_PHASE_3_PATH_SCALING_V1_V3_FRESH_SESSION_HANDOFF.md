# Session 53 Handoff - Phase 3 Path Scaling V1/V2/V3 Fresh Session Brief

**Date:** 2026-05-02  
**Status:** Fresh-session handoff prepared  
**Scope:** research/tooling only  
**Current HEAD at handoff prep:** `2d7bf6e fix(monitoring): suppress ended-session false criticals`  
**Key prior research commit:** `ee25fb1 research(phase3): add raw OHLC path ablation v0`  
**Do not infer:** live trading improvement, alpha promotion, prompt change, config change, or risk-policy change  

## Why This Handoff Exists

The owner wants the next heavy session to continue the path-scaling research with a clean context window. V0 was intentionally simple. The next work must engineer the full idea carefully, layer by layer:

1. V1: lower-timeframe path resolution for lock outcomes.
2. V2: structural/as-of level selection.
3. V3: risk-budgeted reentry and composite path management.
4. Only after each layer is separately tested, reported, synthesized, and ambiguity-cleared should the next layer begin.

This handoff is meant to preserve the exact research vision and discipline so the fresh session does not flatten the idea into a simple trailing-stop test.

## Mandatory Pre-Flight For The Fresh Session

Run and read these first:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. This handoff:
   - `.context/02_session_handoffs/SESSION_53_PHASE_3_PATH_SCALING_V1_V3_FRESH_SESSION_HANDOFF.md`
4. `.context/00_core/quick_reference_card.md`
5. Prior handoff:
   - `.context/02_session_handoffs/SESSION_52_PHASE_3_REPLAY_LAB_MATRIX_FOLLOWUP_HANDOFF.md`

Then read the Phase 3 raw/path artifacts:

- `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_AND_PATH_SCALING_PROTOCOL_2026-05-01.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md`
- `scripts/run_raw_ohlc_path_ablation_v0.py`
- `tests/test_raw_ohlc_path_ablation_v0.py`
- `scripts/run_raw_ohlc_prequential_replay.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PREQUENTIAL_REPLAY_PROTOCOL_2026-05-01.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PREQUENTIAL_REPLAY_FOLLOWUP_ANALYSIS_2026-05-01.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_BLOCKED_CONTROLS_FOLLOWUP_ANALYSIS_2026-05-01.md`

Also read the methodology guardrails:

- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_PROTOCOL_2026-05-01.md`
- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md`
- `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01.md`
- `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
- `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_V1.json`
- `research/ml_program/MASTER_BACKLOG.md`

## Current Workspace Warning

At handoff prep time, the worktree had live/runtime dirt:

- `.context/LIVE_STATE.md`
- `pipeline_state/m5_refinement.json`
- `shadow_logs/daily_pnl.json`
- `src/components/tick_capture.py`
- untracked `pipeline_state/.orch_shutdown_*.json`
- untracked shadow logs including `slippage.jsonl`, `touch_count_gate_decisions.jsonl`, and daily PnL/anomaly files

Do not stage or commit live/runtime dirt unless the owner explicitly asks and the change is understood. The next path-scaling work should commit only scoped research/tooling artifacts.

## V0 Result To Carry Forward

Artifact:

- `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md`

Run scope:

- `FULL_AVAILABLE_CORPUS`
- rows replayed: `205197`
- TAKE rows: `23483`
- refinable setups: `12831`
- path timeframe: `M15`
- blocked controls included: `true`
- first TAKE: `2022-02-07T13:30:00+00:00`
- last TAKE: `2026-04-30T17:00:00+00:00`
- promotion verdict: `NO_PROMOTION_VERDICT`

Top-line V0 findings after `0.05R` round-turn cost sensitivity:

| Variant | Net mean R | Key read |
|---|---:|---|
| `J46_J49_ONLY` | `+0.190128` | Best overall mean R |
| `BASE_RAW_FIXED_TP` | `+0.176720` | Shallowest reported 0.05R-cost max drawdown |
| `PATH_LOCK_HALF_GAIN_V0` | `+0.170370` | Best lock-only overall, but still below J46-J49 |
| `PATH_LOCK_CONSERVATIVE_V0` | `+0.148801` | Safer ladder, weaker mean |
| `PATH_LOCK_EARLY_BE_V0` | `+0.111497` | Too many same-bar ambiguities and weaker global result |

Critical V0 synthesis:

- J46-J49 remains the best universal baseline.
- Lock-only did not beat J46-J49 globally.
- Lock-only did reveal cohort sensitivity:
  - target-family best-lock minus J46 at `0.05R` cost: `+0.033406`
  - primary-family best-lock minus J46: `-0.053504`
  - cleared-non-primary best-lock minus J46: `+0.169881`
- The biggest measurement blocker is same-bar ordering:
  - `PATH_LOCK_EARLY_BE_V0` produced `2598` unresolved same-bar cases.
- Therefore, V1 must solve lower-timeframe path ordering before reentry or structural levels are trusted.

## Owner Vision - Preserve This Exactly

The owner is not asking for a generic trailing stop. The idea is a full path-management architecture:

- Worst case should remain capped at `-1R`.
- The goal is all of:
  - maximize R,
  - reduce drawdown,
  - improve probability of passing challenge/risk objectives,
  - not simply improve win rate.
- The idea is meant to complement J46-J49, not necessarily replace it.
- Price often moves favorably before failing; the owner wants to study whether that path can be harvested without increasing worst-case risk.
- Decisions should be made from the market state in real time: structure, liquidity, displacement, volume/tick activity, volatility, lower-timeframe pullbacks, and momentum changes.
- Execution may need lower timeframes than the original M15 setup. A trade can be selected on M15, while lock/reentry decisions may need M5 or M1.
- Costs matter: spread, slippage, commission, and extra reentry round turns must be charged.
- Final result runs must use the whole available corpus. Bounded runs are only debug/smoke.

Owner wording to preserve as design intent:

> Worst case scenario is always 1R; the rest on to make it more likely to be profitable is up to you and the data.

> It kind of completes the J46-J49. I had the idea when I thought about what we were doing with waiting for 3R and 6R and basically waiting the whole time until it hits. I don't think it hits quickly for the 3R and 6R, and it goes up and down in between, and I thought maybe that's an opportunity to ride the same wave but with more returns.

> The path scaling really needs to be engineered to a sweet spot and calculated based on all the data we have on the optimal level to place the lock profit, to which level is the reentry exactly, the lot sizes, the risk, the calculated output, everything needs to be calculated in detail.

> The execution happens more in the lower timeframe to know exactly when and where to reenter and when and where to place the BE level or lock profit level.

Interpretation:

The system should eventually become a path state machine with pre-registered level families, lower-timeframe path resolution, risk-budgeted reentries, and cost-aware outcome accounting. It must not become an unconstrained optimization grid.

## Non-Negotiable Research Rules

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization disguised as research.
- No paid AI/API calls.
- No push without explicit approval.
- No same-dataset promotion claim.
- Always emit `NO_PROMOTION_VERDICT` unless a separate future/prospective promotion dossier exists.
- Every final result must be full-corpus unless explicitly labeled `BOUNDED_DIAGNOSTIC`.
- Every result/report must include:
  - numbers,
  - synthesis,
  - ambiguities,
  - opened questions,
  - next steps.
- Do not advance V1 -> V2 -> V3 until the current layer has no unresolved ambiguity that blocks the next layer.

## V1 - MTF Path-Resolved Lock Engine

Purpose:

Replace V0's M15-only path ordering with a lower-timeframe resolver. V1 should answer: when M15 says fill/lock/SL/TP may have occurred in the same bar, does M5 or M1 resolve the sequence materially differently?

V1 is not a new strategy. It is measurement infrastructure.

Required V1 features:

- Load M15 setup stream exactly as V0 does.
- For path resolution, prefer lower timeframe in this hierarchy:
  - M1 if available for symbol/time window,
  - else M5 if available,
  - else M15 fallback.
- Never use lower-timeframe candles before the setup decision clock.
- Never use future bars to choose levels.
- Emit coverage diagnostics:
  - M1 available rows/windows,
  - M5 available rows/windows,
  - M15 fallback count,
  - unresolved same-bar count before and after refinement.
- Preserve V0 variants:
  - `BASE_RAW_FIXED_TP`
  - `J46_J49_ONLY`
  - `PATH_LOCK_CONSERVATIVE_V0`
  - `PATH_LOCK_HALF_GAIN_V0`
  - `PATH_LOCK_EARLY_BE_V0`
- Compare V0 M15-only versus V1 MTF-resolved outcomes.
- Keep cost sensitivity.
- Keep DSR/PBO/effective_N language as diagnostics only.

V1 tests must cover:

- lower-timeframe rows start strictly after setup candle close,
- same-bar M15 ambiguity resolved by M1/M5 order,
- no future candle exposure,
- fallback to M15 when lower timeframe unavailable,
- J46-J49 unchanged when no ambiguity exists,
- cost accounting unchanged,
- report says `NO_PROMOTION_VERDICT`.

V1 acceptance criteria before V2:

- Full-corpus report exists.
- Same-bar ambiguity change is quantified.
- Outcome deltas versus V0 are explained.
- Any cohort where MTF resolution changes the conclusion is identified.
- No unresolved clock/as-of/data-coverage ambiguity remains.

Suggested V1 artifact names:

- `scripts/run_raw_ohlc_path_ablation_v1_mtf.py`
- `tests/test_raw_ohlc_path_ablation_v1_mtf.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_PROTOCOL_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_REPORT_2026-05-02.md`

## V2 - Structural Level Selector

Purpose:

Replace fixed R anchors with as-of structural levels. V2 should answer: can predefined market structure identify better lock/pullback levels than fixed R anchors without post-hoc fitting?

V2 should not begin until V1 is accepted.

Allowed first V2 level families:

1. Fixed-R control family:
   - keep V1 fixed levels as benchmark.
2. Structure family:
   - prior M15/M5 swing high/low,
   - session high/low,
   - equal high/low if detectable as of replay clock.
3. POI boundary family:
   - OB boundary,
   - breaker boundary,
   - FVG edge or midpoint where already known as of clock.
4. Volatility/displacement family:
   - ATR-normalized favorable extension,
   - displacement candle extension/halfback.
5. Optional round-number family:
   - only if symbol-specific increments are pre-registered before final run.

V2 must not sweep a large grid. It should register a small number of level selectors before the final run.

V2 tests must cover:

- level known as of replay clock,
- no future swing confirmation leakage,
- selector returns no level when structure is unavailable,
- selector handles long/short symmetrically,
- fixed-R benchmark remains reproducible,
- report separates level-family performance.

V2 acceptance criteria before V3:

- Full-corpus report exists.
- Level-family performance is separated by target family, primary family, cleared non-primary targets, negative controls, and blocked controls.
- No selector relies on future structure.
- Any apparent winner is checked against negative controls and blocked controls.
- The final selected V3 candidate levels are pre-registered, not chosen ad hoc.

Suggested V2 artifact names:

- `scripts/run_raw_ohlc_path_scaling_v2_levels.py`
- `tests/test_raw_ohlc_path_scaling_v2_levels.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_LEVEL_SELECTOR_PROTOCOL_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_LEVEL_SELECTOR_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_LEVEL_SELECTOR_REPORT_2026-05-02.md`

## V3 - Risk-Budgeted Reentry Engine

Purpose:

Implement the actual full path-scaling idea: lock profit, allow structured pullback reentry, and manage a composite position while keeping worst-case risk capped.

V3 should not begin until V2 is accepted.

Required V3 state machine:

```text
ENTRY_PENDING
 -> ACTIVE_INITIAL
 -> LOCK_ARMED
 -> PROFIT_LOCKED
 -> PULLBACK_ZONE_ARMED
 -> REENTRY_FILLED
 -> COMPOSITE_POSITION_MANAGED
 -> FINAL_EXIT
```

Risk rule:

- The reported strategy must keep total worst-case outcome at or above `-1R`.
- If a reentry would make worst-case worse than `-1R`, either:
  - resize it,
  - skip it,
  - or explicitly label the variant as increased-risk and keep it out of promotion comparisons.

Required V3 accounting:

- base R from initial entry to initial structural SL,
- original position realized/locked R,
- reentry distance in base-R units,
- reentry size,
- incremental risk,
- total worst-case after each state transition,
- spread/slippage/commission cost per completed round turn,
- additional cost per reentry,
- final composite R.

V3 tests must cover:

- reentry sizing caps worst-case at `-1R`,
- same-lot reentry is rejected when it violates risk budget,
- multiple reentries cannot silently increase risk,
- missed-pullback runner remains alive,
- direct runner still participates,
- reentry costs are charged,
- long/short symmetry,
- report labels increased-risk variants separately if any are tested,
- `NO_PROMOTION_VERDICT` remains.

V3 acceptance criteria before architecture comparison:

- Full-corpus report exists.
- Risk-budget audit has zero violations for promotion-eligible variants.
- Reentry fill rate and missed-runner rate are quantified.
- Incremental R per incremental cost/risk is reported.
- Controls do not show the same or better behavior for the wrong reasons.
- Any remaining ambiguity is documented as blocker or future lane.

Suggested V3 artifact names:

- `scripts/run_raw_ohlc_path_scaling_v3_reentry.py`
- `tests/test_raw_ohlc_path_scaling_v3_reentry.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_PROTOCOL_2026-05-02.md`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_SPEC_V1.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_REPORT_2026-05-02.md`

## Architecture Comparison After V3

Only after V1, V2, and V3 have accepted reports should the fresh session or a later session run the full architecture comparison:

| Variant | Meaning |
|---|---|
| `BASE_RAW_FIXED_TP` | raw fixed TP/SL |
| `J46_J49_ONLY` | current position-management baseline |
| `L2_ONLY_FIXED_TP` | deterministic L2 filter effect |
| `L2_PLUS_J46_J49` | current architecture stack |
| `MTF_LOCK_ONLY` | V1/V2 lock-only with lower-timeframe resolution |
| `STRUCTURAL_LOCK_ONLY` | V2 structural lock without reentry |
| `STRUCTURAL_LOCK_REENTRY` | V3 full path scaling |
| `L2_PLUS_STRUCTURAL_LOCK_REENTRY` | complete candidate architecture |

The comparison must include:

- target family,
- primary controlled family,
- cleared non-primary targets,
- negative controls,
- blocked dominance controls,
- DSR diagnostic,
- PBO diagnostic,
- effective_N diagnostic,
- drawdown/R distribution,
- cost sensitivity,
- full event-log audit.

## Fresh Session Starter Prompt

Use this in the next session:

```text
Phase 3 path-scaling continuation from Session 53 handoff.

Pre-flight first:
1. Run `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`
3. Read `.context/02_session_handoffs/SESSION_53_PHASE_3_PATH_SCALING_V1_V3_FRESH_SESSION_HANDOFF.md`
4. Read `.context/00_core/quick_reference_card.md`
5. Read:
   - `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_AND_PATH_SCALING_PROTOCOL_2026-05-01.md`
   - `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_SPEC_V1.json`
   - `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md`
   - `scripts/run_raw_ohlc_path_ablation_v0.py`
   - `tests/test_raw_ohlc_path_ablation_v0.py`
   - `scripts/run_raw_ohlc_prequential_replay.py`
   - `research/phase_3_external_feed_validation/RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`

Objective:
Start V1 only: build the MTF path-resolved lock engine. Do not jump to V2/V3 until V1 is fully implemented, tested, full-corpus replayed, reported, synthesized, and ambiguity-cleared.

V1 goal:
Resolve V0's M15 same-bar ambiguity with M1/M5 where available, preserve no-leak discipline, compare V0 M15-only versus V1 MTF-resolved outcomes, include cost sensitivity and methodology diagnostics, and keep `NO_PROMOTION_VERDICT`.

Critical constraints:
- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- Final result must be full available corpus.
- Every report must include synthesis, ambiguity ledger, opened questions, and next steps.
- Do not advance to V2 until V1 has no blocking ambiguity.
```

## Final Note For The Fresh Session

Be ambitious about engineering, but conservative about claims. The owner wants the full idea explored, not prematurely simplified. The standard is not "write a script that runs"; the standard is a reusable research-lab component with protocol/spec/report artifacts, focused tests, full-corpus results, and a clear synthesis after each layer.

