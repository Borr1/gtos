# LIVE-EXPECTATIONS DOSSIER — clean_3 deploy book

**What this is.** The concrete numbers the owner should expect if the **clean_3** deploy book had
traded an FTMO-style challenge account over the historical/replay window. Net of realistic M1 fills
(KB3 per-sleeve R erosion). Returns/dollars/frequency/duration computed directly from the per-day R
streams + trade ledgers; challenge pass-economics from the LOCKED W2 Monte-Carlo engine
(8% target / 5% daily DD / 10% max DD / N=20,000 / block-bootstrap whole cross-sectional days).

**Doctrine headline.** *The forward window (2025-01 -> 2026-06) is the honest out-of-sample
estimate — lead with it.* Full-history 2015-26 is shown for context but is **lumpy**: the deep H4
sleeves are sparse pre-2024 and the substrate/VP layers are essentially forward-only (M1-since-2024).
Per-year is never blended into a single verdict. Sample sizes are stated everywhere. This is
**replay, not live**.

Book composition (11 sleeves, confidence-weighted): metals_core (1.00), crypto (0.85),
energy_agri (0.80), metals_softband (0.50), metals_ob_micro (0.30), idxrev (0.15), fx_jpy (0.15),
fx_jpy_ny (0.15), **sub_xvol_pullback (0.45), vp_euidx_pocgrav (0.30), sub_mid_dn_revert (0.20)**.
Combined daily mean **+0.0852 unit-R net** (all), **+0.187 unit-R net** forward; daily std 0.597;
win-days 49.9%; 1,679 active book-days all / 382 forward.

"Per unit" = % of account risked per correlated risk-unit (one diversified book-day of exposure).
All dollar figures scale **linearly** with account size (a $200k account doubles every dollar below).

---

## 1. RETURNS (compounded daily equity, net of fills)

### FORWARD 2025-26 — the honest live estimate (382 trading days, 2025-01-02 -> 2026-06-12)

| metric | @ 0.50%/unit | @ 0.75%/unit |
|---|---|---|
| **2025 account return** | **+34.8%** | **+56.0%** |
| **2026 account return (partial, to Jun)** | **+22.2%** | **+35.0%** |
| forward-window total (compounded, continuous) | +64.7% | +110.6% |
| forward annualized | +41.4% | +67.7% |
| forward daily mean | +0.132% | +0.198% |
| forward daily std | 0.503% | 0.754% |
| forward % positive days | 55.8% | 55.8% |
| forward best / worst day | +2.54% / -1.02% | +3.81% / -1.53% |
| **forward max drawdown** | **-2.94%** | **-4.39%** |

### FULL HISTORY 2015-26 — context only (lumpy; read per-year, not blended)

Per-year account % (equity reset each Jan), @ 0.50% / @ 0.75%:

| year | 0.50% | 0.75% | note |
|---|---|---|---|
| 2015 | +0.9% | +1.3% | metals-only era, sparse |
| 2016 | -0.4% | -0.7% | only losing year |
| 2017 | +0.8% | +1.2% | |
| 2018 | +1.7% | +2.5% | |
| 2019 | +1.6% | +2.4% | |
| 2020 | +1.6% | +2.4% | |
| 2021 | +5.5% | +8.4% | energy/index breadth comes online |
| 2022 | +1.7% | +2.6% | |
| 2023 | +0.2% | +0.3% | flattest year |
| 2024 | +7.8% | +11.8% | crypto cascade + substrate ramp |
| **2025** | **+34.8%** | **+56.0%** | forward |
| **2026** | **+22.2%** | **+35.0%** | forward (partial) |

- Whole-timeline mean monthly: **+0.60%** (0.50%) / **+0.91%** (0.75%); median monthly +0.19% / +0.28%
  over 120 months. The mean >> median: returns are **right-skewed and regime-lumpy** — a handful of
  hot months (crypto/energy clusters) carry the average. Plan for the median in a quiet month.
- Whole-timeline daily: mean +0.043% / +0.064%, std 0.299% / 0.448%, positive days 49.9%,
  best +2.54% / +3.81%, worst -1.02% / -1.53%. **Max drawdown 3.84% (0.50%) / 5.71% (0.75%)**.

> The 2015-23 years are thin (the deep sleeves trade rarely and the substrate/VP layers did not exist
> yet). The forward years are far hotter — partly genuine edge, partly the easiest regime in the
> sample. **Do not annualize off 2025-26 alone.** The honest forward-annualized band is roughly
> **+20% to +45% at 0.50%/unit** once you discount the 2025 cluster.

---

## 2. DOLLARS — per $100,000 challenge account (scales linearly)

| metric | @ 0.50%/unit | @ 0.75%/unit |
|---|---|---|
| expected **$/month** (forward mean-monthly) | **$603** | **$910** |
| total $ over the forward window (18mo replay) | $64,690 | $110,560 |
| forward-annualized $ | ~$41,400 | ~$67,700 |
| $ needed to pass the +8% target | $8,000 | $8,000 |
| expected days to reach +8% (forward MC median) | **55 days** | **37 days** |
| **funded $/month after passing (80% trader split)** | **$482** | **$728** |

Reading: at the recommended **0.75%/unit** balanced size, a $100k account expects roughly **$900/mo**
gross in the live (forward) regime, clears the $8k profit target in a **median ~37 trading days**, and
once funded throws off about **$728/mo to the trader** (80% of $910) per $100k of funded capital. On a
$200k account double everything; on $50k halve it. The median month is leaner ($188-$282/$100k) — the
average is pulled up by hot clusters.

---

## 3. FREQUENCY & DURATION

### Frequency (forward rate)

- **Whole book: ~2,650 trades/year ≈ 51/week ≈ 10.5/trading-day** (all-history rate ~1,904/yr).
- This count is **dominated by tiny-confidence breadth**: idxrev alone ~1,407/yr (53% of all trades)
  and the JPY pair ~716/yr (27%), both at conf 0.15. The **EV-carriers trade far less often**:
  crypto ~62/yr, energy ~82/yr, metals_core ~38/yr, sub_xvol ~54/yr.
- (The PORTFOLIO_BUILD_W5.md headline of ~1,717 tr/yr is a more conservative count of the risk-banked
  set; the ~2,650 here is the literal forward stream count of every deployed sleeve. Both are correct
  at different definitions — the breadth sleeves are real fills but each carries ~conf-0.15 size.)

| sleeve | conf | trades/yr (fwd) | /week | /day | share of count |
|---|---|---|---|---|---|
| idxrev | 0.15 | 1,407 | 27.1 | 5.58 | 53.1% |
| fx_jpy (London) | 0.15 | 520 | 10.0 | 2.07 | 19.6% |
| fx_jpy_ny | 0.15 | 196 | 3.8 | 0.78 | 7.4% |
| vp_euidx_pocgrav | 0.30 | 160 | 3.1 | 0.63 | 6.0% |
| sub_mid_dn_revert | 0.20 | 94 | 1.8 | 0.37 | 3.5% |
| energy_agri | 0.80 | 82 | 1.6 | 0.33 | 3.1% |
| crypto | 0.85 | 62 | 1.2 | 0.25 | 2.3% |
| sub_xvol_pullback | 0.45 | 54 | 1.0 | 0.22 | 2.0% |
| metals_core | 1.00 | 38 | 0.7 | 0.15 | 1.4% |
| metals_softband | 0.50 | 31 | 0.6 | 0.12 | 1.2% |
| metals_ob_micro | 0.30 | 6 | 0.1 | 0.02 | 0.2% |

### Hold-time / duration (per sleeve; H4=4h, H1=1h, M15=15min bars)

Recomputed bar-to-exit via `geometry_lib.simulate_detail` for fixed-geometry sleeves; bars-to-1R
(H4) for the cascade/EXEC_COMBO carriers; geometry proxy where a sleeve shares another's exact rule.

| sleeve | TF | hold p25 / median / p75 (hours) | median (days) |
|---|---|---|---|
| fx_jpy / fx_jpy_ny | M15 | 0.25 / 0.75 / 1.25 h | 0.03 d |
| idxrev | H4 | 8 / 16 / 24 h | 0.67 d |
| metals_softband | H4 | 8 / 12 / 32 h* | 0.50 d* |
| energy_agri | H4 | 8 / 16 / 40 h* | 0.67 d* |
| vp_euidx_pocgrav | H4 | 12 / 28 / 56 h | 1.17 d |
| sub_mid_dn_revert | H4 | 16 / 24 / 51 h | 1.00 d |
| metals_core | H4 | 12 / 42 / 81 h* | 1.75 d* |
| sub_xvol_pullback | H4 | 28 / 66 / 112 h | 2.75 d |
| crypto | H4 | 27 / 88 / 242 h** | 3.67 d** |

\* metals/energy use bars-to-1R as a hold **lower bound** (runner/cascade legs exit later, up to the
80 H4-bar / 320h modeled horizon). \** crypto base outcome horizon is H4; the H1->M15 cascade fill
typically shortens the effective hold below these figures.

- **Book hold-time is bimodal.** By trade *count* the mean hold is ~16h (idxrev/fx breadth dominate).
  By *EV weight* the mean hold is **~52h ≈ 2.2 days** (the carriers run 1-4 days). For live monitoring:
  most fills are intraday-to-1-day; the money-makers are 1-4-day H4 swings.

---

## 4. CHALLENGE ECONOMICS (locked W2 MC; 8% / 5% daily / 10% maxDD; N=20,000)

P(pass) is on the vol-matched book (the fair comparison); forward is the recent-regime estimate.

| size/unit | P(pass) all-hist | median days | P(pass) FORWARD | fwd median days | P(pass) STRESS 1.5x | daily-breach % |
|---|---|---|---|---|---|---|
| **0.50%** | **100.0%** | 178 | **100.0%** | 55 | 95.3% | 0.0% |
| **0.75%** | **99.99%** | 119 | **100.0%** | 37 | 87.2% | 0.0% |
| **1.00%** | **99.91%** | 89 | **99.94%** | 28 | 80.9% | 0.0% |

- **P(pass 8%): essentially certain (>99.9%) at 0.5-1.0%/unit** unstressed; forward even easier.
- **Median days-to-pass:** ~37 days at 0.75% forward (89 days all-history at 1.0%).
- **1.5x adversarial left-tail stress** (inflate every losing day 1.5x) is the binding constraint:
  P(pass) falls to **95.3% / 87.2% / 80.9%** at 0.5 / 0.75 / 1.0%. The book is challenge-robust, not
  stress-bulletproof — this is why the dilutive high-frequency sleeves were excluded.
- **Daily-breach = 0.0% at every size.** Worst single replay day is **-2.02% at 1.0%/unit** vs the
  -5% limit — diversification mathematically caps per-day concentration. A 5% daily breach is
  structurally unreachable at any sane size.
- **Independent net-of-erosion MC cross-check** (our net streams, nominal risk): P(pass) 100% / 99.96%
  / 99.64% at 0.5 / 0.75 / 1.0% — confirms the 5.6% fill haircut barely moves pass-rate.
- **Recommended live size: balanced 0.75% nominal (≈0.71% effective vol-matched) on both accounts** —
  P(both pass) 99.99% base / 70.3% under 1.5x stress, 0% daily-breach. Step down to 0.50% for the
  first cycle if you want the 95% stress floor.

---

## 5. BREAKDOWN — contribution to return & frequency

### By sleeve (net; share of total book contribution)

| sleeve | conf | return share (all) | return share (FWD) | trades/yr | freq share |
|---|---|---|---|---|---|
| crypto | 0.85 | 36.8% | **40.5%** | 62 | 2.3% |
| metals_core | 1.00 | 24.5% | 15.9% | 38 | 1.4% |
| energy_agri | 0.80 | 22.5% | 24.7% | 82 | 3.1% |
| sub_xvol_pullback | 0.45 | 9.7% | 7.0% | 54 | 2.0% |
| vp_euidx_pocgrav | 0.30 | 3.9% | 2.1% | 160 | 6.0% |
| fx_jpy | 0.15 | 3.3% | 4.7% | 520 | 19.6% |
| sub_mid_dn_revert | 0.20 | 3.2% | 4.9% | 94 | 3.5% |
| metals_softband | 0.50 | 2.2% | 0.7% | 31 | 1.2% |
| fx_jpy_ny | 0.15 | 0.2% | 0.3% | 196 | 7.4% |
| metals_ob_micro | 0.30 | -0.8% | -0.1% | 6 | 0.2% |
| idxrev | 0.15 | **-5.5%** | -0.6% | 1,407 | **53.1%** |

### By asset class (forward return share / forward frequency share)

| class | return share (all) | return share (FWD) | trades/yr | freq share |
|---|---|---|---|---|
| crypto | 36.8% | 40.5% | 62 | 2.3% |
| energy/agri | 22.5% | 24.7% | 82 | 3.1% |
| metals | 25.9% | 16.5% | 75 | 2.8% |
| multi (xvol metals/energy/index/fx) | 9.7% | 7.0% | 54 | 2.0% |
| fx (JPY) | 3.6% | 5.0% | 716 | 27.0% |
| multi (mid-dn all-class) | 3.2% | 4.9% | 94 | 3.5% |
| index (idxrev + VP) | -1.6% | 1.5% | 1,567 | 59.1% |

**The decisive read:** ~84% of forward EV comes from **crypto + energy + metals + sub_xvol** on
~9% of the trades. The index/fx breadth sleeves are **59-86% of the trade count for ~5% of EV** —
they are deliberately tiny-confidence diversifiers (corr~0) that deepen the pass-rate floor, **not**
profit engines. idxrev is even slightly negative on EV; it is kept at conf 0.15 purely for its
orthogonal breadth (the W3/W5 ablation proved it is non-dilutive on the stress tail at that size).

---

## 6. CAVEATS (read before sizing live)

1. **Replay, not live.** These are M1-fill-net replay results. Real spread widens around
   news/rollover; slippage, partial fills, and broker behavior are not fully captured. The system is
   currently hard-halted from prior unacceptable live behavior — this dossier is an *expectation*, not
   a track record.
2. **Short, hot forward window.** The honest out-of-sample is only ~18 months (2025-01 -> 2026-06),
   and it is the easiest regime in the sample. 2025 at 0.75% shows +56% — treat that as a ceiling, not
   a base case. The +20-45%/yr annualized band (0.5%) is the defensible planning range.
3. **Regime-lumpy, right-skewed.** Mean monthly is ~3x median monthly. Returns arrive in
   crypto/energy clusters; expect long flat stretches (2023 was +0.2%) punctuated by hot months.
4. **EV concentration risk.** ~80% of edge is crypto + energy + metals + sub_xvol. A regime that kills
   trend-following in commodities/crypto would hollow out most of the return; the breadth sleeves would
   not rescue it.
5. **Young substrate/VP cells.** sub_xvol (n=51 fwd), sub_mid_dn (n=129), vp_euidx (forward-only,
   M1-since-2024) are real but thin and 1-or-2-forward-year. Their EV (esp. sub_xvol +1.61R) could
   shrink under the deployed STATE_D scale-out exit (they were mined at fixed 1:3R).
6. **New-sleeve fill erosion is proxied.** The 3 W5 additives have no direct M1 measure; I applied
   conservative class proxies (-0.010 to -0.030R/trade). The 8 core sleeves are M1-measured (-5.6%
   combined). A direct M1 pass on the additives would tighten this.
7. **Hold-time for cascade carriers is bracketed,** not exact: metals/energy/crypto use bars-to-1R
   (lower bound) and the H4 modeled horizon (upper bound) because the LTF cascade exit index was not
   re-walked end-to-end here. The fixed-geometry sleeves (idxrev, fx, substrate, VP) are exact.
8. **Frequency is high by count, low by size.** ~10 fills/day sounds heavy, but ~8 of those are
   conf-0.15 breadth fills carrying minimal risk. Live execution load is real (order management,
   monitoring) even though the dollar weight is concentrated in the few carrier fills.

---

*Artifacts:* `LIVE_EXPECTATIONS_RESULT.json` (all numbers), `LIVE_EXPECTATIONS_compute.py` (engine).
*Inputs:* `INTEG_W5_CLEAN3_DEPLOY.json`, `INTEG_W3_streams_cache.pkl`, `INTEG_W5_new_streams_cache.pkl`,
`EXEC_REALISM_COMBINED_RESULT.json` (fill erosion), `INTEG_portfolio_build_w2.py` (LOCKED MC engine).
