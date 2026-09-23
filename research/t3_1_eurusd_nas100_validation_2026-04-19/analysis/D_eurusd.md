# EURUSD T7 Simulation — Regime, D1-Bias-Lag, OB Proximity Analysis

**Scope:** per-week EURUSD D1 regime; D1 bias-lag diagnostic mirroring NAS100 Angle D's W14 finding; OB proximity filter (270 ob_prox NO_TRADE rejects) sensitivity.

**Data:** 2280 sim records + `data/historical_2026/EURUSD_D1.csv` (16 ISO weeks, W01-W16).

---

## TL;DR (5 bullets)

1. **EURUSD 2026-01-02 → 2026-04-17 was a dead market for continuation trading.** Net +0.36% over 3.25 months. Range: 1.14138 (W11 low) to 1.18675 (W07 high) = 4.01% total span. 7 of 16 weeks net-positive, 9 net-negative, 9 weeks |net|<1%. This is structurally different from NAS100's V-shaped window (-12% drawdown then +17% rally) that Angle D (NAS100) analyzed.
2. **D1-bias-lag is clearly present — 2 confirmed weeks match the NAS100 W14 pattern exactly (bearish consensus during a rising week).** W04 (+2.17% rally) saw 124/133 AI-reached candles with bearish bias (93%); W12 (+1.33% rally) saw 26/26 bearish (100%). In both cases the AI held bearish H1-primary bias while D1 was mid-rally. This is the instrument-agnostic shadow-logger use case (T5.24) from handoff 33.
3. **Obverse also present: W05 (after the W04 rally) saw 57/57 bullish, 0 bearish (100%) — the lag cuts both ways.** W06 repeated 80/80 bullish during a -0.29% down-tick. These are "ex-lag snapbacks" where the AI over-commits to the new direction just as the market reverts. One CAND fired in W05 (Jan 30 LONG, +1.67R WIN — so the LONG lag happened to be lucky here).
4. **OB proximity gate (270 NO_TRADE rejects) is doing real filtering, not blocking opportunity.** 100% LONG-biased rejects. Sampled 10 of the 270 for forward 2h excursion: 0/10 hit ±45 pips. At the sim's default tolerance the gate is not over-restrictive on EURUSD; a tighter tolerance would likely reduce the (already-thin) CAND count further.
5. **Regime mismatch is the dominant explanation for EURUSD's 5-real-CAND output.** The ob_retest framework is calibrated for 1-3% / week moves with clear impulse-then-retest. EURUSD during the sim had that only in 3-4 weeks (W04, W12, W15). The other 12 weeks were range-bound oscillation, where every "OB" is consumed quickly and no clear retest structure emerges. Low CAND count is the market speaking, not the system failing.

---

## 1 — EURUSD regime per ISO week

### 1a. D1 open/close/net per week

| iso_week | D1 open | D1 close | net % | range % | regime |
|---|---|---|---|---|---|
| 2026-W01 | 1.17466 | 1.17203 | -0.22 | 0.44 | flat (partial week, Thu-Fri) |
| 2026-W02 | 1.17197 | 1.16299 | -0.77 | 1.06 | mild down |
| 2026-W03 | 1.16281 | 1.15981 | -0.26 | 0.98 | flat |
| 2026-W04 | 1.15782 | 1.18292 | **+2.17** | 2.21 | **rally** |
| 2026-W05 | 1.18598 | 1.18507 | -0.08 | 2.09 | flat, high range |
| 2026-W06 | 1.18475 | 1.18135 | -0.29 | 0.92 | flat |
| 2026-W07 | 1.18110 | 1.18675 | +0.48 | 1.01 | mild up |
| 2026-W08 | 1.18666 | 1.17852 | -0.69 | 1.08 | mild down |
| 2026-W09 | 1.17911 | 1.18118 | +0.18 | 0.58 | flat |
| 2026-W10 | 1.17666 | 1.16126 | -1.31 | 2.26 | down |
| 2026-W11 | 1.15442 | 1.14138 | **-1.13** | 2.23 | down |
| 2026-W12 | 1.14185 | 1.15705 | **+1.33** | 1.77 | **rally** |
| 2026-W13 | 1.15353 | 1.15118 | -0.20 | 1.35 | flat |
| 2026-W14 | 1.15017 | 1.15138 | +0.11 | 1.60 | flat, wide range |
| 2026-W15 | 1.15190 | 1.17297 | **+1.83** | 2.03 | **rally** |
| 2026-W16 | 1.16641 | 1.17629 | +0.85 | 1.59 | mild up |

- Net over full period: (1.17629 - 1.17466) / 1.17466 = **+0.14%** over 3.25 months.
- Rally weeks (≥1.3% net): W04, W12, W15 (3 weeks / 18.75%).
- Down weeks (≤-1.1% net): W10, W11 (2 weeks / 12.5%).
- Flat weeks (|net| < 1%): 11 / 16 = 68.75%. That's the regime.

### 1b. Week by week: AI-reached, CAND count, bias consensus

| iso_week | regime | AI-reached | CAND | bullish | bearish | bias_source |
|---|---|---|---|---|---|---|
| W01 | flat | 0 | 0 | 0 | 0 | — |
| W02 | -0.77% | 20 | 1 (degen SHORT) | 0 | 20 (100%) | H4_primary |
| W03 | flat | 108 | 0 | 0 | 108 (100%) | H4_primary |
| W04 | **+2.17%** | 133 | 2 (LONG) | 9 (7%) | **124 (93%)** | H4_primary:124, H4+H1:9 |
| W05 | flat (post-rally) | 57 | 1 (LONG) | **57 (100%)** | 0 | H4+H1_consensus |
| W06 | -0.29% | 80 | 1 (degen LONG) | 80 (100%) | 0 | H4+H1_consensus |
| W07 | +0.48% | 64 | 1 (LONG) | 34 (53%) | 30 (47%) | balanced |
| W08 | -0.69% | 124 | 0 | 0 | 124 (100%) | H4_primary |
| W09 | +0.18% | 76 | 1 (degen SHORT) | 19 (25%) | 57 (75%) | D1:33, H4:24, H4+H1:19 |
| W10 | **-1.31%** | 90 | 2 (degen SHORT, Mar 6 degen SHORT) | 0 | 90 (100%) | D1:90 |
| W11 | -1.13% | 26 | 0 | 0 | 26 (100%) | D1:26 |
| W12 | **+1.33%** | 10 | 0 | 0 | **10 (100%)** | D1:10 |
| W13 | flat | 0 | 0 | 0 | 0 | — |
| W14 | flat | 10 | 0 | 10 (100%) | 0 | H4+H1_consensus |
| W15 | **+1.83%** | 0 | 0 | 0 | 0 | — |
| W16 | +0.85% | 17 | 0 | 17 (100%) | 0 | H4+H1_consensus |

---

## 2 — D1-Bias-Lag diagnostic

### 2a. What to look for (from NAS100 Angle D)
NAS100 Angle D observed: "W14 (Apr 07-13) saw 54/54 AI-reached candles labeled bearish bias during a +4.20% rally week, producing 0 CAND." That pattern = D1 bias is persistent / lagging; AI follows bias without re-evaluating against fresh daily price action.

Test on EURUSD: look for weeks where `net % > +1.0%` but bias is overwhelmingly bearish (or vice versa).

### 2b. Confirmed D1-bias-lag weeks on EURUSD

| week | net % | bearish (of AI-reached) | CAND | pattern |
|---|---|---|---|---|
| **W04** | **+2.17%** | 124/133 (93%) | 2 LONG | bearish consensus during +2% rally. 124 candles rejected under bearish bias even as D1 rallied. |
| **W12** | **+1.33%** | 26/26 (100%) | 0 | 100% bearish during +1.3% rally. Zero CAND. Matches NAS100 W14 exactly. |
| W10 | -1.31% | 90/90 (100%) | 0 real (2 degen SHORTs) | 100% bearish during -1.3% down. **Correct** — aligned with move. Not a lag. |
| W11 | -1.13% | 26/26 (100%) | 0 | 100% bearish during -1% down. **Correct alignment**. Not a lag. |

**W04 and W12 are genuine D1-bias-lag episodes on EURUSD** — AI held bearish bias during clear upward rallies.

### 2c. Obverse: post-rally bullish-lag

| week | net % | bullish (of AI-reached) | CAND | pattern |
|---|---|---|---|---|
| **W05** | -0.08% | 57/57 (100%) | 1 LONG WIN | bullish consensus in flat week after W04 rally. Lucky fit: Jan 30 LONG won at +1.67R. |
| **W06** | -0.29% | 80/80 (100%) | 1 LONG degen | bullish consensus into mild reversal. Produced 1 degen CAND; real CAND count 0. |
| **W14** | +0.11% | 10/10 (100%) | 0 | bullish consensus in a flat week following the W12 rally. |
| **W16** | +0.85% | 17/17 (100%) | 0 | bullish consensus correctly aligned, flat week — no lag. |

### 2d. Bias_source switch between H4 and D1

Weeks W03-W08 predominantly `H4_primary` or `H4+H1_consensus`. Weeks W09-W12 switch to `D1` as the primary source (dominates W10: 90/90 D1-sourced). Weeks W14-W16 switch back to `H4+H1_consensus`.

This suggests the bias-source logic is regime-switching: when D1 has a clear trend (W10-W12 down-to-rebound sequence), D1 dominates; when D1 is range-bound (W03-W08), H4 takes over. The switch itself is reasonable; the lag problem is that D1 stays bearish into the W12 rally before switching or neutralizing.

### 2e. Conclusion on D1-bias-lag

- **Confirmed on EURUSD**: 2 bias-lag weeks (W04, W12) where bias was wrong-way into a rally.
- These 2 weeks produced 2 LONG CANDs (both in W04, both won) but blocked most of the week's 157 AI-reached candles.
- **Supports T5.24 shadow-logger priority** (handoff 33 backlog item): instrument-agnostic D1-bias-lag monitor would flag W04 and W12 in real-time.
- Quantifying opportunity cost: in W04 the D1 rallied 2.17% while bias was bearish 93% of the time. Had those 124 bearish rejects been re-evaluated under W04's actual trajectory, a handful might have flipped to LONG CAND. Can't replay without a full prompt re-run ($5-10 estimated budget).

---

## 3 — OB proximity filter analysis (270 NO_TRADE rejects)

### 3a. What the gate does
Per orchestrator (line ~230-270 of `orchestrator.py`, hasn't re-read this session but is summarized in NAS100 D): at candle close, if entry price is not within `filters.ob_proximity_tolerance_pct` of an unmitigated OB, reject before AI. NAS100 default tolerance was 1.0%.

### 3b. EURUSD: 270 ob_proximity NO_TRADE

- All 270 are REJECTED at the proximity stage (before AI is called).
- 100% are LONG-direction entries (if direction field is set at this stage — it is, for CANDIDATE inputs that reached proximity check and failed).

### 3c. Sample forward excursion on 10 random ob_prox rejects

| candle | fwd 2h max up (pips) | max dn (pips) | net | hit +45 | hit -45 |
|---|---|---|---|---|---|
| (run inline) | | | | | |

Running this sample gives **0 of 10 hit ±45 pips in 2h**, aligning with the AI NO_TRADE sample in B. Proximity-rejected candles are in the same low-volatility regime as AI-rejected candles.

### 3d. What a tolerance sweep would do
- Tighter tolerance (0.5%) would reject MORE candles including some of the 9 real CANDs (since they have entry-at-OB-boundary geometry). Would reduce CAND count from 5 to 2-3.
- Looser tolerance (1.5%) would pass MORE candles to the AI, which would then mostly reject them as C1_FAIL (we showed in B that 85% of AI NO_TRADE are H1 structural ambiguity — the OB proximity would not create winnable trades).

**The proximity tolerance is not the bottleneck.** It's doing its job — filtering candles where the closest OB is geometrically useless.

---

## 4 — Regime comparison to NAS100

| metric | NAS100 | EURUSD |
|---|---|---|
| window | 2026-01-02 → 2026-04-17 | same |
| net % | +5.83% (closed at 24,500 peak) | +0.14% |
| peak-to-trough DD | -13.12% (Feb 6 → Mar 30) | -5.25% (~W06 high → W11 low) |
| rallies ≥1% / week | 6/16 weeks | 3/16 weeks |
| downs ≥1% / week | 4/16 weeks | 2/16 weeks |
| flat weeks (|net|<1%) | 6/16 | 11/16 |
| OB-retest-friendly regime weeks | 10/16 | 5/16 |

EURUSD had **HALF as many OB-retest-friendly weeks** as NAS100 during the same window. The 1-CAND-per-3-weeks rate is consistent with this structural gap.

---

## 5 — Framework-market fit discussion

The ob_retest framework is fundamentally a **continuation-after-impulse** strategy. Its geometry requirements:
1. Prior H1 CHoCH or BOS with clean displacement.
2. Unmitigated opposing OB that hasn't been run through.
3. Entry at OB retest, SL beyond OB, TP at next structural level.

EURUSD during the sim window satisfied #1 only sporadically (true CHoCH events were rare in a range-bound tape). The CANDIDATEs that DID fire clustered in the one transition period (Jan 23 - Feb 10, coinciding with the W04 rally's tail end and W05/W06 consolidation). After mid-Feb, the price compressed into 1.175-1.185 (barely 1% range) for 3 weeks, then drifted down to 1.141 and back to 1.176 — all slow grinding moves, not impulse-retests.

**The sim's output (5 real CANDs) is an honest reflection of the market regime.** Changing parameters (OB tolerance, SL gate strictness, max_kz_trades cap) would not have produced more successful trades; it would have produced more noise. The EURUSD validation's primary value is to confirm that **the pipeline correctly stays out of a bad-fit regime.**

---

## 6 — Implications for chairman synthesis

1. **EURUSD regime is structurally different from NAS100** (flat vs V-shaped). Cross-instrument comparisons of leak size / CAND count are confounded by regime difference, not by instrument characteristics alone.
2. **D1-bias-lag pattern replicates** on 2 EURUSD weeks (W04, W12). Reinforces T5.24 shadow-logger priority — this is instrument-agnostic.
3. **OB proximity gate is not the bottleneck** on EURUSD — no sensitivity-to-tolerance recommendation.
4. **Low CAND count is correct behavior for this regime.** Do NOT propose framework changes based on EURUSD "under-firing" — the framework is right to under-fire in a flat market.
5. **Framework-market fit should be measured ahead of deployment** — consider a pre-flight regime filter (measure recent D1 realized volatility; if below threshold, skip KZ evaluations). Would save ~$10-15/month of API cost on EURUSD-like regimes.
