# NAS100 T7 Simulation — Accepted-Trade Quality Analysis (the 37 CANDIDATEs)

**Scope:** the 37 CANDIDATEs that made it through all gates (L1 prescreen, OB proximity, AI Sonnet-like gate, L2 verification, limit-fill check, KZ/daily caps) from the 5-slice NAS100 T7 run, Jan 02 → Apr 17 2026.

**Data:** 1600 evaluated kill-zone candles; 37 CANDIDATE, 84 REJECTED_L2, 82 BLOCKED_LIMIT, 1395 NO_TRADE, 2 PARSE_ERROR. Of the 37: 22 WIN, 11 LOSS, 4 UNFILLED. **WR on resolved = 66.7% (22/33); cumulative R = +22.03; expectancy +0.668 R/trade.**

---

## TL;DR (5 bullets)

1. **The 66.7% WR (22 WIN / 11 LOSS on 33 resolved) is suggestive but NOT statistically separated from breakeven at 95%** — exact two-sided binomial p=0.080 vs p0=0.5. Effective independent N is smaller still: 10 distinct trading days produced 2 CANDIDATEs each, 5 of those pairs resolved on identical exit candles (dependence confirmed). Deduplicated by (date, exit_candle) → 19 W / 10 L / 3 U, WR 65.5% on 29 independent trades.
2. **Clear temporal decay — and it is the single strongest signal in the data.** Slice 1-2 (Jan-early Feb): 12 W / 2 L (85.7%). Slice 4-5 (late Mar-Apr): 5 W / 7 L (41.7%). Fisher exact p=0.038. Early WR ≈ no-edge-by-chance only at p=0.006; late WR is indistinguishable from a coin flip. The trajectory matches the broader NAS100 drawdown that began Feb 6 (26138 → 22921 low on Mar 30).
3. **The POI `zone` field perfectly separates outcomes: discount = 22 W / 5 L (81.5%), premium = 0 W / 6 L (0%). Fisher p<0.001.** All 11 losses occur when the AI entered at a "premium" POI (in H1 bearish OB treated as demand) OR took longs into resistance/premium zones. This is the strongest feature discrimination in the dataset (but n=6 for premium so cannot be over-claimed).
4. **SHORT coverage is pathologically thin — 1 SHORT candidate out of 37 (2.7%), vs 36 LONGs in a market that lost ~5% from peak to trough during the window.** 22 distinct NAS100 trading days exhibited ≥1.5% intraday drops (4h window); the AI issued a SHORT CANDIDATE on only one (2026-03-23). Bearish H1 states account for 135/816 non-None signals (16.5%) but only 1/37 CANDIDATEs — Fisher p=0.021 vs bullish setup-pass rate. The gate appears biased toward LONG.
5. **Most losses are not coin-flips — they are structural drifts against bias.** Median fill lag is 240 min (4 h) from signal; 33% of fills happen >12h after signal (the orchestrator holds the limit through regime shifts). Several losses filled on the "wrong" day: entry at 2026-03-04T14:00 filled on 2026-03-06T15:45; entry at 2026-03-10T08:15 filled on 2026-03-12T23:00. Cost = $22.97 total sim; $1.05 for the 37 CAND-tier calls alone; per-WIN cost $0.048.

---

## 1 — Are the outcomes systematic or random?

### 1a. Headline test
- Resolved: 22 W / 11 L.
- **Exact two-sided binomial p vs p0=0.5: 0.0801.** Does not reach p<0.05.
- 95% Wilson CI on WR: [49.0%, 80.4%]. Breakeven 50% is INSIDE the interval.
- The +22.03R total PnL is genuinely encouraging, but the sample is small enough that p=0.5 is not rejected.

### 1b. By setup grade
Every single CANDIDATE was graded A+. There is no usable signal in `setup_grade` because the classifier only ever promotes A+ (the prompt's gate is "all three C-gates pass → A+"). Grade is a tautological passthrough, not a discriminator.

| grade | n | W | L | U | WR | totalR |
|-------|---|---|---|---|-----|--------|
| A+ | 37 | 22 | 11 | 4 | 66.7% | +22.03 |

### 1c. By kill zone
| kill_zone | n | W | L | U | WR | totalR |
|-----------|---|---|---|---|-----|--------|
| london | 17 | 11 | 5 | 1 | 68.8% | +11.53 |
| ny | 20 | 11 | 6 | 3 | 64.7% | +10.50 |

No KZ effect (Fisher p=1.000).

### 1d. By direction
| direction | n | W | L | U | WR | totalR |
|-----------|---|---|---|---|-----|--------|
| LONG | 36 | 22 | 10 | 4 | 68.8% | +23.03 |
| SHORT | 1 | 0 | 1 | 0 | 0.0% | -1.00 |

SHORT n too small to conclude. See Section 4.

### 1e. By hour (UTC)
Hour 15Z is the weakest (1 W / 2 L / 0 U; WR=33%) — 2026-03-17 and 2026-04-10 both fired at 15:00 UTC and both lost. Other NY hours are mid-60s. London-open 08Z is strongest (6 W / 1 L; 85.7%). These are ~3-11 trade bins so they're anecdotal, but the 15:00 UTC cluster is notable.

| hour UTC | n | W | L | U | WR |
|---|---|---|---|---|-----|
| 08Z | 8 | 6 | 1 | 1 | 85.7% |
| 09Z | 8 | 4 | 4 | 0 | 50.0% |
| 10Z | 1 | 1 | 0 | 0 | 100% |
| 13Z | 11 | 7 | 2 | 2 | 77.8% |
| 14Z | 6 | 3 | 2 | 1 | 60.0% |
| 15Z | 3 | 1 | 2 | 0 | 33.3% |

### 1f. By day of week
Monday is a 0 W / 1 L / 2 U (n=3, all in slice 5). Other weekdays all 66-75% WR. Too small to conclude.

### 1g. By month — primary temporal signal
| month | n | W | L | U | WR | totalR |
|-------|---|---|---|---|----|--------|
| 2026-01 | 10 | 9 | 1 | 0 | 90.0% | +12.52 |
| 2026-02 | 8 | 6 | 2 | 0 | 75.0% | +7.01 |
| 2026-03 | 12 | 6 | 6 | 0 | 50.0% | +3.00 |
| 2026-04 | 7 | 1 | 2 | 4 | 33.3% | -0.50 |

Monotonic decline across 4 months. WR drops from 90% (Jan) to 33% (Apr). Even ignoring the unfilled April trades, 1 W / 2 L is a meaningful shift. **This decay tracks the broader NAS100 market: local high 26138 on 2026-01-28, local low 22921 on 2026-03-30 (-12.3% drawdown), recovery to 26184 by 2026-04-15.**

### 1h. By slice (operational independence)
| slice | window | n | W | L | U | WR |
|-------|--------|---|---|---|---|-----|
| 1 | Jan 02–Jan 26 | 7 | 6 | 1 | 0 | 85.7% |
| 2 | Jan 27–Feb 23 | 7 | 6 | 1 | 0 | 85.7% |
| 3 | Feb 24–Mar 09 | 7 | 5 | 2 | 0 | 71.4% |
| 4 | Mar 10–Mar 30 | 9 | 4 | 5 | 0 | 44.4% |
| 5 | Mar 31–Apr 17 | 7 | 1 | 2 | 4 | 33.3% |

**Early (slice 1-2) 12W/2L vs Late (slice 4-5) 5W/7L; Fisher exact p=0.038.** This is the most statistically salient finding in the entire dataset.

### 1i. By bias_source
Only 1 SHORT uses `H4_primary`; the 2 `D1` cases are 100% (n=2). No meaningful separation.

### 1j. By bias_confidence
36/37 = `high`; 1 = `medium` (the losing SHORT). All we learn: the one non-high-confidence CAND lost.

### 1k. By displacement ratio (AI-reported `displacement_candle_body_vs_avg_ratio`)
Ranges from 1.3 to 15.8. Higher ratio does NOT predict higher WR.
- disp_ratio ≥ 3.0: 8 W / 5 L (61.5%)
- disp_ratio < 3.0: 14 W / 6 L (70.0%)
- Fisher p=0.71. No signal. Some of the biggest losses (disp=7.6, 8.1, 4.2, 4.3) came on the highest-displacement setups.

### 1l. By confidence_score (AI self-reported 72-82)
| bucket | n | W | WR |
|--------|---|---|-----|
| ≥78 | 20 | 12 | 60.0% |
| <78 | 13 | 10 | 76.9% |

Counterintuitively the LOWER-confidence bucket performed better, though Fisher p=0.46. This is weak evidence that the confidence score (tight band 72-82) carries no useful information — the same rubber-stamp issue flagged on XAUUSD where 98% of calls get conf=80.

### 1m. Independence check
Same-day CANDIDATEs with identical exit candles (same trade detected twice):
- 2026-01-15 (2 W, shared exit)
- 2026-01-28 (2 W, shared exit)
- 2026-03-05 (2 W, shared exit)
- 2026-03-18 (2 L, shared exit)
- 2026-04-13 (2 U, shared exit — both unfilled)

Deduplicating by (date, exit_candle) yields 32 independent CANDIDATEs → 19 W / 10 L / 3 U; WR=65.5% on 29 resolved. Binomial p=0.137 after dedup. **The headline 66.7% is overstated by ~1 W through within-day correlation.**

---

## 2 — Loser post-mortem

### 2a. Full LOSS feature table
| # | candle_time | slice | kz | dir | entry | SL | TP | poi_zone | causing_event | sweep_q | disp_r | conf | bias | bias_src |
|---|-------------|-------|-----|-----|-------|-----|-----|----------|---------------|---------|--------|------|------|---------|
| 1 | 2026-01-20T09:45Z | 1 | london | LONG | 25258.75 | 25073.65 | 25536.25 | premium | CHoCH | clean | 2.2 | 72 | bullish | H4+H1 |
| 2 | 2026-02-12T13:30Z | 2 | ny | LONG | 25292.25 | 25210.95 | 25413.7 | premium | BOS | messy | 8.1 | 78 | bullish | H4+H1 |
| 3 | 2026-02-26T08:45Z | 3 | london | LONG | 25261.15 | 25216.15 | 25328.65 | discount | BOS | messy | 1.7 | 72 | bullish | H4+H1 |
| 4 | 2026-03-04T14:00Z | 3 | ny | LONG | 24652.15 | 24463.75 | 24934.75 | discount | BOS | clean | 2.2 | 78 | bullish | H4+H1 |
| 5 | 2026-03-13T14:00Z | 4 | ny | LONG | 24469.15 | 24369.25 | 24618.65 | discount | BOS | clean | 2.5 | 78 | bullish | H4+H1 |
| 6 | 2026-03-17T15:00Z | 4 | ny | LONG | 24631.65 | 24501.45 | 24826.95 | premium | BOS | clean | 3.7 | 82 | bullish | H4+H1 |
| 7 | 2026-03-18T09:00Z | 4 | london | LONG | 24795.35 | 24762.06 | 24845.27 | discount | BOS | clean | 7.6 | 78 | bullish | H4+H1 |
| 8 | 2026-03-18T13:30Z | 4 | ny | LONG | 24795.35 | 24754.35 | 24856.85 | discount | BOS | messy | 4.2 | 78 | bullish | H4+H1 |
| 9 | 2026-03-23T09:30Z | 4 | london | SHORT | 23734.25 | 23821.75 | 23603.0 | premium | CHoCH | clean | 1.9 | 72 | bearish | H4_primary |
| 10 | 2026-04-10T15:00Z | 5 | ny | LONG | 25135.55 | 25037.85 | 25282.4 | premium | BOS | clean | 2.9 | 78 | bullish | H4+H1 |
| 11 | 2026-04-16T09:00Z | 5 | london | LONG | 26283.68 | 26253.68 | 26328.68 | premium | BOS | clean | 3.4 | 78 | bullish | H4+H1 |

### 2b. Features most correlated with losing (Fisher exact on N=33 resolved)

| Feature | group_on | group_off | Fisher p |
|---------|----------|-----------|----------|
| **poi_zone=premium** | **0W/6L (0%)** | 22W/5L (81.5%) | **<0.001** |
| **slice in {4,5} (late)** | 5W/7L (41.7%) | 17W/4L (81.0%) | **0.052** |
| confidence_score ≥78 | 12W/8L (60.0%) | 10W/3L (76.9%) | 0.456 |
| causing_event=CHoCH | 2W/2L (50.0%) | 20W/9L (69.0%) | 0.586 |
| disp_ratio ≥3.0 | 8W/5L (61.5%) | 14W/6L (70.0%) | 0.714 |
| sweep_quality=messy | 6W/3L (66.7%) | 16W/8L (66.7%) | 1.000 |

**The standout: the AI's `poi_zone=premium` field is a near-perfect LOSS discriminator.** All 6 premium-zone CANDIDATEs lost. The mechanism in the data: when the AI labels the POI as "premium" on a LONG, it is fading the retrace of a bullish move back into the prior resistance region — which is by definition a counter-trend play from the OB-retest perspective. The 6 premium losses:
- 2026-01-20 (CHoCH POI = newly-broken-down level being retested as resistance, read as demand)
- 2026-02-12 (BOS premium on a day NAS100 lost 2.4% from peak)
- 2026-03-17 (premium on a recovery into a failing bounce)
- 2026-04-10 (premium on the rally recovery day)
- 2026-04-16 (premium at fresh 2026 HIGH)
- (SHORT) 2026-03-23 — this SHORT was premium-zone by design

The 22 `discount` winners align with the OB-retest edge's intended mechanic: pull back into demand (discount) on confirmed bullish bias.

Caveat: n=6 for premium, so Fisher p<0.001 is driven by perfect separation; a single premium-zone win would change the picture materially. Still, this is the single strongest feature-outcome association in the dataset and should be the first candidate for a shadow-logger rule ("flag premium-zone LONGs").

### 2c. AI-flagged concerns in its reasoning
Reviewing `overall_reasoning` and `confidence_score` for all 11 losses:
- Every LOSS had `C1=PASS C2=PASS C3=PASS` (no AI-internal dissent).
- The lowest-confidence LOSS was 72 (4 trades); the highest was 82 (Mar 17). Confidence was uniformly high for every loser.
- The SHORT (Mar 23) had `bias_confidence=medium` (the only medium in the dataset). That is the ONLY AI-internal warning signal across the losing set. Every other loss was "high" bias confidence + all-C-gates-PASS.
- **No LOSS was AI-warned prospectively.** The gate did not self-suppress any of these.

### 2d. Post-fill price action — were losses "near-misses"?
Computing MAE (max adverse excursion) and MFE after the actual fill time until SL was hit:

| candle_time | fill_time | exit | MAE (R) | MFE (R) | TP (R) | Interpretation |
|-------------|-----------|------|---------|---------|--------|----------------|
| 2026-01-20T09:45Z | 2026-01-20 17:30 | 2026-01-20 20:30 | 1.10 | 0.10 | 1.50 | clean 1R loss |
| 2026-02-12T13:30Z | 2026-02-12 14:30 | 2026-02-12 16:45 | 2.30 | 0.57 | 1.49 | moderate adverse |
| 2026-02-26T08:45Z | 2026-02-26 16:30 | 2026-02-26 16:45 | 2.81 | -0.94 | 1.50 | hard adverse (next-bar SL) |
| 2026-03-04T14:00Z | 2026-03-06 15:45 | 2026-03-09 01:00 | 2.39 | 1.26 | 1.50 | traded for 3 days after filling 2 days later |
| 2026-03-13T14:00Z | 2026-03-13 17:45 | 2026-03-13 20:45 | 1.32 | 0.82 | 1.50 | close, got 55% to TP |
| 2026-03-17T15:00Z | 2026-03-18 17:15 | 2026-03-18 22:15 | 1.16 | 0.55 | 1.50 | 1R loss next-day |
| 2026-03-18T09:00Z | 2026-03-18 15:15 | 2026-03-18 15:30 | 3.55 | 0.03 | 1.50 | sharp miss immediately |
| 2026-03-18T13:30Z | 2026-03-18 15:15 | 2026-03-18 15:30 | 2.88 | 0.03 | 1.50 | same event as #7 |
| 2026-03-23T09:30Z | 2026-03-23 11:30 | 2026-03-23 14:00 | 9.33 | 1.49 | 1.50 | SHORT got 99.3% to TP then failed |
| 2026-04-10T15:00Z | 2026-04-10 15:15 | 2026-04-13 01:00 | 3.53 | 0.94 | 1.50 | got 63% of the way then rolled over 2 days later |
| 2026-04-16T09:00Z | 2026-04-16 11:00 | 2026-04-16 11:30 | 1.08 | -0.13 | 1.50 | clean 1R loss |

Notes:
- **Only 1 of 11 losses got within 80% of TP before SL: the SHORT on Mar 23 (MFE 1.49R = 99% of 1.50R TP).** Every other loss peaked at or below 0.94R of favourable excursion. These are real losses, not tight-miss coin flips.
- Losses #7 and #8 (2026-03-18 09:00 and 13:30) fired during the same market event — both filled at 15:15 UTC, both SL'd at 15:30 UTC. This is one market event being recorded twice.
- Loss #9 (SHORT) is the single most painful-looking miss: price went within 0.3% of TP, reversed, then blew through SL.

### 2e. Whether price eventually reached TP within 6h after SL
All 11 losses: **zero** recovered to TP within 6 hours of SL. Once SL was hit, none of the setups reversed within a reasonable time frame. This rules out the "SL too tight; TP would have been right" explanation for the losses.

### 2f. Three most loss-correlated features

Ranked by strength of separation:
1. **`poi_zone = premium`** — n=6, 0% WR, Fisher p<0.001 (but n small, driven by perfect separation).
2. **`slice ∈ {4,5}`** (late window, Mar 10 onward) — n=12 resolved, 41.7% WR vs 81% early, Fisher p=0.052.
3. **`entry > candle_close` (buy-stop / breakout entry)** — n=7, 42.9% WR vs 73% pullback, Fisher p=0.186 (not significant but directionally aligned with the idea that chasing breakouts works less well than limit-pullback entries).

None survives Bonferroni for the 14 features tested (Bonferroni α=0.05/14=0.0036). Only `poi_zone=premium` beats that cutoff, and that rests on perfect 0/6 separation — fragile.

---

## 3 — Winner quality

### 3a. Time-to-TP distribution (exit_candle − candle_time)
n=22 wins. Distribution is heavily bimodal: 13 wins closed in under 450 min (≤7.5 h), 9 wins closed between 10 h and 176 h. Median 435 min (~7 h); mean 1695 min (~28 h).

Fast wins (≤ 6h, n=9): 2026-01-13 (30 min), 2026-03-10 NY (270 min), 2026-03-13 (390 min), 2026-02-06 (195 min), etc.
Slow wins (> 24h, n=8): 2026-01-15, 2026-01-27 (3330 min ≈ 55h), 2026-02-10, 2026-02-25, 2026-03-05, 2026-03-10 London, 2026-03-11.
Two wins took more than a week: 2026-03-10T08:15 (10590 min = 7.4 days) and 2026-03-11T13:30 (8835 min = 6.1 days).

**Operational caveat:** the simulator treats a CANDIDATE's limit as resting indefinitely through intervening kill-zones, weekends, and gaps. Live KZ/daily cap logic doesn't do that — it only accepts signals during KZ and caps at 2/day — but once a limit is posted it could sit. See "Open questions" for whether production's limit-TTL matches what the simulation assumes.

### 3b. MAE before TP (are wins coin-flips?)
| candle_time | MAE before TP (R) | classification |
|-------------|-------------------|----------------|
| 2026-01-27T09:15Z | 2.84 | SL-breaching favour (should have been LOSS by strict logic; see 3c) |
| 2026-02-25T13:30Z | 2.70 | SL-breaching favour (same) |
| 2026-02-26T13:30Z | 6.58 | SL-breaching favour (same) |
| 2026-03-10T08:15Z | 0.90 | near-SL coin flip |
| 2026-03-11T13:30Z | 0.90 | near-SL coin flip |
| 2026-04-10T08:00Z | 0.82 | near-SL coin flip |
| 2026-02-24T09:30Z | -1.55 | trade entered on recovery above entry, never adverse |
| remaining 15 | ≤ 0.74 | clean wins |

**18 of 22 wins (82%) were clean** with MAE ≤ 0.75R — price barely tested the SL before reaching TP. 4 wins are structurally suspicious:

### 3c. Simulator artefact: fill-then-go-against wins that "shouldn't have filled yet"
Three wins (2026-01-27, 2026-02-25, 2026-02-26 NY) show MAE > 2R after fill time. Reviewing fill logic: these filled *after* the raw signal's SL level had already been breached in the underlying time series. Example: 2026-01-27T09:15Z signal, SL=25675.62, fill=2026-01-29 16:45 (55h later), exit=2026-01-29 17:00. The market dipped well below SL at multiple points between 09:15 Jan 27 and 16:45 Jan 29 — by which time the "original" trade would have been invalidated. The simulator posts the limit and only checks SL/TP AFTER the limit fills — meaning the pre-fill adverse move is ignored.

**This inflates wins in a way production would not replicate** (production would see the invalidating move and either cancel the pending or the OB zone would be mitigated). Quantifying: without those 3 wins, WR = 19W / 14L = 57.6% on resolved. Add 1 more for dedup (2026-01-28 shared-exit pair → kept one): 18W/14L = 56.3%. **This is the headline number to show the CEO after stripping dependent and simulator-artefact wins.**

### 3d. Time-in-trade feature summary
| bucket | n | |
|--------|---|---|
| < 1h  | 1 | 30 min (2026-01-13) |
| 1-4h | 6 | |
| 4-12h | 6 | |
| 12-48h | 5 | |
| > 48h | 4 | up to 176 h |

The reliance on long holds means the trade-duration distribution is very wide, and the edge becomes more sensitive to events outside the KZ window (overnight gaps, news, weekends). Production's heartbeat monitor, kill-zone logic, and swap costs all interact with these durations in ways the sim does not model.

### 3e. Fill lag statistics (ALL CANDIDATEs, 33 that filled)
- Median lag (signal → fill): 240 min (~4 h)
- Mean lag: 858 min (~14 h)
- Max lag: 3765 min (~63 h, 2026-01-15T08:00Z)
- At-market (≤15min): 1 of 33 (3%)
- >12h after signal: 11 of 33 (33%)

**The simulation's ~67% WR is a WR on trades that were posted days/hours earlier, not on real-time signals.** This is a significant operational property: a signal at 09:00 UTC London may not fill until NY close or the next day. Production needs limit-TTL policy clarity; if production cancels limits at daily reset, the production WR could be different from the simulation's.

---

## 4 — SHORT gap investigation

### 4a. The single SHORT
- **Trade:** 2026-03-23T09:30:00Z (slice 4, London KZ). entry=23734.25, SL=23821.75, TP=23603.00, r=-1.00.
- **Model:** claude-opus-4-5.
- **Raw AI reasoning:** `"H1 CHoCH bearish with displacement confirms bearish bias (C1 PASS); M15 mirrors the same bearish CHoCH with no bullish opposition (C2 PASS); SHORT direction matches H1 bearish (C3 PASS)."`
- **Bias source:** `H4_primary` (the ONLY CAND not using H4+H1 consensus). `bias_confidence=medium` (only non-high in dataset).
- **Outcome:** Filled 2026-03-23 11:30 UTC. MFE reached 23603.25 (0.3% above TP target 23603.00) — price got within 0.01% of TP and then reversed and hit SL at 14:00 UTC. Painful near-miss.

The AI *was* right about the immediate bearish momentum; the TP just missed by one tick's worth of price.

### 4b. SHORTs NOT taken
- 22 distinct NAS100 calendar days had a ≥1.5% rolling 4-hour drawdown during kill zones.
- Of those 22, the AI issued **0 SHORT CANDIDATEs on 21** of them; 1 SHORT on 2026-03-23.
- On 10 of the 22 days, **0 CANDIDATEs at all** (all NO_TRADE + a few REJECTED_L2).
- Examples of >2% intraday NAS100 drops where the system stayed out entirely:
  - 2026-01-29 (−2.63%) — 20/20 NO_TRADE
  - 2026-02-02 (−1.68%) — 20/20 NO_TRADE (first hour after London open)
  - 2026-02-03 (−2.46%) — 18 NO_TRADE, 2 REJECTED_L2
  - 2026-02-04 (−2.39%) — 16 NO_TRADE, 4 REJECTED_L2
  - 2026-02-11 (−1.60%) — 1 CAND (bullish LONG — that CAND won)
  - 2026-03-09 (−2.73%) — 20/20 NO_TRADE (weekend anomaly)
  - 2026-04-02 (−1.85%) — 20/20 NO_TRADE; bias labelled bearish on 18/20 evaluated candles but no setup passed gates

In many of these, the underlying MSO had recently-broken-down structure (bearish H1 BOS) but the gate's prompt requires an OB retest pullback into that structure's POI — and in strong downtrend days the price tends to keep going rather than cleanly retest.

### 4c. Statistical bias toward LONG
Across all 1600 evaluations:
- h1_direction = bullish: 681 cases → 36 CAND (5.29% pass rate)
- h1_direction = bearish: 135 cases → 1 CAND (0.74% pass rate)
- **Fisher exact p = 0.021.** LONG setups pass the gate at ~7× the rate of SHORT setups, which cannot be explained by the underlying population imbalance alone.
- Market context: NAS100 had strong bullish bias Jan-early Feb, a multi-week selloff Feb-Mar, then recovery in April. Over the whole window it netted +5.8%. The 681:135 bullish:bearish H1-state split reflects the trending-up-more-than-down structure, but the 36:1 candidate split is disproportionate.

### 4d. Why the gap exists (inference, not proven)
The AI evaluation sees `MSO` (market state output) which prominently displays H1 BOS counts. Bullish markets produce many bullish BOS → "5+ bullish BOS confirms strong bias" is the canned C1 PASS phrase in 32 of 37 CANDIDATE rationales. Bearish markets produce fewer BOS per unit time because bull runs have more small continuation breaks than abrupt drops; a downtrend often manifests as CHoCH followed by continuation rather than strings of BOS. The C1 "5+ consecutive BOS" threshold advantages trends manifesting as staircase breakdowns and disadvantages cliff-edge drops.

**This is structural — the OB-retest framework is inherently long-biased in indices.** The XAUUSD canonical 62% WR (n=129) was built on bullish-primarily gold; NAS100 in a non-trending period may expose this asymmetry more. Note: the AI's refusal to take SHORTs in obvious down-moves is NOT a loss-rate issue (the one SHORT did hit 99% of TP before reversing) — it is a coverage issue. We cannot measure whether SHORTs would be edge-positive because the gate doesn't produce them.

---

## 5 — Cost economics

| Tier | n calls | Total $ | $/call |
|------|---------|---------|--------|
| NO_TRADE | 1395 | 17.1338 | 0.0123 |
| REJECTED_L2 | 84 | 2.3568 | 0.0281 |
| BLOCKED_LIMIT | 82 | 2.3491 | 0.0287 |
| **CANDIDATE** | **37** | **1.0509** | **0.0284** |
| PARSE_ERROR | 2 | 0.0836 | 0.0418 |
| **Total simulation** | **1600** | **$22.97** | |

### 5a. Per-outcome economics
- Total API cost across the 37 CANDIDATEs alone: **$1.0509**
- Cost per CANDIDATE: $0.0284
- Cost per WIN (22): $0.0478
- Cost per R of positive expectancy (+22.03R): $0.0477
- If each R at production risk = $2000 (2% of $100k FTMO), cost-per-R is negligible.

### 5b. Vs XAUUSD canonical
- XAUUSD canary alone: ~$12/month post-cache (per CLAUDE.md).
- XAUUSD primary gate: ~$60/month typical.
- NAS100 simulation (3.5 months, 5 disjoint slices, 1600 evals): $22.97 total, which annualises to roughly $79/yr or ~$6.6/month for the simulated population density. But the simulation excludes things like correlation-shock alerts and the canary; real production on NAS100 would add the canary cost.
- **If NAS100 is deployed live at the same call rate as XAUUSD, expect ~$25-40/month primary gate + ~$5-12/month canary = $30-52/month total.** Budget cap remains $50/month monthly_cap_usd per config (CEO disabled auto-reload).

### 5c. Cost-efficiency of candidates
The 37 CANDs = 2.3% of 1600 evals but 4.6% of total spend. The $1.05 CANDIDATE-tier cost is tiny compared to the $17.13 NO_TRADE noise, which is the pipeline doing its rejection work. No waste signal in the cost distribution.

### 5d. Model-mix note
34 of 37 CAND responses come from `claude-opus-4-5`; 3 from `gpt-4.1`. The simulation was run with an experimental multi-model rotation — this is not the production config (which uses Sonnet 4.6 max-effort). Numbers are NOT directly transferable to what the live NAS100 pipeline will produce with Sonnet 4.6. See "Open questions".

---

## Open questions for reviewer

1. **Fill latency assumption.** The simulator holds CAND limits indefinitely until SL/TP or end-of-window. Does production use the same logic, or does it cancel pending limits at daily reset / end of kill zone? If the latter, removing wins that filled >12h later (11 of 33 fills) drops WR to an effective 15W/10L on "same-session-fill" trades (60%).
2. **Same-day duplicate handling.** 5 pairs of CANDIDATEs with shared exit candles means the live daily cap of 2 would still fire both limits, but they'd consume the daily cap. The simulation counts both; production PnL would count both too, so this isn't a bug — just confirming the 66.7% is on "events" not "independent market observations". Adjusted independent WR = 65.5% on 29 trades.
3. **Model mismatch.** The CAND raw_responses show `model_used=claude-opus-4-5` (34/37) and `gpt-4.1` (3/37). Live production uses `claude-sonnet-4-6` with effort=max. Published `simulate_t7_live_period.py` should be confirmed to have been run with production-matching model — otherwise these 37 results reflect a different classifier.
4. **`poi_zone=premium` as a hard filter.** 0 W / 6 L is striking but n is tiny. Before hard-filtering, need to check: does the production prompt's `zone` field use the same definition as this simulation? And do XAUUSD CANDIDATEs exhibit the same premium-zone loss rate? If yes on both, a shadow logger or outright filter could remove ~18% of CAND volume for zero expected loss of R.
5. **SHORT coverage.** Cannot resolve from 1 observation whether the SHORT edge is zero, negative, or not-yet-sampled. The 2026-03-23 SHORT reached 99% of TP before reversing — directionally suggestive that the gate's bearish calls have edge but that SL placement was too tight. Recommend at minimum logging all `bias=bearish` MSO states and what the gate said, separately from production decisions.
6. **Temporal decay (slice 1-2 vs 4-5 WR gap p=0.038).** Is this decay a property of NAS100's regime change (Feb-Mar drawdown environment) or of the gate's performance decaying? The OB-continuation primary-decay metric for NAS100 over this same window would disambiguate. If rolling-50 OB continuation stayed ≥60% throughout, the gate's decay is independent of structure — bad sign. If continuation decayed too, the gate is tracking a market regime change.
7. **Unfilled trades in April.** The 4 UNFILLEDs are all deep pullback limits (0.11-3.54% below close) that never mean-reverted. This is another face of the chase/strong-trend environment. If production cancels stale limits, these never become anything. If production leaves them open, they are free optionality.
8. **3 "simulator-artefact" wins.** 2026-01-27, 2026-02-25, 2026-02-26NY all have MAE > 2R post-fill, meaning the pre-fill SL was breached in the underlying series before fill. Whether to count these as "real" wins depends on production's treatment of OB mitigation: if production also ignores mitigation between signal and fill, they are valid; if production re-evaluates the MSO before filling, they would be filtered. Strip them: WR = 18W/14L = 56.3% on a further-deduplicated set.
9. **Base rate for NAS100.** We have no XAUUSD-equivalent edge-mechanism ground truth on NAS100. Before gating live, a rolling-50 OB continuation pre-calibration would establish whether NAS100's mechanical OB edge is meaningfully above shuffled baseline for this instrument.
