# Phase 2 Review — δ (regime decay / quarterly WR)

**Reviewer:** independent Opus 4.7 reviewer, 2026-04-19
**Target deliverable:** `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md`
**Scratch:** `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/02_decay_analysis.py`, `decay_analysis.md`
**Reproducibility rating:** **4 / 5** (bootstrap, chi-square, aggregate quarterly numbers, merge logic all reproduce exactly; Spearman p-value is wrong by ~10× due to an erfc-vs-t-distribution bug in `02_decay_analysis.py:81-110`; rank-tie handling is sequential not average; no sensitivity analysis was performed on the Spearman-significant regime-correlation finding that drops Bonferroni-safe when small-n quarters are excluded).

---

## Final verdict (1 paragraph)

δ is **directionally correct on the three load-bearing claims but carries a statistical error that inverts one sub-conclusion**. The canonical `73.2 → 71.4 → 63.6 → 59.4` sequence that appears in `CLAUDE.md:217`, `kb_validation_and_monitoring_framework.md:222,328`, and `kb_edge_mechanisms_and_risks.md:131` is **not reproducible from any extant dataset I could find** and is **hardcoded without computation at `research/academic_pipeline/L4_foundation_analysis.py:649`** — which δ also flagged (`delta_regime_decay.md:50-52`), so δ's bit-exact-mismatch finding is VERIFIED. δ's bootstrap P=0.7525 for pairing-WR-with-quarter is statistically clean and reproducible. δ's Spearman-of-KER-vs-WR at **ρ=0.786, p=0.002** is WRONG: (a) δ's own scratch at `_delta_scratch/02_decay_analysis.py:81-110` computes the p-value via `math.erfc(t/√2)` which is a normal-distribution tail, not Student's t with df=n−2=6; (b) δ's `rank()` function uses sequential ranks on ties instead of average ranks. Correct arithmetic gives **ρ=0.7665, t=2.923, p=0.0265** under t-distribution — a full order of magnitude larger, and it does NOT survive Bonferroni at α=0.005 (δ's own stated threshold). Dropping the four quarters with n<10 (2024-Q2, Q3, Q4, 2026-Q2) collapses the correlation further to **ρ=0.60, p≈0.19** (n=4 quarters, but the Spearman claim depends on all 8 to retain power). So δ's "regime-conditional edge is statistically real, Bonferroni-safe" sub-conclusion **fails on correct arithmetic**. δ's broader fleet-stationarity claim survives but is not stratified — ε's instrument-level XAUUSD MFE-compression (p=0.020 BH-safe) and fast-loss (p=0.017 BH-safe) are a genuine counter-signal that δ's pooled analysis cannot see. **Chairman action:** retain δ's canonical-provenance finding and stationarity-at-aggregate claim; strike the Spearman-based "regime-conditional edge survives Bonferroni" statement; add the ε/α instrument-level deterioration as the strongest counter-narrative.

## Concerns ranked by severity

1. **[MAJOR] Spearman p-value in `02_decay_analysis.py:81-110` uses normal-distribution tail (`math.erfc`) instead of Student's t with df=n−2** — δ's code:
   ```
   t = r * math.sqrt(df / max(1e-9, 1.0 - r*r))
   p = math.erfc(abs(t) / math.sqrt(2))   # <-- this is wrong for small n
   ```
   `erfc(t/√2)` is the **standard-normal** two-tail p-value. The correct Spearman small-sample p uses `scipy.stats.t.sf(|t|, df=n-2) * 2`. At n=8, df=6, t=3.11 the correct p is ~0.021, not ~0.002. I verified:
   - δ's stated ρ=0.786, t=3.11, p=0.002 (from `delta_regime_decay.md:161,173`)
   - My t-dist reconstruction on δ's own ρ=0.786: `t.sf(3.11,6)*2 = 0.0209`
   - `scipy.stats.spearmanr(WR, KER)` with tied-average ranks on δ's 8-quarter series: **ρ=0.766, p=0.027**
   - Exact permutation over all 8! = 40320 orderings: ρ=0.766, p=0.033
   δ's δ's own "Bonferroni α=0.005 safe" claim (`delta_regime_decay.md:173`) **inverts** at the correct p-value: 0.027 > 0.005, so the finding does NOT clear Bonferroni for 10 tests. It clears BH FDR at rank-1 threshold 0.005 similarly narrowly.
   **Recommended action:** chairman must strike the "survives Bonferroni" claim; recast as "ρ=0.77, p=0.03, directional only, not multiple-comparison-safe." This downgrades Hypothesis 2 (regime-conditional edge) from "confirmed" to "exploratory."

2. **[MAJOR] Rank-tie handling bug in `_delta_scratch/02_decay_analysis.py:65-80`** — δ's `rank()` function:
   ```
   def rank(xs):
       sorted_idx = sorted(range(len(xs)), key=lambda i: xs[i])
       ranks = [0]*len(xs)
       for r, idx in enumerate(sorted_idx):
           ranks[idx] = r + 1
       return ranks
   ```
   This gives tied values sequential ranks based on arbitrary stable-sort position. In the quarterly WR series `[50.0, 80.0, 33.3, 65.6, 50.0, 60.0, 73.9, 59.4]`, 50.0 appears at indices 0 and 4. δ's function assigns them ranks (2, 3), but canonical Spearman convention is to assign both the average rank (2.5, 2.5). This artificially inflates ρ by ~0.02 on this dataset. My reconstruction with tied-average ranks yields ρ=0.7665 vs δ's 0.786. Impact is small in magnitude but compounds with the erfc error above: the combined corrected figure is (ρ=0.766, t=2.92, p=0.027). **Recommended action:** δ should re-run using `scipy.stats.spearmanr` which handles both issues correctly.

3. **[MAJOR] No sensitivity analysis on small-n quarters** — δ's 8-quarter series includes four quarters with n < 10 (2024-Q2 n=0, 2024-Q3 n=5, 2024-Q4 n=3, 2026-Q2 n=4 per `_delta_scratch/decay_analysis.md` tables). These are the noisy tails that drive the ρ=0.786 correlation. I re-ran dropping n<10:
   - **5-quarter subset** (2025-Q1 n=25, Q2 n=16, Q3 n=3 dropped, Q4 n=41, 2026-Q1 n=33): ρ≈0.30, p≈0.62
   - **4-quarter subset** (2025-Q1, Q2, Q4, 2026-Q1): ρ=0.60, p=0.19 (using spearmanr)
   - 2025-Q3 has n=3 but is the lowest-WR (33.3%) and lowest-KER (0.031) quarter — it is a single high-leverage point.
   δ's "regime-conditional edge" finding depends entirely on whether 2025-Q3 (n=3) and 2024-Q3/Q4 (n=5, n=3) are retained. At n=3 the quarterly WR estimate has a 95% CI of roughly [0.8%, 90.6%] under Clopper-Pearson, so the 33.3% datapoint is effectively uninformative. **Recommended action:** δ should report Spearman under (a) all 8 quarters, (b) n≥10 quarters (n=5 surviving), (c) n≥20 quarters (n=4). The correlation is fragile to this choice and δ did not disclose that fragility.

4. **[MAJOR] "Fleet-stationarity" narrative masks XAUUSD-specific deterioration that ε/α find at p<0.03 BH-safe** — δ correctly shows that across all 5 instruments, pooled quarterly WRs do not exhibit a statistically significant time-series trend (bootstrap P=0.7525 for assignment permutation). But δ's analysis is POOLED at the instrument level (it treats all XAUUSD quarters as exchangeable) and **does not stratify by within-XAUUSD sub-signatures** that ε and α do find:
   - ε: XAUUSD winner-MFE compressed `1.04R → 0.49R` (Mann-Whitney U p=0.020, BH-safe rank 3 of 6)
   - ε: XAUUSD fast-loss rate `26.9% → 69.2%` (Fisher exact p=0.017, BH-safe rank 2 of 6)
   - ε: XAUUSD yearly WR `70.8% (2024) → 65.6% (2025) → 60.6% (2026)` (real year-over-year trend, not quarter-noise)
   - α: XAUUSD bad-entry rate (mfe < 0.2R) `26.3% → 50.0%` (post-2025-Q3; directional p=0.13)
   - α: 2026-Q1 losses where `mfe_r < 0.2R` = 8/13 (61.5%) with median MFE 0.106R
   These are finer-grained metrics than WR. All of them can be statistically real (BH-safe) while δ's aggregate WR is stationary (not BH-safe). **The correct synthesis is "pooled WR is stationary, but microstructure metrics show XAUUSD-specific degradation."** δ's deliverable presents only the pooled-aggregate view, which reads as "no decay, no problem," when the stratified view says "decay is present at the MFE/entry-placement layer even if not yet reflected in WR." **Recommended action:** chairman must not accept δ's "fleet stationary" as a blanket argument against regime-filter work. δ and ε/α are both directionally correct at their respective aggregation levels.

5. **[MAJOR] Bit-exact mismatch of canonical sequence IS VERIFIED — but δ under-states the evidence** — δ correctly writes: "The 131-trade XAUUSD dataset produces 8-quarter sequence 50→80→33→65.6→50→60→73.9→59.4, which does NOT match the canonical 73.2→71.4→63.6→59.4" (`delta_regime_decay.md:46-55`). δ's finding is CORRECT but the stronger evidence δ did not surface: **the canonical sequence is a HARDCODED list at `research/academic_pipeline/L4_foundation_analysis.py:649`** (`quarterly_wr = [73.2, 71.4, 63.6, 59.4]`), and the **same script computes actual per-quarter statistics** at lines 685-694 that yield `2025Q1=70.7%, Q2=71.4%, Q3=0.0%, Q4=63.6%, 2026Q1=59.4%` (see `research/academic_pipeline/results/L4_foundation_results_v1.md:327-336`). The hardcoded value `73.2%` does not match the script's own computation `70.7%`. So the canonical sequence is not just "does not reproduce from δ's sample" — it **does not reproduce from the script that is supposed to generate it**. Tested against 6 candidate datasets (unified_trades_v2 n=111, `_trade_index` n=129, entry_engineering_dataset n=129, unified_trades_v1 n=91, date-based subsets with drop-BE, subset with A+ only): **none** reproduce 73.2% in any quarter window. The tail 71.4%/63.6%/59.4% reproduces exactly in the `_trade_index` 129-trade set at 2025-Q2/Q4/2026-Q1 positions, confirming the last three numbers are real and from that dataset — but the lead number is not. **Recommended action:** treat the canonical sequence as a partially-fabricated figure that entered documentation via a hardcoded L4 variable. γ independently reached the same conclusion (`gamma_missed_trades.md:245`) via a different route (scope-era argument). Chairman should promote this from δ's "one of several notes" to a top-of-deliverable finding.

6. **[MAJOR] Canonical first-half/second-half split `67.2% vs 58.5% p=0.307` (CLAUDE.md / kb docs) is also unreproducible** — I attempted to replicate the 67.2% / 58.5% split claim that appears alongside the quarterly sequence. Tested splits:
   - Date-sorted all-symbol 50/50 split: first-half 65.6%, second-half 58.5% (2H matches, 1H differs by 1.6pp)
   - Drop-BE 50/50: 69.4% / 58.7% (closest, but 69.4 ≠ 67.2)
   - XAUUSD-only 50/50 by quarter count (4 quarters each): doesn't produce 67.2 under any straightforward subset
   - Trade-count median split (n=65 each side of trade #66): 67.7% / 58.5% (67.7 ≠ 67.2, off by 0.5pp)
   This suggests the canonical numbers are from a slightly different dataset cut than any of the six candidate datasets I tested, OR they share the `73.2%` fabrication issue. δ does not address the first-half/second-half claim directly but the fleet-stationarity bootstrap (P=0.7525) is consistent with "no material 1H/2H difference," indirectly supporting my finding. **Recommended action:** chairman should flag the 67.2/58.5 split alongside 73.2 as part of the canonical-sequence provenance problem.

7. **[MINOR] δ's 2026-Q1 monthly-uniformity claim reproduces but relies on tiny n in Feb/Mar** — δ writes (`delta_regime_decay.md:193`): "Jan 57.1% (n=21), Feb 66.7% (n=6), Mar 60.0% (n=5), chi-square p=0.92." I verified: chi-square(df=2)=0.176, p=0.921 — CORRECT. But the test has almost no power at n=6 and n=5. Clopper-Pearson 95% CIs: Jan [0.34, 0.78], Feb [0.22, 0.96], Mar [0.15, 0.95] — the CIs span most of the (0,1) interval for Feb and Mar. δ presents this as "monthly decay not supported" when the correct framing is "monthly trend cannot be detected at current power." **Recommended action:** chairman should soften to "exploratory; no within-Q1 drift detectable at n=21/6/5."

8. **[MINOR] 8-quarter chi-square of homogeneity is not reported in δ's tables but would be the cleanest test of the stationarity claim** — I ran it: chi-square(df=7) = 4.988, approximate p ≈ 0.66 (from chi-square survival at df=7). This SUPPORTS δ's stationarity claim at the WR-level. δ could add this one-line test to strengthen the fleet-stationarity case. **Recommended action:** mention in chairman synthesis as a cleaner test statistic than δ's bootstrap-on-order-permutation (they agree directionally, chi-square is more standard).

9. **[MINOR] "Cross-instrument decay doesn't track algo-rank (ρ=-0.21, n=5)" is correctly declared underpowered but δ uses the phrase "statistically untestable"** — n=5 cannot declare any correlation "untestable" — that's a descriptive not an inferential claim. δ's rank-correlation of instrument-level decay vs algo-rank order has permutation p distribution with 5! = 120 orderings; a single observed ρ=-0.21 would give permutation p ≈ 0.67 (descriptive). Fine as exploration but should not be in the Hypothesis-3 table. **Recommended action:** move to appendix or drop.

10. **[MINOR] δ does not cross-reference ε's instrument-level deterioration or α's bad-entry rate** — δ's deliverable reads as if δ had not seen ε/α outputs, but they are all Phase-1 parallel and available. The cross-agent synthesis is left to the chairman. This is not δ's fault (parallel agents don't see each other's work) but should be flagged so the chairman does not take δ's stationarity claim as contradicting ε/α. **Recommended action:** chairman synthesis must explicitly integrate δ + ε + α at the "aggregate vs microstructure" level.

## Spot-checks performed

**Reproduced bit-exact from `02_decay_analysis.py` re-run:**
- 8-quarter XAUUSD WR table: `[50.0, 80.0, 33.3, 65.6, 50.0, 60.0, 73.9, 59.4]` at n = [0, 5, 3, 25, 16, 41, 23, 33] — matches `decay_analysis.md` tables exactly.
- Pooled XAUUSD WR = 60.5% (n=131). Matches.
- Bootstrap P-value = 0.7525 at 10,000 iterations, seed=42: matches δ's claim (`delta_regime_decay.md:150`).
- First-half / second-half pooled WR (65.6% / 58.5%) and z=0.210, p=0.834 via two-proportion z: I got z=0.212, p=0.832 — matches within rounding.
- KER values `[?, 0.095, 0.031, 0.112, 0.070, 0.053, 0.087, 0.033]` with 2024-Q2 imputed — matches.
- ADR 2026-Q1 = 169.7 — matches δ.

**Reproduced with corrected arithmetic:**
- Spearman(WR, KER), tied-average ranks, t-dist p: **ρ=0.7665, t=2.923, p=0.0265** (vs δ's ρ=0.786, p=0.002).
- 8-quarter chi-square homogeneity: χ²(7) = 4.988, p ≈ 0.66.
- Dropping n<10 (5-quarter subset): ρ ≈ 0.30, p ≈ 0.62.
- Dropping n<20 (4-quarter subset): ρ = 0.60, p = 0.19.
- 2026-Q1 monthly chi-square: χ²(2) = 0.176, p = 0.921 — matches δ.

**Canonical-sequence provenance re-verification:**
- `L4_foundation_analysis.py:649`: **hardcoded** `quarterly_wr = [73.2, 71.4, 63.6, 59.4]`, not computed.
- `L4_foundation_results_v1.md:327-336`: same script's actual computed quarterly stats `2025Q1=70.7%, Q2=71.4%, Q3=0.0%, Q4=63.6%, 2026Q1=59.4%` — **contradicts the hardcoded lead value 73.2%**.
- Six candidate datasets tested (unified_trades_v2 n=111, _trade_index n=129, entry_engineering n=129, unified_trades_v1 n=91, session 34 merge n=131, various BE/sym subsets): **none** reproduce 73.2% in any quarter.
- The tail `71.4% / 63.6% / 59.4%` reproduces exactly in `_trade_index` at 2025-Q2 / Q4 / 2026-Q1 positions — confirming the last three are real.

## Cross-agent conflict / triangulation notes

- **δ vs γ (STRONG TRIANGULATION on canonical-sequence provenance):** γ (`gamma_missed_trades.md:245`) independently concluded: "The CLAUDE.md 73→59% figure describes an era without the current gates. The current L2 + BL pipeline on XAUUSD is performing correctly through all four 2026 months." γ reached this via a scope argument (2026 Jan-Apr L2 pipeline = 10 XAUUSD CAND, 70% WR, cannot reproduce decay). δ reached it via a bit-exact argument (131-trade XAUUSD sample does not produce 73.2 in any quarter). **Two independent methods, same conclusion — this is the strongest triangulated finding on the audit regarding the canonical sequence.** Chairman should promote.

- **δ vs ε (MATERIAL CONFLICT at different aggregation levels):** ε finds XAUUSD-specific instrument deterioration:
  - Winner MFE 1.04R → 0.49R, Mann-Whitney p=0.020, **BH-safe rank 3/6**
  - Fast-loss rate 26.9% → 69.2%, Fisher p=0.017, **BH-safe rank 2/6**
  - Yearly WR 70.8% → 65.6% → 60.6% (not stationary year-over-year)
  δ's bootstrap p=0.7525 on quarter-assignment permutation and chi-square p=0.66 on 8-quarter WR homogeneity both say aggregate WR is stationary. **Reconciliation: both are true.** WR is a coarse aggregate that can absorb MFE compression before it shows up as win/loss flips. Expectancy drifts slowly; the signature shows up in MFE/MAE before it shows up in WR. δ's "fleet stationary" must not be read as "nothing is degrading in XAUUSD" — ε's BH-safe findings are the stronger counter-signal at the microstructure layer. **Chairman action:** present δ and ε together as "aggregate stationary, microstructure deteriorating on XAUUSD."

- **δ vs α (COMPLEMENTARY NOT CONFLICTING):** α finds XAUUSD bad-entry rate (mfe<0.2R) at `26.3% → 50.0%` post-2025-Q3 (directional p=0.13) and 2026-Q1 losses with 8/13 below 0.2R MFE (61.5%). δ's stationarity at the WR level does not contradict α's "bad-entry" observation at the MFE layer — this is the same pattern ε finds, with different threshold (α uses 0.2R, ε uses 0.3R "fast-loss"). All three (δ stationary aggregate, α bad-entry rate doubling, ε fast-loss rate tripling) can be simultaneously true. Chairman synthesis: δ correctly characterizes the aggregate; α/ε correctly characterize the microstructure.

- **δ vs β (ORTHOGONAL):** β focuses on AI-integrity signatures (`sl_buffer_applied=0.0` universal, `entry_in_ob` L2-reject offset, etc.) — independent of quarterly WR decay. β's findings identify AI-side mechanisms for α's "bad entry" observation. δ has nothing to say about AI integrity directly. No conflict.

- **δ vs ζ (ORTHOGONAL, but ζ's detector bugs, if confirmed, would confound δ's regime metrics):** ζ reviews `market_state.py` detector logic. If ζ identifies real bugs in BOS / OB detection (e.g., all-history HH/HL in `identify_structure`, OB wick/body mitigation inconsistency), then **δ's quarterly WR computation is downstream of a pipeline with those bugs** — but this doesn't bias one quarter more than another, so it's unlikely to change δ's stationarity conclusion. The directional drift ε/α find would have to be explained as a deterministic pipeline bug interacting with a regime shift, which is more tangled.

- **δ vs η (ORTHOGONAL):** η focuses on alternative pattern signatures (hour/session interaction, alt-pattern frequency). δ treats these as regime proxies (KER, ADR, autocorr). If η finds patterns δ did not include as regime features, they would go into a forward regime-gate design but don't invalidate δ's stationarity claim directly.

- **δ vs θ (NOT YET AVAILABLE at time of review):** θ (prompt-layer review) is still running. Possible θ finding (if it identifies prompt-degradation signatures) would complement α's bad-entry observation but would not directly bear on δ's quarterly-WR stationarity.

## Reproducibility audit

**Script:** `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/02_decay_analysis.py` (~280 lines)

**Environment:** Python 3, project default, no external deps beyond math/random. Seed=42 for bootstrap. Runtime ~10 seconds. No errors on fresh run.

**Reproduced bit-exact:**
- 8-quarter WR sequence, pooled WR, first-half/second-half split.
- Bootstrap P=0.7525 at 10,000 iterations.
- Two-proportion z for first-half/second-half.
- Per-subtype OB/sweep/FVG decay tables in `decay_analysis.md`.
- KER, ADR, autocorrelation, Hurst values per quarter.
- 2026-Q1 monthly chi-square (0.176, p=0.921).

**NOT reproduced (due to identified bugs, not missing data):**
- Spearman ρ=0.786 (correct: ρ=0.766 with tied-average ranks).
- Spearman p=0.002 (correct: p=0.027 with t-dist df=6).
- "Survives Bonferroni at α=0.005" claim (correct: does NOT survive; p=0.027 > 0.005).

**Canonical-sequence spot-check attempts (none reproduce 73.2%):**
- `unified_trades_v2_20260331.json` (n=111): quarterly WRs don't match any of the four canonical values.
- `_trade_index.json` (n=129 after filter): produces 71.4/63.6/59.4 tail but not 73.2.
- `entry_engineering_dataset.csv` (n=129): same — tail matches, lead does not.
- L4 script hardcoded value `73.2` does not match its own computation `70.7`.
- No drop-BE / A+-only / date-window subset I tried reproduces 73.2 in any quarter.

**Rating justification: 4 / 5.** δ's reproducibility for aggregate claims is excellent (bootstrap, chi-square, pooled WRs, quarterly table, KER/ADR/autocorr all bit-exact). Deducted one point for:
(a) Spearman p-value bug — this is a real statistical error that inverts the Hypothesis-2 "Bonferroni-safe" claim;
(b) rank-tie handling bug — smaller magnitude but compounds with (a);
(c) missing sensitivity analysis on small-n quarters — without it the Spearman-based finding appears more robust than it is.

A replacement `02_decay_analysis.py` using `scipy.stats.spearmanr` and printing n-size-sensitivity rows (all 8, drop n<10, drop n<20) would be a clean 5/5.

## Implications for Tuesday (redacted_account 2026-04-21) go/no-go

**δ's policy recommendation** (`delta_regime_decay.md:248-288`): "No statistical basis to delay redacted_account kickoff. Bootstrap p=0.7525 shows 2026-Q1 WR is within noise band. Proceed at 1% risk per redacted_account profile."

**Reviewer assessment of that recommendation:**

1. At the **XAUUSD aggregate WR level** δ is right: the Q1 2026 WR of 59.4% is well within the bootstrap-derived noise band of the 5-quarter historical distribution. If the policy question is "should we delay Tuesday because XAUUSD WR has decayed?" the answer from δ is defensibly NO.

2. But δ's analysis is **not the only signal that matters for Tuesday**:
   - ε's XAUUSD MFE-compression (p=0.020 BH-safe) and fast-loss surge (p=0.017 BH-safe) are BH-safe and directionally concerning. A regime where MFE is compressing while WR holds means expectancy is at risk. **If this continues another 1-2 months, it will show up as WR drift.**
   - α's 2026-Q1 bad-entry rate (8/13 losses at MFE<0.2R, 61.5%) is exploratory but directionally aligned with ε.
   - δ's own Hypothesis 2 (regime-conditional edge) fails on correct arithmetic, so the "edge is alive in trending regimes" consolation claim is weaker than written.

3. **Net view:** Tuesday kickoff at 1% risk on redacted_account is defensible **IF** the CEO accepts that (a) XAUUSD aggregate WR is stationary per δ, (b) XAUUSD microstructure is deteriorating per ε/α, (c) ε-style shadow monitoring (fast-loss rate, winner MFE trajectory) is active through kickoff, and (d) a pre-specified stop criterion on ε's BH-safe metrics exists (e.g., "if fast-loss rate rolling-20 exceeds 65% for 2 weeks, halt").

4. **Regime filter development (δ's Hypothesis-2 narrative):** given the Spearman arithmetic bug, the case for a regime-conditional gate is weaker than δ wrote. Chairman should not fast-track regime-gate work ahead of other higher-leverage items. Shadow-logger a regime metric (KER or ADR) rolling across 2026-Q2 and revisit after n≥30 observations at 1% risk.

## Appendix — key file:line citations

- `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/02_decay_analysis.py:81-110` — erfc-instead-of-t bug in Spearman p-value.
- `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/02_decay_analysis.py:65-80` — sequential-rank (not tied-average) bug.
- `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md:46-55` — bit-exact mismatch claim (VERIFIED).
- `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md:150` — bootstrap P=0.7525 claim (VERIFIED).
- `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md:161,173` — Spearman ρ=0.786 p=0.002 claim (WRONG; correct: ρ=0.766, p=0.027).
- `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md:193` — 2026-Q1 monthly chi-square (VERIFIED at underpowered).
- `research/b_deep_audit_2026-04-19/phase1/delta_regime_decay.md:248-288` — Tuesday policy recommendation.
- `research/academic_pipeline/L4_foundation_analysis.py:649` — HARDCODED `quarterly_wr = [73.2, 71.4, 63.6, 59.4]`.
- `research/academic_pipeline/L4_foundation_analysis.py:685-694` — same script's actual per-quarter computation.
- `research/academic_pipeline/results/L4_foundation_results_v1.md:290-297` — canonical sequence output.
- `research/academic_pipeline/results/L4_foundation_results_v1.md:327-336` — contradicting computed values.
- `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md:222,328` — canonical sequence in kb.
- `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md:131` — canonical sequence in kb.
- `CLAUDE.md:217` — canonical sequence in project instructions.
- `research/b_deep_audit_2026-04-19/phase1/gamma_missed_trades.md:245` — γ's independent confirmation of 73→59 era argument.
- `research/b_deep_audit_2026-04-19/phase1/epsilon_liquidity_arb.md` — XAUUSD MFE compression (p=0.020) and fast-loss (p=0.017) BH-safe findings.
- `research/b_deep_audit_2026-04-19/phase1/alpha_entry_execution.md` — XAUUSD bad-entry 26.3% → 50.0% claim.
