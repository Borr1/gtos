# Pre-Lock Final Review — Walk-Forward Window WF-1

**Date:** April 5, 2026
**Reviewer:** Strategic trading mentor / red team
**Scope:** All 12 sprint outputs reviewed against 5 gate questions
**Decision required:** Lock prompt for 3 months or halt for fixes

---

## Question 1: Is there ANY FTMO rule that our system violates?

### Verdict: NO VIOLATION ON DEMO. ONE CRITICAL GAP FOR FUNDED.

The system is **fully compliant** for the Monday demo launch. Every FTMO rule was checked against system behavior:

| Rule | Status | Evidence |
|------|--------|----------|
| Daily loss limit (5%) | COMPLIANT | Circuit breaker at 3%, hard stop at 4.5%. Position sizing at 1% risk means max 2 concurrent losses = 2% daily. |
| Max drawdown (10%, static) | COMPLIANT | Monte Carlo: 99.4% P(pass) at 1% risk. Static floor never trails up — early profits create buffer. |
| Min trading days (4) | COMPLIANT | ~17 trades/month across instruments, spread across many days. |
| EA allowed | COMPLIANT | Proprietary, MT5, <100 server requests/day. |
| Position sizing consistency | COMPLIANT | Programmatic percentage-based sizing. No irregular lots. |
| Weekend holding | COMPLIANT | System never holds overnight. Timeout trailing closes all positions within session. |
| Consistency rule | N/A | 2-Step has no Best Day Rule or consistency requirement. |
| Copy trading / coordination | COMPLIANT | Proprietary system, no external signals. |

**The one critical gap:** News trading restrictions on the funded account. FTMO Standard prohibits opening or closing trades within 2 minutes of high-impact USD events (NFP, CPI, FOMC). If an SL triggers during that window, it counts as a violation. The system has no news calendar filter.

**This does NOT affect the demo launch.** FTMO imposes zero news restrictions during the evaluation phases (Challenge and Verification). The restriction only applies to funded accounts.

**Action required before purchasing the challenge:** Implement a news calendar pre-screen that blocks new XAUUSD entries within 15 minutes of scheduled high-impact USD events. Estimated effort: 2-3 hours of Claude Code work. Timeline: must be complete before the challenge purchase, which is earliest mid-May (after 30+ demo trades).

**No halt required.** Proceed with Monday demo launch.

---

## Question 2: Should we change the prompt before locking?

### Verdict: NO. Lock the prompt as-is.

I reviewed the prompt against findings from Test B, the per-step evaluation, the reasoning text mining, and the R-multiple analysis. Here is the evidence for and against each potential change, and why none of them clears the bar.

### Change considered: Strip identity framing ("institutional gold trader")

**Evidence for:** Test B showed the neutral prompt (with identity and quality signals removed) produced similar WR (60.0% vs 61.5%) with fewer trades (10 vs 13).

**Evidence against:** The production prompt caught the +3.77R winner and two other winners the neutral missed. Net R-impact: +5.06R favoring production. The identity framing makes the AI more willing to take trades, which increases volume at similar quality.

**Decision: Keep.** The framing increases CANDIDATE rate without degrading WR. More trades at the same quality = more expected profit. The +5R advantage is noisy (n=7 flips, one outlier) but directionally clear.

### Change considered: Remove Steps 1, 2, 5 (100% pass rate = "cargo cult")

**Evidence for:** Per-step analysis shows D1 bias confidence, H4 alignment, and M15 displacement quality pass 100% of CANDIDATEs. They add zero discriminative power within the CANDIDATE population.

**Evidence against:** These steps filter at the NO_TRADE stage, before CANDIDATE. Every CANDIDATE has already survived these filters. Removing them would allow setups with unclear D1, misaligned H4, or weak M15 displacement to reach CANDIDATE — exactly the setups the filters are designed to catch. The 100% pass rate within CANDIDATEs is evidence the filters are working, not evidence they're useless.

**Decision: Keep.** You cannot evaluate a filter's value by looking only at the population that passed it.

### Change considered: Remove or de-weight the liquidity sweep requirement (Step 4)

**Evidence for:** Per-step analysis shows trades WITHOUT sweeps win more often (71.6%) than with sweeps (63.4%), p=0.40. The sweep check may be adding noise.

**Evidence against:** p=0.40 means this is not statistically significant. The directional finding could reverse with 20 more trades. The sweep is not a hard requirement — the AI already takes trades without sweeps (67 of 108 trades had no sweep detected). The prompt says to note sweeps as confluence, not to require them.

**Decision: Keep.** The finding is directionally interesting but not significant. Log it for WF-2 investigation. Do not modify the prompt based on p=0.40.

### Change considered: Remove the quality signals (FVG creation +11%, impulse compactness, OB absorption caution)

**Evidence for:** Test B removed these and WR was similar. The reasoning text mining shows the AI produces near-identical assessments regardless — confidence 80 for 98% of trades, grade A+ for 83%.

**Evidence against:** Test B showed the production prompt (with quality signals) caught bigger winners. The quality signals appear to give the AI confidence to pull the trigger on valid setups, not to improve its quality discrimination. Removing them reduces CANDIDATE rate without improving WR.

**Decision: Keep.** The signals earn their keep through trade frequency, not quality discrimination. This is a subtle but real contribution.

### Change considered: Fix the confidence score (currently rubber-stamps 80 on everything)

**Evidence for:** The reasoning text mining confirms zero variance. Confidence 80 on 98% of trades. Grade A+ on 83%. The confidence score adds no information.

**Evidence against:** Fixing this requires either restructuring the confidence elicitation (forced decomposition instead of holistic rating) or removing it entirely. Either change modifies the prompt output structure, which changes how downstream systems parse the response. This is a meaningful change, not a cosmetic fix.

**Decision: Defer to WF-2.** The rubber stamp doesn't hurt — it's wasted tokens but doesn't degrade performance. Restructuring the confidence system is a WF-2 engineering project, not a pre-lock patch.

### Final prompt decision: **LOCK AS-IS. NO CHANGES.**

The prompt produces +0.200R expectancy with a 1.75 profit factor across 111 validated trades. Every proposed change either (a) is not statistically supported, (b) would reduce trade frequency, or (c) requires structural rework beyond a pre-lock patch. The walk-forward window exists to collect forward data on the current system. Changing the prompt now would restart the validation clock on an unproven modification.

---

## Question 3: Should we activate any inactive signals before locking?

### Verdict: NO. Keep all activation states unchanged.

The signal activation audit identified seven signals at various activation levels. Here is the assessment for each:

| Signal | Current Status | Activate Now? | Reasoning |
|--------|---------------|---------------|-----------|
| Align score | ACTIVE | Already active | Soft guidance, no gate. Validated +7.5pp. Working as designed. |
| Session memory | ACTIVE | Already active | Load-bearing. Test B confirmed: without it, CANDIDATE rate drops from 100% to 43%. |
| Trade index (KB L1) | ACTIVE | Already active | Last 10 trades flow to PA. Working. |
| Confidence scorer | SHADOW | **No** | Analysis 2 showed near-zero feature variance. price_level_count doesn't replicate (+3pp vs claimed +17pp, p=1.0). hesitation_score is untestable (all ≤2). Activating a filter that can't discriminate is pointless. Shadow mode collects data for WF-2 decision. |
| Breaker block | INACTIVE | **No** | Adding a second framework changes the trade population. SPRT baselines, batch WR, and monitoring metrics all assume ob_retest only. Contaminating WF-1 data with breaker trades makes the June review uninterpretable. |
| FVG framework | INACTIVE | **No** | Needs new verification checks, prompt criteria, and batch validation. High effort, zero evidence of edge. Not ready. |
| Similar setups (L3) for PA | PARTIAL | **No** | Wiring Layer 3 into the PA user message changes what the AI sees on every candle. This is functionally a prompt change. Defer to WF-2. |

**The walk-forward principle applies to signals as well as the prompt:** any change to what the system does — what it filters, what it shows the AI, what frameworks it trades — changes the trade population and contaminates the walk-forward data. The only valid WF-1 configuration is the one that's been batch-tested.

---

## Question 4: What is the single biggest risk we're taking that we haven't mitigated?

### Answer: The volatility regime mismatch.

The gold market snapshot documents GVZ at ~42 (vs ~20 during the batch period). Gold is in a corrective/consolidation phase dominated by geopolitical headline risk, with an active war driving inverted safe-haven dynamics. Daily ranges are roughly 2x what the batch was calibrated on.

**Why this is the biggest risk:**

1. **The system's ATR-based parameters will produce wider stops.** This is handled mechanically (wider SL = smaller position = same dollar risk). But wider stops also mean fewer setups qualify for the minimum RR threshold, reducing trade frequency below the already-conservative 4-6/month estimate.

2. **OB continuation behavior may differ in headline-driven markets.** The batch validated OB retests in a structurally trending gold market. In a headline-driven corrective market, BOS events may be caused by news spikes rather than institutional order flow. News-driven impulses may create OB zones that don't hold because there's no institutional position behind them — the zone was created by a temporary liquidity event, not by sustained buying/selling.

3. **The regime tagging attempted to quantify this risk but produced unreliable results.** The classifier put 74% of gold's strongest bull run into "RANGING," which means either the definition is wrong or gold's D1 swing structure doesn't fit neat trend/range categories. Either way, we cannot use the regime analysis to predict system behavior in the current environment.

4. **We have no circuit breaker for regime.** The monitoring dashboard tracks 20 metrics, but none of them directly measures "is the current market regime compatible with OB retest continuation?" The OB continuation rate (M15) is the closest proxy, but it requires 30+ retested OBs before it becomes informative — roughly 6-8 weeks of data.

**What we HAVE mitigated:**
- Position sizing automatically adjusts for higher ATR (mechanical)
- SPRT will detect sustained underperformance and kill underperforming instruments (statistical)
- Emergency stops catch catastrophic scenarios (circuit breaker)
- The 13:00 UTC skip filter removes the worst NY open candle (evidence-based)
- Correlation sizing limits JPY pair exposure (portfolio risk)

**What we HAVEN'T mitigated:**
- No way to detect "OB zones formed by headline spikes rather than institutional flow"
- No volatility-regime gate (e.g., pause when GVZ > 40)
- No event-driven position reduction for imminent FOMC/CPI
- The first 30 trades will tell us whether the system handles this regime — but we're flying blind until then

**Mitigation available without changing the prompt:** Start at 1.0% risk on demo (as planned), treat the first 30 trades as out-of-sample validation, and monitor the OB continuation rate from Day 1. If the first 10 trades show WR below 40%, that's not normal variance at the batch WR — it's a regime problem. The playbook (Scenario 17: 5 consecutive losses) provides the halt trigger.

---

## Question 5: Confidence rating — will this system be profitable over the next 3 months?

### Rating: 6/10

**What drives the rating upward (toward confident):**

- The OB zone edge is real. Test A rerun confirmed +17pp over dumb baseline on the actual trading population (p=0.003). This is the largest validated finding in the project.
- The batch expectancy (+0.200R, profit factor 1.75) is positive across 111 trades with sub-period stability (XAUUSD improved from 55% to 61% in the second half).
- Session memory doubles expectancy. It's active and validated.
- Kill zone timing works. London 74% WR is the strongest signal after OB identification itself.
- The walk-forward protocol, SPRT tracking, CUSUM monitoring, and operator playbook are genuinely world-class operational infrastructure for a retail trading system. Even if the edge decays, you'll detect it before it destroys capital.
- Static FTMO drawdown and unlimited time remove the two biggest prop firm failure modes (trailing drawdown traps and time pressure).

**What drives the rating downward (toward uncertain):**

- **Volatility regime mismatch (the #1 risk).** GVZ at 42 vs ~20 during batch. The system has zero forward data in this environment. The first 30 trades are genuinely unknown territory.
- **The AI adds ~0pp to entry WR.** Two independent analyses (Test A rerun, R-multiple decomposition) show the AI's CANDIDATE/NO_TRADE filtering doesn't improve WR over unfiltered OB entries. The system is profitable because of Component 2's zone detection and the execution rules, not because of Claude's reasoning. This means the expensive API call in the middle is functioning as a pass-through on entry selection. Its value may be in TP placement, direction selection, and session memory context — but that's unproven.
- **Confidence scorer is a rubber stamp.** 98% of trades get confidence 80. The shadow mode will collect data but won't produce actionable discrimination for at least 2-3 months.
- **Multi-instrument expansion is unproven at portfolio level.** GBPJPY has +0.5pp Wilson margin above breakeven — essentially coin-flip territory. GBPUSD has 6 trades. US30 showed the only per-instrument WR decline in the sub-period analysis. Only XAUUSD and USDJPY have batch evidence strong enough to trade with real confidence.
- **The 15-16 month Phase 1 timeline is long.** At +0.154R adjusted expectancy per trade, the system needs ~87 trades to hit the $10K profit target. Patience erosion is a genuine operator risk, especially during inevitable drawdown periods.
- **The prompt's conservative bias (7 conservative nudges, 2 aggressive) creates session memory dependency.** Without memory, CANDIDATE rate drops to 33-43%. If session memory degrades (bug, context window issues, LanceDB failure), the system effectively stops trading.

**The 6/10 means:** I believe the system has a genuine positive expectancy, and the infrastructure to detect and respond to edge decay is excellent. But the probability that the NEXT 3 months produce positive returns (not just that the system has positive expected value in the long run) is meaningfully uncertain due to the regime mismatch and the thin margins on several instruments. A 3-month window is short — 50-80 trades at portfolio level. Even with a true 60% WR, a 3-month losing stretch has roughly 8-12% probability.

If you asked me "will this system be profitable over the next 12 months, assuming the walk-forward process works correctly and you make evidence-based adjustments at each boundary?" — I'd rate that 7.5/10. The 3-month window is where regime variance dominates.

---

## Final Checklist — Pre-Lock Actions

| # | Action | Status | Blocking? |
|---|--------|--------|-----------|
| 1 | Lock walk-forward window: `python run_agent.py --lock-walk-forward --window WF-1 --months 3` | **DO NOW** | Yes |
| 2 | Verify all 5 processes start cleanly on Windows machine | **Sunday night** | Yes |
| 3 | Verify MT5 connected, AutoTrading enabled, all 5 symbols in Market Watch | **Sunday night** | Yes |
| 4 | Verify Windows sleep settings = Never | **Sunday night** | Yes |
| 5 | Check XAUUSD spread at Sunday evening open (5 PM ET) | **Sunday night** | No — informational |
| 6 | Confirm `enabled_frameworks: ["ob_retest"]` in config (no breaker, no FVG) | **Now** | Yes |
| 7 | Confirm `confidence_filter_mode: "shadow"` in config | **Now** | Yes |
| 8 | Confirm `skip_first_ny_candle: true` for XAUUSD in config | **Now** | Yes |
| 9 | Confirm risk_percent = 1.0 for all instruments (demo rate) | **Now** | Yes |
| 10 | Commit all Gamma session changes (543 tests passing) | **Now** | Yes |
| 11 | Verify `ExecutionEngine.open_trade()` handles `risk_pct_override` kwarg | **Now** | Yes — correlation sizing depends on this |
| 12 | Close the prompt file. Do not open `primary_analyzer_prompt.py` until July. | **After lock** | N/A |

---

## Documents to Keep Open During WF-1

| Document | Purpose | When to reference |
|----------|---------|-------------------|
| Quick Reference Card | Daily operations — KZ times, SPRT tables, emergency stops | Every trading day |
| Operator Decision Playbook | "What do I do when..." — 40 scenarios | When something unexpected happens |
| Monitoring Dashboard Spec | What to measure and when to act | Weekly reviews |
| Trade Journal Template | Per-trade recording format | After every trade |

## Documents to Archive Until July

| Document | Purpose | When to revisit |
|----------|---------|-----------------|
| Prompt Feature Inventory | WF-1 baseline for comparison | WF-1 boundary review |
| Test A/B Results | Evidence base for prompt decisions | WF-2 prompt redesign |
| Confidence Scorer Promotion Design | Activation decision | WF-1 boundary, contingent on shadow data |
| Regime Analysis Design | Re-run with verified swing detection | WF-2 planning |
| Competitive Landscape | Strategic context | Quarterly review |

---

## One-Line Summary

The system has a validated +0.200R edge driven primarily by Component 2's OB zone detection, with genuine uncertainty about performance in the current high-volatility regime. Lock the prompt, launch Monday, collect data, resist the urge to intervene. The walk-forward window is sacred.

---

*Reviewed: April 5, 2026. System goes live Monday April 7, 2026. WF-1 expires July 7, 2026. Next prompt review: July 2026.*