# Q-16 Adversarial / Game-Theoretic Analysis

Generated: 2026-04-17 10:33 local
Script: `research/academic_pipeline/scripts/q_16_adversarial.py`
Cost: $0 (local only).

## Pre-registered hypotheses

Stated BEFORE any data inspection. No post-hoc threshold tuning.

**Q-16.1 — Predatory / forced-flow detection.**

- H1. Candles where (range/ATR14) > 3 AND tick_volume is in top-decile of prior 50 bars AND close is within 20% of the candle's high (or low) exhibit a 6-candle forward reversion rate >= 55%, vs 50% null. One-prop z-test, two-sided.
- H2. Forced-flow candles show higher reversion WR than extreme-range-but-normal-volume candles (baseline). Two-prop z-test.
- Pre-registered significance: Bonferroni-adjusted α = 0.05/4 = 0.0125.

**Q-16.3 — Session-open patterns.**

- H3. At least one session-open bucket (first 15m / 15-60m / mid / last 30m) shows mean range >= 1.5× the non-session baseline, with Welch's t two-sided p < 0.01.
- H4. Sydney/Tokyo/London/NY opens (retail CFD-relevant hours) each differ measurably from baseline — report ratios even if non-significant.

**Q-16.5 — OHLCV-VPIN proxy (informed vs uninformed flow).**

- H5. Classifying tick_volume via close-in-range Bulk Volume Classification, then computing rolling 50-bar VPIN, and matching each XAUUSD trade to the prior-session VPIN: the WR gap between the top and bottom tercile is >= 5 percentage points with p < 0.0125 (two-prop z).
- H6. Trade-population terciles are balanced (within 20% of uniform).

**Q-16.6 — Game-theoretic response to SMC crowding.**

- Qualitative. Operational question: If OB retest is in fact crowded, which of (a) deeper entry, (b) earlier exit, (c) fade the crowd, (d) alternative instruments is the defensive play, and which does the current system already implement? The 'evidence that would update' field specifies what data would trigger re-classification.

## Upfront caveats and scope

- **Tick volume on CFD is a proxy for true trade volume.** CFD tick_volume = number of price updates received by the broker terminal, not volume traded at venue. High correlation with real volume in most regimes, but systematically biased during illiquid overnight hours (broker feed heartbeat dominates) and during news spikes (multiple price updates per true trade). This applies to Q-16.1 and Q-16.5.
- **MT5 broker clock.** CSVs are in broker-local time (typically EET/EEST; the data starts at 01:00 not 00:00, consistent with EET/EEST where hour 0 = 22:00/23:00 UTC the prior day). We label sessions by broker clock and report UTC equivalents in the Q-16.3 section. The Jan 2 - Apr 10 window straddles the Mar 8 2026 US DST change and the Mar 29 2026 EU DST change — this introduces minor session-drift noise that is not corrected here.
- **Data window is 2026-01-02 to 2026-04-10 only.** Historical CSVs do not extend pre-2026. Q-16.5 can only match batch trades within this window (~29/111).
- **Cross-reference with Wave 2.** Q-16.5 shares trade-population dependence with Q-crowding_retail.md (Q-8.3/Q-16.4); if a VPIN WR gap exists, it may be confounded with the same upward-trending WR documented there (Kendall tau +0.754, p<0.001). Sample-overlap flagged explicitly.

## Data

- **M15 bars:** `C:/Users/MSI/Documents/ai-trading-agent/data/historical_2026/XAUUSD_M15.csv` — 6420 bars, 2026-01-02 01:00 → 2026-04-10 23:45.
- **H1 bars:** `C:/Users/MSI/Documents/ai-trading-agent/data/historical_2026/XAUUSD_H1.csv` — 1606 bars.
- **Batch trades:** `C:/Users/MSI/Documents/ai-trading-agent/knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` — n=111. 2026-only subset used for Q-16.5 matching: n=29.

## Q-16.1 — Predatory / forced-flow detection

### Method (deterministic)

1. Compute ATR14 on M15 bars (Wilder's smoothing).
2. For each bar i with i > 50 and i + 6 < N: flag if
   - (high-low) / ATR14 > 3.0, AND
   - volume >= 90th percentile of the prior 50 bars, AND
   - close within 20% of high (bullish forced) OR within 20% of low (bearish forced).
3. Reversion test: for a bullish forced candle, contrarian = SHORT; WIN if in the next 6 bars any bar's low <= candle mid. Symmetric for bearish.
4. Baseline: extreme-range candles (> 3x ATR) without top-decile volume. Same close-extreme and reversion rules.

### Results

- Eligible bars (post-ATR-warmup, pre-lookahead buffer): 6,364
- Extreme-range candles total (>3× ATR, any volume): 47

| subset | n | reversion wins | WR |
|---|---|---|---|
| forced UPs (bull close) | 7 | 4 | 0.571 |
| forced DNs (bear close) | 12 | 6 | 0.500 |
| **forced pooled** | **19** | **10** | **0.526** |
| baseline UPs | 2 | 0 | 0.000 |
| baseline DNs | 1 | 0 | 0.000 |
| **baseline pooled** | **3** | **0** | **0.000** |

- **Forced vs 50% null:** z = 0.229, two-sided p = 0.819
- **Forced vs baseline:** z = 1.701, two-sided p = 0.089

### Q-16.1 verdict

**UNDERPOWERED** — n < 20 forced-flow candles. Extend data window or relax thresholds to re-test.

## Q-16.3 — Session-open patterns

### Method

1. For each of 4 sessions (Sydney, Tokyo, London, NewYork), define a 4-hour session window starting at broker-clock session open.
2. Within each window, bucket M15 bars by minute-of-session: first 15m, next 15-60m, mid-session (60-180m), last 30m.
3. Compare mean bar range to the non-session baseline (all M15 bars that fall in none of the 4 sessions).
4. Welch's t-test, two-sided. Pre-registered α = 0.01.

- **Baseline (non-session bars):** n=2236, mean range=13.664, mean norm-range=0.00283, mean volume=2,521

### Session x bucket range vs baseline

| session | bucket | n | mean_range | ratio (vs baseline) | welch t | p (two-sided) |
|---|---|---|---|---|---|---|
| NewYork | midSession | 560 | 23.548 | 1.72× | 11.076 | <0.001 |
| NewYork | first15 | 70 | 21.013 | 1.54× | 4.098 | <0.001 |
| Tokyo | midSession | 560 | 19.258 | 1.41× | 7.013 | <0.001 |
| NewYork | next15_60 | 210 | 18.277 | 1.34× | 4.988 | <0.001 |
| Sydney | last30 | 280 | 17.337 | 1.27× | 4.178 | <0.001 |
| Tokyo | first15 | 70 | 17.270 | 1.26× | 2.028 | 0.043 |
| NewYork | last30 | 280 | 16.422 | 1.20× | 3.322 | <0.001 |
| Sydney | first15 | 68 | 15.378 | 1.13× | 1.211 | 0.226 |
| London | first15 | 70 | 15.118 | 1.11× | 0.874 | 0.382 |
| Tokyo | next15_60 | 210 | 14.678 | 1.07× | 1.222 | 0.222 |
| Sydney | next15_60 | 204 | 14.102 | 1.03× | 0.574 | 0.566 |
| London | next15_60 | 210 | 13.708 | 1.00× | 0.051 | 0.959 |
| Tokyo | last30 | 280 | 13.654 | 1.00× | -0.013 | 0.990 |
| London | midSession | 560 | 13.165 | 0.96× | -0.869 | 0.385 |
| London | last30 | 280 | 12.304 | 0.90× | -1.882 | 0.060 |
| Sydney | midSession | 272 | 9.836 | 0.72× | -6.032 | <0.001 |

### Broker-clock -> UTC mapping (approximate, DST-sensitive)

| Session | Broker-clock open | UTC (pre-DST, Jan-Mar 8) | UTC (post-DST, Mar 29+) |
|---|---|---|---|
| Sydney | 22:00 broker | 20:00 UTC | 19:00 UTC |
| Tokyo | 02:00 broker | 00:00 UTC | 23:00 UTC (prev day) |
| London | 10:00 broker | 08:00 UTC | 07:00 UTC |
| NewYork | 15:30 broker | 13:30 UTC | 12:30 UTC |

These UTC mappings are approximate — the CSV's broker clock is EET/EEST (UTC+2 winter, UTC+3 summer). The data window spans EU DST (Mar 29 2026) and US DST (Mar 8 2026); session-open windows will drift by 1h across the window. Any conclusion that hinges on a specific hour-bucket within < 30min precision should be re-computed with timezone-aware bars. For the pre-registered H3 threshold (1.5× ratio, p<0.01), DST drift is not material.

### Q-16.3 verdict

**SIGNAL** — 2 bucket(s) meet the pre-registered (ratio >= 1.5x, p < 0.01) threshold:

- NewYork / midSession: 1.72× baseline, t=11.076, p=<0.001
- NewYork / first15: 1.54× baseline, t=4.098, p=<0.001

These buckets are consistent with forced order flow / spread-cost amplification around session opens. Already partially captured by the GTOS kill zone schedule (London 07:00-10:30 UTC, NY 13:00-17:00 UTC for XAUUSD) — cross-check these session-opens are inside kill zones.

## Q-16.5 — OHLCV-VPIN proxy

### Method

1. Bulk Volume Classification: for each M15 bar, buy_frac = (close-low)/(high-low); buy_vol = buy_frac x volume; sell_vol = (1-buy_frac) x volume.
2. Rolling 50-bar VPIN: sum |buy_vol - sell_vol| / sum volume.
3. Match each batch trade by trade date -> prior trading day's last M15 bar VPIN. Prior-day is used (not same-day) to avoid trivial lookahead.
4. Tercile split on VPIN. Compute WR per tercile.

- Matched trades: **29** / batch 111
- Skipped (no prior M15 bar in window): 82
- Skipped (VPIN not yet converged at bar): 0
- VPIN range: 0.4497 → 0.5640 (median 0.5133)
- Tercile thresholds: low<=0.4930, high>=0.5184

| tercile | n (W+L+BE) | wins | losses | WR | exp_R |
|---|---|---|---|---|---|
| low | 10 | 7 | 3 | 0.700 | 0.391 |
| mid | 8 | 5 | 3 | 0.625 | -0.054 |
| high | 11 | 6 | 5 | 0.545 | 0.097 |

- **High vs low tercile:** z = -0.728, two-sided p = 0.466
- **WR gap (high - low):** -15.5 pp

### Q-16.5 verdict

**NO SIGNAL** — WR gap (high-low) is -15.5pp with p=0.466. Pre-registered threshold (|gap| >= 5pp, p<0.0125) not met. OHLCV-derived VPIN does not discriminate entry quality on this sample. Direction note: the sign is inverted from the naive 'informed flow helps' prior — low-VPIN (balanced flow) tercile WR is higher than high-VPIN (directionally imbalanced flow). If real, this would be consistent with 'strong directional flow before entry is a warning, not a signal' — but at p=0.466 this is underpowered and not actionable. Revisit when the pre-2026 M15 data gap is closed.

## Q-16.6 — Game-theoretic response to SMC crowding

Qualitative, no statistical test. Operational question: if OB-retest is a crowded trade, which defensive play should the system prefer?

### Candidate responses, mapped against current system

| Option | Defensive rationale | Current system | Evidence that would update |
|---|---|---|---|
| (a) Deeper entry / pre-retest | If crowd fills at the OB edge, pre-position closer to the OB mid / 50% zone to get filled before crowd liquidity absorbs the move. | PARTIAL. Limit-order architecture (handoff 16) lets price be caught on pullback; m5_refinement can tighten entry. No explicit 'mid-OB' entry pricing — default entry_price is AI-nominated edge. | If a batch sub-analysis shows mid-OB-50% entries have materially better MFE/R than edge entries on the same setups (n>=30, p<0.0125), tighten entry_price to 0.5 * (ob_high + ob_low) for LONGs. |
| (b) Earlier exit / skim first touch | If the crowd takes profit at +1R and unwinds the move, capture 33-50% at 1R before the reversal. | SHADOW-LOGGED. partial_close_shadow_logger (Variant C: 33% @ 1.0R) is running observation-only. Not yet promoted. BE shadow logger tracks +1R -> BE hypothetical. | If the partial_close shadow logger shows >0 delta_R with p<0.05 across 30+ trades, promote to live (per existing WF-2 promotion rules). |
| (c) Fade the SMC crowd (go opposite) | If OB retests systematically fail, the contrarian position becomes the edge. Stop-hunt / forced-flow candles (Q-16.1) are a direct instantiation of this. | NOT IMPLEMENTED. Q-16.4 contrarian framework was previously underpowered (n=2 matched). Q-16.1 adds candle-level forced-flow detection. | (1) Q-16.1 pooled reversion WR >= 55% with p<0.0125 AND baseline delta >= 5pp -> shadow-log a forced-flow contrarian signal. (2) Rolling-window WR of the live strategy trending negatively (Kendall tau < 0, p < 0.05 on a fresh window >= 40 trades) would warrant a directional flip trial. |
| (d) Alternative instruments / niche diversification | Crowd effects are correlated with venue popularity. Trading a less-crowded cross (e.g., USDJPY, GBPJPY) or a less-SMC-targeted instrument diversifies the adversary. | IMPLEMENTED. Portfolio is already 5 instruments. USDJPY batch WR 75.8% (n=33, p=1.96e-4) — strongest; GBPJPY 57.1% (n=42, weakest). GBPUSD observer-only. US30 68% continuation on sweep divergence (handoff H16). | If USDJPY live WR holds above XAUUSD live WR across another 30+ trades with p<0.05, CEO could allocate more risk budget to USDJPY. The 8% drawdown rule (H29) makes this automatic to some degree. |

### Q-16.6 verdict (qualitative)

The current system is **primarily on plays (b) and (d)**: partial_close (shadow), BE shadow logger, and a 5-instrument portfolio explicitly diversifying away from pure XAUUSD-SMC exposure. Play (a) is partial via m5_refinement; play (c) is not implemented. Q-16.1 (this document) is the natural data-collection hook for play (c).

If Q-16.1 surfaces a SIGNAL verdict, promote forced-flow contrarian as a candidate SHADOW-logged signal (observation-only), consistent with the WF-2 shadow-gate promotion protocol. Do not deploy as a live rule without 30+ shadow-observed outcomes and CEO approval.

## Caveats and cross-references

1. **Tick-volume proxy bias.** CFD tick_volume is not real trade volume. Q-16.1 and Q-16.5 interpretations both degrade in overnight / illiquid / news-spike regimes. Independent L1-quote or tape data would strengthen both.
2. **Data window 2026-01-02 to 2026-04-10.** All historical-bar analysis is inside this quarter. No seasonal / multi-regime validation is possible locally.
3. **Sample overlap with Q-crowding_retail (Q-8.3/Q-16.4).** Q-16.5 uses the same batch trades. The +0.754 Kendall tau of rolling-window WR (documented there) is a time-trend confound for any VPIN-vs-WR relationship unless VPIN is de-trended.
4. **Broker-clock / DST.** All session-segmentation in Q-16.3 is in broker-clock. The Mar 8 (US) and Mar 29 (EU) DST changes drift each session open by 1h UTC — effect is small for 4h session buckets but real. A UTC-aware re-run is a future task.
5. **Multiple testing.** Four primary tests (Q-16.1 vs null, Q-16.1 vs baseline, Q-16.3 any session bucket, Q-16.5 high-vs-low). Bonferroni α = 0.0125 was pre-registered and applied.
6. **Q-16.6 is qualitative.** The 'evidence that would update' fields specify what would trigger re-classification; no statistical claims are made on the mapping itself.

## Verdicts (summary)

- **Q-16.1 (forced-flow):** UNDERPOWERED
- **Q-16.3 (session-open patterns):** SIGNAL (2 bucket(s) >= 1.5× baseline at p<0.01)
- **Q-16.5 (VPIN):** NO SIGNAL (|gap|=15.5pp, p=0.466)
- **Q-16.6 (crowding defense):** System is already on plays (b) and (d) (partial-close shadow + 5-instrument portfolio). (a) is partial, (c) is not implemented. Q-16.1 is the data hook for (c).

## Next steps

1. If Q-16.1 is SIGNAL: stand up a SHADOW-MODE logger that records forced-flow detections and 6-candle forward outcomes on live bars. 30+ observations with p<0.05 -> CEO review for WF-2 promotion.
2. If Q-16.3 is SIGNAL: audit that all hot buckets lie inside active kill zones. Any hot bucket *outside* kill zones is either (a) a kill-zone calibration miss or (b) a candidate micro-session to add.
3. If Q-16.5 is underpowered, close the pre-2026 M15 data gap (as with Q-crowding_retail) then re-run.
4. Q-16.6: when the partial-close shadow logger crosses 30 BE-triggered trades, re-run the evidence check in the play-(b) row and decide promote/kill per protocol.
5. **Do NOT deploy any of the above as live gates from this document.** These are adversarial-lens diagnostics. Live changes require the standard shadow-then-promote workflow and CEO approval.

*End of report.*