# Session 51 Handoff - Phase 3 Cohort Stability And Next Controlled Research

**Date:** 2026-05-01  
**Repo:** `C:\Users\MSI\Documents\ai-trading-agent`  
**Starting HEAD:** `6a3e852 research(phase3): add truth-layer cohort stability follow-up`  
**Purpose:** Preserve the Phase 3 context synthesis, truth-layer cohort diagnostics/stability results, ML master-backlog reconciliation, open questions, and the next-session starter prompt.

## 1. Mandatory Fresh-Session Preflight

Run this first. Do not rely on this handoff if `LIVE_STATE.md` or git disagrees.

```powershell
python scripts\generate_live_state.py
Get-Content .context\LIVE_STATE.md
Get-Content .context\02_session_handoffs\SESSION_51_PHASE_3_COHORT_STABILITY_AND_NEXT_CONTROLLED_RESEARCH_HANDOFF.md
Get-Content .context\00_core\quick_reference_card.md
git log --oneline -24
git status --short --untracked-files=all
```

Then read the Phase 3 core evidence:

```powershell
Get-Content .context\04_agents\PHASE_3_FREE_FEED_SPRINT_PLAN.md
Get-Content .context\04_agents\PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md
Get-Content research\phase_3_external_feed_validation\VALIDATION_PROTOCOL_V1.md
Get-Content research\phase_3_external_feed_validation\NEXT_ACTIONS_AND_DATA_AUDIT_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_COHORT_DIAGNOSTICS_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\TRUTH_LAYER_FOLLOWUP_COHORTS_V1.json
Get-Content research\phase_3_external_feed_validation\TRUTH_LAYER_COHORT_STABILITY_2026-05-01.md
Get-Content research\ml_program\MASTER_BACKLOG.md
Get-Content scripts\analyze_truth_layer_cohort_stability.py
```

Known runtime/live-monitoring dirt at handoff creation:

- `.context/LIVE_STATE.md` regenerated
- `pipeline_state/m5_refinement.json`
- `src/components/tick_capture.py` shows modified in status but no intended content change from this research session
- untracked `shadow_logs/*` runtime files

Do not stage or commit those unless the CEO explicitly asks. A parallel live-monitoring session may keep mutating runtime files.

## 2. What Phase 3 Is And Is Not

Phase 3 so far is **measurement infrastructure, data-quality rescue, historical opportunity truth labeling, and cohort triage**.

It is **not** yet:

- edge validation
- parameter optimization
- live trading logic improvement
- J46-J49/S79/risk-policy replay
- AI-prompt or Component 3A behavior validation
- promotion-grade external-feed alpha proof

Correct framing:

- Phase 3 has made the research clearer by proving what can and cannot be measured.
- It narrowed promising mechanical truth-layer cohorts.
- It did not prove a deployable new edge.
- It should now move from diagnostic mining to pre-declared controlled research.

## 3. Commit Stack To Inspect

Most relevant recent commits:

```text
6a3e852 research(phase3): add truth-layer cohort stability follow-up
71273ed research(phase3): add truth-layer cohort diagnostics
4803c96 docs(phase3): add lower-timeframe rescue handoff
f8960f9 docs(phase3): record post-maxbars tick constraint
3457087 research(phase3): complete lower-timeframe data rescue
3e76430 research(phase3): audit lower-timeframe data rescue path
e95b7b9 research(phase3): add historical truth layer v2 taxonomy
76f2de4 research(phase3): analyze historical opportunity substrate
88640b4 feat(phase3): build historical pre-ai opportunity dataset
```

## 4. Phase 3 Questions Answered So Far

### External-feed alpha validation

Answered: **not yet possible.**

Candidate-level joins exist, but actual realized-R remains too sparse and DSR/PBO/effective_N are not computed. External-feed tables are shadow-only exploratory screens until the validation protocol clears.

Evidence:

- `research/phase_3_external_feed_validation/VALIDATION_PROTOCOL_V1.md`
- `research/phase_3_external_feed_validation/NEXT_ACTIONS_AND_DATA_AUDIT_2026-05-01.md`
- `research/phase_3_external_feed_validation/CANDIDATE_DIAGNOSTIC_2022_2026_PLUS_GAP_2026-05-01.md`

### Lower-timeframe data blocker

Answered: **M1/M5 bar-data blocker was fixable terminal state.**

MT5 `maxbars=100000` capped historical M1/M5. After setting MT5 Charts max bars to Unlimited, M1/M5 coverage became usable for the historical truth layer.

Evidence:

- `research/phase_3_external_feed_validation/LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md`

### Tick-history blocker

Answered: **not fixed by max-bars.**

Historical tick data is available for recent windows but not broad 2022-2026 history. It is not blocking M1/M5 truth-layer diagnostics, but it remains unresolved for tick-level same-bar sequencing.

### Truth-layer substrate

Answered: **usable for M1/M5 mechanical truth anatomy.**

Rescued truth-layer run:

- rows: `205,197`
- unique keys: `205,197`
- AI attempted rows: `0`
- AI call count sum: `0`

Main truth outcomes:

- `NO_ENTRY`: `44,098`
- `SL`: `14,024`
- `TP`: `11,124`
- `SAME_BAR`: `1,907`
- `LOWER_TF_GAPPY`: `1,135`

Evidence:

- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md`

### NO_ENTRY anatomy

Answered: **not mostly near-miss.**

Global NO_ENTRY path coverage was complete, and only `5.44%` came within `0.25R` of entry. This argues against broad entry-offset tuning from the full population.

Evidence:

- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_COHORT_DIAGNOSTICS_2026-05-01.md`

### M1/M5 label disagreement

Answered: **small but concentrated in ambiguity.**

M1/M5 comparable rows: `73,387`  
Disagreement rows: `2,650` (`3.61%`)  
Disagreements concentrate around same-bar and gappy rows.

### Cohorts worth controlled follow-up

Answered: **two primary mechanical follow-up cohorts and four watchlist cohorts.**

Primary controlled-research candidates from stability pass:

1. `USDJPY|tokyo|bearish|D1`
   - CLEAN_HIGH n=`212`
   - mean R=`+0.630181`
   - WR=`65.566%`
   - valid years=`3`
   - positive years=`3`

2. `GBPJPY|tokyo|bullish|D1`
   - CLEAN_HIGH n=`430`
   - mean R=`+0.493024`
   - WR=`60.9302%`
   - valid years=`4`
   - positive years=`4`

Watchlist/split-required cohorts:

- `XAUUSD|ny|bullish|D1`
- `US30_cash|ny|bullish|H4+H1_consensus`
- `NAS100|ny|bullish|D1`
- `XAGUSD|ny|bullish|H4+H1_consensus`

Evidence:

- `research/phase_3_external_feed_validation/TRUTH_LAYER_COHORT_STABILITY_2026-05-01.md`

### Gap ambiguity inside strong cohorts

Answered: **selected-source gaps are after mechanical resolution in these cohorts.**

Initial zero-gap sensitivity looked alarming. The corrected selected-source gap accounting shows the gap counts are after resolution, so they do not invalidate the labels. Strict `ZERO_GAP_*` remains a sensitivity view, not the main validity boundary. `RESOLUTION_SAFE_*` is the right boundary for this diagnostic layer.

## 5. MASTER_BACKLOG Reconciliation

Important: the Phase 3 question map was originally produced without `research/ml_program/MASTER_BACKLOG.md` in active context. After reading it, the backlog **does not overturn** Phase 3 findings. It adds a larger research roadmap and reinforces the methodology gates.

Key backlog implications:

- `M-12` and `M-13` matter next: effective-N tracker and PBO baked into primary-hypothesis evaluation.
- `A-5`, `A-14`, `K-7`, and `E-1` become more relevant because the best Phase 3 cohorts are JPY-session cohorts.
- `A-1` through `A-4` and `U-2` remain relevant for NAS100/US30 watchlist cohorts.
- `A-8` through `A-11` remain relevant for XAUUSD/XAGUSD watchlist cohorts.
- `D-11` becomes important: backfill data-quality bias check, mechanical extraction vs live.
- The backlog itself has stale-status tension: some individual K54 v3 items are still `PENDING` while composite `B-1` says K54 v3 master bundle failed. Verify statuses before dispatching any backlog item.

Backlog anchors:

- `M-1` / `M-3`: J46-J49 and S79 survived DSR.
- `M-4` / `U-5`: many old headline WR/expectancy claims failed DSR; mechanical OB mechanism survives separately.
- `K-4` / `P-4` / `U-3`: Stoikov micro-price failed on MT5 retail substrate.
- `Q-1`: DLinear failed; sequence-model track deferred.
- `B-1`: K54 v3 master bundle failed, but NAS/US30 specialist survived as K55-shadow candidate.

## 6. Questions Still Open For Phase 3

Highest priority:

1. Can `USDJPY|tokyo|bearish|D1` and `GBPJPY|tokyo|bullish|D1` survive a **pre-declared controlled evaluation** with DSR/PBO/effective_N accounting?
2. What exact hypothesis file and trial-budget entry should represent those cohorts before any further evaluation?
3. What evaluator should implement the Phase 3 controlled hypothesis test without turning into parameter optimization?
4. Can the effective-N/PBO infrastructure reuse existing K54 methodology code, or should Phase 3 get a minimal research-only evaluator first?

Data-quality:

5. Are 2022-2023 backfilled mechanical opportunity labels comparable to live trade records (`D-11`)?
6. Does historical tick absence materially affect same-bar cases, or can same-bar rows remain excluded/sensitivity-only?
7. Do NAS100/US30 need an alternate intraday source before controlled research because redacted_account starts index M1/M5 at `2022-10-20`?

External feeds:

8. Can JPY carry/funding/macro features be joined as-of for the primary JPY cohorts?
9. Can CFTC/WGC/LBMA/FRED/FlashAlpha forward accumulation produce enough candidate-level coverage for watchlist cohorts?
10. Is gamma-sign constructible from free/proxy data for NAS100/US30, or is a paid source required later?

Live-vs-mechanical:

11. How do these mechanical cohorts behave after layering back actual live architecture: Component 3A AI, L2 gates, J46-J49, S79/risk policy, execution slippage, and live constraints?
12. Can actual realized-R enrichment be recovered from live session summaries, trade index, execution/exit records, or broker history?

Research-program hygiene:

13. Which `MASTER_BACKLOG.md` items are stale after Phase 3 and the K54 v3 failure?
14. Should Phase 3 create a polished `HYPOTHESIS_BACKLOG.md` entry for the two JPY cohorts plus the watchlist cohorts?
15. How should trial budget be counted for post-diagnostic cohorts selected from the same truth layer?

## 7. Recommended Next Session Objective

Do **not** do more free-form mining first.

Recommended next unit:

1. Create a pre-registration artifact for controlled truth-layer cohort hypotheses, likely:
   - `research/phase_3_external_feed_validation/PRE_REGISTERED_TRUTH_LAYER_COHORT_HYPOTHESES_2026-05-01.md`
   - or a JSON + markdown pair if the evaluator should consume it.

2. Define exactly two primary hypotheses:
   - `USDJPY|tokyo|bearish|D1`
   - `GBPJPY|tokyo|bullish|D1`

3. Define watchlist-only cohorts:
   - `XAUUSD|ny|bullish|D1`
   - `US30_cash|ny|bullish|H4+H1_consensus`
   - `NAS100|ny|bullish|D1`
   - `XAGUSD|ny|bullish|H4+H1_consensus`

4. Implement a minimal controlled-evaluation script, only if it can be done without pretending to solve DSR/PBO fully. If full DSR/PBO is too large, produce a protocol and evaluator skeleton instead:
   - `scripts/evaluate_truth_layer_controlled_hypotheses.py`
   - `tests/test_truth_layer_controlled_hypotheses.py`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_CONTROLLED_HYPOTHESIS_PROTOCOL_2026-05-01.md`

5. Explicitly label same-dataset limitations:
   - These cohorts were selected after diagnostics.
   - Same truth-layer evaluation is exploratory/stability only unless the hypothesis is tested on future/holdout data or under a declared validation split not used for selection.
   - No parameter sweeps.
   - No prompt/src live-logic changes.
   - No paid AI/API calls.

## 8. Suggested Controlled-Hypothesis Design

Candidate schema:

```text
hypothesis_id
cohort_key
selection_source
primary_or_watchlist
allowed_population
forbidden_exclusions
primary_target
secondary_targets
split_plan
fold_min_n
methodology_gates
invalidation_rules
trial_budget_note
```

Suggested split plan:

- Use year folds where available.
- Treat 2022-2023 vs 2024-2026 partial as an early/recent diagnostic split.
- Do not optimize thresholds, entry offsets, stop buffers, session windows, or regime definitions from this artifact.
- Report pooled values only as secondary context.

Suggested primary target:

- `truth_realized_r` on `CLEAN_HIGH` or `RESOLUTION_SAFE_HIGH` rows.

Suggested secondary targets:

- no-entry rate
- SL/immediate-stop burden
- high+medium sensitivity
- zero-gap sensitivity
- early/recent split

Explicitly not included:

- J46-J49 portfolio policy
- S79/risk policy
- AI prompt behavior
- live L2/execution
- account pass probability

## 9. Verification From This Session

Latest focused verification before this handoff:

```powershell
python -m pytest tests\test_historical_opportunity_truth_layer.py tests\test_historical_opportunity_truth_layer_diagnostics.py tests\test_truth_layer_cohort_stability.py -q -p no:cacheprovider
```

Result:

```text
14 passed
```

Note: pytest emitted a live-process snapshot warning because a separate live process updated `pipeline_state/heartbeat_US30_cash.json`. That is expected in the CEO's parallel live-monitoring setup; it was not staged.

## 10. Fresh-Session Starter Prompt

Use this prompt in the next Codex session:

```text
Phase 3 continuation from Session 51.

Pre-flight first, per AGENTS.md:
1. Run `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`
3. Read latest handoff:
   `.context/02_session_handoffs/SESSION_51_PHASE_3_COHORT_STABILITY_AND_NEXT_CONTROLLED_RESEARCH_HANDOFF.md`
4. Read `.context/00_core/quick_reference_card.md`
5. Read:
   - `.context/04_agents/PHASE_3_FREE_FEED_SPRINT_PLAN.md`
   - `.context/04_agents/PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md`
   - `research/phase_3_external_feed_validation/VALIDATION_PROTOCOL_V1.md`
   - `research/phase_3_external_feed_validation/NEXT_ACTIONS_AND_DATA_AUDIT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md`
   - `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_COHORT_DIAGNOSTICS_2026-05-01.md`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_COHORT_STABILITY_2026-05-01.md`
   - `research/phase_3_external_feed_validation/TRUTH_LAYER_FOLLOWUP_COHORTS_V1.json`
   - `research/ml_program/MASTER_BACKLOG.md`
   - `scripts/analyze_truth_layer_cohort_stability.py`

Context:
Phase 3 has built the external-feed substrate, rescued M1/M5 lower-timeframe history, built the historical opportunity truth layer, and identified two primary mechanical truth-layer cohorts for controlled follow-up:
- `USDJPY|tokyo|bearish|D1`
- `GBPJPY|tokyo|bullish|D1`

This is not edge validation yet and not live trading improvement. It is measurement infrastructure and controlled-research setup. The next step is to stop free-form mining and pre-register controlled hypotheses before any further evaluation.

Objective:
Prepare the controlled Phase 3 truth-layer hypothesis protocol and, if safe, a research-only evaluator skeleton/report for the two primary cohorts.

Goal:
Preserve DSR/PBO/effective_N discipline, define trial-budget handling, define allowed populations and invalidation rules, and make it impossible to accidentally treat same-dataset post-diagnostic selection as promotion-grade proof.

Constraints:
- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No pushing without approval.
- Do not stage or commit live-monitoring/runtime dirt.

Recommended first task:
Create a pre-registration/protocol artifact, likely:
- `research/phase_3_external_feed_validation/PRE_REGISTERED_TRUTH_LAYER_COHORT_HYPOTHESES_2026-05-01.md`
- optionally a machine-readable JSON hypothesis file if useful
- optionally `scripts/evaluate_truth_layer_controlled_hypotheses.py` and tests only after the protocol boundary is clear

Be strict about language: this can authorize controlled research, not alpha promotion.
```
