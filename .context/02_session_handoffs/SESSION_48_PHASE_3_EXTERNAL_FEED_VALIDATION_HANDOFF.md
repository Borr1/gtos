# Session 48 Handoff - Phase 3 External Feed Validation Groundwork

**Date:** 2026-05-01  
**Repo:** `C:\Users\MSI\Documents\ai-trading-agent`  
**Handoff HEAD:** `6c14165 feat(phase3): add M5 candidate simulation audit`  
**Purpose:** Give the next fresh session enough context to continue Phase 3 without replaying this long session from chat memory.

## 1. CEO Direction

The CEO wants Phase 3 to move from ingestion toward real validation and invalidation of external-feed alpha and market-data substrate robustness.

Important constraints and preferences stated during the session:

- Do not spend costly API calls now. Plan and build free/offline validation infrastructure first.
- Do not change live trading decision logic.
- Additive shadow logging is acceptable if it does not change live behavior or create new live risk.
- Quality of the snapshot is priority 1. Speed and efficiency matter, but quality wins.
- Use MT5 read-only history if needed. MT5 is connected on the Windows machine.
- If more data is needed, state it clearly and identify the best source or broker path.
- Do not push without CEO approval.

## 2. Mandatory Fresh-Session Preflight

Run the normal project preflight first:

```powershell
python scripts/generate_live_state.py
Get-Content .context\LIVE_STATE.md
Get-ChildItem .context\02_session_handoffs -File | Sort-Object Name | Select-Object -Last 5
Get-Content .context\02_session_handoffs\SESSION_48_PHASE_3_EXTERNAL_FEED_VALIDATION_HANDOFF.md
Get-Content .context\00_core\quick_reference_card.md
Get-Content .context\04_agents\PHASE_3_FREE_FEED_SPRINT_PLAN.md
Get-Content .context\04_agents\PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md
git log --oneline -12
git status --short
```

Do not commit runtime dirt such as `.context/LIVE_STATE.md`, `pipeline_state/*`, or `shadow_logs/*` unless the CEO explicitly asks. At this handoff, known runtime/untracked dirt included:

- `.context/LIVE_STATE.md`
- `pipeline_state/m5_refinement.json`
- several `shadow_logs/*` files

## 3. Recent Phase 3 Commit Stack

Inspect these commits in order before editing:

```text
6c14165 feat(phase3): add M5 candidate simulation audit
1f132eb fix(phase3): extract realized R from trade exits
d72b58d feat(phase3): expand substrate and canonicalize shadow candle time
95bbdab feat(phase3): add candidate diagnostics and mt5 data audit
57b6729 feat(phase3): join candidates to external validation snapshots
f7c7153 feat(phase3): build no-lookahead validation dataset
30bc1c4 feat(phase3): build historical external snapshots
```

Also inspect older Phase 3 feed commits named in the CEO's original brief:

```text
ae59fa0 plan(phase3): add free-feed integration sprint plan
3e9ad15 external feed cache spine
75c7066 fetch CLI
6f21264 snapshot CLI
d6b9dd9 WGC XLSX + single-expiry FlashAlpha GEX
2998811 WGC demand trends workbook import
```

## 4. What Was Built

### External-feed substrate

Current infrastructure supports shadow-only ingestion/cache/snapshot work:

- `src/components/external_feeds.py`
- `scripts/fetch_external_feeds.py`
- `scripts/external_feed_status.py`
- `scripts/build_external_feed_snapshot.py`
- `scripts/build_external_feed_snapshots_historical.py`
- `scripts/build_external_feed_validation_dataset.py`
- `scripts/build_external_feed_candidate_dataset.py`
- `scripts/analyze_external_feed_candidate_diagnostics.py`
- tests in `tests/test_external_feeds.py`

Working feeds observed during Phase 3:

- FRED key detected and DGS10 smoke-fetched.
- CFTC/Socrata works with token aliases.
- LBMA calendar works.
- WGC Goldhub ETF workbook imported: `ETF_Flows_March_2026.xlsx`, 101 rows.
- WGC GDT workbook imported: `GDT_Tables_Q126_EN.xlsx`, 9475 rows.
- FlashAlpha Basic works for single-expiry GEX with `--expiration 2026-05-15`; fetched QQQ/DIA/SPY/GLD/SLV.
- Methodology PDFs were reviewed. No PDF numeric feed is needed yet.

### Market-data expansion

MT5 read-only exports were expanded with chunked `copy_rates_range` support in:

- `scripts/export_mt5_research_ohlcv.py`

Generated ignored data artifacts:

- `data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1/`
- `data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1/`

M15 substrate coverage from MT5:

```text
XAGUSD   99,195 rows, starts 2022-01-03
XAUUSD  100,012 rows, starts 2022-02-01
GBPJPY  100,012 rows, starts 2022-04-14
GBPUSD  100,012 rows, starts 2022-04-14
USDJPY  100,012 rows, starts 2022-04-14
NAS100   72,862 rows, starts 2022-10-20
US30     72,847 rows, starts 2022-10-20
```

M1/M5/H1/D1 export totals:

```text
M1  698,224 rows
M5  699,635 rows
H1  171,309 rows
D1    7,421 rows
```

Important data-quality finding:

- Current MT5 terminal appears capped around 100k bars per timeframe/symbol.
- M1 only reaches roughly January 2026.
- M5 reaches late 2024.
- H1/D1 are much deeper and usable.
- For deeper M1/M5, likely next actions are MT5 terminal "Max bars in chart" increase/restart/refresh, alternate broker terminal export, or an external historical data provider.

### Shadow timestamp improvement

Commit `d72b58d` added additive shadow-only canonical candle close metadata:

- `src/components/data_ingestion.py`
- `src/components/candidate_features_logger.py`
- `src/components/orchestrator.py`

This does not change trade decisions. It improves future joins by logging a canonical `candle_close_utc` instead of relying on approximate runtime timestamps.

### Candidate join and diagnostics

Commit `1f132eb` fixed realized-R extraction from historical trade records by accepting both `realized_r` and historical `realized_R` from multiple locations.

Commit `6c14165` made candidate opportunity simulation timeframe-aware. The candidate join now preloads the requested OHLCV timeframe and passes rows to `resolve_mechanical_outcome`, rather than relying on hardcoded M15 lookup behavior.

Latest M5 simulation artifact:

```text
data/external/validation/calendar_macro_bundle_v1/candidate_join/phase3_candidate_calendar_macro_join_2022_2026_plus_gap_m5_sim_v2_20260501T015608Z.jsonl
```

Latest diagnostic doc:

```text
research/phase_3_external_feed_validation/CANDIDATE_DIAGNOSTIC_M5_SIM_2026-05-01.md
```

Result:

```text
76 rows kept
70 matched to validation snapshots
2 actual realized-R rows
29 synthetic/mechanical R rows
```

This is not enough for alpha claims. It is only a diagnostic proving the join path works.

## 5. Critical Clarification: The 76 Candidate Confusion

The CEO correctly challenged the apparent "76 candidates from 2022 to 2026" number.

Correct interpretation:

- `76` is not the full 2022-2026 historical candidate count.
- It is the current recent live/shadow candidate log joined to the new 2022-2026 external-feed substrate.
- The all-candle external validation substrate is much larger: about `644,952` rows across the 7 instruments.
- What is still missing is a historical opportunity/candidate replay that regenerates current-pipeline opportunities across 2022-2026.

Current shadow candidate log checked during the session:

```text
426 total rows
77 CANDIDATE rows
first row around 2026-04-17
last row around 2026-05-01
```

Therefore the plan is still healthy. The issue is not "too few historical candidates"; it is that historical candidates have not yet been generated.

## 6. What We Found

### We are closer

The project now has:

- A no-lookahead external-feed snapshot substrate.
- A validation dataset path.
- Candidate-to-snapshot join tooling.
- A clearer market-data quality audit.
- Additive canonical candle timestamps for future live/shadow joins.
- Evidence that current MT5 can support broad M15/H1/D1 research.

### We are not ready to claim alpha

No alpha claim should be made from the current candidate diagnostic.

Reasons:

- Actual realized-R coverage is too sparse.
- The 76/77 candidate rows are recent live/shadow rows, not a historical candidate population.
- Synthetic/mechanical outcomes are useful diagnostics but cannot substitute for full production-faithful AI outcomes.
- External-feed bundles must be frozen before evaluation to avoid p-hacking.

### Main uncertainty

The biggest remaining uncertainty is the high-N historical opportunity population:

- How many current-pipeline pre-AI opportunities exist across 2022-2026?
- Which deterministic gates remove them?
- Which symbols/timeframes contribute useful sample size?
- Can external-feed bundles explain realized/mechanical outcomes out of sample after DSR/PBO controls?

## 7. Next Session Objective

Highest-leverage next action:

**Build the historical pre-AI opportunity dataset.**

This should be free/offline and should not spend Anthropic/OpenAI/API budget.

Target artifact:

```text
scripts/build_historical_opportunity_dataset.py
```

Expected output:

```text
data/external/validation/<bundle>/historical_opportunities/<label>_<timestamp>.jsonl
research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md
```

Minimum row fields:

```text
symbol
broker_symbol
timeframe
candle_close_utc
kill_zone
session
spread/session metadata if available
deterministic_bias
pre_ai_gate_status
pre_ai_gate_reason
would_send_ai
external_snapshot_match_status
external_snapshot_as_of_utc
bundle_id
feature availability flags
mechanical outcome fields if available
```

Do not call the AI. The first version should enumerate and label deterministic opportunities only.

## 8. Suggested Implementation Path

Recommended no-cost plan:

1. Inspect `scripts/simulate_t7_live_period.py`.
2. Inspect reusable helpers for loading OHLCV, building MSO, kill-zone filtering, deterministic prescreening, and mechanical outcome simulation.
3. Export or assemble a combined replay OHLCV root with M15/H1/H4/D1 if needed.
4. Build a research-only opportunity dataset generator.
5. Join opportunities to existing external validation snapshots.
6. Add tests for:
   - no-lookahead snapshot matching by `as_of_utc`, not observation date
   - one row per symbol/candle opportunity
   - `would_send_ai` is computed without calling AI
   - missing external snapshot produces explicit null flags, not dropped rows
7. Produce an audit markdown with counts by symbol, year, kill zone, and pre-AI gate status.

Potential export command if a combined replay root is needed:

```powershell
python scripts/export_mt5_research_ohlcv.py --start 2022-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --label phase3_replay_ohlcv_2022_2026_fn_v1 --timeframes M15,H1,H4,D1 --chunk-days 30 --yes-live-readonly
```

Do not run a full paid AI replay unless the CEO gives separate explicit budget approval.

## 9. Validation Protocol Still Required

The next session should either create or extend a committed protocol doc covering:

- target/outcome being tested
- baseline comparison
- effective N
- DSR/PBO requirements from project methodology
- cumulative trial budget protection
- invalidation rules for a source or bundle

Frozen bundles:

```text
calendar_macro_bundle_v1:
  LBMA fix calendar
  FRED real yield/USD/vol
  CFTC positioning
  WGC ETF/GDT context

nas_us30_gamma_regime_v1:
  FlashAlpha GEX proxies
  Cboe/FRED vol proxies
  OPEX/calendar controls
```

Do not evaluate individual features opportunistically before the bundle hypotheses are frozen.

## 10. Market-Data Expansion Notes

Current view:

- M15/H1/D1 from MT5 are usable for broad substrate and opportunity enumeration.
- Deep M1/M5 is not yet good enough from the current terminal alone.
- Recent tick history is available from MT5, but needs a dedicated read-only exporter before bulk backfill.

One-off tick probe found strong recent availability for 2026-04-28/2026-04-30 windows:

```text
XAUUSD hundreds of thousands of ticks per day
XAGUSD hundreds of thousands of ticks per day
GBPJPY hundreds of thousands of ticks per day
USDJPY hundreds of thousands of ticks per day
GBPUSD hundreds of thousands of ticks per day
NAS100 over 1M ticks per active day
US30_cash hundreds of thousands of ticks per day
```

Recommended data-source research direction:

- First try improving MT5 terminal history depth with settings/restart/cache refresh.
- Then test FTMO or alternate broker demo terminals for deeper M1/M5.
- For FX, stable public/download/API candidates include Dukascopy, OANDA, TrueFX, and paid low-cost vendors if needed.
- For options/vol, prefer official Cboe historical files where available and paid APIs like Polygon/ThetaData only if the free path cannot answer the question.
- Avoid fragile scrapers. In particular, do not automate extraction from pages whose terms prohibit automated quote-table extraction.

## 11. Blockers and Ambiguities

No fresh-session blocker for the next no-cost artifact.

Known ambiguities to resolve with evidence:

- Whether terminal settings can extend M1/M5 depth enough without another broker.
- Whether historical opportunity count is large enough after deterministic gates.
- Whether NAS100/US30 pre-2022-10 depth can be sourced without licensing fragility.
- Whether FlashAlpha single-expiry GEX has enough historical continuity to matter or is mainly forward-shadow only.
- Whether WGC quarterly/monthly publication lag gives enough sample size for candle-level validation or only regime context.

Potential CEO action later, not needed immediately:

- Increase MT5 "Max bars in chart" / "Max bars in history", restart terminal, and refresh symbols if deeper M1/M5 is needed.
- Provide/approve an alternate broker demo terminal if current broker cannot expose enough intraday depth.
- Approve paid data only after the free substrate shows the exact missing interval/timeframe and why it matters.

## 12. Verification Already Run

Latest relevant test run before this handoff:

```powershell
python -m pytest tests/test_external_feeds.py -q -p no:cacheprovider --basetemp=C:\tmp\pytest_gtos_phase3_m5_docs
```

Result:

```text
43 passed
```

Other earlier verification in this session included focused external-feed tests and `py_compile` checks.

## 13. Recommended First Commands in Fresh Session

After preflight, run:

```powershell
git show --stat 6c14165
git show --stat 1f132eb
git show --stat d72b58d
Get-Content research\phase_3_external_feed_validation\CANDIDATE_DIAGNOSTIC_M5_SIM_2026-05-01.md
Get-Content research\phase_3_external_feed_validation\MARKET_DATA_EXPANSION_AUDIT_2026-05-01.md
Get-Content scripts\build_external_feed_candidate_dataset.py
Get-Content scripts\simulate_t7_live_period.py
```

Then proceed to implement the historical opportunity generator.

## 14. Bottom Line

We are closer to the Phase 3 goal.

The ingestion and snapshot substrate are no longer the main problem. The main problem is now statistical power: generate the historical current-pipeline opportunity population, join it no-lookahead to external-feed bundles, and only then start validation/invalidation.

Do not interpret the current 76 candidate diagnostic as the historical candidate count. It is only the recent live/shadow candidate population attached to the larger 2022-2026 candle substrate.
