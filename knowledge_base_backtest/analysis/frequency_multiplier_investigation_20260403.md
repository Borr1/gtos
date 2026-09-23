# Frequency Multiplier Investigation — Levers 2, 3, 4

**Date:** 2026-04-03
**Status:** COMPLETE
**Cost:** $0 (pure data analysis on existing candle files)
**Runtime:** 15.6s across all 5 instruments
**Data:** 2024-01-02 to 2026-04-02 (~27 months, ~582 trading days per instrument)

---

## Executive Summary

| Lever | Best Opportunity | Trades/Mo (all instruments) | Edge Quality | Priority |
|-------|-----------------|---------------------------|--------------|----------|
| **Lever 4: Extended NY 15:30-17:00** | XAUUSD, NAS100, XAGUSD | ~3.5 qualifying/mo est. | 48-50% cont, MFE/MAE ~1.0 | **1 — lowest effort, broadest coverage** |
| **Lever 3: Loose pre-screen** | GBPUSD, XAGUSD | ~2-3 qualifying/mo est. | 53-55% cont where positive | **2 — for GBPUSD/XAGUSD only** |
| **Lever 4: Extended London 09:30-12:00** | GBPUSD, EURUSD | ~2-3 qualifying/mo est. | 50% cont, MFE/MAE ~1.04 | **3 — London instruments only** |
| **Lever 2: H4 OB Retest** | All | 0.6-0.7/mo per instrument | 70-85% cont (!), MFE/MAE 1.0-2.3 | **4 — high edge but tiny frequency, 100% overlap** |

**Key finding:** The H4 OB retest lever shows extraordinary edge quality (70-85% continuation) but fires extremely rarely (0.6-0.7/mo) and has **100% overlap** with dates that already pass the pre-screen — meaning it adds ZERO new trade dates. It is an alternative entry on existing dates, not a frequency multiplier.

The true frequency multipliers are **extended session windows** (low effort, moderate edge) and **pre-screen loosening** (low effort, instrument-dependent edge).

---

## Lever 2: H4 OB Retest — Detailed Results

### 2A: H4 OB Generation Rate

| Instrument | Total H4 OBs | D1 Clear Dates | D1+H4 Aligned | KZ Retests | Extended Retests | KZ/Mo | Ext/Mo | Avg Zone Width |
|------------|-------------|----------------|----------------|------------|-----------------|-------|--------|---------------|
| XAUUSD | 184 | 232 (40%) | 182 (31%) | 20 | 25 | 0.7 | 0.9 | $28.93 |
| GBPUSD | 167 | 247 (42%) | 134 (23%) | 18 | 14 | 0.7 | 0.5 | 26 pips |
| EURUSD | 163 | 223 (38%) | 122 (21%) | 17 | 14 | 0.6 | 0.5 | 26 pips |
| NAS100 | 172 | 259 (48%) | 197 (36%) | 18 | 31 | 0.7 | 1.1 | 147 pts |
| XAGUSD | 180 | 243 (42%) | 157 (27%) | 15 | 26 | 0.6 | 1.0 | $1.08 |

H4 OBs are created at ~6-7/month per instrument when D1+H4 align. But most get mitigated before they can be retested during kill zone hours. Only ~0.6-0.7/month survive to be retested during KZ, rising to ~0.5-1.1/month if we include extended hours.

### 2B: H4 vs H1 Overlap — CRITICAL FINDING

**Overlap: 100% across ALL instruments.**

Every single H4 OB retest opportunity occurs on a date that already passes the standard pre-screen (D1 clear + H4 aligned). This makes sense — the H4 OB retest by definition requires D1+H4 alignment, which IS the pre-screen.

**Implication:** The H4 framework does NOT add new trade dates. It only provides an alternative entry mechanism on days that the H1 ob_retest already evaluates. The value proposition shifts from "more trades" to "better entries on existing dates" — a quality play, not a frequency play.

### 2C: H4 OB Retest Outcomes

| Instrument | n | 3h Cont% | MFE/MAE | Assessment |
|------------|---|----------|---------|------------|
| XAUUSD | 20 | **85.0%** | **2.20** | Exceptional edge, tiny sample |
| NAS100 | 18 | **77.8%** | **1.74** | Very strong, tiny sample |
| XAGUSD | 15 | **73.3%** | **2.31** | Very strong, tiny sample |
| GBPUSD | 18 | **72.2%** | **1.40** | Strong, tiny sample |
| EURUSD | 17 | **70.6%** | **1.00** | Good continuation, breakeven MFE/MAE |

The continuation rates are extraordinary (70-85% vs 48% baseline), but n=15-20 per instrument means high variance. The edge appears real but the frequency is too low to be a primary frequency multiplier.

### Lever 2 Verdict

**NOT a frequency multiplier.** Zero new trade dates (100% overlap). However, the edge quality data suggests H4 OB zones could be used as a **confirmation filter** within the existing H1 framework — if price is near both an H1 OB and H4 OB, the setup is likely higher quality. This is a quality lever, not a frequency lever. Consider as a future enhancement after the main frequency levers are implemented.

---

## Lever 3: Pre-Screen Loosening — Detailed Results

### 3A: Killed Date Categorization

| Instrument | Total | Pass | Kill | Cat1 (H4+H1 aligned) | Cat2 (all unclear) | Cat3 (H4 mismatch) | Cat4 (H1 conflict) |
|------------|-------|------|------|----------------------|-------------------|--------------------|--------------------|
| XAUUSD | 582 | 182 (31%) | 400 (69%) | **321 (55%)** | 14 (2%) | 50 (9%) | 15 (3%) |
| GBPUSD | 586 | 134 (23%) | 452 (77%) | **274 (47%)** | 15 (3%) | 113 (19%) | 50 (9%) |
| EURUSD | 586 | 122 (21%) | 464 (79%) | **300 (51%)** | 14 (2%) | 101 (17%) | 49 (8%) |
| NAS100 | 544 | 197 (36%) | 347 (64%) | **235 (43%)** | 25 (5%) | 62 (11%) | 25 (5%) |
| XAGUSD | 583 | 157 (27%) | 426 (73%) | **298 (51%)** | 14 (2%) | 86 (15%) | 28 (5%) |

**Category 1 dominates killed dates.** "D1 unclear but H4+H1 aligned" accounts for 43-55% of all killed dates. This is the primary opportunity pool.

Cat2 (all unclear) and Cat4 (H1 conflict) are small and should remain killed. Cat3 (D1 clear but H4 mismatch) is the second-largest bucket but represents genuine structural conflict.

### 3A continued: Cat1 with Displacement + OB Retest

| Instrument | Cat1 Dates | Cat1/Mo | With Displacement | Disp/Mo | With Disp+Retest |
|------------|-----------|---------|------------------|---------|-----------------|
| XAUUSD | 321 | 11.9 | 255 (79%) | 9.5 | 194 (60%) |
| GBPUSD | 274 | 10.1 | 219 (80%) | 8.1 | 164 (60%) |
| EURUSD | 300 | 11.1 | 230 (77%) | 8.5 | 191 (64%) |
| NAS100 | 235 | 8.7 | 183 (78%) | 6.8 | 147 (63%) |
| XAGUSD | 298 | 11.0 | 217 (73%) | 8.0 | 163 (55%) |

~80% of Cat1 dates show displacement activity, and ~60% show displacement + OB retest. The opportunity pool is large.

### 3B: Cat1 Outcome Quality — THE CRITICAL TEST

| Instrument | n | Cat1 3h Cont% | Cat1 MFE/MAE | Baseline 3h Cont% | Verdict |
|------------|---|-------------|-------------|-------------------|---------|
| XAUUSD | 255 | **55.7%** | 0.90 | 48.7% | **Above baseline cont, but MFE/MAE < 1** |
| GBPUSD | 219 | **53.4%** | **1.11** | ~49% | **Above baseline on BOTH metrics** |
| XAGUSD | 217 | **54.8%** | 0.91 | ~48% | Above baseline cont, MFE/MAE < 1 |
| EURUSD | 230 | 48.7% | 0.88 | ~48% | At baseline, poor MFE/MAE |
| NAS100 | 183 | 48.1% | 0.74 | ~48% | At baseline, worst MFE/MAE |

**GBPUSD is the standout.** It shows both above-baseline continuation AND MFE/MAE > 1.0 on Cat1 dates. XAUUSD and XAGUSD show positive continuation lift but MFE/MAE is below 1.0 (meaning losers are bigger than winners on average). EURUSD and NAS100 show no improvement over baseline.

**Recommendation:** Loosen pre-screen for **GBPUSD** (clear win) and consider **XAUUSD/XAGUSD** (positive continuation but needs tighter stop management). Do NOT loosen for EURUSD or NAS100.

### 3C: Architectural Changes Required

To allow Cat1 dates through, these code locations need changes:

1. **`scripts/batch_backtest.py:94-131`** — `prescreen_date()`: Change Layer 1 from requiring D1 bullish/bearish to accepting "D1 transitional/unclear IF H4+H1 agree". Add a Layer 1b check.

2. **`src/components/orchestrator.py:590-608`** — `prescreen_mso()`: Same logic as above for the live system.

3. **`src/prompts/primary_analyzer_prompt.py:165`** — PA prompt Step U1/BR1: Currently says "D1 must be clear, H4 must agree." Would need a secondary path: "If D1 is transitional, H4 and H1 must both be clear and agree."

4. **`src/components/permissions.py:92-98`** — Gate 1 safety: Currently checks `daily_bias.direction` against trade direction. If D1 is unclear/transitional, this gate would need to check H4 direction instead.

**Implementation effort: ~2-4 hours.** The architecture is already parameterized. Main risk is prompt changes — the PA prompt currently anchors on D1 clarity as a foundational rule. Allowing transitional D1 requires careful prompt engineering to prevent quality degradation.

---

## Lever 4: Extended Sessions — Detailed Results

### 4A: Displacement Activity by Hour (Selected Key Hours)

Current KZ capture rates:
- XAUUSD: 29.7% of all displacements
- GBPUSD: 31.4%
- EURUSD: 30.1%
- NAS100: 30.3%
- XAGUSD: 28.1%

**The current KZ windows capture only ~30% of total displacement activity.** 70% of displacements happen outside the 5-hour KZ windows.

### Top displacement hours OUTSIDE current KZ:

| Hour (UTC) | Best Instruments | Disps/Day (avg) | Cont 3h% | Note |
|------------|-----------------|-----------------|---------|------|
| **15:00-16:00** | All | 0.85-1.42 | 46-54% | Post-NY, pre-US close. Highest volume hour for NAS/XAUUSD/XAGUSD |
| **16:00-17:00** | All | 0.75-1.42 | 49-54% | US equity session overlap |
| **10:00-11:00** | GBPUSD, EURUSD | 1.36-1.39 | 50% | London session core (post KZ) |
| **03:00-04:00** | XAUUSD, XAGUSD | 0.99-1.29 | 47-48% | Asian pre-London |
| **17:00-18:00** | NAS100, XAUUSD | 0.87-1.34 | 49-52% | US cash session close |

### 4B: Extension Window Analysis

#### 15:30-17:00 Extended NY — **TOP CANDIDATE**

| Instrument | Disps/Mo | Cont 3h% | MFE/MAE | OB Retest% | Worth Testing? |
|------------|---------|----------|---------|-----------|---------------|
| XAUUSD | 52.5 | **50.4%** | **1.06** | 81% | **YES** |
| NAS100 | 47.3 | **50.4%** | **1.04** | 85% | **YES** |
| XAGUSD | 56.9 | 48.6% | 1.02 | 83% | **YES** |
| GBPUSD | 34.5 | 48.7% | 0.95 | 82% | NO (MFE/MAE < 1) |
| EURUSD | 34.4 | 48.6% | 0.98 | 84% | NO (marginal) |

This is the single largest untapped displacement pool. The 15:00-17:00 UTC window is the US equity cash session (09:30-11:00 EST for NAS100) and gold's most active trading period. Continuation rates are at or above baseline.

**Critical note:** The 15:00 hour is technically inside the current KZ (ends 15:30). The real extension is 15:30-17:00.

#### 09:30-12:00 Extended London — London Instruments

| Instrument | Disps/Mo | Cont 3h% | MFE/MAE | Worth Testing? |
|------------|---------|----------|---------|---------------|
| GBPUSD | **81.4** | **50.2%** | **1.04** | **YES** |
| EURUSD | **81.5** | 49.2% | 1.04 | **YES** |
| XAGUSD | 42.1 | 50.4% | 1.08 | **YES** |
| XAUUSD | 46.0 | 46.7% | 0.99 | NO |
| NAS100 | 60.0 | 47.7% | 0.96 | NO |

For GBPUSD and EURUSD, the 09:30-12:00 window has the HIGHEST displacement frequency of any extension window (~81/month raw). These are London-session instruments — they remain active well past the 09:30 KZ cutoff.

#### 05:00-07:00 Pre-London

| Instrument | Disps/Mo | Cont 3h% | MFE/MAE | Worth Testing? |
|------------|---------|----------|---------|---------------|
| XAUUSD | 19.5 | **50.7%** | **1.07** | **YES** |
| XAGUSD | 22.2 | 48.6% | 1.02 | **YES** |
| GBPUSD | 17.4 | 48.1% | 1.03 | **YES** |
| EURUSD | 15.7 | 49.8% | 0.96 | NO |
| NAS100 | 9.4 | 47.2% | 0.83 | NO |

Pre-London activity is modest. OB retest rates are good (83-88%). Could be viable for gold and silver.

#### 22:00-02:00 Asian Open

| Instrument | Disps/Mo | Cont 3h% | MFE/MAE | Worth Testing? |
|------------|---------|----------|---------|---------------|
| XAUUSD | 19.3 | 45.1% | 1.10 | **YES** |
| NAS100 | 16.6 | 49.7% | 1.07 | **YES** |
| GBPUSD | 25.4 | 41.0% | 0.79 | NO |
| EURUSD | 19.6 | 43.2% | 0.93 | NO |
| XAGUSD | 17.7 | 43.3% | 1.08 | NO |

Continuation rates are generally below baseline. Only XAUUSD and NAS100 show MFE/MAE > 1.0, but NAS100 has limited liquidity in Asian hours. **Not recommended as a priority.**

### 4C: OB Retest Rate by Hour

OB retest rates (origin revisit within 18 candles) are remarkably stable across hours:
- Peak: 91-95% during 13:00-14:00 (NY open) across all instruments
- Trough: 75-80% during 19:00-22:00 (late session)
- KZ average: ~87%
- Extension window average: ~84%

The drop is modest. Entry mechanics remain reliable outside KZ.

### 4E: History Check — Extended London (09:30-10:30) ZERO Gold Trades

The Apr 2 test found 0 trades on XAUUSD in the 09:30-10:30 extended window across 130+ dates. My data explains why:

1. **There WERE displacements** — XAUUSD shows 485 displacements in the 10:00 hour alone (0.83/day). This is NOT a displacement desert.

2. **The problem is continuation quality** — XAUUSD 10:00 hour has only **45.6% continuation** (below baseline) and MFE/MAE of **1.03** (essentially breakeven). The AI correctly found no qualifying setups.

3. **GBPUSD is different** — GBPUSD 10:00 hour has **50.4% continuation** and 794 total displacements (1.36/day). This IS the peak London hour for GBPUSD. The 09:30-12:00 window on GBPUSD passed the worth-testing threshold.

**Conclusion:** The extended London failure on gold was instrument-specific, not a structural problem. The same window is viable for London-native instruments (GBPUSD, EURUSD).

---

## Synthesis: Priority-Ranked Recommendations

### Tier 1: Implement Now (Low effort, clear positive signal)

| # | Lever | Instruments | Est. Additional Trades/Mo | Edge | Effort |
|---|-------|------------|--------------------------|------|--------|
| 1 | **Extended NY 15:30-17:00** | XAUUSD, NAS100, XAGUSD | 2-3 (after AI filtering) | 50% cont, MFE/MAE 1.02-1.06 | Config change only |
| 2 | **Extended London 09:30-12:00** | GBPUSD, EURUSD | 2-4 (after AI filtering) | 50% cont, MFE/MAE 1.04 | Config change only |

These are pure config changes — just widen the KZ windows in `agent_config.yaml` per instrument. Estimated ~15% of raw displacements qualify as trades after AI filtering, giving 2-4 additional trades/month across the portfolio.

### Tier 2: Test via Batch (Low effort, needs validation)

| # | Lever | Instruments | Est. Additional Trades/Mo | Edge | Effort |
|---|-------|------------|--------------------------|------|--------|
| 3 | **Loose pre-screen (Cat1)** | GBPUSD | 1-2 | 53.4% cont, MFE/MAE 1.11 | 2-4h code change |
| 4 | **Loose pre-screen (Cat1)** | XAGUSD | 1-2 | 54.8% cont, MFE/MAE 0.91 | Same code change |

GBPUSD Cat1 dates show genuine edge (MFE/MAE > 1). Worth a batch test with the pre-screen loosened. XAGUSD is marginal — positive continuation but slightly underwater on MFE/MAE.

### Tier 3: Monitor / Deprioritize

| # | Lever | Why |
|---|-------|-----|
| 5 | Pre-London 05:00-07:00 | Modest frequency (17-22 disps/mo raw). Could work for gold/silver but limited upside. |
| 6 | Asian Open 22:00-02:00 | Below-baseline continuation for most instruments. |
| 7 | Loose pre-screen for EURUSD/NAS100 | No edge improvement over baseline. |

### Tier 4: Shelve (High edge but wrong lever type)

| # | Lever | Why |
|---|-------|-----|
| 8 | H4 OB Retest | 100% overlap with existing dates. Not a frequency multiplier. Preserve the edge data — could be useful as a quality filter within existing framework. |

---

## Implementation Roadmap

### Phase 1: Extended Sessions (Day 1)
- Add per-instrument KZ overrides to `agent_config.yaml`
- XAUUSD: add NY2 window 15:30-17:00
- GBPUSD: add London_ext window 09:30-12:00
- EURUSD: add London_ext window 09:30-12:00
- NAS100: add NY2 window 15:30-17:00
- XAGUSD: add NY2 window 15:30-17:00
- Run batch test on new windows for validation

### Phase 2: Pre-Screen Loosening (Day 2-3)
- Modify `prescreen_date()` and `prescreen_mso()` to accept Cat1
- Update PA prompt to handle transitional D1 with H4+H1 alignment
- Update Gate 1 to check H4 direction when D1 is transitional
- Batch test GBPUSD with loosened pre-screen

### Phase 3: Quality Enhancement (Future)
- Investigate H4 OB proximity as a confidence signal within existing framework
- Consider per-instrument pre-screen thresholds based on this analysis

---

## Raw Data

Full hourly breakdown, outcome data, and per-instrument details saved to:
`knowledge_base_backtest/analysis/frequency_multiplier_data_20260403.json`

Analysis script:
`knowledge_base_backtest/analysis/frequency_multiplier_analysis.py`
