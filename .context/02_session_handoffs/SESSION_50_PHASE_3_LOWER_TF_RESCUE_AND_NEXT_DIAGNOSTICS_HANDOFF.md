# Session 50 Handoff - Phase 3 Lower-Timeframe Rescue And Next Diagnostics

**Date:** 2026-05-01  
**Repo:** `C:\Users\MSI\Documents\ai-trading-agent`  
**Starting handoff:** `.context/02_session_handoffs/SESSION_49_PHASE_3_HISTORICAL_OPPORTUNITY_TRUTH_LAYER_HANDOFF.md`  
**Purpose:** Preserve the full Phase 3 lower-timeframe rescue, truth-layer v2, tick-constraint decision, and the next recommended research step.

## 1. CEO Direction Preserved

The CEO's core concern this session was not "just run the next report." The CEO wanted to make sure the research program does not advance into parameter optimization while avoidable data constraints remain unresolved. The specific concern was:

- If M1/M5/tick data is missing, determine whether it is a fixable exporter/terminal problem, a broker/source problem, or a real unavoidable constraint.
- If data can be rescued, rescue it before accepting a weaker alternative.
- Preserve the ambiguity-chasing research posture: do not prematurely simplify label uncertainty away.

Standing constraints still apply:

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No paid AI/API calls.
- No pushing without CEO approval.
- Commit completed artifacts locally with:

```text
```

## 2. Mandatory Fresh-Session Preflight

Run the normal project preflight first:

```powershell
python scripts/generate_live_state.py
Get-Content .context\LIVE_STATE.md
Get-Content .context\02_session_handoffs\SESSION_50_PHASE_3_LOWER_TF_RESCUE_AND_NEXT_DIAGNOSTICS_HANDOFF.md
Get-Content .context\00_core\quick_reference_card.md
git log --oneline -16
git status --short
```

Then read these Phase 3 artifacts:

```powershell
Get-Content .context\04_agents\PHASE_3_FREE_FEED_SPRINT_PLAN.md
Get-Content .context\04_agents\PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_AUDIT_CLOSED_ONLY_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_SYNTHESIS_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md
Get-Content scripts\build_historical_opportunity_dataset.py
Get-Content scripts\analyze_historical_opportunity_dataset.py
Get-Content scripts\build_historical_opportunity_truth_layer.py
Get-Content scripts\inspect_mt5_tick_availability.py
```

Known runtime dirt after this session, intentionally not committed:

- `.context/LIVE_STATE.md` after regeneration
- `pipeline_state/m5_refinement.json`
- untracked `shadow_logs/*` runtime files such as daily PnL, slippage, heartbeat throttle, and touch-count logs

Do not commit those unless the CEO explicitly asks.

## 3. Commit Stack From This Session

Inspect these commits in order:

```text
e95b7b9 research(phase3): add historical truth layer v2 taxonomy
3e76430 research(phase3): audit lower-timeframe data rescue path
3457087 research(phase3): complete lower-timeframe data rescue
f8960f9 docs(phase3): record post-maxbars tick constraint
```

Session 49 predecessor context:

```text
f640353 docs(phase3): add historical opportunity truth-layer handoff
76f2de4 research(phase3): analyze historical opportunity substrate
88640b4 feat(phase3): build historical pre-ai opportunity dataset
```

## 4. What Was Built

### Truth Layer v2

Commit `e95b7b9` added a research-only lower-timeframe truth/failure taxonomy:

- `scripts/build_historical_opportunity_truth_layer.py`
- `tests/test_historical_opportunity_truth_layer.py`
- `research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_2026-05-01.md`

Purpose:

- Classify every historical pre-AI opportunity into explicit anatomy buckets.
- Separate setup rejects, no-fill outcomes, TP-first/SL-first outcomes, same-bar ambiguity, incomplete horizon, and lower-timeframe data-quality issues.
- Produce symbol/session/year/framework/regime diagnostics.
- No AI/API calls.

Initial v2 run, before data rescue:

- Rows classified: `205,197`
- AI calls: `0`
- M1 local coverage: `5,258 / 73,950` (`7.11%`)
- M5 local coverage: `26,015 / 73,950` (`35.18%`)

This proved the taxonomy was useful but also exposed that the historical lower-timeframe substrate was too weak for parameter work.

### Lower-Timeframe Rescue Audit

Commit `3e76430` added:

- `scripts/inspect_mt5_tick_availability.py`
- `tests/test_mt5_tick_availability.py`
- `research/phase_3_external_feed_validation/LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md`

The audit found the first blocker:

```text
terminal_info.maxbars = 100000
```

The old MT5 export was capped around 100k M1/M5 rows per symbol/timeframe. Smaller chunks did not fix it. The CEO then set MT5 Charts max bars to Unlimited.

Post-change terminal verification:

```text
terminal_info.maxbars = 100000000
server = redacted_account-Server 2
login = 0
```

### Rescued M1/M5 Export

One-symbol XAUUSD retest after max-bars:

```powershell
python scripts\export_mt5_research_ohlcv.py --start 2022-01-01 --end 2026-05-01 --timeframes M1,M5 --symbol XAUUSD:XAUUSD --chunk-days 1 --label phase3_rescue_xau_m1_m5_chunk1_after_maxbars --yes-live-readonly
```

Result:

| Timeframe | rows | first | last |
| --- | ---: | --- | --- |
| XAUUSD M1 | 1528838 | 2022-01-03 01:00 | 2026-04-30 23:59 |
| XAUUSD M5 | 305941 | 2022-01-03 01:00 | 2026-04-30 23:55 |

All-symbol export:

```powershell
python scripts\export_mt5_research_ohlcv.py --start 2022-01-01 --end 2026-05-01 --timeframes M1,M5 --chunk-days 1 --label phase3_rescue_all_m1_m5_chunk1_after_maxbars --yes-live-readonly
```

Output directory:

```text
data\mt5_research_exports\phase3_rescue_all_m1_m5_chunk1_after_maxbars
```

Key coverage:

| Symbol | M1 first | M1 rows | M5 first | M5 rows |
| --- | --- | ---: | --- | ---: |
| GBPJPY | 2022-01-03 00:00 | 1602547 | 2022-01-03 00:00 | 320888 |
| GBPUSD | 2022-01-03 00:00 | 1601117 | 2022-01-03 00:00 | 321006 |
| USDJPY | 2022-01-03 00:00 | 1601161 | 2022-01-03 00:00 | 321024 |
| XAUUSD | 2022-01-03 01:00 | 1528838 | 2022-01-03 01:00 | 305941 |
| XAGUSD | 2022-01-03 01:00 | 1485307 | 2022-01-03 01:00 | 297511 |
| NAS100 | 2022-10-20 11:00 | 1052457 | 2022-10-20 11:00 | 212964 |
| US30_cash | 2022-10-20 11:00 | 1051102 | 2022-10-20 11:00 | 212948 |

Interpretation:

- The M1/M5 bar-data issue was a fixable terminal max-bars constraint.
- Metals and FX now cover the requested 2022-2026 research window from the first trading session in January 2022.
- NAS100/US30_cash only start at `2022-10-20` on redacted_account; pre-2022-10 index intraday truth remains unavailable from this broker.

### Truth-Layer Performance Fix And Rescued Rerun

The first full rescued truth-layer rerun timed out after 30 minutes because the old truth script passed full multi-year M1/M5 series into the shared mechanical resolver for every setup, and the resolver copies `ohlcv_rows` internally.

Commit `3457087` changed the research-only truth-layer script to slice the legal future lower-timeframe horizon before calling the resolver. Regression test added:

```text
test_lower_timeframe_refinement_slices_horizon_before_resolver
```

Successful rescued rerun:

```powershell
python scripts\build_historical_opportunity_truth_layer.py --data-dir data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1 --data-dir data\mt5_research_exports\phase3_rescue_all_m1_m5_chunk1_after_maxbars --report-path research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md --write --quiet
```

Output:

```text
research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md
data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl
data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_summary_20260501T061655Z.json
```

Rescued truth-layer headline:

- Rows classified: `205,197`
- Unique keys: `205,197`
- AI attempted rows: `0`
- AI call count sum: `0`
- Runtime after fix: about 3.5 minutes

Lower-timeframe coverage after rescue:

| Timeframe | attempted | local coverage | local coverage rate | selected truth rows | horizon complete |
| --- | ---: | ---: | ---: | ---: | ---: |
| M1 | 73950 | 73387 | 99.24% | 30421 | 11836 |
| M5 | 73950 | 73401 | 99.26% | 10098 | 25349 |

Main truth outcomes:

| Outcome | Rows |
| --- | ---: |
| SETUP_NOT_REFINABLE | 61112 |
| PRE_SCREEN_REJECT | 56834 |
| NO_ENTRY | 44098 |
| SL | 14024 |
| PRE_AI_POI_REJECT | 12209 |
| TP | 11124 |
| SAME_BAR | 1907 |
| TIMEOUT | 1662 |
| LOWER_TF_GAPPY | 1135 |
| SKIP_FIRST_NY_CANDLE | 1092 |

Confidence and ambiguity:

| Confidence | Rows |
| --- | ---: |
| HIGH | 37713 |
| MEDIUM | 32888 |
| LOW | 3349 |
| NONE | 131247 |

Selected truth source:

| Source TF | Rows |
| --- | ---: |
| M1 | 30421 |
| M5 | 10098 |
| M15 | 33431 |
| NONE | 131247 |

Interpretation:

- The label substrate is now strong enough for Phase 3 M1/M5 historical truth diagnostics.
- It is not yet a green light for parameter optimization. First compress the truth layer into actionable failure/anatomy questions and cohort candidates.

## 5. Tick Constraint Saved

Commit `f8960f9` recorded the post-maxbars tick constraint in:

```text
research\phase_3_external_feed_validation\LOWER_TF_DATA_RESCUE_AUDIT_2026-05-01.md
```

Post-maxbars tick probe:

```powershell
python scripts\inspect_mt5_tick_availability.py --label phase3_tick_history_probe_post_maxbars_20260501 --write-json --yes-live-readonly
```

Artifact:

```text
data\mt5_research_exports\tick_availability\phase3_tick_history_probe_post_maxbars_20260501_20260501T062554Z.json
```

Post-maxbars tick availability:

| Window | XAUUSD | XAGUSD | GBPJPY | USDJPY | GBPUSD | NAS100 | US30_cash |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-30 13:00-14:00 UTC | 31597 | 9632 | 33218 | 25236 | 17549 | 40833 | 11069 |
| 2026-04-27 13:00-14:00 UTC | 14680 | 6494 | 8446 | 3250 | 5882 | 14564 | 2637 |
| 2026-01-20 13:00-14:00 UTC | 0 | 0 | 0 | 5410 | 0 | 0 | 0 |
| 2025-12-01 13:00-14:00 UTC | 0 | 0 | 0 | 4879 | 0 | 0 | 0 |

Interpretation:

- Raising MT5 max bars fixed M1/M5 bar depth.
- It did not broadly backfill historical tick depth.
- Historical tick data is a broker/server retention constraint from the current terminal state.
- Save it for later. Do not block the M1/M5 truth-layer work on ticks.
- Reopen tick sourcing only when tick-level same-bar ordering becomes the limiting question, or if the CEO wants an alternate broker/tick-source investigation.

## 6. Verification Completed

Commands run after the truth-layer optimization:

```powershell
python -m pytest tests\test_historical_opportunity_truth_layer.py tests\test_mt5_tick_availability.py -q -p no:cacheprovider
python -m py_compile scripts\build_historical_opportunity_truth_layer.py scripts\inspect_mt5_tick_availability.py tests\test_historical_opportunity_truth_layer.py tests\test_mt5_tick_availability.py
git diff --check
```

Result:

```text
10 passed
py_compile passed
git diff --check passed, only CRLF warnings
```

## 7. Where We Are Now

The Phase 3 data-substrate concern is materially resolved for M1/M5 truth:

- We have the broad historical pre-AI opportunity population.
- We have lower-timeframe truth/failure taxonomy v2.
- We have rescued M1/M5 coverage for almost all setup rows.
- We know the historical tick constraint and documented it.
- We have not changed live trading logic, prompts, or config.

The remaining ambiguity is now research/interpretation ambiguity, not an obvious missing-data blocker:

- `NO_ENTRY` is the largest actionable mechanical outcome (`44,098` rows).
- `SL` is the next major failure outcome (`14,024` rows), including `820` immediate stops after fill.
- `SAME_BAR` remains (`1,907` rows), but is now isolated and much smaller than before.
- `LOWER_TF_GAPPY` is explicit (`1,135` rows), mostly a data-quality/schedule issue.
- High-confidence lower-TF resolved rows (`37,713`) are enough for cohort diagnostics, but promotion-style claims still require DSR/PBO discipline.

## 8. Recommended Next Task

Build a research-only diagnostic compression pass over the rescued truth layer.

Suggested artifact:

```text
scripts/analyze_historical_opportunity_truth_layer.py
research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_COHORT_DIAGNOSTICS_2026-05-01.md
tests/test_historical_opportunity_truth_layer_diagnostics.py
```

Suggested input:

```text
data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl
```

Do not start by sweeping parameters. First answer:

1. Which failure buckets dominate by symbol/session/year/regime?
2. Which cohorts have high-confidence lower-TF truth, enough sample size, positive mean R, and tolerable ambiguity?
3. Is `NO_ENTRY` a general mechanical issue or concentrated in specific symbols/sessions/regimes?
4. For `NO_ENTRY`, how close did price come to entry before expiry? This can reveal whether entries are too deep, zones are stale, or no-fill is actually a useful reject signal.
5. For `SL`, how many failures are immediate after fill versus later structural failures?
6. Where do M1 and M5 disagree, and are disagreements concentrated around same-bar/gappy cases?
7. Which low-confidence or gappy rows should be excluded versus sensitivity-tested?

Suggested metrics:

- Counts and rates by `symbol`, `session`, `year`, `truth_regime`, and `symbol|session`.
- Mean R and win rate for high-confidence and high+medium-confidence cohorts separately.
- Failure bucket concentration with sample-size guards.
- M1/M5 selected-source diagnostics.
- `NO_ENTRY` anatomy:
  - distance from entry reached before expiry,
  - percentage of SL distance retraced toward entry,
  - bars until nearest approach,
  - whether no-entry later would have won/lost if filled by a looser offset, if safely derivable from M1/M5.
- `SL` anatomy:
  - immediate stop after fill,
  - bars from fill to stop,
  - MFE before stop if derivable.

Important methodological guardrails:

- Treat this as diagnostic ranking, not alpha validation.
- Do not claim edge from small n. Use explicit minimum sample thresholds.
- Do not optimize buffers/offsets until the diagnostic report identifies stable candidate cohorts.
- Any future parameter sweep must report DSR/PBO and should be scoped to pre-declared cohorts.

## 9. Suggested Fresh-Session First Move

After preflight and reading this handoff, inspect the rescued summary and decide the exact diagnostic schema before writing code:

```powershell
Get-Content research\phase_3_external_feed_validation\HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md
Get-Content data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_summary_20260501T061655Z.json
```

Then implement the diagnostic compression script/report and tests. Leave room for the session to challenge the obvious buckets: if the data suggests a better split than the proposed one, follow the data and document the reason.

