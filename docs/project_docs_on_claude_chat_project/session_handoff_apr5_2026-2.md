# DEFINITIVE SESSION INTEGRATION — All 12 Agents + Red Team
# Date: April 5, 2026
# Status: FINAL. System goes live Monday April 7.

---

## PART 1: THE 10 FINDINGS THAT MATTER

### Finding 1: The OB Zone IS the Edge (+17pp, p=0.003)
Test A rerun on real 219 BOS events: OB zone entry outperforms best dumb baseline (80% retrace) by 16.8pp. Same-SL-distance variant confirms: 36-39% dumb vs 70.5% OB. NOT an artifact. Component 2's zone detection is the load-bearing component.
**Action: Protect Component 2. Do not simplify OB detection. Ever.**

### Finding 2: The AI Adds ~0pp to Entry WR
Two independent analyses confirm: AI-selected trades (56.1%) ≈ unfiltered OB entries (57.9% calibrated). The AI's CANDIDATE/NO_TRADE binary on entry selection is at best neutral, possibly slightly negative on R-multiples (+0.200R AI vs +0.264R unfiltered).
**BUT: This was tested without session memory. Finding 6 complicates this.**
**Action: Log for WF-2 investigation. Do not change prompt.**

### Finding 3: The AI Is a Rubber Stamp
98% of trades get confidence 80. 83% get A+. Steps 1, 2, 5 pass 100% of CANDIDATEs. The 7-step evaluation produces the same answer for every setup. The confidence scorer features don't replicate (price_level_count +3pp not +17pp, hesitation untestable due to zero variance).
**Action: Defer confidence score restructuring to WF-2. Current rubber stamp doesn't hurt — it's wasted tokens, not negative value.**

### Finding 4: The Production Prompt Beats the Neutral Prompt on R
Test B: 23.3% flip rate (7/30). Production caught the +3.77R winner and two other winners the neutral missed. Net R-impact: +5.06R favoring production. The identity framing and quality signals increase CANDIDATE rate (13 vs 10) at similar WR (61.5% vs 60.0%). More trades at same quality = more profit.
**Caveat from Zeta: This wasn't a full terminology neutralization — only removed identity/quality signals/self-check. The narrative fitting question is technically still open. But the production prompt is clearly better than the stripped version.**
**Action: Lock the production prompt. It earns its keep through trade frequency.**

### Finding 5: Session Memory Is Load-Bearing Infrastructure
Test B revealed: without session memory, CANDIDATE rate drops from 100% to 33-43%. The AI's conservative prompt bias (7 conservative nudges vs 2 aggressive) means without memory context, the AI defaults to NO_TRADE on most setups. Session memory provides the "developing pattern" context that overcomes this conservatism.
**This reframes the "AI adds 0pp" finding: the tests that showed 0pp ran without session memory. The AI + session memory combination may add genuine value that the isolated tests couldn't capture.**
**Action: Treat session memory as the #1 architectural component to protect. If it degrades (bug, context window, LanceDB failure), the system effectively stops trading.**

### Finding 6: FTMO Is Compliant for Demo, One Gap for Funded
No violations for Monday demo launch. The critical gap: funded accounts prohibit trading within 2 minutes of high-impact USD events (NFP, CPI, FOMC). Need a news calendar filter before purchasing the challenge.
**Action: Build news calendar filter before mid-May (earliest challenge purchase date). Not a Monday blocker.**

### Finding 7: We're Entering a High-Vol Headline-Driven Market
GVZ at 42 (doubled from batch period). Iran war active. Gold correcting 16% from ATH. NOT a clean trend — choppy, 2-sided, headline-driven. The batch was validated in a different regime.
**Zeta correctly notes: position sizing automatically handles higher ATR (wider stops = smaller lots = same dollar risk). The real question is whether OB continuation works when impulses are driven by headlines rather than institutional flow. We won't know until we collect data.**
**Action: Launch at 1.0% risk on demo as planned. First 30 trades are out-of-sample validation. Monitor OB continuation rate from Day 1.**

### Finding 8: USDJPY and GBPUSD Are in Extreme Mean-Reversion
Autocorrelation: USDJPY -0.411, GBPUSD -0.340. The OB retest strategy depends on continuation — the opposite of mean-reversion.
**Zeta correctly notes: 20-candle windows are noisy. Could be a single choppy session, not a regime. Don't pause instruments based on a snapshot.**
**Action: Monitor autocorrelation daily. If persistent negative for 2+ weeks on any instrument, reduce confidence in that instrument's SPRT data. SPRT handles sustained underperformance automatically.**

### Finding 9: The Regime Classifier Is Broken
74% of gold's strongest bull run classified as RANGING. The swing detection is scale-sensitive — large absolute swings at $5,000 gold don't register as HH/HL the same way they did at $2,500.
**Action: Do NOT add regime to monitoring or pre-screen. The classifier needs redesign with proper swing normalization. Defer to WF-2.**

### Finding 10: The Signal Landscape — What's Active vs Inactive
| Signal | Status | Value | Monday Action |
|---|---|---|---|
| Align score | ACTIVE | +7.5pp validated | None needed — already working |
| Session memory | ACTIVE | 2x expectancy, load-bearing | None needed — protect at all costs |
| FVG detection | ACTIVE (data shown to AI) | +7-20pp validated | None needed — AI sees FVGs in MSO |
| Trade index (L1 KB) | ACTIVE | Provides last-10-trade context | None needed |
| Confidence scorer | SHADOW | Features don't replicate | Stay shadow. Collect data. |
| Breaker block | INACTIVE (config) | ~10x/month in KZ | Do NOT activate during WF-1 |
| Similar setups (L3) | PARTIAL — debate only, PA doesn't see | Unknown | Do NOT wire to PA during WF-1 |

**The good news: the two most valuable signals (align score +7.5pp, session memory 2x) are already active. Nothing critical is sitting idle.**

---

## PART 2: WHAT ZETA'S FINAL REVIEW SAYS

### Q1: FTMO violations? NO for demo. One gap for funded (news filter).
### Q2: Change prompt? NO. Lock as-is. Every proposed change either lacks statistical support, would reduce frequency, or requires structural rework.
### Q3: Activate signals? NO. Keep all activation states unchanged for WF-1.
### Q4: Biggest unmitigated risk? Volatility regime mismatch. GVZ doubled, system untested in this environment, no regime circuit breaker.
### Q5: Confidence rating? 6/10 for next 3 months. 7.5/10 for next 12 months with walk-forward adjustments.

---

## PART 3: THE WF-2 DEFERRED CHANGES LOG

Everything below is logged for the July review. NONE of this touches WF-1.

| # | Change | Evidence | Priority |
|---|---|---|---|
| 1 | Restructure confidence score as forced decomposition (rate each step 1-5, sum = confidence) | Rubber stamp problem: 98% confidence=80 | HIGH |
| 2 | Investigate removing or de-weighting sweep requirement (Step 4) | Anti-predictive: 71.6% without vs 63.4% with (p=0.40) | MEDIUM |
| 3 | Add 1-2 aggressive nudges to balance 7 conservative biases | Session memory dependency caused by prompt conservatism | MEDIUM |
| 4 | Wire Layer 3 (similar setups) to PA prompt | Currently only debate agents see it, debate is disabled | MEDIUM |
| 5 | Test mechanical-only system (no AI, just Component 2 + rules) | AI adds ~0pp to WR, costs $60/month | HIGH |
| 6 | Fix regime classifier (normalize swings for price level) | Current classifier calls bull market "RANGING" | LOW |
| 7 | Evaluate breaker_retest activation | Fully built, config toggle, ~10x/month | MEDIUM |
| 8 | Run full neutral prompt (terminology replacement, not just signal removal) | Test B only stripped identity/signals, not SMC terms | LOW |
| 9 | Investigate premium zone trades | 5 trades, 100% WR, +1.79R avg — tiny sample but worth monitoring | LOW |
| 10 | Rethink AI's role: shift from "is this valid?" to "is context favorable?" | Component 2 pre-filters; AI should add contextual judgment | HIGH |

---

## PART 4: DOCUMENTS TO UPLOAD TO PROJECT KNOWLEDGE

| Document | Upload? | Why |
|---|---|---|
| operator_decision_playbook_final.md | YES | 4th KB document — operational reference |
| quick_reference_card.md | YES after 5 Zeta fixes | Daily phone reference |
| trade_journal_template.md | YES | Operational tool starting Monday |
| test_a_rerun_real_bos_results.md | YES | Definitive zone value evidence |
| test_a_implications_analysis-2.md | YES | Updated strategic framing |
| pre_lock_final_review.md | YES | Zeta's final assessment — reference for WF-1 boundary review |

Documents to archive (NOT project knowledge — save locally):
- test_b_results.md, signal_activation_audit.md, prompt_feature_inventory.md
- r_multiple_analysis.md, reasoning_text_mining.md, per_step_evaluation_analysis.md
- regime_tagging_results.md, regime_analysis_design.md
- competitive_landscape_assessment.md, ftmo_rules_deep_dive.md
- gold_market_snapshot_apr2026.md, confidence_scorer_promotion_design.md
- monitoring_dashboard_spec.md, autocorrelation baselines

---

## PART 5: QUICK REFERENCE CARD — 5 FIXES TO APPLY

1. Verify XAUUSD/US30 NY KZ end time against config (15:30 vs 17:00)
2. First-10-trades override: add "UNLESS WR falls below 25% (e.g., 1/6 or worse)"
3. Risk per trade: "Demo: 1.0%. Funded: 0.75% until SPRT confirms 2 instruments"
4. Add: "WF-1: April 7 – July 7, 2026. NO prompt changes."
5. GBPUSD: add "Enters SPRT tracking after 10 trades"

---

## PART 6: MONDAY MORNING SEQUENCE

### Sunday Night (before sleep)
1. Verify Windows machine sleep settings = Never
2. Check XAUUSD spread at Sunday evening open (5 PM ET = 5 AM KL Monday)
3. Confirm config: `enabled_frameworks: ["ob_retest"]`, `confidence_filter_mode: "shadow"`, `skip_first_ny_candle: true` for XAUUSD, `risk_percent: 1.0`

### Monday 7:45 AM KL (before Tokyo)
```bash
cd ~/Documents/ai-trading-agent
nohup python run_agent.py --symbol XAUUSD --mode demo > logs/xauusd.log 2>&1 &
nohup python run_agent.py --symbol US30_cash --mode demo > logs/us30.log 2>&1 &
nohup python run_agent.py --symbol USDJPY --mode demo > logs/usdjpy.log 2>&1 &
nohup python run_agent.py --symbol GBPJPY --mode demo > logs/gbpjpy.log 2>&1 &
nohup python run_agent.py --symbol GBPUSD --mode demo > logs/gbpusd.log 2>&1 &
```

Then immediately:
```bash
python run_agent.py --lock-walk-forward --window WF-1 --months 3
```

### Monday Monitoring
| KL Time | What |
|---|---|
| 8:00 AM | Tokyo opens — verify USDJPY + GBPJPY evaluating |
| 3:00 PM | London opens — ALL 5 instruments should evaluate |
| 6:30 PM | London closes (gold) — review session |
| 9:15 PM | NY opens — verify XAUUSD skips 13:00 candle |
| 1:00 AM | End of day — fill daily journal |

### After every trade
```bash
python scripts/live_monitor.py trade INSTRUMENT WIN/LOSS R_MULT
```

---

## PART 7: WHAT WE KNOW NOW THAT WE DIDN'T KNOW 24 HOURS AGO

| Before this sprint | After this sprint |
|---|---|
| "The AI picks good trades" | The AI rubber-stamps everything. Edge is Component 2 + execution rules. |
| "Confidence scorer shows +17pp" | Features don't replicate (+3pp). Scorer is dead on arrival. |
| "Quarterly decay is real" | Mix artifact. Gold IMPROVED +5.7pp in second half. |
| "OB zone might be cargo cult" | Zone adds +17pp (p=0.003). It's the primary edge source. |
| "Autocorrelation is the decay metric" | Autocorrelation is already zero. Monitor OB continuation rate instead. |
| "We should activate breaker blocks" | Keep inactive for WF-1. Don't contaminate the walk-forward. |
| "Maybe strip the prompt for neutrality" | Production prompt earns +5R over neutral through higher trade frequency. Keep it. |
| "Session memory helps" | Session memory is LOAD-BEARING. Without it, CANDIDATE rate drops to 33-43%. |
| "We're ready for FTMO" | Demo ready. Need news calendar filter before funded account. |
| "The regime doesn't matter" | GVZ doubled. We're flying blind in a new regime. First 30 trades are calibration. |

---

## PART 8: THE HONEST ASSESSMENT

**What you're deploying Monday:**
A system with a validated +0.200R edge (profit factor 1.75) driven primarily by Component 2's OB zone detection (+17pp) and execution rules (session timeouts + BE stops). The AI evaluation in the middle functions as a pass-through on entry selection but contributes through session memory context and trade frequency. The system is entering a volatility regime it wasn't tested in, with genuine uncertainty about performance.

**What gives me confidence (the 6 in Zeta's 6/10):**
The OB zone edge is real and statistically significant. Session memory works. Kill zone timing works. The monitoring infrastructure (SPRT, CUSUM, playbook, journal) is comprehensive. The walk-forward discipline will detect problems before they destroy capital. FTMO's static drawdown and unlimited time remove the worst prop firm failure modes.

**What gives me concern (the 4 that's missing):**
GVZ doubled and we have zero data in this regime. The AI adds ~0pp to entry selection. The confidence scorer is a rubber stamp. Multi-instrument edges are thin (GBPJPY +0.5pp margin). The system has a structural dependency on session memory that creates cold-start risk every session.

**The bottom line:**
Lock the prompt. Launch Monday. Collect data. Resist the urge to intervene. The system has earned the right to trade. The walk-forward window will tell you whether it deserves to keep trading. Close `primary_analyzer_prompt.py` and don't open it until July.
