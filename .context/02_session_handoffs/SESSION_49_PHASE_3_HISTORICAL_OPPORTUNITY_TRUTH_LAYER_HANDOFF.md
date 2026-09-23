# Session 49 Handoff - Phase 3 Historical Opportunity Truth Layer

**Date:** 2026-05-01
**Repo:** `C:\Users\MSI\Documents\ai-trading-agent`
**Research base HEAD before this handoff:** `76f2de4 research(phase3): analyze historical opportunity substrate`
**Prior Phase 3 handoff:** `.context/02_session_handoffs/SESSION_48_PHASE_3_EXTERNAL_FEED_VALIDATION_HANDOFF.md`
**Purpose:** Preserve the full context from the Phase 3 historical opportunity continuation and prepare the next fresh session for lower-timeframe truth and failure-taxonomy work.

## 1. CEO Direction Preserved

The CEO explicitly wants quality, curiosity, and detail over speed. The research goal is not just to produce a dataset. The goal is to make the trading system much stronger at:

- detecting real setups,
- rejecting likely failing setups,
- understanding how and why price moved,
- linking lower-timeframe and higher-timeframe behavior,
- using compute/research/AI carefully without p-hacking,
- asking the right questions and pursuing ambiguity until it is materially reduced.

Important working constraints from the CEO and project rules:

- Research/tooling only unless explicitly approved.
- No live trading logic changes.
- No prompt edits.
- Do not edit `src/components/orchestrator.py`, `prompts/`, or `agent_config.yaml` unless explicitly approved.
- No paid AI/API replay.
- No pushing without approval.
- Commit completed artifacts with:

```text
```

## 2. Mandatory Fresh-Session Preflight

Run the normal project preflight first:

```powershell
python scripts/generate_live_state.py
Get-Content .context\LIVE_STATE.md
Get-Content .context\02_session_handoffs\SESSION_49_PHASE_3_HISTORICAL_OPPORTUNITY_TRUTH_LAYER_HANDOFF.md
Get-Content .context\00_core\quick_reference_card.md
Get-Content .context\04_agents\PHASE_3_FREE_FEED_SPRINT_PLAN.md
Get-Content .context\04_agents\PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md
git log --oneline -12
git status --short
```

Then read the core artifacts from this continuation:

```powershell
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_AUDIT_CLOSED_ONLY_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md
Get-Content scripts\build_historical_opportunity_dataset.py
Get-Content scripts\analyze_historical_opportunity_dataset.py
Get-Content tests\test_historical_opportunity_dataset.py
Get-Content tests\test_historical_opportunity_analysis.py
```

Known runtime dirt after this session, intentionally not committed:

- `.context/LIVE_STATE.md`
- `pipeline_state/m5_refinement.json`
- several `shadow_logs/*` runtime files

Do not commit those unless the CEO explicitly asks.

## 3. Commit Stack To Inspect

The two commits from this continuation are the main continuity points:

```text
76f2de4 research(phase3): analyze historical opportunity substrate
88640b4 feat(phase3): build historical pre-ai opportunity dataset
```

Also inspect the external-feed groundwork stack from Session 48 if needed:

```text
ee7f986 docs(phase3): add external feed validation handoff
6c14165 feat(phase3): add M5 candidate simulation audit
1f132eb fix(phase3): extract realized R from trade exits
d72b58d feat(phase3): expand substrate and canonicalize shadow candle time
95bbdab feat(phase3): add candidate diagnostics and mt5 data audit
57b6729 feat(phase3): join candidates to external validation snapshots
f7c7153 feat(phase3): build no-lookahead validation dataset
30bc1c4 feat(phase3): build historical external snapshots
```

## 4. What Was Built In This Continuation

### Commit `88640b4`

Added the historical pre-AI opportunity builder:

- `scripts/build_historical_opportunity_dataset.py`
- `tests/test_historical_opportunity_dataset.py`
- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md`

The builder enumerates historical deterministic pre-AI opportunities across available 2022-2026 MT5 data, joins rows no-lookahead to external-feed snapshots, and writes audit counts by symbol/year/kill zone/gate status.

Main ignored dataset output:

```text
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z.jsonl
```

Summary JSON:

```text
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_summary.json
```

### Commit `76f2de4`

Added the historical opportunity analysis/refinement layer:

- `scripts/analyze_historical_opportunity_dataset.py`
- `tests/test_historical_opportunity_analysis.py`
- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md`
- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_AUDIT_CLOSED_ONLY_2026-05-01.md`

The analysis script consumes the historical opportunity JSONL, produces synthesis tables, optionally refines mechanical outcomes on lower timeframes, and writes exploratory external-feature separation tables. It does not call paid AI clients.

Latest ignored analysis outputs:

```text
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/analysis/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_synthesis_20260501T044959Z.json
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/analysis/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_m5_refinements_20260501T044959Z.jsonl
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/analysis/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_m1_refinements_20260501T044959Z.jsonl
```

Closed-only HTF sensitivity output:

```text
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/phase3_historical_pre_ai_opportunities_closed_only_no_mech_v1_20260501T035754Z.jsonl
data/external/validation/calendar_macro_bundle_v1/historical_opportunities/phase3_historical_pre_ai_opportunities_closed_only_no_mech_v1_20260501T035754Z_summary.json
```

## 5. Required Tests Covered

The required tests from the CEO's objective were implemented.

Covered by `tests/test_historical_opportunity_dataset.py`:

- no-lookahead snapshot matching uses `as_of_utc`, not observation date,
- missing external snapshot produces explicit missing/null flags instead of dropped rows,
- builder import does not load paid AI clients,
- rows are stable and keyed by symbol/candle,
- generated opportunity rows have `ai_call_attempted=False`, `ai_call_count=0`, and `paid_ai_replay=False`.

Covered by `tests/test_historical_opportunity_analysis.py`:

- lower-timeframe refinement rejects nonlocal M1/M5 rows instead of accidentally matching 2026 bars to 2022 opportunities,
- lower-timeframe refinement scales the hold window by wall-clock time rather than using the same bar count across M15/M5/M1.

Final verification:

```powershell
python -m pytest tests/test_historical_opportunity_analysis.py tests/test_historical_opportunity_dataset.py -q -p no:cacheprovider
```

Result:

```text
7 passed
```

Compile check:

```powershell
python -m py_compile scripts/analyze_historical_opportunity_dataset.py scripts/build_historical_opportunity_dataset.py tests/test_historical_opportunity_analysis.py tests/test_historical_opportunity_dataset.py
```

Result: passed.

## 6. Key Results

From `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md`:

```text
Rows scanned: 205,197
WOULD_SEND_AI: 135,062 (65.82%)
Unique keys: 205,197
Duplicate keys: 0
AI-attempted rows: 0
AI call count sum: 0
```

This solves the critical Session 48 confusion:

- The previous `76/77` count was only the recent live/shadow candidate log joined to the new substrate.
- It was not the full 2022-2026 historical opportunity count.
- The historical deterministic pre-AI opportunity substrate is now large: `205,197` rows.

## 7. HTF Sensitivity Finding

A closed-only HTF replay run was produced to test whether partial higher-timeframe replay policy materially inflated the pass population.

Base `partial_htf`:

```text
Rows: 205,197
WOULD_SEND_AI: 135,062
WOULD_SEND_AI rate: 65.82%
```

Closed-only:

```text
Rows: 205,197
WOULD_SEND_AI: 133,853
WOULD_SEND_AI rate: 65.23%
```

Interpretation:

- Closed-only HTF context changes `WOULD_SEND_AI` by `-1,209` rows, or about `-0.59pp`.
- Therefore the broad pre-AI opportunity count is not primarily an HTF replay artifact.
- Row-level studies should still pin one HTF policy because individual opportunities can flip near boundaries.

## 8. Mechanical Outcome Findings

M15 mechanical OB-retest diagnostics:

```text
Resolved R rows: 21,166
Mean realized R: +0.1727R
Same-bar rows: 8,686
No-entry rows: 44,098
```

M5 lower-timeframe refinement:

```text
Attempted setup-ok rows: 73,950
Local coverage: 26,015 (35.18%)
Resolved R rows: 8,588
Mean realized R: +0.1224R
```

M1 lower-timeframe refinement:

```text
Attempted setup-ok rows: 73,950
Local coverage: 5,258 (7.11%)
Resolved R rows: 2,057
Mean realized R: +0.1202R
```

Interpretation:

- Mechanical diagnostics are positive but not promotion-grade.
- The sign is encouraging because M15, M5, and M1 resolved subsets are all positive.
- However, M1/M5 local coverage is not deep enough for confident parameter sweeps.
- Same-bar and no-entry rows remain major label-quality ambiguities.

## 9. External Feed Coverage Findings

On all opportunity rows:

```text
FRED: 205,167 / 205,197 available
CFTC: 28,800 available
LBMA: 9,217 available
FlashAlpha: 0 available
WGC: 0 available
```

On `WOULD_SEND_AI` rows:

```text
FRED: 135,062 / 135,062 available
CFTC: 18,416 available (13.64%)
LBMA: 6,326 available (4.68%)
FlashAlpha: 0 available
WGC: 0 available
```

Interpretation:

- FRED can be used immediately for macro/regime screens.
- CFTC can be used cautiously, with sparse coverage and weekly publication semantics.
- LBMA calendar features are sparse in the current cached/joined substrate.
- FlashAlpha and WGC cannot explain historical opportunity outcomes in this artifact because effective historical coverage is absent.
- Multi-feed confluence is not testable yet from the current historical substrate.

## 10. Questions Raised And Current Status

### Solved

1. **Was 76/77 the full historical candidate count?**
   Solved. No. It was only recent live/shadow candidate history. The historical pre-AI substrate is now `205,197` rows.

2. **Can we enumerate current deterministic pre-AI opportunities without paid AI?**
   Solved. Yes. The builder produces deterministic rows with `0` AI calls.

3. **Can we join opportunities to external snapshots without lookahead?**
   Solved. Snapshot matching uses `as_of_utc`; tests cover observation-date traps.

4. **Do missing external snapshots drop opportunity rows?**
   Solved. Missing feeds produce explicit missing flags and null fields.

5. **Are rows stable and keyable by symbol/candle?**
   Solved. `205,197` unique keys and `0` duplicates in the committed synthesis.

6. **Is the broad pass count mostly an HTF replay artifact?**
   Mostly solved. Closed-only changes the pass population by only `-0.59pp`.

### Semi-Solved

1. **Is the mechanical setup family still positive?**
   Semi-solved. The resolved subsets are positive across M15/M5/M1, but label ambiguity and coverage gaps prevent promotion claims.

2. **Do specific symbols/sessions/years look stronger?**
   Semi-solved. Tokyo, 2026, XAGUSD, USDJPY, and GBPJPY show promising pockets, but composition effects are not controlled yet.

3. **Can external feeds explain opportunity quality?**
   Semi-solved. FRED can be screened now; CFTC/LBMA can be screened with caution; FlashAlpha/WGC need more historical coverage or forward-shadow handling.

4. **Can M5/M1 resolve the same-bar/no-entry ambiguity?**
   Semi-solved. The analysis path works and correctly rejects nonlocal data, but current M5/M1 coverage is too shallow.

### Deferred

1. **Pip-offset, buffer, percentage, entry-level optimization**
   Deferred until lower-timeframe truth coverage is better and same-bar/no-entry handling is pinned.

2. **Paid AI replay**
   Deferred until narrow high-value cohorts are selected and the CEO approves budget.

3. **External multi-feed confluence claims**
   Deferred because FlashAlpha/WGC historical coverage is effectively absent in this substrate.

4. **Live trading logic changes**
   Deferred. No evidence from this session justifies a live decision change.

5. **ML selector training**
   Deferred until labels are cleaner. Bad labels would make a confident but unreliable model.

### Rejected For Now

1. **Treating `WOULD_SEND_AI` as a trade signal**
   Rejected. It only means deterministic pre-AI gates pass.

2. **Optimizing parameters from M15-only outcomes**
   Rejected. Same-bar and fill ambiguity are too large.

3. **Claiming Tokyo/2026 strength as alpha**
   Rejected. It is a hypothesis, not a conclusion.

4. **Using current FlashAlpha/WGC rows for historical validation**
   Rejected. Coverage is effectively zero in this joined historical artifact.

## 11. Recommended Next Path

The next phase should be **Historical Opportunity Dataset v2: lower-timeframe truth and failure taxonomy**.

Priority order:

1. **Truth Layer v2**
   - Improve M1/M5 history depth if possible.
   - Classify each opportunity with clean lower-timeframe truth:
     - entry filled,
     - entry missed,
     - TP first,
     - SL first,
     - same-bar ambiguous,
     - timeout,
     - incomplete horizon,
     - no local lower-timeframe data.

2. **Failure Anatomy**
   - Add explicit failure/success buckets:
     - no fill,
     - same-bar unresolved,
     - liquidity swept then reversed,
     - late-session decay,
     - HTF conflict,
     - weak displacement,
     - range compression,
     - excessive distance to POI,
     - adverse volatility expansion,
     - missing/low-quality POI,
     - external/macro stress context.

3. **Cohort Map**
   - Split by symbol, session, year, side, framework, deterministic bias, regime, POI type, volatility, distance, and external-feed state.
   - Identify where the edge concentrates and where it dies.

4. **DSR-Controlled Feature Screens**
   - Start with FRED because coverage is complete.
   - Treat CFTC/LBMA as sparse screens.
   - Do not claim alpha without trial accounting and out-of-sample/CPCV discipline.

5. **Parameter Sweeps Only After Measurement Is Pinned**
   - Then test entry offsets, SL buffers, RR targets, time stops, and session filters.
   - Every sweep must count as trials under the program methodology.

6. **AI Replay Only On Narrow Cohorts**
   - Use paid AI only after mechanical/failure maps identify high-value cells where AI replay can answer a specific question.

## 12. Suggested V2 Deliverable

Create or extend a research-only tool, likely one of:

```text
scripts/analyze_historical_opportunity_dataset.py
scripts/build_historical_opportunity_truth_layer.py
scripts/build_historical_failure_taxonomy.py
```

Target report:

```text
research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_2026-05-XX.md
```

Minimum useful output fields:

- `opportunity_key`
- `symbol`
- `broker_symbol`
- `timeframe`
- `candle_close_utc`
- `session`
- `deterministic_bias`
- `pre_ai_gate_status`
- `pre_ai_gate_reason`
- `would_send_ai`
- `mechanical_setup_status`
- `mechanical_side`
- `mechanical_framework`
- `mechanical_entry`
- `mechanical_sl`
- `mechanical_tp`
- `mechanical_rr`
- `m15_outcome`
- `m15_realized_r`
- `lower_tf_timeframe`
- `lower_tf_local_coverage`
- `lower_tf_future_rows_available`
- `truth_outcome`
- `truth_realized_r`
- `truth_fill_status`
- `truth_exit_status`
- `truth_failure_bucket`
- `truth_ambiguity_bucket`
- `truth_confidence`
- `external_snapshot_match_status`
- `external_snapshot_as_of_utc`
- feature availability flags

Suggested tests:

- lower-timeframe data must be contiguous after the evaluated candle,
- old/future lower-timeframe files must not be matched to unrelated historical candles,
- same-bar M15 ambiguity is explicitly preserved or resolved by lower timeframe,
- incomplete future horizon is flagged, not treated as no-entry or timeout,
- no paid AI modules are imported or called,
- output rows remain stable and keyed by `symbol|candle_close_utc`.

## 13. Starter Message For Next Session

Use this exact starter message for the next fresh session:

```text
Phase 3 continuation from Session 49.

Pre-flight first, per AGENTS.md:
1. Run `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`
3. Read latest handoff:
   `.context/02_session_handoffs/SESSION_49_PHASE_3_HISTORICAL_OPPORTUNITY_TRUTH_LAYER_HANDOFF.md`
4. Read `.context/00_core/quick_reference_card.md`
5. Read:
   - `.context/04_agents/PHASE_3_FREE_FEED_SPRINT_PLAN.md`
   - `.context/04_agents/PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_AUDIT_CLOSED_ONLY_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md`
   - `scripts/build_historical_opportunity_dataset.py`
   - `scripts/analyze_historical_opportunity_dataset.py`
   - `tests/test_historical_opportunity_dataset.py`
   - `tests/test_historical_opportunity_analysis.py`

Objective:
Start Phase 3 Historical Opportunity Dataset v2: lower-timeframe truth and failure taxonomy.

Goal:
Improve label quality before any parameter optimization. Focus on M1/M5 outcome truth, same-bar/no-entry resolution, setup failure taxonomy, and symbol/session/year cohort diagnostics.

Context:
- Commit `88640b4` built the historical pre-AI opportunity dataset.
- Commit `76f2de4` added analysis/refinement synthesis.
- Dataset: 205,197 historical pre-AI rows.
- WOULD_SEND_AI rows: 135,062.
- HTF closed-only sensitivity is small: -1,209 WOULD_SEND_AI rows / -0.59pp.
- M15 mechanical resolved mean: +0.1727R over 21,166 rows.
- M5 refinement: +0.1224R over 8,588 resolved rows, but only 35.18% local coverage.
- M1 refinement: +0.1202R over 2,057 resolved rows, but only 7.11% local coverage.
- Main ambiguity: lower-timeframe truth, same-bar/no-entry resolution, incomplete lower-timeframe history, and failure reasons.

Constraints:
- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- Do not edit `src/components/orchestrator.py`, `prompts/`, or `agent_config.yaml` unless explicitly approved.
- No paid AI/API calls.
- No pushing without approval.
- Commit artifacts with:

Recommended first task:
Design and implement a research-only v2 lower-timeframe truth/failure taxonomy script or extension. It should classify each opportunity into explicit failure/success anatomy buckets and produce an audit report by symbol/session/year/framework/regime. Do not tune pip offsets or buffers until the truth layer is stronger.
```

## 14. Bottom Line

This session converted Phase 3 from "we have external-feed ingestion and a recent candidate join" into "we have a large historical deterministic pre-AI substrate plus a first mechanical/refinement synthesis."

The correct next move is not immediate tuning. The correct next move is to make the label layer stronger: lower-timeframe truth, explicit failure taxonomy, and cohort-conditioned diagnostics. That is the path most likely to turn the current research substrate into a more powerful trading system rather than an overfit artifact factory.
