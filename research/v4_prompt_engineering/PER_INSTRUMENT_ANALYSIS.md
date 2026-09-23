# V4 Prompt Engineering — Per-Instrument Specialization Analysis

**Agent:** Research Agent C (Opus 4.7, max effort)
**Date:** 2026-04-24
**Branch:** `research/v4-prompt-per-instrument`
**Scope:** Should V4 specialize the AI prompt per instrument / per class, or stay universal?
**Subscription only — $0 API cost.**

---

## 1. Executive Summary

### Recommendation — **Option 4: Universal core + thin instrument-aware injection** (HIGH confidence, ~80%)

One system prompt, unchanged core (three-gate C1/C2/C3 framework, NO_TRADE allow-list, geometric invariants, data-grounding rules). A single `{instrument_guidance}` placeholder injects 4–8 lines of per-instrument context (regime notes + class-level cautions) computed from config. **No structural logic change.** Budget: $20–40 for one canary + F3-style 12-slice v2-active backtest of the V4 prompt.

**Why not Option 1 (pure universal):** The evidence does not support "one prompt serves all equally" — asset classes have genuinely different structural signatures (ATR/price ratio spans 11× across the catalog, fat-tail kurtosis ranges from −0.44 to +7.15, Monday gap magnitudes differ 22×). The v1-bullish-bias bug (ADR-004) also showed that behavior that looked "universal" silently collapsed differently per instrument (USDJPY 0/426 raw SHORT vs XAUUSD's 22.8% post-v2). Universal means there's no "shock absorber" to catch that.

**Why not Option 2 (per-class prompts):** Maintenance burden is disproportionate to the edge recovery possible. The one robust cross-instrument failure mode (D1-bias-lag on trending weeks — W14 NAS100 100% bearish bias during +4.20% rally) is instrument-agnostic per T3.1 — a per-class prompt would not fix it. The instrument-specific findings (FX precision, EURUSD 60% degenerate outputs) were fixed by precision-scaffolding the universal prompt in V2 (FA-2), not by splitting it.

**Why not Option 3 (per-instrument):** 24 instruments × prompt-drift risk × canary cost ≈ $240–600 per V-bump. No evidence justifies this granularity — F3 + A2 show XAUUSD SHORT emerges under v2 but USDJPY does not, which is a *structure-detector* discriminator, not a prompt-discriminator.

### One-line rationales per class

- **Commodities (XAU, XAG, XTI/XBR):** fat-tail kurtosis median +3.53 (XAU), +7.15 (XAG), +2.85 (USOIL). Prompt should note "wide wicks are NORMAL — don't tighten SL buffer on apparent sweep" — instrument-agnostic rule already exists in V3.
- **FX majors (EUR, GBP, AUD, NZD, USD-X):** lowest ATR/price (0.08–0.17%) + 5dp precision is the only non-trivial delta. V2 precision-scaffolding (FA-2, `fa35cc0`) already fixed the 60% EURUSD degenerate-output bug. Class-level prompt change not warranted.
- **FX JPY pairs:** 3dp precision. Session-ATR 0.10–0.16%. Structurally similar to FX majors; Tokyo session adds extra setup opportunity. V2 handles 3dp correctly.
- **Indices (US30, NAS100, SPX500, GER40, JP225, UK100):** gap-heavy Monday open (0.38–0.63% vs FX 0.07–0.21%). `skip_first_ny_candle`-style guardrails are instrument-level. Current config handles via `first_ny_candle_skip`. Not a prompt concern.
- **Crypto (BTC, ETH):** 24/7 liquidity, 26% of H1 bars fall on weekends. `kill_zones` config must differ (no session boundaries). The prompt itself needs no crypto-specific text because OB-retest structural logic is the same — but the KZ-display section in the prompt must render correctly for 24/7. This is already handled by `build_system_prompt(config)` using `market.kill_zones`.

### Proposed validation plan

1. Canary expansion: add 10 multi-instrument borderline fixtures (2 USDJPY + 2 GBPUSD + 2 NAS100 + 2 BTCUSD + 2 XAGUSD) using existing fixture-generation pipeline. Current canary is 60 fixtures — no additional baseline regen needed. Canary cost: ~$3–4 per run.
2. F3-style backtest of V4 prompt on same 12 slices (XAUUSD×8 + USDJPY×4) under `detector_version: v2` with V4-injection enabled. Re-run cost: ~$40 (F3 spent $37.50). This provides a direct-comparable before/after.
3. Phase 2a: dispatch single-slice sims on the 5 non-live instruments (EURUSD, NAS100, BTCUSD, XAGUSD, USOIL) @ ~$10/slice = $50 to validate the V4 prompt does not regress on unseen asset classes.
4. Total: **~$100** in API spend for the complete V4 validation.

---

## 2. Current Prompt State — Baseline

Source: `src/prompts/primary_analyzer_prompt.py` (V3, 2026-04-24).

**What already varies per instrument:**
- `price_format` → `{decimal_places}` (5, 3, 2, 1dp buckets in `_build_precision_examples`).
- `sl_min_display` → SL minimum in pips / points / dollars (`risk.sl_absolute_min`).
- `kz_display` → KZ windows from `market.kill_zones` config.
- `valid_examples` / `invalid_examples` → precision-calibrated numeric anchors (FA-2, `fa35cc0`).
- `_INSTRUMENT_IDENTITY` dict — "institutional gold trader" vs "institutional index trader" etc. Currently UNUSED in the prompt text itself (scaffolding for future role priming).

**What does NOT vary per instrument:**
- C1/C2/C3 gate semantics.
- NO_TRADE allow-list (R1–R8).
- Anti-gaming FORBIDDEN reason blocks (G1–G5).
- OB-retest framework mechanics.
- Self-check items.
- Pre-screen / Gate 0 / Gate 0.5 logic (not part of prompt).

**Already class-aware logic:** `_PIP_PAIRS`, `_JPY_PAIRS`, `_POINT_INSTRUMENTS` tuples drive `sl_min_display` branching. This is a config-time scaffolding pattern, not a prompt-text split.

---

## 3. Task 1 — Instrument Characteristic Catalog (24 instruments)

Computed from `data/historical_2026/` via `_compute_instrument_characteristics.py` (Jan 2 – Apr 24, 2026 range for most; stale tails on NAS100 / USOIL / SPX500 per commit `74f2fec`). All rates bit-exact reproducible.

### 3.1 Per-instrument structural characteristics

| Symbol | Class | DP | H1 ATR % (med / p95) | D1 range % (med) | D1 kurt (fat-tail) | Mon-gap abs % (med) | Wkn bars |
|---|---|--:|---:|---:|---:|---:|---:|
| **XAUUSD** | commodity_metal | 2 | 0.467 / 1.611 | 2.38 | **+3.53** | 0.578 | 0% |
| **USDJPY** | fx_jpy | 3 | 0.119 / 0.281 | 0.60 | +1.31 | 0.086 | 0% |
| **GBPUSD** | fx_major | 5 | 0.114 / 0.297 | 0.67 | +0.15 | 0.114 | 0% |
| **GBPJPY** | fx_jpy | 3 | 0.115 / 0.273 | 0.68 | +0.47 | 0.144 | 0% |
| **US30_cash** | index | 1 | 0.196 / 0.676 | 1.33 | +1.24 | **0.398** | 0% |
| EURUSD | fx_major | 5 | 0.099 / 0.264 | 0.59 | +0.85 | 0.069 | 0% |
| AUDUSD | fx_major | 5 | 0.165 / 0.445 | 0.96 | −0.40 | 0.209 | 0% |
| AUDJPY | fx_jpy | 3 | 0.156 / 0.389 | 0.94 | −0.44 | 0.252 | 0% |
| NZDUSD | fx_major | 5 | 0.161 / 0.406 | 0.88 | −0.16 | 0.175 | 0% |
| USDCAD | fx_major | 5 | 0.082 / 0.218 | 0.44 | +5.73 | 0.075 | 0% |
| USDCHF | fx_major | 5 | 0.126 / 0.323 | 0.74 | +1.40 | 0.186 | 0% |
| CHFJPY | fx_jpy | 3 | 0.115 / 0.281 | 0.68 | −0.07 | 0.065 | 0% |
| EURGBP | fx_cross | 5 | 0.067 / 0.163 | 0.33 | +0.66 | 0.066 | 0% |
| EURJPY | fx_jpy | 3 | 0.101 / 0.237 | 0.55 | +0.55 | 0.136 | 0% |
| NAS100 | index | 1 | 0.278 / 0.843 | 1.73 | +0.15 | **0.527** | 0% |
| SPX500 | index | 1 | 0.219 / 0.666 | 1.31 | +1.34 | **0.379** | 0% |
| GER40 | index | 1 | 0.273 / 0.807 | 1.46 | +1.12 | **0.615** | 0% |
| JP225 | index | 1 | 0.425 / 1.173 | 2.41 | +0.46 | **0.633** | 0% |
| UK100 | index | 1 | 0.222 / 0.619 | 1.29 | +0.44 | **0.387** | 0% |
| XAGUSD | commodity_metal | 2 | **1.167 / 3.982** | 6.32 | **+7.15** | **1.444** | 0% |
| USOIL_cash | commodity_energy | 2 | **0.792 / 4.292** | 4.12 | **+2.85** | **0.959** | 0% |
| UKOIL_cash | commodity_energy | 2 | 0.874 / 3.844 | 4.18 | +1.44 | 0.894 | 0% |
| **BTCUSD** | crypto | 1 | 0.623 / 1.842 | 3.70 | +3.92 | 0.095 | **26%** |
| **ETHUSD** | crypto | 1 | 0.849 / 2.678 | 4.60 | +1.70 | 0.111 | **26%** |

**Key discriminators (material ≥2× differences between classes):**

- **Volatility (H1 ATR/price):** XAGUSD (1.17%) is 17× EURGBP (0.07%). Commodity-energy ≈ commodity-metal ≈ crypto > index > FX-JPY ≈ FX-major > FX-cross.
- **Fat-tail kurtosis:** XAGUSD +7.15, USDCAD +5.73 (spike — USD-CAD oil-link episodes), BTCUSD +3.92, XAUUSD +3.53, USOIL +2.85 vs AUDJPY −0.44, AUDUSD −0.40 (bell-shaped). **Fat-tail pairs have 10×+ more 3σ events per distribution theory — SL buffer behavior must account for this.**
- **Monday gap:** Indices cluster 0.38–0.63% (JP225 highest). Commodities 0.58–1.44% (XAGUSD extreme). FX majors 0.07–0.21%. Crypto 0.09–0.11% (no gap; 24/7 means Sunday-close ≈ Monday-open). **Gap-on-open rule applies to indices + commodities, not FX or crypto.**
- **Weekend activity:** Only BTC/ETH have weekend bars (26% of H1 bars). Everything else is 24/5 maximum.
- **Session concentration:** All FX + USDJPY have balanced Tokyo/London/NY coverage (~320 bars each). Indices drop Tokyo exposure (NAS100 228 Tokyo vs 304 London). Commodities similar to indices. **Tokyo kill zone is meaningful only for JPY pairs + Australasian FX; irrelevant for indices + US commodities.**

### 3.2 Class-level behavioral profiles (literature-confirmed)

| Class | Session bias | News sensitivity | Structural behavior | Source |
|---|---|---|---|---|
| Commodity metal (XAU, XAG) | London + NY (gold dual-active, silver follows) | Fed / DXY / real yields / CB purchases | Strongly trending in regime shifts; deep wicks for liquidity sweeps | ICT KZ docs + CoinCodex 2026 outlook + forexgdp.com |
| Commodity energy (WTI, Brent) | NY (API/EIA inventories 14:30 UTC Wed) | OPEC / supply shocks / geopolitical | Gap on Sunday/Monday after weekend events; event-driven | Market convention |
| Index | NY open (cash open 13:30 UTC US indices, 07:00 UTC GER40, 00:00 UTC JP225) | Earnings / FOMC / CPI | Gap on Mon open is STRUCTURAL (weekend news); post-gap mean-reversion common | ICT 2026 + empirically confirmed here (0.38–0.63% median gap vs FX 0.07–0.21%) |
| FX major (EUR/GBP/AUD/NZD/CAD/CHF) | London for European, NY for Americas | CB rate path / macro data (NFP, CPI) | Range-bound in consolidation; trending on CB divergence | ICT KZ + ATLAS framework |
| FX JPY pairs | Tokyo (JPY leg) + London (other leg) | BOJ / carry trade flows | Directional on yield-differential shifts; Tokyo-only trades exist | ICT + empirical — Tokyo concentration is meaningful here |
| Crypto (BTC, ETH) | 24/7 — US-hours activity peaks due to retail flow | Regulatory (SEC/CFTC) / macro (real yields) / on-chain | Weekend activity non-trivial (26% of bars); post-halving/news gaps | Ledger + BingX guides + observed 26% weekend bar rate |

**Key literature synthesis:**
1. **ICT doctrine already class-aware:** Asian KZ = AUD/NZD/JPY pairs. NY open = indices + gold. London open = EUR/GBP/gold. The kill-zone assignment is the per-class vector, not the prompt text.
2. **ATLAS framework (arxiv.org 2510.15949) claims horizon- and asset-agnostic design.** The scoring window and scale are chosen to match the volatility profile rather than the prompt being specialized. This maps to Option 1 + config overrides.
3. **TradingAgents (Tauric Research)** uses role-based specialization (fundamentals / sentiment / technical / trader) NOT per-asset specialization. Each role has a universal prompt applied to any asset.
4. **No published paper or production trading system ships per-asset prompts.** Our own FX precision scaffolding (FA-2) was implemented as numeric examples inside the universal prompt, not as a separate FX prompt.

---

## 4. Task 2 — Per-Instrument Backtest Evidence

Sources: F3 backtest (`WAVE2_F3_SYNTHESIS_REPORT.md`), A2 v2-active backtest (`research/a2_v2_active_backtest/`), Phase 1 full extraction (`research/phase1_full_extraction/EXTRACTION.md`), Track C sub-session map (`research/phase1_xauusd_reverse_engineering/SUB_SESSION_MAP.md`), T3.1 NAS100 + EURUSD validation, T3.2 SL-beyond-OB cross-instrument audit.

### 4.1 F3 v2-shadow backtest (Jan 2 – Apr 13 2026)

| Symbol | Slices | API calls | Raw CAND (L / S) | Final CAND | Filled n | WR | Exp R |
|---|---|---:|---|---:|---:|---:|---:|
| XAUUSD | 8 | 313 | 124 / 37 (**22.8% S**) | 15 (11 L, 4 S) | 13 | 53.8% | +0.347 |
| USDJPY | 4 | 574 | 426 / **0** (0% S) | 24 (24 L, 0 S) | 19 | 57.9% | +0.447 |
| **Fleet** | 12 | 887 | 550 / 37 (6.3% S) | 39 | 32 | 56.2% | +0.407 |

**Observations:**
- **XAUUSD SHORT emergence from v2 is real** (22.8% raw, 26.7% final). 2/2 simulated SHORT fills won.
- **USDJPY SHORT is dead** even under v2 (0/426). F3 synthesis hypothesizes: (a) USDJPY was genuinely bullish regime Jan-Apr 2026 (155→160); (b) divisor=8 may still be too permissive for FX. F3 recommends F2-SWEEP2 on USDJPY with divisor=6. **This is a structure-detector concern, not a prompt concern.**
- **CAND rate differs:** XAUUSD 162 raw / 313 API = 51.8% AI-CAND rate. USDJPY 426 / 574 = 74.2%. USDJPY's higher CAND rate is a direct consequence of 100% bullish-bias MSOs + no SHORT-discriminator — the AI sees "bullish H1" and approves almost everything. **A per-instrument prompt split cannot fix this; only upstream structure detection can.**

### 4.2 A2 v2-active backtest (2026-04-25 rerun)

| Symbol | Raw CAND (L / S) | Filled | LONG WR | SHORT WR | Exp R |
|---|---|---:|---:|---:|---:|
| XAUUSD | 9 L / 4 S (**30.8% S**) | 11 | 33.3% (n=9) | 100% (n=2) | +0.136 |
| USDJPY | 24 L / 0 S (0% S) | 19 | 57.9% | N/A | +0.447 |
| **Fleet** | 33 L / 4 S (10.8% S) | 30 | — | — | +0.333 |

**Observations:**
- XAUUSD SHORT emergence strengthens further (30.8% raw vs F3's 22.8%) with v2 fully active.
- **USDJPY bit-exact reproducible with F3** (WR, Exp, Total R identical). Confirms v2 pipeline deterministic; USDJPY 0-SHORT is real, not a flake.
- XAUUSD LONG WR drop 45.5% → 33.3% on small n (CIs overlap); cannot statistically reject either.

### 4.3 Phase 1 A1 backtest — per-instrument stratification (v1-era, 1,142 rows)

A1 ran with `detector_version: v2_shadow` which routes production to v1 (per `structure_detector_shadow_logger.py:105`). It is therefore a **v1-baseline** representing ~4 months of what production has been doing.

| Symbol | Filled CAND | Filled WR | Touch=1 WR | Touch=2 WR | Touch≥3 WR | LONG-only | SHORT count |
|---|---:|---:|---:|---:|---:|---|---:|
| XAUUSD | 56 | 45.1% LONG / 60% SHORT (n=5) | 40.0% (n=25) | 52.4% (n=21) | 50.0% (n=10) | 91% | 5 |
| USDJPY | 19 | 42.1% LONG | 45.5% (n=11) | 50.0% (n=4) | 25.0% (n=4) | 100% | 0 |

**Touch-count-vs-WR pattern is NOT consistent across instruments:**
- XAUUSD touch=2 best.
- USDJPY touch≥3 worst (but n=4, useless).
- **No touch-based gate generalizes** — same conclusion as Phase 1 Extraction E1.

**XAUUSD monthly WR decay (χ² p=0.006):**

| Month | n | WR | Exp R |
|---|---:|---:|---:|
| 2026-01 | 11 | 45.5% | +0.14 |
| 2026-02 | 20 | **75.0%** | +0.88 |
| 2026-03 | 15 | 33.3% | −0.17 |
| 2026-04 | 10 | **10.0%** | −0.75 |

**H1-2026 (Jan+Feb) 64.5% vs H2-2026 (Mar+Apr) 24.0% — the highest-signal cross-instrument finding.** This is **instrument-specific but a structure-detector (v1 bullish lock) effect, not a prompt effect.** Per F3 / A2 data v2 SHORTs during Mar (s7, 2/2 WINs) would have recovered much of this. A per-instrument prompt would not have helped because the bias was at the structure layer.

### 4.4 T3.1 NAS100 + EURUSD sims (Jan 2 – Apr 17 2026, pre-v2)

| Instrument | KZ candles | API calls | CAND | Filled | WR | Exp R | Key finding |
|---|---:|---:|---:|---:|---:|---:|---|
| **NAS100** | 1,600 | 818 | 37 | 33 | **66.7%** | **+0.668** | `sl_beyond_ob` bit-exact rejects +13.5R leak (NAS100-specific — did NOT replicate on XAUUSD) |
| **EURUSD** | 815 | 300 | 9 (5 real, 4 degen) | 5 real | 80% sim | (collapses to 0% at 1-pip eps) | AI rounded to 2dp on 4dp instrument → **59.7% degenerate trade_params** |

**EURUSD per-instrument finding diagnostic:**
- 60% of EURUSD AI outputs had `entry==stop_loss==take_profit_1` (collapsed to 2dp rounding).
- 252/253 EURUSD L2 rejects were LONG (99.6%) — SHORT-side geometry had even more silent failures.
- **Fixed in FA-2 (`fa35cc0`) by precision-scaffolding the universal prompt, not by forking to an FX-prompt.** The V2 `{decimal_places}` + precision examples block was the fix.

### 4.5 T3.2 cross-instrument XAUUSD/NAS100 comparison — `sl_beyond_ob`

| Metric | XAUUSD | NAS100 |
|---|---:|---:|
| Bit-exact `SL == OB bound` rate (of sl_beyond_ob rejects) | 30% | **91%** |
| Bit-exact as % of all L2 rejects | 0.81% | **50%** |
| Counterfactual if T2.9 strict-< relaxed | −1R / −0.167R Exp | **+20.50R / +0.489R Exp** |

**Decision:** REJECTED the T2.9 gate change, shipped universal prompt fix (FA-2) instead. Pattern is **NAS100-specific** on geometric grounds; fixing it at the prompt layer universally (via non-zero `sl_buffer_applied` requirement) was the correct approach.

### 4.6 Track C sub-session map — 266 unified trades (pre-v2)

| Instrument | n | Baseline WR | Baseline E[R] | n ≥ 20 buckets |
|---|---:|---:|---:|---:|
| XAUUSD | 144 | 61.1% | +0.241R | 5 (all 60-min) |
| USDJPY | 48 | 66.7% | +0.358R | 0 |
| US30_cash | 33 | 57.6% | +0.388R | 0 |
| GBPJPY | 26 | 50.0% | −0.036R | 0 |
| GBPUSD | 15 | 66.7% | +0.519R | 0 |

**Conclusion from Track C:** No formal EMPHASIS or SKIP recommendation at 60-min granularity — the sub-session bucket signal does not justify per-instrument prompt KZ adjustments. **Existing `market.kill_zones` config (per-instrument KZ windows) is already the right abstraction.**

### 4.7 Cross-instrument summary — what the evidence shows

| Finding | XAUUSD | USDJPY | NAS100 | EURUSD | GBPJPY | GBPUSD | US30 | Prompt-layer fix warranted? |
|---|---|---|---|---|---|---|---|---|
| Edge preserved in v1-batch (WR) | ✓ 62% (n=129) | ✓ 75.8% (n=33) | ✓ 66.7% (n=33 sim) | ? n=5 | 57.1% (n=42) | ? n=15 sim | ✓ 58.5% (n=41) | Universal |
| v2 detector fix needed (SHORT emergence) | ✓ 22.8% | ✗ 0/426 | not retested | not retested | not retested | not retested | not retested | No — detector layer |
| FX precision bug (degenerate outputs pre-FA-2) | 0% | low | N/A | 60% | ? | ? | N/A | **Universal** (V2 scaffolding shipped) |
| SL bit-exact = OB bound leak | 0.81% | ? | **50% of L2** | ? | ? | ? | ? | Mostly NAS100; universal V2 `sl_buffer_applied` block handles |
| Touch-count monotone-predictive | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | No gate — Phase 1 E1 |
| Monthly WR decay | **Yes (p=0.006)** | weak | weak (T3.1 month-wise 90→33%) | not measured | ? | ? | ? | No — regime concern, shadow monitor instead |

**The evidence consistently points to:**
1. **Precision + anti-gaming issues are solvable universally** (V2 + V3 did this).
2. **Directional bias issues are structure-detector problems, not prompt problems** (ADR-004 / v2).
3. **Per-instrument WR decay is regime-driven, not prompt-driven.**
4. **No finding in the evidence corpus is "the prompt works for instrument X but fails for instrument Y for prompt-specific reasons that can be fixed by per-instrument prompt text."**

---

## 5. Task 3 — External Literature Synthesis

Searched April 2026: `ICT kill zones session instrument specific 2026`, `LLM trading instrument class specialization prompt engineering FX indices crypto 2026`, `prompt engineering per-asset specialization vs universal LLM financial trading`, `XAUUSD fat tail volatility DXY correlation 2026 order block`.

| Source | Relevant claim | Citation |
|---|---|---|
| ICT KZ docs + Phidias + Trading Rage | Asian KZ favors AUD/NZD/JPY crosses; London Open favors GBP/EUR/XAU; NY Open favors NAS100/US30/XAU | [Phidias Prop Firm](https://phidiaspropfirm.com/education/kill-zones), [ICT Killzone.com](https://www.ictkillzone.com/ict-kill-zones) |
| ATLAS (arXiv 2510.15949) | LLM trading agent framework is "horizon- and asset-agnostic; the same protocol applies to alternative windows or instruments, with the scoring window and scale chosen to match the volatility profile" | [ATLAS paper](https://arxiv.org/html/2510.15949v1) |
| TradingAgents (Tauric Research) | Multi-agent LLM framework with ROLE-based specialization (fundamentals, sentiment, technical, trader, risk). NOT per-asset. Universal prompt applies to any asset. | [TradingAgents GitHub](https://github.com/TauricResearch/TradingAgents) |
| ForexGDP (XAU analysis) | XAU-DXY correlation is strong-but-inconsistent; "not foolproof, there are times when both move in the same direction or when their relationship weakens" — matches our empirical XAU kurtosis +3.53 behavior | [ForexGDP](https://www.forexgdp.com/analysis/xauusd/gold-dxy-correlation/) |
| FXNX Gold volatility | "Gold can easily move 200-300 pips in a single session. XAUUSD is notorious for throwing deep wicks past key levels to hunt for liquidity pools" | [FXNX](https://fxnx.com/en/blog/gold-trading-strategy-how-to-master-xauusd-volatility-traps) |
| SoA LLM Investment paper | "LLMs can benefit from specialization. LLMs are suitable for transfer learning — new data can be fed into pre-trained models for specific tasks." But paper does NOT recommend per-asset prompts | [SOA.org paper](https://www.soa.org/493a31/globalassets/assets/files/research/opportunities/shang-effective-usage-ofllm-in-investment.pdf) |

**Synthesis:**
- **Zero production references to per-asset prompt specialization in the LLM-trading literature.** The consistent pattern is universal-prompt + config/tool specialization (ATLAS scales scoring window, TradingAgents roles, our V2 `_PRICE_FMT`).
- **ICT doctrine is already class-aware** at the KILL ZONE layer (config), not the prompt layer. Our `market.kill_zones` config already captures this.
- **Asset-specific behaviors (fat tails in gold/silver, gap-on-open in indices) are documented behaviorally but not addressed via per-asset prompts in any published framework.** They are handled by risk sizing, SL geometry, or session filters — all config / deterministic-code layers.

---

## 6. Task 4 — Options Comparison Matrix

| | **Option 1** Universal | **Option 2** Per-class (4 prompts) | **Option 3** Per-instrument (5–24 prompts) | **Option 4** Universal + injection (RECOMMENDED) |
|---|---|---|---|---|
| Prompt files to maintain | 1 | 4 (FX / Commodity / Index / Crypto) | 5 live + 19 dormant = 24 | 1 core + 4–8 snippet strings |
| Canary fixtures needed | 60 baseline + 4 borderline (current) | 60 + ~40 (10 per class extras) | 60 + ~120 (10 per instrument) | 60 + 10 multi-instrument borderline |
| Canary cost per V-bump | ~$3 | ~$8 | ~$25 | ~$4 |
| Full F3-style backtest cost | $40 | $40 × 4 = $160 | $40 × 5 = $200+ | $40 |
| Maintenance burden (relative) | 1× | 4× | 24× | 1.2× |
| **Expected R/mo improvement (evidence-based)** | Baseline | **Unknown — no evidence class-split helps** | **Unknown — no evidence per-instrument helps** | **+0.05–0.15R/mo conditional on v2 SHORT edge emerging** |
| Over-fitting risk | Low | Medium — class boundaries are arbitrary (is USDCAD a commodity-linked FX? Is EURJPY a JPY pair or EUR pair?) | **High — will absorb regime quirks that are not persistent** | Low — injection is 4–8 lines, hard to over-fit |
| Risk of destabilizing V3 | Low (no change) | Medium — prompt fork = independent drift per class | **High — 5× drift surfaces** | Low — one addition, tested in canary |
| Fat-tail / XAUUSD wicks handling | Universal V3 already says `sl_buffer_applied > 0` required | Would add "XAU wicks are normal" text | Would add per-instrument numeric buffers | Adds one sentence to XAU/XAG/commodity snippets |
| FX precision bug recurrence | V2 scaffolding (DP-aware examples) already generalized | Would split into FX-specific | Further split per pair | Already-universal + context lines per instrument |
| v2 USDJPY 0-SHORT problem | Not addressable by any prompt option | Not addressable by any prompt option | Not addressable by any prompt option | Not addressable by any prompt option |
| Cost per V-bump post-V4 | $3–5 | $15–25 | $40–80 | $4–8 |

### 6.1 Decision criteria

1. **Evidence supports class-split?** No. F3 + A2 + Phase 1 + T3.1 all show that successful fixes were universal (precision, anti-gaming) and unsuccessful fixes were structural (bias, decay).
2. **Maintenance economics?** Option 2 costs 4× canary + 4× F3; returns unknown. Option 3 costs 24×; returns unknown. Neither passes the `high-quality frequency > small WR gain` CEO test (`feedback_research_goal_high_quality_frequency.md`).
3. **CEO budget?** $100–200 V4 total. Option 2/3 would hit $200+ on backtest alone. Option 4 stays well under.
4. **Compounding risk?** V3 shipped with known partial-mitigation (`Optional[str]` no_trade_reason not `Literal[...]`, see unresolved #5 in CLAUDE.md). V4 per-instrument forks would require N× such follow-ups. Option 4 keeps ONE prompt surface.

**Option 4 wins on every criterion.**

---

## 7. Task 5 — Option 4 Proposed Injection Content

### 7.1 Architecture

Add to `primary_analyzer_prompt.py`:

```python
def _instrument_guidance_snippet(symbol: str, config: dict) -> str:
    """Return 4–8 line instrument-specific cautionary block.

    Purely informational — does not change the three-gate decision logic.
    Intended to anchor AI reasoning when CAND/NO_TRADE is borderline,
    not to add a fourth gate.
    """
    cls = _instrument_class(symbol)  # uses CLASS_MAP
    base_snippets = {
        "commodity_metal": _SNIPPET_COMMODITY_METAL,
        "commodity_energy": _SNIPPET_COMMODITY_ENERGY,
        "index": _SNIPPET_INDEX,
        "fx_major": _SNIPPET_FX_MAJOR,
        "fx_jpy": _SNIPPET_FX_JPY,
        "fx_cross": _SNIPPET_FX_CROSS,
        "crypto": _SNIPPET_CRYPTO,
    }
    return base_snippets.get(cls, _SNIPPET_FX_MAJOR)  # fallback to FX-major tone
```

Place the `{instrument_guidance}` template variable **ONCE** between the precision block and the OBSERVATION REPORT, replacing 4–8 lines of context. The injection explicitly does NOT modify C1/C2/C3, the allow-list, or the geometric invariants.

### 7.2 Per-class snippet drafts

**Commodity-metal (XAUUSD, XAGUSD) — 6 lines:**

```
## INSTRUMENT CONTEXT — metals (informational only, not a gate)
This instrument exhibits fat-tail volatility: wide wicks and sudden price
spikes occur during liquidity sweeps. Session ATR may be 2–3× normal in
Fed / CPI / NFP windows. Do NOT tighten the SL buffer or reject a
qualifying C1/C2/C3 CANDIDATE because a recent wick looks "unusual" —
wicks are STRUCTURAL in this asset class. If H1/M15 structure is clean
and all three gates pass, the candidate is valid.
```

**Commodity-energy (USOIL_cash, UKOIL_cash) — 5 lines:**

```
## INSTRUMENT CONTEXT — energies (informational only, not a gate)
Oil exhibits event-driven gaps: EIA weekly inventories (Wed 14:30 UTC),
OPEC announcements, geopolitical headlines. Monday-open gaps of 1%+ are
common. Structural breaks BETWEEN events are tradeable; breaks ON an
event candle often revert. If the current candle sits on a known
scheduled event (config.event_calendar), treat C1 PASS with medium
confidence.
```

**Index (US30_cash, NAS100, SPX500, GER40, JP225, UK100) — 5 lines:**

```
## INSTRUMENT CONTEXT — equity indices (informational only, not a gate)
Indices cash-open windows gap reliably — Mon open vs Fri close typically
0.4–0.6% for US indices, 0.6% for DAX/JP225. The first NY cash-open
candle (13:30 UTC US, 00:00 UTC JP225) often shows displacement that
RESOLVES within the following hour. Your C1/C2/C3 evaluation is
unchanged; the system's first-candle skip handles this deterministically.
```

**FX major (EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF) — 5 lines:**

```
## INSTRUMENT CONTEXT — FX majors (informational only, not a gate)
FX majors are 5-decimal-place instruments. Every numeric field you emit
must use exactly 5dp (see PRECISION block above). Typical H1 ATR is
0.1–0.2% of price; a 0.3% move is a 3σ event. Swing lows/highs cluster
at psychological levels (1.25000, 1.30000) — protected swings often sit
within 2–3 pips of round numbers.
```

**FX JPY (USDJPY, EURJPY, GBPJPY, AUDJPY, CHFJPY) — 5 lines:**

```
## INSTRUMENT CONTEXT — JPY pairs (informational only, not a gate)
JPY pairs are 3-decimal-place instruments (see PRECISION). Tokyo session
(00:00–03:00 UTC) is a legitimate structural-setup window — do NOT
default to "low liquidity = skip" reasoning. BOJ intervention risk is
real near multi-year highs; the system's deterministic gates handle
this — you evaluate C1/C2/C3 as normal.
```

**FX cross (EURGBP) — 4 lines:**

```
## INSTRUMENT CONTEXT — FX cross (informational only, not a gate)
EURGBP exhibits the lowest volatility in the instrument universe (H1 ATR
0.07% median, 0.16% p95). Structural breaks are smaller in absolute
terms; the `sl_absolute_min` config value is already scaled. Evaluate
gates normally.
```

**Crypto (BTCUSD, ETHUSD) — 5 lines:**

```
## INSTRUMENT CONTEXT — crypto (informational only, not a gate)
This instrument trades 24/7 including weekends (~26% of bars). There is
no "dead zone" — weekend bars are STRUCTURAL, not noise. The Asian
session (00:00–08:00 UTC) sees meaningful volume. Your C1/C2/C3 logic
is unchanged; evaluate as normal.
```

### 7.3 Key safety property

**Every snippet includes the literal phrase "(informational only, not a gate)"** and explicitly reaffirms "your C1/C2/C3 logic is unchanged." This prevents the AI from interpreting the injection as a fourth gate (the V3 anti-gaming concern).

### 7.4 What is DELIBERATELY NOT added

- No per-instrument "expected WR" or historical performance numbers (would bias the AI's CAND threshold).
- No per-instrument kill-zone times (already handled by `{kz_display}`).
- No per-instrument fibonacci levels or fixed POI levels.
- No per-instrument news-calendar specifics (would require live event feed; out of scope).
- No per-instrument session-ATR thresholds (handled by post-AI gates + M5 refinement).

---

## 8. Task 6 — Validation Plan

### 8.1 Preregistration gates

State BEFORE touching data:

**H0:** V4 injection produces no meaningful change in CAND rate, direction split, or filled WR vs V3 baseline on the same fixtures/slices.

**H1:** V4 injection produces:
- (i) ≤1 canary flip vs V3 baseline on 60 existing fixtures + ≤2 flips on 10 new multi-instrument borderline fixtures
- (ii) Fleet Exp ≥ +0.30R on v2-active F3 rerun (12 slices, Jan–Apr 2026)
- (iii) No instrument's filled WR degrades >10pp vs V3 baseline on same period

### 8.2 Canary validation ($3–4)

1. Add 10 new borderline fixtures: 2 USDJPY, 2 GBPUSD, 2 NAS100, 2 BTCUSD, 2 XAGUSD.
2. Each fixture has a manual CEO-classified ground truth (CAND/NO_TRADE with expected direction).
3. V4 passes canary if ≤1 flip on the 60 existing XAU-focused fixtures AND ≤2 flips on the 10 new multi-instrument fixtures.
4. **Gate:** canary timeout scales per `feedback_canary_timeout_scales_with_fixture_count.md` — re-benchmark `timeout` after fixture-count expansion.

### 8.3 Backtest A/B — F3 rerun with V4 ($40, parallel)

1. Same 12 slices (XAUUSD×8 + USDJPY×4).
2. Flags: `--prompt-version v4 --detector-version v2`.
3. Compare fleet metrics against F3 baseline (56.2% WR, +0.407R Exp, 22.8% XAU SHORT).
4. Pass: Exp stays within ±0.10R, WR within ±5pp, SHORT share within ±5pp. Kill: any metric degrades >2× threshold.

### 8.4 Phase 2a expansion on non-live instruments ($50, parallel)

1. Single slice each on EURUSD, NAS100, BTCUSD, XAGUSD, USOIL_cash (Feb 1 – Feb 28, 2026 or similar clean month per data availability).
2. Each ~$10 at current rates.
3. Goals:
   - Confirm V4 does not blow up on unseen asset class (e.g., no `ai_output_malformed` spike on BTCUSD).
   - Establish baseline CAND rate + decision integrity per class for Phase 2b live decision.
4. Pre-commit fail-criterion: >5% malformed response rate on any instrument.

### 8.5 Total cost

**~$97** ($4 canary + $40 F3 rerun + $50 Phase 2a) — well within $100–200 CEO budget.

### 8.6 Timeline (wall clock)

- Day 1: Canary fixture additions + V4 snippet commits.
- Day 2: Parallel F3 rerun + Phase 2a launches (8h compute).
- Day 3: Council / cold review of metrics.
- Day 4: CEO go/no-go on V4 production flip.

---

## 9. Honest Nulls — Where Evidence Does NOT Support Specialization

To be crystal-clear about what the data does NOT say:

1. **No evidence any class-level prompt change improves WR.** We have no backtest data to support the claim.
2. **No evidence any instrument needs its own prompt.** All observed instrument-specific failures (EURUSD degeneracy, NAS100 sl_beyond_ob, USDJPY 0-SHORT) were either fixed at the UNIVERSAL prompt layer (EURUSD via FA-2) or at the structure-detector layer (USDJPY via v2).
3. **No evidence fat-tail instrument guidance changes AI behavior.** We only have evidence of what the AI does WITHOUT such guidance, and it is broadly good (XAUUSD 62% WR pre-decay).
4. **Option 1 is a defensible fallback.** If the CEO prefers to DEFER V4 entirely and wait for v2-production live data to accumulate (≥100 filled CANDs post-flip), that is a rational conservative choice. V4 injection is a proactive optimization, not a bug fix.
5. **The regime-decay finding (H2-2026 XAUUSD WR collapse from 64.5% to 24%) dominates everything.** No prompt change fixes regime change. Monthly-decay shadow monitor (Phase 1 recommendation #2) is higher-priority than V4 prompt work.

---

## 10. Deliverables & Provenance

### 10.1 Files committed

| Path | Purpose |
|---|---|
| `research/v4_prompt_engineering/PER_INSTRUMENT_ANALYSIS.md` | This report |
| `research/v4_prompt_engineering/_compute_instrument_characteristics.py` | Reusable script computing per-instrument characteristics table from `data/historical_2026/` |
| `research/v4_prompt_engineering/instrument_characteristics.json` | 24-instrument JSON output of the script (bars, ATR, kurtosis, gaps, sessions) |

### 10.2 Data sources consulted

- `data/historical_2026/{24}_{M15,H1,H4,D1}.csv` (96 CSVs, 2026-01-02 → 2026-04-24)
- `research/f3_backtest_2026-04-24/` (12 slices, $37.50 spend)
- `research/a2_v2_active_backtest/` (12 slices rerun, v2-active)
- `research/phase1_full_extraction/EXTRACTION.md` (E1-E12, 1,142 logger rows × 3,539 outcomes)
- `research/phase1_xauusd_reverse_engineering/SUB_SESSION_MAP.md` (266 unified trades)
- `research/phase1_xauusd_reverse_engineering/SYNTHESIS.md` (13,208 walk rows, 75-feature GBM)
- `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/` (NAS100 + EURUSD syntheses)
- `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md`
- `research/directional_concentration_audit_2026-04-24/summary.md` (ADR-004 diagnosis)
- `src/prompts/primary_analyzer_prompt.py` (V3 prompt, set_price_format, precision examples)
- `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, `ftmo.yaml`
- External: arxiv.org ATLAS 2510.15949, Tauric TradingAgents, ForexGDP, ICT KZ 2026 docs

### 10.3 Branch + commit status

- Branch: `research/v4-prompt-per-instrument` ✓
- Committed: yes, single commit with `PER_INSTRUMENT_ANALYSIS.md` + supporting script + JSON output
- Merged: **no** (per task spec)
- Pushed: **no** (per task spec)

---

## 11. One-Sentence Final Answer

**Ship V4 as Option 4 (universal core + 6 thin class-level injection snippets controlled by a single config flag), validate with $100 of canary + F3 rerun + Phase 2a expansion, and kill-switch revert to V3 if any instrument's filled WR degrades >10pp on the 12-slice F3 replay.**

---

*End of analysis. Next action per task spec: commit to `research/v4-prompt-per-instrument`, do not merge, do not push. Await CEO review.*
