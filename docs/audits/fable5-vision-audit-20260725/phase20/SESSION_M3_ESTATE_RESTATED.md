# m3 — WHAT THE REPAIR DOES TO THE MONEY. The live sleeve estate, restated.

**Lane:** m3 (wave 20). **Population:** the live sleeve estate — AA's own archive walk
(`AA_ESTATE_TRADES.json.gz`, 32 sleeves, 22,324 trades, 2000–2026) plus AM's re-clocked
`sub_mid_dn_revert` (533), re-derived from `vps-bars-20260727` and re-walked on lane r1's
quote-side-corrected convention. Nothing sampled. **Research walks only — no live-forward P&L
was read, no live behaviour was changed, no `src/` byte was edited.**

Receipts: `receipts/m3/` — `m3_substrate.py` → `M3_SUBSTRATE_V1.json.gz`,
`m3_regate.py` → `M3_REGATE_V1.json` (840 gated arms), `m3_armed_econ.py` →
`M3_ARMED_ECON_V1.json`, `m3_exit_contract.py` → `M3_EXIT_CONTRACT_V1.json`,
`m3_compose_null.py` → `M3_COMPOSED_NULL_V1.json`, `m3_analyse.py` → `M3_RESULT_V1.json`.

---

## 0. HEADLINE

**The quote-side repair does not kill the estate's standing admission — it kills the sleeve
nobody was looking at.** `mx_btcusd @ target_5R` is unmoved: at the ratified rule its pooled
OOS mean goes `+0.98169 → +0.98017 R/day` (−0.16 %) and its `p_raw` does not move at all
(0.0011 → 0.0011), and it still admits at exactly two of three cost bands. **`sub_mid_dn_revert`,
which is ARMED on both accounts and which no wave-20 artifact listed as armed, loses 59.6 % of
its published gross** (+0.47842 → +0.19325 R/trade) and its pooled OOS expectancy collapses from
`+0.1206 R/day` to `+0.0028` — statistically indistinguishable from zero — or to **−0.1958** if
you keep charging the spread.

Four things follow, each with its number:

| | |
|---|---|
| **Q1** the standing admission | **SURVIVES the walker.** It was already killed by a DIFFERENT repair — A1b's corrected null — and this lane composes the two and proves the walker adds nothing to that flip: A1b's corrected p goes 0.002810 → **0.002843** (+1.2 %) when the walk is corrected. The ADMIT→REJECT is A1b's, entirely. |
| **Q2** the exit contract | **SURVIVES, and the inference that killed it was wrong.** The correction moves the LEVEL by −0.1024 R/emission and the PAIRED DELTA by −0.0040 — a ratio of **25.7×**. `stop_only_horizon` beats `target_2.0R` by **+0.0392 R/emission** fill-anchored (published: +0.0432), day-block CI95 [+0.0115, +0.0698], p 0.00235, over 1,127,805 emissions. |
| **Q3** armed economics | **Two of five sleeves move materially and both are armed.** `crypto` −23.5 % of gross; `sub_mid_dn_revert` −59.6 %. `energy_agri`, `sub_xvol_pullback` and `mx_btcusd` move by ≤ 0.1 %. Book `p_pass` on the ARCHIVE population: FTMO two-phase **0.5468 → 0.5157** honest, **0.3370** conservative. |
| **Q4** corrections | **9 of 29 sleeves change the SIGN of their published gross.** Pooled estate gross +0.112763 → −0.027726; pooled NET moves the OTHER way, −0.174858 → −0.123124, because the cost model's spread term was standing in for a geometry the walk now carries. |

---

## 1. THE ARMED SET — established from disk, because all three wave-20 lanes had it wrong

`scripts/run_book_supervisor.ps1:86` (FTMO) and `:87` (redacted_account), parsed by
`m3_armed_econ.armed_from_launcher()`:

```
FTMO        crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert, mx_btcusd_d1_donchian_20_breakout
redacted_account  crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert
```

`mx_btcusd` was **disarmed on FTMO 2026-08-05 by owner instruction** — D-2 CLOSED, host commit
`2fa77722d`, `phase19/SESSION_FA_CONTINUATION_RESULT.md:107-119`; the committed launcher was
never updated. So **the armed set today is the same four on both accounts**:
`crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert`.

Lanes r1 and r2 both declare a four-sleeve armed set that **omits `sub_mid_dn_revert` and
includes `mx_btcusd`** (`r1_estate_rewalk.py:75-81`, `R2_RESULT_V1.json → live_isolation`,
`tests/test_broad_origin_emission_repairs.py`). Lane v1 caught it. This lane measures both
readings and every conclusion below names the SET, never the count.

**Why the omission cost something.** `sub_mid_dn_revert` is the single largest proportional
casualty of the repair in the whole armed set, and it had no fold table, no p-value and no
gated verdict at the corrected numbers anywhere in the wave. §3 and §4 are that receipt.

---

## 2. Q1 — DOES THE STANDING ADMISSION SURVIVE?

### 2.1 The rule, and the control that makes this a re-gate and not a new experiment

Ratified rule, spelled out and not chosen here: **population `RECORDED`** with AN's conditions
(`phase10/receipts/POPULATION_RULE_V1.json → ratified_rule`, Borhen 2026-07-30); **option
`B_balanced`, α = 0.10, BH** (`options.py:88-104`); **declared family `CANDIDATE_BOOK_V1` on the
`all_declared` basis at the wave-18 tip V27 — 59 declared / 57 looks**
(`phase18/receipts/CANDIDATE_FAMILY_V27.json`).

**Control C2.** The published arm, run through this lane's own substrate at AN's own family
(V2, 35), reproduces `POPULATION_RULE_V1.json → grid.arms` on **12 of 12** checked cells:
identical `p_raw`, identical `n_trades`, identical verdicts, including the admission itself
(`p_raw = 0.0010998900109989002`, n 232, ADMIT). **Control C0/C1** on the substrate: the `old`
arm reproduces AA's published `r_gross` on **22,324/22,324** rows and AM's on **533/533**, max
abs error **0.0**, and `resimulate_qs(band=None)` reproduces `ad_exit_sweep.resimulate`
field-for-field on all three candidate cells (`M3_SUBSTRATE_CONTROLS_V1.json`).

### 2.2 `mx_btcusd_d1_donchian_20_breakout @ target_5R`, RECORDED / B_balanced / V27

| walk | cost band | spread charged | verdict | pooled OOS R/day | p_raw | q |
|---|---|---|---|---:|---:|---:|
| published | flat snapshot | yes | ADMIT | +0.98907 | 0.001000 | 0.0590 |
| published | low | yes | ADMIT | +0.98334 | 0.001100 | 0.0649 |
| published | mid | yes | ADMIT | +0.98169 | 0.001100 | 0.0649 |
| published | high | yes | REJECT | +0.87808 | 0.005099 | 0.2360 |
| **corrected** | **low** | yes | **ADMIT** | **+0.98322** | **0.001100** | **0.0649** |
| **corrected** | **mid** | yes | **ADMIT** | **+0.98017** | **0.001100** | **0.0649** |
| **corrected** | **high** | yes | **REJECT** | **+0.76473** | **0.016298** | **0.4808** |

**"Admits at two of three cost bands" is still exactly true after the correction**, with the same
two bands and the same rejecting band. `oos_positive_fold_frac` stays 1.0 (5/5) and
`drop_best_retention` moves 0.7747 → 0.7740. On the underlying trades the correction changes
**one** exit reason in 232 and moves the gross by −0.019 R/trade at mid; at the `as_walked`
contract it moves it by **exactly zero**.

The reason is mechanical and worth stating because it does not generalise: BTCUSD's
spread-over-risk is the smallest in the estate (`spread_r` mean **0.0124 R** against the estate's
0.1917), so a one-spread displacement almost never crosses a level. At the `high` band it does —
and there the rejection deepens from p 0.0051 to p 0.0163.

### 2.3 The composition with A1b — the number that actually decides this cell

Two independent repairs land on this one cell and they are not comparable until composed,
because A1b's correction is computed ON a daily series and m3's correction CHANGES that series.

`m3_compose_null.py` captures the daily series and fold segmentation behind both walks with
**A1b's own hooks** and runs **A1b's own `corrected_p_for_arm`** on each, 200,000 sims × 3 seeds
per variant.

**Control:** the `old` walk's captured series is **float-identical** to A1b's
(`A1B_AU_CAPTURED_SERIES.json`, arm `target_5R` @ `mid`) — n 184, seg_lens `[36, 42, 26, 30, 50]`,
max abs error **0.0** — and its corrected p reproduces A1b's published **0.00281** to six
decimals, with ρ̂ = 0.3835 ± 0.0690 against A1b's published 0.384 ± 0.069.

| | corrected p (primary) | q @ 48 | q @ 57 | q @ 59 | verdict |
|---|---:|---:|---:|---:|---|
| published walk | 0.002810 | 0.13488 | 0.16017 | 0.16579 | REJECT |
| **quote-side-corrected walk** | **0.002843** | 0.13648 | 0.16207 | 0.16776 | REJECT |

**The walker moves A1b's corrected p by +0.000033 — 1.2 % — and moves no verdict.** The
ADMIT→REJECT flip on the estate's one standing admission is A1b's finding in full; wave 20's
walker repair neither causes it nor rescues it. (The sleeve is in any case disarmed since
2026-08-05.)

### 2.4 What the correction does across the whole 840-arm grid

31 arms ADMIT out of 840; **all 31 are on `RECORDED`**, which independently re-confirms AN's
population finding. By walk: **published 27, corrected-low 2, corrected-mid 2, corrected-high 0.**
The corrected walker removes 25 of 27 admissions. Almost all of the removed ones are
`sub_mid_dn_revert` and `sub_xvol_pullback` arms that only ever admitted under the
spread-removed cost convention — see §3.

---

## 3. Q1b — THE TWO CO-JUDGED CELLS, AND THE ONE THAT IS ARMED

RECORDED / mid / B_balanced / V27, `config X_btc5R`:

### `sub_mid_dn_revert @ reclocked` — **ARMED ON BOTH ACCOUNTS**

| walk | spread | verdict | pooled OOS R/day | p_raw | fold means | failing gates |
|---|---|---|---:|---:|---|---|
| published | charged | REJECT | **+0.12065** | 0.16348 | −0.337, +0.249, −0.444, +0.402, +0.734 | robustness, significance |
| published | removed | ADMIT | +0.31925 | 0.00350 | −0.010, +0.473, −0.139, +0.494, +0.778 | — |
| **corrected** | charged | REJECT | **−0.19583** | 0.90691 | −0.791, −0.465, −0.691, +0.262, +0.705 | **expectancy, lifetime, stability, robustness, significance** |
| **corrected** | removed | REJECT | **+0.00277** | 0.49555 | −0.465, −0.241, −0.386, +0.355, +0.750 | stability, robustness, significance |

Read the fold means, not the pooled number. Under the published walk this sleeve was positive in
3 of 5 OOS folds; under the corrected walk it is positive in **2 of 5**, and **the three negative
folds are the three OLDEST**. All of its remaining expectancy sits in the two most recent folds.
At the honest cost convention its pooled OOS mean is `+0.0028 R/day` on 325 trades — a number
that is zero to within any resolution this estate has.

It was already a REJECT, so no admission moves. What moves is the *magnitude* a sizing decision
would rest on, and it moves by **97.7 %** (+0.1206 → +0.0028).

### `sub_xvol_pullback @ target_4R` — **ARMED sleeve, contract NOT live**

Unchanged where it matters: pooled +1.36505 → +1.36727 (charged), p 0.00800 → 0.00800, REJECT on
`significance` in both. The only movement is on the spread-removed arm, where q crosses the bar
(0.08849 → 0.13864, ADMIT → REJECT) purely through BH re-ranking against the co-judged set.
`--frontier-exits` is not set for this sleeve on either account, and AS handoff 3 already says
*"do not propose it."* Nothing here changes that.

---

## 4. Q3 — DO THE ARMED SLEEVES' ECONOMICS MOVE ENOUGH TO MATTER?

Population ARCHIVE, `walkforward.panel.price_trades` (the gate's own pricer, so blackout drops
and the day-collapse are the verdict's own), FTMO broker truth.

**Control, book level:** AI's published ARCHIVE control book — the armed three at registry
weights on the flat snapshot — rebuilt from m3's own re-walked rows reproduces
`BOOKS_MC_V1.json → archive_books.CONTROL_FTMO_ARMED_TODAY_3_on_the_archive`:
book_days **201 / 201**, mean R/book-day **0.18846 / 0.188464**, worst day **−1.77983 /
−1.779828**, FTMO two-phase `p_pass` **0.566017 / 0.56631**.

**Control, sleeve level:** the same flat-snapshot arm reproduces
`AA_SLEEVE_SPLITS_V1.json → <sleeve>.daily_net_r` to six decimals and to the day, on every
armed sleeve — `crypto` 0.236894 / 133 days, `energy_agri` −0.133176 / 34, `mx_btcusd`
0.222438 / 316, `sub_xvol_pullback` 0.908808 / 36. `sub_mid_dn_revert` is the one deliberate
difference (0.306747 / 392 here against AA's 0.170482 / 416) because this lane judges it on
**AM's re-clocked 533**, not AA's 503 — AM measured that AA's population was produced by a
clock defect and AN's substrate makes the same substitution.

### 4.1 Per sleeve

| sleeve | armed | conf | n | gross R/trade published → corrected(mid) | Δ | net R/day published | net R/day corrected | net R/day conservative |
|---|---|---:|---:|---|---:|---:|---:|---:|
| **crypto** | ✅ both | 0.85 | 181 | +0.56732 → **+0.43389** | **−23.5 %** | +0.19296 | +0.15592 | +0.10825 |
| **sub_mid_dn_revert** | ✅ both | 0.20 | 533 | +0.47842 → **+0.19325** | **−59.6 %** | +0.12928 | +0.07736 | **−0.16579** |
| **energy_agri** | ✅ both | 0.80 | 67 | +0.77921 → +0.77851 | −0.1 % | −0.09178 | −0.06542 | −0.09256 |
| **sub_xvol_pullback** | ✅ both | 0.45 | 88 | +1.26850 → +1.26764 | −0.1 % | +0.92706 | +0.97050 | +0.93018 |
| `mx_btcusd` (`as_walked`) | disarmed 08-05 | 0.025 | 318 | +0.34906 → +0.34906 | 0.0 % | +0.21130 | +0.22324 | +0.21079 |

`p(mean ≤ 0)` on the daily series, published → corrected → conservative: `crypto`
0.121 → 0.163 → 0.255; **`sub_mid_dn_revert` 0.087 → 0.188 → 0.958**; `sub_xvol_pullback`
0.0014 → 0.0009 → 0.0014; `energy_agri` 0.620 → 0.594 → 0.621 (negative on the archive
population throughout — a known population artefact, 14 of its 67 trades are blackout-dropped
carrying +38.49 R of gross).

**Only `mx_btcusd` and `sub_xvol_pullback` are unmoved because they are unmoved; `energy_agri` is
unmoved because it is 100 % target/stop exits on a wide stop.** `crypto` and `sub_mid_dn_revert`
move because their spread-over-risk is 4.4× and 19.1× BTCUSD's respectively
(`spread_r` mean 0.0542 and 0.2366 R against 0.0124).

### 4.2 The book, on the ARCHIVE population

Registry-confidence weights, 2 % nominal dial, each firm's MEASURED rules, 200,000 paths.

**ARMED_TODAY_4** = `crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback` (581 book days):

| arm | R/book-day | p(mean ≤ 0) | FTMO PH1 | FTMO 2-phase | FN PH1 | FN 2-phase |
|---|---:|---:|---:|---:|---:|---:|
| published walk, spread charged | +0.07654 | 0.0244 | 0.7023 | **0.5468** | 0.7235 | 0.5661 |
| **corrected walk, spread removed** *(the arithmetically right arm)* | **+0.06477** | 0.0416 | 0.6780 | **0.5157** | 0.7008 | 0.5366 |
| corrected walk, spread charged *(conservative bound)* | +0.02029 | 0.3011 | 0.5183 | **0.3370** | 0.5539 | 0.3626 |
| corrected @ high band, spread charged | +0.00158 | 0.4837 | 0.4565 | 0.2786 | 0.4965 | 0.3059 |

**The honest arm costs 5.7 pp of two-phase `p_pass` on FTMO (0.5468 → 0.5157) and 2.9 pp on
redacted_account.** The conservative arm costs 21.0 pp and takes the book's daily mean to
`p(mean ≤ 0) = 0.30`, i.e. not distinguishable from zero.

**These are NOT the published 0.9172 / 0.9331.** Those come from the **W7 recost caches**, a
different population; this lane has corrected the ARCHIVE walk only and every row above is
stamped `population: ARCHIVE`. **The W7 caches were built by the same class of bar walk on the
same BID archive and are therefore exposed to the same defect — that is an untested inference,
stated as one, and it is the single largest open item this lane leaves behind** (§7).

---

## 5. Q2 — DOES THE EXIT-CONTRACT FINDING SURVIVE A CORRECTION LARGER THAN THE EFFECT?

**Yes, and the inference that said it could not was a category error.**

Wave 19's owner report reasons: the effect is +0.03472 R/trade and the walker bias is
−0.0696 to −0.1160 R/fill, "so it is below the walker-bias floor". **A paired difference between
two exit contracts on the same rows is not a level.** Whatever part of the bias is common to both
contracts cancels exactly — and it is common on every row where `target_2.0R` never reaches its
target, which is 73–76 % of them.

Measured, not argued. `m3_exit_contract.py` walks BOTH contracts on the same emission,
on the same roster, tape, spread model and walker lane r1 used: **1,127,805 of 1,211,077
emissions**, eight open windows 2025-10 … 2026-05, sealed three untouched.
Control C1 (median `d_bps` vs `D8X_GEOM_V1.json`) max relative error **0.0**.

| anchoring | `target_2.0R` | `stop_only_horizon` | **paired delta** | day-block CI95 | p(≤0) | months + |
|---|---:|---:|---:|---|---:|---:|
| published (unshifted) | +0.017228 | +0.060379 | **+0.043151** | [+0.01224, +0.07770] | 0.00265 | 7/8 |
| level-anchored (the family's own geometry) | −0.029038 | +0.014564 | **+0.043602** | [+0.01378, +0.07717] | 0.00175 | **8/8** |
| fill-anchored (the live book's convention) | −0.085151 | −0.045990 | **+0.039161** | [+0.01154, +0.06977] | 0.00235 | 7/8 |

**The arithmetic:** the correction moves the LEVEL of `target_2.0R` by **−0.102379** R/emission
and the PAIRED DELTA by **−0.003990**. Ratio **25.7×**. Under level anchoring the delta moves
**+0.000451** — it gets *bigger* — and its month-count improves from 7/8 to **8/8**.

The exit swap is the one lever in the estate that a quote-side defect cannot reach, because it
is a difference and the defect is a common shift. Its own weakness is unchanged and is not a
walker problem: **p2's sealed out-of-sample value was +0.01002, it failed its own pre-declared
+0.02 bar, and d7 measured that a paired mirror captures 108.5 % of the best exit cell** — it is
a *contract* improvement available to any participant, not evidence of an edge. That is exactly
why it transfers, and it is why its natural home is a book where one R is 44–436 bps.

---

## 6. Q4 — THE CORRECTIONS LIST

### 6.1 Every sleeve in the estate

Pooled: gross **+0.112763 → −0.027726** R/trade (n 22,354); net **−0.174858 → −0.123124** —
moving the OTHER way, because `costs.model.cost_r` charges one full spread as a level (mean
0.1917 R) which under FILL anchoring the corrected walk already carries as geometry.
**9 of 29 sleeves change the sign of their published gross.** Full table in
`M3_RESULT_V1.json → Q4_estate_restatement_every_sleeve`; the ten largest movers:

| sleeve | n | gross published | gross corrected | Δ | exit reasons changed | sign flip |
|---|---:|---:|---:|---:|---:|---|
| liq_asia_up_low_metal | 157 | +0.12102 | −0.46497 | −0.58599 | 14.65 % | **FLIP** |
| asia_pdl_fade | 2,827 | +0.17195 | −0.32888 | −0.50083 | 12.98 % | **FLIP** |
| vss_fxcross_london_up_low | 308 | +0.23701 | −0.05520 | −0.29221 | 9.74 % | **FLIP** |
| **sub_mid_dn_revert** *(ARMED)* | 533 | +0.47842 | +0.19325 | −0.28518 | 7.13 % | |
| mx_cadjpy_d1_volume_surge_reversal | 286 | +0.12238 | −0.05594 | −0.17832 | 5.94 % | **FLIP** |
| mx_nzdjpy_d1_donchian_20_breakout | 503 | +0.05599 | −0.11779 | −0.17378 | 5.76 % | **FLIP** |
| metal_session_reversion | 837 | +0.11112 | −0.04398 | −0.15509 | 7.05 % | **FLIP** |
| kz_london_crypto_low | 286 | −0.16343 | −0.30849 | −0.14506 | 2.45 % | |
| asian_fade | 1,319 | +0.23821 | +0.10117 | −0.13704 | 5.15 % | |
| **crypto** *(ARMED)* | 181 | +0.56732 | +0.43389 | −0.13343 | 2.76 % | |

### 6.2 The published claims this lane overturns or confirms

| # | published claim | status | new number |
|---|---|---|---|
| 1 | `mx_btcusd @ target_5R` admits at the ratified rule, p 0.0011, two of three cost bands | **CONFIRMED** under the corrected walker at the **V27** family (59), not just V2 (35) | pooled +0.98169 → +0.98017, p 0.0011 → 0.0011, low+mid ADMIT / high REJECT |
| 2 | …and A1b flips it ADMIT→REJECT on the corrected null | **CONFIRMED and composed** — the walker adds nothing to the flip | corrected p 0.002810 → 0.002843 (+1.2 %), q@59 0.16579 → 0.16776 |
| 3 | `sub_mid_dn_revert` published gross +0.47842 R/trade | **WRONG by 59.6 %** | **+0.19325**; pooled OOS +0.1206 → **+0.0028** R/day (−97.7 %), 3/5 → **2/5** positive folds, the three negatives being the three oldest |
| 4 | `crypto` published gross +0.56732 R/trade | **WRONG by 23.5 %** | **+0.43389**; net R/day +0.19296 → +0.15592, `p(mean ≤ 0)` 0.121 → 0.163 |
| 5 | wave 19: "the exit swap is below the walker-bias floor" | **WRONG — a level bound applied to a paired difference** | the correction moves the level 25.7× more than it moves the delta; the delta is +0.0392 fill-anchored, p 0.00235 |
| 6 | wave 20 lanes r1/r2/v1-inputs: the ARMED set is `crypto, energy_agri, sub_xvol_pullback, mx_btcusd` | **WRONG at both ends** (v1's finding, independently re-derived here from the launcher) | armed today = `crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert` on **both** accounts |
| 7 | AI's ARCHIVE control book, armed three, FTMO 2-phase `p_pass` 0.566017 | **REPRODUCED exactly**, then restated for the armed FOUR | armed four: 0.5468 published → **0.5157** corrected → 0.3370 conservative |
| 8 | `energy_agri`, `sub_xvol_pullback` published economics | **CONFIRMED unmoved** (< 0.1 % of gross, 0 exit-reason changes) | — |
| 9 | pooled estate NET −0.174858 R/trade | **PESSIMISTIC**, not optimistic — the spread was charged twice | **−0.123124**; still negative, and no sleeve changes NET sign |

---

## 7. WHAT THIS LANE DOES **NOT** SETTLE

1. **The W7 recost caches are untouched.** Every `p_pass` the owner has seen for the armed
   book — 0.9172 FTMO / 0.9331 redacted_account, 4.501 %/month, the 5-sleeve expansion at 6.120 % —
   comes from `INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`, a different
   population from AA's archive walk. Those caches were built by the same class of bar walk on
   the same BID archive. **If the defect reaches them, every published book economic moves in the
   same direction as §4.2, and by an amount nobody has measured.** Establishing that is one
   session and it is the highest-value forward item this lane leaves.
2. **The cost convention is a genuine fork and both arms are published.** Removing
   `cost_r`'s spread term under FILL anchoring is arithmetically right (a long buys the ask,
   sells the bid, and realises exactly −1 R at its stop — the round trip is already in the R) and
   it is the arm that makes every number LESS bad, so it is the one that must be argued for.
   The spread-charged arm is carried everywhere for a reader who rejects the argument.
3. **`sub_mid_dn_revert`'s chronological decay is measured but not diagnosed.** Its three oldest
   OOS folds go negative under the correction while its two most recent stay positive. That is
   the same shape AN found on `mx_btcusd` in the opposite direction (admission decaying
   chronologically). Whether it is a regime story or a spread-era story is unmeasured.
4. **No arming or sizing recommendation is made or implied.** Composition, weights and the dial
   are Borhen's.

---

## 8. SAFETY

- **No `src/` byte edited.** This lane wrote six scripts and six artifacts under
  `phase20/receipts/m3/` and nothing else. `git status` carries no modification to any tracked
  source, config, test or launcher.
- **Live isolation.** Nothing here imports or drives `run_book.py`, `book_owner`, `book_engine`
  or any broker path; every walk is offline against `vps-bars-20260727` and the true-UTC M1
  packs. No live-forward P&L was read. The VPS was not touched.
- **H1 re-read at HEAD with the LFS caveat applied: 3 entries, IDENTICAL to before this lane** —
  `broker_net_cost_engine.py` (the pre-existing, owner-authorised CN break) plus the two
  unhydrated LFS pointers, which are not drift. `research/operations/broker_truth_layer_2026_07_29`
  was added to the sparse-checkout to materialise `BROKER_TRUE_COSTS_V1_1.json`; that is a
  checkout operation, it moved no tracked file, and the drift count is unchanged.
- **H2.** No source change, so no A/B is owed; the suite is untouched by this lane.
