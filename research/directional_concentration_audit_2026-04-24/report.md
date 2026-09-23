# Directional Concentration Audit - April 2026

**Date:** 2026-04-24
**Triggered by:** research/thursday_2026-04-23_analysis/system_forensics.md Section 5
**Claim:** "Directional concentration risk: 98%+ bullish bias across all 4 live instruments in April 2026. ZERO bearish CANDIDATEs since redacted_account kickoff (2026-04-20)."
**Mandate:** discriminate among (a) regime, (b) structural bias in market_state.py, (c) downstream pipeline bias, (d) AI prompt bias. Investigation only.

---

## 1. Claim Verification

### Per-instrument April 2026 CANDIDATE counts

| Instrument | Total | bullish | bearish | ranging |
|---|---|---|---|---|
| XAUUSD | 12 | 12 (100%) | 0 | 0 |
| US30_cash | 26 | 26 (100%) | 0 | 0 |
| USDJPY | 39 | 39 (100%) | 0 | 0 |
| GBPJPY | 35 | 35 (100%) | 0 | 0 |
| GBPUSD (observer) | 29 | 29 (100%) | 0 | 0 |
| 4-live total | 112 | 112 (100.0%) | 0 | 0 |

Post-redacted_account kickoff (2026-04-20 - 2026-04-23), 4 live: LONG 44/44, SHORT 0/44.
All-time lifetime CANDIDATEs: 141 total, 0 SHORT-reasoned.

**Claim verdict:** "98%" is directionally correct but understates. Actual rate is 100.0% in both April and all-time.

### AI daily_bias_direction distribution across ALL evals (not just CANDIDATEs)

| Instrument | n_evals | bullish | bearish | ranging |
|---|---|---|---|---|
| GBPJPY | 286 | 50.3% | 6.6% | 43.0% |
| GBPUSD | 154 | 74.7% | 2.6% | 22.7% |
| US30_cash | 258 | 68.2% | 1.6% | 30.2% |
| USDJPY | 366 | 89.6% | 0.5% | 9.8% |
| XAUUSD | 219 | 63.0% | 0.9% | 36.1% |

Bearish bias is emitted by the AI occasionally (0.5-6.6% of evals) but NEVER results in a CANDIDATE. Only one day in April had a bearish-majority on any instrument: GBPJPY 2026-04-10 (15/31 bearish, 0 CANDIDATEs).

Evidence files: evidence_extract_candidates.txt

---

## 2. D1 Bias Logic Audit

### 2.1 daily_bias_direction is AI-emitted, not deterministic

- Schema: src/models/analysis_models.py:11-15 - DailyBiasAnalysis.direction: Literal[bullish, bearish, ranging].
- Prompt instruction line 165 of src/prompts/primary_analyzer_prompt.py: "daily_bias: Report H1 direction as the bias. confidence = high if 3+ BOS, medium if 2 BOS, low if 1 BOS or CHoCH only."
- Misleadingly named (it is H1 direction), but not a bug per se.

### 2.2 THE CORE BUG - src/components/market_state.py:216-257 identify_structure

The swing-structure classifier:

    recent_pairs = min(3, len(highs) - 1, len(lows) - 1)
    if hh_count >= recent_pairs and hl_count >= recent_pairs:
        direction = "bullish"        # BRANCH A, fires first
    elif ll_count >= recent_pairs and lh_count >= recent_pairs:
        direction = "bearish"        # BRANCH B
    else:
        direction = "transitional"

Three compounding asymmetries:
1. recent_pairs saturates at 3 - H1 lookback=168 typically produces 20+ swings, so rp=3.
2. Threshold too low - 3 HH AND 3 HL is trivially satisfied in any noisy market.
3. Bullish branch fires first - when both branches qualify, bullish wins deterministically.

### 2.3 Synthetic scenario tests (scripts/structure_stickiness.py)

| Scenario | True regime | hh/hl/lh/ll | Label |
|---|---|---|---|
| S_up | pure uptrend + noise | 9/12/12/9 | bullish (correct) |
| S_down | pure downtrend + noise | 4/6/16/17 | bullish (WRONG) |
| S_flat | pure random walk | 14/10/9/11 | bullish (WRONG) |
| S_stick_3 | 25% up + 75% down | 8/10/15/13 | bullish (WRONG) |

A pure downtrend gets labeled bullish. A pure random walk gets labeled bullish.

### 2.4 Full CSV replay with production lookbacks (scripts/structure_full_replay_v2.py)

| Instrument | TF | n_closes | bullish % | bearish % | transitional % |
|---|---|---|---|---|---|
| XAUUSD | D1 | 46 | 17.4% | 4.3% | 78.3% |
| XAUUSD | H4 | 371 | 94.3% | 5.7% | 0.0% |
| XAUUSD | H1 | 1554 | **100.0%** | **0.0%** | 0.0% |
| US30_cash | H1 | 1566 | **100.0%** | **0.0%** | 0.0% |
| USDJPY | H1 | 1657 | **100.0%** | **0.0%** | 0.0% |
| GBPJPY | H1 | 1657 | **100.0%** | **0.0%** | 0.0% |
| GBPUSD | H1 | 1657 | **100.0%** | **0.0%** | 0.0% |
| GBPUSD | D1 | 47 | 0.0% | 59.6% | 40.4% |

H1 direction is bullish in 100% of 7,991 H1 closes across 5 instruments across 3.5 months. This is structurally impossible in real markets and is definitive evidence of the bug.

### 2.5 Git history

git log --all -S recent_pairs -- src/components/market_state.py returns only 436c16b (initial files). The biased logic has existed since day zero.

---

## 3. Market Cross-Check

Naive D1 direction (close > open) from data/historical_2026/ CSVs for April 2026:

| Instrument | Bull days | Bear days | Net April move |
|---|---|---|---|
| XAUUSD | 7 | 5 | +3.4% |
| US30_cash | 8 | 5 | +6.8% |
| USDJPY | 8 | 5 | -0.09% |
| GBPJPY | 9 | 4 | +2.14% |
| GBPUSD | 8 | 5 | +2.20% |

All 5 instruments had 58-69% bull days. 4 of 5 had positive net April returns (USDJPY flat). This is a mild bullish regime, not an extreme one. It explains ~60-70% LONG concentration at best; it does NOT explain 100%.

---

## 4. Pipeline Symmetry Check

### 4.1 Pre-screen (orchestrator.py:3016-3046)
Symmetric. Rejects both bullish_d1_vs_bearish_h4 AND bearish_d1_vs_bullish_h4.
Evidence in logs/xauusd.log: 48 rejections bullish_vs_d1_bearish (Apr 13-15) and 23 rejections bearish_vs_d1_bullish (Apr 23-24).

### 4.2 Pre-AI gate (src/components/pre_ai_gates.py:12-76)
h1_poi_availability: symmetric by construction. ob.type == bias and bb.direction == bias with identical structure for both directions.

### 4.3 Deterministic bias (orchestrator.py:1046-1093)
_compute_deterministic_bias: symmetric, no bullish default, falls back to no_bias.

### 4.4 Alignment tie-breaker (orchestrator.py:1117-1120) - MINOR
dominant = "bullish" if bullish >= bearish else "bearish". Ties go bullish, but this is the human-readable alignment context string, not a decision gate. Near-zero impact.

### 4.5 L2 verification (src/components/verification.py)
All direction-aware checks mirror LONG/SHORT correctly. Strict < for LONG sl_beyond_ob, strict > for SHORT. Two minor required_dir=bullish fallbacks when tp is None, but those paths return SKIP before exercise. Not impactful.

### 4.6 Permissions (src/components/permissions.py)
All gates symmetric: expected_ob_type mapping, direction-mismatch gate (rejects both combos), TP/SL geometry (strict mirror).

**Pipeline asymmetry conclusion:** No decision gate is direction-biased. One cosmetic tie-breaker on the advisory alignment string.

---

## 5. AI Prompt Check

src/prompts/primary_analyzer_prompt.py:
- LONG: 7 occurrences, SHORT: 6 occurrences.
- bullish: 2, bearish: 3.
- Line 132: "H1 bullish -> LONG. H1 bearish -> SHORT. Mismatch -> FAIL." - symmetric.
- Lines 150-155 trade parameter rules: symmetric LONG/SHORT instructions.
- No LONG-only in-prompt examples.

Prompt is balanced. Not implicated.

Moreover, the AI demonstrates it CAN emit bearish: 15/15 bearish-bias rows on GBPJPY 2026-04-10 were correctly labeled bearish by the AI. The bottleneck is the MSO-injected H1 structure, not the AI.

---

## 6. Causal Chain Reconstruction

How does the bug produce 100% LONG CANDIDATEs?

1. identify_structure classifies H1 as bullish in ~100% of production windows (bullish-first + low threshold).
2. identify_structure classifies H4 as bullish in ~95% of production windows.
3. D1 with lookback=30 can still flip to bearish sometimes (GBPUSD was 60% bearish in April).
4. When D1=bearish and H4=bullish: pre-screen rejects (48 XAUUSD bars observed Apr 13-15).
5. When D1 and H4 both agree bullish: deterministic bias injected = bullish -> AI emits LONG CANDIDATEs.
6. When AI independently judges bias=bearish: C3 gate fails because H1 structure (MSO) is bullish-stuck -> NO_TRADE ("Directional bias requires SHORT but H1/M15 structure is bullish").
7. Result: bias=bearish AND H1_structure=bearish AND bearish OB available -> empty set for 3.5 months.

---

## 7. Verdict (ranked by likelihood x magnitude)

### (b) STRUCTURAL BULLISH BIAS IN market_state.py - CONFIRMED HIGH SEVERITY

- Deterministic: produces bullish on >99% of H1 and H4 windows.
- Synthetic pure-downtrend -> bullish.
- Synthetic pure random walk -> bullish.
- Root cause: recent_pairs = min(3, ...) too low + bullish branch first.
- Confidence: >=99%.

### (a) Mild genuine April uptrend - PARTIAL CONTRIBUTOR

- 4/5 instruments had +0.9% to +6.8% net April return, 58-69% bull days.
- Explains ~60-70% LONG concentration at most. Amplifies but does not cause 100%.
- Confidence: ~85%.

### (d) AI prompt bias - NOT IMPLICATED

- Balanced prompt, no asymmetric examples.
- AI emits bearish correctly when inputs support it.
- Confidence: >=95%.

### (c) Downstream pipeline bias - NOT IMPLICATED (one cosmetic tie-breaker only)

- Pre-screen, pre-AI gate, verification, permissions all symmetric.
- orchestrator.py:1119 cosmetic tie-breaker on display string, not a gate.
- Confidence: >=95%.

---

## 8. Recommendation

1. This is a real, high-severity bug. In a bearish regime, the system would produce zero signals across all instruments.
2. DO NOT FIX IN THIS TASK. Any fix requires:
   - CEO approval under CLAUDE.md WF-1 discipline.
   - Full 2026 CSV backtest to measure signal count and CANDIDATE rate impact.
   - Re-verification of validated numbers (62% XAUUSD WR, 65% full-pop WR, 10.3% CAND rate, 70% OB continuation rate) which were all computed over this biased classifier - they may not survive the fix.
   - T7 live-sim rerun to verify AI still produces positive EV with bearish signals reintroduced.
3. Priority-1 escalation to CEO and chairman.
4. Recommended ADR in .context/06_decisions/ documenting the finding, considered fixes (raise threshold; balance branch order), and the empirical-number re-validation plan.
5. Consider shadow-branch validation first: ship the fix to shadow mode and compare signal counts/WR for 30 days before production.

---

## 9. Reproducibility artifacts

Scripts in research/directional_concentration_audit_2026-04-24/scripts/:
- extract_candidates.py - Parse live_evaluations JSONL, count LONG/SHORT per symbol per day.
- mso_vs_ai_bias.py - Cross-tab MSO vs AI bias from candidate_features_log.
- d1_market_direction.py - Naive D1 direction labeling from CSV OHLC data.
- h1_structure_replay.py - Early exploration with 200-bar window.
- structure_full_replay_v2.py - Bit-exact replay with production lookbacks.
- structure_stickiness.py - Synthetic tests (pure downtrend, random walk, reversals).

Evidence output files: evidence_*.txt in the audit root.

---

## 10. Appendix - Key file:line citations

- src/components/market_state.py:216-257 - identify_structure (THE BUG).
- src/components/market_state.py:239-240 - bullish branch checked first.
- src/components/market_state.py:237 - recent_pairs = min(3, ...) threshold too low.
- src/components/orchestrator.py:1046-1093 - _compute_deterministic_bias (symmetric).
- src/components/orchestrator.py:1117-1120 - alignment tie-breaker (minor cosmetic).
- src/components/orchestrator.py:3016-3046 - prescreen_mso (symmetric).
- src/components/pre_ai_gates.py:12-76 - h1_poi_availability (symmetric).
- src/prompts/primary_analyzer_prompt.py:105-252 - system prompt (symmetric).
- src/prompts/primary_analyzer_prompt.py:165 - "Report H1 direction as the bias".
- src/models/analysis_models.py:11-15 - DailyBiasAnalysis schema.
- config/agent_config.yaml:120-125 - production lookbacks (D1=30, H4=80, H1=168).
- logs/xauusd.log - 48 bullish_vs_d1_bearish + 23 bearish_vs_d1_bullish rejections.
- knowledge_base/live_evaluations/GBPJPY/2026-04-10.jsonl - 15 bearish-bias rows, all NO_TRADE.
- scripts/structure_stickiness.py S_down: pure downtrend -> bullish (hh=4, hl=6, lh=16, ll=17, rp=3).
- scripts/structure_full_replay_v2_output.txt: 0 bearish H1 labels across 7,991 closes.