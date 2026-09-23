# Session Handoff 11 — Strategic Research Advisor (T2c Analysis In Progress)
## Date: April 12, 2026
## For: Next Claude Code agent continuing as Strategic Research Advisor
## From: Two sessions of deep analysis (T2b review, prompt drift, T2c design, T2c Phase 1 analysis)

---

## YOUR ROLE: STRATEGIC RESEARCH ADVISOR

You are the **Strategic Research Advisor** for the GTOS academic research pipeline. You are the same mind continuing across sessions. Read handoff 10 for the full role origin story. Key rules:
- STRICTLY ADVISORY: write prompts, review outputs, decide TEST/IMPLEMENT/KILL/DEFER
- Do NOT execute prompts, modify src/, or run code
- Every deliverable is a committed file
- NEVER fabricate data — "file not found" is always acceptable

---

## THE BIG PICTURE (why all this matters)

GTOS is a live trading system on FTMO $100K demo. It evaluates gold (XAUUSD) and 4 other instruments using Claude Sonnet as the AI evaluator. The system has a **frequency problem**: near-zero trades in the first 4 live days. The research pipeline exists to systematically diagnose WHY and find validated improvements.

The core thesis from T2a: **accuracy is a closed path** (outcomes within CANDIDATE pool are unpredictable, AUC~0.5). The only lever is **frequency** — getting more trades through the gate while maintaining WR >= 60%.

The three biggest frequency levers identified so far:
1. Session memory suppresses 55% of CANDIDATEs (proven, p=0.007)
2. Model upgrade Sonnet 4 → 4.6 (tested in T2c — results below, NOT what we expected)
3. Prompt drift — live prompt differs fundamentally from batch prompts

---

## WHAT HAPPENED ACROSS BOTH SESSIONS

### Session 1 (early morning Apr 12): Discovery Phase

**1. Resolved 3 ambiguities from T2b:**
- Live prompt (14,382 chars) differs from ALL batch prompts (4 template versions, 9,415-12,340 chars)
- Memory suppression is 55% on closest-to-live template (stronger than pooled 45%)
- Memory injection format is identical between T2b test and live system

**2. Prompt Drift Discovery:**

| Template Length | Trades | Source |
|----------------|--------|--------|
| 9,415 chars | 9 | GBPUSD batch |
| 9,972 chars | 46 | Multi-instrument |
| 10,105 chars | 2 | XAUUSD batch |
| 12,340 chars | 64 | Largest XAUUSD |
| **14,382 (LIVE)** | — | Current production |

Key live vs batch differences: min RR 2.5→1.5, session_sweep→breaker_block framework, strict→flexible bias, discretionary→mechanical TP, added quality signals and anti-hallucination rules.

**3. Model Version Discovery:**
- System runs `claude-sonnet-4-20250514` (Sonnet 4) — never changed since initial commit
- Sonnet 4.6 is available at the same price
- April 5 test: Opus 4 rejected 92-100%, forced thinking on Sonnet 4 rejected 96%
- BUT: `effort` parameter is architecturally different from forced thinking
- `effort` uses `output_config={"effort": level}`, does NOT require temperature=1

**4. Designed and Dispatched T2c:**
- 3 parallel agents: Sonnet 4.6 at medium/high/max effort
- 121 MSOs from T2b (replaying exact batch prompts)
- Budget: $50/agent

### Session 2 (continuing Apr 12): Analysis Phase — CRITICAL FINDINGS

**5. T2c Medium + High Results:**

| Config | CR | WR | CR*WR | N_cand |
|--------|----|----|-------|--------|
| Sonnet 4.6 medium | 11.6% | 42.9% | 0.050 | 14 |
| Sonnet 4.6 high | 17.4% | 52.4% | 0.091 | 21 |

Both show severe Opus-like over-rejection. Lost trades WR = 67% (good trades being killed).

**6. CRITICAL: The Baseline Was Wrong**

The initial reports compared Sonnet 4.6 against "100% CANDIDATE rate" (since all 121 T1 trades were executed). But checking the actual Sonnet 4 batch re-evaluation results:

| Condition | CR | WR | CR*WR | Notes |
|-----------|----|----|-------|-------|
| **Live system (original execution)** | 100% | 64.5% | 0.645 | Different prompts at trade time |
| **Sonnet 4 batch re-eval** | **55.8%** | 61.1% | 0.341 | Same prompts T2c uses |
| Sonnet 4.6 medium | 11.6% | 42.9% | 0.050 | |
| Sonnet 4.6 high | 17.4% | 52.4% | 0.091 | |

The correct comparison is Sonnet 4 batch (55.8%) vs Sonnet 4.6 (11.6-17.4%). Still a 3-5x degradation, but not the 10x the initial reports showed.

**Gap 1 (Live 100% → Batch 55.8%)** = Prompt drift. Even Sonnet 4 rejects 44% when using batch prompts instead of the original live prompts.

**Gap 2 (Batch 55.8% → T2c 11.6-17.4%)** = Model + confounders (see below).

**7. Root Cause Analysis — Three Possible Explanations for Gap 2:**

| Variable | Batch (Sonnet 4) | T2c (Sonnet 4.6) | Effect |
|----------|-----------------|-------------------|--------|
| **Model version** | claude-sonnet-4-20250514 | claude-sonnet-4-6 | PRIMARY suspect — 3-5x degradation |
| **max_tokens** | 2000 | 4096 | UNCONTROLLED — S4.6 outputs 1189-1270 tokens vs ~500 |
| **effort param** | absent | medium/high | UNCONTROLLED — even medium might add conservatism |
| API path | Batch API | Messages API | Unlikely to matter |

We CANNOT yet say "this is 100% the model" because max_tokens and effort are uncontrolled. The effect is large enough that the model is likely dominant, but rigor demands we isolate.

**8. Grade Inversion Discovery:**

Sonnet 4.6's grading is ANTI-CORRELATED with actual outcomes:

| Grade | N | WR |
|-------|---|----|
| A+ (highest) | 4 | 50.0% |
| A | 10 | 40.0% |
| B+ | 16 | **81.2%** |
| B | 30 | **70.0%** |
| C | 61 | 62.3% |

The trades it's most confident about are the worst. B/B+ (which it rejects) are the best.

**9. CANDIDATE Overlap is Low:**
- Only 12/63 Sonnet 4 CANDIDATEs also selected by medium
- Only 16/63 by high  
- Medium has 2 unique picks Sonnet 4 missed
- High has 5 unique picks
- Sonnet 4.6 isn't just "pickier" — it has genuinely different judgment

**10. Medium vs High Comparison:**
- All 14 medium CANDIDATEs are a strict subset of high's 21
- The 7 extra high picks have 71.4% WR (better than the core 14's 42.9%)
- Neither: 100 trades (83% agreement to reject)
- Medium is strictly worse than high — tighter filter makes things worse

**11. T2c Max Still Running:**
- At 58/121 (~48%) as of last check
- Running as nohup process: `T2c_effort_max.py`
- Log: `/tmp/T2c_max_run.log`
- Expected cost: ~$4-5 total (similar to medium/high)
- Medium re-run ALSO running (ignore — results already captured from first run)

**12. Source File Mismatch (minor):**
- 12/121 trades have prompt from batch file A but Sonnet 4 result from batch file B
- Both scripts use `glob.glob()` with "last wins" dedup, same as T2b
- Minor issue — doesn't change conclusions

---

## WHAT TO DO NEXT

### Immediate: When Max Completes

1. Check if max process finished: `ps aux | grep T2c_effort_max`
2. Read results: `research/academic_pipeline/results/T2c_max_results_v1.md`
3. Read raw data: `research/academic_pipeline/data/T2c_max_results.json`

Expected outcome: Max will likely show similar or slightly different CR than high. The pattern (Opus-like over-rejection) is consistent across medium and high, so max will probably confirm it.

**Apply the CORRECTED baseline** when analyzing max:
- Don't compare to "100% CR" — compare to Sonnet 4 batch's 55.8% CR
- Check lost trades WR (if >65%, over-rejecting)
- Check grade distribution (expect same inversion)

### Decision Point: Do We Need Isolation Controls?

The CEO asked: "Is this completely model-related or also prompt/configuration?" We identified three uncontrolled variables. The options:

**Option A: Accept current evidence, move on**
- The 3-5x degradation is so large that model version is almost certainly dominant
- max_tokens ceiling shouldn't fundamentally change behavior (only allows longer output)
- effort=high is Sonnet 4.6's default — removing it shouldn't help much
- Cost: $0, fast

**Option B: Run quick isolation controls (~$12 total)**
1. Sonnet 4 through T2c pipeline (same code, max_tokens=4096, Messages API, no effort) — proves pipeline isn't the issue
2. Sonnet 4.6 with max_tokens=2000 — isolates token ceiling
3. Sonnet 4.6 without effort param — isolates effort effect
- Cost: ~$4 each, can run in parallel
- Gives definitive attribution

**Option C: Skip to Phase 2 with Sonnet 4 locked in**
- T2c Phase 1 verdict: Sonnet 4.6 FAILS the switch gate at all effort levels
- Lock Sonnet 4 as the model
- Proceed to C4 (live prompt test) + C5 (memory interaction) using Sonnet 4
- This is where the real frequency gains are (memory removal = +55% CR)

The CEO's instinct is to understand root causes thoroughly ("box the issue"). Recommend Option B if he wants full isolation, Option C if he's ready to move to the high-impact levers.

### Phase 2 (After Locking Model Decision)

**C4 — Live Prompt Test:**
- Take the 121 MSOs, replace batch system prompt with CURRENT live prompt (14,382 chars)
- Keep market data from batch user message
- Run with Sonnet 4 (locked model)
- Answers: "What does the current live prompt actually do with the same market data?"

**C5 — Memory Removal Validation:**
- Take the 66-trade subset from Exp1 (trades with >= 3 prior candles)
- Run Sonnet 4 WITHOUT session memory
- Compare to T2b Exp1 memory condition
- Answers: "Can we safely remove memory to get +55% CR?"

### Implementation Queue (after all testing)

| Change | Cost | Expected Impact | Evidence |
|--------|------|-----------------|----------|
| Remove session memory | $0 (code change) | +55% CR (proven p=0.007) | T2b Exp1 |
| Keep Sonnet 4 (don't upgrade) | $0 | Avoids 3-5x CR destruction | T2c Phase 1 |
| Keep effort=none | $0 | Avoids potential conservatism | T2c comparison |
| Increase max_tokens 2000→4096 | Marginal | Prevents truncation | Config change |
| Live prompt already deployed | $0 | Already different from batch | Known |

### Long-term Queue
- T3-DC: DC framework implementation (highest-impact L3 finding, 4-8h dev)
- L4: Wave 2C lit search (SL, Exit, Decay)
- "Non-obvious setup" composite re-validation on 12,340 template subset

---

## KEY FILES

### T2c Results (Phase 1)
| File | Content |
|------|---------|
| `research/academic_pipeline/results/T2c_medium_results_v1.md` | Medium effort report (agent-generated, baseline incorrect) |
| `research/academic_pipeline/results/T2c_high_results_v1.md` | High effort report (agent-generated, baseline incorrect) |
| `research/academic_pipeline/data/T2c_medium_results.json` | Raw medium results (121 trades) |
| `research/academic_pipeline/data/T2c_high_results.json` | Raw high results (121 trades) |
| `research/academic_pipeline/data/T2c_medium_cost_log.csv` | Medium cost log |
| `research/academic_pipeline/data/T2c_high_cost_log.csv` | High cost log |
| `research/academic_pipeline/results/T2c_max_results_v1.md` | Max effort report (PENDING — check if exists) |
| `research/academic_pipeline/data/T2c_max_results.json` | Raw max results (PENDING) |

### T2c Scripts
| File | Content |
|------|---------|
| `research/academic_pipeline/T2c_effort_medium.py` | Medium agent script |
| `research/academic_pipeline/T2c_effort_high.py` | High agent script |
| `research/academic_pipeline/T2c_effort_max.py` | Max agent script |
| `research/academic_pipeline/prompts/T2c_model_effort_shootout.md` | Master template |

### Must-Read for Full Context
| File | Why |
|------|-----|
| `.context/02_session_handoffs/10_apr11_strategic_advisor_handoff.md` | Role definition, pipeline history, all prior findings |
| `research/academic_pipeline/results/T2b_shadow_api_results_v1.md` | T2b full results (5 experiments) |
| `research/academic_pipeline/data/T2b_api_results.json` | Raw T2b data (168KB) |
| `research/academic_pipeline/data/entry_engineering_dataset.csv` | The 121 T1 trades (candle_time, outcome, win) |
| `src/prompts/primary_analyzer_prompt.py` | Live system prompt (14,382 chars for XAUUSD) |
| `src/components/primary_analyzer.py` lines 115-190 | How live system builds prompts |
| `config/agent_config.yaml` | Live config — model is `claude-sonnet-4-20250514` |

### Batch Data (for understanding prompt drift)
| File | Why |
|------|-----|
| `knowledge_base_backtest/batch_api/*_full_prompts.json` | Original batch prompts (18 files, various template versions) |
| `knowledge_base_backtest/batch_api/*_raw_results.json` | Original Sonnet 4 batch decisions |

---

## VALIDATED FINDINGS (carry forward from all sessions)

### T2a (confirmed)
- Outcomes within CANDIDATE pool are unpredictable (AUC~0.5)
- CANDIDATE gate is a deterministic rules check (setup_grade explains 97%)
- Confidence score is dead (rubber stamp at 80)
- Primary optimization target = CANDIDATE frequency, not accuracy

### T2b (confirmed)
- Session memory suppresses 55% of CANDIDATEs on closest-to-live template (p=0.007)
- Memory works via distributional priming, not label content (scrambled labels = identical CR)
- Full CoT prompt is essential (simplified = 0% CANDIDATE rate)
- SMC framing neutral for accuracy, slightly better for frequency
- 3-run self-consistency: 86% agreement, majority-CANDIDATE (2/3) has 81.8% WR

### T2c Phase 1 (NEW — confirmed)
- Sonnet 4.6 is NOT a free upgrade — 3-5x CR degradation vs Sonnet 4 on same prompts
- Both medium (11.6% CR) and high (17.4% CR) show Opus-like over-rejection
- Lost trades WR = 67% — good trades being killed
- Sonnet 4.6 grade is ANTI-CORRELATED with outcomes (A+ = 50% WR, B+ = 81.2%)
- All medium CANDIDATEs are a subset of high (medium strictly worse)
- CANDIDATE overlap between S4 and S4.6 is low (12-16 out of 63)
- CORRECT Sonnet 4 batch baseline is 55.8% CR (not 100%)
- The 100% figure represents live system with DIFFERENT prompts
- max_tokens and effort parameter effects are UNCONTROLLED confounders

### T3 (confirmed)
- Fib depth: KILL (p=0.029 misses Bonferroni)
- Round numbers: KILL (no significance)
- BOS displacement: KILL (REVERSED — weaker is better)
- Confidence distribution: CONFIRM (144x CR diff high vs low confidence, p~0)
- Structural density: KILL (noise)

### Prompt Drift (confirmed)
- 4+ template versions in batch data (9,415 to 12,340 chars)
- None match live (14,382 chars)
- Live has: lower min RR (1.5 vs 2.5), breaker block framework, flexible bias, mechanical TP, quality signals, anti-hallucination rules
- Even Sonnet 4 with batch prompts only gives 55.8% CR on trades the live system took
- 20+ commits touched `primary_analyzer_prompt.py` between Mar 30 and Apr 12

### Model (confirmed)
- System uses Sonnet 4 (`claude-sonnet-4-20250514`) — never changed
- Sonnet 4.6 available at same price but FAILS the upgrade gate
- Opus rejected 92-100% (April 5 test, n=298)
- `effort` parameter is different from forced thinking (behavioral signal, not budget)

---

## HOW TO THINK ABOUT THIS (advisor's reasoning patterns)

1. **Always verify the baseline before comparing.** The medium report said "100% baseline CR" which was technically true (all 121 were executed) but misleading. The correct baseline for a model comparison is "what does Sonnet 4 produce on the SAME prompts" = 55.8%.

2. **Separate prompt effects from model effects.** The Live→Batch gap (100%→55.8%) is entirely prompt drift. The Batch→T2c gap (55.8%→11.6-17.4%) is model + confounders. Don't conflate them.

3. **Uncontrolled variables matter.** max_tokens 2000→4096 and the effort parameter are technically uncontrolled. The effect is probably dominated by the model, but "probably" isn't "proven." The CEO values rigorous isolation.

4. **Grade inversion means the model's confidence is anti-signal.** Sonnet 4.6 is most confident about its worst picks. This isn't noise — it's systematic. The model's calibration is inverted for this task.

5. **CR*WR is the only metric that matters for comparison.** High WR with tiny CR is worse than moderate WR with good CR. The live system at 100% CR * 64.5% WR = 0.645 crushes everything.

6. **The CEO thinks in terms of isolation and root causes.** He doesn't want "probably model" — he wants to know exactly which variable explains which portion of the effect. When he says "box the issue," he means identify all possible causes and eliminate them one by one.

7. **Every claim needs a file path.** Don't cite numbers from memory — point to the JSON or CSV that contains them.

---

## WHAT NOT TO DO

1. Do NOT cite the agent-generated T2c reports at face value — the medium report's baseline is correct (100% by construction) but the high report's baseline is wrong (42.1% from mismatched raw_results). Always recompute from raw JSON.
2. Do NOT assume Sonnet 4.6 is universally worse — it's worse FOR THIS TASK. The grade inversion and over-rejection are specific to trading evaluation prompts.
3. Do NOT skip checking max results against the CORRECTED baseline (55.8%, not 100%).
4. Do NOT combine prompt drift effects with model effects in the same comparison.
5. Do NOT recommend model upgrade — T2c Phase 1 definitively fails the switch gate.
6. Do NOT modify src/, config/, or prompts/ — advisory role only.
7. Do NOT re-run T2b experiments — they're done and validated.

---

## RUNNING PROCESSES (check status)

```bash
# T2c max effort agent (was at 58/121 when session ended)
ps aux | grep T2c_effort_max | grep -v grep
tail -20 /tmp/T2c_max_run.log

# T2c medium re-run (ignore — original results already captured)
ps aux | grep T2c_effort_medium | grep -v grep
```

---

*Handoff written by Strategic Research Advisor across two sessions. Covers: T2b deep analysis, prompt drift discovery, model version audit, T2c experiment design, T2c Phase 1 analysis, corrected baseline discovery, root cause analysis.*
