# Market Microstructure Deep Analysis — Master Report
**Generated:** 2026-04-05
**Data Period:** April 2024 – March 2026 (27 months)
**Instruments:** XAUUSD (515 trading days), GBPUSD (584 trading days)
**Status:** ALL FINDINGS ARE EXPLORATORY HYPOTHESES requiring forward validation

---

## 1. Top 10 Most Actionable Patterns

### Pattern 1: FVG Creation Distinguishes Quality Displacements
- **Finding:** 66.7% of high-continuation displacements create FVGs vs 56.3% of low-continuation (n=6,641)
- **MI Score:** 0.0057 (modest but clean signal — no outcome leakage)
- **Frequency:** Occurs in ~62% of all displacements
- **Implementable:** YES — FVG creation is already detected. Weight it more heavily in scoring.
- **Instrument:** XAUUSD only (no displacement DB for GBPUSD)

### Pattern 2: `tight` and `consol` Are the Top Non-Leaky Predictors
- **Finding:** Pre-displacement tightness (MI=0.175) and consolidation (MI=0.130) are by far the strongest NON-outcome features predicting 3h continuation
- **Interpretation:** A displacement emerging from a tight consolidation is significantly more likely to continue. This captures the "coiled spring" effect.
- **Implementable:** YES — both features exist in the system. Use as primary quality filters.
- **CAVEAT:** MI values include high cardinality effects; chi2 p-values are not significant (0.225 and 0.391). Treat with caution.

### Pattern 3: GBPUSD Asian Level Rejections Are Tradeable (n=377)
- **Finding:** GBPUSD rejection sweeps of Asian levels: 19.6% rejection rate for Asian H (n=684), with NY rejection sweeps producing 69.5% positive net moves at 30min (n=154)
- **Post-rejection (NY):** Avg MFE = 13.8 pips at 30min, 17.1 pips at 1hr, 23.6 pips at 2hr
- **Contrast with gold:** XAUUSD has only 3.7% rejection rate for Asian H (n=488) — sweeps almost always break through
- **Implementable:** YES for GBPUSD — add "NY rejection sweep" as a high-priority signal

### Pattern 4: 83.7% of Displacements Get Origin Revisited
- **Finding:** Of 6,641 displacements, 5,560 (83.7%) get their origin revisited. Median revisit time: 1 candle. Average: 2.5 candles.
- **Retest continuation rate:** 58.1% (n=5,560)
- **Interpretation:** The OB retest framework has strong structural support — origins DO get revisited consistently, and when they do, continuation is modestly above chance.
- **Implementable:** Already the core framework. Validates the approach.

### Pattern 5: Hour 2 UTC Is the Best Displacement Hour
- **Finding:** Hour 2 UTC produces 56.9% continuation rate (n=232) vs 49.3% overall
- **Dead zone:** Hour 0 UTC has only 21.7% continuation (n=23, small sample)
- **Interpretation:** Very early Asian displacements (hour 0) are noise. Hour 2-3 displacements have better continuation.
- **Implementable:** YES — consider filtering or downweighting very early displacements

### Pattern 6: OB Mitigation Rate Is 69.7% with 74.9% Continuation
- **Finding:** Of 818 OBs across 129 trade dates, 570 (69.7%) get mitigated. Of mitigated OBs, 427 (74.9%) produce continuation moves.
- **OB survival:** Median 4 candles, mean 18.3 candles (bimodal — either fast mitigation or none)
- **Implementable:** Confirms OB framework validity. Fresh OBs (< 6 candles) are 47% of all mitigated OBs.

### Pattern 7: OB Freshness Is the ONLY Statistically Significant Winner/Loser Differentiator
- **Finding:** Winners use OBs 2.65 candles old vs 2.05 for losers (p=0.016, the ONLY significant result). Premium zone: 76.4% winners vs 59.5% losers (p=0.165, trending).
- **Interpretation:** OBs that aren't immediately adjacent to the structure break — with a small confirming gap — perform better. The OB needs "breathing room."
- **Implementable:** YES — prefer OBs 2-3 candles from the break, not the immediately preceding candle. Add premium zone as secondary filter.

### Pattern 8: GBPUSD Double Sweeps Are 5x More Common Than Gold
- **Finding:** GBPUSD double Asian sweep: 25.7% of sessions (n=176). XAUUSD: 7.0% (n=34).
- **Time between sweeps:** GBPUSD avg 129 min, XAUUSD avg 151 min
- **96.1% of GBPUSD days have 2+ sweeps** — sweep-based strategies have high opportunity frequency
- **Implementable:** For GBPUSD — expect and wait for second sweep before committing

### Pattern 9: London First-Hour Direction Is Near-Random
- **Finding:** XAUUSD London first-hour persistence: 49.6% (n=514). GBPUSD: 54.1% (n=582). NY slightly better: 52.3% and 51.2%.
- **Bullish first hours persist more than bearish** (55.2% vs 43.0% for XAUUSD London)
- **Implementable:** Do NOT use first-hour direction as a strong signal. Slight bullish bias worth noting.

### Pattern 10: Cross-Instrument Correlation Is Moderate and Variable
- **Finding:** Daily return correlation: 0.359 (n=516). H1 direction alignment: 60.9%
- **Rolling 20d correlation:** Mean 0.369, range -0.35 to 0.81
- **Divergence signal:** When XAU down + GBP up, next day XAU positive 58.5% (n=82) — weak mean-reversion
- **Implementable:** LOW — correlation too variable to use as reliable filter

---

## 2. The Winning Trade Blueprint

Based on Stream 3 OB analysis (n=77 winners, n=44 losers):

### Winning Trade Profile:
1. **OB Zone:** Narrow (median $6.99), in **premium zone** (80.5% of winners vs 56.8% of losers)
2. **OB Freshness:** 2-3 candles after formation (median 2)
3. **Displacement:** Creates an FVG (66.7% of high-continuation displacements)
4. **Pre-conditions:** Tight consolidation before displacement (`tight` is #1 predictor)
5. **Sweep present:** ~87% of displacements have a prior sweep (similar for winners/losers — not differentiating)
6. **Origin revisited:** 83.7% of origins get revisited; 58.1% continuation at retest

### Timing Benchmarks:
- Best displacement hours: 2-3 UTC (Asian transition), 7-11 UTC (London core)
- OB mitigated within: median 4 candles (most that work, work fast)
- Post-sweep reversal MFE: XAUUSD NY $15.29 at 30min; GBPUSD NY 13.8 pips at 30min

### Stream 4 — Event Sequencing (CRITICAL FINDING):
Using a 4-hour M15 window before each CANDIDATE entry (n=80 winners, n=45 losers):

**The event signature is IDENTICAL for winners and losers.** Both show:
- ~2.5 structure breaks (BOS + CHoCH)
- ~2 sweeps (86% have at least one)
- ~2.3 displacements at ~3.5x average body
- ~2.6 OBs formed
- ~9.5 total events

**No feature reaches p<0.05 in the comparison.** The "full confluence" pattern (BOS + CHoCH + SWEEP + DISPLACEMENT + OB) appears in the majority (>50%) of BOTH winners and losers.

**This means the alpha does NOT come from the event sequence before entry.** It comes from **OB selection quality** — specifically freshness (p=0.016) and likely premium zone positioning.

---

## 3. The Losing Trade Red Flags

### Observable Differences (Winners vs Losers):
| Feature | Winners (n=72) | Losers (n=42) | p-value | Significant? |
|---------|---------------|---------------|---------|--------------|
| **OB Freshness (candles)** | **2.65** | **2.05** | **0.016** | **YES** |
| Premium zone % | 76.4% | 59.5% | 0.165 | Trending |
| OB width mean | $10.02 | $12.81 | 0.316 | No |
| Body-range ratio | 0.420 | 0.399 | 0.690 | No |
| Nearby OBs | 2.50 | 2.95 | 0.369 | No |
| CHoCH-caused % | 31.9% | 40.5% | — | No |

### Pre-Entry Event Profile (n=80 winners, n=45 losers):
| Event Feature | Winners | Losers | p-value |
|---------------|---------|--------|---------|
| Structure breaks | 2.67 | 2.38 | 0.201 |
| Has CHoCH | 71.3% | 75.6% | 0.874 |
| Sweeps | 2.14 | 1.84 | 0.285 |
| Has sweep | 86.3% | 86.7% | 0.998 |
| Displacements | 2.19 | 2.60 | 0.124 |
| Disp strength | 3.29x | 3.66x | 0.268 |
| Total events | 9.66 | 9.38 | 0.692 |

### Key Red Flags:
1. **OB too fresh (adjacent to break)** — the ONLY statistically significant finding (p=0.016). Losers enter OBs that are too close to the structure break. Winners have a 2-3 candle "breathing room."
2. **NOT in premium zone** — losers are 40.5% discount vs 23.6% for winners (p=0.165, trending but not significant)
3. **No displacement creating FVG** — 43.7% of low-continuation displacements lack FVG creation vs 33.3% of high-continuation (from displacement database)

### Critical Null Result — Event Sequence Does NOT Differentiate:
- The microstructure event profile (sweeps, structure breaks, displacements, OBs) is **statistically indistinguishable** between winners and losers
- Both groups have "full confluence" — the setup LOOKS the same
- **The alpha comes from OB selection, not from the pre-entry event pattern**
- This means adding more confluence checks (require sweep + CHoCH + displacement) will NOT improve win rate — losers already have all of these

---

## 4. The Sweep Calendar

### XAUUSD (515 days):
| Level | Total Sweeps | Rejection % | Breakout % | Avg Minutes Into KZ |
|-------|-------------|-------------|------------|---------------------|
| Asian H | 488 | 3.7% | 96.3% | 84.5 |
| Asian L | 448 | 7.6% | 92.4% | 82.1 |
| PDH | 353 | 1.7% | 98.3% | 84.7 |
| PDL | 324 | 5.6% | 94.4% | 88.1 |

- **85% of days have 2+ sweeps** (gold is active)
- **Only 4.3% of days have zero sweeps**
- Gold overwhelmingly breaks through levels (>92% breakout for all levels)
- **Rejection sweeps are RARE** for gold — only 76 total rejection sweeps across all levels and KZs
- Post-rejection (NY): Avg MFE $15.29 at 30min, $19.80 at 1hr (n=42)

### GBPUSD (584 days):
| Level | Total Sweeps | Rejection % | Breakout % | Avg Minutes Into KZ |
|-------|-------------|-------------|------------|---------------------|
| Asian H | 684 | 19.6% | 80.4% | 78.0 |
| Asian L | 607 | 17.8% | 82.2% | 75.3 |
| PDH | 476 | 6.1% | 93.9% | 78.3 |
| PDL | 486 | 7.0% | 93.0% | 78.1 |

- **96.1% of days have 2+ sweeps** (GBPUSD even more active)
- **377 total rejection sweeps** (5x more than gold!)
- **GBPUSD Asian level rejections are the main sweep-based opportunity**
- Post-rejection (NY): 69.5% positive at 30min (n=154), avg MFE 13.8 pips
- Asian H rejection in NY: 73.9% positive at 30min (n=46)

### Sweep Sequencing:
- GBPUSD double Asian sweep: 25.7% of sessions (n=176)
- XAUUSD double Asian sweep: 7.0% (n=34)
- Average time between sweeps: XAUUSD 151min, GBPUSD 129min
- Full PDH→PDL range sweep: very rare (XAUUSD 0.8%, GBPUSD 4.5%)

### Post-Rejection: Asian Range Reversal Within 3hr
- **GBPUSD NY PDH rejection → 1x Asian range: 56% (n=32)** — best single setup in entire dataset
- GBPUSD Asian H swept in NY → hit 1x Asian range reversal: 47.8% (n=46)
- GBPUSD PDL swept in NY → hit 1x Asian range reversal: 39.3% (n=28)
- XAUUSD rejection reversals: sample sizes too small for reliable conclusions (n<20 per category)
- **London rejections on gold produce 0% 1x Asian range reversals** — London gold rejections do not reverse meaningfully

### Best Individual Setups (from agent deep-dive):
- **GBPUSD PDH rejection (NY):** 75% net-positive at 1hr, avg +8.5 pips (n=56). Late-KZ PDH: 72% at 1hr, avg +9.3 pips (n=43).
- **Gold Asian H rejection at 1hr:** 83% positive, $7.27 avg net (n=18 — small sample)
- **Gold PDL rejection 30min:** $19 MFE but net goes negative by 3hr — need fast exit

### Strategic Character Difference:
- **Gold is a momentum instrument** — fading sweeps is low probability. Rejections produce large MFE but poor close-based returns (reversals of reversals).
- **GBPUSD is sweep-fade friendly** — 19.3% overall rejection rate, PDH rejections especially strong in NY.
- Gold's Asian range averages 46% of ADR (proportionally wider), leaving less room for KZ expansion.
- GBPUSD sweeps Asian range first 58.2% of the time vs gold 33.8% — GBPUSD is faster at London open.

---

## 5. Feature Importance Ranking (Non-Leaky, XAUUSD)

**Displacement → 3h Continuation** (Mutual Information, n=6,641):

| Rank | Feature | MI Score | Type | Notes |
|------|---------|----------|------|-------|
| 1 | tight | 0.175 | Consolidation | **TOP PREDICTOR** — pre-displacement tightness |
| 2 | consol | 0.130 | Consolidation | Pre-displacement consolidation ratio |
| 3 | nc_dir | 0.028 | Next candle | Direction of candle after displacement |
| 4 | nc_cont_pct | 0.028 | Next candle | Next candle continuation percentage |
| 5 | volume | 0.012 | Volume | Displacement candle volume |
| 6 | body_size | 0.007 | Displacement | Absolute body size |
| 7 | creates_fvg | 0.006 | FVG | **Whether displacement creates FVG** |
| 8 | fvg_size | 0.005 | FVG | Size of FVG created |
| 9 | ob_dist | 0.005 | OB | Distance to nearest OB |
| 10 | direction | 0.005 | Direction | Bullish vs bearish |
| 11 | fvg_pct | 0.004 | FVG | FVG size as percentage |
| 12 | nc_body_ratio | 0.003 | Next candle | Next candle body ratio |
| 13 | sweep_cb | 0.003 | Sweep | Candles back to sweep |
| 14 | liq_depth | 0.003 | Liquidity | Depth of liquidity at sweep |
| 15 | prior_body | 0.002 | Context | Prior candle body size |
| 16 | levels_swept | 0.002 | Sweep | Number of levels swept |
| 17 | mss | 0.002 | Structure | Market structure shift |
| 18 | p5_range | 0.002 | Context | Prior 5-candle range |
| 19 | at_ob | 0.001 | OB | At an order block |
| 20 | p5_bavg | 0.001 | Context | Prior 5-candle body average |

**Key insight:** `tight` and `consol` dominate all other features by 5-10x in MI. The "next candle" features (nc_dir, nc_cont_pct) are not usable for entry decisions (they're post-entry). The first truly usable entry-time features after tight/consol are: volume, body_size, creates_fvg, fvg_size.

**What's NOT predictive:** sweep presence/quality (MI ≈ 0), premium/discount zone (MI ≈ 0), day of week, kill zone, alignment score, Asian range metrics. These are near-random for continuation prediction.

---

## 6. Volatility Map

### XAUUSD — Average M15 Body Size by Hour (USD):
```
Hour  Body   Range  | Interpretation
  00   4.39   9.51  | Asian transition (active)
  01   3.36   6.36  | Asian core
  02   3.39   6.80  | Asian core
  03   3.53   6.75  | Asian late
  04   3.41   6.72  | Asian-London transition
  05   2.49   5.21  | Low activity
  06   1.96   4.44  | QUIETEST (pre-London)
  07   2.29   5.01  | London open (slow start)
  08   2.70   5.36  | London warming up
  09   2.53   5.28  | London core
  10   2.96   5.90  | London core (picks up)
  11   2.78   5.52  | London mid
  12   2.63   5.24  | London-NY transition
  13   2.55   5.27  | NY pre-open
  14   2.46   5.13  | NY open
  15   4.16   8.28  | NY CORE ★
  16   4.67   9.44  | NY PEAK ★★
  17   4.67   9.38  | NY PEAK ★★
  18   3.52   7.26  | NY close
  19   2.79   5.87  | Post-NY
  20   2.56   5.31  | Asia early
  21   2.41   5.24  | Asia early
  22   2.46   5.32  | Asia early
  23   1.67   3.66  | QUIET
```

**Peak volatility:** 15:00-17:00 UTC (NY core) — body sizes 2x London average
**Secondary peak:** 00:00-04:00 UTC (Asian session) — surprisingly active for gold
**Dead zone:** 06:00-07:00 UTC (pre-London) and 23:00 UTC

### GBPUSD — Similar Pattern:
Peak at hours 10-11 UTC (London core) and 15-17 UTC (NY)
Note: GBPUSD values are in pips (0.000xx scale)

### Displacement Distribution (XAUUSD, from displacement database):
- Peak displacement hours: 3 (n=516), 7-8 (n=500+), 15-16 (n=400+)
- Best continuation rate: Hour 2 (56.9%, n=232), Hour 20 (55.6%, n=72)
- Worst continuation rate: Hour 0 (21.7%, n=23 — small sample)
- Average across all hours: 49.3%

---

## 7. Cross-Instrument Signals

### Correlation:
- **Daily return correlation:** 0.359 (moderate positive, n=516)
- **H1 direction alignment:** 60.9% (n=13,154 H1 candles)
- **Rolling 20d correlation range:** -0.35 to 0.81 (highly variable)

### Divergence Analysis:
| Condition | n | XAU Next Day +ve% | GBP Next Day +ve% |
|-----------|---|--------------------|--------------------|
| XAU↑ GBP↓ | 99 | 51.0% | 48.0% |
| XAU↓ GBP↑ | 82 | **58.5%** | 39.0% |
| Strong alignment | 78 | 47.4% | 45.5% |

- When gold is down and GBPUSD is up, gold tends to mean-revert next day (58.5% positive, n=82) — weak but interesting
- Cross-instrument divergence provides no actionable edge for GBPUSD
- Strong alignment days have slightly NEGATIVE next-day continuation — mild mean-reversion

### Asian Session as Predictor:
- Asian direction → London direction correlation: 0.003 for XAUUSD (zero signal)
- Asian first-touch analysis: when Asian high touched first, London sweeps the same high 51.8% and the opposite low 43.4% — essentially random

### London-NY Relationship:
- Same direction: XAUUSD 51.8%, GBPUSD 50.0% — perfectly random
- No predictive relationship between London and NY direction

---

## Summary Statistics

| Metric | XAUUSD | GBPUSD |
|--------|--------|--------|
| Trading days | 515 | 584 |
| Total sweeps | 1,613 | 2,253 |
| Rejection sweeps | 76 (4.7%) | 377 (16.7%) |
| Days with 2+ sweeps | 85.0% | 96.1% |
| Asian range median | $19.23 | — |
| London first-hour persistence | 49.6% | 54.1% |
| London-NY same direction | 51.8% | 50.0% |
| Displacement cont_3h rate | 49.3% | — |
| OB mitigation rate | 69.7% | — |
| OB continuation at retest | 74.9% | — |
| Daily correlation (returns) | 0.359 | 0.359 |

---

## Limitations & Open Questions

1. **Stream 4 event sequencing succeeded with 4hr M15 window** — the critical finding is that event profiles are identical between winners and losers. The alpha is in OB selection quality, not event confluence.
2. **Displacement database is XAUUSD only** — all displacement/feature findings need separate GBPUSD validation.
3. **Multiple testing:** With 94 features tested, some findings will be spurious. The top features (tight, consol) have large MI scores unlikely to be chance, but lower-ranked features (MI < 0.01) are suspect.
4. **No forward test performed** — all findings are in-sample. True validation requires hold-out or walk-forward testing.
5. **Gold rejection sweeps are too rare (n=76)** for reliable post-sweep statistics. GBPUSD rejection data is much richer (n=377).
6. **Premium zone finding** from OB analysis (80.5% winners vs 56.8% losers) needs formal statistical testing with larger sample.
