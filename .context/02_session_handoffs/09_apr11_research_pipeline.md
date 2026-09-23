# Session Handoff — Academic Research Pipeline Continuation
## Date: April 11, 2026 (evening KL time)
## For: Fresh Claude session continuing the 113-question research execution plan
## From: Previous session that completed all Priority A implementations + built the roadmap

---

## YOUR ROLE

Strategic trading mentor, technical coach, and research advisor for Borhen. You are continuing an academic research pipeline that has already completed Phase 0 (taxonomy), Phase 1 Priority A (literature search + implementations), and is now entering Phase 1 Priority B/C — the systematic sweep of 113 remaining questions.

**Core behavior:**
- Brutally honest and direct. No sugarcoating.
- Statistical rigor is non-negotiable. p-values, Bonferroni, Wilson CIs.
- "Feels right" is not evidence.
- Every prompt you write MUST be pressure-tested before presenting: (1) switch to critic mode, (2) try to break the prompt, (3) list issues found, (4) fix them, (5) explicitly state what was found and fixed.
- Challenge sloppy reasoning. If outputs look wrong, say so.
- Finished artifacts over design documents.

---

## WHAT HAS BEEN BUILT (don't rebuild this)

### Phase 0: Taxonomy
- 137 questions across 19 disciplines mapped to 17 GTOS pipeline components
- File: PHASE_0_ACADEMIC_RESEARCH_TAXONOMY.md

### Phase 1 Priority A: Literature Search
- 69 papers found across 8 questions (Q-6.1, Q-6.4, Q-5.1, Q-6.2, Q-7.1, Q-8.1, Q-2.2, Q-13.1/Q-13.3)
- File: phase1_priority_a_papers.md

### 12 Diagnostic Tests + Peer Review Audit
All run on MT5 H1 data across 5 instruments. Key results:
- Gold is a random walk by every linear test (VR, ACF, ARFIMA, Hurst)
- Fat tails: GPD ξ=0.35 (gold), kurtosis=34.85
- GARCH α+β=0.99, vol half-life ~73 H1 bars
- OU half-life: 23.05 bars all-hours, 17.05 bars KZ-only (26% faster)
- Nonlinear structure exists (PE=0.99876) but KZ ordering is NOT significant (p=0.79)
- 9 hypotheses eliminated, 4 confirmed, 4 informational

### 5 Priority A Implementations (ALL COMPLETE)

| # | Question | Result | Action |
|---|----------|--------|--------|
| 1 | Q-6.1 Trailing Stop | Symmetric OU can't rank GTOS exits. Timeout: 26 KZ / 35 all-hours bars. Fat tails reduce Sharpe ~20% but don't shift optimal levels. | NO CHANGE to SL/TP — SL governed by zone invalidation, not OU Sharpe. Timeout values available for future refinement. |
| 2 | Q-5.1 GARCH-EVT SL | NULL RESULT. 0/11 tests survive Bonferroni. Higher vol → higher WR (reversed direction). Removing Q4 entries hurts by -18.8R. | NO CHANGE — do NOT implement GARCH entry filter. ATR-based SL already handles vol. |
| 3 | Q-7.1 Constrained Kelly | f*=4% (P(pass)=75.7%, P(violation)=22.3%). f_safe=3%. Current 1%: P(pass)=37.5%. Best jump: 1%→2% doubles P(pass) with 4.2% violation risk. | DEPLOYED to 2% on FTMO demo. Target 2.5-3% after 30+ live trades confirm edge. |
| 4 | Q-2.2 OB Zone Age | 106,147 events, 13 instruments. Touch-1=72.7%, Touch-2+=31.5%. 41pp cliff, Bonferroni-significant. Formation age irrelevant (99.9% retest within 10 bars). | NO CHANGE — system already trades touch-1 only. Codified rule explicitly. |
| 5 | Q-8.1 Shiryaev-Roberts | SR/CUSUM/BOCPD built. SR optimal for GTOS (wins on mean ADD). ADD=56 trades (3.3 months) for p₁=0.50. Historical backtest: no alarm (correct — edge never fully collapsed). | DEPLOYED — EdgeMonitor integrated into post-trade pipeline + Telegram alerts. |

### Deployment (in progress via Claude Code)
Three changes being deployed:
1. Risk 1% → 2%
2. EdgeMonitor (SR + CUSUM + BOCPD) integrated into live system
3. Touch-1-only rule codified in prompt and code

---

## THE CORE UNDERSTANDING (this is what makes your prompts good)

### 1. The Edge Mechanism
The OB retest edge is a **stop-cascade mechanism** (Osler 2003/2005). Stop-loss orders cluster at specific price levels. When price hits the cluster, cascade pushes through → exhausts → reverts. First touch depletes the cluster (72.7% continuation). Subsequent touches find empty clusters (31.5%). This is why:
- VR shows random walk (no linear autocorrelation)
- But OB continuation is 70%+ (conditional on being at a zone with clustered stops)
- The edge is NONLINEAR and MICROSTRUCTURAL

### 2. Gold's Statistical Fingerprint
- Random walk by every linear test (VR≈1.0, H≈0.5, d≈0)
- Fat tails: ξ=0.35 (6.2× more 3σ events than Gaussian)
- Volatility clustering: GARCH 0.99 (half-life 73 bars — quiet predicts quiet)
- Negative skew: -1.529 (crashes harder than rallies)
- No leverage effect (symmetric vol for LONG and SHORT)
- OU half-life: 23.05 all-hours, 17.05 KZ-only

### 3. Per-Instrument Differences (CRITICAL — never apply gold parameters universally)

| Property | XAUUSD | US30 | USDJPY | GBPJPY | GBPUSD |
|----------|--------|------|--------|--------|--------|
| Tail ξ | 0.35 | 0.20 | 0.22 | 0.18 | 0.16 |
| GARCH persistence | 0.99 | 1.00 | 0.99 | 0.89 | 0.80 |
| OU HL (H1) | 23.05 | 21.4 | 23.8 | 21.2 | 21.4 |
| OB Touch-1 cont% | 75.1% | 75.1% | 73.8% | 72.3% | 72.4% |
| Batch WR | 65% | 59.5% | 75% | 62.5% | 66.7% |
| Batch n | 100 | 37 | 28 | 40 | 21 |

### 4. What Didn't Work (and why — so you don't repeat)
- **GARCH entry filter:** Higher vol = better outcomes, not worse. OBs formed during high-vol are stronger.
- **VWAP as zone type:** 24.5% reversion — too weak. Gold trends away from VWAP during KZ.
- **Asia narrow → London explosive:** Opposite. r=0.83 narrow→narrow. Pure GARCH persistence.
- **Intraday momentum:** β=-0.187 but 0.3 bps edge — dead after costs.
- **London gold fix:** Dead post-2015 LBMA reform.
- **Compression → expansion:** ATR too smooth to test. Pure persistence, no spring.
- **PE KZ ordering:** Methodological error. p=0.79 after permutation test. KZ advantage is faster OU reversion, not ordinal structure.
- **OU for SL/TP optimization:** Symmetric OU model has no directional prior. Predicts 40% WR where GTOS gets 62%. The 22pp gap IS the edge. OU can't rank exits but CAN calibrate timeout bars.

### 5. Why the Priority Order Matters
The execution plan organizes 113 questions into 5 waves:
- **Wave 1 (Multipliers):** Entry, features, AI — affects EVERY trade. Small gains here multiply across everything.
- **Wave 2 (Edge optimization):** Make OB retest sharper/more frequent.
- **Wave 3 (Edge discovery):** Find new setups. Highest variance but highest potential.
- **Wave 4 (Risk/portfolio):** Protect capital.
- **Wave 5 (Strategic):** Long-term understanding.

We do Wave 1 first because a 0.1R improvement to entry compounds across 17 trades/month × 5 instruments × every month forever. A new edge in Wave 3 adds frequency but only after it's validated.

### 6. The System Architecture
- **Claude Sonnet** is the reasoning engine (evaluates structured JSON Market State Objects)
- **MetaTrader 5** on Windows runs live execution
- **Python codebase** (~16,000+ lines, 463+ tests)
- **FTMO $100K demo** account (free trial, not paid challenge)
- **5 instruments:** XAUUSD, US30, USDJPY, GBPJPY, GBPUSD
- **Kill zones:** London 07:00-10:30 UTC, NY 13:00-15:30 UTC (+ Tokyo for USDJPY)
- **Current setup:** OB retest after liquidity sweep with BOS confirmation, 50/25/25 partial exits
- **Claude Code terminal agents** attached to the project folder with full context via CLAUDE.MD

### 7. Operational Rules
- WF-1 is CANCELLED — free to modify src/, prompts/, parameters
- Agents propose, CEO approves — every deliverable is a FILE
- Pressure test every prompt before presenting
- Never re-run in-sample data to validate fixes
- Version all outputs, never overwrite
- Bonferroni correction on all hypothesis testing
- Per-instrument analysis mandatory where data allows
- Shadow-test 30+ observations before promoting to live gate
- Convergence protocol: strategic review + red team + Claude Code

---

## WHAT YOU'RE DOING NOW

Executing the RESEARCH_EXECUTION_PLAN_113Q.md — the systematic literature search and testing of 113 remaining questions across 9 planned search sessions.

**Current position:** Starting L1 (Wave 1A: Entry Engineering, Q-4.1 to Q-4.4)

**Sequence:**
L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8 → L9
(Entry → AI → Pre-screen/Structure → SL/Exit/Decay → Edge Discovery Zones → Edge Discovery Non-Zone → Edge Discovery Math/Adversarial → Risk/Portfolio → Strategic)

For each search session:
1. Write the literature search prompt (pressure-tested)
2. Send to Claude Code (Opus, high effort)
3. Review the output — validate paper quality, flag suspicious findings
4. Identify which findings need empirical testing on GTOS data
5. Write diagnostic test prompts for testable findings
6. Send tests to Claude Code (Sonnet, high effort)
7. Review test results — validate methodology, check for bugs
8. Document findings, update the 113-question status tracker
9. If actionable: write implementation prompt → deploy

**Your quality standard:** Every prompt output gets reviewed for:
- Are the papers real? (hallucinated papers are a known LLM failure mode — verify via citation count, author reputation, journal existence)
- Are the findings correctly interpreted? (papers can be misread)
- Are the GTOS implications correctly drawn? (a finding on equities may not transfer to gold)
- Is the statistical methodology sound? (p-hacking, multiple comparisons, in-sample-only)

---

## FILES IN PROJECT KNOWLEDGE

These are your reference documents:

| File | Purpose |
|------|---------|
| PHASE_0_ACADEMIC_RESEARCH_TAXONOMY.md | The 137-question taxonomy — your master question list |
| phase1_priority_a_papers.md | 69 papers already found — cross-reference against these |
| PEER_REVIEW_AUDIT.md | Audit methodology — use same rigor for new findings |
| DEEP_CONTEXT_ACADEMIC_PIPELINE_APR11.md | Full reasoning chain — WHY each decision was made |
| SESSION_HANDOFF_ACADEMIC_PIPELINE_APR11.md | Previous session handoff — diagnostic results table |
| RESEARCH_EXECUTION_PLAN_113Q.md | The 113-question execution plan — your roadmap |
| architecture.md | System architecture reference |
| kb_edge_mechanisms_and_risks.md | Edge mechanism deep knowledge |
| kb_gold_market_deep_knowledge.md | Gold market properties |
| kb_validation_and_monitoring_framework.md | Statistical validation framework |

---

## WHAT SUCCESS LOOKS LIKE

At the end of this research pipeline:
- All 137 questions have a status (answered, eliminated, informational, or actionable)
- ~12 actionable findings deployed or queued for deployment
- The system trades more frequently (new edges), more accurately (better entry/features/AI), and more profitably (better exits/sizing)
- Every finding has a versioned file, a statistical test, and an independent audit
- No hallucinated papers, no p-hacked results, no in-sample-only conclusions

---

*Handoff generated: April 11, 2026*
*Previous session: ~8 hours, 5 implementations completed, 3 changes deployed, execution plan built*
*Next action: L1 literature search — Entry Engineering (Q-4.1 to Q-4.4)*
