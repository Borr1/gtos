# Session 52 Handoff - Phase 3 Replay Lab And Matrix Follow-Up

**Date:** 2026-05-01  
**Status:** Phase 3 research/tooling continuation complete  
**Latest commit at handoff:** `0375e38` before final dominance-audit commit in this session  
**Scope:** research/tooling only  
**Do not infer:** live trading improvement, alpha promotion, prompt change, config change, or risk-policy change  

## What This Session Built

Session 52 converted the Phase 3 truth-layer work into a controlled historical replay lab and matrix follow-up map.

Key commits before this handoff:

- `d88960e research(phase3): add historical prequential replay lab`
- `0375e38 research(phase3): replay registered truth-layer matrix`

The final dominance-audit commit should be the next commit after this handoff.

## New Replay Lab Boundary

The replay lab uses prequential replay:

1. historical row is sorted by `candle_close_utc`
2. strategy receives only an as-of observation projection
3. strategy decides `TAKE` / `SKIP`
4. scorer attaches hidden truth/outcome/refinement fields after decision

Primary artifact:

- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_PROTOCOL_2026-05-01.md`
- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json`
- `scripts/run_truth_layer_prequential_replay.py`

Guardrail result on full historical truth-layer input:

- rows replayed: `205197`
- duplicate opportunity keys: `0`
- invalid clock rows: `0`
- forbidden future-field exposure: `0`
- external as-of violations: `0`
- AI calls: `0`
- integrity: `PASS`

Promotion verdict remains `NO_PROMOTION_VERDICT` because this is same-dataset historical research and DSR/PBO/effective_N/prospective confirmation are not computed by the replay harness.

## Registered Matrix Replay Result

The full 44-candidate registered matrix was replayed under the same no-leak boundary.

Artifact:

- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md`
- `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_STRATEGY_REGISTERED_MATRIX_V1.json`
- `scripts/run_truth_layer_registered_matrix_replay.py`

Headline matrix result:

- candidates: `44`
- rows replayed: `205197`
- actions taken: `91407`
- resolved rows: `18541`
- mean R: `+0.128559`
- WR: `45.4237%`
- guardrails: `PASS`
- promotion verdict: `NO_PROMOTION_VERDICT`

Interpretation:

- The pooled matrix is not the answer; it is heterogeneous.
- `5` strong discovery leads.
- `23` positive but unstable.
- `3` positive but dominated.
- `12` negative/flat controls.
- `1` marginal positive.

## Follow-Up Lanes Frozen

The follow-up registry is:

- `research/phase_3_external_feed_validation/PRE_REGISTERED_TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_2026-05-01.md`
- `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_V1.json`

### Lane 1 - Original Primary Controlled Family

Keep separate. Do not mix into broader matrix ranking:

- `USDJPY|tokyo|bearish|D1`
- `GBPJPY|tokyo|bullish|D1`

### Lane 2 - Non-Primary Strong Leads

These are now the cleared diagnostic targets for the fresh raw-OHLC replay adapter session:

- `USDJPY|london|bearish|D1`
- `USDJPY|tokyo|bearish|H4+H1_consensus`
- `XAGUSD|london|bullish|D1`

Dominance audit result:

- family resolved rows: `655`
- family mean R: `+0.403276`
- cohorts clear: `3/3`
- family status: `CLEAR_DIAGNOSTIC_ONLY`

Per-cohort audit:

| cohort | n | mean R | top year share | top-year-excluded mean R | audit status |
|---|---:|---:|---:|---:|---|
| `USDJPY|london|bearish|D1` | 154 | +0.428571 | 0.337662 | +0.642157 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY |
| `USDJPY|tokyo|bearish|H4+H1_consensus` | 252 | +0.387224 | 0.341270 | +0.324780 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY |
| `XAGUSD|london|bullish|D1` | 249 | +0.403878 | 0.357430 | +0.354791 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY |

Important nuance:

- XAGUSD has a negative 2024 year with only 12 resolved rows.
- Registered valid-year minimum is 30 resolved rows, so it does not block the diagnostic lane.
- This should still be visible in raw-OHLC work.

### Lane 3 - Dominance Watchlist

These remain blocked from deeper work unless a separate dominance/fold-rescue protocol is registered:

- `NAS100|ny|bullish|D1`
- `US30_cash|ny|bullish|H4+H1_consensus`
- `XAUUSD|ny|bullish|D1`

Dominance audit result:

- family resolved rows: `1262`
- family mean R: `+0.456411`
- cohorts clear: `0/3`
- family status: `BLOCKED_DIAGNOSTIC_ONLY`
- blocker: `single_year_dominance`

## Dominance Audit Artifact

Audit script:

- `scripts/analyze_truth_layer_matrix_followup_dominance.py`

Audit report:

- `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01.md`

Audit output summary:

- rows scanned: `205197`
- duplicate keys: `0`
- AI calls: `0`
- promotion verdict: `NO_PROMOTION_VERDICT`

## Next Fresh Session Objective

Start the larger engineering move: raw-OHLC prequential replay adapter.

Recommended first target set:

1. Original primary controlled family:
   - `USDJPY|tokyo|bearish|D1`
   - `GBPJPY|tokyo|bullish|D1`
2. Cleared non-primary strong leads:
   - `USDJPY|london|bearish|D1`
   - `USDJPY|tokyo|bearish|H4+H1_consensus`
   - `XAGUSD|london|bullish|D1`
3. Negative controls from registered matrix, for sanity checks:
   - choose representative negative/flat cohorts from `HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md`

Do not include the dominance-watchlist names in the first raw-OHLC adapter target set unless the CEO explicitly asks to run them as blocked controls.

## Ready-To-Paste Starter Message

Use this exact starter prompt for the fresh session:

```text
Phase 3 continuation from Session 52.

Pre-flight first, per AGENTS.md:
1. Run `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`
3. Read latest handoff:
   `.context/02_session_handoffs/SESSION_52_PHASE_3_REPLAY_LAB_MATRIX_FOLLOWUP_HANDOFF.md`
4. Read `.context/00_core/quick_reference_card.md`
5. Read:
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_PROTOCOL_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json`
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_REGISTERED_MATRIX_RAW_REPLAY_REPORT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/PRE_REGISTERED_TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_2026-05-01.md`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_V1.json`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`
   - `scripts/run_truth_layer_prequential_replay.py`
   - `scripts/run_truth_layer_registered_matrix_replay.py`
   - `scripts/analyze_truth_layer_matrix_followup_dominance.py`
   - `research/ml_program/MASTER_BACKLOG.md`

Context:
Phase 3 has built the external-feed substrate, rescued M1/M5 lower-timeframe history, built the historical opportunity truth layer, pre-registered the two primary controlled truth-layer cohorts, built a no-leak prequential historical replay lab, replayed the full 44-candidate registered matrix, and froze follow-up lanes.

Important results from Session 52:
- Replay lab guardrails passed on 205,197 truth-layer rows: 0 duplicate keys, 0 invalid clocks, 0 forbidden future-field exposure, 0 external as-of violations, 0 AI calls.
- Full registered matrix replay: 44 candidates, 18,541 resolved rows, mean R +0.128559, WR 45.4237%, `NO_PROMOTION_VERDICT`.
- Primary controlled family remains:
  - `USDJPY|tokyo|bearish|D1`
  - `GBPJPY|tokyo|bullish|D1`
- Cleared non-primary raw-replay priority targets:
  - `USDJPY|london|bearish|D1`
  - `USDJPY|tokyo|bearish|H4+H1_consensus`
  - `XAGUSD|london|bullish|D1`
- Dominance-watchlist names are blocked from the first raw-OHLC target set unless explicitly run as blocked controls:
  - `NAS100|ny|bullish|D1`
  - `US30_cash|ny|bullish|H4+H1_consensus`
  - `XAUUSD|ny|bullish|D1`

Objective:
Build the raw-OHLC prequential replay adapter for Phase 3 research. This is the larger engineering move: walk historical candles forward one at a time and reconstruct/test decisions from the candle stream instead of only using prebuilt truth-layer opportunity rows.

Goal:
Make historical testing as close as possible to a rapid live session while preserving no-leak discipline, DSR/PBO/effective_N/trial-budget language, and the `NO_PROMOTION_VERDICT` boundary. Do not stop at a loose script. Produce a clean, reusable research-lab component with protocol/report artifacts and tests.

Quality mandate:
Go full in. Read the relevant docs carefully before coding. If context is missing, find it in the repo before assuming. Pursue every ambiguity until it is either resolved, encoded as an explicit rule, or documented as a blocker. Do not fabricate numbers. Do not overclaim. Do not call same-dataset historical results promotion proof. But also do not be timid: if a constraint can be engineered around, engineer around it. If a blocker cannot be solved safely, state it clearly and leave an artifact explaining why.

Required engineering questions to resolve:
- What raw OHLC data files are available for each target symbol/timeframe?
- What is the canonical candle schema and timestamp/as-of policy?
- How will M15 replay expose rolling history without revealing future candles?
- How will H1/H4/D1 features be computed or aligned as of each M15 close?
- How will target cohort filters be represented without leaking `truth_*` fields?
- What event log is needed to audit each replay decision?
- Which negative-control cohorts should be included for sanity checks?
- What is the minimum first version that is correct, tested, and extensible?

Constraints:
- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No pushing without approval.
- Do not stage or commit live-monitoring/runtime dirt.
- Keep promotion language blocked unless a separate future/prospective promotion dossier is built.

Recommended first implementation path:
1. Inventory available raw historical OHLC data and document coverage/gaps.
2. Create a raw replay protocol/spec artifact under `research/phase_3_external_feed_validation/`.
3. Implement a reusable raw-OHLC replay scaffold, likely a new script under `scripts/`, that:
   - loads OHLC data without future leakage,
   - exposes a replay clock,
   - yields as-of rolling candle windows,
   - records event logs and data coverage diagnostics,
   - supports the five approved target cohorts plus negative controls,
   - emits `NO_PROMOTION_VERDICT`.
4. Add focused tests for clock ordering, no future candle exposure, HTF as-of alignment, target selection, and report semantics.
5. Run a first research-only report if the data supports it.
6. Commit scoped research/tooling artifacts only.

Do not restart Phase 3 from scratch. Continue from Session 52 and preserve the reasoning behind the existing replay lab: the truth-layer replay solved future-field leakage for prebuilt opportunities; the raw-OHLC adapter is the next layer that tests from historical candle streams.
```

## Next Session Constraints

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No pushing without approval.
- Do not stage or commit live-monitoring/runtime dirt.
- Keep `NO_PROMOTION_VERDICT` language unless a separate future/prospective promotion dossier is built.

## Pre-Flight For Next Session

Run normal AGENTS.md pre-flight:

1. `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`
3. Read this handoff.
4. Read `.context/00_core/quick_reference_card.md`
5. Read:
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_PROTOCOL_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json`
   - `research/phase_3_external_feed_validation/HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/PRE_REGISTERED_TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_2026-05-01.md`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01.md`
   - `scripts/run_truth_layer_prequential_replay.py`
   - `scripts/run_truth_layer_registered_matrix_replay.py`
   - `scripts/analyze_truth_layer_matrix_followup_dominance.py`

## Known Worktree Dirt To Avoid

At the time of this handoff, unrelated/runtime dirt existed and must not be staged with research commits:

- `.context/LIVE_STATE.md`
- `pipeline_state/m5_refinement.json`
- `scripts/watchdog.ps1`
- `src/components/tick_capture.py`
- `shadow_logs/*`
