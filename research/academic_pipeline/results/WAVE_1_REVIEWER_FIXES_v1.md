# Wave 1 Reviewer Fixes - Summary

**Generated:** 2026-04-17
**Author:** GTOS research agent (Claude Code)
**Scope:** 5 issues flagged by Wave 1 reviewers; each fix ships as a versioned v2 artefact alongside the untouched v1.
**Ground rules:** no production code modified; no v1 files deleted; every script is deterministic (seed 42) and re-runnable.

---

## Issue 1 (CRITICAL): Q-5/Q-6 Kelly Monte Carlo ignored H29 drawdown brake

### Root cause

`research/academic_pipeline/scripts/Q5_Q6_exit_engineering.py` computed the Monte
Carlo equity path with a **constant** risk fraction across all 200 simulated
trades per path:

```python
# v1 (simplified)
path_factors = 1.0 + risk_frac * sampled
equity = start_equity * np.cumprod(path_factors, axis=1)
```

Production risk is NOT constant: `H29` (drawdown_manager.py) drops risk from
2.0% to 0.5% when drawdown from equity peak >= 8%, then restores normal risk on
a new equity high. Q-7 already applied H29 correctly in its own MC; Q-5/Q-6 did
not. At 2% risk the simulated P(breach) was therefore inflated and P(pass)
deflated by a meaningful margin.

### What changed in v2

- New script: `research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py`
- `mc_equity()` now has an `h29=False/True` flag.
  - `h29=True` switches to a per-iteration state-machine loop: track
    `equity_peak`, compute `dd_from_peak`, and use `H29_REDUCED_RISK=0.005`
    whenever `dd_from_peak >= H29_TRIGGER=0.08`, else `risk_frac`.
  - Normal risk is restored on a new peak.
- Runs BOTH v1 (no H29) and v2 (H29 on) MC tables side-by-side with the same
  seed (42) for direct comparability.
- Adds a `delta_v1_vs_v2` table with pp deltas per risk level.
- Exit-rule DD columns (`rule_dd_v1_no_h29` and `rule_dd_v2_with_h29`) are
  also computed side-by-side for Q-6.8.

Outputs:
- `research/academic_pipeline/results/Q-5_Q-6_exits_v2.md`
- `research/academic_pipeline/results/Q-5_Q-6_exits_v2.json`

### Delta numbers (v1 -> v2)

FTMO $100K static-DD 200-trade Monte Carlo (n_iter=10,000, seed=42):

| Risk | P(pass) v1 | P(pass) v2 | Delta   | P(DD>=10%) v1 | P(DD>=10%) v2 | Delta     |
|------|------------|------------|---------|---------------|---------------|-----------|
| 0.25% | 4.17%     | 3.85%      | -0.32pp | 0.00%         | 0.00%         | +0.00pp   |
| 0.50% | 51.88%    | 52.01%     | +0.13pp | 0.01%         | 0.02%         | +0.01pp   |
| 1.00% | 81.76%    | 81.77%     | +0.01pp | 3.82%         | 2.16%         | -1.66pp   |
| 1.50% | 74.48%    | 78.97%     | +4.49pp | 22.52%        | 13.46%        | -9.06pp   |
| 2.00% | 51.15%    | 60.38%     | +9.23pp | 48.50%        | 36.77%        | -11.73pp  |

**Interpretation.** At 2% risk (the production risk-per-trade), v1 overstated
the breach probability by ~12pp and understated pass probability by ~9pp. At
1% risk (the profile currently recommended per handoff 19) the effect is only
~2pp on P(DD>=10%). Reviewer concern confirmed: the H29 brake materially
changes the 2% risk conclusion.

---

## Issue 2 (MAJOR): Q-7 Monte Carlo WIN/LOSS/BE counts inconsistent; misleading "P(daily DD)" column

### Root cause

1. **Count mismatch.** `research/academic_pipeline/scripts/q_7_monte_carlo.py`
   line 389 hard-coded the text "72 WIN, 36 LOSS, 3 BE" but the MC computed
   WR via `wr_batch = (r_dist > 0).mean()`, which treats r=0 as "not win"
   and r>0 as win. In the actual batch:
   - `outcome` field says WIN=72, LOSS=36, BREAKEVEN=3 (n=111)
   - `r_multiple > 0` says 73 "wins", `r_multiple < 0` says 37 "losses", 1 zero
   - The 2-trade discrepancy between the two conventions comes from two BE
     trades with non-zero r_multiple (`bt_2025-02-19_ny_001`=+0.02,
     `bt_2025-12-23_ny_001`=-0.01).
   - v1's reported WR (0.6577) silently used r>0/N=111 which mixes conventions.
2. **Misleading column.** The Survival table had `P(daily DD breach)` which
   was always 0.00% because the daily DD logic only counted single-trade
   equity drops >=5%; this does NOT match FTMO's daily 5% rule (which is
   calendar-day cumulative, measured vs start-of-day equity). The label
   therefore created the impression that "FTMO daily DD is never breached".

### What changed in v2

- New script: `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`
- Counts come from `outcome` field: `n_win=72, n_loss=36, n_be=3`.
- WR uses standard BE-excluded convention:
  `wr_v2 = n_win / (n_win + n_loss) = 72/(72+36) = 0.6667`.
- MC draws still use the full 111-row `r_multiple` distribution (so BE trades'
  tiny real returns remain in the path), but the headline WR figure no longer
  contradicts the outcome labels.
- `P(daily DD breach)` column renamed to `P(trade-level drop >= 5%)` with an
  explanatory footnote: "NOT the FTMO calendar-day 5% rule; this is the
  fraction of MC trades whose single-trade outcome drops equity by >=5%
  from the trade open."
- The v1 WR (0.6577) is reported alongside the v2 WR (0.6667) as
  `wr_v1_implicit_r_gt_0_over_N` in the JSON so the auditor can see both.

Outputs:
- `research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.md`
- `research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.json`

### Delta numbers (v1 -> v2)

| Quantity | v1 | v2 |
|----------|-----|-----|
| Batch counts | "72 WIN, 36 LOSS, 3 BE" (printed text) but WR math used r>0/N convention | `counts = {WIN:72, LOSS:36, BE:3, N_BATCH:111}` (explicit) |
| WR | 0.6577 (= 73/111, r>0 convention) | 0.6667 (= 72/108, BE-excluded) |
| Daily DD column label | "P(daily DD breach)" (=0 everywhere, misleading re FTMO) | "P(trade-level drop >= 5%)" with footnote disclaiming FTMO link |
| FTMO optimum (1%) | P(pass)=98.3% | P(pass)=98.3% (unchanged - MC r_multiple distribution unchanged) |

The MC output is essentially unchanged (numerically) because WR enters only the
r_multiple empirical draw, which still uses all 111 rows. The fix is
presentational: documentation, counts, and column labels now match the data.

---

## Issue 3 (MAJOR): Q-10 macro USDJPY proxy correlation was circular

### Root cause

`research/academic_pipeline/scripts/q_10_macro.py` justified the USDJPY proxy by
computing `corr(USDJPY_ret, 0.5*USDJPY_ret + 0.5*inv_GBPUSD_ret) = 0.913`.
USDJPY appears on BOTH sides of the correlation. The reported r is mechanically
bounded below by ~`sd_USDJPY / sqrt(sd_USDJPY^2 + sd_invGBPUSD^2)` by
construction, even if the cross-pair correlation is exactly zero. The 0.913
number therefore does not measure proxy quality.

### What changed in v2

- New script: `research/academic_pipeline/scripts/q_10_macro_v2.py`
- `compute_proxy_sanity_v2()` now returns:
  - **Non-circular** `r(USDJPY_ret, inv_GBPUSD_ret)` — cross-correlation of two
    independent USD-base daily returns. USDJPY appears on the left only;
    inv-GBPUSD appears on the right only. This is the real proxy-quality number.
  - v1 circular number reproduced under
    `circular_v1_reproduced.r_usdjpy_vs_basket_0p5_usdjpy_0p5_invgbpusd`
    and labelled CIRCULAR, with a verification that it equals the closed-form
    algebraic identity
    `r_circ = (sd_x + r_off sd_y) / sqrt(sd_x^2 + 2 r_off sd_x sd_y + sd_y^2)`.
- Markdown report has a "v1 circular number (reproduced for audit)" subsection
  that shows the identity numerically so the reader can see why the circular
  number is inflated.
- Recommendation text annotates the Q-10.1 verdict with proxy-quality
  context from the non-circular number.

Outputs:
- `research/academic_pipeline/results/Q-10_macro_v2.md`
- `research/academic_pipeline/results/Q-10_macro_v2.json`

### Delta numbers (v1 -> v2)

| Quantity | v1 (circular) | v2 (non-circular) |
|----------|--------------|-------------------|
| USDJPY <-> (0.5 USDJPY + 0.5 inv-GBPUSD) | 0.9131 | 0.9131 (reproduced, flagged circular) |
| USDJPY <-> inv-GBPUSD (the real proxy test) | not computed | **0.6329** (n=71 days) |
| Algebraic identity match | not verified | yes (delta < 1e-9 from identity formula) |
| Proxy-quality label | "defensible but imperfect" (based on 0.913) | "moderate - shared USD factor visible but not dominant" (based on 0.633) |

**Interpretation.** Proxy quality is real but much weaker than v1's 0.913
implied. USDJPY + inv-GBPUSD together capture ~25.5% of DXY weight (JPY 13.6%
+ GBP 11.9%); no EUR pair is available. The Q-10.1 alignment-effect verdict
(28 pp headline with Fisher p=0.31, n too small) is unchanged; v2 just stops
using 0.913 to argue the proxy is solid.

---

## Issue 4 (MAJOR): live_breakdowns schema bug + denominator inconsistencies

### Root cause

1. **Wrong field name.** `live_breakdowns.py:load_live_closed_trades()` looked
   for a top-level `trade_outcome` field that does not exist. The real schema
   puts live-trade outcome in a top-level `exit` field (shape
   `{exit_reason, exit_price, exit_time, realised_r_multiple, ...}`).
   The v1 script silently returned 0 closed trades; the 0 happened to be
   correct (no records have non-null `exit` yet) but only by accident.
2. **Arithmetic inconsistency.** The report claimed "22/47 L2 rejections (47%)"
   for `entry_in_ob`. Inspection shows `sum(l2_reasons.values()) = 49`
   because the L2 reason Counter includes 2 `post_m5_refinement_failed`
   entries from REJECTED_L2_POST_M5 records. So the denominators floating
   around the report are 47 (REJECTED_L2 pure), 49 (L2-reason Counter total),
   and sometimes neither label was spelled out.
3. **"78% / 7 of 9"** (sl_too_tight SL/ATR >= 1.0): mathematically correct
   (7/9 = 77.8%) but not visually reproduced; a reviewer had to reconstruct
   the arithmetic from the raw ratio list.

### What changed in v2

- New script: `research/academic_pipeline/scripts/live_breakdowns_v2.py`
- `load_live_closed_trades_v2()` reads the real top-level `exit` field and
  `exit.realised_r_multiple` (with defensive fallback to
  `execution.realised_r_multiple`). Returns a `schema_stats` dict alongside
  the trade list so the reviewer can verify counts directly.
- New "Schema verification" section at the top of the report prints:
  - files parsed = 85
  - `exit` field present at top level = 85
  - `exit` field non-null = **0**
  - `execution.realised_r_multiple` present = 0
  - records with any usable r_multiple = 0
  So "0 live closed trades" is now provably real, not a bug symptom.
- L2 rejection table uses **two** denominator columns, both spelled out:
  - `% of L2-reason Counter (n=49)`
  - `% of REJECTED_L2 pure (n=47)`
- `sl_too_tight` section lists the raw SL/ATR ratios in sorted order AND
  the tallies `n_ge_1.0 = 7/9`, `n_ge_1.2 = 7/9`, `n_ge_1.5 = 0/9` each with
  the percentage.
- JSON output includes explicit `denominators` object:
  `{REJECTED_L2_pure: 47, REJECTED_L2_family: 49, l2_reason_counter_total: 49}`.

Outputs:
- `research/academic_pipeline/results/live_breakdowns_v2.md`
- `research/academic_pipeline/results/live_breakdowns_v2.json`

### Delta numbers (v1 -> v2)

| Quantity | v1 | v2 |
|----------|-----|-----|
| Live closed trades discovery | 0 (via nonexistent `trade_outcome` field) | 0 (via real `exit` field, schema-proven) |
| `entry_in_ob` share | "22/47 (47%)" | "22 of 47 REJECTED_L2 pure (46.8%), 22 of 49 L2-reason Counter (44.9%)" |
| `sl_beyond_ob` share | "19 of 47" implied | "19 of 47 REJECTED_L2 pure (40.4%), 19 of 49 L2-reason Counter (38.8%)" |
| sl_too_tight SL/ATR >= 1.0 | "7 of 9 (78%)" | "7 of 9 (77.8%)" with full sorted ratio list, `ob_retest_sl_exception` bypass unblocks 7/9 (77.8%) |
| L1 top reason count | 9 of 13 | 9 of 13 (69.2%) |
| Schema audit section | absent | present (5-row table proves exit field is real but null) |

---

## Issue 5 (MINOR): Q-4 Q-1.2 verdict too strong at n=28

### Root cause

`research/academic_pipeline/results/Q-4_entry_engineering.md` verdict line 49:

> Verdict: promote_as_nonmonotonic - MI perm p=0.027 (signal present) but
> linear tests flat

At n_matched = 28 with only one of three tests significant (MI perm p=0.027,
Pearson p=0.996, point-biserial p=0.916) and quartile buckets of n=7 each, the
"promote" language is above the evidence level. A Bonferroni correction over
the 10+ sub-tests in the Q-series lifts the MI perm threshold to ~p<0.005.

### What changed in v2

- New results file: `research/academic_pipeline/results/Q-4_entry_engineering_v2.md`
- Q-1.2 verdict: `promote_as_nonmonotonic` -> `defer_pending_replication`.
- New "Recalibration note (v2)" section explaining the four reasons the
  evidence does not support promotion (small n, single significant test out of
  three, pre-registered prediction was "no signal" and observed was marginal,
  no clean mechanism).
- Explicit replication plan: re-run on full 2024-04..2026-04 window with
  target n_matched >= 90; require MI p < 0.01 AND at least one of
  {Pearson, point-biserial, Spearman} with p < 0.05 in the same direction
  before any shadow-gate promotion.
- Quartile WR table unchanged; all numbers preserved. Q-4.3 and Q-4.4
  verdicts unchanged (they were already correctly `defer`).

### Delta numbers (v1 -> v2)

| Quantity | v1 | v2 |
|----------|-----|-----|
| Q-1.2 verdict | `promote_as_nonmonotonic` | `defer_pending_replication` |
| Promotion requirement | (implicit - one positive test) | MI p<0.01 AND one linear test p<0.05 in same direction, n>=90 |
| Other Q-4 verdicts | `defer`, `defer_data_gap` x2 | unchanged |
| Numerical results | MI=0.19, MI perm p=0.027, quartile WRs 42.9/42.9/85.7/71.4% | identical |

---

## Deferred items (with reasons)

These are NOT fixed in this wave because they either require data outside the
repo or would change production behaviour:

1. **Q-10.2 economic-calendar overlap gap** (unchanged from v1): current
   calendar starts 2026-04-01, batch ends 2026-03-13, zero overlap. Blocker is
   external - need a back-dated ForexFactory or Econoday HIGH-impact feed for
   2024-04 through 2026-03. Q-10 v2 retains the `DATA_GAP_STOP` verdict.
2. **Q-4.4 touch count** still `defer_data_gap`: batch JSON lacks
   `touch_count` field; live records have it but n<10. Fix requires
   `proximity_shadow_logger` to log `touch_count` at CANDIDATE time; waiting
   for 50+ live-candidate samples.
3. **Q-4.4 OB depth** still `defer_data_gap`: batch JSON lacks
   `ob_high`/`ob_low`. Fix requires modifying `simulate_t7_live_period.py` to
   persist OB bounds; non-trivial re-run cost (~$20+ simulation spend).
4. **Q-7 daily-DD proper semantics**: the v2 fix renames and footnotes the
   column, but a truly faithful daily-DD calculation would require simulating
   calendar days with multiple trades per day rather than single-trade MC.
   This is an architectural change to the MC, deferred pending reviewer
   go-ahead.
5. **Live closed-trade data** (0 of 85 records populated): live window is
   short (Apr 6-17). The `exit` writer in `_finalize_exit()` has to fire; per
   handoff 17 there is a pre-existing bug where `_active_trade_record` is
   never set on limit-fill paths. Production fix is pending CEO approval
   (handoff 17 item). Once that lands, v2's schema-aware loader will pick up
   live closed trades automatically.

---

## Files added (v2 artefacts)

Scripts:
- `research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py`
- `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`
- `research/academic_pipeline/scripts/q_10_macro_v2.py`
- `research/academic_pipeline/scripts/live_breakdowns_v2.py`

Result files:
- `research/academic_pipeline/results/Q-5_Q-6_exits_v2.md` + `.json`
- `research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.md` + `.json`
- `research/academic_pipeline/results/Q-10_macro_v2.md` + `.json`
- `research/academic_pipeline/results/live_breakdowns_v2.md` + `.json`
- `research/academic_pipeline/results/Q-4_entry_engineering_v2.md`
- `research/academic_pipeline/results/WAVE_1_REVIEWER_FIXES_v1.md` (this file)

Files NOT modified:
- All v1 scripts (`Q5_Q6_exit_engineering.py`, `q_7_monte_carlo.py`,
  `q_10_macro.py`, `live_breakdowns.py`)
- All v1 result files (same base names without `_v2` suffix)
- All production code under `src/`, `prompts/`, `config/`

---

## Reproducibility

All v2 scripts are deterministic (numpy `default_rng(42)`) and produce
identical output on rerun. To regenerate all v2 artefacts from scratch:

```bash
python research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py
python research/academic_pipeline/scripts/q_7_monte_carlo_v2.py
python research/academic_pipeline/scripts/q_10_macro_v2.py
python research/academic_pipeline/scripts/live_breakdowns_v2.py
# Q-4 v2 is a hand-edited md (no script regeneration needed; numbers taken from
# v1's already-deterministic entry_engineering.py output).
```

Total compute cost: zero API spend, ~30 seconds of local CPU.
