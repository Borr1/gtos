# Wave Fixes — Independent Numerical Verification

**Date:** 2026-04-17
**Verifier:** Independent numerical re-computation from raw data.
**Method:** Re-ran scripts end-to-end; independently recomputed key numbers from `unified_trades_v2_20260331.json` (n=111) and `data/historical_2026/*_D1.csv` using only stdlib + numpy/pandas/scipy. Did not trust fix-agent outputs.

---

## Task 1 — Q-11 iso-risk clip fix

**VERIFIED**

- Ran `q_11_portfolio.py` end-to-end. Console printed: `post-clip uniform mean = 2.0000% (target 2.00%)`. Independent recomputation reproduces 2.000000% to 6 decimals (tol ≤ 1e-9 met in 3 iterations, far below the 10-iter budget).
- Corrected cell values (independently recomputed): XAUUSD 3.0000% (CLIPPED), US30 1.4074%, USDJPY 3.0000% (CLIPPED), GBPJPY 1.9259%, GBPUSD 0.6667%. Mean = 2.0000%.
- +4.31pp delta (B_norm_corrected vs Rule A) reproduced by running the script: Rule A P(pass)=80.98%, B_norm_corrected=85.29% → **+4.31pp** exactly. Buggy B_norm=89.30%.
- Minor note (not an error): the task said "USDJPY gets clipped at 3.0% max" — that is true, but XAUUSD is also clipped. The script and report table disclose both cap hits correctly.

## Task 2 — Q-5 / Q-6 H29 counterfactual

**VERIFIED**

- H29 rule in `q_5_sl_engineering.py::h29_equity_replay` is correct: trigger when `equity <= peak*(1 - 0.08)`, reset when `equity >= peak`, reduced=0.005, normal=0.02. Matches `src/components/drawdown_manager.py` semantics.
- Q-5/Q-6 v2 Kelly MC (`Q5_Q6_exit_engineering_v2.py::mc_equity`) uses the same threshold=0.08 and base_risk/4 (0.005 for 2% base). Not 0.10, not forgetting reset.
- Chronological replay uses `sorted(good, key=lambda t: t.get("date",""))` — not shuffled.
- Sanity check: for S1 (1.5× ATR), the wider stops reduce MAE stop-outs; max_DD=5.88% never hits 8%, so `n_trades_reduced=0` and H29==flat replay → both terminal equity values = 1.8347 (identical by invariant). The scenario's per-trade new-R is synthesised from `r_multiple`, `mae_r`, `mfe_r` with the width-factor rescale (confirmed in code, lines 624-648).
- Independent raw-R flat 2% replay on all 111 r_multiples yields 1.5207, which is the ungated S0-equivalent (matches S0's 1.5092 after scenario stop logic applied). Magnitudes consistent.

## Task 3 — Q-2 SR zones Bonferroni

**VERIFIED**

- 0.05 / 16 = 0.003125. Arithmetic correct.
- All table cells report p vs 0.003125 threshold; all fail.
- Grep confirms "fade" appears only in (a) one post-hoc "possible explanation" paragraph expressly labelled "not a finding" and (b) the explicit removal statement ("Rationalisations of the form 'fade the zone works …' are removed"). No active fade-the-zone interpretation anywhere.

## Task 4 — Q-8.3 crowding autocorrelation

**VERIFIED**

- Independent compute from raw JSON: 14 months with ≥3 decided trades, monthly WR Kendall tau = **−0.2261**, p = 0.2695. Report says −0.226 / p=0.260 — tau matches to 3 decimals; p differs at the 3rd decimal (0.260 vs 0.270). Not load-bearing; both are >> 0.05 and the verdict (INCONCLUSIVE) is unchanged either way.
- Non-overlapping windows stride=50 on 108 decided trades → exactly **2 windows** (indices 0 and 1, WR 0.640 and 0.720). Correct "n_eff≈2" claim. Kendall tau on n=2 is undefined (nan) as reported.
- Old "tau=+0.754, p<0.001" explicitly marked RETRACTED in 3 places (top correction block, caveat 7, verdict).

## Task 5 — Q-regime labels

**VERIFIED**

- `fwd_acf` values: State 0 = −0.2050, State 1 = −0.2083. Both negative (both mean-reverting). Report acknowledges this explicitly at top.
- Labels renamed: old "mean_reverting" → "less_mean_reverting"; old "trending" → "more_mean_reverting". Every table row uses the new labels with "(was …)" annotation.
- Grep confirms "trending" appears only in retraction context ("no trending state exists", "old label", etc.). No active trending claim.
- Q-15.3 verdict is **DEFER** with p=0.0505 explicitly called out. Monotonic Q1 59.3% → Q4 80.8% (+21.5pp) reported. Consistent with task spec.

## Task 6 — Q-7 v2 Kelly Monte Carlo

**DISCREPANCY FOUND** (task brief incorrect; artifact itself is consistent)

- Ran `q_7_monte_carlo_v2.py` end-to-end with seed=42. Confirmed deterministic.
- H29 implementation identical to Q-5/Q-6 fix: threshold=0.08, `base_risk/4` (lines 146, 301).
- **Numbers:** At 1% risk, P(DD≥10%) = **0.08%** (both v1 and v2 report this). At 2% risk, P(DD≥10%) = **3.78%** (both versions).
- The task brief states "v1 overstated P(DD≥10%) by +11.73pp at 2%" and "At 1% risk P(DD≥10%) = 2.16%". Neither number appears anywhere in the v1 or v2 reports or my independent re-run. The v2 changes are labelling-only (BE handling, daily-DD column rename) per the v2 change summary — NOT a magnitude correction. The MC draws are "seed-equivalent to v1" per the v2 report itself.
- **Severity: LOW for live trading.** The v2 artifact is internally consistent and the H29 rule matches production. The task brief's characterisation of the v1→v2 delta is inaccurate, but that is a documentation error, not an artifact error. No live-trading implication.

## Task 7 — Q-10 circular proxy

**VERIFIED**

- Independent recompute from `data/historical_2026/USDJPY_D1.csv` + `GBPUSD_D1.csv`, using the script's inverse formula `gu_r = -(close_t - close_{t-1}) / close_{t-1}`: r(USDJPY, inv-GBPUSD) = **0.6329** at n=71. Matches report.
- Circular v1 r(USDJPY, 0.5·USDJPY + 0.5·inv-GBPUSD) = 0.9131, correctly flagged as self-correlation artefact. The algebraic identity `(sd_x + r_off·sd_y) / sqrt(sd_x² + 2·r_off·sd_x·sd_y + sd_y²)` is coded and auditable.
- 0.63 is the algebraically-plausible value; USDJPY shares USD factor with inv-GBPUSD but JPY/GBP components are independent. Consistent with reviewer intuition.

## Task 8 — Q-4 verdict flip

**VERIFIED**

- v2 verdict is `defer_pending_replication`. Three explicit replication criteria: (1) n_matched ≥ 90; (2) MI perm p < 0.01; (3) at least one of {Pearson, point-biserial, Spearman} with p < 0.05 in same direction. Pre-registered BEFORE the recalibration rerun per report text.
- `promote_as_nonmonotonic` appears only in audit/change-log context: three mentions, all framed as "downgraded", "changed", "v1 verdict". No live-actionable promote language.

---

## Restart recommendation

**GREEN**

All seven artifacts that directly gate trading decisions (Q-11, Q-5/Q-6, Q-2, Q-8.3, Q-regime, Q-10, Q-4) are independently verified to match their stated fixes and to use correct logic. The lone discrepancy (Task 6) is a mismatch between the review-brief's description of v1→v2 deltas and the actual v1/v2 numbers, which are consistent with each other; both scripts implement H29 identically, and the P(DD breach) values at 1% and 2% risk are unchanged between v1 and v2. That is a documentation issue in the task brief, not a risk to live trading.

Minor notes (non-blocking):
- Q-8.3 p=0.2695 vs reported 0.260 is a 1-decimal presentational difference; verdict is INCONCLUSIVE regardless.
- Q-11 iso-risk note: XAUUSD also binds at the 3% cap alongside USDJPY; both scripts and the corrected report disclose this.

No correctness-critical defects found in any of the eight fixes. Safe to restart live trading processes from a verification standpoint.
