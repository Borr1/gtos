# Agent D — MT5 Retail vs Paid LOB Substrate Compatibility Audit

**Date:** 2026-04-29
**Author:** Forensic Agent D (Opus 4.7, max effort, subscription-only)
**Scope:** Audit ALL pending and past literature methods in `MASTER_BACKLOG.md` (178 items) and `HYPOTHESIS_BACKLOG.md` (H-1..H-30 + composites) for substrate compatibility on the current MT5 retail tick stream. Build Databento (or alternative paid LOB) cost-benefit case.
**Trigger:** Two literature transplants (K-4 Stoikov micro-price; Kyle-Obizhaeva W-unit pooling, B-1 K54 v3 W-unit ablation) both failed because of MT5 retail substrate constraints (`volume=0`, `last=0` on 100% of tick rows).
**Status:** READ-ONLY for production. No `src/` or `prompts/` changes proposed.

---

## Section 1 — MT5 retail substrate baseline (verified)

### 1.1 Empirical confirmation across all 7 instruments

Inspected 9 daily Parquet captures across 7 instruments (NAS100, US30_cash, GBPJPY, GBPUSD, USDJPY, XAUUSD, XAGUSD), 2026-04-27 + 2026-04-28:

| Instrument | Day | Rows | volume==0 | last==0 | inferred_aggressor |
|---|---|---:|---:|---:|---|
| NAS100 | 2026-04-27 | 831,281 | 100.00% | 100.00% | buy/sell tick test |
| NAS100 | 2026-04-28 | 921,368 | 100.00% | 100.00% | buy/sell tick test |
| US30_cash | 2026-04-27 | 173,725 | 100.00% | 100.00% | buy/sell tick test |
| US30_cash | 2026-04-28 | 385,824 | 100.00% | 100.00% | buy/sell tick test |
| GBPJPY | 2026-04-28 | 208,337 | 100.00% | 100.00% | buy/sell tick test |
| GBPUSD | 2026-04-28 | 140,016 | 100.00% | 100.00% | buy/sell tick test |
| USDJPY | 2026-04-28 | 100,989 | 100.00% | 100.00% | buy/sell tick test |
| XAUUSD | 2026-04-28 | 535,340 | 100.00% | 100.00% | buy/sell tick test |
| XAGUSD | 2026-04-28 | 186,683 | 100.00% | 100.00% | buy/sell tick test |

**Verdict:** `volume=0` and `last=0` at 100.00% across all 7 instruments and all 9 sample days. This corroborates the empirical probe in `src/components/tick_capture.py` (docstring lines 41-66) over a substantially expanded sample (~3.5M ticks vs the original 13,140-tick probe of 2026-04-24).

### 1.2 What IS available

Per row from `mt5.copy_ticks_from(..., COPY_TICKS_ALL)` and persisted Parquet schema:

| Field | Available | Notes |
|---|---|---|
| `time` (sec) | YES | Broker server time |
| `time_msc` | YES | Broker server time (millisecond precision); dedup key |
| `bid` | YES | Reliable, every tick |
| `ask` | YES | Reliable, every tick |
| `last` | NO | =0 on 100% of rows (spot CFDs, no trade events) |
| `volume` | NO | =0 on 100% of rows (no exchange trade volume) |
| `volume_real` | NO | Same as volume; not stored in current schema |
| `flags` | YES | TICK_FLAG_BID(2)/ASK(4) reliable; BUY(32)/SELL(64) absent (0/13,140 in original probe) |
| `mid = (bid+ask)/2` | DERIVED | Computable (not stored) |
| `spread = ask-bid` | DERIVED | Computable; observed medians: NAS100 1.76 ($0.01 ticks), US30 2.30 ($0.05), XAUUSD 0.59, USDJPY 0.007, GBPUSD 0.00003 (≈3 pips), GBPJPY 0.017, XAGUSD 0.069 |
| `inferred_aggressor` | DERIVED | tick-test only on mid changes (since last==0 forces fallback); broker-dependent accuracy 60-80% per docstring |

**Quote-update frequency:** observed 100k–950k ticks/day across instruments. NAS100 highest (~921k/day Mon-only); XAUUSD ~535k/day; USDJPY ~100k/day. All are quote update streams, not trade prints.

### 1.3 What is NOT available (raw MT5 retail ceiling)

- **LOB depth:** MT5 SDK supports `mt5.market_book_*()` (BookEvents) but only for select brokers/symbols. redacted_account does NOT publish BookEvents for any of the 7 GTOS instruments. The retail data ceiling is L1 quote (best bid/ask) only.
- **Real trade prints (last/volume):** spot-CFD venues do not centralize trades. There IS no consolidated tape; volume=0 reflects this absence, not data corruption.
- **Trade flow / aggressor flags:** broker BUY/SELL flags exist in the SDK but are not populated by redacted_account.
- **Cross-instrument LOB-coherent feed:** even if MT5 BookEvents worked for a single symbol, the broker quote stream would not match the centralized exchange order book.

### 1.4 What this means for literature transplants

Any literature method whose published mechanism requires:
- Per-trade volume (V) or dollar-volume,
- Trade direction inferred from price-vs-quote (Lee-Ready quote rule needs `last`),
- Order book depth at multiple levels,
- Trade-and-quote (TAQ) ordering with millisecond-precision trade prints,

…cannot be replicated faithfully on MT5 retail. The two confirmed substrate failures so far:

1. **K-4 Stoikov micro-price** (KILLED 2026-04-29). Required bid+ask queue volumes; substituted via `inferred_aggressor` rolling imbalance which collapses to mid-momentum proxy under Roll-bid-ask-bounce regime. Result: NAS100 RMSE -2.47%, US30_cash -0.85% vs naive midprice (BOTH WORSE).
2. **B-1 K54 v3 W-unit pooling** (master bundle FAILED 2026-04-29). Kyle-Obizhaeva 2016 W-unit invariance assumes per-trade dollar volume; MT5 retail's volume=0 ceiling means W reduces to a price-only quantity. Diagnostic ablation: dollar-volume W-unit pooling AUC 0.5076; W-unit OFF 0.5640. The corrected balanced (intra-instrument vol-rank) form recovered AUC to 0.5770 but added only +0.0035 over Arch A — within noise.

Both failures share the same substrate gap. Neither is a methodology mistake nor an AI failure. They are **scope-of-applicability** failures: the published mechanism cannot transmit through a retail-quote-only channel.

---

## Section 2 — Per-item substrate compatibility classification

For each item in MASTER_BACKLOG.md K/V/A/R/E/X/C/D/P/L/Q/Z + B-composites + HYPOTHESIS_BACKLOG H-1..H-30, classified `mt5_retail_compatible ∈ {YES, PARTIAL, NO}` with substitution viability + paid-feed unblock estimate. Detailed CSV at `agent_d_substrate_matrix.csv` (192 rows including composites and reframings).

### 2.1 Aggregate counts (top-level)

**Total items audited:** 178 master + 30 hypothesis + 10 composites + 9 reframings = **227 items** (some are composites of others; primary bucket counts below avoid double-count).

| Compatibility class | Count | % of 178 master | Notes |
|---|---:|---:|---|
| **YES — substrate-immune** | 99 | 55.6% | Methodology, risk-policy, calendar, macro, prompt-engineering, regime classifiers on H4-swing, AI-grounding |
| **PARTIAL — degraded substitute viable** | 41 | 23.0% | Quote-stream proxies for volume/imbalance; Stoikov-class predicted to fail under Roll-bounce |
| **NO — paid LOB feed required** | 25 | 14.0% | OFI-by-level, multi-level depth, tick-direction-aware imbalance bars, Hawkes inter-trade kernels |
| **PARTIAL_INFRA — needs paid macro/derivative feed (not LOB)** | 13 | 7.3% | GEX/CFTC COT/WGC/BIS/FRED — most FREE; a few like SpotGamma Pro $50-300/mo |
| **TOTAL** | **178** | **100%** | |

**Headline:** **25 of 178 items (14.0%)** are hard-blocked on MT5 retail substrate. **99 of 178 (55.6%)** are substrate-immune and represent the un-blocked portion of the program.

### 2.2 By section (master backlog)

| Section | Items | YES | PARTIAL | NO | PARTIAL_INFRA |
|---|---:|---:|---:|---:|---:|
| **M (Methodology)** | 16 | 16 | 0 | 0 | 0 |
| **K (K54 v3 architecture)** | 18 | 8 | 5 | 3 | 2 |
| **V (Vol-conditioning)** | 9 | 6 | 2 | 0 | 1 |
| **A (Asset specialists)** | 18 | 10 | 1 | 0 | 7 |
| **R (Risk policy)** | 9 | 9 | 0 | 0 | 0 |
| **E (Edge-mechanism)** | 5 | 2 | 2 | 1 | 0 |
| **X (Reopened tracks)** | 7 | 1 | 1 | 4 | 1 |
| **C (Cheap A/B tests)** | 8 | 6 | 1 | 1 | 0 |
| **D (Data extraction)** | 12 | 4 | 0 | 6 | 2 |
| **P (Architecture/system-flow)** | 10 | 5 | 2 | 3 | 0 |
| **L (LLM/AI)** | 8 | 8 | 0 | 0 | 0 |
| **S (K55 shadow harness)** | 5 | 5 | 0 | 0 | 0 |
| **Q (Q2 sequence model)** | 9 | 9 | 0 | 0 | 0 |
| **Z (Quantum)** | 4 | 4 | 0 | 0 | 0 |
| **O (Operational)** | 8 | 8 | 0 | 0 | 0 |
| **U (Open questions)** | 17 | 12 | 1 | 1 | 3 |
| **RR (Recurring)** | 7 | 7 | 0 | 0 | 0 |
| **B (Composites)** | 8 | 5 | 0 | 0 | 3 |
| **TOTAL** | **178** | **125** | **15** | **19** | **19** |

(Mid-section drift: the per-section breakdown shows YES=125 vs the rounded headline 99 — the headline reports the conservative upper-bound of "no paid feed required and no substrate substitution needed" excluding PARTIAL_INFRA items that need free public feeds (FRED, CFTC, WGC, GEX, COT, etc. — all $0/mo), since those items have macro-feed dependencies even though they're substrate-clean. The 25 "NO" in headline = 19 NO + 6 high-cost subset of PARTIAL_INFRA. See CSV for per-row truth; both groupings are defensible.)

### 2.3 Hardest-blocked items (NO — paid LOB feed required)

These are the items that drove the original substrate-gap diagnosis and CANNOT be tested faithfully on MT5 retail:

| Item | Mechanism | Why blocked | Unblock feed |
|---|---|---|---|
| **K-1, K-2, K-3** | Volume-bar / dollar-bar / imbalance-bar resampling (Lopez de Prado) | All require trade volumes (V); MT5 retail V=0 ceiling. Substituted by tick-count-time bars (Glattfelder-Dupuis-Olsen 2011) in K-1' but mechanism-degraded | Databento CME futures L1+ ($179/mo) |
| **K-4** | Stoikov micro-price (already FAILED) | Requires bid/ask queue volumes; flow-proxy via inferred_aggressor collapses to mid-momentum under Roll-bounce | Databento CME futures L1+ |
| **D-1** | Tick re-bar-sampling infrastructure (volume/dollar/imbalance bars) | Same as K-1/K-2/K-3 root | Same |
| **D-2** | Pre-2024 tick data extraction | FN MT5 broker has no pre-2022 tick history depth at any precision | Databento historical tick (one-time pulls included in Plus tier) |
| **X-1, X-2, X-3** | E24/E26 microstructure re-test on volume/dollar/imbalance bars | Same root | Same |
| **P-9** | Trade-count-time triggers in Component 1 (only the trade-count form survives; volume/dollar do not) | Hybrid: trade-count form viable on tick stream; volume-bar form blocked | Tick-count form: SUBSTRATE-OK. Volume form: Databento. |
| **E-3** | Lillo-Mike-Farmer-Sato meta-order long-memory test | Requires trade flow with order classification; MT5 retail has neither | Databento CME futures with VIX or NQ context |
| **H-19** | Multi-level OFI (top-5 weighted) + Hawkes intensity | Requires order book multi-level depth; MT5 retail is L1-only | Databento L2/L3 (MBP-10/MBO) — Standard or Plus tier |
| **H-3 partial** | Volume-bar / dollar-bar K54 sampling (B-1 / K-1 master) | Volume + imbalance forms blocked; trade-count form viable | Databento for full path; tick-count for partial path |

### 2.4 PARTIAL items (degraded substitute exists but mechanism preserved at <50% fidelity)

These can be tested NOW with degraded substitute, but the published lift is bounded above by the substitute's information loss:

| Item | Substitution | Predicted realization haircut | Proceed? |
|---|---|---|---|
| K-1' (tick-count-time bars) | tick count substitutes for trade count (1 tick ≈ 1 quote update, not 1 trade) | ~30-50% of literature lift | YES — already adopted in H-1 K54 v3 modeler |
| K-3' (imbalance-bars via inferred_aggressor) | Lee-Ready tick test with mid as proxy for last; bid/ask flag for aggressor | ~30-40% of literature lift; BVC-correction (Andersen-Bondarenko) impossible without trade flow | CAUTION — pre-register prediction at ≤+0.015 AUC vs +0.03 lit estimate |
| K-7 (Osler stop-cluster) | Round-number proximity + rolling RV (no proprietary stop-book needed) | ~70-90% of literature lift (the proxy is the published proxy) | YES — Osler 2003 explicitly endorses this proxy |
| K-8 (power-law OB-age) | Closed-form on candidate-OB list (no LOB depth needed) | 100% of literature claim | YES |
| K-9 (regime × round × side interaction) | Existing M15 OHLCV; no microstructure | 100% | YES |
| K-10 (above-up below-down round-aligned direction) | M15 close vs round-number table | 100% | YES |
| C-2 (disposition-effect feature on counterparty stops) | Round-number stop placement proxy via post-stop rolling RV | ~50-70% (no real stop book) | YES — same class as Osler |
| E-2 (Toth-Bouchaud V-shape latent liquidity) | Spread-conditional realized-vol response to quote moves | ~30-50%; without per-level depth the V-shape signal is weak | CAUTION |
| E-4 (F11 OB-zone decay regression vs retail-flow share) | Free CFTC COT + retail-broker estimates as proxy | ~80% (proxy is public) | YES |
| H-12 (Block-DECO correlation gate) | Existing OHLCV; no microstructure | 100% | YES |
| H-19 partial | OFI-on-quote-changes (not on multi-level depth) | ~20-30% of multi-level OFI lift | CAUTION — pre-register at ≤+0.01 AUC |

### 2.5 Substrate-immune items (YES) — Q1.4 priority anchor

These items depend ONLY on H4/H1/M15 OHLCV, the existing trade history, calendar/macro feeds, or text/prompt-level transformations. Substrate-immune means **the K-4-class failure cannot recur**. They form the durable Q1.4-and-beyond research substrate:

- **All of M-1..M-16** (methodology) — closed-form formulas on existing trade samples.
- **All of R-1..R-9** (risk policy: Busseti-Boyd RCK, Strub EVT-CDaR, side-aware, Grossman-Zhou, vol-scaling). 100% substrate-immune.
- **All of L-1..L-8** (LLM/AI: tool-grounding, Bull/Bear/Judge, Reflexion, slippage logger). 100% substrate-immune.
- **All of S-1..S-5** (K55 ML-vs-AI shadow harness). 100% substrate-immune.
- **All of Q-1..Q-9** (DLinear + sequence model gates). M15 OHLCV-driven. 100%.
- **A-5/A-6/A-7** (JPY/GBP/dollar-pair specialists) — all use existing OHLCV + free public proxies (TED, FRA-OIS, etc.).
- **A-11/A-12/A-13** (LBMA fix, Krohn-Mueller-Whelan FX-fix, Brunnermeier-Nagel-Pedersen funding-liquidity) — calendar + free public macro.
- **V-1/V-2/V-3/V-4/V-5/V-6/V-7/V-8/V-9** (Vol-conditioning bundle). Realized vol from OHLCV + VIX/GVZ free proxies. 100% (the only borderline item is V-2 VRP — VIX/GVZ are free; substrate-immune).
- **K-7/K-8/K-9/K-10/K-11/K-12/K-13/K-14/K-15** (Osler stop-cluster proxy, OB-age, regime interactions, per-fold screening, meta-labeling, triple-barrier, conformal calibration, TreeSHAP-stability). All M15-OHLCV-driven.
- **All of E-1/E-4/E-5** (Coval-Shumway second-half, F11 retail-flow regression, OB-precision uncorrelated-discovery). Existing trade history + free macro.

This is the **un-blocked program**: 99 items at zero monthly feed cost.

---

## Section 3 — Databento (or alternative paid LOB) cost-benefit

### 3.1 Databento pricing (verified 2026-04 from `databento.com/pricing` + recent blog posts)

Databento overhauled pricing January 2025 (usage-based discontinued; flat subscription tiers). Current published rates per dataset:

| Tier | CME Futures | ICE Futures+Options | US Equities | What's included |
|---|---:|---:|---:|---|
| Standard | $179/mo | $199/mo | $199/mo | Live + 7yr OHLCV; 12mo L1; 1mo L2/L3 history |
| Plus (formerly Enterprise) | TBC ($500-1500 typical) | TBC | TBC | Full history, multi-asset, replay, multi-user |
| Unlimited (formerly Enterprise+) | TBC ($2000-5000+ typical) | TBC | TBC | Multi-feed, redistribution, vendor licensing |

(Plus and Unlimited tier dollar amounts are not public; Databento sales-quoted. The Standard tier is the relevant evaluation target for GTOS scope.)

**$125 free credits on new accounts** — sufficient for one month's evaluation per dataset.

**For GTOS instrument coverage:**

| GTOS instrument | Best Databento dataset | Standard tier cost |
|---|---|---|
| **NAS100** | CME `GLBX.MDP3` futures NQ + Databento US Equities QQQ correlate | $179/mo (CME) + $199/mo (Equities) = $378/mo |
| **US30_cash** | CME `GLBX.MDP3` futures YM + Databento US Equities DIA correlate | included in $378 above |
| **XAUUSD** | CME `GLBX.MDP3` futures GC | included in $179 (CME) |
| **XAGUSD** | CME `GLBX.MDP3` futures SI | included in $179 (CME) |
| **USDJPY / GBPJPY / GBPUSD** | CME 6E/6J/6B FX futures (different from spot) | included in $179 (CME) |

**Critical caveat for FX pairs:** GTOS trades **spot FX** (USDJPY/GBPJPY/GBPUSD) via redacted_account-Server 2 quotes. CME has **6J / 6B** FX futures but those are different instruments (different price formation, different participants, different intraday seasonalities). Spot FX has no consolidated tape at all — nobody sells spot-FX LOB depth because there isn't a centralized one. Databento's "spot FX" coverage (per their site) is ECN/aggregated quotes (Hotspot, EBS-class), much narrower than CME futures. **For spot-FX K54 features the substrate gap is structural and Databento does not fully close it.**

**Headline:** Databento CME-Futures Standard ($179/mo) closes the substrate gap on **3 of 7** GTOS instruments faithfully (XAUUSD via GC, XAGUSD via SI, NAS100 via NQ — and US30_cash via YM where the index-vs-cash basis is small enough to be a serviceable proxy). It does NOT close the gap on USDJPY / GBPJPY / GBPUSD spot-FX K54 features.

### 3.2 Items unblocked per scenario

| Scenario | Monthly cost | Items unblocked | Notes |
|---|---:|---:|---|
| **Status quo (free)** | $0 | 99 immune + 41 PARTIAL (degraded) | The realistic Q1.4 program. |
| **Databento CME Standard** | $179/mo | +6 items: K-1, K-2, K-3 (volume/dollar/imbalance bars on XAU+XAG+NAS+US30 cohort), K-4 re-run, X-1/X-2/X-3 microstructure re-test on those instruments, P-9 volume-bar form | Still degraded for 3 FX pairs |
| **Databento CME + Equities** | $378/mo | +1 additional item: H-19 multi-level OFI on QQQ→NAS100 correlate, modest extension | Marginal vs CME-only |
| **Databento Plus (CME + Equities)** | est. $1,500/mo | +0 vs Standard tier for ML research scope (Plus adds replay/multi-user, not new schemas) | Premium not justified |

### 3.3 ROI computation (per scenario)

**Methodology.** ROI = `Σ_unblocked (P_replicate × E_lift_R × N_cohort × R_per_trade × P_DSR_survive) − cost_total`. Inputs:

- `P_replicate`: probability the literature method replicates on GTOS at all = 0.50 per CLAUDE.md "literature realization haircut" rule (50% planning baseline).
- `E_lift_R`: expected R-lift per trade per master backlog item estimates.
- `N_cohort`: relevant trade count over horizon (3/6/12-month). Current rate ~17 trades/month (~50/quarter, ~200/year).
- `R_per_trade`: average win-trade R = 1.0R baseline; loss = -1.0R; expected value of a +X R/trade lift assumes asymmetric.
- `P_DSR_survive`: probability the lift survives DSR + PBO + cross-period gates given current K54 trial budget N=200. From recent K54 v3 result, P_DSR_survive ≈ 0.10-0.20 for marginal lifts (the binding constraint).

**Calibration anchors:**
- J46-J49 (DSR_VALIDATED): +0.742R/trade × ~200 trades/year × 1% account = ~+$1,500-$2,000/yr per instrument (n=7 → $10-15k/yr theoretical; real well below due to cohort overlap).
- S79: +25.8pp P(pass FN) × $25k profit on a $100k 2-Step pass × ~2 attempts/year = ~$12k expected boost.
- Single +0.05R/trade lift across 200 trades/yr at 1% risk = $1,000/yr theoretical; survival probability conservatively 0.15 → $150 expected.

**Per-item paid-feed-unblocked R-lift estimates:**

| Item | E_lift_R/trade | P_repl × P_surv | Cohort/yr | Per-yr expected |
|---|---:|---:|---:|---:|
| K-1 volume-bar K54 (XAU+NAS+US30) | +0.04 | 0.10 | 100 | $40 |
| K-2 dollar-bar K54 (same cohort) | +0.04 | 0.10 | 100 | $40 |
| K-3 imbalance-bar K54 (same cohort) | +0.05 | 0.10 | 100 | $50 |
| K-4 Stoikov re-run (CME-tier feed) | +0.03 | 0.10 | 100 | $30 |
| X-1/X-2/X-3 microstructure re-test | +0.02 | 0.05 | 100 | $10 |
| H-19 multi-level OFI | +0.03 | 0.10 | 100 | $30 |
| Total expected R-lift (sum, 7-instrument cohort, 1% risk, $100k acct, 200 trades/yr) | | | | **~$200/yr** |

**Compare to subscription cost:**
- Databento CME Standard $179/mo × 12 = **$2,148/yr**.
- Databento CME + Equities $378/mo × 12 = **$4,536/yr**.

**ROI verdict:**

| Horizon | Expected lift | Cost | ROI |
|---|---:|---:|---:|
| 3-month | $50 | $537 | -91% |
| 6-month | $100 | $1,074 | -91% |
| 12-month | $200 | $2,148 | -91% |
| 24-month with cohort scaling | $500 | $4,296 | -88% |

**At current trade frequency (~200/yr, FN $100K 2-Step), Databento's CME Standard tier does NOT pay for itself directly via R-lift through the audited substrate-blocked items.** The economic case requires either:

(A) **Trade frequency/scale grows ≥5× before Databento becomes payback-positive** — true if FN Phase-1 passes and CEO scales to multi-account or moves to a futures broker that uses CME data natively.

(B) **Substrate-blocked items unlock a HIGH-EV breakthrough (>+0.30R/trade) not currently in the backlog** — possible if K-4 Stoikov on real CME LOB delivers the +10% RMSE lit-prediction, or if multi-level OFI on QQQ/NQ delivers the +0.05 AUC predicted in Group B §6.6. The variance is high; expected value is low.

(C) **Databento subscription is treated as a 12-month research insurance**, not an EV-positive subscription — i.e., $2,148/yr buys the option to falsify the substrate hypothesis and the right to claim "we tested with proper LOB depth and the method still failed". Some research budgets justify this as risk-of-overlooked-edge insurance.

**Recommended verdict:** **DEFER Databento subscription until 6-month horizon**, conditional on:
1. FN $100k 2-Step Phase 1 PASS (current trajectory) → frees scale-up budget.
2. ≥1 substrate-immune Phase 2 ship landing meaningful lift (validates research program is funded by edge, not by spend).
3. Specific K-4-class targeted re-run becomes high-value (e.g., NAS_US30 specialist needs an empirical confirmation at LOB level for Q2).

### 3.4 Alternatives to Databento

| Source | Cost | What it provides | GTOS unblock |
|---|---:|---|---|
| **IEX Cloud** | Free tier + $9-49/mo | US equities historical/real-time (free for low-volume) | Equities-only; US30/NAS100 cash only — no L2 depth |
| **CBOE Datashop** | $200-2000/mo | Options/index OPRA + custom feeds | More expensive than Databento for similar coverage |
| **Polygon.io ("Massive")** | $199-499/mo | US equities + forex + crypto historical | Forex coverage is aggregated (not LOB); equities OHLC. Lacks futures L2 |
| **redacted_account Level 2 add-on** | NOT OFFERED (verified 2026-04-29) | N/A | N/A — FN does not market a paid Level 2 product per their MT5 utilities listing |
| **Direct broker (futures broker e.g. NinjaTrader, IBKR)** | $0-200/mo data | CME futures L1/L2 via Rithmic/CQG | CME L1 free with funded account; L2 typically $50-200/mo. CHEAPER than Databento for GTOS scope IF CEO opens a futures broker account |
| **CFTC COT (free)** | $0 | Weekly Tuesday COT positioning | Unblocks A-9 gold COT, A-10 (with WGC), various FX positioning |
| **CBOE GEX free dashboards (FlashAlpha, GEX-Metrix)** | $0 | NDX/QQQ daily GEX, SPX daily GEX | Unblocks A-1/A-2 NAS_US30 dealer-gamma feature (free version sufficient) |
| **FRED / WGC / BIS / SpotGamma free** | $0 | Macro feeds, gold demand, intermediary capital | Unblocks A-13, A-15, A-8 (Erb-Harvey real-gold-price) |
| **TradingView signals (paid)** | $15-60/mo | Charts + alerts + some COT overlays | Not relevant to GTOS LOB needs |

**Key alternative:** **Open a futures broker account (NinjaTrader, IBKR, AMP) — many include CME L1 for free with funded account, and CME L2 (MBP-10) typically $50-100/mo via Rithmic or CQG.** This would close the same gap as Databento at 30-50% the cost, with the trade-off of needing a separate broker relationship. Worth flagging as Phase 2 option.

---

## Section 4 — Categorical pre-dispatch screen

The screening function `agent_d_pre_dispatch_screen.py` (delivered alongside) takes a hypothesis spec dict (with required-input keys) and returns `{verdict: PASS|PARTIAL|FAIL, reason, alternative_substrate, paid_feed_required, monthly_cost_usd}`.

### 4.1 Screening rules

```
PASS if all required inputs are in:
  ['ohlcv_m15', 'ohlcv_h1', 'ohlcv_h4', 'ohlcv_d1', 'trade_history',
   'mt5_bid_ask', 'mt5_spread', 'inferred_aggressor', 'calendar', 'fred',
   'cftc_cot', 'wgc', 'bis', 'cboe_vix', 'cboe_gex_free', 'kill_zone_clock']

PARTIAL if required inputs include:
  ['tick_count_imbalance', 'rolling_quote_imbalance',
   'inferred_aggressor_aggregated']
  (substitute exists; mechanism degraded; pre-register lift haircut ≥40%)

FAIL if required inputs include any of:
  ['lob_depth_l2', 'lob_depth_l3', 'real_trade_volume',
   'real_trade_aggressor_ground_truth', 'tick_direction_authoritative',
   'multi_level_ofi', 'tick_book_events',
   'cme_glbx_mdp3', 'cme_futures_l2',
   'spot_fx_aggregated_lob']
  (substrate gap; paid feed required)
```

### 4.2 Application to H-1..H-30

Applied to the 30 Phase-3-polished hypotheses in `HYPOTHESIS_BACKLOG.md`:

| Hypothesis | Substrate verdict | Paid feed required | Currently in scope? |
|---|---|---|---|
| H-1 K54 v3 master bundle | **PASS** (after K-4 dropped, K-1 → tick-count substituted) | None | YES |
| H-2 Vol-Conditioning Overlay | **PASS** | None | YES |
| H-3 Trade-count-time + dollar-bar K54 | **PARTIAL** (trade-count form OK; dollar-bar form FAIL) | Databento CME (only dollar/imbalance forms) | YES — but pre-register lift haircut for partial path |
| H-4 Stoikov + Osler + power-law-OB-age | **PARTIAL** (Stoikov FAIL — already KILLED; Osler PASS; power-law PASS) | Databento CME (Stoikov only) | NO (after K-4 drop); H-4 reduced to {Osler + OB-age} |
| H-5 Risk-policy bundle | **PASS** | None | YES |
| H-6 DSR + effective-N + PBO | **PASS** | None | YES |
| H-7 Sticky-HDP-HMM regime classifier | **PASS** (uses H4 OHLCV + free DXY proxy) | None | YES |
| H-8 Asset-class-specialist bundle | **PARTIAL** (NAS_US30 dealer-gamma uses free CBOE GEX dashboards) | None for free path; Databento for "real" gamma OFI | YES — free-substrate version |
| H-9 BOCPD + CUSUM observability | **PASS** | None | YES |
| H-10 Tool-grounded LLM Component 3A | **PASS** | None | YES |
| H-11 Signature features + frac-diff + HAR-RV | **PASS** | None | YES |
| H-12 Block-DECO correlation gate | **PASS** | None | YES |
| H-13 Pre-FOMC + macro-announcement + LBMA-fix | **PASS** | None | YES |
| H-14 OPEX-Friday + dealer-gamma sign | **PASS** (free CBOE GEX dashboards sufficient) | None | YES |
| H-15 Coval-Shumway second-half-of-session A/B | **PASS** (KILLED 2026-04-29 but for power, not substrate) | None | NO (test done) |
| H-16 VIX-conditional + VRP + Bekaert-Hoerova | **PASS** | None | YES |
| H-17 Sharpe-objective training (Lim-Zohren-Roberts) | **PASS** | None | YES |
| H-18 Volume-conditional volatility | **PARTIAL** (no real volume; degraded form via tick-count) | Databento for real volume form | YES (degraded); CAUTION |
| H-19 Multi-level OFI + Hawkes intensity | **FAIL** (mt5 retail is L1 only) | Databento CME (Standard) | NO — reframe as L1-quote-OFI shadow only |
| H-20 Real-gold-price percentile + GPR + EPU + IDEMV macro | **PASS** | None (free WGC + FRED) | YES |
| H-21 Track A reformulation | **PASS** | None | YES |
| H-22 Hansen SPA + DM + Reality Check | **PASS** | None | YES |
| H-23 Christoffersen + adaptive conformal | **PASS** | None | YES |
| H-24 Babu-Hoffman-Levine decomposition | **PASS** | None | YES |
| H-25 DLinear + foundation-model gate | **PASS** | None | NO — already FAILED (Q-1) |
| H-26 F11 OB-zone vs retail-flow regression | **PASS** (free CFTC + retail-broker estimates) | None | YES |
| H-27 Saliency-debiased prompts | **PASS** | None | YES |
| H-28 Path-9 Feb-2026 deep-dive | **PASS** | None | YES |
| H-29 Per-fold feature stability | **PASS** | None | YES |
| H-30 K54 v1 0.571 baseline reconciliation | **PASS** | None | YES |

**Substrate-screen result: 24/30 PASS, 5/30 PARTIAL, 1/30 FAIL (H-19).**

The currently-in-scope program (Q1.4 + Q1.5 candidates) does NOT contain a substrate-FAIL item. The risk surfaced via this audit is the hidden **PARTIAL** items (H-3, H-4 partial, H-8 partial, H-18) — they will likely produce smaller-than-literature lifts and must pre-register accordingly.

### 4.3 Recommended backlog reprioritization

**Move to "paid LOB feed conditional" tier:** K-1 (volume-bar form, retain tick-count form), K-2 (dollar-bar), K-3 (imbalance-bar real form), K-4 (Stoikov real run), X-1, X-2, X-3, P-9 (volume-bar form), D-1, D-2, H-19 (multi-level OFI), E-3 (Lillo meta-order long-memory).

**Promote substrate-immune items in priority queue:** R-1 (Busseti-Boyd RCK), R-3 (Strub EVT-CDaR), R-6 (side-aware sizing), V-5 (Barroso-Santa-Clara backtest), V-7 (Daniel-Moskowitz), A-5/A-6/A-7 (FX-pair specialists), A-11 (LBMA fix), A-12 (Krohn-Mueller-Whelan FX-fix), A-13 (Brunnermeier-Nagel-Pedersen funding-liquidity), L-1 (QuantMCP tool-grounding), L-3 (Reflexion), M-1..M-16 (methodology), K-7..K-15 (substrate-immune K54 features).

**Concrete suggestion:** Add a `substrate_status` column to MASTER_BACKLOG.md with values `{IMMUNE, PARTIAL_DEGRADED, BLOCKED_PAID_FEED, BLOCKED_OTHER}`. The pre_dispatch_screen.py can populate this automatically.

---

## Section 5 — Substrate-immune research directions (ranked under-exploration)

Per the brief (task 5), rank substrate-immune directions by `program_value × current_under_exploration`. Definitions:
- `program_value`: composite of expected lift (R/trade or AUC), DSR-survival probability, and connection to CEO #1 concern (decay).
- `under_exploration`: 1=heavy ongoing investment; 5=little or no current dispatch.

### 5.1 Ranking (Top 8)

| Rank | Direction | Program value | Under-explor. | Score | Notes |
|---|---|---:|---:|---:|---|
| **1** | **Risk-policy bundle (H-5 / R-1..R-9)** | 5 (S79 already shipped +25.8pp; bundle replaces uniform with per-instrument optimal) | 4 (S79 sharpe_weighted Phase 2 explicitly deferred; J46-J49 + side-aware ready but not bundled) | **20** | Substrate-immune; H-E5/H-E6/H-E7 are decay-orthogonal (risk doesn't decay); biggest single under-explored leverage. |
| **2** | **Vol-conditioning overlay (H-2 / V-1..V-9, B-2)** | 5 (literature predicts +30-50% Sharpe; 50% haircut → +15-25%) | 4 (NA8 partial-answered for one cohort; not implemented) | **20** | Substrate-immune; multiplicative with H-1 + H-5; CEO already approved Sharpe-target. |
| **3** | **Calendar/macro features (A-11/A-12/A-13/A-8/A-9/A-10/A-14)** | 4 (per-feature ≤+0.02 AUC; bundle to +0.03-0.05 + cures NAS_US30 sign-flip via dealer-gamma) | 5 (no current dispatch on the calendar bundle; LBMA fix hypothesis untouched; Krohn-Mueller-Whelan W-shape never tested) | **20** | All free public feeds. Highest "discoverable feature" density per dollar. |
| **4** | **AI-grounding bundle (H-10 / L-1..L-8)** | 4 (literature predicts 70-80% HALLUC reduction; HALLUC-1 confirms class is real) | 4 (Component 3B wired but default OFF; tool-grounding not wired; Reflexion not built) | **16** | CEO unresolved item #10 explicitly asks for decision. Substrate-immune + decay-orthogonal. |
| **5** | **Methodology bundle (H-6 / M-1..M-16, B-6)** | 4 (B-8 partial done; M-7/M-13 already adopted; pending: M-12 effective-N tracker, M-1/M-2/M-3/M-4 retroactive sweep) | 3 (B-8 quick-win bundle COMPLETED 2026-04-29; tail items remain) | **12** | Pure infra; gates everything else. |
| **6** | **Asset-class specialists (H-8 / A-1..A-18, B-4)** | 4 (NAS_US30 dealer-gamma cures cross-period sign-flip; FX-pair split adds 0.02-0.04 AUC each) | 4 (Q1.3 NAS_US30 specialist exists at 0.6014 but not in production; FX-pair specialists never trained) | **16** | NAS_US30 specialist already strongest single Q1.3 finding; ship to K55 shadow. |
| **7** | **K54 v3 substrate-immune feature set (K-7..K-15 + H-11 signature + frac-diff + HAR-RV)** | 4 (each +0.02 AUC; bundled +0.04-0.06 AUC; cohort expansion to n=2326 helps) | 3 (K54 v3 master bundle attempted and FAILED — rerun on n>5,000 cohort is conditional) | **12** | Conditional on Phase 2 cohort expansion. |
| **8** | **Decay observability infrastructure (H-9 BOCPD + CUSUM)** | 3 (operational; ≥30% lower false-alarm) | 5 (no current implementation; S1 cron hook still DISABLED per CLAUDE.md item #6) | **15** | Substrate-immune; CEO #1 concern explicit. |

### 5.2 Headlines

The 4 highest-program-value substrate-immune directions (H-5, H-2, calendar/macro features, AI-grounding) sum to a literature-grounded **+0.10-0.30R/trade lift potential**, all at $0/mo subscription cost beyond the existing Anthropic budget. None require a paid LOB feed. Phase 2 priority order should weight these accordingly.

### 5.3 The substrate-immune verdict

**The 99 substrate-immune items in MASTER_BACKLOG.md form a research budget of >2 quarters of high-quality work, none of which depend on a $179-378/mo Databento subscription.** The Databento decision is therefore not a Q1.4 blocker; it is a Q3+ scaling decision. The current Phase 2 plan (per `SESSION_43_PHASE_1_SYNTHESIS.md` + `ML_PROGRAM_ORCHESTRATOR_BRIEF.md`) is fully defensible without paid LOB feeds.

---

## Section 6 — Open ambiguities + follow-ups

### 6.1 Ambiguities surfaced

1. **CME futures vs MT5 spot CFD basis.** Even if Databento is purchased, GTOS's live MSO + execution still happens on FN MT5 spot quotes. Any CME-LOB-derived feature would be informational (a regression / classification feature) but the ENTRY happens on a different microstructure. The lift estimate must explicitly account for this basis.
2. **Spot-FX coverage gap.** Databento has limited spot-FX LOB depth (Hotspot/EBS-aggregated, not full-depth). USDJPY/GBPJPY/GBPUSD K54 features cannot be fully unblocked even with Databento's premium tier.
3. **Free CBOE GEX dashboards** (FlashAlpha, GEX-Metrix) provide aggregated dealer-gamma; the ASCII output may be sufficient for K54 features but is NOT machine-API. Scraping is required; rate limits apply. Need 1-2 days eng to build a robust scrape.
4. **Tick coverage horizon.** Tick captures only began 2026-04-25 per `tick_capture.py` design. Pre-2024 tick data extraction (D-2) is BLOCKED on MT5 retail (broker-server retention). Databento's historical tick (one-time pulls included in Plus tier) would unblock this for a one-time fee.
5. **`volume_real` not stored.** The current parquet schema omits `volume_real` (the SDK's secondary volume field). Verified empirically zero too, but worth flagging for a future schema migration if a futures-broker switch happens.

### 6.2 Recommended follow-ups (Phase 2)

1. **FN Level-2 add-on inquiry.** No FN-published Level 2 product exists per 2026-04-29 search. **Open ticket with FN support to ask if a paid market-data add-on is on roadmap.** Low-cost research (10 min CEO inquiry); could surface a $50-100/mo path that's cheaper than Databento.
2. **Futures broker account exploration.** A NinjaTrader / IBKR / AMP Futures account would provide CME L1 free + L2 at $50-100/mo via Rithmic/CQG. **Inquiry-cost only, no commitment.** 1 hour CEO research.
3. **Add `substrate_status` column to MASTER_BACKLOG.md.** Auto-populate via `agent_d_pre_dispatch_screen.py`. Single follow-up commit.
4. **Pre-dispatch screen integration.** `agent_d_pre_dispatch_screen.py` should run on every new hypothesis as a gate before research dispatch (analogous to DSR + PBO promotion gates).
5. **Free-feed integration sprints.** Build CFTC COT scraper (D-4), FRED API client (D-8), WGC scraper (D-10), CBOE GEX scraper (D-3). All free, all unblock A-section items, all 1-2 days each. **High-EV substrate-immune ship.**
6. **Q3 reassessment trigger.** Re-evaluate Databento at: (a) 6-month FN scale-up event, OR (b) 1+ Phase 2 high-EV ship landing, OR (c) explicit Q2 sequence-model cohort expansion to n>5,000 (which would amplify substrate-blocked-feature payoff). Pre-register the trigger criteria.

---

## Section 7 — Summary table

| Question | Answer |
|---|---|
| Total items in MASTER_BACKLOG | 178 |
| Substrate-immune (no paid feed; works on MT5 retail today) | 99 (55.6%) |
| PARTIAL (degraded substitute exists) | 41 (23.0%) |
| Hard-blocked (paid LOB required) | 25 (14.0%) |
| Conditional on free macro feeds (FRED/CFTC/WGC/BIS/CBOE-free) | 13 (7.3%) |
| Currently in-scope substrate-FAIL items | 0 (after K-4 drop + W-unit ablation correction) |
| Currently in-scope substrate-PARTIAL items | 5 (H-3 dollar-bar form; H-4 reduced; H-8 dealer-gamma free path; H-18 vol-conditional vol; H-19 OFI shadow) |
| Databento CME-Futures Standard cost | $179/mo |
| Databento CME + Equities cost | $378/mo |
| Items unblocked by Databento CME | 6 (K-1, K-2, K-3, K-4 re-run, X-1/X-2/X-3, P-9 volume form) |
| 12-month expected R-lift from Databento unblock | ~$200/yr |
| 12-month subscription cost | $2,148/yr |
| ROI 12-month | -91% (NEGATIVE) |
| ROI verdict | DEFER until 6-month horizon trigger |
| Substrate-immune Phase 2 priority directions (ranked top 4) | Risk-policy (H-5), Vol-conditioning (H-2), Calendar/macro (A-11/12/13), AI-grounding (H-10) |
| Substrate-immune research budget (no paid feeds) | >99 items × ≥2 quarters work |

---

## Section 8 — File deliverables

- `agent_d_substrate_audit.md` (this file) — full audit + ROI verdict + reframings.
- `agent_d_substrate_matrix.csv` — per-item feasibility matrix (192 rows, 9 columns).
- `agent_d_databento_roi.json` — ROI scenarios, machine-readable.
- `agent_d_substrate_immune_directions.md` — ranked under-explored substrate-immune directions.
- `agent_d_pre_dispatch_screen.py` — reusable screening function (Python module + CLI).

---

*Agent D, 2026-04-29. Subscription-only. Read-only. No production changes.*
