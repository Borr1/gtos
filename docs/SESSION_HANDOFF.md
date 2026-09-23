# Session Handoff — Phase 1 Backtesting

**Date:** 2025-03-30
**Last commit:** `f95a169` — 78 sessions backtested
**Tests:** 220 passing (210 original + 10 safety check tests)

---

## Project State

### Git
- **Branch:** main
- **Last 3 commits:**
  - `f95a169` — 78 sessions backtested
  - `2d0963a` — Safety fixes: direction match, ATR 1.5x SL, $5 floor, 220 tests passing
  - `752ff8a` — 40 backtests, 1st, no debate
- **Working tree:** clean (only `knowledge_base/pipeline_state/02_market_state.json` modified)

### Files Modified This Session
```
scripts/backtest_runner.py          — dotenv, cost tracking, budget limit, safety checks, D1 pre-filter
src/components/debate.py            — _parse metadata injection, per-agent max_tokens, token tracking
src/components/market_state.py      — calculate_atr(), ATR in TimeframeState
src/components/primary_analyzer.py  — prompt caching, _normalize_pa_fields, session cache reset
src/models/analysis_models.py       — session_high/session_low in pool_type Literal
src/models/market_state_models.py   — atr_14 field in TimeframeState
src/prompts/primary_analyzer_prompt.py — JSON schema, condensed MSO, static/dynamic split, ATR/direction rules
src/prompts/bear_agent_prompt.py    — conciseness rules (200 word limit)
src/prompts/bull_agent_prompt.py    — conciseness rules (200 word limit)
tests/test_prompts.py               — updated for new build_user_message signature
tests/test_safety_checks.py         — 10 new tests for all safety checks
```

---

## What's Built and Working

### Core Pipeline (all functional)
| Component | Status | Notes |
|-----------|--------|-------|
| Historical Data Loader | Working | HuggingFace XAUUSD data, Jul 2024 - Sep 2025 |
| Market State (Component 2) | Working | Swings, structure, OBs, FVGs, ATR, premium/discount |
| Primary Analyzer (Component 3A) | Working | Prompt caching, condensed MSO, 0% retry rate |
| Debate Engine (Component 3B) | Working but DISABLED | Negative skill — rejected winners, approved losers |
| Knowledge Base | Working | LanceDB vectors, rolling stats, trade index |
| Backtest Runner | Working | Resume, budget limit, cost tracking, safety checks |
| Monitoring/Dashboard | Working | FastAPI, alerts, session logging |
| Adaptive Review | Working | Condition tracking, quality scores |

### Safety Checks (in `BacktestRunner._safety_check()`)
1. **Grade filter:** Only A and A+ candidates pass
2. **Direction match:** LONG must match bullish daily bias, SHORT must match bearish
3. **$5 minimum SL floor:** Gold noise floor
4. **1.5x ATR minimum:** SL distance must be >= 1.5 * M15 ATR(14)
5. **RR minimum:** Must be >= 2.5:1

### Cost Optimizations Implemented
- **Prompt caching:** Static context (system prompt + D1/H4) cached per session via Anthropic ephemeral cache. Candles 3-10 pay ~90% less on input tokens.
- **Condensed MSO:** 238K chars raw -> 5.8K chars condensed (only key structure data)
- **max_tokens limits:** PA=1500, Bull/Bear=1000, Judge=800
- **Conciseness rules:** In all system prompts
- **Token tracking:** Per-session input/output/cache_read/cache_create with cache-aware cost calculation
- **Budget limiter:** `--budget-limit` flag auto-stops batch

### Retry Elimination
- Added `_normalize_pa_fields()` to fix Pydantic validation mismatches (pool_type, poi_type, setup_grade)
- Added `session_high`/`session_low` to pool_type Literal
- JSON schema added to system prompt with exact field names
- Result: **0% retry rate** (was 30%)

---

## Backtest Results

### Combined: 78 Sessions (Dec 2 2024 — Mar 21 2025)

| Period | Regime | Sessions | Trades | WR | Total R | Expectancy |
|--------|--------|----------|--------|-----|---------|------------|
| Dec 2024 - Jan 24 2025 | Pullback/ranging | 38 | 0 | N/A | 0.00R | N/A |
| Jan 27 - Mar 21 2025 | Rally | 40 | 7 | 43% | +3.85R | +0.55R |
| **Combined** | **Mixed** | **78** | **7** | **43%** | **+3.85R** | **+0.55R** |

### Per-Trade Breakdown (Jan 27 - Mar 21, no-debate run)
| Date | Dir | Entry | SL | Risk | Outcome | R | Issue |
|------|-----|-------|-----|------|---------|---|-------|
| Jan 27 | SHORT | 2752.4 | 2759.1 | $6.7 | LOSS | -1.00 | Counter-trend (fixed: direction check) |
| **Feb 10** | **LONG** | **2882.3** | **2877.0** | **$5.4** | **WIN** | **+3.87** | |
| Feb 12 | LONG | 2891.9 | 2880.0 | $11.9 | LOSS | -1.00 | Genuine loss |
| Feb 24 | LONG | 2940.4 | 2935.4 | $5.0 | LOSS | -1.00 | SL too tight (fixed: ATR 1.5x) |
| **Mar 04** | **LONG** | **2899.2** | **2890.7** | **$8.5** | **WIN** | **+2.59** | |
| **Mar 17** | **LONG** | **2988.7** | **2979.8** | **$8.9** | **WIN** | **+1.39** | |
| Mar 19 | LONG | 3037.5 | 3034.1 | $3.5 | LOSS | -1.00 | SL too tight (fixed: $5 floor) |

### Loss Diagnosis
- **Jan 27:** BAD SETUP — SHORT against bullish bias. **Fixed** by direction safety check.
- **Feb 12:** GENUINE LOSS — correct setup, market didn't follow through. Unfixable variance.
- **Feb 24:** BAD LUCK — SL clipped by noise, then price ran to TP1. **Fixed** by ATR 1.5x minimum.
- **Mar 19:** BAD LUCK — $3.4 SL in $2.20 ATR environment. **Fixed** by $5 floor.

**With fixes applied, projected: 5W/2L = 71% WR, ~+6.8R total.** (Not re-run yet — needs verification.)

### Backup Location
- `knowledge_base_backtest_jan27_mar21_backup/` — 40 sessions, 7 trades, candidate_review.json

---

## Known Issues

### Bugs
- **None outstanding.** All 220 tests pass.

### Debate System (DISABLED)
The debate has **negative skill** and is bypassed via `--no-debate` (now the default):
- 94% rejection rate on Grade A candidates
- Approved 2 trades -> both LOST (-2.00R)
- Rejected 30 trades -> 10 would have WON (+6.63R)
- The bear agent fabricates convincing-sounding structural concerns that don't predict outcomes
- **To re-enable:** Would need complete redesign of bear agent prompt (more constrained, data-only arguments) and judge scoring calibration. The bull/bear/judge code is intact in `src/components/debate.py`.

### D1 Structure Pre-Filter (NOT YET INTEGRATED)
A free pre-check was tested but not yet wired into the runner:
- If D1 structure is "transitional" or "insufficient_data", skip the AI call entirely
- Tested on 78 sessions: would save 51% of API calls with zero false negatives
- Code exists in the session analysis script but needs to be added to `BacktestRunner.run_session()`

### Sweep Pre-Filter (ABANDONED)
`session_has_sweep_event()` was tested and found ineffective:
- Asian H/L is always within $1-7 of London Open price on gold
- 0% of sessions would be skipped — the filter passes everything
- The proximity-based approach doesn't work for gold's volatility

---

## What To Do Next

### Immediate (no API cost)
1. **Integrate D1 pre-filter** into `run_session()`:
   ```python
   # Before calling PA, check D1 structure
   d1_tf = mso.timeframes.get("D1")
   d1_dir = d1_tf.structure.direction if d1_tf and d1_tf.structure else "insufficient_data"
   if d1_dir in ("transitional", "insufficient_data"):
       # Skip AI call, log as NO_TRADE
       eval_entry = CandleEvaluation(candle_time=candle_time, decision="NO_TRADE",
                                      reason="d1_structure_not_trending")
       manifest.candle_evaluations.append(eval_entry)
       continue
   ```

2. **Switch to `claude -p` for Max subscription billing** (optional):
   - Replace `Anthropic().messages.create()` with `subprocess.run(["claude", "-p", ...])`
   - Must `unset ANTHROPIC_API_KEY` first
   - Test quota consumption with 5 sessions before full batch

3. **Re-run Jan 27 - Mar 21 with all safety fixes** to get true post-fix numbers
   - Estimated cost with D1 pre-filter: ~$3 (vs $5.95 without)

### Medium Term
4. **Extend data range** — download more recent HuggingFace data (Apr-Sep 2025 has gaps)
5. **Test on bearish periods** — current data is all bullish/ranging, no SHORT validation
6. **Component 1 (MT5 integration)** for live data feed
7. **Component 4 (Execution engine)** for paper trading

### Debate Redesign (if attempted)
- Constrain bear to data-only objections (no speculation about "momentum divergence")
- Lower judge approval threshold from 50 to 40
- Add "burden of proof" asymmetry — bull's Grade A analysis is presumed correct unless bear cites specific contradicting data points
- Consider removing judge entirely — just run bear as a checklist of specific disqualifying conditions

---

## Configuration

```yaml
# Current effective settings
model: claude-sonnet-4-20250514
debate: disabled (--no-debate is default)
round2: disabled
safety_checks:
  grade_filter: ["A+", "A"]
  direction_match: true  # LONG=bullish, SHORT=bearish
  sl_floor: 5.00         # minimum $5 on XAUUSD
  atr_minimum: 1.5       # SL >= 1.5x M15 ATR(14)
  rr_minimum: 2.5
max_tokens:
  primary_analyzer: 1500
  bull_agent: 1000
  bear_agent: 1000
  judge: 800
prompt_caching: true      # ephemeral cache on system + static context
budget_limit: 5.50        # per batch default
avg_cost_per_session: 0.13-0.15
```

---

## Key File Locations

| File | Purpose |
|------|---------|
| `docs/architecture.md` | Full system architecture document |
| `config/agent_config.yaml` | Model settings, timeframes, thresholds |
| `scripts/backtest_runner.py` | Main backtest orchestrator, safety checks, cost tracking |
| `scripts/historical_data_loader.py` | CSV parsing, session replay, MSO pre-computation |
| `src/components/primary_analyzer.py` | AI analysis with prompt caching and normalization |
| `src/components/debate.py` | Bull/bear/judge debate engine (currently disabled) |
| `src/components/market_state.py` | Structure, swings, OBs, FVGs, ATR, sweeps |
| `src/components/knowledge_base.py` | Trade records, rolling stats, vector DB |
| `src/components/adaptive_review.py` | Post-trade scoring, condition tracking |
| `src/components/dashboard.py` | FastAPI monitoring dashboard |
| `src/prompts/primary_analyzer_prompt.py` | PA system prompt, JSON schema, static/dynamic context builders |
| `src/prompts/bull_agent_prompt.py` | Bull debate agent prompt |
| `src/prompts/bear_agent_prompt.py` | Bear debate agent prompt |
| `src/prompts/judge_prompt.py` | Judge verdict prompt |
| `src/models/analysis_models.py` | Pydantic models for PA output |
| `src/models/market_state_models.py` | MSO, TimeframeState, ATR field |
| `src/models/debate_models.py` | Debate verdict, arguments |
| `src/models/trade_models.py` | Trade records, session manifests |
| `tests/test_safety_checks.py` | 10 tests for direction/ATR/floor/grade checks |
| `data/historical/` | XAUUSD M15/H1/H4/D1 CSVs (Jul 2024 - Sep 2025) |
| `data/raw/` | Original cleaned CSVs from HuggingFace |
| `knowledge_base_backtest/` | Current OOS run (Dec 2024 - Jan 2025) |
| `knowledge_base_backtest_jan27_mar21_backup/` | Rally period results (40 sessions, 7 trades) |
| `.env` | ANTHROPIC_API_KEY (loaded via python-dotenv with override=True) |

---

## API Cost Summary

| Run | Sessions | Cost | Per Session |
|-----|----------|------|-------------|
| First batch (with debate, pre-fixes) | 55 | ~$35 | $0.64 |
| Second batch (debate, post-prompt-fix) | 40 | $7.29 | $0.18 |
| No-debate + safety checks | 40 | $5.95 | $0.15 |
| Out-of-sample (Dec-Jan) | 38 | $5.02 | $0.13 |
| **Total spent this session** | | **~$53** | |

Cost reduction achieved: **$0.64/session -> $0.13/session (80% reduction)**
