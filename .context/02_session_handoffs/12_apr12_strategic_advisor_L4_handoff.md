# Session Handoff 12 — Strategic Research Advisor (L4 Complete, Prompt Ablation Ready)
## Date: April 12, 2026
## For: Next Claude Code agent continuing as Strategic Research Advisor
## From: Session 3 — deployed winning config, completed L4 literature search, foundation analysis, prompt ablation script ready to run

---

## YOUR ROLE: STRATEGIC RESEARCH ADVISOR

You are the **Strategic Research Advisor** for the GTOS academic research pipeline. You are the same mind continuing across sessions. Read handoff 10 for the full role origin story. Key rules:
- STRICTLY ADVISORY: write prompts, review outputs, decide TEST/IMPLEMENT/KILL/DEFER
- Do NOT execute prompts, modify src/, or run code UNLESS implementing validated changes with CEO approval
- Every deliverable is a committed file
- NEVER fabricate data — "file not found" is always acceptable

---

## WHAT HAPPENED THIS SESSION

### 1. Opus 4.6 Model Test — KILLED
Opus 4.6 tested on 121 MSOs: CR=19%, WR=61%, CR*WR=0.116, cost=$18.67.
**Sonnet 4.6 max is the winner:** CR=38%, WR=69.6%, CR*WR=0.265.
Opus is 2x cost, half the performance. Definitively ruled out.

### 2. Full Deployment of Winning Config to Live System
Deployed Phase 2A v1 scored evaluation prompt to production. Changes:
- **`config/agent_config.yaml`**: primary_model → `claude-sonnet-4-6`, primary_effort → `"max"`, session_memory_enabled → `false`, api_timeout → 60s
- **`src/prompts/primary_analyzer_prompt.py`**: Complete prompt replacement — old binary 7-gate → scored Q1-Q7 evaluation with CALIBRATION section, DECISION INTEGRITY, tolerance bands
- **`src/components/primary_analyzer.py`**: effort parameter wired via `output_config={'effort': 'max'}`, model default to sonnet-4-6, timeout to 60s
- **`src/components/orchestrator.py`**: Session memory gated on `session_memory_enabled` config flag (lines ~445, ~467)
- **Tests updated**: test_breaker_blocks, test_cross_instrument, test_prelaunch_audit, test_prompts — all updated for new prompt

### 3. Session Memory Disabled
T2b proved session memory suppresses 55% CR (p=0.007). Disabled via config flag. Orchestrator gated on `config.get("session_memory_enabled", True)`.

**Cross-session zone map idea**: CEO proposed tracking unmitigated OBs across sessions as OBJECTIVE structural context (different from session memory which was subjective evaluations). LOW PRIORITY vs prompt optimization — park for later.

### 4. L4 Literature Search — COMPLETE
All 4 clusters searched in parallel (188 papers surveyed, ~135 promoted):
- `phase1_stop_loss_refinement_papers_v1.md` — 42 papers, 28 promoted (Q-5.2 to Q-5.5)
- `phase1_exit_optimization_papers_v1.md` — 62 papers, 41 promoted (Q-6.2, Q-6.5-6.8)
- `phase1_alpha_decay_crowding_papers_v1.md` — 42 papers, 32 promoted (Q-8.2 to Q-8.4)
- `phase1_model_risk_q9_2_3_4_v1.md` — 42 papers, 34 promoted (Q-9.2 to Q-9.4)

### 5. Complete Actionable Items Inventory — 128 Items
**`research/academic_pipeline/L4_all_actionable_items_v1.md`** — Every testable hypothesis from all promoted papers with test methodology.
- Cluster A (SL): 28 items
- Cluster B (Exit): 38 items
- Cluster C (Decay): 37 items
- Cluster D (Model Risk): 25 items

### 6. Trade-by-Trade Diff Analysis (P2A-3 vs P2A-v2)
**`research/academic_pipeline/results/P2A_trade_diff_analysis_v1.md`** — 379 lines, full analysis.

Key findings:
- v2 killed 12 trades that had **83.3% WR** (v1's best picks) → -8.15R regression
- Root cause: Q3 (zone proximity) and Q5 (M15 confirmation) over-strictness in v2
- v2 gained 5 trades with only 40% WR (bad adds)
- **Q-scores are effectively binary within CANDIDATEs** — winners and losers both cluster at 85-90 total. Zero discrimination within the accepted pool.
- **v1's accept/reject boundary is well-calibrated. DO NOT tighten Q3 or Q5.**
- Near-misses (score 45-64) had 50% WR — v1 correctly rejects them.

### 7. $0 Foundation Analysis — COMPLETE
**`research/academic_pipeline/results/L4_foundation_results_v1.md`** — 50 tests from existing data.

**Critical findings that inform prompt optimization:**

| Finding | Result | Implication |
|---------|--------|------------|
| **B36: P(2R\|1R reached)** | **53.2%** | HOLD at 1R is correct. Partial close DESTROYS value. |
| **B4: Winner MFE skewness** | 1.232 (right-skewed) | Big winners exist. Don't truncate with partial close. |
| **B23: IS decomposition** | Reversal cost (62R) > early exit (54R) | Tighter stops marginally more valuable than wider TP |
| **B25: Efficient frontier** | TP=1.0R has highest Sharpe (0.299) | Current 1.5R TP may be suboptimal! TP=1.0R has better risk-adjusted return. |
| **A1: Winner MAE** | Median=0.138R, P80=0.354R | Only 3.8% of winners had MAE >0.8R. SL is well-calibrated. |
| **A3: MAE tail** | GPD shape xi=0.476 (heavy-tailed) | Confirms EVT-based SL sizing would be safer |
| **A6: Tail asymmetry** | MAE xi=0.476, MFE xi=-0.442 | Losses ARE heavier-tailed than gains. Asymmetric risk confirmed. |
| **A7: Vol-regime** | Significant (p=0.047) | High-vol trades need wider SL buffer |
| **A20: Kelly f*** | 38.8% (current 1% = 0.03x Kelly) | Room to increase position size after live validation |
| **MC: FTMO P(pass)** | f=1%: 45.9%, f=1.5%: 63.3%, f=2%: 56.2% | Optimal at 1.5% risk per trade for FTMO pass probability |
| **C1: Formal decay test** | p=0.40 (NOT significant) | Cannot confirm WR decay from 65.6% to 58.5% |
| **C16: Failure clustering** | p=0.60 (INDEPENDENT) | Losses do NOT cluster — random, not cascade |
| **C20: Loss/win asymmetry** | 0.840 (wins > losses) | FAVORABLE: wins are larger than losses |
| **C22: R-multiple trend** | p=0.95 (no trend) | NO significant R decline over time |
| **C31: Decay rate** | 13.8pp/year observed | 14x faster than FX TA baseline — too fast for pure decay, regime effects dominate |
| **C33: Regime decomposition** | Session composition shifts, ATR correlation not significant | WR decline likely driven by data composition, not edge erosion |
| **A8: Round-number SL** | p=0.45 (not significant) | Round-number effects do NOT amplify MAE in our data |
| **A15: Serial correlation** | p=0.08 (marginal) | Trade returns are approximately independent |
| **B24: Late KZ entry** | London late WR=81.2%, NY early WR=58.3% | Entry timing within KZ matters — late London is excellent |
| **B28: MFE vs vol** | Spearman rho=-0.53, p<0.001 | MFE strongly scales with volatility — dynamic TP justified |

### 8. Prompt Ablation Test Script — READY TO RUN
**`research/academic_pipeline/T3_prompt_ablation.py`** — 5 prompt variants ready to test:

| Variant | Name | L4 Item | What It Tests |
|---------|------|---------|---------------|
| A | smc_persona | D10 (reverse) | Add back SMC expert persona (tests if persona hurts) |
| B | no_role | D10 (full) | Remove ALL role framing, just instructions |
| C | checklist | D12 | Factual YES/NO checklist (no judgment framing) |
| D | binary_no_cot | D13 | Minimal no-CoT prompt (System 1 fast thinking) |
| E | fincot_blueprint | D14 | FinCoT rigid step-by-step (1 value per step) |

Run: `python research/academic_pipeline/T3_prompt_ablation.py` (~$25 for all 5, ~$5 each)
Or: `python research/academic_pipeline/T3_prompt_ablation.py C E` (run specific variants)

D17 (ensemble) is computed automatically from results — no extra API calls. All 3-variant combinations are majority-voted and compared.

---

## CEO'S STRATEGIC DIRECTION (CRITICAL — read carefully)

The CEO made a strong directional statement this session. Paraphrased key points:

1. **"We are NOT confident in the current prompt."** Despite v1 being well-calibrated (CR=38%, WR=69.6%), the 65.3% WR on rejected trades means we're leaving money on the table.

2. **"I want ALL actionable items, not top 5."** The CEO wants exhaustive, rigorous testing — not cherry-picked improvements.

3. **Prompt ablation methodology:** Study each prompt change individually. Compare trade-by-trade: what got better, what got worse, what stayed the same. Test ONE change at a time. Stack winning changes. **Do NOT make multiple changes at once.**

4. **"This is not over-engineering — it's delivering a working system."** The CEO explicitly rejected the idea that this level of testing is excessive. Low frequency is the primary problem and the prompt is the primary lever.

5. **Session memory is a separate concept from cross-session zone map.** Disabled session memory (subjective evaluations) is correct. Cross-session OB tracking (objective structural data) is a different idea for later.

---

## CURRENT LIVE SYSTEM STATE

| Parameter | Value | Changed This Session? |
|-----------|-------|----------------------|
| primary_model | claude-sonnet-4-6 | YES (was claude-sonnet-4-20250514) |
| primary_effort | max | YES (new) |
| session_memory_enabled | false | YES (was true implicitly) |
| api_timeout_seconds | 60 | YES (was 30) |
| enabled_frameworks | ["ob_retest"] | No |
| confidence_filter_mode | shadow | No |
| risk_per_trade_pct | 1.0 | No |
| min_rr | 1.5 | No |
| max_daily_trades | 2 | No |

Live system prompt: Phase 2A v1 scored evaluation (`src/prompts/primary_analyzer_prompt.py`)

---

## WHAT TO DO NEXT (priority order)

### Priority 1: Run the Prompt Ablation Test
```bash
python research/academic_pipeline/T3_prompt_ablation.py
```
This runs 5 prompt variants (A-E) on 121 MSOs. ~$25, ~2-3 hours. Produces:
- Per-variant results in `data/T3_{name}_results.json`
- Comparative report in `results/T3_prompt_ablation_results_v1.md`
- D17 ensemble analysis (all 3-way majority vote combinations)

After results: **trade-by-trade diff analysis** for each variant vs baseline (which trades flipped, why, Q-score bottlenecks). Use the same methodology as `P2A_trade_diff_analysis_v1.md`.

### Priority 2: Act on Foundation Analysis Findings

**Immediate actionable from $0 analysis:**
- **B25 TP=1.0R question**: The efficient frontier shows TP=1.0R has the highest Sharpe (0.299 vs 0.275 at 1.5R). This is surprising and needs validation. Design a shadow test: log what would happen with TP=1.0R alongside the live 1.5R TP.
- **FTMO optimal f=1.5%**: MC shows P(pass) jumps from 45.9% to 63.3% at 1.5% risk. After 30+ live trades confirm WR >= 60%, this is the first sizing change to make.
- **B28 dynamic TP**: MFE strongly correlates with vol (rho=-0.53). Test HAR-RV or ATR-based dynamic TP as a shadow logger.

### Priority 3: Stack Winning Prompt Changes
After the ablation test identifies which variants improve WR:
1. Identify the best single variant
2. Trade-by-trade diff that variant vs v1 baseline
3. Isolate which SPECIFIC prompt element caused each trade flip
4. Test that element in isolation on a fresh dataset
5. If it holds, stack it with the next winning element
6. Repeat until diminishing returns

### Priority 4: Build Monitoring Infrastructure (from D cluster)
The drift detection tools (D1-D8) are all $0 compute. Wire them into the live system:
- CUSUM on CANDIDATE rate (D1)
- ADWIN for general change detection (D2)
- EWMA on output features (D3)
- Borderline canary fixtures (D6) — $10 one-time to discover, then free

---

## KEY FILES CREATED THIS SESSION

| File | Purpose |
|------|---------|
| `research/academic_pipeline/L4_all_actionable_items_v1.md` | Complete 128-item inventory from L4 |
| `research/academic_pipeline/results/L4_foundation_results_v1.md` | $0 foundation analysis results (50 tests) |
| `research/academic_pipeline/L4_foundation_analysis.py` | Script that generated foundation results |
| `research/academic_pipeline/T3_prompt_ablation.py` | 5-variant prompt ablation test (READY TO RUN) |
| `research/academic_pipeline/results/P2A_trade_diff_analysis_v1.md` | v1 vs v2 trade-by-trade comparison |
| `research/academic_pipeline/P2C_opus_max.py` | Opus 4.6 test script |
| `research/academic_pipeline/data/P2C_opus_max_results.json` | Opus results |
| `research/academic_pipeline/results/P2C_opus_max_results_v1.md` | Opus results report |
| `research/academic_pipeline/data/P2A_v2_s46_max_results.json` | v2 regression results |
| `research/academic_pipeline/results/P2A_v2_s46_max_results_v1.md` | v2 regression report |
| `research/academic_pipeline/phase1_stop_loss_refinement_papers_v1.md` | L4 SL papers |
| `research/academic_pipeline/phase1_exit_optimization_papers_v1.md` | L4 exit papers |
| `research/academic_pipeline/phase1_alpha_decay_crowding_papers_v1.md` | L4 decay papers |
| `research/academic_pipeline/phase1_model_risk_q9_2_3_4_v1.md` | L4 model risk papers |

---

## RESEARCH PIPELINE STATUS

| Test | Status | Result | Key Number |
|------|--------|--------|-----------|
| T1: Baseline | DONE | Establishes 129-trade dataset | WR=62%, E[R]=0.278 |
| T2a: Accuracy | DONE | AUC~0.5 within CANDIDATEs | Accuracy is closed path |
| T2b: API configs | DONE | 5 experiments ($31.44) | Session memory kills 55% CR (p=0.007) |
| T2c-medium | DONE | Sonnet 4.6 medium | CR=12%, over-rejects |
| T2c-high | DONE | Sonnet 4.6 high | CR=17.4%, over-rejects |
| T2c-max | DONE | **Sonnet 4.6 max (WINNER)** | CR=38%, WR=69.6%, CR*WR=0.265 |
| P2A-v1 | DONE | **DEPLOYED to live** | Same as T2c-max |
| P2A-v2 | DONE | 4 evidence-backed fixes | **REGRESSED**: CR=32%, WR=62%, -8.15R |
| P2C-opus | DONE | Opus 4.6 max | **KILLED**: CR=19%, WR=61%, 2x cost |
| L4 | DONE | 188 papers, 128 actionable items | Complete inventory ready |
| $0 Foundation | DONE | 50 hypothesis tests | See findings table above |
| T3 Ablation | **READY** | 5 prompt variants | ~$25 to run, script ready |
| Trade Diff | DONE | v1 vs v2 per-trade analysis | Q3/Q5 over-strictness = root cause |

---

## VALIDATED NUMBERS UPDATE

These numbers supplement the CLAUDE.md canonical numbers:

| Metric | Value | Source |
|--------|-------|--------|
| P(2R \| 1R reached) | 53.2% | B36 foundation analysis |
| Winner median MAE | 0.138R | A1 Sweeney scatter |
| MAE GPD shape (xi) | 0.476 (heavy-tailed) | A3 GPD fit |
| Binary Kelly f* | 38.8% (current=0.03x Kelly) | A20 |
| Vince optimal f | 25.3% | A21 |
| FTMO P(pass) at 1% risk | 45.9% | Monte Carlo 10k paths |
| FTMO P(pass) at 1.5% risk | 63.3% | Monte Carlo 10k paths |
| Efficient frontier best Sharpe | TP=1.0R (Sharpe=0.299) | B25 |
| MFE-vol correlation | rho=-0.53 (p<0.001) | B28 |
| Formal WR decay test | p=0.40 (NOT significant) | C1 z-test |
| Failure clustering | p=0.60 (INDEPENDENT) | C16 runs test |
| Loss/win asymmetry ratio | 0.840 (favorable) | C20 |
| Observed decay rate | 13.8pp/year | C31 (14x FX TA baseline) |
| London late KZ entry WR | 81.2% | B24 |
| NY early KZ entry WR | 58.3% | B24 |

---

## GIT STATUS

Branch: main, 18+ commits ahead of origin/main.
Uncommitted files:
- L4 literature search outputs (4 files)
- L4 actionable items inventory
- Foundation analysis results
- T3 prompt ablation script
- Foundation analysis script
- Trade diff analysis
- Various research data

CEO has NOT explicitly asked for a commit or push this session.

---

*This handoff was written at ~18:45 UTC on April 12, 2026. The next agent should start by running `T3_prompt_ablation.py` and then doing trade-by-trade diff analysis on the results.*
