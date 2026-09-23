# NAS100 T7 Validation — Direction, Regime, and OB-Proximity Rejects

_Generated 2026-04-19. Source: 5 slice JSONs in `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json` + `data/historical_2026/NAS100_D1.csv` + `NAS100_M15.csv`. All 1600 M15 candles covered Jan 02 → Apr 17 2026 (though record counts per week vary due to KZ hours and holidays)._

_Cross-cutting caveat: per the B_ai_notrade report in this same directory, this simulation ran the `claude-opus-4-5` evaluator (not live `claude-sonnet-4-6`). Opus is known (per CLAUDE.md memory) to produce CR 19% vs Sonnet 38% on the MSO gate — roughly half the CANDIDATE rate. Every claim below about directional bias distribution, CR asymmetry, and fitness must be read as an Opus observation. Rerun on Sonnet before gate-live decisions._

---

## TL;DR

- **NAS100 regime Jan 02 – Apr 17 was V-shaped**: +5.83% net close-to-close (25,202 → 26,671), with a -13.12% drawdown trough on Mar 31 followed by a +17.30% rally to Apr 17 peak. 16 trading weeks: 6 bullish >1%, 4 bearish <-1%, 6 flat. The 36:1 LONG:SHORT CANDIDATE ratio is primarily a **deterministic D1-bias artifact**, not pure regime: only 2 of 16 weeks (W13, W14) even permitted SHORT-required calls, and in W14 D1 was still printing "bearish" while NAS100 rallied +4.20%.
- **One SHORT CANDIDATE (Mar 23, slice 4, -1.0R loss)**: structurally flawless A+ setup with H1 CHoCH bearish + M15 displacement + PDL sweep. Killed by an intraday reversal — the Mar 23 daily bar itself was a +2.1% outside-reversal (L=23561 → C=24201), and the trade was stopped by an 882-point bullish spike in a single M15 bar at 14:00Z.
- **The D1 bias source is the binding direction gate, not AI discretion.** In all 4 BEAR weeks, AI-evaluated records totaled 266; only 55 (W13 alone, 21%) had D1 bias=bearish. The other 211 were sent up as "LONG required" by the deterministic pre-gate even inside declining weeks. W14 was the starkest case: 54 AI-seen records, 54 bearish bias from lagged D1, 54 C1 FAIL (H1 had already flipped bullish) — 0 CANDIDATEs during a +4.20% rally.
- **432 `price_far_from_ob` rejects look correctly filtered.** Only 1.4% of the skipped candles saw price move ≥ the reported OB-gap within 2h; 7.2% within 4h; 36.3% by end-of-day. Of 73 multi-reject day-KZ clusters, 15 (20.5%) eventually yielded a CANDIDATE later in the same KZ — the filter is not over-pruning tradable setups. 110 `no_unmitigated_ob` rejects are distributed across weeks, not concentrated in regime shifts; no systematic weakness detected.
- **Fitness verdict is "promising but not clean".** NAS100 at 66.7% WR on 33 filled CANDIDATEs, +22.03R sum, +0.668R avg. Pre-AI rejects are 48.9% of all candles (15.0% prescreen + 33.9% ob_proximity). The post-AI CANDIDATE rate (37/818 = 4.5%) is roughly half XAUUSD's 10.3% baseline — most of that gap is plausibly the Opus-vs-Sonnet mismatch, not instrument fitness. Keep NAS100 on the table; rerun on Sonnet before committing.

---

## Q1 — NAS100 regime Jan 02 → Apr 17 2026

### Headline numbers (from `NAS100_D1.csv`)

| Metric | Value | CSV anchor |
|---|---|---|
| Start close | 25,202.86 | 2026-01-02 |
| End close | 26,671.26 | 2026-04-17 |
| Net move | +1,468.40 pts / **+5.83%** | |
| Overall high | 26,722.08 | 2026-04-17 |
| Overall low | 22,780.75 | **2026-03-31** |
| Max drawdown from rolling peak | **-13.12%** | Peak 2026-01-28 → trough 2026-03-31 |
| Max rally from rolling trough | **+17.30%** | Trough 2026-03-31 → peak 2026-04-17 |

This is **not a clean trend**. Two distinct regimes:

- **Regime A (Jan 2 – Mar 31):** net declining. Peak high 26,219 on Jan 28, trough low 22,780 on Mar 31. ~-13% drawdown over ~9 weeks (Feb sell-off + March panic).
- **Regime B (Mar 31 – Apr 17):** vertical recovery. +17.3% in 13 trading days. W14 +4.20%, W15 +5.37%, W16 +7.56%.

**Confidence: high.** Pulled directly from the CSV; no interpretation needed.

### Week-by-week trajectory

(ISO week. Open = Monday open, close = Friday close or last day available. Range = weekly H/L spread relative to weekly low.)

| Week | Dates | Open | Close | Net % | High | Low | Range % | Verdict |
|---|---|---|---|---|---|---|---|---|
| W01 | 2026-01-02 | 25252.26 | 25202.86 | -0.20% | 25593.50 | 25074.80 | 2.07% | flat (1-day partial) |
| W02 | 2026-01-05 → 01-09 | 25259.36 | 25755.06 | **+1.96%** | 25815.10 | 25224.26 | 2.34% | BULL |
| W03 | 2026-01-12 → 01-16 | 25721.06 | 25530.15 | -0.74% | 25878.95 | 25262.43 | 2.44% | flat |
| W04 | 2026-01-19 → 01-23 | 25274.86 | 25556.75 | **+1.12%** | 25710.13 | 24881.25 | 3.33% | BULL |
| W05 | 2026-01-26 → 01-30 | 25328.76 | 25517.96 | +0.75% | 26219.45 | 25324.16 | 3.54% | flat |
| W06 | 2026-02-02 → 02-06 | 25383.46 | 25006.26 | **-1.49%** | 25915.25 | 24143.85 | 7.34% | BEAR |
| W07 | 2026-02-09 → 02-13 | 25155.46 | 24709.86 | **-1.77%** | 25380.53 | 24504.73 | 3.57% | BEAR |
| W08 | 2026-02-16 → 02-20 | 24707.06 | 25014.05 | **+1.24%** | 25078.03 | 24380.83 | 2.86% | BULL |
| W09 | 2026-02-23 → 02-27 | 24993.66 | 24906.76 | -0.35% | 25442.46 | 24610.43 | 3.38% | flat |
| W10 | 2026-03-02 → 03-06 | 24707.56 | 24642.46 | -0.26% | 25207.55 | 24314.73 | 3.67% | flat |
| W11 | 2026-03-09 → 03-13 | 24245.46 | 24339.76 | +0.39% | 25189.98 | 23976.55 | 5.06% | flat |
| W12 | 2026-03-16 → 03-20 | 24348.16 | 23993.86 | **-1.46%** | 24981.75 | 23759.83 | 5.14% | BEAR |
| W13 | 2026-03-23 → 03-27 | 23759.06 | 23075.16 | **-2.88%** | 24550.55 | 23045.66 | 6.53% | BEAR |
| W14 | 2026-03-30 → 04-03 | 22991.66 | 23956.45 | **+4.20%** | 24166.23 | 22780.75 | 6.08% | BULL |
| W15 | 2026-04-06 → 04-10 | 23865.56 | 25147.06 | **+5.37%** | 25227.43 | 23771.83 | 6.12% | BULL |
| W16 | 2026-04-13 → 04-17 | 24796.76 | 26671.26 | **+7.56%** | 26722.08 | 24758.55 | 7.93% | BULL |

**Summary: 6 bullish >1%, 4 bearish <-1%, 6 flat, 1 cold-start partial.**

Bearish weeks: W06, W07 (early Feb sell-off), W12, W13 (March meltdown). Bullish weeks: W02, W04, W08 (pre-decline), then the three-week V-shaped rally W14/W15/W16.

**Confidence: high.**

---

## Q2 — Is the 36:1 LONG:SHORT bias regime or prompt?

### Week × decision × bias cross-table

| Week | Label | Total | AI-seen | AI bias bull | AI bias bear | CAND | LONG | SHORT | R sum |
|---|---|---|---|---|---|---|---|---|---|
| W01 | flat | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| W02 | BULL +1.96% | 100 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| W03 | flat | 100 | 50 | 50 | 0 | 4 | 4 | 0 | +6.03 |
| W04 | BULL +1.12% | 120 | 53 | 53 | 0 | 3 | 3 | 0 | +1.99 |
| W05 | flat | 100 | 70 | 70 | 0 | 3 | 3 | 0 | +4.50 |
| W06 | **BEAR -1.49%** | 100 | 54 | **54** | 0 | 1 | 1 | 0 | +1.50 |
| W07 | **BEAR -1.77%** | 120 | 92 | **92** | 0 | 3 | 3 | 0 | +2.00 |
| W08 | BULL +1.24% | 100 | 46 | 46 | 0 | 0 | 0 | 0 | 0 |
| W09 | flat | 100 | 76 | 76 | 0 | 4 | 4 | 0 | +3.51 |
| W10 | flat | 120 | 79 | 79 | 0 | 3 | 3 | 0 | +2.00 |
| W11 | flat | 100 | 48 | 48 | 0 | 5 | 5 | 0 | +5.00 |
| W12 | **BEAR -1.46%** | 100 | 65 | **65** | 0 | 3 | 3 | 0 | -3.00 |
| W13 | **BEAR -2.88%** | 120 | 55 | 0 | 55 | 1 | 0 | 1 | -1.00 |
| W14 | BULL +4.20% | 100 | 54 | 0 | **54** | 0 | 0 | 0 | 0 |
| W15 | BULL +5.37% | 100 | 20 | 20 | 0 | 2 | 2 | 0 | +0.50 |
| W16 | BULL +7.56% | 100 | 48 | 48 | 0 | 5 | 5 | 0 | -1.00 |

### Key observations

1. **Bias source is the D1 deterministic computation** (`bias_source = "D1"` in 54/54 W14 records, `"H4+H1_consensus"` or `"D1"` elsewhere). AI inherits the direction; it does not independently decide to go SHORT.
2. **Only 2 of 16 weeks (W13, W14) ever printed `bias=bearish`**, totaling 109 evaluations (W13 n=55, W14 n=54). Every other week was locked to LONG-required by the pre-gate.
3. **In bearish W06, W07, W12 (n=211 AI-seen records), AI was still handed "bullish" bias** — the D1-bias computation did not react to intra-week declines of 1.5-1.8%. This likely reflects a slow-moving D1 bias (needs multi-day BOS confirmation) combined with those weeks not registering as bearish at D1 scale — the overall regime top was still intact at W05 peak 26219 until W06 broke below it.
4. **W14 is the clearest mismatch.** NAS100 rallied from 22,991 → 23,956 (+4.20%) in this week. All 54 AI-evaluated records came in with `bias=bearish` (from lagged D1 after W13's -2.88% capitulation). The AI itself refused all 54 with "C1 FAIL: H1 structure is bullish, required SHORT but no bearish confirmation." The AI is doing its job — refusing to trade against H1 — but the pre-gate fed it an obsolete D1 bias during a sharp regime inflection. **0 CANDIDATEs produced in a +4.20% rally week.**

### Was there evidence of prompt SHORT-suppression?

**Partially clean test, but not conclusive:**

- Of 109 `bias=bearish` evaluations, only **1 CANDIDATE was produced** (W13, Mar 23). CR = 0.9%.
- Of 709 `bias=bullish` evaluations, **36 CANDIDATEs**. CR = 5.1%.
- Gap = 5.7× in favor of LONG (bias-conditioned).

A ~5× CR asymmetry conditioned on required direction is suggestive of either: (a) the prompt/framework having weaker SHORT-detection, (b) NAS100 genuinely offering fewer clean SHORT OB-retests (OBs in Feb-Mar selloff were not clean-displacement), or (c) D1 bias flipping bearish too late to catch the actual move (it activated in W13 when the decline had been in progress for 2 weeks).

**The right way to resolve this is to look at what AI said on bearish-bias C1 FAILs.** Across 106 bearish C1 FAILs, the most common pattern is: "H1 structure is bullish (5 bullish BOS) but required trade direction is SHORT per D1/H4 bearish bias — H1 does not confirm." This is **H1 disagreeing with D1**, not AI suppressing SHORTs. When H1 actually did align bearish (Mar 23 09:00 CHoCH), AI produced the SHORT CANDIDATE.

**Confidence: medium-high on "regime effect + D1 lag dominates, not prompt bias"**. Full audit would require a Sonnet rerun during W13/W14 to test whether a different evaluator catches more SHORT setups, plus examining whether the D1 bias computation has a regime-shift leaky bucket.

---

## Q3 — The single SHORT (Mar 23, slice 4)

### Record

```
candle_time: 2026-03-23T09:30:00Z
kill_zone: london
direction: SHORT
entry_price: 23734.25  (H1 OB low edge)
stop_loss: 23821.75    (+87.5 pts above)
take_profit_1: 23603.00 (-131.25 pts below)
risk_reward: 1.5
candle_close: 23660.15
setup_grade: A+
bias: bearish (D1)
outcome: LOSS, r_multiple=-1.0, exit 2026-03-23T14:00Z
```

### Structural context (from raw_response)

The AI wrote:
- H1 CHoCH bearish at 23,725.25 with displacement ratio 1.9
- H4 confirmed bearish with 5 consecutive bearish BOS
- Nearest unmitigated H1 bearish OB at 23,792.15 – 23,734.25 (touches=2), caused by the CHoCH at 07:00Z
- Asian low / PDL swept at 23,660.05 with close at 23,660.15 (clean liquidity sweep below session lows)
- M15 CHoCH bearish at 23,734.25 with ratio 1.9 and displacement=True
- All C-gates PASS. Framework `ob_retest` qualified. Confidence 72.

This is a textbook bearish OB-retest setup: structure break, sweep, return-to-OB entry.

### Market context (from `NAS100_D1.csv` + `NAS100_M15.csv`)

D1 row for 2026-03-23: O=23759.06, H=24550.55, L=23561.85, C=24201.26 — an **outside-reversal bullish day**. Low at 23561 (session sell-off completed before 10:30Z), then a ~1000-point intraday rally to close at 24201.

M15 trace (abridged):

| Time (UTC) | Open | High | Low | Close | State |
|---|---|---|---|---|---|
| 09:30 | 23716.85 | 23716.85 | 23660.05 | 23660.15 | signal candle closes |
| 09:45 | 23659.85 | 23673.55 | 23615.35 | 23643.85 | waiting |
| 10:15 | 23682.55 | 23685.35 | **23561.85** | 23587.85 | final low of session |
| 11:30 | 23685.15 | **23740.05** | 23679.75 | 23706.35 | **limit fills at 23734.25** |
| 11:45 → 13:45 | | max 23759 | min 23604 | — | in-trade, MFE ~+0.5R, MAE close to SL |
| 14:00 | 23668.75 | **24550.55** | 23664.85 | 24511.15 | **SL hit (-1R)** — 882-pt bull spike in 15 min |

**Post-mortem:** The setup was correct at 09:30Z entry-signal time. Price then drifted lower (-low at 23561 at 10:15, below the OB), reversed, filled the SHORT limit at 11:30 on a pullback to 23,740, chopped within the OB zone for 2.5 hours, and was stopped out by a single 882-point bull-bar at 14:00Z (NY open). The daily close ended at 24201 — the short trade, even if given more runway, would have been structurally invalidated by the 14:00 reversal.

This is the classic "right signal, wrong day" outcome: the Mar 23 outside-reversal day was a major bullish inflection, and even a correctly-framed SHORT from the London morning OB could not survive the NY-session reversal to daily high. The -1R loss is expected behavior.

**Confidence: high.** The signal, the trade parameters, and the M15 trajectory all cross-verify.

---

## Q4 — Is the OB-proximity filter too aggressive? (432 `price_far_from_ob`)

### Distance distribution of rejected candles

The reported pct_dist (gap from current price to nearest unmitigated H1 zone edge, beyond the 1.0% tolerance threshold) is between 1.0% and 4.0%:

| Dist bucket | Count | % |
|---|---|---|
| 1.0-1.4% | 162 | 37.5% |
| 1.5-1.9% | 132 | 30.6% |
| 2.0-2.4% | 91 | 21.1% |
| 2.5-2.9% | 23 | 5.3% |
| 3.0-3.4% | 18 | 4.2% |
| 3.5-4.0% | 6 | 1.4% |

Median distance: 1.6%. At NAS100 ~25,000 that is ~400 points — well outside a retest.

### 2h / 4h / same-day forward lookahead (all 432 records)

For each rejected candle, I measured the max price move (any direction) within the lookahead window. "Retest plausible" = max move ≥ reported pct_dist (i.e., price covered the gap at some point).

| Lookahead | Retest plausible | Partial move (≥ half the gap) | Neither |
|---|---|---|---|
| 2h (8 bars) | **6 / 432 = 1.4%** | 77 (17.8%) | **349 (80.8%)** |
| 4h (16 bars) | 31 / 432 = 7.2% | 155 (35.9%) | 246 (56.9%) |
| End of day | 157 / 432 = 36.3% | 198 (45.8%) | 77 (17.8%) |

Within 2 hours — the tight window where an OB retest from rejection is physically possible — only 6 candles in 432 (1.4%) saw the market cover the reported gap. **The rejected candles are, on a same-day basis, legitimately far from OBs and do not revisit.**

### Retest rate by distance bucket (2h)

| Dist | Retest rate |
|---|---|
| ~1.0-1.4% | 4% (6/162) |
| ~1.5-1.9% | 0% (0/132) |
| ~2.0+% | 0% (all zero) |

Only the narrowest-rejected candles saw any short-term retest. This is consistent with expected physics: 2.0%+ gaps in 2h would require ~500-point NAS100 swings; those are rare outside news events.

### Cluster conversion — did OB retests materialize later in same day+KZ?

I grouped all 542 `ob_proximity:*` rejects by (date, kill_zone) and checked whether later bars in the same day+KZ ultimately produced a CANDIDATE.

- 75 total date+KZ combinations with proximity rejects.
- **15 of 73 multi-reject clusters (20.5%) ended with a subsequent CANDIDATE in the same KZ.**
- Top examples: 2026-01-13 NY (6 rejects then CAND), 2026-02-06 London (6 rejects then CAND), 2026-03-05 London (5 rejects then CAND), 2026-03-17 NY (6 rejects then CAND).

In other words, the filter is NOT preventing tradable setups. When price is far from OB early in the KZ, rejection is correct; when it returns later (after a pullback), the filter correctly allows the signal through. The 15 "cluster → CANDIDATE" transitions are precisely the "too early" pattern being handled correctly.

### Could we raise tolerance?

The filter uses `tolerance_pct = 0.01` (1.0%). If raised:

| Tolerance | `price_far_from_ob` records that would pass | Extra API cost (@ $0.029/call) |
|---|---|---|
| 1.0% (current) | 0 | baseline |
| 1.5% | 203 additional | +$5.89 |
| 2.0% | 319 additional | +$9.25 |
| 2.5% | 394 | +$11.43 |

If hit rate on new calls ~4.5% (matches current NAS100 AI-seen CR), raising to 2.0% would generate ~14 extra CANDIDATEs at ~$9 cost, but most of those would likely C-gate fail at AI since the proximity filter duplicates the downstream L2 proximity check. The 2h lookahead data shows 98.6% of current rejects genuinely don't interact with the OB — raising tolerance would mostly burn API dollars on candles the AI would then NO_TRADE on proximity grounds anyway (see B_ai_notrade report: 231 of 613 AI NO_TRADEs are "all gates pass but price too far from OB", i.e., the AI is already rejecting similar geometry at its own level).

**Verdict: the 1.0% tolerance looks correctly calibrated for NAS100. Raising it would add cost without clear EV improvement.**

**Confidence: medium-high.** The 2h / 4h / same-day lookahead data is quantitative; the cluster-conversion data is direct evidence of correct handling. The one unknown is whether a different OB-detection (M15 or H4 OBs) might produce more tradable zones — but that's a different filter-design question.

---

## Q5 — "No unmitigated OB" rejects (110)

### Distribution by date

| Date | Count | Week | Week label |
|---|---|---|---|
| 2026-01-07 | 20 | W02 | BULL +1.96% |
| 2026-01-08 | 12 | W02 | BULL +1.96% |
| 2026-01-13 | 16 | W03 | flat |
| 2026-01-14 | 10 | W03 | flat |
| 2026-02-23 | 20 | W09 | flat |
| 2026-03-13 | 6 | W11 | flat |
| 2026-03-16 | 10 | W12 | BEAR -1.46% |
| 2026-03-17 | 12 | W12 | BEAR -1.46% |
| 2026-03-27 | 4 | W13 | BEAR -2.88% |

### Distribution by kill zone

| KZ | Count |
|---|---|
| London | 66 (60%) |
| NY | 44 (40%) |

### By week

| Week | Label | Count | % of week's candles |
|---|---|---|---|
| W02 | BULL +1.96% | 32 | 32.0% |
| W03 | flat | 26 | 26.0% |
| W09 | flat | 20 | 20.0% |
| W11 | flat | 6 | 6.0% |
| W12 | BEAR -1.46% | 22 | 22.0% |
| W13 | BEAR -2.88% | 4 | 3.3% |

All other weeks: 0.

### Reading

**No regime-shift clustering.** If "no unmitigated OB" correlated with regime shifts, we'd expect it to spike in W06/W07 (first leg down), W13 (acceleration), or W14/W15 (rally start). Instead the biggest concentrations are in:

- W02-W03 (Jan 5-16): **cold start** — early in the 2026 sample, OB detection is thin because the MSO needs prior structure history to classify OBs.
- W09 (Feb 23-27): a flat consolidation week.
- W11-W12 transition (Mar 13-17): transition from flat into the W12 bearish leg; OBs from earlier bullish consolidation were likely mitigated.

The London vs NY skew (66 vs 44) suggests morning bars are more OB-deprived — possibly because London is where Tokyo-overnight OBs get mitigated at open, leaving no fresh structure. NY sessions get OBs from the London session.

**Confidence: medium.** The cold-start effect is the most obvious pattern. No evidence of "filter weakness during regime shifts" — if anything, W14 (the biggest inflection) had 0 `no_unmitigated_ob` rejects at all. Monitoring this metric in live would be cheap insurance, but no urgent fix indicated.

---

## Q6 — Instrument fitness: is NAS100 a good fit?

### Headline numbers

| Metric | NAS100 (slice) | XAUUSD baseline (CLAUDE.md) | Note |
|---|---|---|---|
| Total candles evaluated | 1,600 | — | |
| Net CANDIDATE rate | 37/1600 = **2.31%** | 10.3% of *evaluated* | 4.5× less selective at net level |
| Post-AI CANDIDATE rate | 37/818 = **4.52%** | 10.3% | ~2.3× less selective |
| WR on filled | 22/33 = **66.7%** | 65% full-pop | **comparable** |
| Avg R on filled | **+0.668R** | +0.200R (367-trade sim) | higher avg (single-TP at 1.5R helps) |
| Sum R | **+22.03R** | — | |

### Pre-AI filter pressure

- `prescreen:L1_*`: 240 records (15.0%) — mostly cold-start (W02 alone had 60 `insufficient_data` rejects).
- `ob_proximity:*`: 542 records (33.9%) — analyzed above as correctly filtering.
- **Combined pre-AI rejects: 48.9%** of all candles. This is the dominant funnel.

After pre-AI, 818 candles reach AI, and of those:
- 37 CANDIDATE (4.5%)
- 84 REJECTED_L2 (10.3%) — L2 geometry check after AI approved
- 82 BLOCKED_LIMIT (10.0%) — max_kz_trades / max_daily hit (a symptom of clustering, not fitness)
- 613 AI NO_TRADE (74.9%) — most are C1/C2 FAIL or "gates pass but price too far from OB"

### Hypotheses

**(a) NAS100 has fewer clean OB setups than gold.**
- Partial support: 110 `no_unmitigated_ob` shows OB availability does occasionally collapse to zero.
- Weak support overall: 432 `price_far_from_ob` records had OBs available, just out of reach (wider ranges). The OBs exist; they're just not being retested as often on M15 scale.

**(b) The AI prompt wasn't tuned for NAS100.**
- This run used `claude-opus-4-5`, not production `claude-sonnet-4-6`. The B_ai_notrade report documents Opus produces ~half Sonnet's CANDIDATE rate on MSO gate. **If you scale Opus 4.5% → expected Sonnet 9-11%, NAS100 post-AI CR would be in line with XAUUSD baseline.** This is the largest single explanatory factor.
- NAS100-specific prompt tuning wasn't done (XAUUSD is the primary instrument). No direct evidence of prompt mismatch beyond direction asymmetry discussed in Q2.

**(c) The proximity filter is too strict on NAS100's wider ranges.**
- Evidence against: Q4 lookahead shows 98.6% of 2h gaps don't get filled. The filter is geometrically correct.
- Evidence for: at 1.0% tolerance on NAS100 (~250 points), many legitimate swing setups fall outside the window. But raising tolerance would duplicate the AI's own post-gate proximity check (which itself accounts for 231/613 = 37.7% of AI NO_TRADEs — see B_ai_notrade).

### Dominant explanation

**Most of the CR gap is (b): Opus evaluator under-producing.** Rerun on Sonnet is the single highest-leverage action. Secondary contributors: (a) NAS100's wider ranges do make price-at-OB moments rarer (median reject distance 1.6% = ~400 points).

### Net judgment

NAS100's **66.7% WR + 0.668R/filled is comparable to XAUUSD** on this sample. The low CANDIDATE production (37 CANDs over 3.5 months = ~10.6 trades/mo) is largely driven by the evaluator and filter funnel, not by NAS100 being a bad fit. Before gating live, the highest-value action is a Sonnet rerun on the same 1600-candle slice to re-measure both CR and direction asymmetry.

**Confidence: medium.** n=33 filled is not enough for instrument-fitness significance (a Binomial(33, 0.5) → 66.7% has p ≈ 0.04 vs breakeven, not Bonferroni-safe). But the trend is "at least as good as gold on WR, half the CR throughput — likely Opus, not instrument."

---

## Open questions for reviewer

1. **Should we rerun this on Sonnet-4.6 before the gate-live decision?** The B_ai_notrade report flags the Opus-vs-Sonnet mismatch. If CR materially shifts (to ~9-11%), the direction-asymmetry story may also change — Sonnet may be more willing to produce SHORT CANDIDATEs on the same D1-bearish weeks (W13 had 55 bearish-bias evaluations but only 1 CAND; Sonnet might give more).
2. **Is the D1-bias source signal overly-lagged during regime inflections?** W14 had NAS100 rallying +4.20% but all D1 bias computations said bearish. This is a mechanical artifact of D1 needing multi-day BOS confirmation. Would an H4-primary bias (with D1 as confirmation) respond faster without losing the no-trade-against-higher-tf safety property? This is outside the current scope but would change the direction-bias story materially.
3. **Should the proximity tolerance be recalibrated per instrument?** NAS100's 0.01 = ~250 points is geometrically equivalent to XAUUSD's 0.01 = ~$20 at $2000 gold. Yet XAUUSD CR is 10.3%. Is this parity appropriate, or is NAS100 noise scale such that 1.5% would be a better cut? Data argues "no change needed," but a direct instrument-calibrated sweep would confirm.
4. **The 82 BLOCKED_LIMIT records** (max_kz_trades + max_daily_trades_sim) are expected behavior but signal the system is generating multiple valid setups per KZ on volatile days. Is the "1 per KZ" rule the right cap for NAS100, or is NAS100's NY session generating enough sequential valid signals that a "2 per KZ with fresh setup" relaxation would be +EV? Requires looking at the 39+21 KZ-blocked records and measuring how many would have hit +1.5R.
5. **The 4 UNFILLED CANDIDATEs (Apr 13 × 2, Apr 14, Apr 16)** all had entries far below current price (W16 runaway rally). Should the simulation track "CANDIDATE issued but price never returned" as a separate category from filled trades? Currently they contribute 0R to the headline but aren't counted as losses. In live this would be pending limit orders expiring.

---

_Data integrity note: all record counts are derived programmatically from the 5 slice JSONs. The `prescreen` / `ob_proximity:*` / AI NO_TRADE segmentation totals to 240 + 542 + 613 = 1395, matching the NO_TRADE count exactly. CANDIDATE 37 + REJECTED_L2 84 + BLOCKED_LIMIT 82 + PARSE_ERROR 2 + NO_TRADE 1395 = 1600, matching the total. No records were double-counted or dropped._
