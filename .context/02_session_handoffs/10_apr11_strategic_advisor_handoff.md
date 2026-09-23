# Session Handoff 10 — Strategic Research Advisor (L1+L2+T1 Complete, Prompts Delivered)
## Date: April 11, 2026 (late evening)
## For: Next Claude Code agent continuing as Strategic Research Advisor
## From: This session (completed L1+L2+T1 review, wrote T2a/T2b/I1/L3 prompts)

---

## YOUR ROLE: STRATEGIC RESEARCH ADVISOR

You are the **Strategic Research Advisor** for the GTOS academic research pipeline. This is a STRICTLY ADVISORY role:

**You DO:**
- Write literature search prompts (for Opus execution agents)
- Write empirical test prompts (for Sonnet execution agents)
- Write implementation prompts (for Sonnet execution agents)
- Review execution outputs — validate methodology, catch hallucinated papers, verify statistical rigor
- Decide: TEST / IMPLEMENT / KILL / DEFER for each finding
- Consolidate cross-search narratives — connect findings across L1, L2, T1, etc.
- Pressure-test every prompt before delivering (switch to critic mode, try to break it, list issues, fix them)

**You DO NOT:**
- Execute prompts yourself (those go to separate Claude Code terminals)
- Run code, modify src/, or deploy anything
- Make trading decisions
- Fabricate data or statistics
- Accept findings without verifying they're statistically sound

**Delivery format:** Every deliverable is a committed file. Not a chat message.

---

## PIPELINE STATE (verified end of this session)

### Completed
| Stage | Scope | Status | Key Finding |
|-------|-------|--------|-------------|
| L0 | Entry Engineering papers | 51 papers | Foundation literature |
| Priority A | 8 priority questions | 69 papers + 5 implementations | WF-1 cancelled, 2% risk deployed, EdgeMonitor live, touch-1 codified |
| L1 | Feature Engineering (Q-1.1–Q-1.7) | 57 papers, PASS | Kill tick volume (already absent), add CLV+BVC, spread surprise, gold session ATR, MI audit, compute DSR |
| L2 | AI Evaluation (Q-3.1–Q-3.7, Q-9.1) | 96 papers, PASS | XGBoost baseline test needed, SMC framing hurts, session memory = regime inference + conservative bias, confidence dead, 3-run consistency, GTOS in uncharted territory |
| T1 | Entry Engineering Tests (Q-4.1–Q-4.4) | 4 tests, INCONCLUSIVE | Entry precision is low-value; zone detection is where the edge lives. Suggestive: wide SL and wide TP underperform. Need n>50 per quartile. |

### Prompts Written and Ready for Execution
| Prompt | File | Execute With | Priority |
|--------|------|-------------|----------|
| T2a | `research/academic_pipeline/prompts/T2a_ai_evaluation_diagnostics.md` | Sonnet, max effort | HIGHEST — existential test |
| T2b | `research/academic_pipeline/prompts/T2b_ai_shadow_api_experiments.md` | Sonnet, max effort + API key | After T2a results |
| I1 | `research/academic_pipeline/prompts/I1_feature_engineering_implementation.md` | Sonnet, max effort | Parallel with T2a |
| L3 | `research/academic_pipeline/prompts/L3_edge_optimization_search_prompt.md` | Opus, high effort + WebSearch | Parallel with T2a |

### Execution Sequence
```
Wave A (parallel):
  T2a ─── XGBoost baseline + confidence diagnostic (zero cost, ~2 hours)
  I1  ─── Add CLV + BVC + session ATR to MSO (code changes, ~1 hour)
  L3  ─── Literature search: 12 questions on edge optimization (~2 hours)

Wave B (after T2a completes):
  T2b ─── Shadow API experiments (~$80, depends on T2a results)
  
Decision point after T2a:
  If XGBoost WR ≥ 62% on Part B (WIN/LOSS among CANDIDATEs):
    → LLM may be overhead. T2b becomes informational, not actionable.
    → Focus shifts to feature engineering (I1, L3 findings)
  If XGBoost WR < 58%:
    → LLM is irreplaceable. T2b becomes critical for optimization.
    → Focus shifts to prompt architecture (T2b experiments)
  If XGBoost WR 58-62%:
    → Ambiguous. Run T2b anyway for directional signal.
```

---

## THE CONSOLIDATED NARRATIVE (L1 + L2 + T1)

This is the single most important insight from the research so far:

**"The edge is zone detection, not the AI's reasoning over those zones."**

Evidence:
- Test A rerun: OB zone adds +17pp (p=0.003). AI adds ~0pp to entry WR.
- T1: Entry precision (where within the zone you enter) is low-value. The ZONE is what matters.
- L2: The LLM simultaneously ADDS value (spatial reasoning about zone quality, regime inference from session memory) and SUBTRACTS value (SMC narrative bias, conservative session memory bias, CoT overthinking, rubber-stamp confidence).

This means the optimization target is NOT "make the AI smarter" — it's:
1. Give the AI better INPUT data (I1: CLV, BVC, session ATR)
2. Remove AI biases that suppress good decisions (T2b: memory bias, framing bias, overthinking)
3. Test whether the AI is even needed vs. XGBoost (T2a: the existential test)
4. Find more zone opportunities (L3: increase frequency without diluting quality)

---

## KEY FINDINGS THAT INFORM PROMPT WRITING

### From L1 (Feature Engineering, 57 papers):
1. Tick volume is noise — do NOT add to MSO (already absent, confirmed)
2. CLV = (2C-H-L)/(H-L) — order flow proxy, zero data requirement, range [-1,+1]
3. BVC = norm.cdf((C-O)/sigma) — buy/sell classification, 76% accuracy on M15
4. Gold session-specific ATR — W-shaped intraday vol (London open HIGH, NY open HIGHEST, Asian LOW)
5. Majority voting (3 evaluators) — self-consistency per Wang et al. 2023
6. MI audit — mutual information between features and outcomes to identify dead weight
7. DSR (Discrimination Success Ratio) — measures AI's sorting ability, analogous to AUC

### From L2 (AI Evaluation, 96 papers):
1. XGBoost + TabPFN baseline — the existential test. If free model matches LLM, the LLM is overhead.
2. SMC framing is likely HURTING — Spitale & Germani 2025 shows source framing triggers systematic bias
3. Session memory causes majority-label bias — Zhao et al. 2021 recency bias + distributional priming
4. Confidence score is useless — 98% of decisions get confidence=80, it's a rubber stamp
5. CoT may be overthinking — Turpin et al. 2023 shows LLMs rationalize with provided frameworks
6. 3-run self-consistency — Wang et al. 2023 ICLR, optimal temperature 0.5-0.7 (Betz et al. 2024)
7. GTOS is in uncharted territory — no academic literature on LLMs for ICT/SMC trading specifically

### From T1 (Entry Engineering, 4 tests, n=121):
1. INCONCLUSIVE at n=14 per quartile (underpowered)
2. Directional: wide SL trades (>2.1× ATR) may underperform — 32pp WR gap Q3 vs Q4
3. Directional: wide TP trades (R:R > 4.0) may underperform — 37pp WR gap Q3 vs Q4
4. Entry distance from zone showed no signal — the zone itself is what matters, not entry precision within it
5. Batch system enters ABOVE H1 OBs (zone-relative), not within — data reality ≠ assumption

---

## STRATEGIC REASONING CHAINS (the "why behind the why")

This section captures the cross-paper connections and reasoning that inform decisions. Without this, the next agent would need to re-read all 273+ papers to reconstruct the thinking.

### Chain 1: Why Session Memory Is Both Valuable and Dangerous

**The mechanism:** Session memory is injected as "## Prior Candle Assessments (this session)" in the user_message (src/prompts/primary_analyzer_prompt.py lines 649-659). It shows the AI what it decided on prior candles in the same session.

**Why it helps:** Shi et al. 2024 (Nature) + Zhao & Tian 2024 show LLMs do Bayesian-approximate updating when given sequential observations. Session memory gives the AI implicit regime inference — if 3/4 prior candles were NO_TRADE due to "unclear structure," the AI infers a ranging regime and becomes appropriately cautious. This is GOOD. Backtests show session memory doubles expectancy (+0.66R vs +0.33R).

**Why it hurts:** Zhao et al. 2021 (ICML) demonstrated recency bias and majority-label bias in LLMs. If the first 4 candles are NO_TRADE (which happens ~90% of sessions because only 10.3% become CANDIDATE), the AI gets PRIMED toward NO_TRADE on candle 5. It's not learning "this session is ranging" — it's being distributionally biased by the label ratio. This may explain why 0 trades for the first 4 live days.

**The test (T2b Exp 1+2):** Scramble labels → if AI still performs equally well, the learning is distributional (regime), not label-dependent. Inject majority-CANDIDATE priors → if CANDIDATE rate goes up, the bias is real and we're suppressing valid setups.

**Decision consequence:** If bias is confirmed, the fix is NOT "remove session memory" — it's "balance the label distribution" or "use session memory for structure descriptions only, strip the decisions."

### Chain 2: Why SMC Framing Specifically Hurts an LLM

**The mechanism:** The system prompt says "You are an institutional forex trader with 15+ years experience in Smart Money Concepts (SMC) and ICT methodology." Every structural element uses SMC language: Order Blocks, liquidity sweeps, displacement, Fair Value Gaps, premium/discount.

**Why this is a problem:** Spitale & Germani 2025 (Science Advances) showed that when LLMs are given a SOURCE FRAME (a narrative identity), they systematically adjust reasoning to match the frame rather than the evidence. Turpin et al. 2023 (NeurIPS) showed LLMs will RATIONALIZE decisions using whatever framework is provided, even when the framework has nothing to do with the actual computation.

**Specific to GTOS:** The AI's job is geometric — "is price at a zone that statistically continues?" That's a spatial/statistical question. But the SMC framing invites NARRATIVE reasoning: "institutions are accumulating here, smart money is engineering liquidity, this is a mitigation play." This narrative has ZERO predictive power — the edge is mechanical stop-cascade, not "institutional intention." The narrative may be causing the AI to:
- Accept weak zones that "fit the narrative" (false positives)
- Reject strong zones that "don't fit the story" (false negatives)
- Overthink via CoT reasoning about "why smart money would do this"

**The test (T2b Exp 4):** Replace ALL SMC language with neutral statistical terms. "Order Block" → "pre-break opposing candle zone." "Liquidity sweep" → "stop-cluster activation." Keep all rules functionally identical. Compare WR.

**Expected outcome:** Neutral framing should be equal or better. If SMC framing actually helps (unexpected), it means the narrative provides structural guidance the AI can't get from geometry alone.

### Chain 3: Why the XGBoost Test Is Existential

**The mechanism:** Extract 30+ features from the AI's own decision JSON + MSO text. Train XGBoost to predict WIN/LOSS among CANDIDATE trades. Compare to the LLM's 65% WR.

**Why this matters:** The LLM costs ~$60/month and processes ~4000 tokens per evaluation. If a free XGBoost model achieves the same accuracy using features the LLM ALREADY computes (confidence, H4 alignment, sweep detection, displacement ratio, zone fib%, etc.), then the LLM is just an expensive feature-extraction step + a mediocre classifier on top.

**The reasoning chain:**
1. Test A rerun showed AI adds ~0pp to entry WR over mechanical OB entries → AI doesn't improve WHERE we enter
2. L2 literature shows LLMs are mediocre classifiers on tabular data (Hegselmann et al. 2023) → If the problem is tabular classification, the LLM loses
3. BUT: The LLM does spatial reasoning (multi-timeframe alignment, zone quality assessment) that PRODUCES the features XGBoost uses → The LLM might be irreplaceable as a feature extractor even if replaceable as a classifier
4. TabPFN (Hollmann et al. 2023) outperforms XGBoost at n<1000 with zero hyperparameter tuning → If even TabPFN matches 65% WR, the LLM is definitively overhead

**Decision tree after T2a:**
- XGBoost < 55%: Outcomes are unpredictable from extracted features. LLM adds value via reasoning we can't capture as features. Keep and optimize.
- XGBoost 55-62%: Features have signal but LLM adds 3-10pp via reasoning. Worth optimizing the LLM (T2b matters).
- XGBoost ≥ 62%: LLM is overhead. Replace with XGBoost classifier + keep LLM only for feature extraction (or replace feature extraction with rules-based extraction too).

### Chain 4: Why Gold Needs Session-Specific ATR

**The mechanism:** Gold (XAUUSD) has documented W-shaped intraday volatility (Ibikunle 2018): London open HIGH, pre-NY moderate, NY open HIGHEST, overlap declining, Asian LOW. A single ATR(14) smooths across all sessions.

**Why uniform ATR fails for gold specifically:** The L1 search found gold has ξ=0.35 (GPD tail index) — 6.2× more 3σ events than Gaussian. This fat-tailedness is NOT uniform across sessions. NY session produces the largest moves (COMEX futures overlap, institutional flow). Using uniform ATR for SL sizing during Asian session (low vol) means SL is too wide → unnecessary risk. Using it during NY means SL might be too tight → stopped out on normal session volatility.

**Why gold and NOT FX:** FX pairs (GBPUSD, USDJPY) have ξ=0.16-0.22 — much thinner tails. Their intraday vol pattern is flatter (not W-shaped). The session-specific ATR is a gold-specific microstructure feature, not a universal improvement.

**Implementation consequence (I1):** Session ATR is gated on `symbol == "XAUUSD"`. Other instruments keep uniform ATR(14). If session ATR shows ρ > 0.05 with outcomes after 50 trades, it proves the hypothesis. If not, remove to save tokens.

### Chain 5: Why Entry Precision Is a Dead End (for now)

**The data reality discovered in T1:** The batch system enters ABOVE H1 OBs (zone-relative position > 0), not within them. This means the AI is identifying the zone, then waiting for a pullback retest from above, not entering at the zone boundary. Entry precision within the zone is irrelevant because entries aren't IN the zone.

**Why T1 is "inconclusive" not "dead end":**
- n=14 per quartile after splitting 121 trades into 4 bins → statistical power is ~30% for a 10pp effect
- The directional signals ARE consistent with literature: wide SL (>2.1× ATR) and wide TP (R:R > 4.0) both underperform, suggesting the AI oversizes some trades
- With 300+ trades these signals might reach significance — they're worth monitoring, just not actionable yet

**What this means for the pipeline:** Don't write more entry engineering prompts until n > 300 live trades. The T1 findings go into a "monitor and revisit" bucket. Meanwhile, the L3 search for frequency improvements is more impactful — if we can get 30-40 trades/month instead of 17, the entry engineering questions will reach power faster.

### Chain 6: Why Confidence Is Dead and What Replaces It

**The data:** 98% of CANDIDATE decisions get confidence_score=80. The scoring rubric (Baseline 70 + modifiers) has too narrow a range and the AI learned to anchor at 80. One verified CANDIDATE had confidence=85 (rare deviation).

**Why this happened:** The prompt asks for confidence 0-100 but the rubric gives a 70 baseline with +5/+10/-5/-10 modifiers. Maximum achievable = ~95, minimum = ~55. The AI quickly learns that "if I'm making it CANDIDATE, I already believe in it, so confidence is high" — it's post-hoc rationalization, not calibration.

**What replaces it:** Self-consistency agreement rate (T2b Exp 5). Run 3 evaluations at temperature=0.6. If 3/3 agree CANDIDATE → high confidence (analogous to 85+). If 2/3 agree → moderate (analogous to 70-75). This is EXTERNALLY measured, not self-reported, so it can't be gamed by the AI. Wang et al. 2023 (ICLR) showed this reliably improves calibration. Cost: 3× API calls. Adaptive consistency (Aggarwal 2023) reduces to ~2.2× average by stopping after 2 if they agree.

### Chain 7: The Frequency-Quality Tradeoff (L3's Core Question)

**Current state:** 10.3% CANDIDATE rate × ~200 evaluated setups/month × 65% WR = ~17 trades/month. Kelly optimal at this WR is f*=4% but we run at 2% because we need sample size to confirm edge persistence.

**The math:** At 17 trades/month × 2% risk × 0.20R expectancy = 6.8% monthly growth. If we could increase to 30 trades/month without diluting WR below 60%, growth becomes 12% monthly — enough to pass FTMO in ~6 weeks vs current ~12 weeks.

**Where frequency could come from (L3's job to find evidence):**
1. **Recover rejected days** (Q-0.1): D1 "unclear" rejects ~51% of days. If a quantitative rule recovers 20% of those → +10% frequency
2. **Replace D1 pre-screen with HMM** (Q-0.3): Real-time regime detection might identify trading opportunities that "D1 unclear" misses
3. **Better swing detection** (Q-2.1): Current algorithm might miss valid BOS events → more OB opportunities
4. **More zone types** (Q-2.3-Q-2.9): S/R at round numbers, FVG fill, PDH/PDL sweeps — each validated type adds zones

**The constraint:** Any frequency increase MUST show the new trades maintain WR ≥ 60% (roughly breakeven for FTMO at 2% risk). A frequency increase that drops WR below 55% is net negative.

---

## DATA ARCHITECTURE (for reviewing T2a/T2b results)

### Batch data structure
```
knowledge_base_backtest/batch_api/
├── XAUUSD_london_full_prompts.json    # List of evaluation records
├── XAUUSD_london_raw_results.json     # Dict of AI responses
├── XAUUSD_ny_full_prompts.json
├── XAUUSD_ny_raw_results.json
├── US30_london_full_prompts.json
└── ... (one pair per instrument × session)
```

### Full prompts structure
```python
[
  {
    "custom_id": "xau_ldn_20251015_0715",
    "date": "2025-10-15",
    "candle_time": "2025-10-15 07:15:00",
    "kill_zone": "london",
    "prompt": {
      "system": [{"type": "text", "text": "You are an institutional...", "cache_control": {...}}],
      # ↑ IMPORTANT: system is a LIST of dicts, extract [0]['text'] for the actual prompt
      "user_message": "## Market State Object\n...",  # Full MSO with dynamic context
      "model": "claude-sonnet-4-20250514",
      "temperature": 0,
      "max_tokens": 4096
    }
  },
  ...
]
```

### Raw results structure
```python
{
  "2025-10-15_london_0715": {
    "action": "CANDIDATE",  # or "NO_TRADE"
    "direction": "LONG",
    "entry_price": 2645.50,
    "stop_loss": 2638.20,
    "take_profit_1": 2660.30,
    "take_profit_2": 2668.50,
    "take_profit_3": 2675.00,
    "risk_reward_ratio": 2.5,
    "setup_grade": "A",
    "confidence_score": 80,
    "framework": "ob_retest",
    "reasoning": {
      "daily_bias": {"direction": "bullish", "basis": "..."},
      "h4_alignment": {"aligned": true, "structure": "..."},
      "h1_setup": {"zone": "...", "quality": "...", "fib_pct": 62.5},
      "m15_trigger": {"type": "...", "confirmed": true},
      "risk_factors": ["...", "..."]
    }
  },
  ...
}
```

### Trade index structure
```python
# knowledge_base/index/_trade_index.json
{
  "trade_001": {
    "outcome": "WIN",  # WIN, LOSS, or BE
    "r_multiple": 2.1,
    "entry_time": "2025-10-15T07:30:00",
    "exit_time": "2025-10-15T09:45:00",
    "symbol": "XAUUSD",
    "direction": "LONG",
    ...
  }
}
```

### Extractable features for T2a (30+)
From AI decision JSON:
- confidence_score (int, 0-100)
- reasoning.daily_bias.direction (str → binary)
- reasoning.h4_alignment.aligned (bool)
- reasoning.h1_setup.fib_pct (float)
- reasoning.h1_setup.zone quality indicators
- reasoning.m15_trigger.type and confirmed status
- risk_reward_ratio (float)
- setup_grade (A/B/C → ordinal)
- len(reasoning.risk_factors) (int)

From MSO text (requires parsing):
- Number of unmitigated OBs (count from "Unmitigated OBs:" section)
- Number of unfilled FVGs
- ATR value
- Average body size
- Sweep count
- Structure direction (bullish/bearish/unclear)
- Premium/discount position

---

## PROMPT ENGINEERING METHODOLOGY

Every prompt written in this pipeline follows this structure:

### Structure Template
```
1. Header: Who (agent type), When (date), Basis (what research informed it)
2. Overview: What the prompt accomplishes, numbered items
3. Data Discovery: What files exist, what structure, what's available
4. Detailed Method: Per-section with code snippets, formulas, expected outputs
5. Decision Gates: Pre-committed criteria for each possible outcome
6. Output Files: Exact save paths
7. Constraints: Hard rules the execution agent must follow
8. Prerequisites: pip installs, codebase reading, tool requirements
9. Pressure Test Log: Issues found and fixed BEFORE delivery
```

### Quality Rules
- **Bonferroni correction** on all multi-test batteries (p < 0.05/n)
- **Wilson CIs** for proportions (never Wald/normal approximation)
- **Bootstrap CIs** (seed=42, n=10000) for means
- **Leave-one-out CV** when n < 150 (too few for stratified k-fold on WIN/LOSS)
- **Stratified 5-fold CV** when n > 300
- **Pre-committed decision gates** — decide BEFORE seeing data what constitutes pass/fail
- **Practical significance** threshold alongside statistical: |ΔWR| > 3pp or |ΔR| > 0.10R
- **Per-instrument analysis** mandatory where data allows (gold differs from FX)
- **Shadow logging** for 30+ observations before promoting any feature to live gate

### Pressure Testing Protocol
Before delivering any prompt:
1. Switch to critic/adversarial mode
2. Ask: "What would make this prompt produce garbage output?"
3. List all issues found (data availability, edge cases, dependency problems, ambiguity)
4. Fix each issue
5. Add the issues + fixes to the Pressure Test Log section at the bottom

---

## DECISION FRAMEWORK FOR REVIEWING RESULTS

When execution agents return results, apply this triage:

| Signal | Action |
|--------|--------|
| p < Bonferroni threshold + practical significance met | IMPLEMENT — write I-prompt |
| p < Bonferroni threshold + practical significance NOT met | LOG — statistically real but too small to matter |
| p > Bonferroni but < 0.05 + strong directional signal | DEFER — need more data, add to shadow logging |
| p > 0.05 | KILL — no evidence, remove from pipeline |
| Null result (no effect found) | DOCUMENT — null results are findings. "X doesn't work" is valuable. |
| Paper quality concern (predatory journal, no OOS, simulated data) | DOWNWEIGHT — don't act on it alone, need corroboration |
| Hallucinated paper (author doesn't exist, journal fabricated) | FLAG — report to CEO, exclude from analysis |

---

## FILES YOU NEED TO KNOW ABOUT

### Research pipeline files
| File | Purpose |
|------|---------|
| `research/academic_pipeline/phase1_priority_a_papers.md` | 69 papers (Priority A search) |
| `research/academic_pipeline/phase1_entry_engineering_papers_v1.md` | 51 papers (L0) |
| `research/academic_pipeline/phase1_feature_engineering_papers_v1.md` | 57 papers (L1) |
| `research/academic_pipeline/phase1_ai_evaluation_papers_v1.md` | 96 papers (L2) |
| `research/academic_pipeline/results/T1_entry_engineering_results_v1.md` | T1 results stub |
| `research/academic_pipeline/T1_entry_engineering_analysis.py` | T1 full analysis script |
| `research/academic_pipeline/data/entry_engineering_dataset.csv` | 121 matched trades |
| `.context/03_analysis/research_execution_plan_113q.md` | Master 113Q roadmap |

### Prompts ready for execution
| File | Status |
|------|--------|
| `research/academic_pipeline/prompts/T2a_ai_evaluation_diagnostics.md` | READY — execute next |
| `research/academic_pipeline/prompts/T2b_ai_shadow_api_experiments.md` | READY — after T2a |
| `research/academic_pipeline/prompts/I1_feature_engineering_implementation.md` | READY — parallel with T2a |
| `research/academic_pipeline/prompts/L3_edge_optimization_search_prompt.md` | READY — parallel with T2a |

### Batch data (for T2a/T2b)
| Path | Content |
|------|---------|
| `knowledge_base_backtest/batch_api/*_full_prompts.json` | Full MSO + system prompt per evaluation |
| `knowledge_base_backtest/batch_api/*_raw_results.json` | AI decision JSON per evaluation |
| `knowledge_base/index/_trade_index.json` | Trade outcomes |

### Key source files (for I1)
| Path | Key Sections |
|------|-------------|
| `src/components/market_state.py` | Where CLV/BVC/session ATR computation goes |
| `src/components/market_state_models.py` | Pydantic models for new fields |
| `src/prompts/primary_analyzer_prompt.py` | `_format_tf()` line 340, `build_dynamic_context()` line 432 |
| `src/components/data_ingestion.py` line 277 | Volume field source |

---

## WHAT THE NEXT SESSION SHOULD DO

### Immediate (when user is ready)
1. **Dispatch T2a, I1, L3** to separate execution agents (parallel)
2. **Wait for T2a results** — this is the critical decision point
3. **Review L3 results** when they come back — validate papers, identify testable hypotheses
4. **Review I1 implementation** — verify tests pass, features compute correctly

### After T2a results
5. **If XGBoost < 58% WR:** Dispatch T2b immediately. LLM is irreplaceable, optimize it.
6. **If XGBoost 58-62%:** Dispatch T2b for directional signal. Also start writing T3 (MI audit + displacement threshold tests).
7. **If XGBoost ≥ 62%:** T2b is informational only. Pivot to feature engineering (does adding CLV/BVC/session ATR help the model?) and frequency optimization (L3 findings).

### Ongoing pipeline
8. **Write L4 prompt** (Wave 2C: SL, Exit, and Decay questions — Q-6.3, Q-6.5, Q-6.6, Q-0.4, Q-0.5, Q-0.2)
9. **Write T3 prompts** based on L1/L2 findings not yet tested: MI audit, displacement magnitude threshold, DSR computation
10. **Continue through L5-L9** per 113Q execution plan

---

## COMMON PITFALLS TO AVOID

1. **Don't trust handoff 09's "Starting L1" — L1, L2, and T1 are all DONE.** The pipeline has advanced significantly since that handoff was written.
2. **Don't execute prompts yourself.** You write them, the CEO sends them to execution agents in separate terminals.
3. **Don't assume tick volume is in the MSO.** It is NOT. The AI never sees raw volume. I1 adds DERIVED features only.
4. **Don't use GradientBoostingClassifier with class_weight='balanced'** — sklearn's GBC doesn't support this parameter. Use `compute_sample_weight('balanced', y_train)` instead.
5. **Don't claim entry engineering is a "dead end"** — it's INCONCLUSIVE at current n. T1 is underpowered.
6. **Don't forget the system prompt in batch data is wrapped in a list** — extract `prompt.system[0]['text']`.
7. **Don't add scipy as a new dependency** for one function (BVC). Use pure-Python norm CDF approximation.
8. **Don't apply gold-specific findings to other instruments** without checking. Gold ξ=0.35 vs FX 0.16-0.22.
9. **Don't skip the pressure test.** Every prompt gets adversarial review before delivery.
10. **WF-1 is CANCELLED.** There is no code freeze. Implement validated changes directly.

---

*Handoff generated: April 11, 2026 (late evening)*
*This session: Reviewed L1+L2+T1 outputs, wrote 4 execution prompts (T2a, T2b, I1, L3), added prerequisites to all*
*Total papers covered: 273+ across 4 search sessions*
*Next action: Dispatch T2a + I1 + L3 to execution agents (parallel)*
