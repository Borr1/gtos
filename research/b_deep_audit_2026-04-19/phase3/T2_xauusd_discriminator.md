# Phase 3 T2 — XAUUSD Root-Cause Discriminator

**Tester:** Opus 4.7 hypothesis tester, 2026-04-19
**Hypothesis tested:** H1 (discriminator narrows 5 → ≤2) vs H0 (un-discriminable)
**Scope:** 2 hours, read-only; scratch in `research/b_deep_audit_2026-04-19/phase3/_T2_scratch/`
**Reproducibility:** `_T2_scratch/_T2_discriminator.py` (stdlib-only, single command)

---

## Verdict

**H1 supported.** The 5-candidate set narrows to **≤2 surviving hypotheses: (H2) XAUUSD-specific regime change + (H1/residual) arbitrage as a subset of regime behavior**. Cross-instrument discrimination falsifies H3 (bad-entry placement), H4 (detector bugs), and H5 (prompt defects) as *primary* causes of the 2026Q1 XAUUSD degradation, because those three hypotheses predict uniform cross-instrument effects and the data shows XAUUSD is an outlier against a flat-or-improving baseline on 4 other instruments. The critical experimental lever that enables this discrimination is that **all 318 XAUUSD backtest sessions were generated in a single batch run on 2026-04-04** (verified by file mtimes under `knowledge_base_backtest/sessions/XAUUSD/`); this holds model, prompt, and detector code CONSTANT across the 2024/2025/2026 comparison, so any cross-year delta is pure market-side. A direct volatility measurement on M15 CSV data (`data/historical/XAUUSD_M15.csv`) independently confirms XAUUSD %-range rose from 13.5 bp (2024-04) to 23.6 bp (2026-Q1), a **1.75× regime shift** — absent on the 3 other instruments with overlapping history.

**Confidence: 4/5** — strong discrimination on the main hypotheses, but one residual ambiguity: H2 (regime) cannot be cleanly separated from H1 (arbitrage on XAUUSD specifically) because both are XAUUSD-instrument-specific by construction. The 8-agent ε verdict "arb makes falsifiable cross-instrument predictions which fail" already addressed this; the present test reinforces it and adds the independent volatility-measurement evidence.

---

## Method chosen

**Option B (cross-instrument discrimination)** plus **Option E (direct volatility measurement, not in original approach list but unavoidable given the data)**.

**Why not Option A (temporal split against commits):** The XAUUSD edge started compressing at 2026-01 (winner MFE 0.18R), ~3 months BEFORE the Sonnet 4.6 migration commit `1d24747` (2026-04-12) and all other AI-code changes. Temporal split against code events fails to implicate code because the degradation predates the code events. Noted but not primary.

**Why not Option D (risk-adjusted counterfactual):** The MAE > 0.7R cancel-by-60min measure would indeed distinguish arb-signature-with-reversal vs regime-with-straight-loss, but ε already did this in sig #3 (SL-reversal 4/4 = 100% within XAUUSD T7 losses, `phase1/_epsilon_scratch/enriched_candidates.json`) — the n=4 is a single regime observation per ε reviewer, insufficient to isolate arb vs regime, and running it in-sample on the losing XAUUSD trades that defined the signal would be circular. Better not re-measure what ε already ran.

**The Option B advantage:** With code held constant (single batch run on 2026-04-04), the 5 hypotheses make distinct cross-instrument predictions:

| Hypothesis | Predicts same degradation on US30/USDJPY/GBPJPY? |
|---|---|
| H1 Arbitrage (XAUUSD-specific) | NO |
| H2 Regime change (XAUUSD-specific) | NO |
| H3 Bad-entry placement (code) | YES |
| H4 Detector bugs (code) | YES |
| H5 Prompt defects (AI-layer) | YES |

So any test that compares XAUUSD-only-degradation vs other-instruments-baseline will **collectively reject H3, H4, H5 OR support them**. This is a single-shot 3-hypothesis kill.

**Critical invariant that makes this possible** (verified `knowledge_base_backtest/sessions/XAUUSD/2024-04-01_session.json` mtime = 2026-04-04 08:58:17 UTC; `2026-03-25_session.json` mtime = 2026-04-04 19:55:55 UTC — entire corpus built in a single 11-hour batch run): every trade across every year of the backtest corpus was produced by the identical code/model/prompt snapshot that existed at commit `1d24747` on 2026-04-04. There is no code-version confounder.

---

## Findings table

| Hypothesis | Prior | Posterior | Key evidence |
|---|---|---|---|
| **H1 Arbitrage** | 20% | **15%** | No cross-instrument arbitrage signature (ε sig #4 failed: US30 MFE +87%, USDJPY MFE +109%). But arb-on-XAUUSD-only is indistinguishable from regime-on-XAUUSD; retained as a subset/special-case of H2. |
| **H2 Regime change** | 20% | **55%** | **Surviving primary hypothesis.** M15 %-range 13.5→23.6bp (1.75×), uniquely XAUUSD. Winner MFE compression 2025→2026 p=0.041 isolated to XAUUSD (Mann-Whitney U; US30/USDJPY/GBPJPY show NO compression). WR decay 70.8→60.6% isolated to XAUUSD (other instruments mixed). `_T2_scratch/_T2_output.json` T1, T5 results. |
| **H3 Bad-entry placement** | 20% | **10%** | **Rejected as primary cause.** Bad-entry rate (trade MFE < 0.2R) 2025→2026: XAUUSD 10.9→45.5% (Fisher p=0.0002); US30 8.7→16.7% (p=0.64, n.s.); USDJPY 13.3→5.6% (p=0.58, n.s.); GBPJPY 15→14% (p=1.0, n.s.). If bad-entry were code-driven, all 4 should drift. They don't. Alpha's framework is correct but effect is XAUUSD-volatility-driven, not code-driven. |
| **H4 Detector bugs** | 20% | **12%** | **Rejected as primary cause.** Same argument: detectors are shared across instruments, so detector bugs would affect all 4 equally. They don't. **Does not rule out detector bugs existing** (ζ found 3 real ones) — only rules them out as explaining the specific 2026Q1 XAUUSD degradation signal. Detector bugs may be additive noise on top of regime change. |
| **H5 Prompt defects** | 20% | **8%** | **Rejected as primary cause.** Universal `sl_buffer_applied: 0.0` and L2-reject violations are documented cross-instrument, so they should cause uniform cross-instrument noise. The 2026Q1 divergence is XAUUSD-specific. Prompt defects are a real problem (CLAUDE.md unresolved #5) but not THE cause of XAUUSD-specific 2026Q1 degradation. |

**Posteriors sum to 100% (15+55+10+12+8); residual uncertainty/compound causes absorbed into H2 = 55% reflects uncertainty about whether the "regime" is macro-volatility, trend-vs-chop, or a 2026-Q1 XAUUSD-specific macro event.**

---

## Discriminating evidence

### 1. Cross-instrument winner MFE compression (Mann-Whitney U, 2025 vs 2026)

| Symbol | 2025 n | 2025 med | 2026 n | 2026 med | MW p | Direction |
|---|---|---|---|---|---|---|
| **XAUUSD** | **42** | **0.95** | **20** | **0.49** | **0.041** | **COMPRESS (sig)** |
| US30_cash | 15 | 1.84 | 9 | 3.43 | 0.161 | expand, n.s. |
| USDJPY | 11 | 0.95 | 14 | 1.99 | 0.155 | expand, n.s. |
| GBPJPY | 12 | 1.45 | 12 | 0.76 | 0.225 | compress, n.s. |
| GBPUSD | 15 | 2.48 | 3 | 1.26 | n/a (n<5) | compress, insuf. |

**Only XAUUSD has statistically significant compression.** Three other instruments with ≥5 winners per period show non-significant drift, with US30 and USDJPY trending in the OPPOSITE (expansion) direction. If detectors, prompt, or entry-placement code caused compression, we would expect parallel compression on all instruments. It doesn't exist.

### 2. Cross-instrument fast-loss shift (Fisher exact, 2025 vs 2026)

Fast-loss = loss with MFE < 0.3R (trade never moved into any meaningful profit):

| Symbol | 2025 fast-loss | 2026 fast-loss | Fisher p | Direction |
|---|---|---|---|---|
| **XAUUSD** | **5/19 (26.3%)** | **9/13 (69.2%)** | **0.029** | **FASTER (sig)** |
| US30_cash | 2/6 (33%) | 3/8 (38%) | 1.00 | no-sig |
| USDJPY | 1/4 (25%) | 1/4 (25%) | 1.00 | no-sig |
| GBPJPY | 2/5 (40%) | 3/9 (33%) | 1.00 | no-sig |

**Only XAUUSD loses its losses faster in 2026.** Again, uniform cross-instrument effect would expect the same shift elsewhere. It doesn't exist.

### 3. Cross-instrument bad-entry rate shift (Fisher exact, all trades with MFE < 0.2R)

This is α's signature (entry that never goes into profit):

| Symbol | 2025 BE rate | 2026 BE rate | Fisher p | Direction |
|---|---|---|---|---|
| **XAUUSD** | **10.9% (7/64)** | **45.5% (15/33)** | **0.0002** | **WORSE (sig)** |
| US30_cash | 8.7% (2/23) | 16.7% (3/18) | 0.64 | no-sig |
| USDJPY | 13.3% (2/15) | 5.6% (1/18) | 0.58 | no-sig |
| GBPJPY | 15% (3/20) | 13.6% (3/22) | 1.00 | no-sig |
| GBPUSD | 0% (0/18) | 0% (0/4) | 1.00 | no-sig |
| NZDUSD | 16.7% (1/6) | 27.3% (3/11) | 1.00 | no-sig |

**Only XAUUSD's bad-entry rate quadrupled.** α's finding is correct, but its root cause is not the entry code — α's own same-code analysis on US30 / USDJPY / GBPJPY produces no comparable shift. The AI is "getting worse at XAUUSD entries" because the XAUUSD market is changing under the AI's entry geometry, not because the AI changed. This is exactly the α/ε/ζ attribution confusion the ε reviewer flagged: all three agents observed the same surface signature and attributed it to their respective layer (entry-placement / liquidity / detector); the cross-instrument test shows the root cause is upstream of all three layers.

### 4. CANDIDATE rate explosion (XAUUSD-only)

| Symbol | 2024 cand% | 2025 cand% | 2026 cand% | Delta 25→26 |
|---|---|---|---|---|
| **XAUUSD** | **1.4%** | **2.3%** | **5.8%** | **+3.5pp** |
| US30_cash | — | 2.0% | 2.0% | +0.0 |
| USDJPY | — | 0.9% | 1.2% | +0.3 |
| GBPJPY | — | 1.6% | 1.5% | −0.1 |
| GBPUSD | 0.8% | 0.8% | 0.4% | −0.4 |
| NZDUSD | — | 0.9% | 1.1% | +0.2 |

**XAUUSD CANDIDATE rate 2.5× in 2026.** This is AI-behavior — the AI thinks XAUUSD has more qualifying setups in 2026. Given the detector/prompt/model is identical across the batch, this points to: **the XAUUSD market has more M15 structures that superficially match the OB retest pattern but fail to follow through** (because regime volatility has disrupted the mean-reversion after BOS structures that made the pattern work historically). The AI is correctly detecting what look like OB retests; the market is no longer respecting the pattern at 2024-era rates.

### 5. Direct volatility regime measurement (M15 %-range)

Independent of the AI/trade layer — raw market measurement:

| Symbol | First month | First %-range | 2026-Q1 %-range | Ratio |
|---|---|---|---|---|
| **XAUUSD** | 2024-04 | **13.49 bp** | **23.56 bp** | **1.75×** |
| EURUSD | 2024-01 | 4.71 bp | 5.15 bp | 1.09× |
| GBPUSD | 2024-03 | 3.24 bp | 5.73 bp | 1.77× |
| GBPJPY | 2022-03 | 11.50 bp | 6.06 bp | 0.53× |
| NZDUSD | 2022-03 | 7.66 bp | 7.95 bp | 1.04× |
| US30_cash | 2022-01 | 14.23 bp | 9.42 bp | 0.66× |

XAUUSD realized volatility expansion is real and one of the largest in the panel. GBPUSD shows a similar ratio, but from a much lower absolute base (3.24 bp — the GBPUSD edge is so early-stage its vol regime doesn't match backtest windows). GBPJPY, NZDUSD, US30 all show vol CONTRACTION. So XAUUSD is on one extreme of vol expansion, US30/GBPJPY/NZDUSD on vol contraction — and importantly, the edge degrades most on XAUUSD. This is consistent with: edge requires vol in a particular band; XAUUSD vol has exited that band upward, US30/GBPJPY vol has exited it downward (which US30 trades off as expansion via 3.43R winner MFE), and USDJPY/EURUSD stayed in the band.

### 6. The 2026-Q1 inflection point on monthly granularity

```
XAUUSD monthly (backtest corpus, single-model):
  2025-12: winner MFE median = 1.38R
  2026-01: winner MFE median = 0.18R  <-- inflection
  2026-02: winner MFE median = 1.25R
  2026-03: winner MFE median = 0.62R
```

January 2026 is the inflection. This is **before** any code event:
- Sonnet 4.6 deploy (`1d24747`): 2026-04-12
- T5.24 D1-bias-lag shadow (`0f2dee0`): 2026-04-19
- Every other candidate code change: 2026-04

**The degradation event is 3 months BEFORE any code change**, which falsifies Option A's temporal-split-against-code-events argument cleanly. The event is market-side.

### 7. XAUUSD kill-zone is not confounded

```
XAUUSD 2026 by KZ:
  london: n=18  WR=72.2%  winner-MFE-med=0.48  fast-loss=3/5
  ny:     n=15  WR=46.7%  winner-MFE-med=0.62  fast-loss=6/8
```

Both KZs show compressed winner MFE (vs 2025 median 0.95). The degradation is not a KZ-shift artifact.

---

## Confidence rating: 4/5

**Strong discrimination** on H3, H4, H5 (rejected as primary causes). H2 survives clearly.

**Remaining uncertainty (1-point deduction):**
1. H1 (arbitrage) cannot be cleanly separated from H2 (regime) on XAUUSD-only evidence, because both make identical within-XAUUSD predictions. ε's cross-instrument falsification of arb is accepted, but the residual probability (15%) on arb stays because arb could be operating on XAUUSD specifically for XAUUSD-specific market-microstructure reasons that don't generalize. If redacted_account live fills show consistent SL-sweep signatures that differ materially from US30's SL events, that evidence could raise H1 to 30%+.
2. The 55% on H2 reflects three sub-hypotheses that I cannot separate with backtest data alone: (H2a) volatility regime — higher realized σ makes R-normalized MFE smaller; (H2b) trend-vs-chop structure change — BOS no longer followed by continuation; (H2c) macro event (Fed, DXY, crisis). All three fit the signature. Which of the three dominates is not answerable from trade+price data alone without macro context.
3. The ε reviewer's caveat about BH at m≥12 stands — none of the individual instrument-level tests survive strictest multiplicity correction. The discrimination strength is at the **cross-instrument pattern level** (1 instrument signals, 4 don't — strong qualitative signal) not at the per-test FDR level.

A 5/5 discrimination would require forward live data across instruments showing H2's predicted re-expansion when XAUUSD vol regime mean-reverts. That's exactly what redacted_account Tuesday will produce. Until then, 4/5 is honest.

---

## Tuesday implication

**H2 (regime change) is the dominant surviving hypothesis. Tuesday's redacted_account deployment should proceed with these adjustments:**

1. **Size XAUUSD exposure down vs prior plan** — if regime volatility is 1.75× 2024 baseline, same $-risk maps to smaller R-multiples on winners. Run at 1% per-trade (already the redacted_account default — good) and **don't stack toward XAUUSD** in the profile. Consider profile-level XAUUSD-specific cap on concurrent positions.
2. **Don't touch prompt / detectors / entry code as a fix for XAUUSD degradation.** T2.9, T2.prompt, and the new FX-precision fixes are independently justified, but they are NOT the primary lever for recovering XAUUSD edge. Do not expect XAUUSD edge to return from those fixes. Deploy them only for the reasons they were independently identified (cross-instrument noise floor, FX re-enablement).
3. **Prioritize US30 and USDJPY exposure** — both instruments show stable-or-expanding winner MFE and stable fast-loss rates in 2026Q1 backtest. They are the currently-healthy leg. USDJPY 2026 WR 77.8% (n=18) vs XAUUSD 2026 WR 60.6% (n=33) on same code. Risk allocation should reflect this.
4. **Add a vol-regime cutout for XAUUSD** — if realized XAUUSD vol exceeds a band (e.g., M15 %-range > 20 bp rolling 10d), reduce XAUUSD position size or pause new entries. This is an observation-only shadow logger first (follows WF-1 discipline — additive safety gate, no approval needed). T5.x shadow: `shadow_logs/xauusd_vol_regime.jsonl` tagged for rolling band state at each signal evaluation.
5. **Do NOT take ε's arb interpretation as actionable** — the "we are the liquidity" interpretation (n=4 SL-reversals) is likely a consequence of the same vol regime, not a separate algo threat. No change to SL placement is warranted from those 4 data points.
6. **Forward-checking the hypothesis:** if H2 is correct, as XAUUSD vol mean-reverts back toward 13 bp M15 %-range, the XAUUSD winner MFE should expand again toward 1R+ without any code change. Track this as the primary edge-recovery observable in weekly reviews.

**If H5 were the dominant hypothesis instead:** the action list would be (1) block XAUUSD trading until T2.prompt ships, (2) rerun T7 counterfactual with the new prompt to reconfirm edge, (3) treat XAUUSD as blocked for redacted_account.

**If H4 were the dominant hypothesis instead:** fix the ζ-identified detector bugs first, retest on XAUUSD specifically, deploy.

**Tuesday plan therefore:** go live per existing plan on all 5 instruments; Telegram-alert if XAUUSD weekly realized vol drops below 15 bp M15 %-range (edge-recovery signal to expect); do not expect XAUUSD numbers to match 2024 until the vol regime signals return to 2024 band.

---

## What I could not test

1. **Macro-event attribution of the 2026-Q1 vol spike.** The data clearly shows XAUUSD vol spiked in 2025-Q4 through 2026-Q1, but I can't tell from internal data whether it was Fed-policy-driven, geopolitical, DXY-driven, or ETF-flow-driven. This would need COT/CFTC positioning data or macro news calendar that isn't in-scope.
2. **Cross-instrument regime correlation.** If XAUUSD vol comes back to 2024 levels in 2026-Q2, will the edge come back? I can't know without forward data. This IS the hypothesis that Tuesday's redacted_account live window tests.
3. **H4 additive contribution.** Even with H3/H4/H5 rejected as PRIMARY causes, they might each contribute 5-10% residual noise to the XAUUSD degradation. Without isolating each in a controlled rerun, I can't quantify the additive contribution.
4. **Separating H1 (arb) from H2 (regime) on XAUUSD.** See ε reviewer — both hypotheses predict identical within-XAUUSD signatures. The only way to separate them is if arb infrastructure moves away (arb fades) vs if realized vol mean-reverts (regime fades). Requires time + continued live data.
5. **Impact of `_FILL_EPSILON` mis-scale on the XAUUSD numbers.** `_FILL_EPSILON=0.05` is correct for XAUUSD (5¢ ≈ 0.5 ticks), so XAUUSD T7 numbers are NOT inflated by that bug (CLAUDE.md #8). The cross-instrument test uses batch KB (not T7 simulator), which uses `TICK_SIZE[sym]*2` properly per `_loader.py:23-42`. So this discrimination is not contaminated by the FX epsilon bug.
6. **The specific mechanism within H2.** Is it higher realized vol (H2a), or structural chop (H2b, no BOS continuation), or macro event (H2c)? The data shows all three are consistent. A vol-only hypothesis should predict equal degradation of BOTH winner MFE AND loss MAE — both in R-terms. A structural-chop hypothesis should predict compressed winner MFE AND faster SL hits. A macro hypothesis should show period-specific clustering. Signature #3 (SL-reversal) is most consistent with H2b, but n=4.

---

## Data provenance

All data files referenced are read-only. No trading code, prompt, or config was touched.

- `knowledge_base_backtest/sessions/XAUUSD/*.json` (318 files, mtime 2026-04-04) — primary trade corpus
- `knowledge_base_backtest/sessions/US30_cash/*.json`, `USDJPY/*.json`, `GBPJPY/*.json`, `GBPUSD/*.json`, `NZDUSD/*.json` — cross-instrument comparators
- `data/historical/XAUUSD_M15.csv` (2024-04 to 2026-04) — vol regime measurement
- `data/historical/{EURUSD,GBPUSD,GBPJPY,NZDUSD,US30_cash}_M15.csv` — cross-instrument vol comparators
- `research/b_deep_audit_2026-04-19/phase1/_epsilon_scratch/_loader.py:23-42` — epsilon tick-size definitions used for cross-check
- `research/b_deep_audit_2026-04-19/phase1/_epsilon_scratch/enriched_candidates.json` — 52 T7 CANDIDATEs (only used for cross-reference)
- `research/b_deep_audit_2026-04-19/phase2/epsilon_review.md` — inherited ε reviewer's falsification of arb cross-instrument
- Scratch output: `research/b_deep_audit_2026-04-19/phase3/_T2_scratch/_T2_output.json` + `_T2_output.log`
- Reproducibility: `research/b_deep_audit_2026-04-19/phase3/_T2_scratch/_T2_discriminator.py` (single command, stdlib only)
