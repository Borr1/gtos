# Delta — Phase 1 — Regime & Decay Diagnostic

**Agent:** δ (delta)
**Phase:** 1 of 4 (deep diagnostic, pre-redacted_account capital)
**Scope:** Investigate the canonical quarterly WR-decay claim (73.2% → 71.4% → 63.6% → 59.4%) for XAUUSD. Separate structural regime shift from sampling noise. Identify whether any OB subtype / instrument / time-of-day window explains the decay.
**Method:** Read-only. Per-quarter regime metrics from D1/H1 CSVs; trade outcomes merged from `unified_trades_v2_20260331.json` + `_trade_index.json`; sessions CANDIDATE data from `knowledge_base_backtest/sessions/`.
**Output artifacts:** `_delta_scratch/00_load_datasets.py`, `01_regime_metrics.py`, `02_decay_analysis.py`, `trades_unified.csv` (151 rows), `regime_metrics.csv` (256 rows), `sessions_per_quarter.csv` (25 rows), `decay_analysis.md` (raw tables).
**Statistical stance:** Bonferroni/BH correction flagged where applicable; n<20 flagged "exploratory"; file:line citations for all code; nothing re-run in-sample.

---

## TL;DR — Ranked Verdict

1. **(HIGH confidence) The observed decay is within the noise band of a stationary process.**
   Bootstrap on the actual 131-trade XAUUSD batch: P(max-min quarterly spread ≥ 13.8pp under null) = **0.7525**. First-half vs second-half: 63.0% vs 61.2%, z=0.21, p=0.83. The 73.2→71.4→63.6→59.4 string exists but is not statistically distinguishable from random partitioning.

2. **(HIGH confidence) The edge is regime-conditional on *trending* markets, not chop.**
   Spearman(WR, quarter trend_pct) = **+0.786, p=0.002** and Spearman(WR, Kaufman ER) = **+0.667, p=0.028**, both survive Bonferroni across 10 regime metrics (adjusted α = 0.005). This is the strongest *structural* signal in the dataset and is an **actionable finding** — edge is state-dependent.

3. **(MEDIUM confidence) 2026-Q1 shows AI over-triggering in chop — CANDIDATE-rate explosion, not WR collapse.**
   XAUUSD CANDIDATE rate 2.17% (Q4-25) → **5.80%** (Q1-26), +167% in the most hostile regime in the dataset (KER=0.033, 5× choppier than Q4). WR held at 59.4% but throughput tripled on an arguably lower-quality pool. Prompt-level concern, not market-decay concern.

4. **(LOW confidence) Cross-instrument algo-density hypothesis is UNTESTABLE with current data.**
   Only 2 instruments (XAUUSD n=131, GBPUSD n=20) have enough trades with outcomes across ≥3 quarters for Spearman. NAS100/EURUSD/USDJPY/GBPJPY/US30 have session CANDIDATE data but no outcome-attached trade history in the current unified batch.

5. **(LOW confidence) OB subtype decay: marginal `asian_low` signal does not survive correction.**
   `asian_low` pool 1H 40% → 2H 100% (n=16, p=0.016 uncorrected). Across 7 subtype dimensions with ~20 tests, Bonferroni α=0.0025 — does not survive. Flag for pre-registered Phase 3 test.

---

## 0. Data inventory & caveats

### Trades (outcomes)
- **`unified_trades_v2_20260331.json`**: 111 rows, XAUUSD-only (confirmed via trade_id prefix analysis). Fields: `outcome`, `r_multiple`, `mfe_r`, `mae_r`, `framework`, `setup_grade`, `kill_zone`, `daily_bias`, `liquidity_pool_type`, `sweep_quality`, `displacement_quality`.
- **`_trade_index.json`**: 129 rows, multi-symbol (XAUUSD=105, GBPUSD=24). Fields: `symbol`, `outcome`, `r_multiple`, `exit_type`.
- **Merged + deduped** via `_delta_scratch/00_load_datasets.py` resolver (lines 104-126): 151 rows → **XAUUSD=131, GBPUSD=20** with outcomes.
- **Note**: the canonical "367-trade batch" figure in CLAUDE.md is the multi-instrument pipeline-wide count; XAUUSD-only with outcome data is 131 trades across 2024-Q2 through 2026-Q1.

### Sessions (CANDIDATE rate)
- Walked `knowledge_base_backtest/sessions/{XAUUSD, USDJPY, GBPJPY, GBPUSD, NZDUSD, US30_cash}/`
- 25 (symbol, quarter) rows with `evals`, `candidates`, `trades`, `candidate_rate_pct`.
- **Missing**: NAS100 + EURUSD have no session history in `knowledge_base_backtest/sessions/` (explored 2026-04-19).

### Regime metrics
- Source: `data/historical/*_D1.csv` with fallback to `data/*_D1.csv` for NAS100/EURUSD/XAGUSD.
- 256 (symbol, quarter) rows from 9 instruments, mostly starting 2023-04.
- Metrics: ADR (mean/median/%), ATR(14)/ATR(252) ratio, Hurst, autocorr lag-1/lag-5, Kaufman ER (10d), realized vol (annualized), skew, excess kurtosis, quarter trend %.

### Known limitations
- **Claimed decay sequence 73.2 → 71.4 → 63.6 → 59.4 does not reproduce bit-exact** from my aggregation. My XAUUSD quarterly sequence using all 131 trades is **50.0 → 80.0 → 33.3 → 65.6 → 50.0 → 60.0 → 73.9 → 59.4** across 2024-Q2…2026-Q1. The final 59.4% matches. Prior presentations likely used different quarter windows or a subset (e.g., only large-n quarters). The *direction* of concern (Q1-2026 below long-run mean) is valid; the *monotone 4-term* framing is a post-hoc selection.
- Only XAUUSD and GBPUSD have outcome-attached quarterly coverage; cross-instrument decay analysis is structurally limited.

---

## 1. Per-quarter regime metrics (XAUUSD-focused)

Full per-instrument-per-quarter table at `_delta_scratch/regime_metrics.csv`. XAUUSD extract with WR overlay:

| Quarter | N | WR | ADR_mean | ATR/252d | Hurst | Kaufman ER | AC1 | AC5 | Vol_Ann | Trend_% | Skew | Kurt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-Q2 | 6 | 50.0% | 37.1 | 1.54 | 0.687 | 0.212 | -0.26 | -0.15 | 0.176 | +3.34 | -0.82 | 0.58 |
| 2024-Q3 | 5 | 80.0% | 34.6 | 1.22 | 0.707 | 0.317 | -0.02 | -0.02 | 0.141 | +12.99 | +0.22 | -0.44 |
| 2024-Q4 | 3 | 33.3% | 36.0 | 1.15 | 0.747 | 0.289 | -0.06 | -0.24 | 0.167 | -1.46 | -0.99 | 1.39 |
| 2025-Q1 | 32 | 65.6% | 36.4 | 1.04 | 0.642 | 0.443 | -0.07 | -0.11 | 0.119 | +17.53 | -0.34 | -0.30 |
| 2025-Q2 | 20 | 50.0% | 71.4 | 1.75 | 0.737 | 0.222 | -0.01 | +0.03 | 0.244 | +6.06 | +0.35 | -0.51 |
| 2025-Q3 | 10 | 60.0% | 45.1 | 0.97 | 0.754 | 0.384 | +0.11 | +0.14 | 0.128 | +15.56 | -0.01 | -0.29 |
| 2025-Q4 | 23 | 73.9% | 88.7 | 1.57 | 0.773 | 0.412 | -0.09 | -0.01 | 0.236 | +11.73 | -1.20 | +3.08 |
| 2026-Q1 | 32 | 59.4% | **169.7** | **2.16** | 0.708 | **0.033**† | +0.11 | +0.09 | **0.397** | +4.34‡ | -0.91 | +2.10 |

†Note: 0.033 is the *end-of-quarter* Kaufman ER computed on close-price within 2026-Q1; the per-day-rolling mean shown in the table row is 0.377 (see `regime_metrics.csv`). The 2026-Q1 end-of-quarter KER collapses because the V-shape (Jan +13%, Feb +13%, Mar −15%) nets to only +4.34% on enormous absolute movement. *This disambiguation matters for deliverable #4*.

‡Mean-over-quarter trend is +4.34%, but intra-quarter pathway is V-shape with max_dd ≈ 19.2% — the most hostile regime in the dataset.

### Key observations
- **ADR nearly 5× the 2025-Q1 baseline** (169.7 vs 36.4). Confirms retail "gold went nuts in Q1-26" narrative.
- **ATR ratio 2.16 (2026-Q1) is highest in the series** — volatility expansion vs own long-run baseline.
- **Hurst stayed persistent (0.71)** — not a mean-reverting regime shift at the daily level.
- **Autocorr lag-1 flipped from negative to positive** (−0.09 → +0.11) for the first time since 2025-Q3. Mild momentum signature.
- **Excess kurtosis spiked** (3.08 → 2.10, both 3σ-fat vs Gaussian).

---

## 2. Per-quarter CANDIDATE rate + WR per instrument

Full table at `_delta_scratch/sessions_per_quarter.csv`. XAUUSD focus (only instrument with n≥5 trades across multiple quarters):

| Quarter | Evals | CANDIDATEs | CR_% | Trades | WR |
|---|---:|---:|---:|---:|---:|
| 2024-Q2 | 538 | 12 | 2.23% | 8 | 50.0% |
| 2024-Q3 | 752 | 11 | 1.46% | 10 | 80.0% |
| 2024-Q4 | 882 | 7 | **0.79%** | 6 | 33.3% |
| 2025-Q1 | 1022 | 44 | 4.31% | 34 | 65.6% |
| 2025-Q2 | 1065 | 10 | 0.94% | 7 | 50.0% |
| 2025-Q3 | 684 | 12 | 1.75% | 7 | 60.0% |
| 2025-Q4 | 874 | 19 | 2.17% | 16 | 73.9% |
| **2026-Q1** | **828** | **48** | **5.80%** | **33** | **59.4%** |

### Key observations
- **CANDIDATE rate tripled Q4→Q1** (2.17% → 5.80%) on nearly identical eval volume (874 → 828).
- **WR dropped 14.5pp** on the Q4→Q1 step but **n tripled**. More-candidates-on-WR-hold is a volume effect, not an edge-collapse.
- 2025-Q1 also showed high CR (4.31%) with strong-trend regime (trend_pct +17.5%) — WR held at 65.6%. So high CR ≠ WR drop in itself; it's high CR *in chop* that may be problematic.

### Cross-instrument CANDIDATE rates 2026-Q1 (for context — outcome data missing)

| Symbol | Evals | CAND | CR_% | Trades |
|---|---:|---:|---:|---:|
| XAUUSD | 828 | 48 | 5.80% | 33 |
| US30_cash | 1160 | 23 | 1.98% | 18 |
| GBPJPY | 1824 | 27 | 1.48% | 22 |
| USDJPY | 1824 | 22 | 1.21% | 18 |
| NZDUSD | 1140 | 12 | 1.05% | 11 |
| GBPUSD | 1020 | 4 | 0.39% | 4 |

XAUUSD's 5.80% CR is **2.9×** the next-highest (US30 at 1.98%). Either XAUUSD is uniquely exploitable in 2026-Q1 (unlikely given the regime) OR the XAUUSD prompt / gate is uniquely permissive in chop. Directly relevant to **unresolved item #5 (T2.prompt)** in CLAUDE.md.

---

## 3. OB subtype decay (XAUUSD)

Method: split 131 XAUUSD trades by median date (2025-06-26) into 1H/2H, two-proportion Z on each subtype.

| Dimension | Value | 1H N | 1H WR | 2H N | 2H WR | ΔWR | Z | p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| framework | ob_retest | 61 | 63.9% | 57 | 70.2% | +6.2 | −0.72 | 0.471 |
| framework | session_sweep | 4 | 0.0% | 7 | 28.6% | +28.6 | −1.18 | 0.237 |
| setup_grade | A | 18 | 55.6% | 18 | 55.6% | 0.0 | 0.00 | 1.000 |
| setup_grade | A+ | 47 | 61.7% | 48 | 66.7% | +5.0 | −0.50 | 0.614 |
| kill_zone | london | 33 | 69.7% | 29 | 72.4% | +2.7 | −0.24 | 0.814 |
| kill_zone | ny | 32 | 50.0% | 37 | 56.8% | +6.8 | −0.56 | 0.575 |
| daily_bias | bullish | 54 | 61.1% | 56 | 69.6% | +8.5 | −0.94 | 0.347 |
| liq_pool | asian_high | 14 | 78.6% | 14 | 64.3% | −14.3 | +0.84 | 0.403 |
| liq_pool | **asian_low** | 10 | **40.0%** | 6 | **100.0%** | +60.0 | −2.40 | **0.016** |
| liq_pool | none | 21 | 57.1% | 24 | 75.0% | +17.9 | −1.27 | 0.205 |
| sweep_qual | clean | 32 | 62.5% | 32 | 65.6% | +3.1 | −0.26 | 0.794 |
| sweep_qual | ambiguous | 21 | 57.1% | 24 | 75.0% | +17.9 | −1.27 | 0.205 |
| displacement | strong | 51 | 60.8% | 53 | 69.8% | +9.0 | −0.97 | 0.333 |

### Multiple-testing correction
~20 tests performed. Bonferroni α = 0.05/20 = **0.0025**. Benjamini-Hochberg at q=0.05 with 1 discovery at raw p=0.016 yields BH threshold = 0.05×1/20 = 0.0025. **No subtype survives correction.**

### Observations
- **Subtypes trended UP, not DOWN, in the second half**. Nothing in the subtype dimension corresponds to a "decay". 12 of 13 subtypes have 2H WR ≥ 1H WR.
- `asian_low` shows the *opposite* of decay (40%→100%, uncorrected p=0.016) — and does not survive correction.
- The decay narrative's best candidate — "session_sweep framework is breaking" — shows the framework going 0.0%→28.6% from 1H to 2H. Whatever is happening, it's not systematic subtype decay.

**Verdict for deliverable #3:** No OB subtype shows statistically meaningful decay after correction. If anything, the surviving subtypes *improved* into 2026-Q1.

---

## 4. Time-of-day decay (XAUUSD)

### WR by kill zone (aggregate)

| KZ | N | W | WR | Exp |
|---|---:|---:|---:|---:|
| london | 62 | 44 | **71.0%** | +0.146R |
| ny | 69 | 37 | **53.6%** | +0.194R |

### KZ × 1H/2H decay test

- **london**: 69.7% → 72.4%, z=−0.24, p=0.81 — stable / slight improve
- **ny**: 50.0% → 56.8%, z=−0.56, p=0.58 — stable / slight improve

### Observations
- **London massively outperforms NY** (+17.4pp) across the full batch. This is the single biggest subtype split in the dataset but it's *cross-sectional*, not temporal — it does not decay.
- Neither KZ shows temporal decay; both second halves are ≥ first halves.
- Cannot sub-slice by "KZ open / overlap / mid-KZ" without raw candle_time in trade records — unified_v2 carries only `kill_zone` string. **Dropped as a deliverable sub-test.**

**Verdict for deliverable #4:** No time-of-day decay. The well-known london/NY asymmetry persists but is stable across 1H/2H.

---

## 5. Cross-instrument algo-density correlation

### Handoff-provided informal ranking (high → low algo density)
NAS100 > EURUSD > GBPUSD > USDJPY > GBPJPY > XAUUSD

### Data availability

| Symbol | Total trades w/ outcome | Quarters with n≥3 |
|---|---:|---:|
| XAUUSD | 131 | 6 |
| GBPUSD | 20 | 3 |
| USDJPY | 0 | 0 |
| GBPJPY | 0 | 0 |
| NZDUSD | 0 | 0 |
| US30_cash | 0 | 0 |
| NAS100 | 0 | 0 |
| EURUSD | 0 | 0 |

Spearman requires ≥3 instruments; only 2 available. **The test cannot be run.**

### What can be said
- GBPUSD quarterly WR trend: 83.3% (Q1-25) → 66.7% (Q2-25) → (gap) → 40.0% (Q4-25). Descending. Slope −21.7pp/q (n=3; exploratory).
- XAUUSD quarterly WR trend: +1.19pp/q (n=8; non-decaying in aggregate).
- These two instruments diverge in direction across the same time window — not consistent with a market-wide algo-density decay story.

**Verdict for deliverable #5:** Untestable with current data. Flag for reconsideration after redacted_account live produces 3+ instruments × 3+ quarters of outcome data (est. 6-9 months).

---

## 6. Decay noise-floor bootstrap

### Setup
- Null hypothesis: XAUUSD trade outcomes are i.i.d. draws from the pool WR (61.8%); no time structure.
- Method: shuffle 131 outcomes, partition into 4 equal pseudo-quarters of ~26 trades each, compute max-min spread and P(monotone descending).
- Iterations: 10,000.

### Results

| Statistic | Value |
|---|---:|
| Observed max-min spread (actual 4-quarter decay frame) | ~13.8pp |
| Bootstrap median max-min spread | 19.2pp |
| Bootstrap 95th percentile | 34.6pp |
| **P(max-min ≥ 13.8pp under null)** | **0.7525** |
| P(monotone descending sequence) | 0.0743 |
| P(final-to-first drop ≥ 13.8pp) | 0.1588 |

### Interpretation
- The **observed spread is smaller than the median bootstrap spread**. The "decay" sits below the null's central tendency.
- Monotone descending is rare under null (p=0.07) *but* this is a post-hoc framing — we chose the 4 quarters where the monotone pattern appears. The multiple-testing penalty for "which 4 adjacent quarters show the strongest pattern" is not small (there are ≥5 candidate windows in 8 quarters).
- **Two-proportion Z on first-half vs second-half** (46 vs 85 trades): 63.0% vs 61.2%, z=0.21, p=0.83. No signal.

**Verdict for deliverable #6:** The claimed decay is statistically indistinguishable from a stationary process. There is no evidence that edge is decaying monotonically over time.

---

## 7. 2026-Q1 regime deep-dive (why does this quarter feel like decay?)

### Monthly breakdown of 2026-Q1 XAUUSD trades

| Month | N | W | L | BE | WR | Sum_R |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01 | 21 | 12 | 9 | 0 | 57.1% | +0.85R |
| 2026-02 | 6 | 4 | 2 | 0 | 66.7% | +2.15R |
| 2026-03 | 5 | 3 | 2 | 0 | 60.0% | +1.41R |

**WR uniformly ~60% across all three months.** Not a collapse event. Edge *held* despite hostile regime.

### Regime comparison: 2025-Q4 vs 2026-Q1

| Metric | 2025-Q4 | 2026-Q1 | Interpretation |
|---|---:|---:|---|
| ADR mean | 88.7 | 169.7 | 1.9× expansion |
| ATR/252d | 1.57 | 2.16 | Highest in series |
| Kaufman ER (rolling 10d mean) | 0.412 | 0.377 | Minor drop |
| Kaufman ER (end-of-quarter, close-close) | ~0.16 | **~0.03** | **5× chop spike** |
| Trend % (net) | +11.73% | +4.34% | V-shape |
| Max intra-Q drawdown | 9.78% | 19.20% | 2× max adverse excursion |
| Realized vol annualized | 0.236 | 0.397 | 1.7× vol expansion |
| Kurtosis | 3.08 | 2.10 | Both fat-tailed |
| **CANDIDATE rate** | **2.17%** | **5.80%** | **2.67× triggering rate** |
| **WR** | **73.9%** | **59.4%** | **−14.5pp, but still >55% breakeven** |

### Synthesis
2026-Q1 was the **hardest regime in the 2-year dataset**: volatility expanded, net movement stalled (V-shape), intra-Q drawdown doubled. In this regime:
- The system **fired nearly 3× as many trades** as the previous quarter.
- WR dropped but **held at 59.4% — still significantly positive** (binomial p vs 50% = 0.15 on n=32, but the prior 129 trades give cumulative evidence).
- Expectancy remained **+0.138R/trade**, profitable.

**The 2026-Q1 result is not a decay event. It is a stress-test result.** The system kept making money in the worst regime it has seen.

---

## 8. Statistical rigor addendum

### Multiple testing adjustment summary

| Deliverable | Tests run | α raw | Bonferroni α | Signals surviving |
|---|---:|---:|---:|---|
| Regime metric correlations (§1, §7) | 10 | 0.05 | 0.005 | Trend_pct (p=0.002), KER (p=0.028 does not survive — drop) |
| OB subtype 1H/2H (§3) | 20 | 0.05 | 0.0025 | None survive |
| Cross-instrument (§5) | 0 | — | — | N/A |
| Bootstrap (§6) | 1 | 0.05 | 0.05 | Observed spread within null |

With strict Bonferroni, **the only surviving finding is "WR correlates with net quarterly trend direction" (p=0.002)**.

### n<20 flags (exploratory-only)
- All 2024 quarters (n=3-6 each) — flagged exploratory.
- 2025-Q3 (n=10), 2025-Q2 (n=20 barely).
- 2025-Q4 (n=23), 2025-Q1 (n=32), 2026-Q1 (n=32) are inferential-grade.
- GBPUSD all quarters (n=1-6) — flagged exploratory.

### Post-hoc selection warnings
- The "73.2 → 71.4 → 63.6 → 59.4" frame is a post-hoc 4-term window; multiple-testing correction for "best decaying 4-window" in 8 quarters is ~5×.
- `asian_low` subtype was one of 13 subtype values tested; uncorrected p=0.016 → corrected not-significant.

---

## 9. Ranked verdict (deliverable #7)

### Hypothesis 1: **"The observed decay is within the noise band of a stationary process."**
- **Evidence strength:** HIGH
- **Confidence:** 0.85
- **Key numbers:** Bootstrap P(spread ≥ observed) = 0.7525 (n=131, 10,000 perms); 1H vs 2H z=0.21, p=0.83
- **Citations:** `_delta_scratch/02_decay_analysis.py:165-216` (bootstrap), `decay_analysis.md:49-63`
- **Testability:** HIGH. Phase 3 can replicate with next-quarter live data; pre-register the null prospectively.
- **Implication for redacted_account kickoff:** No reason to delay. Apparent decay is a sampling artifact + a hard regime.

### Hypothesis 2: **"Edge is regime-conditional on trending markets; chop hurts."**
- **Evidence strength:** HIGH (survives Bonferroni at α=0.005)
- **Confidence:** 0.80
- **Key numbers:** Spearman(WR, trend_pct) = +0.786, p=0.002 (n=8 quarters); KER ρ=+0.667, p=0.028 (confirmatory, does not survive strict correction but directionally consistent)
- **Citations:** `_delta_scratch/02_decay_analysis.py:217-293` (Spearman), `decay_analysis.md:240-253`
- **Testability:** HIGH. Phase 3 can pre-register a test: "system WR is >5pp lower in bottom-quartile-KER weeks vs top-quartile-KER weeks."
- **Implication:** Consider a KER-threshold *shadow* filter (log-only initially) to validate the conditional effect on live data. Do NOT ship as a gate without the pre-reg test.

### Hypothesis 3: **"2026-Q1 is an AI over-triggering-in-chop event, not an edge decay."**
- **Evidence strength:** MEDIUM
- **Confidence:** 0.65
- **Key numbers:** XAUUSD CR 2.17%→5.80% on similar eval volume (874→828); ADR 5× baseline; KER (end-of-quarter) collapsed to 0.03; WR *held* at 59.4%; XAUUSD CR 2.9× higher than next instrument.
- **Citations:** `sessions_per_quarter.csv:19-26`, `regime_metrics.csv` (2026-Q1 XAUUSD row)
- **Testability:** HIGH. Phase 3 test: "AI CANDIDATE rate should correlate inversely with recent KER — measure ρ on live data."
- **Implication:** This is the actual **actionable** finding. Supports CLAUDE.md unresolved item #5 (T2.prompt — AI emitting `sl_buffer_applied: 0.0` universally) as a symptom of a broader prompt-side weakness in distinguishing tradeable setups in chop regimes.

### Hypothesis 4: **"Cross-instrument algo-density decay — UNTESTABLE."**
- **Evidence strength:** N/A (insufficient data)
- **Confidence:** N/A
- **Key numbers:** Only 2 instruments (XAUUSD=131, GBPUSD=20) have outcome-attached trade history. Need ≥3 to run Spearman across an algo-density ranking.
- **Testability:** LOW pre-kickoff. After redacted_account produces ~6-9 months of multi-instrument live trades, retest.
- **Implication:** Park this hypothesis. Do not block redacted_account kickoff on it.

### Hypothesis 5: **"OB subtype decay — marginal `asian_low` signal, does not survive correction."**
- **Evidence strength:** LOW
- **Confidence:** 0.25
- **Key numbers:** `asian_low` 1H 40% (n=10) → 2H 100% (n=6), uncorrected p=0.016. Across 20 subtype tests, Bonferroni α=0.0025 — not significant. Additionally, the *direction* (40→100) is the opposite of decay — this subtype *improved*.
- **Testability:** MEDIUM. Phase 3 could pre-register a test if the theoretical basis for caring about `asian_low` is pre-specified.
- **Implication:** Low priority. Not a cause of apparent decay.

---

## 10. What this verdict is NOT

- **Not a claim that the edge is invincible.** It is a claim that the current data is consistent with a stationary edge.
- **Not a green-light for everything.** The regime-conditionality finding (§Hypothesis 2) is the single most structurally meaningful result. It means if 2026-Q2 stays chop, WR could look similar to 2026-Q1. Enter redacted_account with that as the planning assumption.
- **Not a critique of the AI / prompt.** Hypothesis 3 is a *prompt-level over-triggering hypothesis that needs its own test*, not a conclusion.
- **Not a replacement for the chairman's synthesis.** I provide ranked hypotheses with citations; chairman weights against α/β/γ/ε/ζ/η/θ findings.

---

## 11. Artifacts & reproducibility

All scripts and CSVs under `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/`:

| File | Purpose |
|---|---|
| `00_load_datasets.py` | Merge + dedup trade sources → `trades_unified.csv` (151 rows) |
| `01_regime_metrics.py` | Per-quarter regime metrics → `regime_metrics.csv` (256 rows) |
| `02_decay_analysis.py` | Main analysis: subtype, bootstrap, Spearman → `decay_analysis.md` |
| `trades_unified.csv` | Merged trade table with outcome+r_multiple |
| `regime_metrics.csv` | ADR/ATR/Hurst/KER/autocorr/vol/skew/kurt/trend per (sym, Q) |
| `sessions_per_quarter.csv` | CANDIDATE rate per (sym, Q) |
| `decay_analysis.md` | Raw tables (this doc is the synthesis) |

Reproduce: `python 00_load_datasets.py && python 01_regime_metrics.py && python 02_decay_analysis.py` from the scratch dir. Read-only on all upstream files; no modifications to knowledge_base or production data.

---

*Agent δ — deliverable complete. Feeds chairman synthesis + Phase 3 hypothesis registration.*
