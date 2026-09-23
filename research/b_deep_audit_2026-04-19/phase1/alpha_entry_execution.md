# Phase 1 — Alpha: Entry Mechanics + Execution Audit

**Agent:** Alpha
**Date:** 2026-04-19 (Session 35, Phase 1)
**Mission:** Quantify R leakage from entry slippage, bit-exact SL touches ("becoming liquidity"), BE stop-outs, and partial-close timing. Show whether each is growing quarter-over-quarter.

---

## TL;DR verdict (ranked by estimated R impact / quarter)

| # | Leak | Est. R impact / quarter | Evidence strength | Fix difficulty | Survives n≥20? |
|---|------|-------------------------|-------------------|----------------|-----------------|
| 1 | **"Bad-entry" rate on XAUUSD almost doubled post-2025-Q3** (26% → 50% of losses never went into profit, mfe<0.2R) | −2 to −4R per quarter at batch n=33, scales to live | MEDIUM — n=65 pre vs 56 post trades in batch; p=0.13 (not Bonferroni-safe) | Prompt-level entry-point correction; M15 pre-check | **Yes on XAUUSD** (n=39 losses combined); **no** at split level |
| 2 | **No partial-close = leaking +0.128R/trade** on Variant C 33%@1R (sign-test p=0.23) | +0.13R × ~17 trades/mo = +2.2R/month ≈ +6.6R/quarter if adopted | MEDIUM — n=45 shadow records, rescues 9/9 losing trades; sign test NOT significant | Deterministic 1-line execution change | n=45 → OK for direction; combined test p=0.23 not Bonferroni-safe |
| 3 | **NAS100 loss-MFE median 1.66R = liquidity-hunt pattern** (losses go deep into profit then reverse to SL) | ≥ +11R/quarter if switched to aggressive partial or 0.5R move-to-BE trigger | MEDIUM — n=11 losses at NAS100 2026-Q1; 10/11 losses had mfe≥0.5R, 9/11 had mfe≥1R | Prompt + execution rule change; needs NAS100 live | **Yes for directional**; n=11 borderline for hard claim |
| 4 | **BE-stop counterfactual: 9/9 shadow losses are "reversed-past-entry" trades** — would be saved by Variant C's 33%@1R fixed partial | +1.23R per rescued loss × ~3-5 rescues/quarter = +4 to +6R/quarter | MEDIUM — n=9 in shadow, 100% hit rate on rescue; but n<30 = exploratory | Adopt Variant C | Exploratory (n=9) |
| 5 | **"Bit-exact SL touch + ≥1R reversal" (pure liquidity-hunt signature): 0 / 16 losses** (0%) — signature not present in this dataset | 0R — hypothesis NOT supported by XAUUSD/NAS100/EURUSD losses | **Low** — n=16 losses, 0 signature hits; 2 bit-exact but no reversal, or reversal but no bit-exact | N/A | n=16 → exploratory; null finding |
| 6 | **Fill slippage: UNMEASURABLE from existing data** — T7 sim has no slippage model (fill AT `entry_price`); live has 0 filled trades since 2026-04-07 | Cannot be scored; must re-measure after redacted_account Tuesday | **n=0 fills** on live | Pending redacted_account data collection | N/A |

**Primary actionable finding:** XAUUSD entry-quality degradation is the largest measurable leak (Q-over-Q "bad-entry" rate doubled). Variant C partial-close is a cheap +0.1-0.3R/trade rescue mechanism with moderate evidence. The "we are the liquidity" thesis is **NOT supported** by losses in this data — only 0/16 show the bit-exact wick + reversal signature. What NAS100 losses DO show is a "went in profit, then reversed" pattern — a different failure mode (deep MFE on losses = TP too far / no partial).

---

## 1. Fill slippage distribution — NOT MEASURABLE

### Method
Sought `(actual_entry − intended_entry)` across all filled trades, by instrument and session.

### Findings

**Fill slippage cannot be measured from existing data.** Two independent reasons:

1. **Live has produced 0 filled trades since 2026-04-07.** All `knowledge_base/sessions/2026-04-*_live_session.json` show `trades_today: 0` (verified 11 session files). Every `knowledge_base/trade_records/{XAUUSD,USDJPY,US30_cash,GBPJPY,GBPUSD}/*.json` has `"execution": null` and `"exit": null` (92 files checked). No `shadow_logs/be_shadow_log.jsonl` exists — the BE shadow tracker fires only on live fill, and nothing has fired.
   - Evidence: `knowledge_base/sessions/2026-04-17_live_session.json:trades_today=0` and peers.
   - Evidence: `knowledge_base/trade_records/XAUUSD/2026-04-17_ny_1345.json` top-level `execution: None`.

2. **T7 simulator fills exactly at `entry_price`** (no slippage model). See `scripts/simulate_t7_live_period.py:539-549` — once `low <= entry` (LONG limit) or `high >= entry` (stop), the trade fills AT `entry`. There is also no spread model. Per-instrument `_FILL_EPSILON` (session 35 Tier A1) handles close≈entry "at-market" semantics but still applies zero slippage to subsequent fills.

### SL-distance distribution (proxy for fill-geometry risk)

Since slippage is 0 in sim and N/A in live, the meaningful intended-fill-geometry measure is |entry − SL|:

| Symbol | n | median | mean | p05 | p95 |
|---|---:|---:|---:|---:|---:|
| XAUUSD | 10 | 23.17 | 27.73 | 9.50 | 79.06 |
| NAS100 | 37 | 87.50 | 96.71 | 30.00 | 240.00 |
| EURUSD | 9  | 0.0003 | 0.0021 | 0.0000 | 0.0100 |

Evidence: `research/t7_live_simulation/all_results_jan_apr10.json` + NAS100 slices 1-5 + EURUSD `t7_simulation.json`. Calculation script: `_alpha_scratch/slippage_analysis.py`. EURUSD distances suspect — see `EURUSD_epsilon_revalidation.md`: 4/9 CANDIDATEs are degenerate (entry=SL=TP), so the genuine n is 5 and numbers are epsilon-contaminated.

### Status
- **DIRECTIONAL / NULL**: cannot measure; live slippage must be captured post-Tuesday redacted_account.
- **Direction for Phase 4:** slippage is an **unknown unknown** for live. Agent βη recommend logging every fill with `(intended_entry, fill_price, slippage_ticks, spread_at_fill)` on first live trade Tuesday.
- **Code hook exists:** `src/models/trade_models.py:151-153` defines `fill_price`, `slippage_cents`, `spread_at_entry` — these need to actually be populated by `execution.py` on fill.

---

## 2. Bit-exact SL-touch signature ("we are the liquidity")

### Method
For every filled losing trade in the three T7 simulations (XAUUSD/NAS100/EURUSD), walked M15 forward from `candle_time`, found the SL-hit candle, measured:

1. **Touch distance** = |SL − candle.low| (LONG) or |candle.high − SL| (SHORT)
2. **Bit-exact STRICT** = touch_distance ≤ 2 ticks
3. **Bit-exact LIQ** = touch_distance ≤ 1-2 pips (XAUUSD 0.20 pts, NAS100 2.0 pts, EURUSD 0.00020 — matches session 35 Tier A1 epsilon table)
4. **Reversed ≥1R within 4h** = within 16 subsequent M15 candles, did price trade back past `entry` (toward TP)?
5. **Liquidity-hunt signature** = bit-exact AND reversed

### Raw findings

n=16 losing CANDIDATEs total (XAUUSD=4, NAS100=11, EURUSD=1).

| Symbol | n_loss | bit_exact_strict (2-tick) | bit_exact_liq (~1-2 pip) | reversed≥1R/4h | signature_liq |
|---|---:|---:|---:|---:|---:|
| XAUUSD | 4  | 0 | 0 | **4 (100%)** | **0** |
| NAS100 | 11 | 1 | 1 | 5 (45%) | 0 |
| EURUSD | 1  | 1 | 1 | 0 | 0 |
| **Total** | **16** | **2** | **2** | **9** | **0** |

### Per-loss detail (sorted by touch distance as fraction of SL distance)

| Symbol | Candle time | Dir | touch_d / R | reverse_R | Interpretation |
|---|---|---|---:|---:|---|
| NAS100 | 2026-01-20 09:45 | LONG | 0.65% | 0.20R | Bit-exact but NO reversal (failed to recover) |
| EURUSD | 2026-02-23 08:15 | LONG | 1.90% | 0.47R | Near bit-exact, weak reversal (<1R) |
| XAUUSD | 2026-03-10 16:00 | LONG | 4.27% | 1.47R | NEAR-bit-exact, strong reversal — only partial liq-signature |
| NAS100 | 2026-04-16 09:00 | LONG | 8.10% | 1.68R | Near bit-exact, strong reversal |
| NAS100 | 2026-03-17 15:00 | LONG | 15.57% | 0.29R | Typical sweep loss (no reversal) |
| NAS100 | 2026-03-13 14:00 | LONG | 32.35% | 0.95R | SL penetrated; partial reversal (<1R) |
| XAUUSD | 2026-02-20 15:00 | LONG | 45.29% | 1.95R | SL hard hit then bounced 2R |
| XAUUSD | 2026-01-15 13:15 | LONG | 45.46% | 1.26R | SL hard hit then bounced 1.26R |
| NAS100 | 2026-02-26 08:45 | LONG | 89.82% | 1.71R | Deep penetration, bounced 1.71R |
| XAUUSD | 2026-01-21 15:00 | LONG | 111.59% | 1.84R | Deep news-like flush then bounce |
| NAS100 | 2026-02-12 13:30 | LONG | 129.91% | 0.39R | Deep flush, no recovery |
| NAS100 | 2026-03-04 14:00 | LONG | 139.06% | 0.00R | Deep flush, sustained trend against |
| NAS100 | 2026-03-18 09:00 | LONG | 254.76% | 1.03R | Deep flush, bounced 1R |
| NAS100 | 2026-03-18 13:30 | LONG | 188.05% | 1.03R | Same day — double-stop |
| NAS100 | 2026-04-10 15:00 | LONG | 252.81% | 0.00R | Deep flush, sustained trend against |
| NAS100 | 2026-03-23 09:30 | SHORT | 832.91% | 1.79R | MASSIVE flush then bounce — news event |

Evidence: `_alpha_scratch/slippage_analysis.py` Section 2 output; underlying records in `research/t7_live_simulation/all_results_jan_apr10.json` + NAS100 slices + EURUSD sim.

### Quarterly evolution (2026 only — older T7 sim data not available)

| Quarter | n_losses | bit_exact_liq | reversed≥1R | signature_liq |
|---|---:|---:|---:|---:|
| 2026Q1 | 14 | 2 | 8 (57%) | 0 |
| 2026Q2 | 2  | 0 | 1 | 0 |

**Important caveat:** 2026Q2 is only 2 weeks of data. XAUUSD T7 sim doesn't extend beyond 2026-04-10; NAS100 covers through 2026-04-17. Cannot do meaningful Q-over-Q comparison with this dataset — **batch KB has no entry/SL prices, only MFE/MAE R-relative, so cannot rerun this analysis on Q1-2024 / Q3-2025 to test "growing over time."**

### Interpretation

**"We are the liquidity" thesis is NOT supported in this dataset.**
- Only 0/16 losses match the strict signature (bit-exact wick + 1R reversal).
- Of the 16 losses, 9 did reverse ≥1R within 4h — but **only 2 had bit-exact wicks**, and those 2 did NOT reverse.
- The 9 reversals had wicks averaging 100%+ penetration past SL = **not liquidity hunts, but real impulse moves that overshot**.

**Counter-hypothesis now stronger:** SL placement is too tight/too far from structure, causing mid-session whipsaws NOT institutional liquidity harvesting. Confirmed by:
- XAUUSD 4/4 losses reversed after SL hit with penetration 1.63–16.04 points (mean 10.7pt).
- XAUUSD typical R-distance is 23pt median (from Section 1). So price penetrated ~40-50% of another R before reversing — looks more like "normal overshoot inside volatility" than "stop-hunt surgical wick."

### Status
- **MEDIUM-to-NULL claim** (n=16 losses): liquidity-hunt signature not present. Direction-only finding.
- **Alternative pattern detected:** XAUUSD 100% of losses reversed ≥1R within 4h. This suggests SL distance too tight relative to XAUUSD intra-session noise, not algo-arbitrage.
- **Recommendation:** ε agent should cross-check this by extending to OLDER quarters where batch data has SL/entry prices recoverable from `knowledge_base_backtest/batch_api/responses/XAUUSD/*.json` (has `trade_parameters.stop_loss/entry_price`). Session 35 Tier B1 eta agent may already cover this.

---

## 3. BE-stopped counterfactual

### Method
Live BE rule is: **at kill-zone end, if in profit, move SL to entry** (`src/components/execution.py:880-907`). NOT triggered at +1R — the BE shadow logger at `src/components/be_shadow_logger.py` is a separate observation-only simulator for a hypothetical +1R trigger.

Because live BE rule is KZ-end only, and because live has produced 0 filled trades since Apr 7, we cannot directly measure BE-stopped counterfactual losses. Instead, two proxies:

**Proxy A — batch KB MFE:** flag trades with `mfe_r ≥ BE_TRIGGER` AND final `−0.1 < r < 0.2` (consistent with BE retrace stop-out). Across XAUUSD batch (n=121 trades):
- BE-trigger 0.5R proxy: 12 candidates, **0 reached mfe≥1.5R**, sum actual R = +1.29
- BE-trigger 0.8R proxy: 4 candidates, **0 reached mfe≥1.5R**, sum actual R = +0.32
- BE-trigger 1.0R proxy: 2 candidates, **0 reached mfe≥1.5R**, sum actual R = +0.09

**Proxy B — partial_close shadow log:** looked at 9 `reversed_past_entry=True` records in `shadow_logs/partial_close_backtest.jsonl`:
- These are trades where mfe ≥ 1.0R, then price came back past entry → **BE stop would have triggered**.
- Actual outcome sum: **-8.11R** (8 went to full SL -1R, 1 went to -0.11R).
- Variant C 33%@1R sum: **+2.97R** (locked in 0.33R × 9 = +2.97R, no further drawdown from SL because 67% remaining went to full SL -0.67R).
- **Net benefit of Variant C over actual: +11.08R across 9 rescues.**

### BE-trigger at +0.5R / +0.8R / +1.0R — counterfactual delta

| BE trigger (MFE threshold) | n_rescued | Counterfactual if NO BE | Actual with BE-stop proxy | Delta if BE eliminated |
|---|---:|---|---|---|
| 0.5R | 12 | if these would have hit -1R instead of +0.13 sum: **net -13.3R** | +1.29R | BE actually SAVES ~13R — KEEP BE |
| 0.8R | 4 | hypothetical -1R × 4 + -0.32 actual → **net -4.3R** | +0.32R | KEEP |
| 1.0R | 2 | -2R − 0.09 actual → **net -2.1R** | +0.09R | KEEP |

### Interpretation
The batch KB proxy suggests the **current live BE rule (KZ-end + in-profit only) is a weak positive** — the rescued trades DIDN'T have high mfe ceilings, so letting them run to SL would have lost more than the BE-stop captures.

However, **the `partial_close_backtest.jsonl` shadow tells a different story for higher-MFE trades**: 9 records with mfe ≥ 1.2R that reversed past entry — had we closed 33% at +1R (not moved SL to BE), we would have gained +2.97R locked versus BE stop-out which left us near zero.

**The right answer is not "kill BE" but "add fixed partial close at +1R before BE considerations"** — Variant C 33%@1R.

### Status
- **EXPLORATORY on BE-elimination alone (n=9 in shadow log).**
- **DIRECTIONAL POSITIVE for Variant C adoption (n=45 combined; 9/9 rescues).**
- Cannot hard-claim until n≥30 full Variant-C-eligible events in shadow log.

---

## 4. Partial-close Variant C (33% @ 1R) vs baseline

### Data sources
- `shadow_logs/partial_close_backtest.jsonl` (n=45: 36 approx + 9 exact_r_path)
- `shadow_logs/partial_close_backtest_exact_only.jsonl` (n=11 strict-match subset)

### Full dataset (n=45, approx+exact)

| Metric | Baseline (no partial) | Variant C (33%@1R) | Δ |
|---|---:|---:|---:|
| sumR | 44.02 | 49.78 | **+5.76R** |
| meanR | 0.978 | 1.106 | **+0.128R/trade** |

**Wins (n=36):** baseline mean 1.448, VC mean 1.300, delta **-0.148R** (VC caps winners slightly)
**Losses (n=9):** baseline mean -0.901, VC mean +0.330, delta **+1.231R** (VC rescues every single loss that gained ≥1R first)

### Sign test (H0: median delta = 0)
- pos=27, neg=18, zero=0
- Two-sided binomial p = **0.2327** — not significant at α=0.05, **not** Bonferroni-safe at α=0.00625.
- Claim is DIRECTIONAL at n=45.

### Exact_only subset (n=11, EXPLORATORY — n<20)

| Metric | Baseline | Variant C | Δ |
|---|---:|---:|---:|
| sumR | 7.89 | 11.60 | +3.71R |
| meanR | 0.717 | 1.054 | +0.337R/trade |

Sign test p=1.00 (pos=6, neg=5) — **no signal at exact-only n=11.**

### Interpretation

Variant C at n=45 shows **+0.13R/trade mean improvement**. Not statistically significant. The mechanism is clear: 9 losing trades that went ≥1R in profit then reversed → VC captures 0.33R on partial, 67% remaining position goes to -0.67R, net -0.34R instead of -1.00R. That's +0.66R per rescued loss × 9 = +5.94R locked in.

**Caveats:**
- Sign test p=0.23 is weak; combined test not robust.
- Wins suffer slightly (winners cut by 0.15R mean) — acceptable given loss-rescue magnitude.
- All 9 losses are rescued — this is a deterministic +R if event occurs.

**Expected contribution if live production:** at ~17 trades/month expected frequency, mean +0.128R/trade = **+2.2R/month = +6.6R/quarter** IF the ratio of "reversed-past-entry" trades holds in live (~20% of wins in this dataset became "reversed-past-entry" pattern).

### Status
- **MEDIUM directional evidence at n=45.**
- n=30+ required for hard claim with sign-test alone; p=0.23 is not Bonferroni-safe. Exploratory at best.
- **Recommendation:** adopt Variant C under CEO-approval gate as a low-downside, moderate-upside execution change. Maintain shadow logger to continue collecting data.

---

## 5. Quarterly evolution of entry quality

### XAUUSD batch KB (n=121 trades, 2024-Q2 through 2026-Q1)

| Quarter | n | W | WR% | sumR | expR | mfe_median | bad_entry%/loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024Q2 | 8 | 6 | 75.0 | 3.30 | 0.412 | 0.880 | 50.0 (n=2) |
| 2024Q3 | 10 | 8 | 80.0 | 6.55 | 0.655 | 1.515 | 50.0 (n=2) |
| 2024Q4 | 6 | 3 | 50.0 | 1.75 | 0.292 | 0.783 | 0.0 (n=3) |
| 2025Q1 | 34 | 23 | 67.6 | 5.71 | 0.168 | 0.454 | 30.0 (n=10) |
| 2025Q2 | 7 | 5 | 71.4 | 5.74 | 0.820 | 1.206 | 0.0 (n=2) |
| 2025Q3 | 7 | 4 | 57.1 | 1.72 | 0.246 | 0.717 | 66.7 (n=3) |
| 2025Q4 | 16 | 11 | 68.8 | 6.24 | 0.390 | 0.764 | 0.0 (n=4) |
| **2026Q1** | **33** | **20** | **60.6** | **5.22** | **0.158** | **0.231** | **61.5 (n=13)** |

Evidence: `knowledge_base_backtest/sessions/XAUUSD/*.json` (318 files, 121 XAUUSD trades with dates).

### Pre-decay vs post-decay "bad entry" rate (H2-2025+ cutoff)

**"Bad entry" definition:** loss where mfe_r < 0.2R (trade never went meaningfully into profit).

| Era | Trades | Losses | Bad-entry losses | % of losses |
|---|---:|---:|---:|---:|
| Pre-decay (≤ 2025-06-30) | 65 | 19 | 5 | **26.3%** |
| Post-decay (≥ 2025-07-01) | 56 | 20 | 10 | **50.0%** |

Two-proportion z-test: z=1.52, **p=0.1286** (not significant at α=0.05, not Bonferroni-safe).

### Quarter-over-quarter bad-entry evolution (the key signal)

| Q | bad-entry % of losses | n losses |
|---|---:|---:|
| 2024Q2-2025Q2 (combined) | 26.3% | 19 |
| 2025Q3 | 66.7% | 3 |
| 2025Q4 | 0.0% | 4 |
| **2026Q1** | **61.5%** | **13** |

### Interpretation

**The XAUUSD bad-entry rate doubled between pre- and post-2025-Q3.** In 2026Q1, 8 of 13 losses had MFE < 0.2R — the trade never went into profit before hitting SL. This is the single biggest **entry quality** signal in the dataset.

**Why "entry quality" and not "market noise":**
- Median loss MFE in 2026Q1 is 0.106R (across 13 losses) — less than 1/9 the 2025Q2 median (0.820R).
- Median MAE across ALL 2026Q1 trades is 0.374R — higher than 2025Q1 0.247 and 2024Q3 0.385.
- Pattern: entries go immediately against us, penetrate 1/3 of SL distance on first adverse, then revert is insufficient.

**This is consistent with "AI is placing limit entries too close to tops of ranges / bottoms of rallies"** — picking knives rather than fading liquidity sweeps.

**NOT consistent with liquidity-hunt:** liquidity-hunt = price goes in favor, then reverses through our stop. Here, price immediately goes AGAINST us.

### Status
- **MEDIUM on XAUUSD at n=121 overall** (enough for the headline number).
- **Exploratory / directional on Pre-vs-Post z-test** (p=0.13, not Bonferroni-safe).
- **Directionally strong 2026Q1 finding** (8/13 bad entries = 61.5%).
- **Recommendation:** agent β (AI audit) and agent ζ (market state) should cross-check: are 2026Q1 losses concentrated in specific setups (grade, POI type, bias source)?

---

## 6. Cross-instrument loss pattern divergence (exploratory — new finding)

### NAS100 T7 Q1-2026 losses (n=11)

| Metric | Value |
|---|---|
| Loss MFE median | **1.66R** (losses go DEEP into profit before reversing) |
| Loss MFE mean | 1.92R |
| Individual loss MFEs | [0, 0.57, 1.82, 1.71, 1.66, 1.62, 5.60, 3.90, 1.97, 0.94, 1.39] |
| Losses with mfe ≥ 0.5R | 10 / 11 (91%) |
| Losses with mfe ≥ 1.0R | 9 / 11 (82%) |
| Losses with mfe ≥ 1.5R | 6 / 11 (55%) |
| Bad-entry (mfe < 0.2R) | 1 / 11 (9%) |

### XAUUSD T7 Q1-2026 losses (n=4)

| Metric | Value |
|---|---|
| Loss MFE median | 0.724R |
| Loss MFE mean | 0.655R |
| Individual loss MFEs | [0.182, 0.840, 0.607, 0.991] |
| Losses with mfe ≥ 0.5R | 3 / 4 |
| Bad-entry (mfe < 0.2R) | 1 / 4 |

### XAUUSD batch Q1-2026 losses (n=13, older pipeline)

| Metric | Value |
|---|---|
| Loss MFE median | 0.106R |
| Bad-entry (mfe < 0.2R) | 8 / 13 (61.5%) |

### Interpretation

**Two completely different failure modes:**

1. **NAS100 losses = "deep MFE then reversal"** (9/11 had mfe≥1R). This is the pattern Variant C rescues most effectively. It is consistent with either:
   - NAS100 being heavily algo-traded (trades go sufficiently in profit to attract algo fades),
   - OR NAS100's impulsive nature favoring trend reversal around session extremes,
   - OR TP being too ambitious (set at ~1.5R = 1R beyond the natural profit zone).

2. **XAUUSD losses = "bad from the start"** (especially in batch 2026Q1, 61.5% never went profitable). Inconsistent with liquidity-hunt; consistent with degrading entry-point quality (AI mis-identifying OB or POI level).

3. **Contrast between XAUUSD T7 sim (loss mfe 0.72R) and XAUUSD batch (0.106R) in same quarter** suggests the new AI pipeline (Sonnet 4.6, effort=max) produces meaningfully better entries — AI-level change from the old debate pipeline. But **only n=4 T7 losses** — exploratory.

### Status — EXPLORATORY
- n=11 for NAS100, n=4 for XAUUSD T7, n=13 for XAUUSD batch 2026Q1.
- **Cross-instrument failure-mode divergence** is the biggest surprise of this audit but requires replication with more data.

---

## 7. What cannot be answered with this dataset

1. **Fill slippage on live instruments** — 0 filled trades since Apr 7. Action: instrument `execution.py` to populate `fill_price` / `slippage_cents` / `spread_at_entry` (model slots exist, code doesn't write them).
2. **Q-over-Q evolution of fill-slippage** — cannot compare 2024 vs 2026 fills; no price-level fill data in batch KB.
3. **Bit-exact wick rate for pre-decay quarters on XAUUSD** — batch KB doesn't carry entry/SL prices in trade records. Could be partially recovered from `knowledge_base_backtest/batch_api/responses/XAUUSD/*.json` (has `trade_parameters`), but trade outcomes aren't cross-linked in that file. **~4-6 hours of engineering to recover** if deemed critical.
4. **BE shadow log behavior on live trades** — empty; live has no fills.

---

## 8. Methodology + reproducibility

### Scripts
- `_alpha_scratch/slippage_analysis.py` — primary analysis. Reads:
  - `research/t7_live_simulation/all_results_jan_apr10.json` (XAUUSD, 2100 rec)
  - `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json` (1600 rec)
  - `research/t7_live_simulation/EURUSD_t7_simulation.json` (2280 rec; epsilon-contaminated)
  - `data/historical_2026/{XAUUSD,NAS100,EURUSD}_M15.csv` (forward-price replay)
  - `knowledge_base_backtest/sessions/XAUUSD/*.json` (121 batch trades)
  - `shadow_logs/partial_close_backtest.jsonl` (n=45)
  - `shadow_logs/partial_close_backtest_exact_only.jsonl` (n=11)

### Key assumptions
1. T7 `entry_price` = limit price; fill AT `entry_price` once touched (no slippage, no spread). Confirmed at `scripts/simulate_t7_live_period.py:539-549`.
2. "2-tick" for bit-exact = 2 × `MT5.Symbol.trade_tick_size`. For XAUUSD = 0.02, NAS100 = 2.0, EURUSD = 0.00002.
3. "Liquidity-hunt threshold" = session 35 A1 `_EPSILON_BY_SYMBOL` (2 pips / 1-2 points). More realistic than tick-level.
4. "Reversed ≥1R within 4h" = within 16 M15 candles after SL hit, price touched `entry_price` in the direction opposite to the SL hit.
5. "Bad entry" = loss with mfe_r < 0.2R (proxy for "never meaningfully profitable").

### Bonferroni budget
- 8 parallel Phase 1 agents → α = 0.05 / 8 = 0.00625.
- Tests in this report that would need to pass Bonferroni:
  - Two-proportion z-test on pre-vs-post bad-entry rate: p=0.1286 → **fails** α=0.05, let alone Bonferroni.
  - Sign test on Variant C: p=0.2327 → **fails** α=0.05.
  - All findings in this report should be treated as **directional** evidence, not Bonferroni-safe.

### Claim strength summary
| Claim | n | Evidence strength | Survives Bonferroni? |
|---|---|---|---|
| Liquidity-hunt signature 0/16 | 16 | NULL at small n | N/A (null finding) |
| Variant C +0.128R/trade | 45 | DIRECTIONAL | No (p=0.23) |
| 9/9 rescue rate (VC on reversed_past_entry) | 9 | EXPLORATORY | N/A (descriptive) |
| XAUUSD 2026Q1 61.5% bad-entry | 13 | EXPLORATORY | No |
| XAUUSD pre-vs-post bad-entry 26% → 50% | 65 / 56 | DIRECTIONAL | No (p=0.13) |
| NAS100 loss mfe median 1.66R | 11 | EXPLORATORY | No |

---

## 9. RANKED VERDICT (final)

1. **XAUUSD entry-point quality degradation** (directional, n=121 batch; p=0.13 pre-vs-post)
   - Evidence: 26% → 50% bad-entry rate in losses, 2026Q1 at 61.5%
   - Estimated R impact: **−2 to −4R/quarter** (back-of-envelope: 8 added bad-entry losses × 1R = 8R direct loss; assume only 50% of those would have otherwise won at 1.5R → net 8 × 1.5 = 12R upside lost, minus 8 bad entries avoided = ~-4R)
   - Fix difficulty: **MEDIUM** — requires agent β (AI prompt audit) and/or agent ζ (market-state pre-check audit) to identify specific entry-placement failure. Not a simple execution fix.
   - Confidence: **Medium** — n large enough for directional; p not significant but effect size 2×.

2. **Variant C partial-close adoption** (directional, n=45)
   - Evidence: +0.128R/trade mean across 45 combined shadow records; 9/9 rescue rate on losing "reversed_past_entry" trades.
   - Estimated R impact: **+2 to +7R/quarter** depending on trade frequency and event rate.
   - Fix difficulty: **LOW** — deterministic execution rule (close 33% at +1R). Already scoped.
   - Confidence: **Medium** — sign test p=0.23 not significant; effect is directional with clear mechanism.
   - **Requires CEO approval** (WF-1 execution change).

3. **NAS100 "deep MFE then reversal" failure mode** (exploratory, n=11)
   - Evidence: 9/11 NAS100 losses went ≥1R in profit before reversing to SL.
   - Estimated R impact: if these were partial-closed at +1R: **+9 × 0.33R = +3R locked + reduced full-SL damage**. Conservative estimate **+5-11R/quarter** if NAS100 goes live with Variant C.
   - Fix difficulty: **LOW-MEDIUM** — same Variant C mechanism; NAS100-specific.
   - Confidence: **Exploratory** — n=11 below hard-claim threshold. But directional strong.

4. **Liquidity-hunt thesis NOT supported at strict definition** (null, n=16)
   - Evidence: 0/16 losses fit bit-exact wick + 1R reversal pattern.
   - Counter-finding: 4/4 XAUUSD losses reversed 1R+ after SL penetration of 1.6-16pt (not bit-exact). Consistent with "SL placement or TP extent mismatch with volatility" rather than algo arbitrage.
   - Fix difficulty: N/A — null finding.
   - Confidence: **Directional NULL** — n=16 too small for definitive. Agent ε replication on older data would raise confidence either direction.

5. **Fill-slippage measurement infrastructure gap** (operational, not a leak per se)
   - `src/models/trade_models.py:151-153` defines `fill_price`, `slippage_cents`, `spread_at_entry` — but `execution.py` never writes them.
   - Action: add logging hook on first live fill Tuesday. Low effort.
   - This doesn't produce R impact directly but is a blocker for future slippage analysis.

---

## 10. Handoffs to other Phase 1 agents

- **Agent β (AI integrity):** Are 2026Q1 bad-entry losses concentrated by `setup_grade`, `bias_source`, or POI type? We have the 13 losing XAUUSD trades — cross-reference the decisions file to check if `setup_grade=A+` bad-entry rate differs from `A`.
- **Agent γ (missed trades):** Opportunity cost of the 33% of 2026Q1 CANDIDATEs that hit SL immediately — would L2 `entry_in_ob` or similar gate have caught them?
- **Agent δ (regime decay):** XAUUSD batch 2025Q2 WR=71.4% and loss mfe_median=1.206 both strong → 2026Q1 WR=60.6% and loss mfe_median=0.231 collapsed. Is this a volatility-regime shift or a pipeline change?
- **Agent ε (liquidity arb):** I find 0/16 bit-exact signature. Replicate on batch-era data where entry/SL prices recoverable from batch_api responses to raise n → 50+. XAUUSD pre-2025 should have distinct pre-AI-saturation baseline.
- **Agent ζ (market state pre-check):** The 61.5% bad-entry rate in 2026Q1 XAUUSD batch — are these setups where OB proximity was too tight (we entered at retest top)?

---

## Exit

Primary finding: **XAUUSD entry-point quality has degraded**, and the evidence is directionally strong though statistically borderline. Secondary finding: **Variant C (33%@1R) is worth adopting** with medium evidence. Null finding: **liquidity-hunt signature is not present** in the current data at the strict definition. Blocker for follow-up: **live execution has produced no fills since Apr 7** — redacted_account Tuesday will start the first real slippage-measurement corpus.

Sign-off: Agent α, 2026-04-19.
