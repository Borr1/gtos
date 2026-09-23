# BELIEF-RECAL — honest-belief subpopulation screen (Session FA, Phase B item 3)

**Analyst:** BELIEF-RECAL (Fable 5) · **Date:** 2026-08-04 · **Branch:** phase19/broad-forensic

> **EVIDENCE CLASS — read first.** Everything in this receipt is **DEVELOPMENT-FITTED lane
> evidence, billed:false, NEVER admission-grade.** The BH marks below are a **triage screen
> only**. Admission under the ratified rule requires a declared candidate family gated at the
> sealed `B_balanced` α = 0.10 on `CANDIDATE_BOOK_V1` populations — out of scope for a lane
> screen by construction. No March-2026 data and no live-forward (2026-07-29+) data was read.
> **February is used-once VAL: every February number here is attribution-only, labeled as
> such, and selects nothing.** Selection is done on January ONLY; February is read only
> through the January-frozen selection.

**Question (owner's axis 6, Phase B form):** under HONEST beliefs — base-rate probabilities
fitted from realized outcomes instead of the engine's fictions, EV priced at the contract
actually walked (the 2.0R-capped-giveback diagnostic proxy, not the stamped 1.5R payoff),
net of MEASURED cost — does ANY subpopulation of the January pool clear its own breakeven,
and does the answer transfer to February?

**Inputs (read-only, committed):**

- January: `phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` — 27,658 scoreable rows.
- February: `phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` — 24,239 scoreable rows
  (schema/provenance per `phase18/receipts/CP_FEBRUARY_POOL_S0R0_V1.json`).
- Prior work inherited, not repeated: `research/operations/wave19_broad_forensic_2026_08_01/`
  `calibration/` (CALIBRATION.md: Brier skill −1.147/−0.965; stamped p̄ 0.766; EV floor +0.398;
  confidence ≡ 0.55; `execution_fill_probability` 0.92 flat; `expected_cost_r == cost_r`
  tautology) and `funnel_jan/FUNNEL_JAN.md`.
- Script: `belief_recal.py` (this directory); machine mirror: `BELIEF_RECAL.json`.

---

## 1. DECLARATION — written before any outcome aggregation

This section was written and saved to disk after a schema-only pass (field names, axis value
censuses, null counts, placeholder-symbol row counts — no outcome field aggregated) and
**before** any per-cell outcome statistic was computed. The script enforces the same order:
it emits the declaration block from axis fields alone, then computes.

### 1.1 Cell partition (fixed, no fitting, identical in both windows)

Three axes, declared from the schema census:

- **`origin_family`** — 10 values (both windows carry exactly these): `current_fvg_fill`,
  `liquidity_sweep_reclaim`, `displacement_continuation`, `current_breaker_re_entry`,
  `cross_asset_lead_lag`, `structural_distance_extreme`, `current_ob_retest`,
  `session_open_range_break`, `volatility_compression_expansion`, `regime_transition_break`.
- **Cost band** on `cost_r` (the pool's own total broker-true cost field, the one its
  `loss_concentration` receipt bands on), at fixed absolute thresholds — no quartile fitting,
  so the bands transfer to February byte-identically:
  - `C1` cost_r < 0.10 (the executed-trade stratum: max executed cost in January was 0.1765)
  - `C2` 0.10 ≤ cost_r < 0.30
  - `C3` 0.30 ≤ cost_r < 1.00
  - `C4` cost_r ≥ 1.00 (the pool's own documented "stop narrower than round-trip cost" band)
- **`route_session`** — 4 values (both windows): `ny`, `london`, `tokyo`,
  `off_configured_session`.

**Declared partition: 10 × 4 × 4 = 160 cells** (within the 100–200 cap). Populated-cell
counts are reported in §2; empty cells are reported as empty, not dropped from the
declaration. There is exactly ONE partition in this screen; no secondary partition, no
post-hoc re-slicing. Symbol is deliberately NOT an axis; the placeholder-spread discipline
(§1.5) handles the symbol-level cost defect instead.

### 1.2 Metrics (two, declared before numbers)

- **M1 — empirical:** per cell, on January: n, mean/median of `opportunity_net_proxy_r`
  (the walked 2.0R-capped-giveback diagnostic net proxy: gross − broker-true cost), SD,
  one-sided t statistic (H1: mean > 0), p-value from Student t with n−1 df.
- **M2 — calibrated-belief:** win event := gross_r > 0, where
  gross_r := `opportunity_net_proxy_r` + `cost_r` (January carries no explicit gross field;
  February's explicit `opportunity_gross_r` is used ONLY to verify the derivation, expected
  match ≤ 1e-8 per Phase 1). Per cell: p̂ = realized win rate; W̄ = mean gross over wins;
  |L̄| = |mean gross over losses|; c̄ = mean `cost_r`;
  **p\* = (|L̄| + c̄) / (W̄ + |L̄|)**; **margin = p̂ − p\***.
  **Honesty note, declared up front:** margin > 0 ⟺ M1 mean net > 0 by algebraic identity
  (mean net = p̂·W̄ − (1−p̂)·|L̄| − c̄), so M2 is a re-expression of M1 on the probability
  scale, NOT an independent test. Its value is the decomposition an R-BELIEF author needs:
  the required precision p\* per cell vs the honest base rate p̂ vs the engine's stamped
  mean `candidate_probability` (reported per cell, descriptive only).

### 1.3 Multiplicity (triage marker only)

Benjamini–Hochberg at **α = 0.10** across all January cells with **n ≥ 30**, on the M1
one-sided p-values. **This admits nothing.** It is a screen marker; the ratified admission
rule (declared family, sealed α, `CANDIDATE_BOOK_V1` basis) is out of scope here.

### 1.4 Selection + transfer rule (frozen before any February read)

- **Jan-selected cell** := n_jan ≥ 30 AND mean net (Jan) > 0 AND BH-marked at α = 0.10.
  Cells with n_jan < 30 are reported in the JSON but excluded from BH and from selection
  (tiny-n mirage guard).
- **February transfer (attribution-only, labeled):** for each Jan-selected cell, the SAME
  cell's February n and mean net. Reported:
  (a) **sign-agreement rate** — share of Jan-selected cells with Feb mean net > 0, primary
  over cells with Feb n ≥ 30, secondary over all Jan-selected cells;
  (b) **Spearman** of Jan-cell-mean vs Feb-cell-mean over ALL cells with n ≥ 30 in both
  windows (not just selected — rank-transfer context);
  (c) **the headline aggregate** — February net of the Jan-selected sub-book: equal-weight
  mean of Feb cell means, n-weighted pooled mean over all Feb rows landing in Jan-selected
  cells, and the pooled total R sum. A sensitivity variant of (c) excluding asterisked cells
  (§1.5) is also declared and reported.

### 1.5 Placeholder-spread (asterisk) discipline

Phase 1 measured that three symbols carry placeholder spreads, not measurements: **BTCUSD
(`spread_r` = 0.0001 on every row of both windows), UKOIL_cash (constant 0.02580), USOIL_cash
(constant 0.02700)** — i.e. their `cost_r` may be materially understated, which fakes
positivity. Jan placeholder rows: 2,726 (9.86%); Feb: 2,835 (11.70%). Declared rule:

- every cell reports its placeholder-row share (both windows);
- a Jan-selected cell gets an **ASTERISK** if its positivity depends on placeholder-priced
  rows: excluding rows with symbol ∈ {BTCUSD, UKOIL_cash, USOIL_cash}, the cell's January
  mean net drops to ≤ 0, or the remainder has n < 30;
- asterisked cells are never silently presented as clean; the headline is reported with and
  without them.

### 1.6 Cross-check anchors (must reproduce Phase 1 exactly)

Jan: n 27,658, net mean −0.880657, gross mean −0.217496, cost mean 0.663161, positive share
0.27862. Feb: n 24,239, net mean −0.640021, gross mean −0.150551, positive share 0.309336.
Any mismatch voids the run.

*(End of declaration. Everything below was computed after this section was written.)*

---

## 2. HEADLINE

**NO. Under honest beliefs, no subpopulation of the January pool clears its own breakeven
at the declared partition, and nothing exists to transfer.** Of 160 declared cells, 138 are
populated in January and 108 carry n ≥ 30 (covering 27,316 / 27,658 rows = 98.8 %). Exactly
**4 of 108 cells (3.7 %) have positive January mean net**, and **BH at α = 0.10 marks ZERO
of them** — the best p-value in the entire grid is 0.0084 against a rank-1 bar of 0.000926.
The Jan-selected set is **empty**, so the declared headline is exact: *the January-honest
sub-book, walked into February, earns 0 R because it contains no cells.*

And the relaxed reading is worse, not better: dropping the BH requirement entirely (labeled
sensitivity, §5.2 — NOT the declared headline) and walking all four nominal January-positive
cells into February yields **−19.13 R over 129 February rows (n-weighted −0.148 R/row;
equal-weight −0.208 R/row)**, sign agreement **1 of 4** (1 of 3 at Feb n ≥ 30) — and the one
sign-agreeing cell is asterisked (its January positivity depends on placeholder-priced
rows, §6). There is no selectable positive sub-book at true costs in this pool, with or
without multiplicity discipline.

Cross-checks: all Phase-1 anchors reproduced exactly (§1.6); February gross derivation vs
the pool's explicit `opportunity_gross_r` max |diff| 5.0e-9.

## 3. Empirical view (January, M1)

- Cost-band marginals (descriptive rollup of the declared cells) show the gradient that
  dominates everything: mean net **C1 −0.178, C2 −0.360, C3 −0.781, C4 −2.689** R/row
  (n = 4,493 / 9,252 / 9,005 / 4,908). Even the cheapest-to-trade quarter of the pool is
  negative on average.
- 4/108 eligible cells positive; the 30 small-n cells (342 rows total, reported in the JSON
  but excluded from selection by declaration) contain 5 positive means worth ~+7 R combined
  — no hidden mass.
- Per-cell one-sided t: only one cell in the grid reaches even nominal p < 0.01
  (`cross_asset_lead_lag|C1|london`, p 0.0084); the next-best positive cell sits at p 0.40.

## 4. Calibrated-belief view (M2) — the margin distribution

Margin = p̂ − p\* (realized win rate minus the win rate required at the cell's own measured
win/loss magnitudes and mean cost, at the walked 2.0R-capped-giveback contract). Over the
108 eligible cells: **min −2.156** (`current_breaker_re_entry|C4|tokyo`: p\* = 2.16 with
p̂ = 0.0 — a cell whose required precision exceeds 1, i.e. no win rate can pay its cost),
**p10 −0.892, p25 −0.458, median −0.226, p75 −0.130, p90 −0.072,
max +0.176**; **3.7 % of cells have positive margin** (identical to M1 by the declared
identity). The honest-belief restatement of the pool: at true costs and walked-contract
payoffs, the typical cell needs ~23 points more win rate than reality delivers; the engine
meanwhile stamped p̄ 0.75–0.85 on every one of these cells.

**Top 15 cells by January margin** (of 108; AST-dep = January positivity depends on
placeholder-spread rows — meaningful only where mean > 0, else "—"; February columns are
attribution-only):

| # | cell (family \| band \| session) | n Jan | mean net | margin | p̂ | p\* | c̄ | stamped p̄ | placeholder share | AST | n Feb | Feb mean net |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | cross_asset_lead_lag\|C1\|london | 53 | **+0.472** | **+0.177** | 0.566 | 0.390 | 0.056 | 0.837 | **0.64** | **YES** | 7 | −0.538 |
| 2 | current_ob_retest\|C2\|tokyo | 48 | +0.035 | +0.024 | 0.542 | 0.518 | 0.181 | 0.847 | 0.00 | no | 48 | −0.401 |
| 3 | regime_transition_break\|C1\|off_configured_session | 80 | +0.001 | +0.001 | 0.512 | 0.511 | 0.061 | 0.818 | 0.30 | no | 37 | −0.088 |
| 4 | liquidity_sweep_reclaim\|C1\|london | 123 | +0.002 | +0.001 | 0.439 | 0.438 | 0.062 | 0.800 | 0.47 | **YES** | 37 | +0.193 |
| 5 | cross_asset_lead_lag\|C2\|london | 168 | −0.062 | −0.026 | 0.470 | 0.496 | 0.200 | 0.789 | 0.18 | — | 156 | −0.120 |
| 6 | current_fvg_fill\|C2\|london | 257 | −0.059 | −0.035 | 0.584 | 0.619 | 0.161 | 0.844 | 0.00 | — | 450 | −0.165 |
| 7 | liquidity_sweep_reclaim\|C1\|ny | 180 | −0.066 | −0.035 | 0.506 | 0.541 | 0.067 | 0.792 | 0.22 | — | 115 | −0.011 |
| 8 | liquidity_sweep_reclaim\|C1\|off_configured_session | 280 | −0.103 | −0.058 | 0.461 | 0.519 | 0.065 | 0.807 | 0.26 | — | 125 | −0.026 |
| 9 | session_open_range_break\|C1\|tokyo | 31 | −0.091 | −0.064 | 0.419 | 0.483 | 0.074 | 0.815 | 0.00 | — | 23 | +0.154 |
| 10 | cross_asset_lead_lag\|C2\|tokyo | 31 | −0.129 | −0.069 | 0.581 | 0.650 | 0.218 | 0.796 | 0.00 | — | 20 | −0.120 |
| 11 | cross_asset_lead_lag\|C2\|ny | 165 | −0.169 | −0.071 | 0.424 | 0.496 | 0.194 | 0.803 | 0.12 | — | 183 | −0.315 |
| 12 | liquidity_sweep_reclaim\|C2\|london | 414 | −0.153 | −0.072 | 0.457 | 0.528 | 0.197 | 0.784 | 0.08 | — | 435 | −0.218 |
| 13 | structural_distance_extreme\|C2\|london | 64 | −0.167 | −0.073 | 0.453 | 0.526 | 0.212 | 0.752 | 0.33 | — | 69 | −0.063 |
| 14 | current_ob_retest\|C2\|ny | 120 | −0.176 | −0.087 | 0.442 | 0.528 | 0.178 | 0.829 | 0.05 | — | 191 | −0.201 |
| 15 | current_ob_retest\|C2\|off_configured_session | 337 | −0.130 | −0.089 | 0.493 | 0.581 | 0.180 | 0.845 | 0.10 | — | 379 | −0.270 |

The four positive cells, honestly read:

- **#1 `cross_asset_lead_lag|C1|london`** is the only cell with a real margin (+0.472 R/row,
  sum +25.0 R, t 2.47, p 0.0084 — still 9× short of the BH rank-1 bar). **64.2 % of its rows
  are placeholder-spread symbols**; ex-placeholder it keeps a positive mean (+0.350) but on
  n = 19 < 30 → ASTERISK by the declared rule. Its February same-cell read: **n = 7, mean
  −0.538** — the cell almost vanishes out-of-window and flips sign. Even taken at face value
  its full capture was worth ~25 R/month.
- **#2 `current_ob_retest|C2|tokyo`** is placeholder-clean but statistically nothing
  (p 0.40), and February flips it hard: n 48 → mean **−0.401** on equal n.
- **#3 `regime_transition_break|C1|off`** and **#4 `liquidity_sweep_reclaim|C1|london`** are
  +0.001/+0.002 R/row — breakeven noise (p 0.49 both). #4 is the only one of the four whose
  February mean is positive (+0.193, n 37), and it is exactly the cell whose January
  positivity is placeholder-dependent: ex-placeholder its January mean is **−0.058**.

## 5. February transfer (attribution-only — February is used-once VAL)

### 5.1 Declared transfer

Jan-selected set = ∅ → sign-agreement undefined, headline aggregate **0 cells / 0 rows /
0 R**. That IS the declared answer.

### 5.2 Labeled sensitivity (NOT the declared headline): the four nominal positives

Relaxing ONLY the BH requirement (keeping n ≥ 30 and mean > 0):

| aggregate | n cells | n Feb rows | equal-weight mean | n-weight mean | total |
|---|---:|---:|---:|---:|---:|
| all four nominal positives | 4 | 129 | −0.208 | −0.148 | **−19.13 R** |
| ex placeholder-dependent (#2, #3 only) | 2 | 85 | −0.245 | −0.265 | −22.52 R |

Sign agreement: 1/4 overall, 1/3 among Feb n ≥ 30 — and the agreeing cell (#4) is
asterisked. **Even without any multiplicity discipline, the January-positive set transfers
negative.**

### 5.3 What DOES transfer: the ordering of losses, not any positivity

Spearman of Jan-cell-mean vs Feb-cell-mean over all 91 cells with n ≥ 30 in both windows:
**ρ = +0.823 (p 1.5e-23)**. The cell-level structure is highly stable across months — but
what transfers is *how negative a cell is*, dominated by the cost-band gradient (band means
Jan −0.178/−0.360/−0.781/−2.689 vs Feb −0.081/−0.311/−0.753/−2.076). Within a cost band the
rank transfer decays toward noise at the cheap end: C1 ρ 0.224 (p 0.37), C2 0.463, C3 0.556,
C4 0.791. This is Phase 1's decomposition finding reproduced at cell level: **the
predictable component of this pool is its cost, not its edge** — exactly where a selectable
sub-book would have to live (C1), cross-month rank correlation is statistically
indistinguishable from zero.

## 6. Asterisk discipline (placeholder-spread honesty)

Three symbols carry placeholder spreads, not measurements (Phase 1): **BTCUSD** (`spread_r`
0.0001 every row; its cost is carried by broker-true commission instead, so it is
under-stated rather than absent), **UKOIL_cash** (constant 0.02580), **USOIL_cash**
(constant 0.02700). Jan 2,726 rows (9.86 %), Feb 2,835 (11.70 %). Consequence here: of the
4 nominal positive cells, **2 are placeholder-dependent** (#1 by ex-n < 30 at 64 %
placeholder composition; #4 by ex-placeholder mean −0.058 < 0). **No positive cell in this
screen is simultaneously (a) placeholder-clean, (b) statistically distinguishable from
zero, and (c) sign-stable into February.** Every cell's placeholder share is in the JSON;
no placeholder-priced cell is presented as clean anywhere in this receipt. If R-COST-TRUTH
later replaces these three spreads with measured values, the two asterisked cells can only
get WORSE (costs are under-stated, never over-stated, by these placeholders).

## 7. Verdict against the question

At honest base-rate beliefs, walked-contract payoffs, and measured costs, the January pool
contains **no subpopulation at this partition that clears its own breakeven** with any
statistical support, and the nominal positives fail out-of-window in February
(attribution-only read). This closes the L3b "BELIEF-RECAL" question in the negative and
**independently corroborates axis 6** of `SESSION_FA_BROAD_FORENSIC_RESULT.md`: the belief
fields cannot carry the separation, and re-fitting beliefs honestly does not conjure a
sub-book — the separable edge, where it exists, lives in mechanism identity × geometry
(the R-GEOMETRY / declared-candidate route), not in re-weighting this pool. All of this is
DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade.

## 8. REPAIR IMPLICATION — to the R-BELIEF author, concretely

The screen supplies the honest formulas and also bounds what they can buy:

1. **Probability.** Replace `candidate_probability` with a fitted base rate:
   p̂(cell) = realized win share at the finest granularity that holds n ≥ 30 (this grid's
   family × cost-band × session is a workable default), shrunk toward the pool base rate
   (e.g. Jeffreys/beta shrinkage) for thin cells. Remove the `0.04×sha256(family)` term and
   the structural 0.58 floor — honest p̂ in this pool spans 0.42–0.58 in the BEST cells and
   the engine must be able to say 0.2. Anchor numbers: stamped p̄ 0.766 vs realized 0.347
   gross / 0.279 net (Jan).
2. **EV.** Price EV at the WALKED contract from measured magnitudes:
   EV(cell) = p̂·W̄win − (1−p̂)·|L̄loss| − c̄, with W̄/|L̄| the realized gross win/loss means
   per cell (across this pool's eligible cells: W̄ 0.27–2.29 R, |L̄| 0.30–1.00 R — the
   stamped symmetric ~1.5R win payoff describes almost no cell) and c̄ the measured cost. EV must be allowed to go negative; under these
   formulas essentially every cell of this family prices negative, which is the correct
   output. Publish p\* = (|L̄|+c̄)/(W̄+|L̄|) alongside it — the required-precision form the
   scheduler can compare against p̂ directly.
3. **Confidence.** Delete the ≡0.55 `candidate_confidence` constant from the scheduler
   score (a constant × 0.20 weight is a no-op wearing a weight); if a confidence slot must
   exist, use an n-based shrinkage weight (how much the cell's p̂ is data vs prior).
4. **Fill probabilities.** Replace the 0.92 template `execution_fill_probability` with
   measured fill rates or drop the term from the score until measured.
5. **Cost.** Keep `expected_cost_r` = measured cost as an input (the tautology was never
   the defect — the defect was calling it "calibration"), but the three placeholder spreads
   (BTCUSD, UKOIL_cash, USOIL_cash) must be repaired by R-COST-TRUTH before any belief
   output touching those symbols is trusted — they are the difference between "asterisk"
   and "clean" for 2 of the 4 nominal positives here.
6. **Expectation management, on the record:** honest beliefs make the system STAND DOWN on
   this family — they do not make it profitable. The value of R-BELIEF is truthful refusal
   (and truthful pricing of any future family), not recovered edge from this pool. Any
   claim that a belief repair alone produced a positive broad-V4 book should be treated as
   a red flag against this receipt.

---

*Receipt generated by `belief_recal.py` (this directory); machine mirror
`BELIEF_RECAL.json` (declaration, all 160 cells, BH block, transfer block, descriptive
rollups). Evidence class: DEVELOPMENT-FITTED lane evidence, billed:false, never
admission-grade; February attribution-only (used-once VAL); no March, no live-forward.*
