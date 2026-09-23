# EURUSD T7 Simulation — Accepted-Trade Quality Analysis (the 9 CANDIDATEs)

**Scope:** the 9 CANDIDATEs that made it through all gates (L1 prescreen, OB proximity, AI Sonnet-4.6 gate, L2 verification, limit-fill check, KZ/daily caps) from the EURUSD T7 simulation, Jan 02 2026 → Apr 17 2026.

**Data:** 2280 evaluated kill-zone candles; 9 CANDIDATE, 253 REJECTED_L2, 38 BLOCKED_LIMIT, 1980 NO_TRADE, 0 PARSE_ERROR. Of the 9: 8 WIN (1 loss) raw. Headline: **WR on all-9 resolved = 88.9% (8/9); cumulative R = +5.17; expectancy +0.574 R/trade**. **But after stripping degenerate (entry=SL=TP) records the real accepted set is n=5, WR 80% (4W/1L), +5.17R, expectancy +1.034 R/trade.**

Input: `research/t7_live_simulation/EURUSD_t7_simulation.json` (4.3 MB, 2280 records, $30.0715 spent).

---

## TL;DR (5 bullets)

1. **9 CANDIDATEs is too small to claim an edge on its own, AND the edge inverts under honest fill modeling.** At sim-default `_FILL_EPSILON = 0.05` (500 pips on EURUSD): 4W/1L on 5 real CANDs, +5.17R. At honest 1-pip epsilon: **0W/5L, -5.00R** — a 10R flip on the same 5 signals. Binomial p vs 0.5 is 0.625 at sim-eps (+5.17R non-significant) and 0.063 at honest-eps (-5R also non-significant). The result is not "small edge" — it is "edge is 100% fill-epsilon artefact". Effective independent N after deduping Jan 23 10:45+13:30 duplicate: 4 distinct trades over 3.25 months.
2. **4 of the 9 CANDIDATEs (44%) are data-corruption artefacts where the AI emitted entry=SL=TP.** The sim's `compute_outcome()` has no zero-risk guard: when `sl_dist = abs(entry - sl) == 0`, the TP comparison still fires as WIN with r=0 (because `c.high >= tp` trivially holds when tp == entry). These 4 records show "WIN r=0" in the raw output but carry zero trading information — they are lossless-by-construction. Reporting WR=88.9% without excluding them would be misleading. Real-trade set: 5 (4W/1L = 80%, +5.17R, +1.034R Exp).
3. **LONG skew is absolute: 5/5 real CANDIDATEs are LONG. Zero SHORT CANDIDATEs survived all gates.** Three SHORT CANDIDATEs show in the raw data (Jan 7, Mar 2, Mar 6) — all three are degenerate (E=SL=TP=0-risk), meaning no viable SHORT trade made it past the gate stack during 3.25 months. The EURUSD regime had 7 of 16 weeks net-positive and 9 of 16 net-negative (see D), so a pure LONG bias is not justified by underlying directional drift.
4. **4 of 5 real CANDs occurred in one 19-day window (Jan 23 → Feb 10).** That cluster produced +5.17R on 4 trades (all LONG, all WIN on the real-data replay). From Feb 11 onward to April 17, there is 1 CANDIDATE (Feb 23 LONG, which lost). The strategy ran effectively idle for 9 weeks of the sim. This matches the pattern of price pinning 1.175-1.185 from mid-Feb onward (see D section 2).
5. **Cost: $30.0715 total sim cost. Bit-exact Sonnet-4.6 math: 5,267,672 input × $3/MTok + 951,272 output × $15/MTok = $30.0721 (ratio 1.0000). Cost per real CAND = $6.01. Cost per R = $5.82.** The `raw_response.model_used` field contains 593 "gpt-4.1", 305 "structural-bias-evaluator-v1", 208 "claude-opus-4-5", 1174 empty — all JSON-output fabrications by the model; the **API actually called Sonnet-4.6** per the cost ratio.

---

## 1 — Are the outcomes systematic or random?

### 1a. Degenerate handling (read this before any other section)
The sim data must be split before any outcome analysis:

| set | n | W | L | U | totalR | ExpR |
|-----|---|---|---|---|--------|------|
| all CANDs (raw) | 9 | 8 | 1 | 0 | +5.17 | +0.574 |
| real (entry ≠ SL) | 5 | 4 | 1 | 0 | +5.17 | +1.034 |
| degenerate (entry=SL=TP) | 4 | 4 (sim artefact) | 0 | 0 | 0.00 | 0.000 |

All 4 degenerate CANDs are cases where the AI rounded to 2 decimal places on EURUSD prices (e.g. entry=1.18000, SL=1.18000, TP=1.18000). The sim treats this as an instant WIN-at-zero-risk because the replay loop's first post-fill candle trivially satisfies `c.high >= tp` when tp equals the entry. This is a **sim-engine bug compounding an AI-output bug**; both need fixing but the immediate implication for this analysis is: *WR and expectancy must be computed on the n=5 real set, not the raw n=9.*

### 1b. Headline test (real set)
- Resolved real: 4 W / 1 L on n=5.
- **Exact two-sided binomial p vs p0=0.5: 0.625.** Nowhere close to significance.
- 95% Wilson CI on WR: [37.6%, 96.4%] — encompasses breakeven and heavy edge alike.
- n=5 is below the CLAUDE.md "no-significance claims below n=20" line.

### 1c. All 9 CANDs explicitly

| t (UTC) | dir | E | SL | TP | outc | r | degen |
|---|---|---|---|---|---|---|---|
| 2026-01-07 09:30 | SHORT | 1.17000 | 1.17000 | 1.17000 | WIN | 0 | YES |
| 2026-01-23 10:45 | LONG | 1.16000 | 1.15700 | 1.16450 | WIN | +1.5 | no |
| 2026-01-23 13:30 | LONG | 1.16000 | 1.15700 | 1.16450 | WIN | +1.5 | no (dup of 10:45) |
| 2026-01-30 13:00 | LONG | 1.19000 | 1.18970 | 1.19050 | WIN | +1.67 | no |
| 2026-02-04 07:00 | LONG | 1.18000 | 1.18000 | 1.18000 | WIN | 0 | YES |
| 2026-02-10 07:15 | LONG | 1.18000 | 1.17700 | 1.18450 | WIN | +1.5 | no |
| 2026-02-23 08:15 | LONG | 1.18000 | 1.17000 | 1.19000 | LOSS | -1.0 | no |
| 2026-03-02 08:00 | SHORT | 1.18000 | 1.18000 | 1.18000 | WIN | 0 | YES |
| 2026-03-06 13:45 | SHORT | 1.16000 | 1.16000 | 1.16000 | WIN | 0 | YES |

Striking: the 4 degenerate records are all 3 SHORTs plus Feb 4 LONG. **The degenerate pattern is concentrated (but not exclusive) on SHORTs** — this is consistent with a prompt/geometry issue where the AI can't determine a bearish entry structure and emits a single price three times.

### 1d. By setup grade
All 9 CANDIDATEs were graded A+ (all C-gates passed). Same tautological pass-through as NAS100.

| grade | n | W | L | U | WR | totalR |
|-------|---|---|---|---|-----|--------|
| A+ | 9 | 8 | 1 | 0 | 88.9% | +5.17 |

(Grade is not a discriminator — the prompt promotes A+ whenever all three gates pass.)

### 1e. By kill zone (real set)

| kill_zone | n | W | L | U | WR | totalR |
|-----------|---|---|---|---|-----|--------|
| london | 4 | 3 | 1 | 0 | 75.0% | +3.67 |
| ny | 1 | 1 | 0 | 0 | 100% | +1.50 |

London carries 4 of 5 real CANDs; NY 1 of 5. No KZ signal possible at n=5.

### 1f. By direction (real set)

| direction | n | W | L | U | WR | totalR |
|-----------|---|---|---|---|-----|--------|
| LONG | 5 | 4 | 1 | 0 | 80% | +5.17 |
| SHORT | 0 | — | — | — | — | — |

**ZERO real SHORTs.** See section 4.

### 1g. By month (real set)

| month | n | W | L | totalR |
|-------|---|---|---|--------|
| 2026-01 | 2 | 2 | 0 | +3.00 |
| 2026-02 | 2 | 1 | 1 | +0.50 |
| 2026-03 | 0 | — | — | — |
| 2026-04 | 0 | — | — | — |

**0 real CANDs in March OR April.** The strategy is fully silent for 2+ months after Feb 23.

### 1h. By week (all 9 CANDs — context for D's regime analysis)

| iso_week | regime | n | dir | W |
|---|---|---|---|---|
| 2026-W02 | -0.77% | 1 | SHORT | 1 (degen) |
| 2026-W04 | +2.17% | 2 | LONG×2 | 2 |
| 2026-W05 | -0.08% | 1 | LONG | 1 |
| 2026-W06 | -0.29% | 1 | LONG | 1 (degen) |
| 2026-W07 | +0.48% | 1 | LONG | 1 |
| 2026-W09 | +0.18% | 1 | SHORT | 1 (degen) |
| 2026-W10 | -1.31% | 1 | SHORT | 1 (degen) |

Only 7 of 16 weeks fired any CAND. 2 real CANDs (Jan 23 × 2) landed in a +2.17% bullish week — good alignment. 1 real LONG CAND (Feb 10) landed in a -0.29% flat-bearish week — geometrically correct but the direction fought the weekly drift.

---

## 2 — Per-trade geometry & fill-lag

### 2a. Fill epsilon exposure (CRITICAL)
Sim uses `_FILL_EPSILON = 0.05` POINTS at line 462 of `scripts/simulate_t7_live_period.py`. On EURUSD the instrument-native unit is price (1 pip = 0.0001). 0.05 price units = 500 pips. **Every limit order with |entry - candle_close| ≤ 500 pips is treated as a market fill at entry_price** — i.e., every EURUSD limit in this sim is effectively market.

| t | entry | candle_close | Δ (pips) | sim behavior |
|---|---|---|---|---|
| 2026-01-23 10:45 | 1.16000 | 1.17401 | 140.1 | at-market at 1.16 (fill epsilon absorbs) |
| 2026-01-23 13:30 | 1.16000 | 1.17370 | 137.0 | at-market at 1.16 |
| 2026-01-30 13:00 | 1.19000 | 1.19337 | 33.7 | at-market at 1.19 |
| 2026-02-10 07:15 | 1.18000 | 1.19069 | 106.9 | at-market at 1.18 |
| 2026-02-23 08:15 | 1.18000 | 1.18313 | 31.3 | at-market at 1.18 |

Price at signal time is 30-140 pips AWAY from the stated entry, but the fill-epsilon tells the sim "just fill at entry anyway." The simulator then continues forward and those at-market fills happen to catch the reversal move, producing 4 WIN / 1 LOSS.

### 2b. Honest-epsilon replay — the real-CAND edge inverts

Using `_scratch/eurusd_replay.py` at fill_epsilon=0.0001 (1 pip, realistic FX):

| t | entry | at eps=0.05 | at eps=0.0001 |
|---|---|---|---|
| 2026-01-23 10:45 LONG | 1.16000 | WIN +1.5R | **LOSS -1.0R** |
| 2026-01-23 13:30 LONG | 1.16000 | WIN +1.5R | **LOSS -1.0R** |
| 2026-01-30 13:00 LONG | 1.19000 | WIN +1.67R | **LOSS -1.0R** |
| 2026-02-10 07:15 LONG | 1.18000 | WIN +1.5R | **LOSS -1.0R** |
| 2026-02-23 08:15 LONG | 1.18000 | LOSS -1.0R | **LOSS -1.0R** |
| **total R** | | **+5.17** | **-5.00** |

**A 10.17R flip on 5 trades, purely from fill-epsilon recalibration.** At honest 1-pip epsilon, price is 30-140 pips away from the stated limit at signal; by the time price comes back down to fill the limit, the OB has already been consumed and the trade loses immediately. The "edge" reported by the sim is 100% the fill-epsilon artefact — not a discrimination signal from the AI.

This is the most consequential single number in the whole EURUSD validation: **the 80% WR collapses to 0% WR under realistic fill modeling.**

### 2b. Geometry distribution (real CANDs)

| metric | min | median | max |
|---|---|---|---|
| SL distance (pips) | 3 | 30 | 100 |
| TP distance (pips) | 5 | 45 | 100 |
| RR | 1.5 | 1.5 | 1.67 |

All 5 real CANDs have R:R in [1.5, 1.67] — the AI is rounding heavily to the minimum acceptable RR.

### 2c. Jan 23 duplicate
The two Jan 23 CANDs fire at 10:45 and 13:30 (both London+NY, 2h45m apart) with **identical** entry/SL/TP. The 10:45 order would already be on the book when 13:30 evaluates — and would be blocked by `max_kz_trades` cap. Yet both are recorded as CAND, both WIN at +1.5R. This suggests the sim is not modeling the pending-limit-still-open state between bars. Effective dedup: 4 independent tests.

### 2d. No fill-lag problem (inverse of NAS100)
Unlike NAS100's 4h median fill lag, EURUSD has zero fill lag because the fill epsilon absorbs every limit. Fill candle == signal candle for all 5 real CANDs. This is an artifact of the simulator, not a real edge signature.

---

## 3 — Post-AI CANDIDATE rate vs other instruments

| instrument | evaluated | prescreen PASS | post-OB-prox | AI-reached | CAND | post-AI CR |
|---|---|---|---|---|---|---|
| XAUUSD (batch) | — | — | — | — | — | ~10.3% |
| NAS100 T7 | 1600 | ~1000 | ~820 | 816 | 37 | 4.5% |
| **EURUSD T7** | **2280** | **1376** | **1106** | **815** | **5 real** | **0.61% real / 1.10% raw** |

EURUSD's post-AI CAND rate is **~1/9th of NAS100's** on the real set. The gate is MUCH more selective here — and with only 5 CANDs surviving 3.25 months, the edge is not deployable in practice even if statistically valid. This is an instrument-level finding: the Model A / ob_retest prompt is mis-calibrated for EURUSD's flat-range regime.

---

## 4 — The LONG skew is real and pathological

5/5 real CANDs LONG. Three SHORT records exist but all three are degenerate (E=SL=TP=0-risk). Directional bias at the MSO level is roughly balanced:

- `bias` field across 815 AI-reached candles: 504 bullish, 602 bearish (see D for weekly breakdown).
- `h1_direction` field: mix of bullish/bearish by week.

So the SHORT skew is NOT from lack of bearish bias input — it's from a prompt/geometry issue where bearish OB-retest setups fail to produce a coherent trade plan. This surfaces as either (a) L2 rejection (98.4% of REJECTED_L2 are LONG — but that's also a LONG-biased rejection pattern! see C), or (b) degenerate output (AI emits 3-of-a-kind price because it cannot compute a sensible SHORT entry zone).

**Fisher exact test (SHORT CAND vs LONG CAND) vs (SHORT bias rate vs LONG bias rate) at 815 AI-reached:**

- LONG CANDs real: 5/5 = 100%
- SHORT CANDs real: 0/5 = 0%
- LONG bias (across AI-reached): 504 / (504+602) ≈ 45.6%
- SHORT bias: 602 / 1106 ≈ 54.4%

Null hypothesis: if the gate is direction-blind, SHORT rate should match bias rate (≈54% SHORTs). Observed: 0% SHORTs. Binomial(5, 0.544) P(≤0 SHORTs) = 0.456^5 = 0.020. **The LONG skew in accepted trades is unlikely to be chance (p≈0.02), and it replicates NAS100's finding (NAS100: 36/37 LONG, p<0.01).**

---

## 5 — Statistical caveats

1. **n=5 real CANDs is below the CLAUDE.md "no significance claims at n<20" threshold.** Every per-bucket table in this document is anecdotal. Treat the 80% WR / +1.034 R Exp as descriptive statistics, not a validated edge.
2. **Effective N is smaller still.** Jan 23 10:45 + 13:30 are identical geometry, same day — one independent event at most. Dedup → 4.
3. **Strong correction burden.** Whatever per-instrument WR threshold survives Bonferroni for the 4-instrument validation battery, EURUSD does NOT clear it on these n.
4. **Sim-engine bugs (at-market epsilon, no zero-risk guard, dup-setup not deduped) interact with AI-output bugs (2-dp rounding on 4-dp instrument, SHORT geometry collapse). Every number on this page is downstream of both.**

---

## 6 — Cost math

| metric | value |
|---|---|
| Records | 2280 |
| Input tokens | 5,267,672 |
| Output tokens | 951,272 |
| Actual cost | $30.0715 |
| Expected if Sonnet-4.6 ($3 in / $15 out per MTok) | $30.0721 |
| Ratio actual/expected-sonnet | **1.0000** |
| Expected if Opus-4.x ($15 in / $75 out) | $150.3605 |
| Ratio actual/expected-opus | 0.2000 |

**The API called Sonnet-4.6 bit-exact.** The 208 "claude-opus-4-5" strings in `raw_response.model_used` are model hallucinations (same pattern NAS100 exhibited). The 593 "gpt-4.1" and 305 "structural-bias-evaluator-v1" strings are more-egregious hallucinations in the same field — the JSON-output `model_used` key is unreliable as a provenance marker.

Cost per real CAND: $6.01. Cost per +R: $5.82. Cost per independent CAND (n=4 dedup): $7.52 / $8.19.

---

## 7 — What to take from Angle A into the chairman synthesis

- EURUSD produced **5 real accepted trades in 3.25 months** — the post-AI CAND rate is too low to deploy even if WR is honest.
- **4 of the 9 recorded CANDs are degenerate (entry=SL=TP) with sim-engine phantom-WIN outcomes.** These are a data-cleanliness red flag, not trades.
- The LONG skew replicates NAS100 (p≈0.02), suggesting a **prompt-level SHORT geometry failure** that crosses instruments.
- **The 80% WR on n=5 inverts to 0% WR at honest 1-pip fill-epsilon.** A 10.17R flip in the same 5 trades from epsilon recalibration alone. This is the strongest single finding — not an "edge is small" result but an "edge is epsilon artefact" result.
- The in-sample WR of 80% (4/5 at sim eps) is not significant (p=0.625). The honest 0% WR (0/5 at 1-pip eps) is also not significant (p=0.063). Neither direction is supportable; the result is uninformative on edge, informative on sim calibration.
- Cost math proves the sim used Sonnet-4.6, not Opus-4.5 as the raw_response strings claim.
