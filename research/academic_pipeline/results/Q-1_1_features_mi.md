# Q-1.1 — Features Mutual Information Audit

*Generated:* 2026-04-17T09:29:15.905817
*Script:* `scripts/q_1_1_mi_audit.py`
*Raw JSON:* `research/academic_pipeline/results/Q-1_1_features_mi.json`

## TL;DR

- **2 pre-trade feature(s)** exceed the 95th-percentile null threshold at n=111.
- **Top-3 by MI:** `sl_dollars_q` (MI=0.0609), `framework` (MI=0.0440), `ob_eval_reason_bucket` (MI=0.0375)
- **Headline negative result:** the canonical SMC quality features — `liquidity_pool_type`, `sweep_quality`, `displacement_quality`, `setup_grade`, `ob_eval_reason_bucket` — all show MI below 95th null. Conditional on the OB trigger having fired, these carry no detectable signal about win/loss.
- **Top 'significant' pre-trade feature:** `sl_dollars_q` (MI=0.0609, p=0.006) — but see caveats: effect is non-monotonic U-shape with Q3 at 88.9% WR and Q1/Q4 at ~50%, likely volatility-regime confounder, not a discriminative gate.
- **Top kill candidate:** `setup_grade` (MI=0.0001) — essentially zero information in a dataset where 72% of trades are graded 'A+'.
- **`framework`** significant (MI=0.0440, p=0.005) only because session_sweep (n=10, 20% WR) is a known-bad sub-framework — already handled: `enabled_frameworks: ["ob_retest"]`. No new action.
- **`kill_zone`** is borderline (MI=0.017, p=0.086): London 74.1% vs NY 56.6%. Below 95th null but worth shadow-logging.
- **Base rate:** 73/111 = 65.8% WR.
- **Post-hoc sanity PASSES:** `mae_r_q` MI=0.384 (p=0.000), `mfe_r_q` MI=0.091 (p=0.000). Pipeline behaves correctly — it detects known outcome-leaking features.

## Hypothesis (pre-data)

Prior beliefs registered before running MI computation:

| Feature | Prior | Reason |
|---|---|---|
| `daily_bias_match` | **signal** | Baseline Test A rerun: trend-aligned entries +17pp edge. |
| `kill_zone` | weak signal | XAUUSD sessions differ structurally; London = liquidity raid, NY = trend continuation. |
| `liquidity_pool_type` | **signal** | Asian_high/low vs PDH/PDL is the canonical SMC split. |
| `sweep_quality` | signal | Clean vs ambiguous sweep is a core OB prerequisite. |
| `displacement_quality` | **signal** | Strong displacement is the archetypal M15 entry trigger. |
| `setup_grade` | weak/none | A vs A+ scoring is human-ish; Q-scores proven r=-0.06 with wins (handoff 13). |
| `confidence_score_q` | **no signal** | Shadow mode, proven 98% rubber-stamp in prior audits. |
| `planned_rr_q` | weak/none | Downstream of zone geometry, not independent. |
| `sl_dollars_q` | weak/none | Scales with volatility, not setup quality. |
| `day_of_week` | **no signal** | Underpowered at n=111; ~22 trades/bucket. |
| `quarter` | **no signal** | Captures non-stationarity, not setup quality. |
| `ob_eval_reason_bucket` | signal | Captures setup completion status from analyzer text. |
| `framework` | weak | Dataset is 91% ob_retest — low variance. |
| `direction` | weak | Dataset is 93% LONG — low variance. |
| `daily_bias` | **constant** | 100% bullish in this dataset — MI undefined. |

## Data

- **Source:** `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base_backtest\analysis\unified_trades_v2_20260331.json`
- **n raw:** 111
- **n after cleaning:** 111 (dropped 0 missing outcome/r_multiple)
- **Base win rate:** 65.77% (73 wins / 38 losses)
- **Win definition:** `r_multiple > 0` (breakeven counts as loss)
- **Scope:** batch data only (2024-04-01 → 2026-03-13, XAUUSD). Pipeline_state had only one current snapshot (not joinable). Live trade records were NOT mixed per spec.

## Method

- **MI estimator:** `sklearn.feature_selection.mutual_info_classif(X, y, discrete_features=True, random_state=42)` (sklearn 1.8.0).
- **Encoding:** each categorical ordinal-encoded independently. Numerics (`planned_rr`, `sl_dollars`, `confidence_score`) discretized into sample quartiles.
- **Feature leakage:** `mfe_r`, `mae_r`, `hold_time_candles`, `r_multiple`, `exit_substate` excluded from the predictive set. Reported in post-hoc section only.
- **Null distribution:** 1000 permutations of `y`, MI recomputed per permutation. Report 95th percentile as significance threshold and 99th for tighter comparison. Empirical p = P(null MI >= observed MI).
- **Win-rate buckets:** reported alongside MI. Buckets with `n<20` flagged as underpowered.
- **Quartile cut points (Q1|Q2|Q3):** `planned_rr` at [2.500, 2.670, 2.800]; `sl_dollars` at [13.892, 27.190, 51.555]; `confidence_score` at [80.000, 80.000, 80.000] — note confidence collapses to a single value (80) in all quartiles; feature flagged as constant.

## Results — Pre-trade features (predictive)

Sorted by MI descending.

| # | Feature | MI | 95th null | 99th null | p-emp | Sig (>95th) | Unique | Underpowered buckets |
|---|---|---|---|---|---|---|---|---|
| 1 | `sl_dollars_q` | 0.0609 | 0.0436 | 0.0567 | 0.006 | YES | 5 | missing |
| 2 | `framework` | 0.0440 | 0.0155 | 0.0400 | 0.005 | YES | 2 | session_sweep |
| 3 | `ob_eval_reason_bucket` | 0.0375 | 0.0532 | 0.0690 | 0.228 | no | 6 | no_h1_break, bias_conflict, no_ob_match, price_not_at_ob |
| 4 | `planned_rr_q` | 0.0251 | 0.0414 | 0.0654 | 0.241 | no | 5 | Q4, missing |
| 5 | `quarter` | 0.0229 | 0.0670 | 0.0912 | 0.747 | no | 8 | 2024_Q2, 2024_Q3, 2024_Q4, 2025_Q2, 2025_Q3, 2025_Q4 |
| 6 | `kill_zone` | 0.0171 | 0.0194 | 0.0278 | 0.086 | no | 2 | — |
| 7 | `day_of_week` | 0.0154 | 0.0460 | 0.0664 | 0.522 | no | 5 | Friday |
| 8 | `liquidity_pool_type` | 0.0114 | 0.0715 | 0.0864 | 0.968 | no | 8 | session_high, asian_low, pdh, london_low, session_low, pdl |
| 9 | `sweep_quality` | 0.0056 | 0.0230 | 0.0349 | 0.690 | no | 3 | messy |
| 10 | `direction` | 0.0048 | 0.0316 | 0.0367 | 0.792 | no | 3 | SHORT, unknown |
| 11 | `daily_bias_match` | 0.0048 | 0.0316 | 0.0367 | 0.792 | no | 3 | mismatch, missing |
| 12 | `displacement_quality` | 0.0041 | 0.0287 | 0.0312 | 1.000 | no | 3 | weak, medium |
| 13 | `setup_grade` | 0.0001 | 0.0168 | 0.0307 | 1.000 | no | 2 | — |
| 14 | `daily_bias` | 0.0000 | n/a | n/a | n/a | no | 1 | — |
| 15 | `confidence_score_q` | 0.0000 | n/a | n/a | n/a | no | 1 | — |

### Per-feature win-rate breakdown (pre-trade)

**`sl_dollars_q`** — MI=0.0609, p=0.006
  - Buckets: Q4=15/28 (54%); Q1=14/28 (50%); Q3=24/27 (89%); Q2=19/27 (70%); missing=1/1 (100%)

**`framework`** — MI=0.0440, p=0.005
  - Buckets: ob_retest=71/101 (70%); session_sweep=2/10 (20%)

**`ob_eval_reason_bucket`** — MI=0.0375, p=0.228
  - Buckets: all_criteria_met=34/51 (67%); other_met=35/48 (73%); no_h1_break=1/5 (20%); no_ob_match=2/4 (50%); price_not_at_ob=1/2 (50%); bias_conflict=0/1 (0%)

**`planned_rr_q`** — MI=0.0251, p=0.241
  - Buckets: Q3=25/39 (64%); Q1=15/29 (52%); Q2=21/27 (78%); Q4=11/15 (73%); missing=1/1 (100%)

**`quarter`** — MI=0.0229, p=0.747
  - Buckets: 2025_Q1=20/30 (67%); 2026_Q1=18/29 (62%); 2025_Q4=15/19 (79%); 2025_Q2=7/15 (47%); 2025_Q3=6/8 (75%); 2024_Q3=4/5 (80%); 2024_Q2=2/3 (67%); 2024_Q4=1/2 (50%)

**`kill_zone`** — MI=0.0171, p=0.086
  - Buckets: london=43/58 (74%); ny=30/53 (57%)

**`day_of_week`** — MI=0.0154, p=0.522
  - Buckets: Tuesday=21/27 (78%); Thursday=13/23 (57%); Wednesday=14/22 (64%); Monday=14/20 (70%); Friday=11/19 (58%)

**`liquidity_pool_type`** — MI=0.0114, p=0.968
  - Buckets: none=31/45 (69%); asian_high=20/28 (71%); asian_low=10/17 (59%); pdh=5/7 (71%); session_high=2/4 (50%); london_low=2/4 (50%); pdl=2/4 (50%); session_low=1/2 (50%)

**`sweep_quality`** — MI=0.0056, p=0.690
  - Buckets: clean=41/65 (63%); ambiguous=31/45 (69%); messy=1/1 (100%)

**`direction`** — MI=0.0048, p=0.792
  - Buckets: LONG=68/103 (66%); SHORT=4/7 (57%); unknown=1/1 (100%)

**`daily_bias_match`** — MI=0.0048, p=0.792
  - Buckets: match=68/103 (66%); mismatch=4/7 (57%); missing=1/1 (100%)

**`displacement_quality`** — MI=0.0041, p=1.000
  - Buckets: strong=69/105 (66%); medium=3/5 (60%); weak=1/1 (100%)

**`setup_grade`** — MI=0.0001, p=1.000
  - Buckets: A+=53/80 (66%); A=20/31 (65%)

## Results — Post-hoc features (sanity, NOT predictive)

These leak outcome information by construction. Reported only to confirm MI pipeline behaves sensibly (high MI expected).

| # | Feature | MI | 95th null | p-emp | Sig (>95th) |
|---|---|---|---|---|---|
| 1 | `_posthoc_mae_r_q` | 0.3840 | 0.0371 | 0.000 | YES |
| 2 | `_posthoc_mfe_r_q` | 0.0909 | 0.0357 | 0.000 | YES |
| 3 | `_posthoc_hold_time_q` | 0.0159 | 0.0368 | 0.306 | no |

**`_posthoc_mae_r_q`** — MI=0.3840, p=0.000
  - Buckets: Q2=26/28 (93%); Q1=28/28 (100%); Q4=1/28 (4%); Q3=18/27 (67%)

**`_posthoc_mfe_r_q`** — MI=0.0909, p=0.000
  - Buckets: Q1=9/28 (32%); Q4=23/28 (82%); Q2=19/28 (68%); Q3=22/27 (81%)

**`_posthoc_hold_time_q`** — MI=0.0159, p=0.306
  - Buckets: 31-50=22/35 (63%); 11-30=16/29 (55%); 0-10=20/28 (71%); 51+=15/19 (79%)

## Recommendation

Verdict per pre-trade feature:

| Feature | MI | Verdict | Rationale |
|---|---|---|---|
| `sl_dollars_q` | 0.0609 | **DEFER (suspicious)** | MI=0.0609 significant but effect is non-monotonic: Q3 88.9% WR, Q2 70.4%, Q1/Q4 ~50%. U-shape suggests volatility-regime confounder, not a discriminative gate. Likely spurious at n=27-28 per bucket. Do NOT promote. Re-audit at n>=300 with regime-controlled split. |
| `framework` | 0.0440 | **KILL (already actioned)** | Significant only because session_sweep (n=10, 20% WR) is a known-bad sub-framework. `enabled_frameworks: ["ob_retest"]` in agent_config.yaml already removes it. No new action required. |
| `ob_eval_reason_bucket` | 0.0375 | **DEFER** | MI=0.0375, p=0.228. 'other_met' (72.9%) slightly beats 'all_criteria_met' (66.7%) but the non-success buckets are n<6 each — underpowered. Re-audit with larger live sample. |
| `planned_rr_q` | 0.0251 | **KILL** | MI=0.025 below null. Not an independent predictor. |
| `quarter` | 0.0229 | **KILL (for gating)** | MI=0.023 below null. Captures non-stationarity, not setup quality. Useful for regime analysis but not as a pre-trade gate. |
| `kill_zone` | 0.0171 | **DEFER (shadow log)** | MI=0.017 below 95th null (0.019), p=0.086 — just missed threshold. London 74.1% vs NY 56.6% is a 17.5pp gap worth tracking in live shadow logger. Promote if persists at n>=200. |
| `day_of_week` | 0.0154 | **KILL** | MI=0.0154 below null. Underpowered at ~22/bucket. No day-of-week edge visible at this n. |
| `liquidity_pool_type` | 0.0114 | **DEFER** | MI=0.011, far below null — but 6 of 8 buckets have n<20. Small-n MI estimator is unreliable here. Revisit at n>=300. |
| `sweep_quality` | 0.0056 | **KILL** | MI=0.0056 — no signal. 65 'clean' / 45 'ambiguous' trades have essentially equal WR conditional on the OB trigger. |
| `direction` | 0.0048 | **KILL** | 93% LONG — low variance. Revisit with bearish days. |
| `daily_bias_match` | 0.0048 | **DEFER** | Degenerate: daily_bias is constant so this reduces to `direction`. Revisit once dataset contains bearish-bias days. |
| `displacement_quality` | 0.0041 | **KILL** | MI=0.0041 — no signal. 95% of trades labelled 'strong' — low variance. |
| `setup_grade` | 0.0001 | **KILL** | MI=0.0001 — essentially zero information. 72% of trades graded 'A+' and A+/A win rates are nearly identical. Consistent with prior finding that Q-scores have r=-0.06 with wins (handoff 13). |
| `daily_bias` | 0.0000 | **KILL** | Constant (100% bullish) — zero variance, MI undefined. |
| `confidence_score_q` | 0.0000 | **KILL** | Constant after quartile binning (99% of scores = 80). Confidence_score is a rubber-stamp — already flagged in CLAUDE.md. |

**Summary:** 0 features promote to shadow logging from this audit alone. `framework` is technically significant but already actioned in production config. `sl_dollars_q` is significant but non-monotonic — flagged as suspicious, not promoted. `kill_zone` narrowly misses the 95th-null threshold but its 17.5pp London-vs-NY gap is worth tracking live.

**The key negative finding:** the canonical SMC 'quality' features the AI-prompt evaluates (pool type, sweep cleanliness, displacement strength) carry no detectable MI about outcome conditional on the OB trigger. This is consistent with the T6-T8 finding that Q-scores have r=-0.06 with wins — the edge is OB zone precision, not the quality overlay.

## Caveats

- **n=111 is small.** Chi-squared 95% power for a 15pp WR shift needs ~n=170 per arm. This audit can only detect large effects.
- **Multiple comparisons:** ~14 pre-trade features tested. Bonferroni-corrected threshold is 99.6th-percentile null (α=0.05/14). None of the currently-significant features clear that bar — verdicts labelled PROMOTE above are **discovery-tier**, not confirmatory.
- **Non-stationarity:** dataset spans 2024-04 to 2026-03. Q2 2026 (live period) NOT included — this is batch-only training data.
- **`daily_bias` constant:** the dataset contains zero bearish-bias trades. `daily_bias_match` is therefore uninformative here; revisit once bearish days appear.
- **`direction` skew:** 103/111 LONG. Any feature interacting with direction has low variance.
- **Underpowered buckets:** flagged in the main table. `liquidity_pool_type` has 6 of 8 buckets under n=20. MI is biased upward for high-cardinality features — null-distribution threshold compensates for this, but bucket-level WR claims should be treated as exploratory.
- **Batch vs live:** batch data uses the pre-T7 prompt. Live T7 data has different CR (38%) and WR (71.4%). Feature relationships may shift.
- **Binning choices:** numerics binned into sample quartiles per-feature. Alternative binnings (equal-width, entropy-based) were not explored.
- **BE treatment:** 3 breakeven trades counted as losses under `r_multiple > 0`. Recomputing with BE=win does not change top-rank ordering (verified manually).

## Next steps

**No feature promoted from this audit.** The two MI-significant features (`framework`, `sl_dollars_q`) either correspond to an already-actioned production choice or appear spurious.

Recommended actions:

- **Shadow-log `kill_zone` in live pipeline.** London 74.1% vs NY 56.6% (n=58 vs n=53) just below the 95th null. If this persists over +50 live trades, reconsider NY session filter. File: extend `shadow_logs/feature_mi_log.jsonl`.
- **Do NOT deploy `sl_dollars_q` as a gate.** U-shape pattern (Q3=88.9%, Q1/Q4~50%) looks like volatility-regime leakage, not a real gate. Flag for regime-stratified re-analysis at n>=300.
- **Revisit `liquidity_pool_type` at n>=300.** 6 of 8 buckets are underpowered in this dataset. The SMC prior on pool-type differentiation is strong enough to warrant a more powerful test.
- **Wait for bearish-bias trades** before treating `daily_bias_match` as evaluable. Current dataset is 100% bullish-bias.

Additional follow-up research questions:

- **Q-1.2 (interactions):** univariate MI misses joint effects. Once n>=200, compute MI of pairs `kill_zone × liquidity_pool_type`, `sweep_quality × displacement_quality`, etc.
- **Q-1.3 (direction/bias asymmetry):** rerun once bearish-bias trades exist.
- **Q-1.4 (live-T7 vs batch):** rerun MI on T7 live trades only when n>=50. Live data has different CR/WR — may expose different feature importances.
- **Cross-check with L1-logit:** fit penalized logistic regression with all features; compare non-zero coefficients to top-MI features. Expect same null result at n=111.
- **Bayesian analysis:** with informed priors over each feature's WR effect, compute posterior on effect size for the top 3. At n=111 the posterior will be wide, which is the honest takeaway.

## Appendix — feature encoding details

- `daily_bias_match`: `match` if direction agrees with daily_bias, else `mismatch`, else `missing`.
- `quarter`: month bucketed into calendar quarters (YYYY_Qn).
- `ob_eval_reason_bucket`: 28 unique strings collapsed into 6 buckets (`all_criteria_met`, `no_h1_break`, `no_ob_match`, `price_not_at_ob`, `bias_conflict`, `other_met`).
- `planned_rr_q`, `sl_dollars_q`, `confidence_score_q`: sample quartiles (Q1/Q2/Q3/Q4).
- `_posthoc_hold_time_q`: bucketed as 0-10, 11-30, 31-50, 51+ candles.

---

*Prepared for CEO Borhen — Q-1.1 audit, autonomous agent deliverable.*
