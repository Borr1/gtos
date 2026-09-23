# KB: Edge Mechanisms & Risks — What the Edge Is, Why It Works, What Could Kill It

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Final Synthesis  
**Sources:** 6 research sessions + 1 Claude Code empirical analysis + 1 red team review  
**Purpose:** Honest assessment of edge mechanisms, alternative explanations, AI-specific risks, and decay monitoring. Searchable by `project_knowledge_search`.

---

## 1. The Statistical Claim — What We Know For Certain

### 1.1 The Edge Exists

The system produces win rates significantly above breakeven across 4 instruments independently, using the same prompt architecture. Gold (XAUUSD) at 129 trades shows p = 3.42e-08 after the most aggressive Bonferroni correction (30 tests). This is the hardest number in the project. The edge EXISTS. A skeptic cannot credibly argue otherwise. [HIGH confidence]

### 1.2 The Underlying Pattern Is Real

H1 order block (OB) continuation — the tendency of price to continue in the impulse direction after revisiting the last opposing candle zone before a structural break — runs at approximately 70% across 13 instruments mechanically. This is 19pp above a shuffled baseline of 51%. Shuffling destroys temporal structure; the 19pp delta proves temporal structure drives the effect. The pattern is universal (appears across gold, forex, indices) and robust (consistent across instruments with varying SMC retail participation). [HIGH confidence for the existence of the pattern; MEDIUM for the precise 19pp delta — the Claude Code synthetic replication using simplified OB detection could NOT reproduce it, meaning the delta depends on the full MSO-based detection, not on a simple candle rule]

### 1.3 The AI Adds Real Discrimination

The mechanical 70% OB continuation rate is the base. The AI pre-screen kills ~51% of days, and the AI evaluation accepts ~12% of KZ-retested OBs. The resulting 62% WR at better R-multiples (avg winner 1.8R vs avg loser 1.0R) demonstrates the AI is adding selectivity value. The Deflated Sharpe Ratio check (observed SR 0.232 vs null expected max 0.158 with N=5) suggests this value is real, though the margin is thin. [MEDIUM-HIGH confidence]

### 1.4 What We Are Less Certain About

- **Exact expectancy magnitude:** The expectancy p-value (0.046) does NOT survive Bonferroni correction. We know the system is profitable; we are less certain about HOW profitable per trade.
- **GBPJPY's edge:** Wilson CI lower bound exceeds breakeven by only 0.5pp. Fails family-wise correction. This instrument could be a false positive. [LOW confidence for GBPJPY specifically]
- **SHORT trade edge:** Only 3 validated SHORT wins in the batch — far below the 21 needed for directional validation. The system's edge is unproven in bearish conditions. [LOW confidence]

---

## 2. The Canonical Mechanism — Stop-Cascade Mean-Reversion

### 2.1 The Best-Supported Explanation

Multiple research sessions converged independently on this framing, which is also the most consistent with academic microstructure evidence:

**Order blocks form when stop-loss cascades create displacement.** When price approaches a level where stop-losses cluster (below a swing low or above a swing high), triggering those stops creates a one-directional flow surge. Market makers who sold against those stops hedge, creating further directional pressure. This cascade produces the displacement candle (the BOS/CHoCH). The "order block" zone before the displacement is the zone where the market was balanced BEFORE the cascade triggered — it represents the last equilibrium.

**Retests work because price mean-reverts to pre-cascade fair value.** After the cascade, the market is temporarily overextended. The zone before displacement represents "fair value" pre-disruption. When price returns, several forces create the reaction: (a) orders resting from participants who wanted to buy/sell at that level before the cascade disrupted them, (b) algorithmic strategies that target mean-reversion to pre-event levels, (c) dealers who observed the original flow and have standing interest. The ~70% continuation rate reflects the probability that the cascade was genuine (directionally resolved) rather than a false break.

**The key quality indicator — FVG in impulse — fits this mechanism.** A Fair Value Gap (three-candle gap where the middle candle's body extends beyond surrounding candles' ranges) in the impulse leg signals a STRONG cascade — one with enough force to create a price gap. Stronger cascades produce stronger mean-reversion pull. FVG-in-impulse replicated across 6 instruments at +7pp to +20pp above non-FVG OBs. The probability of 6/6 showing positive delta by chance is 1.56%. This survives Bonferroni. [HIGH confidence for the signal; MEDIUM for the specific mechanism]

### 2.2 What This Mechanism Is NOT

This is **fundamentally different from the SMC/ICT narrative** of "smart money deliberately accumulating orders in a range and then displacing to lock in positions." The evidence contradicts that narrative:

- Institutions use TWAP/VWAP/iceberg algorithms specifically designed to be INVISIBLE and to avoid creating displacement. Banks don't WANT to displace — it increases execution cost.
- Central bank gold purchases are entirely OTC, bilateral, and private. They do not appear on exchange order books or on H1 charts.
- The impulse_atr_multiple variable (measuring OB candle body size relative to ATR — a proxy for "how large were the institutional orders?") is NULL (p=0.97). If the SMC narrative were correct, larger OB bodies should indicate larger institutional positions and predict higher continuation. They don't.

**The system should NOT be described as "reading institutional footprints."** It should be described as: **exploiting the statistical tendency of price to mean-revert to pre-cascade equilibrium after stop-loss-triggered displacement events, in the direction of the higher-timeframe trend.** This framing is more mechanistically accurate, less dependent on unverifiable claims, and consistent with all validated findings. [HIGH confidence for this reframe]

### 2.3 Academic Support

The mechanism maps directly onto established academic findings:
- **Osler (2000, 2003, 2005):** Real institutional stop-loss order data showing order clustering at specific levels creates predictable price reactions and cascades. Published in *Journal of Finance* (top-3 journal) and NY Fed Economic Policy Review.
- **Cont, Kukanov & Stoikov (2014):** Order flow imbalance at specific price levels has persistent, linear predictive power for subsequent price changes. Published in *Journal of Financial Econometrics*.
- **Moskowitz, Ooi & Pedersen (2012):** Gold futures exhibit significant time series momentum at 1-12 month horizons. Speculators profit from this momentum at hedgers' expense. Published in *Journal of Financial Economics* (top-3).
- **Caminschi & Heaney (2014):** Institutional information leakage is detectable in gold public market data — informed participants' activity leaves measurable footprints. Published in *Journal of Futures Markets*.

No academic paper uses the term "order block" or directly tests the H1 OB retest hypothesis. Our backtesting results are novel. This is both an opportunity (no known competition from published strategies) and a risk (no independent academic validation). [HIGH confidence for the individual academic findings; MEDIUM for their specific application to our H1 OB strategy]

---

## 3. Alternative Explanations — Ranked by Plausibility

### 3.1 Simple Momentum / Trend-Following (CONCERNING — Untested)

**The argument:** OB continuation is momentum with extra steps. Strong moves (BOS/CHoCH) continue. The pullback to the OB zone is irrelevant — what matters is buying a pullback in a strong trend. The OB zone is a convenient entry anchor, not a causal zone.

**Why this is the strongest alternative:** Short-term momentum is one of the most robustly documented phenomena in financial markets. Trend-following has a 200-year track record. The CTA industry is built on it. If the system is just a well-engineered pullback-in-trend strategy wearing an SMC costume, that's fine for P&L — but it means the OB identification logic and AI discrimination layer may be unnecessary complexity.

**Status: NOT YET TESTED.** The "dumb momentum baseline" — entering on any pullback ≥80% of an impulse after any BOS, with identical SL/TP, no AI, no OB zone identification — has not been formally benchmarked against the full system. This is the single most important unexecuted test in the project. It costs $0 (existing data) and could reveal whether the OB zone adds value over generic trend entry. [UNRESOLVED — highest priority test]

**Partial evidence that the AI adds value:** The pre-screen kills ~51% of days and the AI selects ~12% of retested OBs. If a simple pullback rule were equally good, you wouldn't need either filter. The AI's selectivity significantly outperforms the mechanical 70% base (at better R-multiples). But this hasn't been formally compared to a generic pullback baseline.

### 3.2 Tautological with Trend-Following (CONCERNING)

**The argument:** OBs are, by definition, identified from structural breaks. A structural break means a strong directional move already happened. Saying "the last candle before a strong move, when retested, sees continuation" is tautological with "strong trends continue after pullbacks." This is survivorship bias in OB selection — you only see OBs that preceded successful structural breaks, because that's how you define them.

**Why this matters:** This is conceptually the same as 3.1 but framed differently. The test is also the same: does the OB zone add predictive value over generic trend-following pullback entries?

**Counter-evidence:** The shuffle test delta (19pp) proves temporal structure matters — shuffling destroys the pattern. But the shuffle test cannot distinguish "momentum matters" from "momentum AND the specific zone matters." Both would produce the same delta. [UNRESOLVED]

### 3.3 Volatility Clustering / GARCH Effects (WEAK — Refuted)

**The argument:** The impulse creating an OB signals a high-volatility regime. High-vol regimes persist (GARCH effects). The continuation is about regime persistence, not the zone.

**Status: REFUTED.** All regime tests returned p > 0.05 (volatility p=0.80, trend p=0.18, range p=0.67). OB continuation does NOT vary meaningfully with volatility regime. [HIGH confidence — clean null result]

### 3.4 Self-Fulfilling Prophecy (WEAK — Refuted)

**The argument:** Enough traders watch OB zones that their collective orders create the continuation.

**Status: REFUTED by cross-instrument evidence.** The mechanical screening found 70-74% continuation across all 13 instruments, including NZDUSD, USDCAD, EURJPY — instruments where SMC retail participation is minimal. If this were self-fulfilling, you'd expect higher continuation on popular instruments and lower on obscure ones. No such gradient exists. The pattern is universal. [HIGH confidence]

---

## 4. AI-Specific Risks

### 4.1 Prompt Narrative Fitting (CONCERNING — Cheap to Test)

The system prompt is saturated with SMC terminology — "order block," "displacement," "fair value gap," "institutional flow," "smart money." Claude has been trained on massive amounts of SMC/ICT content from the web. When the prompt says "there is a bullish OB in the discount zone with strong displacement and FVG creation," Claude may activate a pattern-match on the NARRATIVE frame rather than the NUMERICAL data.

Research confirms this risk: the "Can LLMs Trade?" paper (arXiv, April 2025) found that LLM trading behavior is highly sensitive to prompt framing — they faithfully follow directions regardless of profit implications. The FINSABER framework (arXiv, 2025/2026) found previously reported LLM financial advantages deteriorated significantly under broader testing.

**The prompt-neutral test** would directly address this: take 20-30 CANDIDATE evaluations, re-run with neutral terminology (e.g., "order block" → "price zone," "displacement" → "strong candle move," "institutional flow" → "price momentum"). If WR changes by >10pp, the AI is fitting to narrative, not data. Cost: ~$5-10 for 30 re-evaluations. **This test has NOT been run and should be executed within the first week of live trading.** [CONCERNING — cheap to test, potentially reveals a fundamental flaw]

### 4.2 Non-Determinism

Claude's outputs are non-deterministic. The same MSO fed to the same prompt can produce CANDIDATE on one run and NO_TRADE on another. This creates inherent noise in the system. The batch test captures the average tendency, but individual trades are subject to randomness in the AI's evaluation. This is not fixable — it is an intrinsic property of LLM-based systems. The practical mitigation is sufficient sample size (the batch at n=129 captures the average accurately even if individual decisions vary). [MEDIUM confidence — known issue, manageable but not eliminable]

### 4.3 Right-for-Wrong-Reasons Risk

If the edge is momentum but the team believes it's "institutional order flow," the practical consequences are:

1. **Wrong decay monitoring:** Watching "are institutions still creating OBs?" is the wrong signal. The right signal is: "is short-term momentum in gold still exhibiting positive autocorrelation at the H1 horizon?" Momentum can decay from increased algorithmic competition, regime change, or structural market changes — none of which affect "order block" statistics directly.

2. **Wrong expansion criteria:** Believing "OBs work because of institutional flow everywhere" might lead to expanding to instruments where the underlying momentum structure is different. The universal 70% rate suggests this is less risky, but AI performance already varies dramatically (75.8% USDJPY vs. instruments that were killed).

3. **Overengineering risk:** If the mechanism is simple momentum, the FVG overlay, session memory, knowledge base context, and multi-timeframe alignment may be either (a) genuinely helpful filters on top of momentum, or (b) overfitting noise. System complexity becomes a liability if the core mechanism is simple.

**Mitigation:** Monitor H1 autocorrelation alongside OB-specific statistics. If autocorrelation decays, expect edge decay. [CONCERNING]

---

## 5. Edge Decay — What It Would Look Like and How to Detect It

### 5.1 The 9pp Quarterly Decay Signal

The batch data shows quarterly WR progression: 73.2% → 71.4% → 63.6% → 59.4%. This is a clear downtrend. The first-half vs second-half split (67.2% vs 58.5%) has p=0.307 — not statistically significant at current sample sizes. Three possible explanations:

1. **Genuine edge decay:** Algorithmic competition is arbitraging away the H1 structural pattern. Academic research shows algorithmic trading has reduced return autocorrelation in FX markets (Chaboud et al.). If algo traders are faster at exploiting OB retests, the edge narrows.
2. **Regime change:** The gold macro environment shifted during the batch period (rate expectations, geopolitical events, central bank behavior), and the second half captured a less favorable regime.
3. **Sampling noise:** 64-65 trades per half is insufficient to confirm a 9pp difference at conventional significance levels.

**Detection timeline:** 307 trades needed to confirm a 7pp WR drop at 80% power. At portfolio level (~14.5/month), this takes ~21 months. At gold-only (4.5/month), ~68 months. **This is too slow for practical use** — which is why SPRT, CUSUM, and autocorrelation monitoring are essential for early warning.

**Forward monitoring:** Plot the quarterly WR on a dashboard. Extrapolating linearly, the system approaches breakeven WR within 2-3 more quarters. Even if this extrapolation is wrong, the trend warrants active tracking. [MEDIUM confidence — the trend is real but the cause and permanence are unknown]

### 5.2 Specific Decay Signatures

| Signature | What It Means | How to Detect |
|---|---|---|
| OB continuation rate dropping below 65% | Underlying pattern weakening | Quarterly mechanical screening on new data |
| H1 autocorrelation trending toward zero | Momentum at H1 scale decaying | Rolling 20-period H1 return autocorrelation |
| Winning R-multiples shrinking | Price reaching TPs less often; trends shorter | Track avg winner R over rolling 30 trades |
| Trade frequency dropping | Pre-screen becoming more restrictive OR fewer structural breaks forming | Track trades/month trend |
| FVG-in-impulse delta narrowing | Quality signal losing discrimination | Compare FVG vs non-FVG OB WR quarterly |
| Session memory becoming ineffective | Memory-based selectivity no longer adds value | Compare first-eval vs later-eval WR monthly |

### 5.3 What Edge Decay Does NOT Look Like

- A single bad week or bad month is NOT decay. It is expected variance. At 62% WR, a run of 5 consecutive losses has approximately 0.8% probability per 5-trade sequence. Over 50 trades, you'll see it about once.
- A losing month at portfolio level is NOT decay. At ~14.5 trades/month and 62% WR, the probability of a negative-expectancy month is approximately 15-20%.
- SPRT remaining in the "continue" range after 20 trades is NOT failure. The continue range is designed to prevent premature decisions. The tables account for this.

---

## 6. Regime-Dependent Performance Expectations

### 6.1 What We Know

The system was validated during a gold bull market (roughly $1,800 to $4,500+ during the batch period). Bearish conditions are underrepresented — only 3 SHORT wins are validated, far below the 21 needed for directional confirmation.

The academic literature confirms gold has distinct volatility regimes (Naeem et al., 2019; Sopipan et al., 2012) and that strategy performance is regime-dependent. However, the project's own deep dive found market regime is NOT a significant predictor of OB continuation (all regime tests p > 0.05). This suggests the mechanical OB pattern is relatively regime-robust, but the AI's discrimination on top of it may not be.

### 6.2 Regime Risk Factors

| Regime | Expected Impact | Rationale |
|---|---|---|
| Strong trend (current) | Best performance | H1 structural breaks are clear, continuation is natural |
| Range-bound | Likely degraded | BOS/CHoCH events are false breaks more often in ranges |
| High-volatility shock (e.g., financial crisis) | Unknown — could be better or worse | Larger cascades create stronger OBs but also more noise |
| De-correlation (DXY-gold positive) | Possibly degraded | Unusual macro regime; patterns may not hold. Only 4.3% of the time historically |

### 6.3 Central Bank Regime Shift

If central banks reverse from net buyers to net sellers (unlikely in 2026 but possible), the structural demand floor beneath gold disappears. This would likely reduce bullish OB continuation rates and potentially invalidate the bullish D1/H4 bias that the pre-screen relies on. **Monitor World Gold Council quarterly demand data for any deceleration in central bank buying.** [LOW probability, HIGH impact]

---

## 7. Testable Predictions That Distinguish Mechanisms

These tests can separate "the OB zone matters" from "it's just momentum":

### Test A — Dumb Momentum Baseline ($0, Existing Data)

After every H1 BOS, enter LONG/SHORT on any close that retraces ≥80% of the impulse range. No AI evaluation. No OB zone identification. Same SL/TP rules. Compare WR and expectancy to the full system. **If the dumb baseline matches (within 5pp WR), the OB zone and AI layer are unnecessary scaffolding on a momentum strategy.** If the full system outperforms by ≥10pp WR, the AI+OB layer adds genuine value.

**Priority:** HIGHEST. Should be run before or within the first week of live trading. Costs nothing.

### Test B — Prompt-Neutral Rerun (~$5-10)

Take 30 existing CANDIDATE evaluations. Replace all SMC terminology with neutral language. Same MSO data. Compare decisions and outcomes. **If WR changes by >10pp, the AI is fitting to narrative, not data.**

**Priority:** HIGH. Should be run within the first week.

### Test C — Autocorrelation Monitoring ($0, Forward-Looking)

Add rolling 20-period H1 return autocorrelation to the live monitoring dashboard. Track whether this metric correlates with system performance over time. **If autocorrelation drops and system WR drops simultaneously, the edge is momentum-based.** If autocorrelation drops but system WR holds, the OB zone adds independent value.

**Priority:** MEDIUM. Set up during first month.

### Test D — OB Zone vs Generic S/R ($0, Existing Data)

Compare OB-zone retests to retests of other identifiable H1 levels (prior swing highs/lows, round numbers) within the same structural context. **If generic S/R retests have similar continuation to OB-specific retests, the OB identification is just another way to find S/R — the specific "last opposing candle" definition adds nothing.**

**Priority:** MEDIUM. Phase 1 investigation.

---

## 8. Specific Risk Factors to Monitor

### 8.1 Risk Register

| # | Risk | Severity | Probability | Detection Method | Mitigation |
|---|---|---|---|---|---|
| 1 | Edge decay from algo competition | HIGH | MEDIUM | H1 autocorrelation trending down, quarterly WR comparison | Scale down risk; investigate cause |
| 2 | Prompt narrative fitting | HIGH | UNKNOWN | Run prompt-neutral test ($5-10) | Rewrite prompt with neutral terminology if confirmed |
| 3 | Regime change (gold enters bear/range) | HIGH | LOW (2026) | D1 structure shifts persistently bearish; central bank net selling | Reduce position size; expand SHORT data collection |
| 4 | GBPJPY is false positive | MEDIUM | MEDIUM | SPRT tracking; first 20 trades | Kill early if SPRT approaches boundary |
| 5 | Session memory creates path dependence | MEDIUM | LOW | Monitor for "memory-induced" extended conservative streaks | Cap consecutive NO_TRADE decisions |
| 6 | Broker execution degrades | LOW | LOW | Track slippage and spread trends | Switch broker if persistent |
| 7 | API model change (Sonnet upgrade) | MEDIUM | LOW-MEDIUM | Track API model version; test new version on batch before live use | Pin model version in API calls |
| 8 | Walk-forward window violated (prompt changed mid-window) | HIGH | MEDIUM | Process discipline | Make the 3-month rule a hard gate |

### 8.2 Unresolved Questions (From All Sessions)

1. **Does the OB zone itself add value over generic trend-following entries?** (Dumb momentum baseline — Test A)
2. **Is the AI fitting to SMC narrative or reading numbers?** (Prompt-neutral test — Test B)
3. **What explains the 9pp quarterly WR decay?** (Genuine decay, regime change, or noise — requires 12-18 months of live data)
4. **Why does London perform well if London volatility is unremarkable?** (Setup quality vs volatility as the driver)
5. **Does DST affect kill zone performance?** (Free analysis on existing data)
6. **Is session memory genuine signal or reduced self-harm?** (Operationally irrelevant but theoretically important)
7. **Does D1 direction actually matter for AI evaluation?** (Recent finding suggests D1 pre-screen may be removable — awaiting batch test of 50 D1-unclear dates at $15-20)

---

## 9. Summary — Severity Ratings for All Criticisms

| # | Criticism | Severity | Status |
|---|---|---|---|
| 1 | SMC theoretical narrative is unproven | Concerning (theory) / Irrelevant (profitability) | Evidence is against the narrative; system is profitable regardless |
| 2a | OB continuation = simple momentum | **CONCERNING** | Not yet tested — dumb baseline needed (Test A) |
| 2b | Tautological with trend-following | **CONCERNING** | Same test resolves this |
| 2c | Volatility clustering | Weak | REFUTED (p>0.05 all regimes) |
| 2d | Self-fulfilling prophecy | Weak | REFUTED by universal cross-instrument rates |
| 3 | Right-for-wrong-reasons risk | **CONCERNING** | Monitor autocorrelation, not narrative |
| 4 | Edge decay from algo competition | **CONCERNING** | 9pp quarterly decay is real signal; track H1 autocorrelation |
| 5 | LLM prompt narrative fitting | **CONCERNING** | $5-10 test, not yet run (Test B) |
| 6 | Multiple testing (Bonferroni) | Mixed | WR survives; expectancy does not |
| 7 | Instrument selection bias | Weak-Moderate | Math shows selection bias insufficient to explain results |
| 8 | FVG = momentum proxy | Valid but irrelevant | Signal is real regardless of mechanism |
| 9 | Session memory = reduced self-harm | Valid but irrelevant | Same action either way |
| 10 | GBPJPY false positive | **CONCERNING** | Fails family-wise correction; shortest leash |
| 11 | SHORT edge unproven | **CONCERNING** | Only 3 SHORT wins; 21 needed |

**Devastating criticisms: 0.** No single finding invalidates the system.
**Concerning criticisms: 7.** These warrant active monitoring and specific tests.
**Weak/Refuted criticisms: 3.**
**Valid but operationally irrelevant: 2.**

---

## 10. The Bottom Line

**The profitability evidence is stronger than the theoretical explanation for why it works.** This sentence — from the red team review — is the single most important statement across all research. It correctly separates "does it work?" from "why does it work?" and identifies the primary forward risk: **wrong mechanism → wrong decay monitoring → missing the edge when it dies.**

The system has earned the right to go live. The statistical evidence is robust. The concerns are manageable with the monitoring framework and scheduled tests. The 3-month walk-forward windows provide structured checkpoints. The SPRT tables make kill/confirm decisions mechanical.

**What must happen in the first two weeks:**
1. Start SPRT tracking from trade 1
2. Run the prompt-neutral test ($5-10) — Test B
3. Run the dumb momentum baseline ($0) — Test A
4. Do NOT add any new features, filters, or layers
5. Do NOT change the prompt until the first walk-forward window closes

The edge is real until proven otherwise. Monitor it actively. Kill it mechanically if the data says to. Don't let theory dictate risk management.

---

*End of Document 3. Approximately 5,400 words.*
