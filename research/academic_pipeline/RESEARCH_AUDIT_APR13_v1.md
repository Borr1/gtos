# Research Pipeline Audit — April 13, 2026

**Auditor:** Strategic Research Advisor
**Date:** 2026-04-13 17:30 UTC
**Basis:** research_execution_plan_113q.md + handoffs 09-15 + all T-series results
**Current system:** T7 C-gate + Sonnet 4.6 effort=max + session memory disabled

---

## EXECUTIVE SUMMARY

The research pipeline has made substantial progress since April 11. The core finding is that **the AI's discriminative signal comes entirely from the C-gate** (H1 directional bias + M15 non-opposition + direction match). Q-scores, zone proximity checks, and all macro inputs have zero predictive power (r=-0.06).

**Key statistics:**
- 113 questions in original plan
- ~35 questions addressed (literature search, testing, or implementation)
- ~12 actionable findings deployed or validated
- ~78 questions untouched (mostly Waves 3-5: edge discovery)
- 3 major paths permanently closed: multi-TF expansion, macro overlay, accuracy optimization

---

## SYSTEM EVOLUTION TIMELINE

Understanding this timeline is critical for assessing which tests deserve retesting.

| Phase | Dates | System State | Key Changes |
|-------|-------|--------------|-------------|
| 1 | Apr 6-8 | Sonnet 4, old prompts, broken gates | D1 prescreen blocking 60%, spread gate blocking 100%, inverted TP not caught |
| 2 | Apr 9-11 | Bug fixes + research begins | Deterministic bias injection (+77% unblocked), inverted TP auto-correction |
| 3 | Apr 12 | Model upgrade + prompt re-engineering | Sonnet 4.6 max, P2A v1 scored prompt, session memory disabled |
| 4 | Apr 13 | **T7 deployed (CURRENT)** | Pure C-gate, zero zone info in prompt, Q-scores removed |

**Tests run on Phase 1-2 system may produce different results on Phase 4 system.**

---

## RESEARCH STATUS BY WAVE

### WAVE 1 — MULTIPLIERS (19 questions)
*Impact: Affects every trade. Deploy immediately if positive.*

| ID | Question | Status | Finding | Retest? |
|----|----------|--------|---------|---------|
| Q-4.1 | Confirmation vs anticipation entry | T1 INCONCLUSIVE | n=14/quartile underpowered | NO — wait for batch sim data |
| Q-4.2 | Market vs limit order cost | NOT TESTED | — | LOW — infrastructure, not edge |
| Q-4.3 | Time-of-candle execution | T1 INCONCLUSIVE | No signal at n=121 | NO — dead end likely |
| Q-4.4 | Retracement depth vs outcome | T1 INCONCLUSIVE | Batch enters ABOVE OBs | NO — data contradicts premise |
| Q-1.1 | MI: features → returns | L1 SEARCHED | MI audit recommended | YES — $0 on batch data |
| Q-1.2 | Tick volume info content | L1 KILLED | Already absent, confirmed noise | NO |
| Q-1.3 | Spread dynamics | L1 SEARCHED | Spread surprise feature proposed | DEFER — needs Level 2 data |
| Q-1.4 | Multi-TF combination | KILLED | M15 at 49.9%, H1 specific | NO — path closed |
| Q-1.5 | Optimal feature count | L1 SEARCHED | n/p > 10 rule | NO — informational |
| Q-1.6 | Gold vs FX autocorrelation | VALIDATED | Gold xi=0.35 vs FX 0.16-0.22 | NO — confirmed different |
| Q-1.7 | Order flow from OHLCV | I1 PROMPT WRITTEN | CLV/BVC implementation | CHECK — verify if built |
| Q-3.1 | Optimal signal combination | T2a ANSWERED | LLM = expensive feature extractor | NO |
| Q-3.2 | Narrative fitting bias | T2b Exp4 | SMC framing neutral | NO |
| Q-3.3 | Session memory mechanism | T2b VALIDATED | 55% suppression (p=0.007) | NO — disabled in prod |
| Q-3.4 | Confidence calibration | T2a KILLED | 98% get confidence=80 | NO — dead feature |
| Q-3.5 | Sequential evaluation bias | NOT TESTED | — | NO — session memory disabled |
| Q-3.6 | Ensemble / multiple runs | T2b Exp5 TESTED | 86% agreement, 81.8% WR | MAYBE — worth $15 on T7 |
| Q-3.7 | LLM vs logistic regression | T2a ANSWERED | Outcomes random in CANDIDATE | NO — accuracy closed |
| Q-9.1 | LLM performance on financial tasks | L2 SEARCHED | GTOS in uncharted territory | NO — informational |

**Wave 1 Summary:** 7 killed, 4 validated, 3 inconclusive (need n), 3 deferred, 2 need verification

---

### WAVE 2 — EXISTING EDGE OPTIMIZATION (26 questions)
*Impact: Makes OB retest edge sharper or more frequent.*

| ID | Question | Status | Finding | Retest? |
|----|----------|--------|---------|---------|
| Q-0.1 | Daily candle predict trending | NOT TESTED | — | LOW — D1 prescreen removed |
| Q-0.3 | Regime detection (HMM) | NOT TESTED | — | LOW |
| Q-0.6 | GVZ implied vol | NOT TESTED | — | LOW |
| Q-0.7 | Calendar effects | NOT TESTED | — | LOW |
| Q-2.1 | Optimal swing detection | NOT TESTED | — | MEDIUM — infrastructure |
| Q-2.2 | **Zone age** | **VALIDATED** | Touch-1=72.7%, T2+=31.5% | NO — deployed |
| Q-2.3 | S/R mechanisms | NOT TESTED | — | LOW |
| Q-2.4 | FVG gap fill rates | T3 TESTED | Not significant | NO |
| Q-2.5 | Order book dynamics | NOT TESTABLE | Need Level 2 | NO |
| Q-2.6 | Displacement magnitude | T3 KILLED | REVERSED (weaker = better) | NO |
| Q-2.7 | Premium/discount zone | NOT TESTED | — | LOW |
| Q-2.8 | Fractal structural breaks | NOT TESTED | — | LOW |
| Q-2.9 | Liquidity sweep reversal | VALIDATED | This IS the edge mechanism | NO — core assumption |
| Q-5.1 | **GARCH-EVT SL** | **KILLED** | 0/11 survive Bonferroni | NO |
| Q-5.2 | MAE distribution | L4 FOUNDATION | GPD xi=0.476 (heavy-tailed) | NO — informational |
| Q-5.3 | SL vs stop clustering | L4 SEARCHED | — | LOW |
| Q-5.4 | ATR vs quantile SL | L4 SEARCHED | — | MEDIUM |
| Q-5.5 | SL/TP/Kelly interaction | L4 SEARCHED | — | $0 ANALYSIS |
| Q-6.1 | **Trailing stop OU** | **NO CHANGE** | OU can't rank GTOS exits | NO |
| Q-6.2 | Optimal partial close | L4 + FTMO MC | **Variant C shadow logger needed** | YES — build logger |
| Q-6.5 | Speed to MFE | L4 FOUNDATION | — | $0 ANALYSIS on batch |
| Q-6.6 | Session-close strategy | L4 SEARCHED | — | LOW |
| Q-6.7 | Institutional exit principles | L4 SEARCHED | — | LOW |
| Q-6.8 | Dynamic TP based on vol | L4 FOUNDATION | MFE-vol rho=-0.53 | $0 ANALYSIS |
| Q-8.1 | **Shiryaev-Roberts** | **DEPLOYED** | EdgeMonitor live | NO |
| Q-8.2 | Alpha decay half-life | L4 FOUNDATION | p=0.40 (NOT significant) | NO — can't confirm decay |
| Q-8.3 | Crowding measurement | L4 SEARCHED | — | LOW |
| Q-8.4 | Edge lifetime estimation | L4 SEARCHED | — | INFORMATIONAL |
| Q-9.2 | Black-box drift detection | L4 SEARCHED | D1-D8 inventory built | YES — build infra |
| Q-9.3 | Prompt framing effects | T3/T5-T8 TESTED | C-gate is the signal | NO — superseded |
| Q-9.4 | LLM ensemble methods | T2b Exp5 | 3-run at 86% agreement | MAYBE — $15 on T7 |

**Wave 2 Summary:** 5 validated/deployed, 6 killed, 8 need testing, 7 low priority

---

### WAVE 3 — EDGE DISCOVERY (42 questions)
*Impact: Find entirely new tradeable setups.*

| Cluster | Questions | Status | Notes |
|---------|-----------|--------|-------|
| Q-13.x (Zone types) | 8 | L3 PROMPT READY | L3 execution unclear |
| Q-14.x (Non-zone mechanisms) | 11 | NOT STARTED | Highest variance |
| Q-15.x (Math/stat anomalies) | 7 | NOT STARTED | High implementation cost |
| Q-16.x (Adversarial/game theory) | 6 | NOT STARTED | |

**Wave 3 Summary:** ~0% complete. 42 questions untouched. This is where frequency gains hide.

---

### WAVE 4 — RISK & PORTFOLIO (14 questions)
*Impact: Protect capital, optimize allocation.*

| ID | Question | Status | Finding | Retest? |
|----|----------|--------|---------|---------|
| Q-7.1 | **Kelly sizing** | **VALIDATED** | f*=4%, current 1% | NO — math-based |
| Q-7.2 | Optimal DD response | L4 SEARCHED | H29 deployed (8% threshold) | NO |
| Q-7.3 | Max DD distribution | L4 FOUNDATION | — | $0 ANALYSIS |
| Q-7.4 | Correlated asset allocation | NOT TESTED | — | MEDIUM |
| Q-7.5 | Risk of ruin with fat tails | L4 FOUNDATION | — | $0 ANALYSIS |
| Q-7.6 | FTMO-specific optimal | L4 FOUNDATION | f=1.5% optimal | $0 — ACTIONABLE |
| Q-10.1 | DXY-gold lead-lag | KILLED (macro) | 3 null results | NO |
| Q-10.2 | Macro announcements | KILLED (macro) | — | NO |
| Q-10.3 | Gold safe-haven effect | NOT TESTED | — | LOW |
| Q-10.4 | Real rates gold filter | KILLED | p=0.74 | NO |
| Q-11.1 | Heterogeneous allocation | NOT TESTED | — | AFTER batch sim |
| Q-11.2 | Cross-currency signals | NOT TESTED | — | AFTER batch sim |
| Q-11.3 | Dynamic instrument selection | NOT TESTED | — | AFTER batch sim |
| Q-11.4 | Intraday correlation stability | NOT TESTED | — | LOW |

**Wave 4 Summary:** 3 validated, 3 killed, 8 need testing (most require multi-instrument data)

---

### WAVE 5 — STRATEGIC (12 questions)
*Impact: Long-term understanding.*

All 12 questions: NOT STARTED. Low priority — informational only.

---

## TESTS THAT WARRANT RETESTING ON CURRENT SYSTEM

The current system (T7 + Sonnet 4.6 max + no session memory) differs fundamentally from the system used for most tests. These items deserve retesting:

### HIGH PRIORITY (clear benefit, low cost)

| Item | Original Result | Why Retest | Cost | Expected Outcome |
|------|-----------------|------------|------|------------------|
| **T2b Exp5: 3-run consistency** | 86% agreement, 81.8% WR for majority-CANDIDATE | Never tested on T7 prompt + Sonnet 4.6 max | ~$15 | May improve WR calibration |
| **I1: CLV/BVC/session ATR** | Prompt written, execution undocumented | Features may improve T7 decisions | $0 code | Check if implemented |
| **D1-D8: Drift monitoring** | Inventory built, not implemented | Production safety infrastructure | $0 code | Build borderline canaries |

### MEDIUM PRIORITY (depends on batch simulation results)

| Item | Why Retest | Prerequisite |
|------|------------|--------------|
| T1 Entry engineering | n=14/quartile was underpowered | Need n>50/quartile from 5-instrument sim |
| Q-11.1-11.3 Cross-instrument | Need multi-instrument data | Batch sim for US30/USDJPY/GBPJPY/GBPUSD |
| L2 rejection analysis | 66% of AI CANDIDATEs rejected | Understand why simulation differs from live |

### NOT WORTH RETESTING

| Item | Why NOT Retest |
|------|----------------|
| T2b Exp1-4 (session memory, CoT, SMC framing) | Session memory disabled, T7 prompt supersedes |
| T5-T6 prompt variants | T7 already deployed, incorporates learnings |
| Multi-TF expansion | M15 at 49.9% is structural, not system-dependent |
| Macro overlay (DXY, COT, real rates) | 3 null results, mechanism is structural |
| Q-scores optimization | r=-0.06, zero predictive power |

---

## PATHS PERMANENTLY CLOSED

1. **Accuracy optimization within CANDIDATE pool** — T2a proved AUC~0.5, outcomes are unpredictable from features
2. **Multi-TF expansion** — M15 OB continuation = 49.9% (coin flip), H1 is specific and necessary
3. **Macro overlay** — COT, DXY, real rates all null (p>0.40)
4. **Q-score discriminative power** — r=-0.06 correlation with wins
5. **Session memory as regime inference** — 55% CR suppression outweighs any benefit

---

## $0 ANALYSES TO RUN ON EXISTING DATA

These can be done immediately without API cost:

| Analysis | Data Source | Question |
|----------|-------------|----------|
| MI audit (Q-1.1) | Batch decision JSONs | Which features carry signal, which are noise? |
| SL/TP/Kelly interaction (Q-5.5) | Trade index | Formal framework for unified optimization |
| Speed to MFE (Q-6.5) | Trade MAE/MFE data | Does fast 1R → higher P(2R)? |
| Dynamic TP (Q-6.8) | Vol-partitioned trades | Should TP expand in high-vol? |
| Max DD distribution (Q-7.3) | Monte Carlo | Exact probability of ruin at current sizing |
| FTMO optimal (Q-7.6) | Monte Carlo | Confirm 1.5% vs 1% risk |
| L2 rejection breakdown | all_results_jan_mar11.json | Which L2 check rejects most? |
| Monthly WR decay | all_results_jan_mar11.json | Jan → Feb → Mar curve |

---

## BATCH SIMULATION ANALYSIS TEMPLATE

When the XAUUSD remainder (currently at 298/660) and other instruments complete:

### Per-Instrument Analysis
1. CR (raw and live), WR, Total R, Exp/trade
2. Monthly breakdown (WR decay curve)
3. L2 rejection breakdown by check type
4. Entry position within OB zone (T1 re-analysis)
5. Trade distribution by kill zone and direction

### Cross-Instrument Analysis
1. Edge consistency (WR variance across instruments)
2. Correlation of outcomes (are losses clustered by date?)
3. L2 rejection patterns (same checks failing everywhere?)
4. Frequency distribution (which instruments produce most trades?)

### Statistical Tests
1. Instrument WR vs batch WR (Wilson CI overlap)
2. Simulation WR vs live WR (binomial test)
3. Monthly WR trend (logistic regression)

---

## IMMEDIATE PRIORITIES (while simulation runs)

### Can do now ($0)
1. **Verify I1 implementation** — Did CLV/BVC/session ATR get added to MSO?
2. **MI audit on batch data** — Which features have MI > 0 with outcomes?
3. **Build Variant C shadow logger** — 33% partial close at 1.0R, shadow-only

### After simulation completes (~1 hour)
4. Analyze XAUUSD Jan-Apr combined results
5. Investigate L2 rejection rate discrepancy (simulation 66% vs live ???)
6. Design post-hoc entry engineering analysis (if n > 50/quartile)

### Next research session
7. L3 edge optimization lit search (if not already done)
8. D1-D8 drift monitoring infrastructure
9. T2b Exp5 on T7 system ($15)

---

## OPEN QUESTIONS FOR CEO

1. **L2 rejection rate:** Simulation shows 66% of AI CANDIDATEs rejected by L2 (mostly `entry_in_ob`). Live system is producing trades. Is L2 calibrated differently in production?

2. **Batch simulation budget:** After XAUUSD remainder (~$8), do you want to run US30/USDJPY/GBPJPY/GBPUSD (~$113)?

3. **3-run consistency test:** Worth $15 to test T2b Exp5 on the T7 prompt?

4. **Variant C shadow logger:** Should I build it now (code task, no API cost)?

---

*Audit complete. Total research items: 113 questions + T1-T8 tests + L1-L4 searches + I1 implementation + D1-D8 infrastructure. Approximately 35% addressed, 65% untouched (mostly Wave 3-5).*
