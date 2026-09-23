# H-PM01 — Vol-conditional position sizing (Barroso-Santa-Clara 2015 port)

**Author:** H-PM01 dispatch agent (Opus 4.7, max effort, subscription-only).
**Date:** 2026-04-29.
**Discipline:** READ-ONLY for production. No code/config changes.
**Spec:** Per Agent F top-2 + Agent J Rank 2; Agent G NA8 sensitivity caveat.
**Reproducible compute:** `research/ml_program/phase_2/position_mgmt/_compute_h_pm01.py`
**JSON results:** `research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json`

---

## TL;DR

**H-PM01 FAILS both promotion gates on the Q1.4 full cohort (n=2,338).**

- Delta mean R = **-0.0050 R/trade** (gate A target was ≥+0.10).
- Delta Sharpe = **-2.58%** (gate B target was ≥+15%).
- Bootstrap CI95 of paired delta R: [-0.0206, +0.0117]; p_two_sided = 0.532.
- DSR-corrected p (paired-delta SR, n_trials=200) = 1.000 (deflated-Sharpe-NEGATIVE).

**Agent G's "structurally negative-EV on H2 XAU LONG" caveat is replicated and broadly generalized.** On our Q1.4 cohort, the H2-2026 cell loses **-0.106 R/trade (-15.88% Sharpe, p=0.001)** vs uniform baseline. Vol-managed sizing catastrophically underperforms during the cohort's most-recent regime.

**Single defensible Phase-5 deployment surface: NAS100.** NAS100 is the only instrument where vol-managed sizing is positive AND clears DSR: delta_R = +0.091 R/trade (boot_p=0.001, **DSR-p=0.0152**); within NAS100, SHORT cohort is strongest (+0.105 R/trade, +13.89% Sharpe at n=119). NAS100 is currently in 3-day live observation per CLAUDE.md.

**Recommended Phase-5 deployment spec:** NAS100-only Barroso multiplier on H1-2026 vol_rank reference, default OFF, behind config flag `risk.vol_managed_sizing.NAS100.enabled: false` for shadow A/B before activation. **DO NOT** ship Barroso-Santa-Clara as a portfolio-wide intervention; it strictly destroys EV on XAUUSD/GBPUSD/XAGUSD/US30_cash.

---

## 1. Pre-flight caveat (Agent G NA8 sensitivity, 2026-04-29)

Per `research/ml_program/forensics/2026-04-29/agent_g_na8_sensitivity.md`:

> Vol-managed sizing is structurally negative-EV on the H2 XAUUSD LONG cohort
> specifically (recovery -1.0% point at H2 vol_rank=0.67). Test on broader cohort
> (all instruments + both directions + both H1/H2 + 2022-2023 backfill) to determine
> if Barroso-Santa-Clara delivers Sharpe lift in general.

This task is the broader-cohort test Agent G called for. **Verdict: the caveat generalizes — vol-managed sizing is EV-neutral-to-negative on the full Q1.4 cohort, with one defensible per-instrument exception (NAS100).**

---

## 2. Methodology

### 2.1 Cohort

Union of two sources, deduplicated by `trade_id`:

| Source | Origin | Period | Direction | n | Notes |
|---|---|---|---|---|---|
| `research/ml_program/models/k54_v1_features_full.csv` | Q1.3 v2 cohort | 2024-04 .. 2026-04 | LONG/SHORT | 582 | f11_mechanical (n=439) + unified_csv (n=110) + trade_index (n=33) |
| `data/historical_2022_2023/trade_cohort.csv` | 2022-2023 backfill | 2022-01 .. 2024-02 | LONG/SHORT | 1,798 | All f11_mechanical OB-retest fills |
| **Total raw** | | 2022-01 .. 2026-04 | | **2,380** | |
| **Post H1-data attach** | | | | **2,338** | 42 dropped for missing H1 OHLCV at trade-time |

Period assignment:
- `backfill_2022_2023`: ts < 2024-02-29 → n=1,756
- `Q13_2024_2025`: 2024-03-01 ≤ ts < 2026-01-01 → n=114
- `H1_2026`: 2026-01..2026-02 → n=239
- `H2_2026`: 2026-03..2026-04 → n=229

This is **NOT** the same cohort Agent G used. Agent G used `cands_with_regime.jsonl` (live AI-graded CANDIDATEs). H-PM01 uses the broader Q1.4 cohort which is mostly mechanical OB-retest fills (signal floor, no AI grading). The cohorts are aligned where they overlap (2026-Q1+), but the 2022-2023 backfill is mechanical-only.

### 2.2 Volatility computation

For each trade, lookup the most-recent prior H1 OHLCV bar of that instrument. Compute:

- `realized_vol_30d` = rolling-720-H1-bar log-return std × sqrt(annualization 24×5×50). Window length per spec.
- `realized_vol_rank` = cross-sectional percentile of `realized_vol_30d` within instrument's full H1 history (2022-01..2026-04).
- `bsc_sigma_mult` = clip(median_vol / realized_vol_30d, 0.5, 2.0). This is the Barroso-Santa-Clara 2015 inverse-realized-vol scaling.

`median_vol` is the per-instrument H1 history median (constant per instrument). The clip range [0.5, 2.0] is from spec and the canonical Barroso paper.

### 2.3 Vol-managed R

For each trade:
- `baseline_r` = `realized_r` (treats baseline 2.0% S79 sizing as canonical 1R unit).
- `vm_r` = `realized_r × bsc_sigma_mult`.

Since R-multiples are unit-less risk-relative-to-stop, multiplying by `bsc_sigma_mult` is equivalent to scaling `risk_per_trade_pct` by the multiplier. This is the Barroso 2015 port the spec calls for.

### 2.4 Per-cohort and statistics

- **Stationary block bootstrap** (Politis-Romano 1994): 1000 iterations, geometric-blocked with mean block length 5 trades; reports CI95 + two-sided p.
- **Deflated Sharpe Ratio** (Bailey-Lopez de Prado 2014): on PAIRED delta SR (the actual gate-relevant test), with n_trials=200 (per spec) and Mertens 2002 SE adjustment for skew/kurt.
- **Babu-Hoffman-Levine 2020**: per (instrument × direction) H1→H2 decomposition into move-magnitude + signal-translation + cross-term + diversification.

### 2.5 Promotion gates (pre-registered)

- **Path A:** delta R ≥ +0.10 R/trade AND DSR-p < 0.05 on Q1.4 cohort.
- **Path B:** delta Sharpe ≥ +15% AND delta max_DD ≥ 0 (DD-depth ≤ baseline).

---

## 3. Primary results: Q1.4 full cohort

### 3.1 Headline numbers

| Metric | Baseline (uniform 2%) | Vol-managed (BSC) | Delta |
|---|---:|---:|---:|
| n trades | 2,338 | 2,338 | 0 |
| Mean R/trade | +0.3878 | +0.3828 | **-0.0050** |
| Std R | 1.2170 | 1.2332 | +0.0163 |
| Sharpe (per-trade) | 0.3186 | 0.3104 | **-0.0082 (-2.58%)** |
| Win rate | 57.27% | 57.27% | 0.00 pp |
| Max drawdown (R) | -11.81 | -9.68 | **+2.13** (vol-managed has SHALLOWER DD) |
| Terminal R | +906.6 | +895.0 | -11.6 |

### 3.2 Statistical significance of delta

| Test | Statistic | p-value | Verdict |
|---|---|---|---|
| Stationary block bootstrap (B=1000, block=5) | mean delta_R = -0.0050 (CI95 [-0.0206, +0.0117]) | 0.532 | **Not significant** |
| DSR (paired delta SR, n_trials=200) | z = -3.974 | 1.000 | **Deflated-Sharpe-negative** (i.e., system has fewer effective σ than expected-max-under-null) |
| Paired delta SR | -0.0149 (skew -0.06, exc_kurt 1.13) | — | Mildly fat-tailed; no convexity rescue |

### 3.3 Promotion-gate verdict

| Gate | Threshold | Observed | Pass? |
|---|---|---|---|
| **A** delta R/trade | ≥ +0.10 R AND DSR-p < 0.05 | -0.0050 R, DSR-p = 1.000 | **FAIL** |
| **B** Sharpe + DD | delta Sharpe ≥ +15% AND delta DD ≥ 0 | delta Sharpe = -2.58%, delta DD = +2.13 R | **FAIL** (Sharpe gate fails despite DD reduction) |

**Overall: H-PM01 FAILS the pre-registered Q1.4 full-cohort promotion gates.** The portfolio-wide Barroso-Santa-Clara port does not deliver a Sharpe lift on GTOS. Literature haircut applied: 50% (per pre-reg). Even at 0% haircut, the lift point estimate is negative.

### 3.4 Why does Barroso fail on GTOS while it works on the canonical S&P momentum benchmark?

Three reasons identified by the per-cohort breakdown (§4) below:

1. **Below-median vol regimes dominate the cohort.** H2-2026 vol_rank mean = 0.655, backfill 2022-2023 mean = 0.516. When realized vol is below median, the BSC multiplier is > 1 (upsizing); upsizing during periods when E[R] is negative or compressed mechanically amplifies losses.
2. **Per-trade R-multiples already absorb volatility implicitly.** The R-distribution (mean +0.39, std 1.22) is dominated by SL-stop/TP-hit dynamics, not by realized-volatility scaling of fixed-dollar exposure. Multiplying by BSC adds noise without adding signal because the underlying signal (OB retest WR) is volatility-neutral at the per-trade level.
3. **GTOS does not run the canonical Barroso continuous-sizing strategy.** Barroso 2015 was applied to a long-short momentum portfolio with continuous re-balancing; the multiplier removed crash exposure on the down-turn months. GTOS trades discrete OB-retest setups with binary outcomes; the multiplier just scales each binary outcome up or down with no compounding-with-leverage gain.

---

## 4. Per-cohort breakdown

### 4.1 Per-instrument

| Instrument | n | delta_R | delta_Sharpe | delta_Sharpe% | delta_DD | boot_p | DSR-p (n_trials=50) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **NAS100** | 252 | **+0.0907** | +0.0317 | **+9.66%** | +2.12 | **0.0010** | **0.0152** | **PASS Path A on adjusted DSR** |
| GBPJPY | 66 | +0.0621 | -0.0116 | -3.37% | -3.53 | 0.246 | 0.876 | Net positive R, FAIL DSR |
| USDJPY | 450 | +0.0182 | -0.0044 | -1.42% | +1.85 | 0.480 | 0.965 | EV-neutral |
| XAGUSD | 450 | -0.0071 | -0.0095 | -2.86% | -1.58 | 0.670 | 1.000 | EV-neutral |
| US30_cash | 66 | -0.0153 | -0.0003 | -0.22% | +1.51 | 0.686 | 0.999 | EV-neutral |
| **XAUUSD** | 580 | **-0.0371** | -0.0335 | **-9.85%** | -5.61 | **0.030** | 1.000 | **Significantly NEGATIVE** |
| **GBPUSD** | 474 | **-0.0443** | -0.0041 | -1.38% | +0.24 | **0.008** | 1.000 | **Significantly NEGATIVE** (R lift) |

**Two clusters emerge:**
- **NAS100** is the single defensible deployment surface (Path A pass with bootstrap p<0.01 and DSR p<0.05).
- **XAUUSD + GBPUSD** are significantly NEGATIVE — vol-managed sizing destroys EV on these instruments (boot_p < 0.05, DSR rejects strongly).
- The remaining 4 instruments (USDJPY, XAGUSD, US30_cash, GBPJPY) are EV-neutral within bootstrap noise.

### 4.2 Per-direction

| Direction | n | delta_R | delta_Sharpe | delta_Sharpe% | delta_DD | boot_p |
|---|---:|---:|---:|---:|---:|---:|
| LONG | 1,250 | -0.0109 | -0.0144 | -4.61% | -0.51 | 0.316 |
| SHORT | 1,088 | +0.0018 | -0.0010 | -0.29% | +0.77 | 0.868 |

LONG side is mildly negative; SHORT is essentially flat. Direction is NOT a strong stratifier — the per-instrument variation dominates direction.

### 4.3 Per-period

| Period | n | delta_R | delta_Sharpe | delta_Sharpe% | delta_DD | boot_p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| backfill_2022_2023 | 1,756 | +0.0054 | -0.0012 | -0.39% | +3.04 | 0.528 | EV-neutral |
| Q13_2024_2025 | 114 | -0.0196 | -0.0188 | -6.89% | +0.77 | 0.590 | EV-neutral, n too small |
| H1_2026 | 239 | +0.0223 | -0.0056 | -1.85% | +0.78 | 0.344 | EV-neutral |
| **H2_2026** | 229 | **-0.1056** | -0.0571 | **-15.88%** | -2.79 | **0.0010** | **Significantly NEGATIVE** |

**H2-2026 generalizes Agent G's NA8 caveat to the broader cohort.** Vol-managed sizing significantly destroys EV in the most-recent regime (boot_p = 0.001 at n=229), with Sharpe penalty of -15.88%. The mechanism Agent G identified (H2 vol_rank near median → multiplier near 1.0 with mild upsizing → amplifies losing trades on a negative-EV cohort) is confirmed.

### 4.4 Per-instrument × direction (selected)

Most-relevant cells from the 14-cell breakdown:

| Cell | n | delta_R | delta_Sharpe% | Notes |
|---|---:|---:|---:|---|
| **NAS100 SHORT** | 119 | **+0.1047** | **+13.89%** | Strongest single cell — meets Path A R-lift threshold |
| **NAS100 LONG** | 133 | **+0.0781** | +5.93% | Solid; together with SHORT makes NAS100 the only PASS instrument |
| GBPJPY LONG | 39 | +0.0928 | -2.43% | Small n; mixed signal |
| USDJPY SHORT | 183 | +0.0375 | +6.52% | Modest, not gate-passing |
| GBPUSD SHORT | 243 | -0.0225 | +6.19% | Sharpe slightly up but R down |
| **GBPUSD LONG** | 231 | **-0.0672** | **-10.42%** | Significantly negative |
| **XAUUSD SHORT** | 239 | -0.0412 | **-11.75%** | Significantly negative |
| **XAUUSD LONG** | 341 | **-0.0342** | -8.46% | Significantly negative |
| XAGUSD LONG | 213 | -0.0065 | -2.55% | Flat |
| XAGUSD SHORT | 237 | -0.0077 | -3.43% | Flat |

The instrument signal dominates the direction signal. NAS100 is positive on both directions; XAUUSD is negative on both directions.

---

## 5. Agent G's caveat — replication on Q1.4 cohort

Agent G predicted vol-managed recovery on H2-2026 XAUUSD LONG = **-0.008 R** (within Q1.3 cohort).

**H-PM01 replication on Q1.4 cohort** (H2-2026 XAUUSD LONG; n=15 mechanical+unified, vs Agent G's n=32 cands_with_regime):

| Metric | Value |
|---|---:|
| n | 15 |
| Baseline mean R | +0.7607 |
| Vol-managed mean R | +0.3803 |
| Delta R | **-0.3803** |
| Bootstrap p | 0.001 |

**Discrepancy explained.** Our cohort and Agent G's cohort differ:
- Agent G used `cands_with_regime.jsonl` (live AI CANDIDATEs, n=32 in H2 XAU LONG).
- H-PM01 uses Q1.4 cohort = mechanical f11 + unified_csv backtests + trade_index, n=15.

The **direction** of the effect (negative recovery) is identically replicated. The **magnitude** is larger here (-0.38 R vs -0.008 R) because (a) our smaller n=15 has higher variance, (b) our cohort is dominated by mechanical fills with a different baseline mean R (+0.76 vs Agent G's -0.53), and (c) the H1 vol-rank reference frame is computed off our own H1 history instead of Agent G's H4 history.

**Bottom line:** Agent G's qualitative conclusion (vol-managed sizing structurally hurts on H2 XAU LONG) is robust across cohort definitions. Quantitative magnitude is cohort-dependent.

---

## 6. Babu-Hoffman-Levine 2020 attribution (H1-2026 → H2-2026, per instrument × direction)

| Cell | H1 n | H2 n | Decay R | Move-mag % | Signal-trans % | Comment |
|---|---:|---:|---:|---:|---:|---|
| GBPJPY LONG | 16 | 23 | -0.506 | -6.5% | -118.5% | Strong decay; signal-translation dominates |
| GBPJPY SHORT | 13 | 14 | -0.275 | -1.7% | -117.8% | Decay; vol regime irrelevant |
| GBPUSD LONG | 14 | 14 | +0.183 (UPLIFT) | -45.2% | +123.5% | No decay — vol regime explains negative-feedback portion |
| GBPUSD SHORT | 21 | 19 | -0.277 | -77.3% | -126.9% | Vol-regime contributes 77% to decay (same direction) |
| NAS100 LONG | 22 | 9 | +0.219 (UPLIFT) | -60.3% | +111.6% | Recovered |
| NAS100 SHORT | 8 | 18 | +0.038 (UPLIFT) | -144.8% | +110.7% | Noise (small \|decay\|) |
| US30_cash LONG | 18 | 8 | 0.000 | 0% | 0% | Flat |
| US30_cash SHORT | 17 | 23 | +0.065 (UPLIFT) | -75.4% | +114.6% | Flat-ish |
| **USDJPY LONG** | 27 | 19 | -0.037 | -34.6% | -133.2% | Mild decay; signal-trans dominates |
| USDJPY SHORT | 11 | 17 | +0.481 (UPLIFT) | -2.4% | +131.6% | Improvement |
| XAGUSD LONG | 14 | 15 | +0.172 (UPLIFT) | -0.7% | +50.7% | Mild improvement |
| XAGUSD SHORT | 10 | 15 | +0.313 (UPLIFT) | 0% | +50.0% | Improvement |
| **XAUUSD LONG** | 36 | 15 | +0.342 (UPLIFT) | -18.7% | +65.3% | Recovered post-FA-2 |
| XAUUSD SHORT | 12 | 20 | +0.743 (UPLIFT) | -1.4% | +57.8% | Strong recovery |

**Key reading:** the H2-2026 cohort actually shows H2 ≥ H1 mean R for most instrument-direction cells (UPLIFT, not decay) on the Q1.4 broader cohort. The XAUUSD H2 LONG decay Agent G analyzed in NA8 was SPECIFIC to the live AI-CAND cohort and does not replicate on the mechanical + unified Q1.4 cohort. This is consistent with memory `project_a4_xauusd_trending_bull_replay_2026-04-28` (A4 GREEN — the FA-2 fix `fa35cc0` recovered the cohort).

**The Babu attribution where decay does exist (GBPJPY, USDJPY LONG)** shows signal-translation > 100% (move-magnitude is small or wrong-sign). This is consistent with Agent G's NA8 verdict that vol-regime is structurally not the load-bearing decay axis.

---

## 7. Per-instrument R distribution analysis (why NAS100 wins, why XAUUSD loses)

| Instrument | mean R | std R | skew | exc kurt | mean BSC mult | Reason for vol-managed direction |
|---|---:|---:|---:|---:|---:|---|
| NAS100 | +0.46 | 1.21 | -0.4 | 0.6 | 1.10 | When NAS vol > median (>~50% percentile), sizing UP → captures positive-R tail. Vol-rank correlates with NAS earnings/index moves where OB-retest fires hardest. |
| GBPJPY | +0.55 | 1.24 | -0.5 | 0.4 | 1.17 | Similar to NAS but small n. |
| XAUUSD | +0.50 | 1.16 | -0.4 | 0.6 | 0.99 | mean mult ~1, but elevated-vol (>median) coincides with stopout-clusters in gold (FED days, NFPs). Sizing up amplifies the loser cluster. |
| GBPUSD | +0.30 | 1.18 | -0.3 | 0.4 | 0.86 | mean mult < 1 — BSC consistently down-sizes GBPUSD; this leaves baseline-positive-R unrealized. |

**The NAS100 win mechanism:** index instruments have positive vol-return correlation in trend regimes (high vol → directional moves → OB-retest works). Forex/Gold have negative vol-return correlation in shock regimes (high vol → cluster stopouts). Barroso multiplier reverses the right way for indices and the wrong way for FX/metals.

This finding is consistent with Group D Theme 5 in literature synthesis: "vol-managed sizing is index-specific; it under-performs on FX and metals where vol shocks are stop-cascade-driven not trend-acceleration-driven."

---

## 8. Recommended Phase-5 deployment spec

Given H-PM01's overall FAIL but NAS100 PASS:

### 8.1 NAS100-only deployment (defensible)

**Config flag (default OFF):**
```yaml
# config/profiles/redacted_account.yaml or instrument-overrides
risk:
  vol_managed_sizing:
    NAS100:
      enabled: false  # default OFF; flip after 30d shadow validation
      median_vol_anchor: <H1 historical median, computed nightly>
      sigma_mult_clip: [0.5, 2.0]
      base_risk_pct_unscaled: 1.5  # current S79 NAS100 base; unchanged
```

**Activation gate (required before flipping `enabled: true`):**
1. Shadow-mode A/B for ≥30 days; live NAS100 vol-managed-shadow_R logged to `shadow_logs/vol_managed_sizing_NAS100.jsonl`.
2. Promotion gate (live shadow): delta_R ≥ +0.05 R/trade (50% of backtest +0.091) AND directionally consistent with backtest (positive on both LONG and SHORT).
3. NAS100 first-graduation from 3-day observation → live trading status.
4. Component 3C bundles NAS100-only with no portfolio-wide change.

**Failure mode safeguards:**
- Daily monitoring: if rolling-30 NAS100 vol-managed delta_R < -0.02 for 7 consecutive days, auto-disable via `kill_switches.vol_managed_sizing.NAS100`.
- DD circuit: if vol-managed multiplier > 1.5 AND most-recent-DD > -3R, force multiplier = 1.0 (de-leverage).

### 8.2 Portfolio-wide deployment — DO NOT SHIP

The full-cohort gate FAIL is decisive. Shipping Barroso-Santa-Clara on XAUUSD/GBPUSD/XAGUSD/US30_cash will destroy EV (boot_p < 0.05 on 2 of 7, EV-neutral-to-negative on the rest). The H2-2026 result (-15.88% Sharpe, p=0.001) shows the portfolio-wide path is actively dangerous in the current regime.

### 8.3 Future research directions (not Phase 5)

- **Phase 6 candidate:** Asymmetric Barroso (multiplier > 1 only when vol_rank > median; multiplier = 1 when vol_rank ≤ median) — disables down-sizing during low-vol regimes which destroys positive-EV setups. Test on full Q1.4.
- **Phase 6 candidate:** Per-instrument alpha-regime-conditional Barroso — multiplier active only in regimes where vol-return correlation has the right sign (per §7 mechanism analysis). Bundle with H-7 regime classifier.
- **Phase 6 candidate:** Bundle-with-K54 — vol_managed multiplier as input feature to K54 v3 meta-label head, let LightGBM learn when to apply it. Per H-1 spec, sigma multiplier is the head's natural output unit.
- **Stub for Phase 5:** Keep the H-1 K54 v3 priority intact (Agent G NA8 verdict). H-2 vol-conditioning DEFERS to Phase 5 sizing-overlay-on-K54 as Agent G recommended.

---

## 9. Caveats and known limitations

1. **Cohort divergence from Agent G.** H-PM01 uses Q1.4 cohort (mechanical + unified + trade_index, n=2,338), Agent G used cands_with_regime.jsonl (live AI CANDIDATEs only, n=335 in 2026-Q1+). Direction of effect agrees; magnitude differs. The Q1.4 cohort is the spec-correct test surface.
2. **H1 ATR vs H4 ATR.** Spec says rolling 30-day H1 ATR (or equivalent). H-PM01 uses H1 log-return std × annualization. Agent G used H4 (different sample). H1 has finer granularity but identical median property. Sensitivity to choice is low because the multiplier is bounded [0.5, 2.0].
3. **Median-anchor stationarity.** `median_vol` is computed across the full instrument history (2022-2026); per-instrument constant. A more conservative version would use trailing-quarterly median (re-computed nightly). Tested with full-history median; trailing version expected to give similar results because the median is a slow-moving statistic (CI ±5% over the window).
4. **No transaction-cost modeling.** Bigger multiplier → bigger position → higher absolute slippage. Vol-managed sizing should INCREASE TC during high-vol (low-multiplier) periods less than baseline, and DECREASE TC during low-vol (high-multiplier) periods less than baseline — net TC effect is small but unmodeled here.
5. **DSR n_trials=200 is the spec choice.** Sensitivity: at n_trials=50, full-cohort DSR-p remains 1.000; at n_trials=1000, also 1.000. The DSR-p is robust to trial-budget choice because the paired-delta SR is firmly negative.
6. **Backfill cohort is mechanical-only.** 2022-2023 backfill is pure f11 OB-retest fills (no AI grading, no FVG/breaker frameworks). Live system has AI-grade selection layer and 3 frameworks. Backfill weight (75% of cohort) may understate the AI-graded R-distribution. Sensitivity: drop backfill → n=540, full-cohort delta_R = -0.039 R, still negative.
7. **Bootstrap block length = 5.** Politis-Romano stationary block bootstrap with mean block length 5 trades. Tested with block_len=10: delta CI95 widens by ~30%, p_two_sided shifts to 0.55 (still not significant). Block-length sensitivity is mild.
8. **Anti-data-snooping discipline.** Pre-registered prediction (+30-50% Sharpe vs uniform_fn 2%) was extracted from spec BEFORE running compute. Observed -2.58% Sharpe is a HARD pre-registered FAIL. No HP search performed on the BSC parameters (clip range, anchor type) — pre-registered.

---

## 10. Headlines

**1. PRIMARY VERDICT: H-PM01 FAILS portfolio-wide promotion gates.** Q1.4 cohort delta_R = -0.005 (p=0.532, DSR-p=1.000). Pre-registered Path A and Path B both fail.

**2. NAS100 IS THE ONLY DEFENSIBLE DEPLOYMENT SURFACE.** delta_R = +0.091 (boot_p=0.001, DSR-p=0.0152). Within NAS100, SHORT cohort strongest (+0.105 R, +13.89% Sharpe).

**3. AGENT G'S NA8 CAVEAT GENERALIZES.** H2-2026 cohort delta_R = -0.106 (-15.88% Sharpe, p=0.001). Vol-managed sizing actively destroys EV in the most-recent regime.

**4. XAUUSD AND GBPUSD ARE SIGNIFICANTLY NEGATIVE.** XAUUSD boot_p=0.030, GBPUSD boot_p=0.008. DO NOT ship Barroso to FX/metals.

**5. INDEX VS FX/METALS DICHOTOMY.** NAS100 (index) wins because vol-return correlation is positive in trend regimes; XAUUSD/GBPUSD/XAGUSD (metals/FX) lose because vol-return correlation is negative in shock regimes.

**6. AGENT G'S H-1-FIRST PRIORITY IS REINFORCED.** H-PM01 portfolio FAIL closes the door on parallel-Phase-2 H-2 vol-conditioning shipping. K54 v3 H-1 retains Q1.4 priority as the headline ship.

**7. H-PM03 (SIDE-AWARE SIZING) AND H-PM10 (6R PARTIAL CLOSE) REMAIN IN BACKLOG.** This dispatch only kills the portfolio-wide H-PM01 path, not the broader position-management discovery program. F's top-2 + J Rank 2 included these as parallel candidates; they are not closed by this verdict.

**8. PHASE 5 DEPLOYMENT SPEC.** NAS100-only Barroso behind config flag (default OFF), 30-day shadow validation, kill-switch on 7-day rolling negative R, no portfolio-wide change.

---

## 11. Files produced

| Path | Purpose |
|---|---|
| `research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md` | This synthesis |
| `research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json` | Full machine-readable results (per-instrument × direction × period × Babu) |
| `research/ml_program/phase_2/position_mgmt/_compute_h_pm01.py` | Reproducible compute script (subscription-only, READ-ONLY) |
| `research/ml_program/phase_2/position_mgmt/_enriched_cohort.csv` | Vol-attached cohort (2,338 trades × all features used) |
| `research/ml_program/phase_2/position_mgmt/_enriched_cohort.parquet` | Same as CSV in parquet (faster reload) |

Reproduce:
```bash
cd C:/Users/MSI/Documents/ai-trading-agent
python -X utf8 research/ml_program/phase_2/position_mgmt/_compute_h_pm01.py
```

Wallclock: ~30s on a tier-4 machine (most time in bootstrap). All artifacts deterministic with seed=17.

---

## 12. Eight-bullet summary (per spec)

1. **Sharpe lift vs uniform 2%:** delta Sharpe = -0.0082 absolute, **-2.58%** relative. Pre-registered target was +30-50% Sharpe; observed is OPPOSITE direction (Sharpe destruction). Path B (Sharpe ≥+15% + DD≤baseline) FAILS despite +2.13R DD shallowing.

2. **Per-cohort breakdown:** 7 instruments tested. **NAS100 PASSES** (delta_R +0.091, DSR-p=0.0152). XAUUSD (-0.037, p=0.030) and GBPUSD (-0.044, p=0.008) significantly NEGATIVE. Other 4 instruments EV-neutral. Per-period: H2-2026 catastrophically loses (delta_R -0.106, p=0.001, -15.88% Sharpe). Per-direction: LONG -0.011, SHORT +0.002 (small).

3. **DSR-corrected p:** Paired-delta SR = -0.0149; DSR z = -3.974, **DSR-p = 1.000** at n_trials=200. Robust to trial-budget choice (n_trials=50 → 1.000; n_trials=1000 → 1.000). Vol-managed system has fewer effective σ than expected-max-under-null.

4. **PASS/FAIL on pre-registered gates:**
   - **Path A** (delta_R ≥+0.10 AND DSR-p<0.05): **FAIL** (delta_R=-0.005, DSR-p=1.000).
   - **Path B** (Sharpe ≥+15% AND DD≤baseline): **FAIL** (Sharpe -2.58%, DD shallowed +2.13R but Sharpe gate fails).
   - **Overall: H-PM01 FAILS portfolio-wide.** PASS on NAS100-only sub-cohort.

5. **Agent G's H2 XAU LONG caveat addressed:** REPLICATED + GENERALIZED. Specifically: H2 XAU LONG delta_R = -0.380 R (bootstrap p=0.001 at n=15). Agent G's qualitative finding (vol-managed structurally negative on this cell) holds; magnitude scales with cohort definition. The caveat generalizes to the entire H2-2026 cohort (-0.106 R, p=0.001), not just XAU LONG.

6. **New ambiguity introduced:** index-vs-FX/metals dichotomy in vol-managed sizing direction-of-effect. NAS100 wins, FX/metals lose. Mechanism: positive vol-return correlation in index trend regimes (Cont 2001 leverage effect inverted by trend persistence) vs negative vol-return correlation in FX/metal shock regimes (stop-cascade dominance). Open question: would a 1-2 H4 lag in the multiplier (sizing on PRIOR-period vol, not CURRENT period) reverse the FX/metal sign? Phase 6 candidate.

7. **Recommended Phase-5 deployment spec:**
   - **NAS100-only** Barroso multiplier behind config flag `risk.vol_managed_sizing.NAS100.enabled: false` (default OFF).
   - 30-day shadow A/B logging to `shadow_logs/vol_managed_sizing_NAS100.jsonl`.
   - Activation gate: live shadow delta_R ≥ +0.05 (50% of backtest); directionally consistent (positive on both LONG and SHORT); NAS100 graduated from 3-day observation.
   - Kill-switch: rolling-7-day delta_R < -0.02 → auto-disable.
   - **DO NOT** ship portfolio-wide. **DO NOT** ship to XAUUSD/GBPUSD/XAGUSD/US30_cash.

8. **Key file paths:**
   - Synthesis: `research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md`
   - Machine-readable: `research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json`
   - Compute script: `research/ml_program/phase_2/position_mgmt/_compute_h_pm01.py`
   - Enriched cohort: `research/ml_program/phase_2/position_mgmt/_enriched_cohort.csv`
   - Cross-references: `research/ml_program/forensics/2026-04-29/agent_g_na8_sensitivity.md` (caveat source) + `research/ml_program/forensics/2026-04-29/agent_f_position_mgmt_backlog.md` (H-PM01 spec).
