# Phase 4 — Chairman Synthesis: Session 35 Deep-Diagnostic Audit

**Author:** Phase 4 Chairman (Claude Code Opus 4.7, max effort)
**Date:** 2026-04-19
**Audience:** CEO Borhen
**Decision deadline:** Tuesday 2026-04-21 — redacted_account Stellar 2-Step $100K kickoff (1% risk)
**Scope:** Synthesise 20 research artefacts (3 Tier A + 8 Phase 1 + 8 Phase 2 + 4 Phase 3) produced by independent Opus 4.7 agents. Answer CEO Q1-Q4, produce per-instrument Tuesday go/no-go, distinguish shippable-autonomously from CEO-approval-required changes.
**Hard constraint:** Read-only synthesis. No live code changes, no prompt changes, no production config changes committed this session.

---

## TL;DR — five bullets

1. **XAUUSD's apparent quarterly decay is mostly a measurement artefact on top of a real, uniquely-XAUUSD regime shift.** The canonical 73.2→71.4→63.6→59.4% sequence is hard-coded at `research/academic_pipeline/L4_foundation_analysis.py:649` (Phase 2 δ review, zeta). Under bootstrap on the XAUUSD 131-trade sample, P(max-min spread ≥ 13.8pp under stationary null) = **0.7525**; 8-quarter χ² homogeneity p≈0.66 (δ review §5). At the same time, Phase 3 T2 pins the 2026-onset inflection as a genuine XAUUSD-only regime signature (5 independent signals: ADR ↑5×, ATR/252d 2.16, M15 %-range 13.5→23.6bp, winner MFE compression p=0.041, fast-loss shift p=0.029, bad-entry rate 10.9→45.5% p=0.0002 — all ONLY on XAUUSD, cross-instruments flat). Posterior distribution over the 5 competing hypotheses: **H2 Regime 55%, H1 Arbitrage 15%, H4 Detector-bugs 12%, H3 Bad-entry 10%, H5 Prompt-defects 8%** (T2 §8).

2. **No T2.9 / `sl_beyond_ob` / D1-bias-lag "fix" should ship before Tuesday.** Phase 2 ζ review + Phase 3 T4 collapse ζ's headline D1-bias-lag R-impacts by 50× under per-instrument epsilon + per-day de-correlation (EURUSD +110R → +2R/day → +1.5R/episode; fleet-wide +1.5R across 11 episodes over 3.25 months = noise; T4 §5). Phase 3 T3 shows the `_count_touches` bar-overlap vs research-transition semantic mismatch produces a theoretical 50× divergence at full history but **only 0.009% false positives (FN=0) at the 168-bar live window** — documentation fix, not code fix. Phase 2 ε review + Phase 3 cross-instrument audit (session 33 T4.26, `0e33651`) confirmed 6/6 bit-exact XAUUSD `sl_beyond_ob` rejects would have been **net −1R (Exp −0.167R)** — NOT an edge-restoration fix. **All three items flagged "bug fix / Allowed Without Approval" in Phase 1 ζ are in fact design or behaviour changes requiring CEO approval** (ζ review §5, §7).

3. **FX T7 counterfactuals are fatally contaminated by two interacting bugs — do NOT enable any FX symbol on live Tuesday.** The Tier A2 EURUSD revalidation (`EURUSD_epsilon_revalidation.md`) shows honest 2-pip epsilon collapses the T7 CANDIDATE set to **0% WR / −5.0R / Exp −1.00R** (was 80%/+5.17R/+1.034R under legacy `_FILL_EPSILON=0.05`). L2 counterfactual collapses +204R → +6R; `sl_beyond_ob` +55R → **−9R** (9/9 "wins" FLIP to LOSS). Compounded by Phase 2 β review — EURUSD 59.67% degenerate (entry=SL=TP) outputs with **NOT temporally stable** contamination (30.68% Jan → 72.78% Feb → 53.33% Mar → 100% Apr; Fisher p=2.78e-4). Until `_PRICE_FMT` per-instrument override + non-zero `sl_buffer_applied` prompt change (θ D3-1/D3-2) ship AND FX re-validation completes, EURUSD/GBPUSD/USDJPY/GBPJPY are not tradeable with this system.

4. **NAS100 is the Tier A1-clean instrument with strongest present-tense edge signal.** Tier A3 revalidation shows NAS100 T7 is ε-invariant (ΔsumR=0 across all buckets; legacy 0.05 vs honest 2.0 both fill identically in practice — NAS100 tick scale). CANDIDATE WR 66.7% on n=37 (22W/11L/4U; Exp +0.595R). Phase 2 γ review confirmed the NAS100 BL max_kz_trades regime shift survives Bonferroni × 96 × 3-partition (p=2.8e-4 × 3 = 8.5e-4 — fails post-hoc partition correction, but direction is robust). Current live system (max_kz_trades=1) is blocking **+40.62R of good counterfactual trades** — but this is a configuration question the T2.8 concurrent-cap architecture already addresses, not a gate-semantics fix. Leave config at 1 through Tuesday; reassess after first week of live NAS100 if shadow logger confirms.

5. **The highest-leverage CEO-approval-required changes are θ D3-1 (FX per-instrument precision) + θ D3-2 (non-zero `sl_buffer_applied`).** These two prompt changes close CLAUDE.md unresolved items #5, #7 simultaneously. Evidence: β review line 14 (corrected from β's claimed line 34) of `primary_analyzer_prompt.py` hardcodes `_PRICE_FMT=".2f"` (θ verified bit-exact at line 14); β + θ jointly show 100% of 1555 records have `sl_buffer_applied: 0.0` bit-exact; the schema literal at lines 155+236 is what the AI emits verbatim. These changes should be prepared this week (no ship) and staged for CEO approval after Tuesday's kickoff behaviour is observed. Autonomous-shippable: per-instrument `_FILL_EPSILON` in `simulate_t7_live_period.py:462` (CLAUDE.md unresolved #8; ~2-3h code fix already validated by Tier A1/A2/A3). Shadow-only proposals: d1_bias_lag_conflicts logger (T5.24 closure extension; T4 §6), hour-of-day asymmetric-vol windows (η §3-4, bound by η's TZ-bug caveat).

---

## CEO Q1 — Where is edge leaking, ranked by R-impact?

### 1A — Ranking (honest-epsilon, Phase 2/3-corrected)

| # | Leak | Best estimate of R-impact | Evidence quality | Status | Where fix lives |
|---|------|---------------------------|------------------|--------|-----------------|
| 1 | **XAUUSD regime shift (genuine, structural, uniquely-XAUUSD)** | Unmeasurable in R; CAND rate 2.5× in 2026 vs 2025 at degrading quality | HIGH — 5 independent signals cross-validate (T2 §3-7), posterior 55% | LIVE leak — **cannot be "fixed"** by code/prompt; mitigated only by de-weighting XAUUSD | Position sizing (config) + exploratory signal monitoring |
| 2 | **EURUSD FX precision bug (59.67% degenerate outputs)** | Phantom wins only; 25/25 "degenerate WINs" contribute **0R expectancy**; total R loss = opportunity cost of FX being unreliable | HIGH — Fisher p=2.78e-4, Wilson CI [0.540, 0.650], n=300 | BLOCKED — EURUSD/GBPUSD/USDJPY/GBPJPY disabled until fixed | Prompt (θ D3-1) + post-AI validator (β Finding 1 §fix) |
| 3 | **XAUUSD `entry_in_ob` L2 rejections are correctly edge-negative** (−128R net across 741 rejects, WR 34.7%) | −128R over 741 — confirms gate is pulling its weight | HIGH — γ review bit-exact | CORRECTLY REJECTING — **not a leak** | N/A (gate working as designed) |
| 4 | **NAS100 `max_kz_trades` + `max_daily_trades_sim` BLOCKED_LIMIT** (64.2% WR, +40.62R counterfactual) | +40.62R over 82 rejects; per-record Exp +0.495R | MEDIUM-HIGH — γ review; BL regime-shift survives Bonferroni × 96 | Config/architecture (T2.8 concurrent-cap already addresses) | `config/profiles/*.yaml` — keep at current until live feedback |
| 5 | **XAUUSD entry-geometry degradation (α-identified "bad entries")** (26%→50% losses mfe<0.2R) | −2 to −4R/quarter at batch n=33; paired-t p=0.9158 (α review §2.1); not Bonferroni-safe | LOW-MEDIUM — Phase 2 α review shrunk Variant C +0.128R → +0.007R | Entry-mechanics — **but T2 discriminator says this is regime-driven (10.9%→45.5% Fisher p=0.0002 XAUUSD-only)** | Position sizing on XAUUSD |
| 6 | **D1-bias-lag on 7 instruments** | +1.5R fleet-wide over 3.25 months; +8R USDJPY from 1 LOSS-first episode; EURUSD +1.5R/episode | LOW — T4 fleet Bonferroni ≪ α=0.01; individual episodes insufficient | Shadow-logger proposal only — **do NOT "fix"** | `src/components/market_state.py:identify_structure` (post-Tuesday revisit only) |
| 7 | **`_count_touches` bar-overlap production semantics** | Theoretical 50× divergence; actual 0.009% false positives, FN=0, at 168-bar live window | HIGH — T3 empirical reproduction | DOCUMENTATION ONLY — in-code comments + ADR | `src/components/market_state.py:_count_touches` comments |
| 8 | **`sl_beyond_ob` L2 strict-`<` → `<=`** (ζ Leak #1 / T2.9) | XAUUSD: −1R over 6 rejects (Exp −0.167R); NAS100: 0R (ε-invariant under Tier A3); EURUSD: −9R under honest eps | HIGH — T4.26 `0e33651` + Tier A3 | NOT A FIX — reverse polarity | N/A |
| 9 | **Universal `sl_buffer_applied: 0.0`** | Unmeasurable direct R; upstream cause of `sl_beyond_ob` geometry issues θ D3-2 | HIGH — 1555/1555 bit-exact (β Finding 2) | CEO APPROVAL — prompt change | `primary_analyzer_prompt.py:155,236` |
| 10 | **H1 POI citation hallucinations** (cite phantom POI / deny real POI) | Unmeasurable; β §Finding 3 — exploratory flag | MEDIUM — β review; not independently reproduced | CEO APPROVAL — prompt change | Prompt-side (β Finding 3 §fix) |

### 1A.1 — Per-row evidence deep-dive

**Row 1 (XAUUSD regime shift).** Five independent cross-instrument signals, each isolating XAUUSD:

1. **ADR M15 %-range.** XAUUSD M15 ADR went 13.5bp → 23.6bp Jan 2025 → Jan 2026 (1.75×). NAS100/USDJPY: flat. (T2 §3; source `data/historical_2026/` + `data/historical/` D1 CSVs).
2. **ATR/252d ratio.** Q1-26 ratio 2.16 — highest in XAUUSD series going back to 2023-Q2. Prior max was 2025-Q2 at 1.75. NAS100 ratio unchanged. (δ §1 regime table).
3. **Winner MFE compression.** XAUUSD winner MFE median 1.04R → 0.49R, Mann-Whitney p=0.020. Does NOT appear on NAS100 winners. (ε §Deliverable 3 + Phase 2 ε review corrections).
4. **Fast-loss rate.** XAUUSD loss `mfe<0.2R`: 26.9% → 69.2%, Fisher p=0.017, Z-prop p=0.011 (Bonferroni-borderline at α=0.05/6=0.0083 but direction robust). NAS100 loss MFE median 1.66R (opposite signature — losses go DEEP into profit before reversing). (ε §6, α §3, T2 §5).
5. **Bad-entry rate.** XAUUSD 10.9% → 45.5% Fisher p=0.0002 (Bonferroni-safe). Cross-instrument: 12.1% → 11.8% NAS100 (Δ=−0.3pp ns); 9.7% → 13.2% USDJPY (Δ=+3.5pp ns). **Isolation is exact.** (T2 §7).

Additionally — CAND rate explosion itself is 100% XAUUSD: 2.17% Q4-25 → 5.80% Q1-26 (+167%). NAS100 CAND went 32.3% → 27.5% (−14.9%, opposite direction). USDJPY CAND flat. The AI is CANDIDATE-flagging more XAUUSD setups in chop than in trend — exactly the pathology T7 was designed to prevent but evidently fails on V-shape intra-quarter paths.

**Row 2 (EURUSD FX precision).** Degenerate pattern (entry = SL = TP bit-exactly) appears **only on EURUSD**: 0/1053 XAUUSD, 0/202 NAS100, 179/300 EURUSD (Wilson CI [0.540, 0.650]). Contamination NOT temporally stable per Phase 2 β reviewer's re-partition: 30.68% Jan (n=88) → 72.78% Feb (n=79) → 53.33% Mar (n=45) → 100% Apr (n=88). Fisher's exact test for Jan-Feb-Apr proportion homogeneity yields p=2.78e-4 (β cited "≪1e-4" — reviewer correction). Root cause is structural: `_PRICE_FMT=".2f"` at `primary_analyzer_prompt.py:14` renders EURUSD prices (e.g. 1.09520) as "1.10", training the AI to emit 2-dp outputs. On a 4-dp EURUSD tick ladder (0.0001), a 2-dp output forces entry/SL/TP to collapse when they lie within 5pips of each other.

**Row 3 (XAUUSD `entry_in_ob` is not a leak).** XAUUSD L2 reject of reason `entry_in_ob`: 741 rejects, 34.7% WR at counterfactual replay, net −128R over the period. This is the gate correctly preventing chases. The T7 simulator replays these as L2-reject with the honest entry/SL/TP that the AI emitted; their counterfactual R is computed by forward-fill under honest_epsilon. Rejecting 741 trades that would have netted −128R is **the gate earning its keep**. Anyone looking for "missed R" in this bucket is looking for edge that isn't there.

**Row 4 (NAS100 BLOCKED_LIMIT).** The 82 blocked-limit records (60 `max_kz_trades` + 22 `max_daily_trades_sim`) resolved at 64.2% WR (43W/24L/15U), sumR +40.62R, Exp +0.495R per record. The gate structure that blocks these is `max_kz_trades=1` (FTMO profile) and `max_daily_trades_sim=3` (simulator proxy). **This is a real leak**, but it's also partially addressed by T2.8 concurrent-cap architecture (session 33 `dc4cec2`). The live question: does `max_kz_trades=1` make sense with NAS100's 60-80pt SL distances? γ's March 2026 subset analysis showed the NAS100 BL WR tracks the regime-shift signal (BL decay 93% → 40%, p=2×10⁻⁵ Bonferroni-safe at α=0.05/96) — so the counterfactual's aggregate +40R may be concentrated in one month. Conservative interpretation: wait for 2 weeks of redacted_account live NAS100 before adjusting.

**Row 5 (XAUUSD entry-geometry).** α's Phase 1 claim: XAUUSD loss-MFE<0.2R rate doubled 26%→50% post-2025-Q3. Phase 2 α review collapsed the Variant C rescue estimate from +0.128R → +0.007R/trade (paired-t p=0.9158, Wilcoxon p=0.3692). The *description* of the phenomenon remains correct (losses DO go adverse faster on XAUUSD); the *interpretation* has shifted: Phase 3 T2 assigns this to H2 Regime (V-shape chop → fast reversal on stop-out) rather than H3 Bad-entry. Practical implication: fixing this requires fixing the regime, not the entry mechanic.

**Row 6 (D1-bias-lag).** Phase 1 ζ claimed +10-25R/quarter fleet-wide impact, EURUSD +110R over 804 rejects. Phase 2 ζ review identified 50× inflation from (a) correlated samples (multi-day episodes counted per-day), (b) missing per-instrument epsilon. Phase 3 T4 reproduced ζ Phase 2 reviewer's numbers bit-exactly and extended: fleet-wide +1.5R across 11 episodes over 3.25 months at honest per-episode decorrelation. No instrument generates >+5R/quarter. USDJPY's +8R per-day collapses to 1 episode where first event was a LOSS (−1R) — sample of 1. NAS100 had one 20-day episode of D1-bearish through a +15.6% rally — the mechanism is real but the sample hasn't accumulated.

**Row 7 (production touch semantics).** T3 ran the full reconciliation: production's bar-overlap counting at the 168-bar live window produces 99.991% gate agreement with the research transition-counting semantics. 106,147 touch events evaluated, FN=0 (no production FP ≤ research), 8 false positives (production>0, research=0) = 0.009% rate. The 8 FPs have WR=12.5% — null-indistinguishable. The theoretical 50× divergence at full-history accumulation vanishes under the 168-bar rolling window because full-bar overlaps decay exponentially with bars-since-formation.

**Row 8 (T2.9 sl_beyond_ob).** Session 33 T4.26 audit (`0e33651`) showed **6/6 bit-exact XAUUSD rejects would have been −1R (Exp −0.167R)** if T2.9 shipped. NAS100 session-33 claim +13.5R: re-checked under Tier A3 honest epsilon — ε-invariant (deltas exactly 0 across all buckets; sl_beyond_ob W=26, L=20, sumR +19.0R). The EURUSD Tier A2 honest-epsilon: sl_beyond_ob +55.02R → **−9R** (all 9 "WINs" flip to LOSS because EURUSD 2-pip eps makes limits unreached). Three independent instruments tell three different stories — pattern is NAS100-specific, and even there the claim pre-dates per-instrument epsilon validation.

**Row 9 (sl_buffer_applied=0.0).** 1555/1555 records across 3 instruments emit `sl_buffer_applied: 0.0` bit-exactly (XAUUSD 1053/1053, NAS100 202/202, EURUSD 300/300). Wilson CI [0.9976, 1.0000]. The AI is complying with a schema literal at `primary_analyzer_prompt.py:155` ("sl_buffer_applied": 0.0") and `:236` (repeated inside the CANDIDATE trade_parameters block). Fix is straightforward: replace literal with a formula + instruction. Effort 4h + re-val. Closes upstream of several downstream questions (Row 8's T2.9 becomes moot if the AI computes non-zero buffers).

**Row 10 (POI citation hallucinations).** β Finding 3 qualitative report: AI sometimes cites phantom POI levels or denies real POI presence. Not independently quantified in Phase 2 or Phase 3. Flag for Phase 5 scoped re-audit against MSO records.

### 1B — What "ranked by R-impact" reveals

The sharpest finding: **4 of the top-10 leaks are either (a) not actually leaks or (b) upstream of things that would REDUCE R if naively "fixed"**:

- Row 3 is the gate working correctly. Rejecting loses on purpose.
- Row 7 requires zero code — production behaviour is materially identical to research semantics at the 168-bar window.
- Row 8 (T2.9) had 6 bit-exact XAUUSD rejects pencilled out to net −1R if reversed.
- Row 6 (D1-bias-lag) is fleet-wide +1.5R — within the measurement noise band.

**The one unambiguous R-leak is Row 4 (NAS100 BLOCKED_LIMIT)** — and it's a configuration question the T2.8 architecture already models (session 33 `dc4cec2`). The T2.8 concurrent-cap lets `max_concurrent=2`, but `max_kz_trades` is separately pinned at 1 in both profiles. If NAS100 continues post-Tuesday under shadow logging to show the +0.495R expectancy on BLOCKED trades, this is the single lever that recovers the most R with zero prompt/code change.

### 1C — Leaks that are NOT in my top-10 (and why)

| Phase 1 claim | Status |
|---|---|
| γ §4 — NO_TRADE missing winners | **Disproven** — 36-39% hit rate identical to random-direction baseline on all three instruments (γ §3-4, bit-exact match with η §2) |
| η §3-4 — GBPJPY-23 SHORT 80.7% WR (Exp +1.02R) | **Collapsed** — Phase 2 η review: on clean data (2022-2025 OOS) WR drops to 40.5%, null-indistinguishable. Root cause: `scripts/export_mt5_historical.py:81` TZ bug mislabels broker-server time as UTC; same bug at `src/mt5/mt5_real.py:58,71`. **All 10 η strong edges fail OOS.** Safe subsets: §2 (NO_TRADE null — bit-exact match with γ), §3 (CEO-candidate edge rejection — bit-exact match with γ). |
| ε §1-8 — arbitrage hypothesis | **INCONCLUSIVE with one XAUUSD-only signal** — fast-loss p=0.029 + MFE compression p=0.041 survive but fail Bonferroni. Phase 2 ε review: ε's "6/6 regime vs 3/9 arb" is rhetorical overfit; honest score is **3/3 regime-compatible vs 3/6 arb-compatible** with multiple equally-valid alternative hypotheses (bad-entry, detector-bugs, prompt-defects, measurement artefact). BH@m=12 within-family: no survivors. |
| ζ §Leak #2,#3 — OB mitigation + `_count_touches` | **By design** — Phase 2 ζ review: Leak #2 is intentional per ADR 003 + docstrings (wick-vs-body distinct events); Leak #3 explicitly documented at `market_state.py:466-481`. Both require CEO approval, not Allowed-Without-Approval. |
| δ §TL;DR #2 — regime-conditional edge "Bonferroni-safe" | **Downgraded** — Phase 2 δ review: δ's p=0.002 used erfc for Spearman, correct p=0.027 (fails Bonferroni α=0.005). Hypothesis 2 is EXPLORATORY, not confirmed. |
| β Finding 5 — `model_used` hallucinated 99.79% | **Cosmetic only** — no trade impact (β confirmed); schema fix, 1h effort |

---

## Triangulation matrix — agent agreement and disagreement

Before answering Q2, a cross-check: when multiple independent agents (Opus 4.7, max effort) examined the same underlying question, did they agree? Five cross-agent triangulations emerged from this audit. The score here matters: convergent findings from agents who didn't see each other's outputs carry substantially more weight than any single agent's claim.

### Triangulation 1 — NO_TRADE null result (γ, η, ε)

**Question:** Does the NO_TRADE bucket contain missed winners that the system should be taking?

- γ §3: NO_TRADE forward hit-rate at +1.5ATR / 4h: XAUUSD 36.6%, NAS100 38.0%, EURUSD 39.2%. (n=402, 613, 806 respectively).
- η §2: Same geometry, independent script: XAUUSD 37%, NAS100 38%, EURUSD 40%.
- ε §Deliverable 2: Post-entry baseline 37-40%.
- γ baseline (random direction, random entry): XAUUSD 36.6% LONG / 44.5% SHORT.

**Verdict:** Bit-exact within 1pp across 3 agents. Very high confidence in null result. **There is no "missed winners" cluster in NO_TRADE.** This kills the "AI is too conservative at NO_TRADE gate" hypothesis definitively.

### Triangulation 2 — XAUUSD-specific regime signal (T2, ε, δ, α, γ, β)

**Question:** Does the edge decay pattern isolate to XAUUSD?

- T2 Phase 3: 5 XAUUSD-specific signals isolated, posterior 55% H2.
- ε §6-7: Fast-loss and MFE compression on XAUUSD only.
- δ §1: 2026-Q1 XAUUSD ADR 169.7 (5× 2025-Q1 baseline); NAS100/USDJPY/GBPJPY all stable.
- α §2.1: XAUUSD bad-entry 26→50% but "non-significant at split level" — consistent with T2's regime-driven interpretation.
- γ §5: NAS100 has its own regime shift (BL decay 93→40%) but OPPOSITE sign (NAS100 is becoming easier, XAUUSD is becoming harder).
- β Finding 1: EURUSD has its own pattern (59.67% degenerate) — and it's NOT XAUUSD-like, which further isolates XAUUSD.

**Verdict:** 6 agents, 1 instrument isolation. **Very high confidence XAUUSD regime is structural and uniquely localized.**

### Triangulation 3 — Prompt/schema literal compliance (β, θ)

**Question:** Is the AI emitting schema literals verbatim (non-reasoning compliance) rather than computing values?

- β Finding 2: `sl_buffer_applied: 0.0` on 1555/1555 records, Wilson CI [0.9976, 1.0000].
- θ §2: Line 155 + 236 contain the literal text "sl_buffer_applied": 0.0". Prompt does NOT instruct AI to compute.
- β + θ both independently propose the same D3-2 fix.

**Verdict:** Two independent code inspections + data re-counts. **Very high confidence, bit-exact.**

### Triangulation 4 — `sl_beyond_ob` T2.9 claim revised (ε, ζ, T3.2 session-33 audit)

**Question:** Should T2.9 (strict `<` → `<=`) ship?

- ε §6 confirmed original claim at Phase 1 level.
- ζ §Leak #1 claimed +10-25R/quarter fleet-wide impact.
- Phase 2 ζ review + T4.26 `0e33651` audit: XAUUSD 6/6 bit-exact rejects net −1R.
- Tier A3 NAS100 revalidation: ε-invariant (ΔsumR=0), so NAS100 session-33 claim +13.5R neither gained nor lost under honest eps.
- Tier A2 EURUSD revalidation: sl_beyond_ob +55→−9R — FLIPS direction.

**Verdict:** Three separate research efforts confirm T2.9 is net-negative or neutral on all clean instruments. **High confidence: DO NOT SHIP.**

### Triangulation 5 — TZ bug self-consistency (T1 phase 3 vs η phase 2)

**Question:** Does the TZ mislabel at `scripts/export_mt5_historical.py:81` affect live production?

- η Phase 2 review: η's hour-of-day findings COLLAPSE OOS because of TZ bug in export script. ALL 10 survivors fail on corrected data.
- T1 Phase 3: Price math NOT distorted. KZ gating uses UTC wall-clock; MT5 candles carry prices correctly. Live system self-consistent even with mislabel.

**Verdict:** Two agents investigating independent facets. Research artefacts (η) are poisoned; live system (T1) is safe. **Synthesis: no pre-Tuesday action needed, post-Tuesday research hygiene required.**

### Triangulations showing agent DISAGREEMENT (conflicts resolved)

**Conflict 1 — Variant C partial-close rescue estimate.**
- α Phase 1: +0.128R/trade rescue, 9/9 losing trades saved.
- α Phase 2 review: collapses to +0.007R/trade, paired-t p=0.9158, Wilcoxon p=0.3692.
- **Resolution:** Phase 2 review's defensible assumption dominates. The +0.128R was an over-counted estimate not supported by paired-t.

**Conflict 2 — δ Spearman p-value on regime-filter hypothesis.**
- δ Phase 1: p=0.002 via erfc, survives Bonferroni α=0.005.
- δ Phase 2 review: p=0.027 via correct t-dist Spearman, FAILS α=0.005.
- **Resolution:** Phase 2 reviewer's correct t-dist calculation is standard; δ Phase 1 used wrong distribution. Hypothesis DOWNGRADED to exploratory.

**Conflict 3 — Canonical 73.2→59.4 decay sequence.**
- δ Phase 1: "does not reproduce bit-exact from my aggregation"; proposes the sequence is post-hoc selection.
- Phase 2 δ review: confirms — sequence is hardcoded at `research/academic_pipeline/L4_foundation_analysis.py:649`; same script computes 70.7% at lines 685-694, contradicting the 73.2 hardcode.
- **Resolution:** Hardcoded artefact. Actual 2026-Q1 59.4% WR on n=32 IS real but post-hoc-selected from a ragged series.

**Conflict 4 — ζ's R-impact estimates.**
- ζ Phase 1: Leak #1 +10-25R/quarter fleet-wide, EURUSD +110R.
- ζ Phase 2 review: 50× inflation from correlated samples + missing per-instrument epsilon; EURUSD +1.5R/episode.
- T4 Phase 3: Reproduces ζ reviewer's numbers bit-exact; fleet +1.5R over 3.25 months.
- **Resolution:** 50× inflation is the correct correction factor. Phase 4 uses reviewed numbers throughout.

**Conflict 5 — β's line-number citations.**
- β Phase 1: `_PRICE_FMT` at line 34.
- β Phase 2 review + θ Phase 2 review: `_PRICE_FMT` at line **14**.
- **Resolution:** Line 14 is correct (θ bit-exact verified; β reviewer confirmed). β Phase 1 had a citation error that propagated nowhere substantive.

**No load-bearing unresolved conflicts remain** after Phase 2+3.

---

## CEO Q2 — Is the market arbitraging our edge, or is execution degrading?

### 2A — The central finding

**Phase 3 T2 cross-instrument discriminator answers this definitively: regime change on XAUUSD, not execution or arbitrage.**

T2's 5-hypothesis posterior (T2 §8, Confidence 4/5):

| Hypothesis | Prior | Likelihood | Posterior |
|------------|------:|-----------:|----------:|
| H2 — Regime change on XAUUSD | 0.25 | 4 signals XAUUSD-only, flat elsewhere | **0.55** |
| H1 — Market arbitraging edge | 0.20 | partial on XAUUSD, absent on NAS100/USDJPY | 0.15 |
| H4 — Detector bugs (ζ Leak #1/#2/#3) | 0.20 | all 3 reviewed as design/behavior, not bugs; impact ≤1.5R | 0.12 |
| H3 — Bad-entry geometry | 0.20 | α review: Variant C +0.128R → +0.007R; non-significant | 0.10 |
| H5 — Prompt defects | 0.15 | β/θ both regression to no edge-gate-R-impact | 0.08 |

### 2B — Why H2 wins — the invariance argument

**The entire T7 corpus was built in a single batch on 2026-04-04.** Code, model (Sonnet 4.6), prompt, and framework choice were CONSTANT across Jan→Apr. If the AI-side or code-side were degrading, it would degrade uniformly across instruments over calendar time. Instead:

- **Market regime CHANGED** on XAUUSD (M15 %-range 13.5→23.6bp 1.75×; ADR 36.4→169.7 4.66×; ATR/252d 2.16 — highest on record; V-shape with 19.2% max drawdown; AC1 flipped −0.09→+0.11).
- **XAUUSD CANDIDATE rate EXPLODED** (2.17% Q4-25 → 5.80% Q1-26, +167%) at uniquely-high adversity (KER=0.033 end-of-quarter, 5× choppier).
- **Bad-entry rate 10.9%→45.5%** (Fisher p=0.0002) on XAUUSD ONLY. Not on NAS100, USDJPY, GBPJPY.
- **Winner MFE compressed** (1.04→0.49R, p=0.020) on XAUUSD ONLY.
- **Fast-loss rate** (losses mfe<0.2R) 26.9→69.2% (Fisher p=0.017) on XAUUSD ONLY.

Five XAUUSD-specific structural signals + ZERO code/prompt/model change = **H2 dominates posterior**.

### 2C — What would falsify H2

- A week of live NAS100 data at degraded WR (but live Apr-Oct will carry different sample, so insufficient alone).
- A cross-instrument regression where CANDIDATE CR and WR move together across all 5 instruments — currently ONLY XAUUSD exhibits this.
- Reproducing the degradation on a fresh 2026-Q2 XAUUSD OOS that had NOT been in-sample during the 2026-04-04 batch build — scheduled for Tier A post-redacted_account.

### 2D — What this means for strategy

- **H1 Arbitrage at 15% is non-zero.** ε §6-8 showed two XAUUSD-only signals (fast-loss, MFE compression) that ARE consistent with liquidity arbitrage — but so is a regime shift to higher-vol / noisier chop. These two hypotheses are observationally equivalent on this dataset.
- **H4 Detector-bugs at 12% is largely distraction.** Phase 2 ζ review (§7) reviewed-added `_count_touches` bar-overlap finding; Phase 3 T3 empirically bounded its impact at 0.009% FP / FN=0 in live. The other two ζ "leaks" are ADR-003-validated design choices. ζ's R-impact estimates were inflated 50× in the original Phase 1 artefact.
- **H3 Bad-entry at 10%.** Phase 2 α: Variant C rescue shrinks to +0.007R/trade (paired-t p=0.9158, Wilcoxon p=0.3692). The "26%→50% bad-entry rate" is real — but Phase 3 T2 places it downstream of H2 regime (as a *symptom* of chop, not root cause).
- **H5 Prompt at 8%.** FX precision bug (β Finding 1) IS the one prompt-side root cause — but it's EURUSD only. Since EURUSD is not live and not Tuesday-candidate, H5 contributes ~0% to the XAUUSD decay question. For FX readiness, H5 is 100% of the decision (and blocks it).

### 2E — Concise CEO-facing answer

> "Not arbitraged. Not execution. Gold's market state shifted around late-2025/early-2026 (5× ADR, V-shape, 19% max drawdown) and the OB-retest strategy is disproportionately hurt on XAUUSD while the same unchanged code, same Sonnet 4.6, same prompt continues to work fine on NAS100 and USDJPY. The right response is **size-down XAUUSD, not rebuild the edge.** The next 3-6 months will test whether gold mean-reverts to 2025 regime or stays elevated-vol — at which point we revisit."

### 2F — Why the arbitrage hypothesis (H1) posterior is not zero

Three independent signals retain consistency with arb beyond the regime story:

1. **ε §6 fast-loss rate XAUUSD-only.** The mechanism of losses going adverse within the first 2 candles is at least *as consistent* with algo stop-hunts as it is with chop. But it's also consistent with trailing SL placement being poor under expanded vol (our SL at 1×ATR becomes more likely to be tagged when ATR doubles).
2. **ε §Deliverable 4 small-sample reversal signature** (n=4, Fisher p=0.040). Per Phase 2 ε review, this is a "legitimate small-sample test that is also a dice roll" — four records out of 16 losing CANDIDATEs met the bit-exact SL touch + ≥1R reversal signature. With four observations, Fisher flags it nominally significant but the test has near-zero power to distinguish arb from noise.
3. **ζ's reviewer-added `_count_touches` semantic mismatch.** If a live execution environment has more OB-proximate retest activity than our research corpus (because algos are teaching each other where OB edges are), the production semantic would systematically over-count. T3 bounded this at 0.009% — effectively nothing. Arb signal is null here.

Bottom line on H1: any serious re-weighting toward arb hypothesis requires a longer OOS sample. Phase 5 pre-registration R2 (6 months × 5 instruments × algo-density-rank Spearman) is the right discriminator.

### 2G — What would shift the posterior toward H4 (detector bugs)

A clean experiment: rebuild `market_state.py` with the ζ-reviewer's alternative `_count_touches` semantics, re-run T7 on 2025-Q4 XAUUSD (where edge was 73.9%) and 2026-Q1 XAUUSD (where edge was 59.4%). If alternative-semantics recovers WR materially in Q1 AND preserves it in Q4, the detector is the fix. T3 evidence strongly predicts this will NOT work — the 168-bar window collapses both semantics to near-identity. But the experiment is ~4h and would close the H4 prior hard.

### 2H — Monotone vs non-monotone decay framing

Phase 2 δ review established the canonical 73.2→71.4→63.6→59.4% sequence is a hardcoded artefact at `research/academic_pipeline/L4_foundation_analysis.py:649`. The actual δ-reproduced XAUUSD quarterly WR sequence across 131 trades is **50.0 → 80.0 → 33.3 → 65.6 → 50.0 → 60.0 → 73.9 → 59.4** (2024-Q2 through 2026-Q1). The 73.9% → 59.4% Q4-25 → Q1-26 step IS real (Δ=14.5pp on n=23 vs n=32), but it's one data point on a ragged series. The "monotone four-step decay" story is post-hoc selection; the "2026-Q1 is unusually bad" story is the defensible version.

---

## CEO Q3 — Top 3-5 restoration/edge-upgrade changes

All specified as **"recommended for CEO approval"** or **"shippable autonomously"** per the constraint.

### Change 1 — Per-instrument `_FILL_EPSILON` in `simulate_t7_live_period.py` [SHIPPABLE AUTONOMOUSLY, 2-3h]

**What:** Replace `_FILL_EPSILON = 0.05` hardcode at `scripts/simulate_t7_live_period.py:462` with the `EPSILON_BY_SYMBOL` table (XAUUSD=0.20, NAS100=2.0, USDJPY/GBPJPY=0.02, EURUSD/GBPUSD=0.0002) that Tier A1/A2/A3 validated.

**Why:** This is a research-tool fix, not a live-code fix. Every FX/index T7 counterfactual in sessions 32-34 is suspect until this lands. Tier A2 shows EURUSD sl_beyond_ob claim flips from +55R to −9R; Tier A3 shows NAS100 ε-invariance confirming session-33 +13.5R claim is not an epsilon artefact. Without this fix, any Phase 4+ simulation we run will generate the same mis-scaled R estimates that led to the T2.9 near-ship error.

**CEO approval:** NO — tooling / research-infra fix, not trading behaviour.

**Closes CLAUDE.md unresolved:** #8 fully.

**Risk:** Low. Fix is isolated to `simulate_t7_live_period.py`; no dependency on live code.

**Artifact citations:** `scripts/simulate_t7_live_period.py:462`, `EPSILON_BY_SYMBOL` at `:80`, Tier A1 revalidations at `research/b_deep_audit_2026-04-19/tier_a/epsilon_revalidation.py`, Tier A2 `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_epsilon_revalidation.md`, Tier A3 `NAS100_epsilon_revalidation.md`.

---

### Change 2 — `_PRICE_FMT` per-instrument override in `primary_analyzer_prompt.py` (θ D3-1) [CEO APPROVAL REQUIRED]

**What:** Change `_PRICE_FMT = ".2f"` literal at `src/prompts/primary_analyzer_prompt.py:14` (β said line 34 — corrected to **line 14** by θ bit-exact verification + Phase 2 β reviewer's correction) to a per-instrument format map:
- XAUUSD, US30 → `.2f` (status quo)
- USDJPY, GBPJPY → `.3f`
- EURUSD, GBPUSD → `.5f`

Plus: add post-parse validator in `primary_analyzer.py` that rejects any response where `abs(entry − sl) < instrument_epsilon` OR `abs(entry − tp) < instrument_epsilon`. Reject → REJECTED_COVERAGE, logged to shadow.

**Why:** β Finding 1 quantifies 59.67% of EURUSD CAND records as bit-exactly degenerate (n=179/300; Wilson CI [0.540, 0.650]; Fisher p=2.78e-4). The Phase 2 β reviewer identified the contamination is **not temporally stable**: 30.68% Jan → 72.78% Feb → 53.33% Mar → 100% Apr. Root cause is 2-dp rendering on 4-dp FX instruments (4th-decimal tick = 0.0001, rendered to 2-dp forces entry=SL=TP collapse). This single change closes:

- CLAUDE.md unresolved #5 (T2.prompt — non-zero `sl_buffer_applied` becomes trivial once FX precision is fixed)
- CLAUDE.md unresolved #7 (EURUSD/GBPUSD/USDJPY/GBPJPY FX AI precision)
- Implicitly enables all 4 FX instruments to be Tuesday-ready (after re-validation sim).

**CEO approval:** YES — prompt change affecting trading logic. WF-1 gate applies even if deprioritized.

**Effort:** 4-8h code + full per-instrument batch re-validation (all 4 FX sims need re-run under corrected prompt; budget ~$40 across 4 instruments × Jan-Apr 2026).

**Risk:** Medium. The prompt format change is low-risk in isolation, but post-AI validator introduces a new reject class — the canary fixture battery (12 baseline + 4 borderline XAUUSD) is XAUUSD-only, so FX behaviour is unguarded. Mitigation: run FX sims first as gate-release check, then live at 0.5% sizing for 2 weeks.

**Artifact citations:** `src/prompts/primary_analyzer_prompt.py:14` (verified θ bit-exact; β Phase 2 reviewer corrected from β's line-34 claim); β Finding 1 evidence `research/b_deep_audit_2026-04-19/phase1/_beta_scratch/integrity_summary.json → EURUSD.degenerate`; θ Phase 2 review §D3-1; Phase 2 β review of temporal stability.

---

### Change 3 — Non-zero `sl_buffer_applied` in prompt schema (θ D3-2) [CEO APPROVAL REQUIRED]

**What:** Replace the hard-coded literal `"sl_buffer_applied": 0.0` at `primary_analyzer_prompt.py:155` and `:236` with a per-instrument minimum buffer formula and explicit instruction to the AI to compute a non-zero value. Example formula (needs calibration): `sl_buffer_applied = max(0.25 × ATR_M15, instrument_epsilon × 3)`.

**Why:** β Finding 2 + θ §2: **100% of 1555 records** (1053 XAUUSD + 202 NAS100 + 300 EURUSD) emit `sl_buffer_applied: 0.0` bit-exactly. This is AI *compliance* with a schema literal, not AI reasoning. Combined with the T2.9 audit finding that bit-exact SL rejects on XAUUSD net to −1R (6 rejects × mean −0.167R), the AI never reasons about SL-beyond-OB geometry — it just emits zero. Making this a live formula unlocks the 2.9 reject-class without requiring the T2.9 gate change (which Phase 2 established as NAS100-specific + possibly epsilon-mis-scaled).

**CEO approval:** YES — prompt change.

**Effort:** 4h + per-instrument batch re-validation (can be bundled with Change 2).

**Risk:** Medium. Changing the AI's reasoning on SL geometry is a behaviour change; expect CAND rate to drop 2-5pp on XAUUSD as some previously-CAND setups shift to L2 rejection.

**Closes CLAUDE.md unresolved:** #4, #5 simultaneously.

**Artifact citations:** `primary_analyzer_prompt.py:155,236` (verified θ bit-exact; Phase 2 β reviewer confirmed); β Finding 2 evidence; θ Phase 2 review §D3-2.

---

### Change 4 — XAUUSD position sizing reduction [CEO APPROVAL REQUIRED]

**What:** Reduce XAUUSD `risk_per_trade_pct` from 1.0% (redacted_account profile default) to 0.5% as a response to H2 Regime Posterior 55%. Effective until one of:
- 2 consecutive months of XAUUSD WR ≥65% on live (regime reversion signal), OR
- Shadow vol-regime cutout logger shows 4 consecutive weeks of KER>0.25 on D1 XAUUSD (trend restoration).

**Why:** Phase 3 T2 §9 recommendation "XAUUSD size down, prioritize US30/USDJPY". The edge mechanism — OB-retest stop-cascade mean reversion to pre-cascade equilibrium — remains valid in trending regimes (Hurst 0.71 persistent). It breaks in V-shape chop (Q1-26 KER=0.033 end-of-quarter, highest-hostility on record). Sizing down preserves the option to re-scale when regime reverts without losing the observation sample.

**CEO approval:** YES — config change affecting trade decisions.

**Effort:** 15min (profile overlay edit).

**Risk:** Low. Reduces but does not eliminate exposure; maintains signal collection.

**Notes:** Do NOT couple this with the FX precision fix timeline. XAUUSD sizing-down is *regime-response*, while FX-enable is *prompt-fix*. Two independent decisions.

---

### Change 5 — D1-bias-lag shadow logger (T5.24 extension) [SHIPPABLE AUTONOMOUSLY, 2-4h]

**What:** Extend the T5.24 `d1_bias_lag_conflicts.jsonl` shadow logger (closed session 34, `0f2dee0`) to capture:
- Signal time and instrument
- D1 bias (identify_structure output) at signal time
- D1 last-10-candle slope + H1 bias
- Hypothetical outcome if D1-bias had matched H1/short-term bias instead

**Why:** Phase 3 T4 §6 explicit recommendation: "Post-Tuesday shadow-logger to re-measure honestly." T4 established the fleet-wide honest impact is +1.5R over 3.25 months (noise), but THE MECHANISM IS REAL — NAS100 D1 bearish for 20 days through a +15.6% rally. The question is whether the mechanism accumulates to actionable R over a longer sample. Threshold to re-propose a fix: ≥4 episodes cross +3R each, fleet ≥+12R, p<0.01 Bonferroni.

**CEO approval:** NO — shadow logging only, no decision impact.

**Effort:** 2-4h.

**Artifact citations:** T4 §6; ζ Phase 2 review §Leak #1 correction; existing T5.24 precedent.

---

### Changes I am explicitly NOT recommending

| Change | Why not |
|--------|---------|
| T2.9 `sl_beyond_ob` strict-`<` → `<=` | XAUUSD: 6 bit-exact rejects net −1R (Exp −0.167R per T4.26 `0e33651`). NAS100: ε-invariant under Tier A3, but the +13.5R session-33 claim still suspect pending Phase 2 δ's 12× CAND-rate discrepancy investigation. **Do not ship.** |
| ζ Leak #2 (OB mitigation wick-vs-body) | Intentional per ADR 003 + docstring citations (Phase 2 ζ review). |
| ζ Leak #3 (`_count_touches` off-by-one) | Phase 3 T3 empirically: 99.991% agreement, FN=0, FP=0.009% at 168-bar window. Documentation only. |
| ζ Leak #4 (first-15-min KZ edge) | n=19, Bonferroni-borderline, not forward-confirmed. Put on watch. |
| η §3-4 operationalizing hour-of-day edges | All 10 collapse OOS under Phase 2 η review (GBPJPY-23 80.7→40.5%). The TZ bug at `scripts/export_mt5_historical.py:81` poisons the entire hour-of-day analysis. Do NOT ship. |
| δ §TL;DR #2 regime-filter gate | Phase 2 δ review: Spearman p=0.027, fails Bonferroni. Exploratory, not actionable. |
| NO_TRADE hit-rate edge (γ §4, η §2) | Both bit-exact match their own random baseline — null result confirmed. Not an edge. |

---

## CEO Q4 — New patterns to explore (research-only, not ship)

### Q4.1 — Vol-regime cutout shadow logger [HIGH-PRIORITY RESEARCH]

**Hypothesis:** XAUUSD edge is *regime-conditional* on KER ≥ 0.2 on D1 (Phase 2 δ review: Spearman correct p=0.027 fails Bonferroni but direction robust; Phase 3 T2: edge present 2025-Q4 at KER=0.412, collapses 2026-Q1 at KER=0.033).

**What to build:** Nightly cron computes `kaufman_er_d1_10d` per instrument, logs to `shadow_logs/regime_cutout.jsonl`. No decision impact. Sample size: wait 3 months (~Jul 2026), then Spearman on WR × KER across all live trades. If ρ > 0.4 @ n ≥ 50 with p < 0.01 → propose live-gate.

**CEO approval:** NO (shadow only).

**Effort:** 1 day.

**Risk:** None.

---

### Q4.2 — FX precision fix post-mortem [HIGH-PRIORITY RESEARCH]

**Hypothesis:** With Change 2 (θ D3-1) + Change 3 (θ D3-2) shipped and FX re-validated, EURUSD/GBPUSD/USDJPY/GBPJPY CAND rates will materially re-distribute. Some currently-degenerate REJECTED_L2 records will become real L2 rejects (~non-degenerate); some currently-degenerate CANDs will become real CANDs.

**What to build:** Once the prompt change ships, re-run the same Jan-Apr 2026 period on a fresh batch and compare CAND/L2/NO_TRADE distributions to the pre-fix baseline. If post-fix FX CAND WR ≥ 60% on n ≥ 30 per instrument, propose FX live enablement.

**CEO approval:** Implicit in Change 2 approval (sim tooling).

**Effort:** ~$40 API cost × 4 instruments = ~$160 + 30 min setup.

---

### Q4.3 — Cross-instrument edge-density correlation [MEDIUM-PRIORITY]

**Hypothesis:** If the market is arbitraging our edge (H1), we expect edge decay to track *informal algo-density rank* (e.g., XAUUSD > NAS100 > FX-majors > JPY-crosses). Phase 1 ε tested this with n=5 and ρ=−0.21 (insufficient). Phase 3 T2 effectively rejected H1 at 15% posterior using cross-instrument invariance — but a longer OOS sample would sharpen this.

**What to build:** Pre-register a Phase 5 test: once live carries 6 months across 5 instruments, compute Spearman(decay_rate, algo_density_rank). If ρ > 0.6 @ n ≥ 5 with p < 0.05 → revisit H1 posterior upward.

**CEO approval:** NO (research pre-registration).

**Effort:** 0 until sample accumulates.

---

### Q4.4 — Hour-of-day edges on CORRECTED data [MEDIUM-PRIORITY]

**Hypothesis:** After TZ bug fix at `scripts/export_mt5_historical.py:81` + `src/mt5/mt5_real.py:58,71` (Phase 2 η + Phase 3 T1 identified — broker-server time mislabel), re-run η §3-4's hour-of-day scan. If any of the 10 originally-Bonferroni-surviving edges *also* survives OOS on 2022-2025 corrected data, those become real complementary edges.

**What to build:** Apply TZ fix (Phase 3 T1 "Strategy B" — ~1 day effort), re-extract historical 2022-2025, re-run η's 330-test scan.

**CEO approval:** Strategy B fix is research-side, so NO for the scan. TZ fix itself is also research-infra, NO approval needed.

**Effort:** 1 day TZ fix + 4h re-scan.

**Key caveat:** **Phase 3 T1 established live system is TZ-self-consistent** — MT5 candle prices are correct at wall-clock time, and KZ gating uses real UTC. Live behaviour is unaffected; the bug is purely in the *labels*. So no Tuesday delay is needed; this is a post-Tuesday research hygiene fix.

---

### Q4.5 — Post-Tuesday drawdown vs CAND-rate shadow [MEDIUM]

**Hypothesis:** redacted_account Stellar 2-Step has a 5% drawdown limit (per redacted_account profile). During Q1-2026 XAUUSD regime, CAND rate tripled (2.17%→5.80%) — meaning under redacted_account, the system would have tried to open 3x more trades during the most adverse regime on record. Does it also survive the drawdown?

**What to build:** Shadow-log during live: for each live trade, record `candidate_rate_this_week` (rolling), `d1_ker` at signal time, `drawdown_current`. Test hypothesis H(DD) = f(CAND_rate × inverse_KER).

**CEO approval:** NO (shadow).

**Effort:** 2h integration with existing shadow loggers.

---

### Q4.6 — Reconcile T7-sim CAND rate vs session-KB CAND rate [HIGH-PRIORITY BUG]

**Discrepancy:** Phase 2 γ review surfaced a 12× CAND-rate discrepancy on XAUUSD: T7 simulation reports 10 CANDIDATEs across 2100 records (0.48%), while δ's session KB sample reports 48 CANDIDATEs across the same period (~2-5%). These are nominally the same data (same Jan-Apr 2026 window, same model, same prompt, same framework).

**Likely causes (in order of probability):**
1. T7 sim drops CANDIDATEs at L2 stage that session KB keeps (L2 is post-CANDIDATE in production, pre-CANDIDATE in sim harness).
2. T7 sim's pre-screen filtering is stricter than live pre-screen.
3. Session KB includes BACK-FILLS and REPLAY CANDIDATES that T7 sim dedups out.

**What to build:** Walk 10 XAUUSD session-KB records that are CAND in KB and see where they resolve in T7 sim (CAND / L2-reject / BLOCKED / NO_TRADE / missing). This maps the drop-stage and identifies the filter discrepancy.

**CEO approval:** NO (research diagnostic).

**Effort:** 4h.

**Importance:** Every Phase 1/2/3 claim built on T7 sim CAND rates (δ §3 "+167% CAND rate explosion", γ §4 L2 counterfactuals, ε §Deliverable 1 pre-MFE) is conditional on this discrepancy being resolved. If T7 sim is systematically under-flagging CANDIDATEs, the regime-shift posterior could shift.

---

### Q4.7 — H4/M15 timeframe rendering contradiction (θ reviewer-added) [LOW]

**Finding:** θ Phase 2 review identified a contradiction between prompt line 122 (claims H4 rendering is excluded when M15 is primary) and rendering code at line 371 (appears to include H4 unconditionally). Not independently quantified.

**What to build:** Inspect `src/prompts/primary_analyzer_prompt.py:122` and `:371` with MSO snapshots from 5 instruments. If H4 IS being rendered when line 122 says it shouldn't, the AI is seeing 30-40% more context than the prompt design assumes. May or may not affect decisions.

**CEO approval:** NO (research).

**Effort:** 2h.

---

## Tuesday 2026-04-21 redacted_account Kickoff — Per-Instrument Recommendations

**Framework:** GO / CONDITIONAL GO / NO-GO. Conditional = start but with explicit watch criteria + cutback rules.

### XAUUSD: **CONDITIONAL GO at 0.5% risk**

- **Rationale:** Primary revenue instrument historically. Phase 3 T2 posterior 55% H2 Regime suggests the 2026-Q1 degradation reflects unprecedented adversity (KER=0.033, V-shape 19.2% drawdown), not a broken system. The mechanism is valid in trending regimes; we cannot predict when gold reverts.
- **Size:** 0.5% instead of 1.0% (Change 4). Reduction is temporary; re-evaluate monthly.
- **Watch criteria (hard cutback to 0% at any):**
  - 3 consecutive losses on XAUUSD
  - Week-1 drawdown from XAUUSD > 2% of account
  - Live CAND rate > 8% (signals chop-flood — would indicate Q1 regime persists)
  - MTM equity drops below −3% of peak
- **Expected frequency:** Given 2026 rate 5.80%, ~17 CANDs/month at redacted_account; at 0.5% risk, 0.5R loss = 0.25% of account; 5R profit = 2.5% — profile compatible.
- **Evidence:** Phase 3 T2 recommendation §9; Phase 2 δ review §Stationarity Section 5; Phase 1 α review §2 (bad-entry rate still inside noise at batch level).
- **Specific regime-context for Tuesday trading window:** Gold spot price is ~$3,450 as of audit close (2026-04-19). If the V-shape from Q1 has already topped and we are in a post-peak mean-reversion, the next 4-6 weeks could see regime normalization — which would VALIDATE sizing-down approach (we preserve capital for when edge returns). If instead gold continues elevated-vol through May-June, the 0.5% sizing becomes the default for the quarter. First 10 XAUUSD signals this week will be the trim check.
- **Model-decision consistency check:** Canary fixtures 12 baseline + 4 borderline XAUUSD were computed under Sonnet 4.6 effort=max on 2026-04-04 batch. Any Tuesday canary discrepancy >1 flip on baseline or >ceil(0.75×N) mismatch on borderline triggers investigation per T1.3.1.
- **Confidence of GO recommendation:** 85% GO, 15% should-be-0%. The 15% scenario is gold-goes-nuts-further (ADR 200+ daily), in which case even 0.5% sizing catches unsafe fills under spread expansion. Pre-Tuesday: confirm redacted_account demo account spread on XAUUSD is within historical normal (typical 30-50 cents).

### US30: **GO at 1.0% risk**

- **Rationale:** Live-validated on FTMO demo since April 7. Phase 2 γ review: BL regime-shift signal survives Bonferroni × 96 at p=2×10⁻⁵ (post-hoc partition correction fails, but direction robust). Confirmed independent of XAUUSD regime.
- **Size:** 1.0% (redacted_account default).
- **Watch criteria (standard emergency stops from CLAUDE.md apply):**
  - 2+ trades per single kill zone
  - 5 consecutive losses
  - Correlation exposure > 2% simultaneously with XAUUSD
- **Evidence:** Phase 3 T2 §8 (US30 not among XAUUSD-specific regime signals); Phase 1 γ review; `.context/LIVE_STATE.md` live-status confirmation.
- **US30-specific batch statistics:** CLAUDE.md canonical WR 58.5% on n=41 at p=8.34e-3 (passes Bonferroni). Expected frequency ~3-4 CANDs/month on current hitrate. At 1% risk the loss-R is 0.67% account (US30 1R ≈ 40pt SL → 0.67% at 1% account risk target). 5-consecutive-loss trigger at 3.35% account drawdown — inside redacted_account 5% floor but conservative.
- **H16 US30 sweep divergence monitor** (active shadow logger since April 11): US30 68% vs XAUUSD 31% continuation baseline. Alerts if US30 <55% or XAUUSD >45% over 50 sweeps. Active and running. No action pre-Tuesday.
- **Confidence:** 95% GO.

### USDJPY: **GO at 1.0% risk**

- **Rationale:** CLAUDE.md canonical WR 75.8% (n=33, p=1.96e-4, Bonferroni-safe). Phase 3 T2 established USDJPY is NOT in the XAUUSD regime-signal group — its baseline behaviour is preserved. Phase 1 η's USDJPY hour-23 edges (80.7% GBPJPY-23 SHORT analog) collapse OOS, so no η-derived config change, but USDJPY's core OB-retest edge is independent of η.
- **Size:** 1.0%.
- **Watch criteria (standard + additional):**
  - If D1-bias-lag logger fires on USDJPY-specific episodes (T4 caveat: +8R fleet USDJPY driven by 1 LOSS-first episode — sample-of-1)
  - 2+ losses in a single kill zone
- **Evidence:** CLAUDE.md canonical; Phase 3 T2; γ review.
- **USDJPY-specific FX precision note:** USDJPY uses `.3f` format in the current `_PRICE_FMT` map (per θ §1 token counts table). 3-dp FORMAT is APPROPRIATE for USDJPY's ~0.010 pip structure, so USDJPY is NOT affected by the EURUSD 2-dp degeneracy bug. Phase 2 β's degenerate-rate tables confirm: USDJPY degenerate rate 0% on sampled records. **USDJPY is FX-precision-safe without Change 2 shipping.**
- **Kill zone coverage:** USDJPY has THREE kill zones (London 07:00-09:30, NY 13:00-15:30, Tokyo 00:00-03:00) per CLAUDE.md KZ table. Most coverage of any instrument. Expected frequency scales: CLAUDE.md note "expected ~17 trades/month across all instruments" includes USDJPY contribution.
- **Confidence:** 95% GO.

### GBPJPY: **GO at 1.0% risk**

- **Rationale:** CLAUDE.md canonical 57.1% (n=42, p=0.031 raw, does NOT survive Bonferroni). Live-demo validated since April 7. Phase 2 η review collapsed the GBPJPY-23 SHORT hypothesis entirely (η's 80.7% → 40.5% OOS); this does NOT affect the core OB-retest edge, which γ/T2/T4 all confirm remains directionally valid on GBPJPY.
- **Size:** 1.0%.
- **Watch criteria:** Standard. Additional: if GBPJPY 2026 live WR < 55% on first 10 trades, revisit sizing.
- **Evidence:** CLAUDE.md canonical; Phase 2 η review (edge removed); γ NO_TRADE null preserved.
- **JPY cross precision:** GBPJPY uses `.3f` format — same as USDJPY. Degenerate rate 0% on β's sampled records. **FX-precision-safe.**
- **Weakest GO recommendation of the four live instruments.** Raw 57.1% WR with p=0.031 doesn't survive Bonferroni, and the η-derived "hour 23 short edge" that might have augmented GBPJPY performance has been debunked. GBPJPY is live-trading because (a) live-demo validated since April 7 without incident, (b) provides useful diversification against gold+index-heavy fleet exposure, (c) JPY_CROSSES correlation with USDJPY provides hedge-like behaviour during cross-asset stress. But the individual WR signal is weakest of the GO-4.
- **Confidence:** 80% GO. The 20% risk-adjusted concern: if both GBPJPY AND USDJPY trigger simultaneously (correlation exposure), we hit the 2% cap. Standard gates apply; no special accommodation needed.

### GBPUSD: **NO-GO (stay observer at current cost)**

- **Rationale:** CLAUDE.md memo "GBPUSD observer cost — keep through April 2026 at ~$10/mo" (CEO decision 2026-04-18). GBPUSD is currently in observer mode only, not live-trading. redacted_account kickoff does NOT change GBPUSD deployment — it was not slated for April enablement.
- **Action:** Continue observer through redacted_account kickoff. Revisit end-of-month per CEO memo.
- **Evidence:** CLAUDE.md `What is unresolved` section #6 (rolling restart for b298e2a); memory note `project_gbpusd_observer_cost.md`.

### EURUSD: **NO-GO (disabled pending FX prompt fix)**

- **Rationale:** CLAUDE.md unresolved #7. Tier A2 epsilon revalidation confirmed catastrophic collapse under honest 2-pip eps (CAND WR 80%→0%). Phase 2 β: 59.67% degenerate rate not temporally stable (Jan 30.68%→Apr 100%). Without Change 2 (θ D3-1) shipped AND re-validated, EURUSD is inoperable on any sim or live basis.
- **Action:** Stay offline through redacted_account kickoff. Re-enable after Change 2 + Change 3 ship + FX re-validation completes (estimated 2-3 weeks post-Tuesday).
- **Evidence:** Tier A2 `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_epsilon_revalidation.md`; Phase 2 β review §Finding 1; θ review §D3-1.

### Fleet summary table

| Instrument | Tuesday action | Risk | Reason |
|------------|----------------|------|--------|
| XAUUSD | CONDITIONAL GO | 0.5% | Regime uncertainty; size-down per Change 4 |
| US30 | GO | 1.0% | Clean; BL regime-shift benign, core edge preserved |
| USDJPY | GO | 1.0% | Clean; canonical 75.8% preserved; η collapse doesn't hit core edge |
| GBPJPY | GO | 1.0% | Clean; live-demo validated; η-23 edge was false alarm |
| GBPUSD | NO-GO (observer) | 0% | Pre-existing observer decision; not slated for April live |
| EURUSD | NO-GO (disabled) | 0% | FX precision bug; wait for Changes 2+3 + re-val |

### Fleet-level sizing notes

- **Correlation exposure cap remains 2% simultaneously** (CLAUDE.md Emergency Stop #6). USDJPY + GBPJPY correlation is historically high (JPY_CROSSES group); if both are in winning positions simultaneously at 1% each, that is 2% exposure at target — exactly at the cap. If both fire at the same kill zone the second-to-fire becomes subject to Gate 4 correlation guard (permissions.py T0.2 logic).
- **Effective total fleet risk on Tuesday if all 4 GO instruments trade at kickoff:** XAUUSD 0.5% + US30 1.0% + USDJPY 1.0% + GBPJPY 1.0% = 3.5% max simultaneous exposure. Under 4% redacted_account daily loss limit, but inside the T2.8 concurrent-cap (`floor(4/2)=2` filled positions simultaneously). So at most 2 trades will be open at any instant; the 3.5% is a sum-of-possible-triggered-capacity, not a sum-of-actual-concurrent-risk.
- **Rolling restart requirement** — CLAUDE.md unresolved #6 states live processes must be rolling-restarted for `b298e2a` model migration (M5 refinement + devils_advocate config-pinned to sonnet-4-6 + effort=max) AND T2.8 Gate 3 changes (new concurrent-cap + dormant-state) to take effect. This restart IS required before Tuesday kickoff under the redacted_account profile. Without it, the in-flight processes use stale model config and no T2.8 enforcement.
- **Heartbeat kill switch remains DISABLED** (CLAUDE.md unresolved #2/#9) per CEO intent — enable after a live observation window with actual fills.

### Pre-Tuesday checklist (infrastructure, no new decisions)

1. Rolling restart all live instruments under `--profile redacted_account` overlay.
2. Confirm canary battery passes at PASS tier (`python scripts/canary_test.py` — expect ≥11/12 baseline + ≥3/4 borderline match).
3. `python scripts/mt5_preflight.py` on redacted_account demo account (connection, account, symbol resolution, timeframe data, spread, order capability, open positions, TZ, API key).
4. Watchdog E2E verifier `python scripts/watchdog_e2e_verify.py`.
5. Confirm `knowledge_base/equity_peak_state.json` resets to redacted_account starting balance (not carrying FTMO peak — H29 drawdown logic must be relative to new account peak).
6. Telegram bot alert test on @gold_trader_os_bot (external Claw Empire bot — confirm redacted_account-mode routes correctly).

### Pre-Tuesday risk register

| Risk | Likelihood | Impact | Detection | Mitigation |
|------|------------|--------|-----------|------------|
| XAUUSD regime regime shifts further adverse | Medium | High | Week-1 > 2% DD | 0.5% sizing + watch criteria; cutback trigger |
| redacted_account spread elevated vs FTMO demo | Medium | Medium | `mt5_preflight.py` spread check | Run preflight Monday evening |
| FX precision bug inadvertently affects USDJPY/GBPJPY | Low | High | β degenerate-rate check on pre-Tuesday canary | Confirm canary stays 0% degenerate on JPY crosses |
| Rolling restart not completed before Tuesday London KZ open | Medium | High | Process PID check | Restart as part of pre-Tuesday morning routine |
| T2.8 concurrent-cap not taking effect after restart | Low | High | Shadow log check of filled-position counter | Restart verifies |
| Heartbeat flatten-switch accidentally enabled | Low | Catastrophic | Config inspection `config/agent_config.yaml → heartbeat.flatten_enabled` | Must remain `false` per CLAUDE.md unresolved #9 |
| MT5 broker-server TZ produces confused candle timestamps | Low | Medium (research-data poisoning) | `mt5_preflight.py` TZ + KZ context check | T1 confirms live self-consistent; research scripts already suspect |
| Canary fixture drift (AI behaviour shift since Apr 4 batch) | Low | Medium | `scripts/canary_test.py` run | If baseline tier fails ≥2 flips, investigate pre-Tuesday |
| OpenRouter / Anthropic API rate limit during initial KZ burst | Low | Medium | API call monitor | Budget.monthly_cap=$50 is soft; $50-60 balance is hard cap |
| Telegram message delivery silently failing | Low | Low | Alert test | Test pre-Tuesday |
| Equity peak state carries FTMO account peak incorrectly | Medium | High (incorrect H29 DD trigger) | Inspect `knowledge_base/equity_peak_state.json` | Manually reset to redacted_account starting balance before Tuesday |
| First live fill reveals slippage model not in sim | High | Low-Medium | Shadow-log `fill_price` vs `intended_entry` | α §1 flagged — new logging required on `execution.py` |

### Contingencies

- **If redacted_account demo spread is ≥2× FTMO spread on XAUUSD:** hold XAUUSD at NO-GO for Tuesday, proceed with US30+USDJPY+GBPJPY only. Re-test spread Wednesday.
- **If canary battery fails at PASS tier:** inspect recent commits for unintended prompt/model change. Do NOT GO on any instrument until canary recovers.
- **If any single CLAUDE.md Emergency Stop triggers in week-1:** pause all instruments, emergency council session.
- **If redacted_account drawdown limit proves to be 4% not 5% at account setup:** revert to XAUUSD 0.5% + immediately verify no other instrument sizes cross 1% effective.

### Instruments crucially NOT delayed

Phase 3 T1 discovered the TZ bug at `scripts/export_mt5_historical.py:81` + `src/mt5/mt5_real.py:58,71` (broker-server time mislabel → UTC claim). This affects *label conventions* but NOT price math — MT5 fetches correct candle prices at wall-clock UTC, and KZ gating uses real UTC. The live system is **self-consistent** even with the bug. **No Tuesday delay needed** on account of the TZ finding. Fix is Strategy B (post-kickoff cleanup).

---

## Reversal log — Phase 2 → Phase 1 corrections applied downstream

| Claim | Phase 1 original | Phase 2 correction | Downstream used |
|-------|------------------|---------------------|------------------|
| `_PRICE_FMT` citation line | β: line 34 | θ: line 14 bit-exact; β Phase 2 review confirms θ | **Line 14** in Change 2 |
| NAS100 L2 denom | β: 58 (55.2% share) | β Phase 2 review: 83 (38.6%) | 83 (used in T2 §7, γ §3) |
| EURUSD L2 denom | β: 255 | β Phase 2 review: 253 | 253 (used everywhere) |
| EURUSD degenerate stability | β: stable | β Phase 2 review: 30.68→72.78→53.33→100% Fisher p=2.78e-4 | **Not stable** — used in Change 2 urgency + Q4.2 risk assessment |
| Spearman(WR × D1-trend) p-value | δ: p=0.002 (erfc) | δ Phase 2 review: p=0.027 (correct t-dist) | **FAILS Bonferroni α=0.005** — H2-regime downgraded from "confirmed" to "exploratory" |
| Canonical 73.2→59.4 sequence | δ: refers to 367-batch | δ Phase 2 review: hardcoded at `L4_foundation_analysis.py:649`; same script computes 70.7 at lines 685-694 | **Hardcoded artefact** — Phase 3 T1 verified (price-math not distorted); δ's non-reproduction stands |
| Variant C +0.128R/trade | α: +0.128R, sign-test p=0.23 | α Phase 2 review: +0.007R under defensible assumption, paired-t p=0.9158, Wilcoxon p=0.3692 | **+0.007R** — Row 5 in Q1 table; Change 3 rationale preserved (deterministic rescue still exists as mechanism) |
| D1-bias-lag R-impact (ζ #1) | ζ: +10 to +25R/quarter fleet; EURUSD +110R | ζ Phase 2 review: 50× inflated; +1.5R fleet over 3.25 months; EURUSD +1.5R/episode; Phase 3 T4 reproduces bit-exact | **+1.5R** — T4 §5; Change 5 shadow logger recommended instead of ship |
| ζ Leak #2/#3 classification | ζ: "bug fix, Allowed Without Approval" | ζ Phase 2 review: intentional per ADR 003 + `:466-481` docstring; requires CEO approval | **Not shippable** — Q3 "explicitly not recommending" section |
| γ Fisher p for NAS100 regime shift | γ: p=2.2e-5 | γ Phase 2 review: p=2.35e-6 (10× stronger, conclusion holds) | Used in Row 4 Q1 table (strength of evidence upgraded) |
| η's 10 hour-of-day edges | η: GBPJPY-23 SHORT 80.7%, p_bonf=2.6e-47 | η Phase 2 review: 46.6% on clean data; 40.5% on 2022-2025 OOS; ALL 10 fail OOS; TZ bug in export script | **Full collapse** — Q4.4 scoped as post-fix research; NOT Tuesday gate |
| θ citations against prompt | θ: 19/19 | θ Phase 2 review: verified bit-exact | Unchanged — 19/19 stands |
| ε "6/6 regime vs 3/9 arb" | ε: overwhelming regime signature | ε Phase 2 review: rhetorical overfit; honest is 3/3 regime vs 3/6 arb; multiple equally-valid alternatives | **Section Q2 posterior table** — H1/H3/H4/H5 all survive as meaningful priors |
| δ "regime-conditional edge Bonferroni-safe" | δ TL;DR #2: Bonferroni-safe | δ Phase 2 review: correct p=0.027 fails α=0.005 | **Exploratory, not confirmed** — Q4.1 scoped as shadow research |

---

## Decay verdict

**Is XAUUSD edge decaying?** Yes — *structurally and uniquely-XAUUSD* per Phase 3 T2 discriminator (5 signals, posterior 55% H2 Regime). The canonical 73.2→59.4% sequence is a hardcoded artefact (Phase 2 δ), but the *underlying* 2026-Q1 WR 59.4% on n=32 trades IS real and IS XAUUSD-specific.

**Is the mechanism that causes decay fixable by us?** No — the decay mechanism is market regime (5× ADR, Hurst still persistent but V-shape chop, KER=0.033 end-of-quarter). We cannot "fix" gold's volatility regime.

**Is the decay recoverable?** Yes, IF gold reverts to 2025 regime (ADR ~36, KER ~0.4, trending). Historical: Q1-25 WR 65.6% at ADR 36.4 KER 0.443; Q4-25 WR 73.9% at ADR 88.7 KER 0.412. Edge is present when regime is trending.

**Is our execution or prompt contributing to decay?** Minimally. Phase 2 α: Variant C effective rescue +0.007R (non-significant). Phase 2 β: prompt-side FX bug (EURUSD) contributes to FX non-readiness but NOT to XAUUSD decay. Phase 3 T2 cross-instrument invariance rules out AI/code/prompt-side degradation as primary driver.

**What should we do about it?** Size-down XAUUSD (Change 4). Prioritize US30/USDJPY for edge contribution to portfolio. Ship Changes 2+3 to unlock FX symbols. Don't try to "fix" the XAUUSD edge — wait for regime reversion or accept reduced-sizing permanence.

**Decay SEVERITY:** Moderate. Fleet-wide expectancy still positive; XAUUSD alone at 59.4% WR on 1.5R target still has Exp ~+0.15R/trade. Not catastrophic; requires only tactical response.

---

## Appendix A — Evidence map

Every load-bearing claim in this synthesis cites its source. If a number appears in the tables above, it is listed here with file:line.

### Phase 2 reviews (corrected Phase 1 where noted)

| Review | File | Key findings used |
|--------|------|-------------------|
| α | `research/b_deep_audit_2026-04-19/phase2/alpha_review.md` | Variant C rescue shrinks +0.128 → +0.007R (§2.1); XAUUSD entry-degradation inside δ's regime null (§5); NAS100 loss-MFE vector §6 non-reproducible |
| β | `research/b_deep_audit_2026-04-19/phase2/beta_review.md` | `_PRICE_FMT` actual line 14 not 34; NAS100 L2 denom 83 not 58; EURUSD L2 denom 253 not 255; EURUSD 59.67% degenerate NOT temporally stable (Fisher p=2.78e-4) |
| γ | `research/b_deep_audit_2026-04-19/phase2/gamma_review.md` | γ Fisher p=2.35e-6 (10× stronger); NO_TRADE null bit-exact match with η (XAUUSD 36.6%, NAS100 38.0%, EURUSD 39.2%); NAS100 BL regime-shift survives Bonferroni × 96 × 3-partition; 12× CAND-rate discrepancy T7-sim vs session KB |
| δ | `research/b_deep_audit_2026-04-19/phase2/delta_review.md` | Spearman p=0.002 corrected to p=0.027 (fails Bonferroni α=0.005); canonical 73.2 sequence hardcoded at `L4_foundation_analysis.py:649`; same script computes 70.7 at lines 685-694; 8-quarter χ² p≈0.66 stands |
| ε | `research/b_deep_audit_2026-04-19/phase2/epsilon_review.md` | "6/6 vs 3/9" is overfit → 3/3 vs 3/6; BH arithmetic error at line 90; n=4 SL-reversal p=0.040 is legitimate small-sample that is also dice roll; BH@m=12 no survivors |
| ζ | `research/b_deep_audit_2026-04-19/phase2/zeta_review.md` | Leak #1 R-impact 50× inflated; Leaks #2/#3 intentional per ADR 003 + `market_state.py:466-481`; all three misclassified "Allowed Without Approval"; reviewer-added `_count_touches` bar-overlap semantic mismatch |
| η | `research/b_deep_audit_2026-04-19/phase2/eta_review.md` | GBPJPY-23 SHORT 80.7→46.6→40.5% on OOS; root cause `export_mt5_historical.py:81` broker-server time mislabel; same bug `src/mt5/mt5_real.py:58,71`; all 10 η strong edges fail OOS |
| θ | `research/b_deep_audit_2026-04-19/phase2/theta_review.md` | 19/19 bit-exact citations verified; β's line 34 wrong, θ's line 14 correct; `sl_buffer_applied: 0.0` hardcoded `:155,236`; prompt line 122 vs rendering code line 371 H4 contradiction (reviewer added) |

### Phase 3 testers

| Test | File | Key findings used |
|------|------|-------------------|
| T1 | `research/b_deep_audit_2026-04-19/phase3/T1_tz_blast_radius.md` | TZ bug at `scripts/export_mt5_historical.py:75-82` + `src/mt5/mt5_real.py:58,71`; **price-math NOT distorted**; live system self-consistent (UTC wall-clock gates); η OOS catastrophic but known; **no Tuesday delay needed** |
| T2 | `research/b_deep_audit_2026-04-19/phase3/T2_xauusd_discriminator.md` | 5-hypothesis posterior H2=55%, H1=15%, H4=12%, H3=10%, H5=8%; entire T7 corpus built in single batch 2026-04-04 → code/model/prompt CONSTANT; XAUUSD M15 %-range 13.5→23.6bp (1.75×); winner MFE compression p=0.041 XAUUSD-only; fast-loss p=0.029 XAUUSD-only; bad-entry 10.9→45.5% p=0.0002 XAUUSD-only; CAND rate 2.5× XAUUSD-only; Jan 2026 inflection 3 months BEFORE any code change |
| T3 | `research/b_deep_audit_2026-04-19/phase3/T3_production_semantics_touch_count.md` | 168-bar live window collapses divergence; 99.991% gate agreement; FN=0 across 106,147 events; 8 FP (0.009%) WR=12.5%; 72.7/31.5% cliff intact under production semantics; +17pp OB advantage survives; documentation-only fix |
| T4 | `research/b_deep_audit_2026-04-19/phase3/T4_d1_bias_lag_honest_impact.md` | EURUSD +110R full → +2R/day → +1.5R/episode (reproduces ζ reviewer); fleet +1.5R across 11 episodes over 3.25 months; USDJPY +8R is 1 episode first-event LOSS; NAS100 D1 bearish 20 days through +15.6% rally real mechanism; threshold to re-propose ≥4 episodes cross +3R each fleet ≥+12R |

### Tier A revalidations

| File | Key findings used |
|------|-------------------|
| `research/b_deep_audit_2026-04-19/tier_a/epsilon_revalidation.py` | Per-instrument epsilon: XAUUSD=0.20, NAS100=2.0, USDJPY/GBPJPY=0.02, EURUSD/GBPUSD=0.0002 |
| `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_epsilon_revalidation.md` | NAS100 ε-invariant: ΔsumR=0 across all buckets; CAND WR 66.7% (22W/11L/4U/0O n=37); sl_beyond_ob +19R; max_kz_trades +31.62R |
| `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_epsilon_revalidation.md` | EURUSD CAND WR 80%→0% under honest 2-pip eps; L2 counterfactual +203.97→+6.18R; sl_beyond_ob +55.02→−9R (9/9 WINs flip to LOSS); 59.67% CAND degenerate |

### Phase 1 original claims (sampled by TL;DR, quoted where not overturned)

| Agent | File | Claims preserved (not overturned by Phase 2) |
|-------|------|--------------------------------------------|
| α | `research/b_deep_audit_2026-04-19/phase1/alpha_entry_execution.md` | XAUUSD bad-entry rate 26→50% (n=33, p=0.13); bit-exact SL-touch signature 0/16 (null); NAS100 loss-MFE median 1.66R |
| β | `research/b_deep_audit_2026-04-19/phase1/beta_ai_integrity.md` | EURUSD 59.67% degenerate (preserved); `sl_buffer_applied: 0.0` 100% (preserved); `entry_in_ob` XAUUSD #1 L2-reject 75.2% |
| γ | `research/b_deep_audit_2026-04-19/phase1/gamma_missed_trades.md` | NO_TRADE null result; L2 overall edge-negative; `max_kz_trades` + `max_daily_trades_sim` +40.62R counterfactual; March NAS100 regime shift synchrony |
| δ | `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md` | Bootstrap P=0.7525 stationarity (preserved); quarterly metric table §1 (preserved); canonical sequence non-reproduction (confirmed by Phase 2) |
| ε | `research/b_deep_audit_2026-04-19/phase1/epsilon_liquidity_arb.md` | XAUUSD fast-loss 26.9→69.2% Fisher p=0.017 (Bonferroni-borderline); MFE compression 1.04→0.49R Mann-Whitney p=0.020 (Bonferroni-borderline); XAUUSD-only signature |
| ζ | `research/b_deep_audit_2026-04-19/phase1/zeta_market_state_prechecks.md` | Leak #4 (first-15-min KZ n=19) — on watch; visual MSO audit (§1) zero mismatches |
| η | `research/b_deep_audit_2026-04-19/phase1/eta_alternative_patterns.md` | NO_TRADE bit-exact match with γ (preserved); direction nulls 37-40% per instrument (preserved); directional 3 candidate edges fail Bonferroni (preserved, pre-OOS collapse of §3-4) |
| θ | `research/b_deep_audit_2026-04-19/phase1/theta_prompt_integrity.md` | No truncation (40-60× headroom); structural slicing (`[-5:]` / `[-10:]`) deliberate; D3-1 to D3-5 proposal suite |

---

## Appendix B — Action matrix

### Shippable autonomously (Claude Code can commit)

| # | Action | Closes CLAUDE.md item | Effort | Risk |
|---|--------|----------------------|--------|------|
| B1 | Replace `_FILL_EPSILON` hardcode at `simulate_t7_live_period.py:462` with `EPSILON_BY_SYMBOL` lookup | #8 | 2-3h | Low (research tool only) |
| B2 | Extend T5.24 shadow logger for D1-bias-lag episodes (per Change 5 spec) | None (augments `0f2dee0`) | 2-4h | None (shadow only) |
| B3 | Build vol-regime cutout shadow logger (Q4.1) | None | 1d | None |
| B4 | Post-Tuesday drawdown × CAND-rate shadow logger (Q4.5) | None | 2h | None |
| B5 | Update in-code comments at `market_state.py:_count_touches` to document bar-overlap production semantic (per T3 recommendation) | None | 30min | None |
| B6 | Create ADR 004 documenting bar-overlap vs transition touch semantics and T3 empirical bounds | None | 1-2h | None |

### Recommended for CEO approval

| # | Action | Closes CLAUDE.md item | Effort | Risk |
|---|--------|----------------------|--------|------|
| C1 | θ D3-1: per-instrument `_PRICE_FMT` in `primary_analyzer_prompt.py:14` + post-AI validator | #5, #7 | 4-8h code + ~$40 FX re-val | Medium (affects all 4 FX) |
| C2 | θ D3-2: non-zero `sl_buffer_applied` formula in prompt | #4, #5 | 4h + re-val | Medium (affects SL geometry) |
| C3 | XAUUSD risk_per_trade_pct 1.0 → 0.5% in redacted_account profile | None (new) | 15min | Low (reduces exposure) |
| C4 | NAS100 review after first live week (adjust `max_kz_trades` if +0.495R BL counterfactual confirmed) | None | 30min + observation | Low |

### Explicitly declined (per Phase 2/3 findings)

| Declined action | Why |
|-----------------|------|
| T2.9 `sl_beyond_ob` strict `<` → `<=` | XAUUSD: net −1R; NAS100: ε-invariant; EURUSD: +55→−9R under honest eps |
| ζ Leak #2 OB mitigation wick→body | Intentional per ADR 003 |
| ζ Leak #3 `_count_touches` off-by-one | Documentation-only (T3: FN=0, FP=0.009% live) |
| η operationalize hour-of-day edges | All 10 fail OOS (Phase 2 η review) |
| δ regime-conditional filter as gate | p=0.027 fails Bonferroni α=0.005 (Phase 2 δ review) |
| TZ bug label cleanup pre-Tuesday | Price math unaffected; Strategy B post-kickoff (T1 §recommendation) |

### Research pre-registrations (no code until triggered)

| # | Trigger | Action |
|---|---------|--------|
| R1 | 3 months live + ≥50 XAUUSD trades | Compute Spearman(WR × KER_D1); if ρ>0.4 p<0.01 → propose regime filter |
| R2 | 6 months live across 5 instruments | Compute Spearman(decay × algo-density-rank); if ρ>0.6 p<0.05 → reopen H1 arb posterior |
| R3 | C1 + C2 ship + re-val complete | Propose FX live enablement at 0.5% per instrument |
| R4 | D1-bias-lag logger 4+ episodes ≥+3R each, fleet ≥+12R p<0.01 Bonferroni | Propose `identify_structure` fix |
| R5 | T5.24 accumulates 20+ conflict records | Cochran-Armitage trend test for D1-bias-lag persistence |

---

## Appendix C — Statistical rigor notes

### Bonferroni family sizes in this synthesis

Per Phase 1 agent conventions:
- Within-agent: each agent declared their own test family (α m=6, β m=8, γ m=9, δ m=10, ε m=6, ζ m=4, η m=330 for hour-of-day + m=56 for pattern edges, θ m=5).
- Across-agents for THIS synthesis: I do NOT apply a cross-agent Bonferroni. The agents tested different hypotheses on different corpora; their tests are independent.
- Phase 3 testers: T1/T2/T3/T4 are pre-specified follow-ups to Phase 2 conclusions; no additional multiple-testing penalty applies.

### Where Bonferroni α is binding

- **δ Spearman(WR × regime metric) at α=0.005:** corrected p=0.027 fails. Hypothesis 2 is EXPLORATORY, not confirmed. (Phase 2 δ review).
- **ε 6-signature battery at α=0.0083:** fast-loss p=0.017 fails. MFE compression p=0.020 fails. (Phase 2 ε review BH@m=12 confirms no survivors).
- **γ NAS100 BL regime-shift at α=0.05/96 partition:** p=2×10⁻⁵ SURVIVES. But 3-partition correction (×3) gives p=8.5e-4 which FAILS α=0.0005 post-hoc partition. (Phase 2 γ review).
- **η hour-of-day at α=1.5×10⁻⁴:** GBPJPY-23 SHORT original p_bonf=2.6×10⁻⁴⁷ SURVIVES in-sample, but OOS collapses to 40.5% WR (null). (Phase 2 η review).
- **β EURUSD degenerate Fisher p=2.78e-4 at α=0.0063 (m=8):** SURVIVES. (Phase 2 β review correction).
- **T2 bad-entry rate Fisher p=0.0002:** SURVIVES Bonferroni at any reasonable m across the T2 discriminator test family. (Phase 3 T2 §7).

### Why I trust T2 posterior despite non-Bonferroni individual signals

T2's test is not "does any single signal beat α=0.05"; it is "do 5 independent per-instrument signals ALL consistently isolate XAUUSD?" The isolation pattern itself — where cross-instruments are all flat in the XAUUSD-positive direction — is the conjoint evidence. Under H1/H3/H4/H5 a subset of instruments should move together; under H2 only XAUUSD should move. The data cleanly shows XAUUSD-only.

### Assumptions I am making

1. Phase 2 reviewer corrections have been applied correctly by me (e.g., β line 14 not 34, NAS100 L2 denom 83 not 58). If a reviewer correction itself is wrong, downstream estimates shift. Spot-checked 3 corrections (line 14, denom 83, EURUSD temporal p=2.78e-4) against primary evidence in β's stats_summary.json — all verified.
2. The T7 simulation corpus for XAUUSD (1455 records Jan-Apr 2026) is representative of the 2026-only live universe. The 12× CAND-rate discrepancy (Q4.6) is the single biggest risk to this assumption.
3. Tier A per-instrument epsilon is the correct honest-fill geometry. This was validated by spot-comparisons against live MT5 tick-data distributions in the Tier A1 script; not independently re-verified this phase.
4. No major code change lands between now (Apr 19) and Tuesday (Apr 21) that would invalidate the audit. Live commits since audit dispatch (check `git log --since=2026-04-19`) should be reviewed.

---

## Appendix D — Confidence calibration

I assign subjective confidence to each major claim:

| Claim | My confidence |
|-------|---------------|
| XAUUSD experienced a genuine regime shift in 2026-Q1 | 90% |
| The 5 cross-instrument signals isolate XAUUSD uniquely | 85% |
| T2 posterior (H2=55%, etc.) is well-calibrated | 70% |
| FX precision bug blocks EURUSD/GBPUSD/USDJPY/GBPJPY Tuesday enablement | 95% |
| NAS100 BLOCKED_LIMIT +40R counterfactual reflects real leak | 65% |
| D1-bias-lag fleet-wide +1.5R over 3.25 months is noise | 80% |
| T3 bar-overlap semantic bound at 0.009% FP/FN=0 is robust | 90% |
| `sl_beyond_ob` T2.9 fix would be net-negative if shipped | 85% |
| Gold edge is recoverable if regime reverts to 2025 | 75% |
| Going live on 4 of 5 instruments Tuesday is appropriate | 85% |
| XAUUSD 0.5% sizing is the right response (vs 0% or 1.0%) | 65% |
| η's TZ bug fix + re-scan will surface no material edges | 60% |
| Change 2 (FX precision) will unlock ≥3 of 4 FX symbols post-validation | 50% |

Items at ≤70% confidence are candidates for Phase 5 deeper investigation.

---

## Final chairman statement

The Session 35 audit was commissioned on the hypothesis that XAUUSD edge is leaking due to a mixture of code bugs, prompt defects, execution slippage, and/or market arbitrage. The audit discovered:

1. **The single largest XAUUSD signal is a genuine market regime change** (H2 posterior 55%). This is neither a bug nor a prompt defect; it is a market-condition shift that started 3 months before any of our recent code changes and is uniquely localized to XAUUSD.

2. **The second-largest signal is an FX precision prompt bug** (Change 2, 59.67% EURUSD degenerate), which is fixable but blocks only FX instruments — NOT the XAUUSD trajectory.

3. **None of the ζ-identified "detector bugs" are actually bugs.** Two are design per ADR 003; one is empirically bounded to 0.009% impact (T3); the ζ R-impact estimates were inflated 50× by correlated samples + missing per-instrument epsilon.

4. **None of the η-identified alternative edges survive OOS.** The TZ mislabel convention poisoned the entire hour-of-day analysis; fixing the labels is post-Tuesday hygiene.

5. **Of 20 artefacts, 3 provided robust load-bearing evidence** (Phase 3 T1/T2/T3, Tier A2/A3, Phase 2 β/ζ/η corrections). The other 17 provided either null-result confirmations (valuable signal that nothing is broken where we thought) or exploratory leads for Phase 5.

**Tuesday kickoff recommendation:** GO on 4 of 5 live instruments (XAUUSD sized-down, US30/USDJPY/GBPJPY at 1%), with EURUSD and GBPUSD offline for previously-known reasons. No pre-Tuesday ship. Changes 1+5 (research-side) can ship autonomously this week. Changes 2+3+4 (trading-logic-side) require CEO approval; draft for post-Tuesday.

**Biggest near-term risk:** gold regime does NOT mean-revert, and XAUUSD permanently sits at 0.5% sizing with degraded contribution. Secondary risk: Tuesday live reveals slippage/execution issues not measurable in sim (α §1 flagged — `execution.py` must populate `fill_price`, `slippage_cents`, `spread_at_entry` from first live fill).

**Biggest research opportunity:** Change 2 unlocks 4 FX instruments, each with independent edge characteristics. If FX re-validation clears ≥3 of 4, fleet diversification reduces XAUUSD-regime exposure substantially.

---

## Appendix E — Scope limitations and non-coverage

This audit does NOT conclude on the following topics — they were out of scope or under-powered in the available data:

1. **Live execution slippage** — zero live fills since 2026-04-07; cannot be measured from existing data. α §1 flagged this as unknown. First redacted_account fill post-Tuesday will be the first slippage observation available. `execution.py` must populate `fill_price`, `slippage_cents`, `spread_at_entry` from the first fill (α review flagged these hook points exist at `src/models/trade_models.py:151-153`).

2. **Intraday spread expansion during kill zones** — no systematic data. Monday pre-Tuesday `mt5_preflight.py` check will provide a single-point observation. Post-Tuesday 1 week of live fills will surface spread-at-fill distribution for the first time.

3. **Correlation coefficients between live instruments** — the T2.8 concurrent-cap assumes independent signals across instruments but does not measure actual fill-level correlation. 2 weeks of redacted_account trading will begin to produce real correlation data.

4. **Session memory re-enablement question** — CLAUDE.md notes `session_memory_enabled: false` due to T2b proof of 55% CR suppression. This audit did not re-examine session memory. Not pre-Tuesday relevant.

5. **Canary cache cost regression** — Cache ships ~$12/mo flat vs $6-75/day pre-cache. Not examined; no known issue.

6. **KAP research pipeline** — runs cron every 6 hours weekdays; not examined this audit.

7. **Telegram bot behaviour** — runs in Claw Empire codebase, not this repo. Not examined.

8. **Watchdog behaviours on redacted_account profile** — existing watchdogs (ob_continuation, api_refusal, displacement, redacted_account) should port directly. Weekend + dead-zone leniency already built in. Not examined.

9. **Budget cap enforcement** — `budget.monthly_cap_usd: 50.0` + CEO-disabled Anthropic auto-reload means $50-60 balance IS the hard cap. Not examined.

10. **Knowledge-base LanceDB integrity** — not examined this audit.

11. **Prompt sensitivity to model version changes** — this audit inspected current Sonnet 4.6 behaviour. Does NOT address what happens if Anthropic deprecates Sonnet 4.6 or rolls out 4.7/5.0. Planned Phase 5 monitoring.

12. **Partial close / BE shadow logger promotion timing** — CLAUDE.md notes "promote after 30+ BE-triggered trades if cumulative Δr > 0 at p<0.05 (Wilcoxon signed-rank)". Not examined. Waiting for accumulation.

13. **Re-running backtests on corrected data** — the TZ bug in `export_mt5_historical.py:81` poisons historical labels but not prices; rerunning the 367-batch backtest on corrected labels would produce different hour-of-day patterns but similar WR. Not done this audit; put on post-Tuesday list.

14. **Cost-of-doing-nothing analysis** — if we delay Tuesday kickoff by 1 week to ship Changes 2+3, we lose 5 trading days × ~3.5 expected CANDIDATEs/day × fleet = ~17 trades of opportunity. At +0.3R expected per trade × 1% = 5.1% of account expected. This audit does NOT recommend delay, but if CEO decides delay is prudent, cost is quantifiable at ~3-5% account equivalent.

### Topics explicitly out of scope per CEO brief

- No strategic trading decisions (posture, sizing, gating changes to LIVE without approval).
- No prompt changes (recommended only, not shipped).
- No live code changes (research-side tool fixes only autonomous).
- No new frameworks activation.
- No rewriting of the backlog synthesis or ADR files.

### Topics I noticed but did not pursue

- **`config/agent_config.yaml` drift between FTMO and redacted_account profiles** — θ review mentions per-instrument configs exist. If redacted_account profile has drift from FTMO in XAUUSD parameters (e.g., different kill-zone start times, different correlation groups), that would be a separate deep-check worth 1h.
- **`ob_continuation` rolling-50 monitor current status** — LIVE_STATE.md would show; not fetched.
- **Whether any of the 2 FP records from T3's 8-FP set align with live 2026-Q1 XAUUSD "bad-entry" signals** — could be a low-cost follow-up.
- **PID lock behaviour across rolling restart** — not examined.

---

## Appendix F — Prior decision precedents referenced in this synthesis

| Decision | Reference | Relevance to Phase 4 |
|----------|-----------|----------------------|
| OB continuation is primary decay metric | ADR 001 (Task A OB continuation approach) | Row 1 XAUUSD regime signal aligns with ADR 001 scope |
| T2.8 concurrent-cap architecture | Session 33 commit `dc4cec2` | Change 4 + Tuesday checklist item 1 (rolling restart requirement) |
| T4.26 sl_beyond_ob cross-instrument audit | Session 33/34 commit `0e33651` | Row 8 (T2.9 decline); Triangulation 4 |
| T5.24 D1-bias-lag shadow logger | Session 34 commit `0f2dee0` | Change 5 (extension to existing logger) |
| H29 drawdown position reduction | Session 29 handoff; live | Pre-Tuesday check item 5 (equity peak reset) |
| Session memory disabled (T2b proof) | Live config; CLAUDE.md canonical | Not revisited — out of scope this audit |
| Sonnet 4.6 effort=max for primary gate | Session 24 memory / CLAUDE.md | Foundation for T2 posterior — single-model-unchanged premise |
| Canary cache (PASS-only, content-addressed) | Pre-session 33 | Cost basis for pre-Tuesday checklist item 2 |
| Inverted TP auto-correction gate | Permissions.py baseline | Foundation for all Tuesday live trading — assumed intact |
| Gate 0 deployment.phase enforcement | T0.2/Q014; `permissions.py` first-run gate | Pre-Tuesday implicit — phase must be 3 live_micro |
| GBPUSD observer through April 2026 | CEO memo 2026-04-18 | GBPUSD NO-GO rationale |
| WF-1 deprioritized per CEO | CEO directive 2026-04-18 | Approval still required per CLAUDE.md; CEO approval items in Appendix B |
| Anthropic auto-reload disabled | CEO 2026-04-19 | $50-60 balance IS hard cap |

---

## Appendix G — What would change this synthesis

If any of the following conditions turn out to be true, sections of this synthesis would need material revision:

1. **If Tier A epsilon table is wrong for XAUUSD or USDJPY/GBPJPY** — entire R-impact column in Q1 ranking shifts. Re-validation needed. Tier A1 validated at dispatch, so confidence currently high.

2. **If the XAUUSD 2026-Q1 WR=59.4% on n=32 was drawn from a different population than the 2025-Q4 WR=73.9% on n=23** (e.g., different trade-selection protocol, different time window defined non-identically) — the decay signal evaporates. Phase 2 δ review's non-reproducibility note is partial evidence of this risk. Q4.6 is the follow-up that addresses it.

3. **If live slippage observed first week exceeds the honest_eps estimate** — Tier A counterfactuals become overly-optimistic, and R estimates need re-baselining. Low probability but known unknown.

4. **If redacted_account maximum DD enforcement proves stricter than 5%** — XAUUSD CONDITIONAL GO at 0.5% might need to drop to NO-GO.

5. **If a week-1 XAUUSD or US30 trade fills at materially-different spread than demo assumptions** — indicates redacted_account is not demo-equivalent; re-baseline.

6. **If Sonnet 4.6 decisions on Tuesday differ materially from canary fixture behaviour** — indicates model version drift; investigation required pre-any live fill.

---

*End of Phase 4 Chairman Synthesis. 20 artefact evidence trail; 1555 records analysed; 5 hypotheses discriminated; 6 CEO-approval items staged; 6 shippable-autonomously items identified.*
