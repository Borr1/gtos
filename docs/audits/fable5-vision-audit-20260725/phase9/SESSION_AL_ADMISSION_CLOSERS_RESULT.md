# Session AL — the admission closers: one lands, one is refuted, and the binding constraint moved to a field nobody had chosen

**Wave 9. Branch `phase9/admission-closers`, from `main` at `fff431c6b`. Blocks B1150–B1199. Not merged.**

**Scoped verification (agreement §2): 291 passed / 1 skipped / 0 failed / 0 errored at HEAD over a
14-file named blast radius. The 12 files that exist on both sides give 274 passed / 1 failed at the
merge-base and 275 passed / 0 failed at HEAD — 1 fixed, 0 regressed, mechanically diffed. +17 new
tests (16 passing, 1 skipped-by-design).** Receipt: `phase9/receipts/SESSION_AL_AB.md`, §9.

---

## 0. Headline

The commission set two banked prescriptions against AI §2.6's arithmetic. **One works, one is
refuted, and the thing that actually decides the admission turned out to be neither of them.**

> **`mx_btcusd_d1_donchian_20_breakout` at `target_5R` on the RECORDED-era population ADMITS at
> the sealed `B_balanced` α = 0.10 — and at `A_strict`'s Bonferroni α = 0.05 — at the RAISED
> family of 35.** n 232, pooled OOS **+0.9817 R/day**, p_raw **0.0011**, q **0.0385**, no core
> gate failing, **all five fold means positive**, drop-best retention 0.775, coverage 1.00. It is
> the first ADMIT any candidate has reached at the sealed α in this programme, and it did **not**
> need the pair: at p 0.0011 against a rank-1 bar of 0.10/35 = 0.002857 it clears on its own, so
> AI §0's "the two admit or fail as a PAIR" dissolves rather than being satisfied.

**Then my own adversarial pass took it apart, and the finding that survives is better than the
ADMIT would have been.** Seven attacks; the artifact's machine-checked `survived` block scores five
of them (A1, A5, A7 true; A2, A4 false) and A3 and A6 carry no boolean because neither is a
pass/fail test — A3 is a measurement and A6 an evidential aside. **Two came back negative and one of
those relocated the whole question**:

| | attack | result |
|---|---|---|
| A1 | is `target_5R` a spike picked from nine cells? | **SURVIVED** — a RIDGE. `target_4R` also admits (p 0.0023) and the surface is monotone 1R→5R (0.079 → 0.229 → 0.389 → 0.481 → 0.587 → 0.762 → **0.982**) then falls at 6R and 8R |
| A2 | is `RECORDED` a period selection wearing an outcome-independence argument? | **NEGATIVE** — §3 |
| A3 | is the superadditive interaction real? | measured: ×2.27 (population alone), ×1.37 (exit alone), **×13.18 together** |
| A4 | does it admit across the cost model's own envelope? | **NEGATIVE** — admits at `band_low` and `band_mid`, **REJECTS at `band_high`** (p 0.0051). Identical under both spread compositions |
| A5 | does it need the smallest family available? | **SURVIVED, asymmetrically** — the largest admitting family is **90** at α = 0.10 but only **45** at α = 0.05, against a declared 35. So the BH half has 2.6× headroom and the **Bonferroni half has 1.29×** and dies at m ≥ 46 — including at AA's 69, where BH still admits (q 0.0759) and Bonferroni does not. Both reject at 276 / 298 |
| A6 | does the DSR at the ledger's own measured trials change it? | **the attack as framed was inert twice; repaired, the DSR at all 9,853 ledger looks deflates to 0.9731 and still reports `significant`** — §3.6 |
| A7 | is one fold carrying it? | **SURVIVED** — all five positive; drop-**worst** 1.199 against drop-best 0.761 |

**A2 is the session's real result, and it points at a real hole — though not the one my first
draft named. An adversarial pass refuted four of that draft's five supporting sub-claims and left
the conclusion standing on a better foundation; §8.8 owns the whole exchange.**

> The wave-8 agreement §4 and AI §2.6 restrict to **`era_class == RECORDED`** in order to keep the
> eras whose cost is known. **`era_class` and the model's `decidable` both carry
> cost-trustworthiness information and they measure different things**: `era_class` records *how*
> an `era_ratio` was derived — and it drives the era term's `Coverage` (`spread_model.py:439-441`)
> and is the lookup key for the class half-width floor (`build_spread_model.py:1000`) that
> `decidable` is computed *from* — while `decidable` records *whether the resulting band is narrow
> enough to decide anything* (`hw = max(band_halfwidth_log, class_floor); decidable = hw <= 0.5`,
> pinned by `test_spread_model.py:107-115`). The restriction of record selects on the derivation
> and not on the width.
>
> **On BTCUSD they select different populations: the restriction retains 78 trades in quarters the
> model itself calls UNDECIDABLE and drops 86 in quarters it calls decidable.** 9 of 25 RECORDED
> quarters fail the 0.5 rule, worst being 2020Q1 — whose own `capture_requirement` field reads
> *"band spans 204058.1x, wider than any verdict can survive"* — and all 11 dropped quarters (7
> `SCHEDULE`, 4 `QUANTIZED`; 10 carry `mx_btcusd` trades) are `decidable`.
>
> **And the actual unwired hole is sharper than "a field nobody passes".** An undecidable
> **RECORDED** era does not degrade `Coverage` **at all**: `spread_model.py:440-441` degrades only
> when `era_class not in ("RECORDED", "NO_BAR_HISTORY")`, so **2020Q1 returns
> `coverage=MEASURED` on a 204,058× band** — measured by calling the model — and every
> `coverage_policy="restrict_to_priced"` consumer accepts it. The runtime switch that *would*
> refuse it works: `estimate(..., require_decidable=True)` raises on 2020Q1 and prices 2021Q3.
> **No production path passes it** — `src/costs/model.py:388`, the only non-test consumer of
> `spread_price`, omits it; the only call sites that pass it are `test_spread_model.py:193` and
> `:374`.

Measured on four defensible populations, same sleeve, same exit, same band, same family:

| population | n | R/day | p_raw | verdict | fold means |
|---|---:|---:|---:|---|---|
| ALL_ERAS | 318 | 0.547 | 0.0106 | REJECT | 1 of 5 negative |
| **RECORDED** (the agreement's) | 232 | **0.982** | **0.0011** | **ADMIT** | **0 of 5 negative** |
| DECIDABLE (the model's own rule) | 240 | 0.513 | 0.0581 | REJECT | 3 of 5 negative |
| INTERSECTION (both) | 154 | 0.892 | 0.0158 | REJECT | 2 of 5 negative |

**p ranges over 53× across the population axis while the effect size ranges 1.9×, and RECORDED is
the only population on which every fold mean is positive.** So the honest statement is: *the
admission is real at its stated stamp, it exists on exactly one of four defensible populations, and
what now decides it is which era-quality field defines that population* — a rule the estate has
never chosen deliberately. Not the multiplicity bill, which this session raised and paid. Not the
exit, which is a ridge. **The population.**

**Five other things this lane settled.**

1. **AB B658's banked prescription is REFUTED as a significance repair and CONFIRMED as a fragility
   repair.** `sub_xvol_pullback`'s `vr ≥ 1.4` variant, regenerated through the production
   `GenerationPort` over the full archive: n 88 → **406** and p_raw **worsens** 0.0061 → 0.0943 on
   all-eras@flat (0.0120 → 0.0626 on RECORDED@mid; 0.0058 → 0.0781 on ALL_ERAS@mid). The
   **per-trade** edge fell **3.3×** while the block count that buys resolution rose only 11 → 24,
   so the t-statistic went **down**. AB's *"n 88 → 420 is the trade a significance bar exists to make"* is
   measured to be the wrong trade. **But AI §2.5c's zero-integer-slack fragility is genuinely
   gone**: `n_folds_evaluable` 3 → **5**, `thin_fold_frac` → **0.0**. §2.

2. **The armed sleeve has NO p-value at all on the decidability population** — a third,
   independent measurement of AI §2.5c. `sub_xvol_pullback`'s n across the four populations is
   88 / 85 / **56** / — and at 56 it is **NOT_EVALUABLE** under `B_balanced`. It is also
   NOT_EVALUABLE under `A_strict` on RECORDED. Its evidence disappears under an option change *and*
   under a population change, independently, on a sleeve carrying real money. §4.

3. **`asia_pdl_fade`'s cross confirms AK's single-axis answer to 17 digits, and the level is
   mechanism rather than selection.** The stop × target × time-stop cross — **120 distinct cells,
   not 150**: `asia_pdl_fade.py:30` sets `TARGET_R = 3.0`, so the `tgt_3R` column is byte-identical
   to `tgt_native` at all 30 (stop, time-stop) pairs (max |Δ| **4.16e-17**). AK's winner is
   confirmed at the peak, **+0.08462647486216306 against `AK_EXIT_FRONTIER_V2.json`'s
   0.08462647486216306** — identical to 17 digits — and `as_walked` sits at rank 129. By AB's own
   rule the surface is **MIXED, not BROAD** (`ab_neighborhood.py:124` needs `frac_positive ≥ 0.60`;
   this is 89/150 = **0.5933**). And **median/best = 0.0969 is not a selection share**: all three
   axes are monotone (stop `frac_positive` 0.00 / 0.20 / 0.64 / 0.92 / 0.92 / 0.88), 0 of the 25
   stop-1.0 cells are positive, and an axis-wise argmax that never inspects a joint cell recovers
   **99.6 % of the peak**. Significance is still **23.1×** away. §5.

4. **The multiplicity bill was raised and paid — and my first statement of its price mixed two
   bases.** Three threshold cells were run, so three hypotheses joined the family via the ratchet:
   `CANDIDATE_BOOK_V1` **32 → 35** declared, **29 → 32** looks taken. Attributing "0.003448 →
   0.002857" to those three is a cross-basis comparison: 0.003448 is 0.10/**29**, AI's *looks-taken*
   arm, and 0.002857 is 0.10/**35**, this session's *all-declared* arm. Like for like the three cells
   cost **0.003448 → 0.003125** on looks-taken or **0.003125 → 0.002857** on all-declared — an
   **8.6–9.4 %** tightening, not 17 %. Every arm is still reported at the stricter 35, and **the
   admission also holds at V1's 32** (BH bar 0.003125, Bonferroni 0.0015625), so the raise is
   conservative rather than load-bearing. §6.

5. **Two mechanisms shipped, both closing holes that were open.** `register_threshold_variant` —
   the fidelity registrar for a parent rule at different constants, which the estate had no
   equivalent of and without which a threshold variant cannot be gated at all. And
   `test_candidate_family_v2_ratchet.py`, which closes the file-succession hole: the in-file ratchet
   turns a deleted member ROW into a load refusal and **never guarded a session publishing a smaller
   family in a NEW file**. §6.

**Nothing was armed, `config/agent_config.yaml` was not read for any live decision, no
broker-capable script was run, and the VPS was never contacted.** Three of my own load-bearing
claims were corrected or withdrawn by the adversarial pass; §8 owns all of them, and one of them
changed the headline.

---

## 1. Two controls, because a regeneration is only worth what its parity proves

A threshold change is the one repair class that cannot be re-simulated from AA's stored intents —
`vr ≥ 1.4` fires on bars the production cell never fired on, so there is no intent to re-label. The
generator has to run, and then the burden is proving the run is comparable to AA's.

**`regime_spine` was the cheap route and it is the wrong one, measured rather than assumed.**
`regime_spine.conditions.SUB_XVOL_PULLBACK` is already parameterised on exactly these three
thresholds. At the **production** params it fires on **94** bars where AA's walk has **88**, and the
six extra are precisely the pre-gap bars `bar_provider.candles_to_bars` drops — 6/94 = **6.38 %**,
which reproduces AB's independently published 6.4 % for this sleeve (`book_engine.py:83-90`). Those
six bars are **unreachable by the live book**: `--recover-pre-gap-bar` defaults `False`
(`book_engine.py:77`, assigned at `:107`). A variant built on `regime_spine` would carry a 6 % population the armed
book cannot trade.

So generation runs through the production `GenerationPort` on **AA's own pooled H4 grid** (44,681
closes, 2000-03-29..2026-07-27, pooled over all nine H4 sleeves' surfaces exactly as AA built it),
with `registry.BUILT["sub_xvol_pullback"].generator` swapped in-process for a recorder that keeps
every production step except `cell_matches` — the filter being swept — and records the raw state.
**One pass, 443.2 s, 149,247 reachable decision bars**, from which any threshold cell is an offline
filter.

| control | question | result |
|---|---|---|
| **C1 reachability + threshold** | does the production cell, recovered by the offline filter over the recorded state, equal AA's own 88 trades? | **IDENTICAL — 88 vs 88, zero on either side** |
| **C2 labelling** | does this session's labelling path reproduce AA's own `r_gross` on those 88, bit for bit? | **88 / 88 identical to 1e-12** |
| **C3 vs AI** | do AI's RECORDED as-walked figures reproduce with three extra sleeves in the run and a family of 35? | `mx_btcusd` **n 232, p 0.0063994** (AI: 232 / 0.006399); `sub_xvol_pullback` **n 85, p 0.0119988** (AI: 85 / 0.011999) |

C1 is the control that matters, because it validates the whole approach at once: if one offline
filter reproduces the production cell bar-for-bar, every other cell is the same filter at a
different constant and no cell can carry a reachability artefact the production cell does not.
C3's `q` differs from AI's and must — the family is 35 here against 29 there — while `p_raw` does not.

---

## 2. Item 1 — the `vr ≥ 1.4` variant: breadth refuted, fragility repaired

Three cells were run (AB's three banked rows), so three hypotheses were declared. Reachable fires
against AB's published `regime_spine` counts:

| cell | AB published | reachable here | Δ | superset of production? |
|---|---:|---:|---:|---|
| `vr 1.4, slope 1.25, ac 0.15` | 420 | **406** | −14 | yes |
| `vr 1.4, slope 1.5, ac 0.15` | 368 | **356** | −12 | yes |
| `vr 1.4, slope 1.0, ac 0.10` | 309 | **299** | −10 | yes |

The deficits are pre-gap bars, the same defect as the production cell's six.

**The gate, at m = 35, `B_balanced`. The two populations are at DIFFERENT cost bases and that is
part of the stamp:** `al_admission_closers.py:432` sets `spread_band` only on the RECORDED arm, so
ALL_ERAS prices at `flat_37_day_snapshot` (`spec.py:82`) — deliberately, because it is the
comparator against AA's own published figures, which were produced that way. **My first draft
printed this table under a "mid band" heading, which is an R0 violation in the section whose
subject is R0** (§8.8). The band now travels on every arm of the receipt, and the mid-band
restatement is below the table.

| cell | ALL_ERAS@flat R/day | p | RECORDED@mid R/day | p | folds eval. | thin |
|---|---:|---:|---:|---:|---:|---:|
| **production** (n 88 / 85) | **1.0264** | **0.00610** | **1.0215** | **0.01200** | **3** | — |
| `s125_ac015` (n 406 / 370) | 0.4176 | 0.09429 | 0.4656 | 0.06259 | **5** | **0.0** |
| `s150_ac015` (n 356 / 323) | 0.4537 | 0.04650 | 0.5007 | 0.02950 | **5** | **0.0** |
| `s100_ac010` (n 299 / 275) | 0.2893 | 0.23388 | 0.3445 | 0.15248 | **5** | **0.0** |

**At the mid band on ALL_ERAS** the same headline comparison is **1.0438 → 0.4408 R/day with
p 0.005799 → 0.078092 — 13.5× worse, not 15.5×** (`AL_DECIDABLE_POPULATION_V1.json`,
`AL_CANDIDATE_DOSSIER_V1.json`; this is the figure §4's table also carries, and the two now
reconcile). **The direction is identical at every band and on both populations**, which is why the
refutation stands regardless of which stamp a reader prefers.

**The prescription is refuted in the direction it was banked for.** The best variant p anywhere is
`s150_ac015` on RECORDED at **0.0295**, still **10.3×** short of the rank-1 bar. And the arithmetic
of *why* is worth stating correctly, because my first draft got both terms wrong:

- the **per-trade** edge falls **3.3×** on all-eras (`oos_mean_r_per_trade` 1.39322 → 0.42377) and
  **2.8×** on RECORDED (1.40577 → 0.50390). The 2.3× my first draft called "per-trade" was a
  *per-day* ratio;
- and the n that buys resolution is **not trades**. The null is a day-blocked sign-flip on the
  daily series (`stats.block_permutation_p`), so it is **blocks**: inverting the reported
  `p_floor`s through `perm_p_floor`'s own formula
  (`floor = (1 + n_perm·2⁻ᵇ)/(n_perm+1)`) gives **b = 11 → 24** on all-eras and 10 → 22 on
  RECORDED. So the extra resolution is **√2.18 = 1.48×**, not √4.6 = 2.14×, and a 3.3× smaller
  per-trade effect spends far more than that. Corrected, the conclusion is **stronger**.

**And AB's own artifact already pointed this way, so the gate added the p rather than the
direction.** AB publishes `mean_r_net_per_day` on every cell and B658's own text quotes
*"+0.325 R/trade **and +0.352 R/day**"* against production's 0.83666 per-day — a 2.38× fall AB
recorded and did not read as a warning. What no artifact had was a significance test, and that is
the whole of what this session added.

**And the fragility repair is real — but it is OPTION-CONDITIONAL, and my first draft stated it with
no option stamp.** The commission asked for this verification explicitly (*"at n ≈ 420 that should
relax — verify and state it"*), and AI §2.5c framed the fragility against **`A_strict`'s** floors
(`min_folds_evaluable` 4, `min_trades_per_fold` 8). Measured at both options, RECORDED@mid:

| | folds evaluable | thin frac | OOS folds positive | failing |
|---|---:|---:|---:|---|
| production @ `B_balanced` | **3** (floor 3) | 0.2 | 0.75 | significance |
| variant @ `B_balanced` | **5** | **0.0** | 0.80 | significance |
| production @ `A_strict` | 3 (floor **4**) | 0.2 | — | **NOT_EVALUABLE** |
| variant @ `A_strict` | **4** (floor 4) | **0.2** | **0.60** | stability + robustness + significance |

At `B_balanced` the repair is unambiguous: 3 → 5 evaluable folds, no thin fold, and the integer luck
is gone. **At `A_strict` it is half a repair.** The variant does buy evaluability where production
has none at all — production is NOT_EVALUABLE with no p, the variant has one — but it lands at
**4 folds against a floor of 4, which is zero integer slack again**, keeps `thin_fold_frac` at 0.2,
and newly fails **stability and robustness**. So AI §2.5c's concern is **relieved at the sealed
option and reproduced one level up**. That is the honest statement and not the one I first wrote.

**One more measurement worth having: AK's `target_4R` does not transfer to the variants.** On the
production cell it is +1.1565 R/day; on `s125_ac015` at RECORDED it takes the cell from +0.4656 to
+0.4395 and p from 0.0626 to 0.1225. So the exit repair is a property of the production cell's trade
population, not of the mechanism at a relaxed threshold.

**Prescription, not rejection — and the exit half WAS measured here, which my first draft twice said
it was not.** AK's `target_4R` on the PRODUCTION cell is in this session's own dossier at all four
populations, and it is the armed sleeve's best number anywhere in the session:

| `sub_xvol_pullback` | n | R/day | p_raw | q at m=35 | verdict |
|---|---:|---:|---:|---:|---|
| `as_walked` @ ALL_ERAS | 88 | 1.0438 | 0.005799 | 0.2537 | REJECT (significance) |
| **`target_4R` @ ALL_ERAS** | 88 | **1.1739** | 0.007699 | 0.2537 | REJECT (significance) |
| `as_walked` @ RECORDED | 85 | 1.0215 | 0.011999 | 0.2100 | REJECT (significance) |
| **`target_4R` @ RECORDED** | 85 | **1.3651** | **0.007999** | **0.1400** | REJECT (significance) |
| either exit @ DECIDABLE / INTERSECTION | 56 / 53 | — | — | — | **NOT_EVALUABLE** |

**`target_4R` on RECORDED is the armed sleeve's best measured cell — +1.3651 R/day at p 0.0080, a
1.5× improvement on the as-walked 0.0120** — and on ALL_ERAS the same exit *raises* R/day while
*worsening* p, which is exactly AK's warning that the two must not be quoted from different cells.
It is still **2.8×** short of the rank-1 bar (0.002857) and short of rank 2 (0.005714), so it does
not admit, and it does not exist at all on the two decidability populations. So the next lever is
**not breadth** (measured to cost more p than it buys) and **not this exit either** (measured, 2.8×
short) — it is **AB's regime dials**, unexplored for this sleeve, and more RECORDED-era trades.

---

## 3. Item 2 — the ADMIT, and the attack that relocated it

### 3.1 The measurement

`mx_btcusd @ target_5R`, RECORDED@mid, `B_balanced` α = 0.10, m = 35:

```
ADMIT: pooled OOS 0.98169 R/day net of broker-true cost over 5 purged/embargoed folds;
100% of OOS folds positive; q=0.0385 at benjamini_hochberg alpha=0.1 across a family of 35.
FIDELITY CEILING 96% live-recall (transferred_class, per_bar).
```

fold means `[1.134, 1.512, 1.866, 0.284, 0.112]`, drop-best retention 0.7747, coverage 1.00,
`thin_fold_frac` 0.0, `p_floor` 9.999e-05 (so the p is well-resolved, not a floor artefact: 10 of
10,000 block permutations beat the observation). It also ADMITs under `A_strict` — Bonferroni,
α = 0.05, `min_trades_per_fold` 8, `min_folds_evaluable` 4 — which is the harder option. (The
arming disqualification in `options.py:110-111` belongs to **`C_exploratory`** alone — `B_balanced`
is not disqualified either, and my first draft implied it was.)

**The pair structure dissolved.** AI §0: *"The two admit or fail as a PAIR … splitting the pair
makes both strictly worse."* That was true while `mx_btcusd` needed BH rank 2 and therefore needed a
partner to hold rank 1. At p 0.0011 it holds rank 1 itself, so the composition fact stops binding.
`sub_xvol_pullback` is still REJECT at p 0.0120 (RECORDED) / 0.0061 (all-eras) and is no longer the
blocker of anything.

### 3.2 A1 — the ridge, on the population it is claimed on

AD swept nine target cells and 5R won **on all eras**; the honest question is whether it is a ridge
**on RECORDED**, because a one-cell win out of nine is a selection. Measured, whole grid, RECORDED@mid:

| cell | 1R | 1.5R | 2R | 2.5R | 3R | **4R** | **5R** | 6R | 8R | none |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R/day | 0.079 | 0.229 | 0.389 | 0.481 | 0.587 | **0.762** | **0.982** | 0.671 | 0.327 | −0.324 |
| p_raw | 0.217 | 0.025 | 0.0064 | 0.0052 | 0.0030 | **0.0023** | **0.0011** | 0.025 | 0.200 | 0.942 |
| verdict | | | | | | **ADMIT** | **ADMIT** | | | |

Monotone from 1R to 5R, an interior optimum, and **two adjacent cells admit**. A grid median of
+0.481 R/day, so even read at the median rather than the peak the cell is not a spike. `target_none`
collapsing to −0.324 confirms the interior optimum is real rather than an artefact of the grid edge.

### 3.3 A2 — the attack that came back negative, and its mechanism

At `target_5R` the RECORDED half earns **+1.024 R gross per trade** and the complement **−0.017**,
on calendar spans that **overlap** (2017-08..2025-09 against 2021-07..2026-07). A restriction
defended as outcome-independent was separating a strongly profitable population from a flat one, and
"it only distrusts the cost model" cannot explain a *gross* gap of 62×.

**`era_class` is assigned per calendar QUARTER**, so it is not a per-trade filter at all — it removes
whole quarters. Which makes it outcome-**independent** in assignment (a quarter's class cannot see a
return) and **not** outcome-**neutral**, because quarters are not exchangeable in a trending asset.
Those are different properties and an admission rests on the second.

Then the quarter table said something worse. The full BTCUSD era ledger, with the model's own
decidability rule applied:

| era | class | ratio | half-width | decidable? | | era | class | ratio | half-width | decidable? |
|---|---|---:|---:|---|---|---|---|---:|---:|---|
| 2018Q2 | RECORDED | 8.94 | 0.9103 | **NO** | | 2021Q3 | SCHEDULE | 9.00 | 0.0000 | yes |
| 2018Q3 | RECORDED | 11.89 | 1.2926 | **NO** | | 2022Q4 | SCHEDULE | 9.00 | 0.0000 | yes |
| 2019Q3 | RECORDED | 0.86 | 1.3815 | **NO** | | 2023Q3 | SCHEDULE | 12.00 | 0.0000 | yes |
| 2019Q4 | RECORDED | 2.30 | 0.6935 | **NO** | | 2025Q4 | SCHEDULE | **1.00** | 0.0000 | yes |
| **2020Q1** | RECORDED | 1.59 | **6.1131** | **NO** | | 2026Q1 | SCHEDULE | **1.00** | 0.0000 | yes |
| 2020Q3 | RECORDED | 1.69 | 0.7462 | **NO** | | 2026Q2 | SCHEDULE | **1.00** | 0.0000 | yes |
| 2020Q4 | RECORDED | 2.59 | 0.8554 | **NO** | | 2026Q3 | SCHEDULE | **1.00** | 0.0000 | yes |
| 2021Q1 | RECORDED | 35.20 | 0.9005 | **NO** | | | | | | |
| 2025Q3 | RECORDED | 8.60 | 0.9511 | **NO** | | | | | | |

**Nine of twenty-five RECORDED quarters exceed the model's own 0.5 threshold and are kept. All
eleven quarters it drops are `decidable`, and ten of them carry `mx_btcusd` trades** (2017Q2 has
none) — seven `SCHEDULE`, four `QUANTIZED` at half-width 0.044–0.081, and the three traded
`QUANTIZED` quarters hold **25 of the 86 dropped trades**. 2020Q1's `capture_requirement` field
reads *"band spans 204058.1x, wider than any verdict can survive"*, and it sits inside the
"measured" population with `coverage=MEASURED`.

> **Do NOT read the `SCHEDULE` quarters' raw half-width of 0.0 as precision — my first draft did,
> and that was the error at the centre of it.** All **263** raw-0.0 eras in the model are
> `SCHEDULE` and **none** is `RECORDED`: a `SCHEDULE` quarter is a single backfilled constant, so
> cross-instrument dispersion, split-half noise and D1-vs-H4 disagreement are all identically zero
> **by degeneracy**. `_measure_class_hw_floor` (`build_spread_model.py:745-753`) exists to repair
> exactly that — *"the band collapses to a point on the era where the data is least
> trustworthy"* — and floors it to **0.18229** (ratio 0.833–1.200), which is what the model
> actually publishes; a committed test, `test_schedule_eras_are_never_certain`, enforces it.
> **BTCUSD 2021Q3 is a `SCHEDULE` quarter estimated from three nonzero bars**, with raw half-width
> 0.0 and 12 of the 86 dropped trades. And there are **three** 2026 quarters, not four — the fourth
> ratio-1.0 quarter is 2025Q4, and neither it nor 2026Q1 overlaps the reference window
> 2026-06-18..07-25, so "1.0 by construction because they sit inside the window" is true of
> 2026Q2/Q3 only. For the rest, 1.0 means the broker backfilled the current constant, which is the
> look-ahead the model's own `honest_limit` warns about.

**So the defect is not "the restriction drops the eras it knows best."** It is narrower and it is
still decisive: the two fields select different populations, the restriction retains 78 trades in
quarters the model calls undecidable and drops 86 in quarters it calls decidable, and — the part
that is a genuine hole rather than a preference — **an undecidable `RECORDED` era degrades nothing
downstream.** `spread_model.py:439-441` reads:

```python
cov = anchor_cov
if fb is not None and at_utc is not None and not decidable:
    cov = Coverage.MODELLED
elif at_utc is not None and era_class not in ("RECORDED", "NO_BAR_HISTORY"):
    cov = weakest(cov, Coverage.MODELLED if era_class in ("SCHEDULE", "FLOORED")
                  else Coverage.TRANSFERRED)
```

so the `not decidable` branch is reachable only through the `fb` fallback path. Measured by calling
the model: `2020Q1 → class RECORDED, decidable False, coverage MEASURED`;
`2018Q3 → RECORDED, False, MEASURED`; `2021Q3 → SCHEDULE, True, MODELLED`;
`2022Q1 → QUANTIZED, True, TRANSFERRED`. **Nine BTCUSD quarters therefore price as MEASURED while
the model's own artifact calls them capture requirements**, and every consumer of
`coverage_policy="restrict_to_priced"` accepts them. `require_decidable=True` refuses 2020Q1
correctly, and **no production path passes it**: `src/costs/model.py:388`, the only non-test
consumer of `spread_price`, omits it, and the only call sites that pass it are
`tests/test_spread_model.py:193` and `:374`.

**`SpreadModel.estimate` already takes `require_decidable=`. It defaults `False` and nothing in the
estate passes it.** So the field that answers the question the restriction was introduced to ask has
been sitting in the model, unused, since AG shipped it.

### 3.4 The four populations, and the cell that settles it

`AL_POPULATION_INTERSECTION_V1.json` — `target_5R`, band mid, m = 35, every population:

| population | n | R/day | p_raw | q | verdict | fold means |
|---|---:|---:|---:|---:|---|---|
| ALL_ERAS | 318 | 0.547 | 0.0106 | 0.185 | REJECT | 1.18, 0.91, **−0.05**, 0.60, 0.10 |
| **RECORDED** | 232 | **0.982** | **0.0011** | **0.0385** | **ADMIT** | 1.13, 1.51, 1.87, 0.28, 0.11 |
| DECIDABLE | 240 | 0.513 | 0.0581 | **1.0** | REJECT | 2.17, **−0.13**, **−0.05**, 0.60, **−0.03** |
| **INTERSECTION** | 154 | 0.892 | 0.0158 | 0.516 | REJECT | 2.18, **−0.10**, 1.02, 1.58, **−0.23** |
| RECORDED ∧ ¬decidable | 78 | 0.914 | 0.0392 | — | REJECT (3 folds) | −0.01, 2.20, 0.55 |

> **The `q` column is the one figure here that is not a property of the row alone, and my first
> draft mixed two artifacts in it.** BH is a step-up over the whole submitted vector, so the same
> `p_raw` gets a different `q` depending on which sleeves were co-judged. `DECIDABLE` reads **1.0**
> in this artifact and **0.662** in `AL_DECIDABLE_POPULATION_V1.json` — same p, different co-judged
> set (that driver submits three extra threshold-variant sleeves). I had taken the 0.662 from the
> other file while citing this one. `p_raw` is comparable across both; **`q` is not comparable
> across artifacts and must be read only within one**. That is R0 applied to a column rather than a
> figure, and it is a rule this doc needed and did not have.

Four readings, all of which belong in front of the next composition:

- **The INTERSECTION rejects.** The admission exists only under the *looser* of the two era-quality
  fields, so it depends on the field choice. That is the finding.
- **RECORDED is the only population with no negative fold mean.** DECIDABLE has three, INTERSECTION
  two, ALL_ERAS one. The ADMIT rests on a fold-sign pattern no other population reproduces.
- **DECIDABLE's worse p is a fold story, not an effect story.** Its effect (0.513) is within 6 % of
  ALL_ERAS' (0.547) while its p is 5.5× worse — because dropping the 78 undecidable-RECORDED trades
  takes the negative-fold count from **one to three** — folds 2 and 5 flip sign, fold 3 was already
  negative. Those trades concentrate in 2018–2021 and removing them destabilises the early folds.
- **The 78 trades are not free-riders.** On their own they earn **+0.914 R/day**, as much as the
  full RECORDED population, on three evaluable folds at p 0.0392. Dropping them is not removing
  noise; it is removing a third of the evidence.

**So the repair is not "pick DECIDABLE".** It is: *the population rule is a decision the estate has
never made explicitly, the two candidate fields disagree by 53× in p, and the evidence for each is
now published.* Whoever owns agreement §4 owns that choice, and it changes an admission. Filed as
repair-queue row `POPULATION_RESTRICTION_USES_THE_WRONG_FIELD` against `src/costs/spread_model.py`
and the agreement itself.

### 3.5 A4 — the band, which is the second qualification

| arm | verdict | R/day | p_raw |
|---|---|---:|---:|
| RECORDED @ **low** | **ADMIT** | 0.983 | 0.0011 |
| RECORDED @ **mid** | **ADMIT** | 0.982 | 0.0011 |
| RECORDED @ **high** | REJECT | 0.878 | 0.0051 |
| ALL_ERAS @ low / mid / high | REJECT | 0.548 / 0.547 / 0.454 | 0.0105 / 0.0106 / 0.0314 |

Session AG's rule is that a cell winning only at the flat snapshot has not been shown to win. This
one wins at two of three bands and its `band_high` p of 0.0051 is inside the **rank-2** threshold
(0.005714) though not rank 1 — so at the pessimistic band the pair structure comes back and
`mx_btcusd` would need a partner again. Identical under both spread compositions (`v2_damped` and
`v1_multiplicative`), so AH's composition repair is not what is carrying it.

### 3.6 The accounting choice that is actually holding the admission up, priced

**The threshold-variant-costs / exit-cell-free rule (§6.3) is the single load-bearing accounting
decision behind this ADMIT, and my first draft disclosed the choice without pricing it.** A refuter
put the number on it and the number is uncomfortable:

| | count | charged to the family |
|---|---:|---|
| exit cells pushed through the gate in this programme | **≥ 2,260** | **0** |
| — `EXIT_FRONTIER_V1.json` (AD) | 1,507 | 0 |
| — `EXIT_FRONTIER_V1_TRAIL.json` (AD) | 124 | 0 |
| — `AK_EXIT_FRONTIER_V2.json` (AK) | 468 | 0 |
| — `AL_ASIA_PDL_FRONTIER_V1.json` (this session) | 150 | 0 |
| — this session's own `target` ridge on RECORDED | 11 | 0 |
| threshold cells this session ran | 3 | **3** |

**The admission dies at m ≥ 91** (α = 0.10) **and m ≥ 46** (α = 0.05). So charging **4.0 %** of the
exit cells — 91 of 2,260 — rejects at the sealed α, and **2.0 %** rejects under Bonferroni. The rule
is not a technicality at the margin; it *is* the pivot.

**The defence, stated as an argument rather than as an assumption**, is AI §0's: BH corrects for
distinct hypotheses, not for the number of times each was measured, and 2,260 exit cells on ~30
sleeves are re-measurements of ~30 hypotheses, not 2,260 new ones. AD and AK both applied it. It is
the right principle. But it is a *principle*, not a measurement, and the honest statement is that
**the estate's own trial ledger counts all 9,853 looks and prices them at zero in the family-wise
bill**, deliberately, and that the instrument built to price *within*-hypothesis search is the DSR —
which brings us to A6.

**A6 was inert twice, and I reported it as SURVIVED.** Its own question text says *"BH across sleeves
cannot see that nine target cells were searched. The DSR is the instrument that can."* Neither half
of what I concluded from it holds:

1. **The gate never reads the DSR into a verdict.** `gate.py:844-845` writes `sv.telemetry["dsr"]`
   and no `sv.gates[...]` key consumes it. So "feeding `n_trials` leaves the verdict unchanged" is
   true *by construction* and tests nothing. My own artifact note said as much and I still scored the
   attack as survived.
2. **No DSR at the measured count was ever computed** (9,063 when the attack first ran; 9,853 now —
   the ledger grows as this session records its own looks). `_dsr_sweep` evaluates only
   `spec.n_trials_sweep` =
   `(1, 16, 64, 128, 512, 2048)`, and `at_spec_n_trials` looks up `sweep["9063"]`, which does not
   exist — the artifact's `at_spec_n_trials` carries the count and **no `dsr` value**, and
   `family_dsr` is `{}` outright.

**The repair is one line and it was made, so the number exists now.** Adding the measured count to
`n_trials_sweep` — without which `at_spec_n_trials` looks up a key that was never evaluated — gives:

| n_trials | 1 | 16 | 64 | 128 | 512 | 2,048 | **9,853 (the ledger's own count)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| DSR | 1.0000 | 0.9998 | 0.9991 | 0.9983 | 0.9949 | 0.9879 | **0.9731** |
| `sr_benchmark` | 0.000 | 0.095 | 0.125 | 0.138 | 0.162 | 0.183 | **0.204** |
| `significant` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **✓** |

on `sr_per_period` **0.3304**. So **the DSR at the trial ledger's full 9,853 looks still deflates to
0.9731 and still reports significant** — which is real, positive evidence, and the strongest answer
available to §3.6's exit-cell objection. Two limits, both stated: the DSR is a selection-deflation on
the *Sharpe*, not a family-wise error rate, so it does not substitute for the multiplicity bill; and
`sr_variance` is *estimated* from per-sleeve Sharpe dispersion over 29 sleeves × 2,497 days
(`gauntlet.estimate_sr_variance_from_sleeves`) rather than measured on this sleeve. **A6's verdict
is therefore INCONCLUSIVE as I originally framed it and POSITIVE on the instrument that actually
works** — and the artifact now says both.

---

## 4. The armed sleeve, across the same axis

`sub_xvol_pullback` is trading real money on FTMO today via `run_book.py --tags`. Across the same
four populations, `B_balanced`:

| population | n | verdict | R/day | p_raw | folds evaluable |
|---|---:|---|---:|---:|---:|
| ALL_ERAS | 88 | REJECT (significance) | 1.0439 | 0.0058 | 3 |
| RECORDED | 85 | REJECT (significance) | 1.0215 | 0.0120 | 3 |
| **DECIDABLE** | **56** | **NOT_EVALUABLE** | — | **none** | 3 |
| RECORDED @ `A_strict` | 85 | **NOT_EVALUABLE** | — | **none** | — |

**The armed sleeve's evidence disappears under a population change and under an option change,
independently.** That is the third measurement of AI §2.5c's fragility and the one closest to the
money. It is **not** an argument for disarming — wherever the sleeve is evaluable its pooled OOS is
the estate's highest at +1.02 to +1.04 R/day — it is a fact the arming discussion has to carry, and
its prescription is the exit, not more trades from a relaxed threshold.

Note the direction: DECIDABLE drops **more** of this sleeve's trades (88 → 56) than RECORDED does
(88 → 85), because its metals-and-index surface lives in wide-band eras. The two fields do not
disagree in a consistent direction across sleeves, which is another reason the choice has to be made
rather than inferred.

---

## 5. Item 4 — `asia_pdl_fade`, taken seriously

**150 cells, the first stop × target × time-stop CROSS in the programme.** AK and AD both swept
axes separately and stacked the argmaxes; AD §7.1 measured that stack losing to the best single cell
on 17 of 25 sleeves, which is what a stack does when axes interact. Grid: stop ∈ {1.0, 1.5, 2.0,
2.5, 3.0, 3.5} × target ∈ {native, 2R, 3R, 4R, 5R} × time-stop ∈ {none, 8, 16, 32, 48} M15 bars
(32 is the live contract). Gated at the declared 35 with the full family; every cell in the ledger.

**Top of the surface:**

| cell | R/day | p_raw | OOS folds positive | coverage |
|---|---:|---:|---:|---:|
| `stop_2.5x_tgt_native_ts_none` (**= AK's winner**) | **+0.0846** | 0.0659 | **5/5** | 0.812 |
| `stop_2.5x_tgt_5R_ts_none` | +0.0843 | 0.0815 | 5/5 | 0.812 |
| `stop_2x_tgt_5R_ts_48` | +0.0800 | 0.1005 | 4/5 | 0.812 |
| `stop_3x_tgt_native_ts_none` | +0.0757 | 0.0605 | 5/5 | 0.812 |
| `as_walked` (rank **129** of 150) | −0.0686 | — | — | — |

**Four things, and my first draft got three of them wrong. An adversarial pass over this section
corrected all three and the corrected version is more useful; §8.8 owns it.**

1. **The grid is 120 distinct cells, not 150.** `sleeves/asia_pdl_fade.py:30` sets
   `TARGET_R = 3.0` and `:112` sets `target_dist = TARGET_R * sd`, so the `tgt_3R` column is the
   `tgt_native` column: identical `pooled_oos_mean_r` at all **30** (stop, time-stop) pairs, max
   |Δ| **4.16e-17**, identical `p_raw`, `n_trades` and exit-reason histograms. My "150-cell cross"
   double-counted one target level, and the rank-1 cell in my own table is that duplicate beating
   its twin by 4e-17.
2. **The surface is MIXED by AB's own rule, not BROAD.** `ab_neighborhood.py:124` requires
   `frac_positive ≥ 0.60` for BROAD; this is 89/150 = **0.5933** — one positive cell short. Run
   verbatim, AB's `_verdict()` returns **MIXED** with `as_walked` as the selected cell (rank 129)
   and **SPIKE** with the cell I actually propose (rank 1–2 against a `0.05 × 150 = 7.5` threshold
   at `frac < 0.60`). I imported AB's BROAD *prose* at a `frac` AB assigns elsewhere.
3. **"~90 % of the level is selection" is not licensed, and the opposite is closer to true.**
   `median/best = 0.0969` is a property of *this grid*: it becomes **0.2521** on stop ≥ 2.0,
   **0.3414** on the stop-2.5 row, because **0 of the 25 stop-1.0 cells are positive** — and stop
   1.0 is the as-walked geometry the repair exists to replace. All three axes are monotone and
   ordered:

   | axis | mean R/day by level | `frac_positive` |
   |---|---|---|
   | stop 1.0 → 3.5 | −0.0999, −0.0214, +0.0208, +0.0362, +0.0338, +0.0182 | 0.00, 0.20, 0.64, **0.92**, **0.92**, 0.88 |
   | target 2R → 5R | −0.0279, −0.0014 (=native), +0.0056, +0.0149 | 0.33, 0.60, 0.70, 0.73 |
   | time stop 8 → none | −0.0210, −0.0234, −0.0035, +0.0185, +0.0191 | 0.47, 0.43, 0.67, 0.70, 0.70 |

   and AB's own header states the mechanism for the stop axis (`ab_neighborhood.py:20-24`: *"cost in
   R is a price drag divided by the stop"*). **Decisive:** a rule that never inspects a joint cell —
   each axis's argmax over its own marginal — lands on `stop_2.5x_tgt_5R_ts_none` at **+0.08427 =
   99.6 % of the peak**. If 90 % of the level were selection, an axis-wise rule could not recover
   99.6 % of it. What the ratio licenses is *"the median of this grid is a tenth of its peak"*; it
   is not a selection share, and **no held-out selection estimate exists** here at all, because
   cells are ranked on the same `pooled_oos_mean_r` that defines them.
4. **The axes do not separate — but the axis that moves is the TIME STOP, not the target.** With the
   duplicate ties resolved, best target by stop reads `native, 5R, 5R, native, native, 2R` — four of
   six pick native. The artifact's `best_time_stop_by_stop` is `{1: 48, 1.5: none, 2: 48, 2.5: none,
   3: none, 3.5: none}`, and that is where a stack loses: the from-baseline per-axis stack
   (`stop_2.5x_tgt_native_ts_48`) reaches +0.07232, rank 11, **85.5 % of the peak**. My separability
   test is also underpowered as written — it demands the conditional argmax over five targets be
   *identical at all six stops*, which noise alone would defeat, so `False` carries little
   information.

**And the cross's own result contradicts "the cross was necessary."** Its peak equals AK's
stop-only winner to **17 digits**, so 120 distinct cells bought **0.00000 R/day** over the
single-axis answer. §6.3 says exactly that (`asia_pdl_fade`'s cells "add nothing" to the bill) while
my first §5 said the opposite; the correct reading is that **the cross CONFIRMED the single-axis
answer** rather than showing it was the wrong object, and AD §7.1's warning does not bind here.

**And "significance is the only thing left" is true of the BEST cell and false of the surface** —
a fifth correction, and the one that most changes how §5 should be read. The failing-gate histogram
over all 150 gated cells:

| failing gates | cells |
|---|---:|
| `expectancy + lifetime + stability + robustness + significance` | 57 |
| `expectancy + lifetime + robustness + significance` | 35 |
| **`significance` alone** | **26** |
| `lifetime + robustness + significance` | 15 |
| `robustness + significance` | 11 |
| four others | 6 |

So **26 of 150 cells are significance-limited and 124 also fail economics.** That is a direct
argument against the median-cell reading my first draft proposed: the median cell (+0.0082, ranks
74–78, p 0.39–0.45) does not fail significance alone — it fails expectancy and lifetime too, so
"size on the median" would be sizing on a cell that has no edge to size.

**Significance at the best cell is 23.1× away** from the rank-1 bar (0.0659 against 0.002857) and
**all 150 cells are REJECT** — 12 reach p < 0.10, none clears 0.002857. The next lever is **regime
conditioning** from `AB_REGIME_DIALS_V1.json`, unexplored for this sleeve; the entry-hour axis AH
found for the FX D1 cohort is *unavailable* here because the rule is first-of-day by construction.

---

## 6. What was built

### 6.1 `register_threshold_variant` — the registrar the estate had no equivalent of

`fidelity_for` fails closed as UNKNOWN for an unregistered name and `fidelity_refusal_is_hard`
defaults True (`spec.py:393`, so every option inherits it), so **a threshold variant could not be gated at all**, for a reason that
has nothing to do with fidelity. `register_surface_expansion` is the wrong instrument: it demands a
`symbol` and a `timeframe` and writes a `basis_note` claiming the book has never traded that symbol,
all three false for a variant on the parent's own surface.

The stamp is `TRANSFERRED_CLASS` and **never** the parent's own measured recall, and that is the
conservative direction rather than a convenience: a relaxed threshold fires on a **superset** of the
parent's bars and the extra bars were never observed live, so a parent's `MEASURED_DIRECT` recall
does not cover them. For `sub_xvol_pullback`, already `transferred_class`, the grant is numerically
the record it already has — **no relaxation of any kind, pinned by a test**. Four guards: the parent
must be authored, the member must carry `thr_`, an authored entry is never overwritten, and **a
variant whose params equal production's is refused** — that would let one hypothesis be counted as
two, the mirror image of the double-count `CANDIDATE_FAMILY_V1` closed. `EXPANSION_PREFIXES` is
split so each registrar accepts only its own prefixes; widening the shared union can no longer widen
what a registrar admits. **11 tests.**

### 6.2 The ratchet across a file succession

`high_water_size` turns a deleted member ROW into a load-time refusal and `high_water_looks` does
the same for a retracted look. **Nothing guarded the easier route to a smaller bill**: publish a NEW
declaration file with fewer members and point the driver at it — the loader reads one file and has
no predecessor to compare against.

This session had to supersede V1, because `test_candidate_family.py:382-385` asserts the shipped
declaration is exactly 32 / 29 / 276 / 298 and an in-place edit would read as four defects rather
than as an intended raise. That is the operation that opens the hole, so the guard lands with it:
`test_candidate_family_v2_ratchet.py` requires every `CANDIDATE_FAMILY_V*.json` to be a **superset**
of whatever it says it `supersedes`, per family, with non-decreasing high-water marks, every late
addition logged in `history`, and — the test I would not have thought to write without the ratchet's
own logic — **the stated price arithmetically equal to α/m at the new m**. **6 tests.**

### 6.3 The declared family, raised and paid for

`CANDIDATE_FAMILY_V2.json`: `CANDIDATE_BOOK_V1` **32 → 35** declared, **29 → 32** looks taken —
priced like for like, an **8.6–9.4 %** tightening of the rank-1 bar (0.003448 → 0.003125 on
looks-taken, 0.003125 → 0.002857 on all-declared; the artifact now carries both bases and the
warning against mixing them). The rule applied, stated so it can be checked:

- a **threshold** variant creates a new hypothesis → it joins the family and raises the bill;
- an **exit** cell re-measures an existing hypothesis → it does not.

That split is AI §0's principle (*"BH corrects for the number of distinct HYPOTHESES, not for the
number of TIMES each was measured"*) applied to the two kinds of change waves 7–8 made, and it is
what AD and AK already did in practice — every cell in `EXIT_FRONTIER_V1` and `AK_EXIT_FRONTIER_V2`
was gated inside AA's family without adding a member, while no session had ever run a threshold
variant through the gate. So `mx_btcusd @ target_5R` and `asia_pdl_fade`'s cells add **nothing** to
the bill and the three xvol cells add three. It is the one judgement call in the amendment, it is
written into the `history` entry, and **§3.6 now prices it: ≥ 2,260 exit cells were gated across
this programme and charged zero, and charging 4.0 % of them rejects the admission.** A reader who
does not accept the principle should read the ADMIT as conditional on it, which is why the number is
printed rather than left implicit.

**All three cells are declared and not only the best**, because the ratchet's content is that a look
taken cannot be un-taken — declaring only the winner is exactly the curation it exists to prevent.
All three were submitted in **one** gate run, and `gate.py:803` floors the effective family at
`max(n_judged, declared)` with `n_judged = len(verdicts)` at `:789`.

**And on the arm that produced the ADMIT the declared floor is doing all the work, which is worth
saying plainly.** My first draft wrote *"`n_judged` is 35 whatever is declared"* — false, and false
on exactly that arm. Measured: `n_sleeves_judged` is **35 on all twelve ALL_ERAS arms** and **32 on
all twelve RECORDED arms**, because three sleeves have no RECORDED trade at all and so are never
handed to the gate. On ALL_ERAS the bill is self-enforcing; on RECORDED — including the ADMIT — the
35 comes **entirely from the declaration**. That is an argument *for* the ratchet rather than
against it: without the declaration the RECORDED arms would have corrected at 32, and a restriction
that drops sleeves would have quietly bought a cheaper bill.

---

## 7. Artifacts

| file | what |
|---|---|
| `phase9/receipts/ADMISSION_CLOSER_V1.json` | the commissioned deliverable: 24 arms, both candidates, both populations, both exits, three options, the family state after the ratchet, the BH composition at α 0.05 / 0.10 / 0.20, and both controls |
| `phase9/receipts/AL_XVOL_REACHABLE_STATE_V1.json.gz` | 149,247 reachable decision bars with raw state; the parity control lives in it |
| `phase9/receipts/CANDIDATE_FAMILY_V2.json` | the ratcheted declaration, 35 / 32, with `history` and the price |
| `phase9/receipts/AL_BTC_ADVERSARIAL_V1.json` | the seven attacks, each with its result whether or not it supports the claim |
| `phase9/receipts/AL_BTC_ERA_MECHANISM_V1.json` | the quarter table, the complement's economics, the cost-envelope repair |
| `phase9/receipts/AL_DECIDABLE_POPULATION_V1.json` | 54 arms: three populations × three bands × two options × three exits |
| `phase9/receipts/AL_POPULATION_INTERSECTION_V1.json` | the five-population table with fold means — the cell that settles §3.4 |
| `phase9/receipts/AL_ASIA_PDL_FRONTIER_V1.json` | 150 gated / **120 distinct** crossed cells, AB's own verdict run verbatim, the twin-column measurement, the failing-gate histogram, and the separability test with its own underpowering stated |
| `phase9/receipts/AL_CANDIDATE_DOSSIER_V1.json` | per-candidate rows, R0 enforced: every figure inside a `(population, exit, band, option, family)` key, with per-fold windows |
| `phase9/receipts/SESSION_AL_AB.md` | the §2 scoped verification receipt |
| `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | **96 → 104 rows**, 8 appended, session `AL`, 0 byte-level duplicates |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | every look; **8,488 → 10,018** look events, 1,530 of them AL's (the count grows with each re-run, so quote it as a floor) |

---

## 8. What I got wrong

### 8.1 I would have published the ADMIT as the headline

My first draft of §0 led with *"the admission landed at the sealed alpha"* and treated A2 as a
footnote about sample composition. A2 is not a footnote — it is the finding, and the ADMIT is
conditional on a population choice the estate has never made deliberately. The correction is in the
numbers rather than in a caveat: §3.4's table is the headline table now, and §0 says the population
is the binding constraint.

### 8.2 My A7 attack reported INCONCLUSIVE when the data was in front of it

The first version guessed three key names for the per-fold series (`per_fold_oos_mean_r`,
`oos_fold_means`, `fold_oos_mean_r`), found none, and wrote `all_folds_positive: null` — i.e. an
adversarial attack that silently declined to run. The series is at `gates.stability.fold_means` and
all five are positive. **A silent null in an adversarial pass is worse than a failed attack**, because
it reads as "checked" in the artifact. Fixed, re-run, and the fix is named in the source comment.
AK §7.9 recorded the identical class of error on `test_mean_r`; I read that note and made the same
mistake anyway, which is why `_fold_series` in the dossier now falls back loudly rather than to nulls.

### 8.3 "The pair admits" was the wrong frame to carry into the session

The commission's item 3 asks for the pair composed at the sealed α, and I built the composition
machinery for a pair. The pair is the wrong object once one member clears rank 1 alone — BH's step-up
structure only couples candidates while the lower-ranked one needs the higher one's threshold. The
composition tables are still emitted (every arm, every family, α 0.05 / 0.10 / 0.20) because they are
what shows the coupling dissolving, but reading them as "did the pair admit" would miss it.

### 8.4 My first `asia_pdl_fade` run crashed on its own output after gating all 150 cells

`max(sub)` over `(metric, target_r, time_stop_bars)` tuples compares `float` to `None` on a metric
tie, and the native-target cells carry `target_r=None`. 189 s of gating discarded for a reporting
bug. Keyed on the metric alone. The same shape as AK §7.6's `_summary` crash.

### 8.5 Three wrong numbers in my own §0, caught by re-reading the era ledger

All three were in the paragraph I called the session's real result, which is the worst place for them:

- **"9 of 24 RECORDED quarters"** — it is **9 of 25**. I counted from a partial table printed by an
  earlier probe rather than from the ledger.
- **"all 7 quarters the restriction drops carry half-width 0.0"** — false as written. There are
  **11** non-RECORDED quarters (7 `SCHEDULE` + 4 `QUANTIZED`); only the seven `SCHEDULE` ones carry
  raw half-width 0.0, the `QUANTIZED` ones carry 0.044–0.081. The true claim is **stronger**: all
  eleven are `decidable`. I had reached for the vivid number instead of the correct one.
- **"`require_decidable=` … which nothing in the estate passes"** — false. `test_spread_model.py:193`
  and `:374` both pass it, and they exist precisely to prove it works. The defensible sentence is
  *"no driver or receipt in the estate passes it; its only call sites anywhere are two tests"* —
  which is a sharper finding, because a switch that is tested and unused is a stronger statement
  than one that is merely unused.

I also asked, before claiming it, whether `decidable` is computed from `band_halfwidth_log` or from
`band_halfwidth_log_floored` — because if it used the floored value the "0.0 half-width" observation
would be misleading. **I got that answer wrong too, and §8.8 has it.** I checked two eras (2021Q3:
raw 0.0 / floored 0.1823 / true; 2020Q1: raw 6.1131 / floored 6.1131 / false) and concluded "raw" —
but *both* are equally consistent with the floored rule, because 0.1823 ≤ 0.5. The two data points I
chose could not distinguish the two hypotheses, and I asserted one anyway. The source says floored
(`build_spread_model.py:1000-1004`) and a refuter verified it over all 2,653 eras with zero
mismatches. Asking the right question and then answering it from data that cannot settle it is worse
than not asking.

### 8.6 My dossier's own invariance control was wrong, and it fired on itself

`AL_CANDIDATE_DOSSIER_V1.json` carries a control asserting that `p_raw`, `pooled_oos_mean_r`,
`n_trades` and — in my first version — `verdict` are identical across the five declared-family arms
of each group. It reported **5 violations**, all on `verdict`, and **the control was the thing that
was wrong**: `declared_family_size` enters `significance`, so `q_value` and `verdict` are exactly
what a family change is *supposed* to move. Replaced with the assertion that is actually worth
having: the three genuinely invariant fields, plus **monotonicity** — a larger declared family may
only ever be stricter, so an ADMIT at a larger *m* than a REJECT of the same candidate is a real
defect. That check is now in the artifact and reports 0.

### 8.8 The multi-agent refuter pass, which found five more and one of them was the section's core

Eight refuters were run over this doc's load-bearing claims (agreement §7, Borhen's standing
opt-in), each instructed to refute rather than confirm and to default to refuted when it could not
verify a number from an artifact. **Four returned refuted.** Everything they found is verified in the
numbers above rather than footnoted here; this is the ledger of what changed.

**1. The §3.3 defect paragraph was wrong in four of five sub-claims** and the conclusion still
stands. Wrong: *"`era_class` does not carry cost-trustworthiness information"* (it is the sole
determinant of the era term's `Coverage` at `spread_model.py:439-441` **and** the lookup key for the
class half-width floor at `build_spread_model.py:1000` that `decidable` is computed *from*, so the
two are not orthogonal — one is an input to the other); *"`decidable` is computed from the raw
half-width"* (it is computed from the **floored** value, verified over all 2,653 eras with zero
mismatches — my two-data-point check could not distinguish the two because the max floor 0.3646 sits
below the 0.5 threshold, so I asserted a mechanism the data I had could not resolve); *"all seven
dropped quarters carry half-width 0.0"* (11 dropped, 4 of them `QUANTIZED` at 0.044–0.081); *"all
four 2026 quarters"* (there are **three**; the fourth ratio-1.0 quarter is 2025Q4, and neither it
nor 2026Q1 overlaps the reference window, so my stated mechanism was false for half the set).

**And the rhetorical core of my §0 — "the restriction drops the eras it knows best" — read a known
degeneracy as precision.** All **263** raw-0.0 eras in the model are `SCHEDULE` and none is
`RECORDED`, because a `SCHEDULE` quarter is one backfilled constant and every dispersion term is
identically zero by construction. The model has a function whose docstring says so
(`_measure_class_hw_floor`, `build_spread_model.py:745-753`: *"the band collapses to a point on the
era where the data is least trustworthy"*) and a committed test that enforces the repair
(`test_schedule_eras_are_never_certain`). BTCUSD 2021Q3 — one of the quarters I called well-known —
is estimated from **three** nonzero bars.

The refuter then handed me the finding I should have made, which is stronger: **an undecidable
`RECORDED` era degrades nothing downstream.** Verified by calling the model: 2020Q1 →
`RECORDED / decidable False / coverage MEASURED` on a 204,058× band, because
`spread_model.py:440-441` degrades only on `era_class`. That is the actual unwired hole and it is
now what §0 and §3.3 say.

**2. §2's table was stamped with the wrong cost band — an R0 violation in the section about R0.**
`al_admission_closers.py:432` sets `spread_band` only on the RECORDED arm, so every ALL_ERAS figure
I printed under a "mid band" heading is the **flat 37-day snapshot**, and the arm dicts recorded no
band at all, so the receipt could not tell a reader either. That is also why my §2 printed
1.0264 / 0.00610 and my §4 printed 1.0439 / 0.0058 for the same sleeve, population and exit and
never reconciled them. Fixed three ways: the band now travels on every arm with a note, §2 carries
both stamps, and the mid-band restatement (13.5× rather than 15.5×) is printed beside the table.
**The cost band is the one artefact route §8.7 did not list**, and it is the one where my stamp was
wrong.

**3. "The per-trade edge fell 2.3×" was a per-day ratio wearing a per-trade label**, and the √n term
was the wrong n. Per-trade falls **3.3×** / **2.8×**; the null is a day-blocked sign-flip so the n
that buys resolution is blocks, which rose only **11 → 24** (derived from the published `p_floor`s
through `perm_p_floor`'s own formula). Both corrections make the refutation stronger, not weaker.

**4. §5's three headline claims about `asia_pdl_fade` were all wrong**: "150 cells" is 120 distinct
(the `tgt_3R` column duplicates `tgt_native` because `TARGET_R = 3.0`), "BROAD" is MIXED by AB's own
0.60 threshold, and "~90 % of the level is selection" is refuted by the axis-wise rule recovering
99.6 % of the peak on monotone axes. Worse, §5 said "the cross was necessary" while §6.3 said its
cells "add nothing" — an internal contradiction the refuter caught and the numbers settle in §6.3's
favour.

**5. Three more, from the two refuters that attacked the family arithmetic.** The stated price of
the amendment mixed two bases and overstated what three cells cost by ~2× (§6.3, and the artifact's
own `price_stated_up_front`, both corrected). The **threshold-costs / exit-free rule is the pivot the
admission stands on and its price was never printed** — ≥ 2,260 exit cells at zero, 4.0 % of them
enough to reject — which is now §3.6. And **A6 was inert twice and I scored it SURVIVED**: the gate
never reads the DSR into a verdict (`gate.py:844-845` writes telemetry only, which my own artifact
note conceded), and no DSR at the measured count was ever computed, because `_dsr_sweep` only
evaluates `n_trials_sweep` and the count is not in it. The sweep did reach 2,048 at DSR 0.9879 `significant:
true`, which is real evidence and not the evidence the attack claimed.

Two smaller ones, both fixed in place: A5's headroom is **asymmetric** — 90 at α = 0.10 but 45 at
α = 0.05, so the Bonferroni half dies at m ≥ 46 including at AA's 69, and my §8.7 bullet had quoted
only the 90; and the +0.98169 headline is the `pooling_weights="equal_by_fold"` default
(`spec.py:180`), i.e. exactly the unweighted mean of the five fold means — which the doc had never
said, and which is worth saying because it means one 46-day fold and one 4-day fold count the same.

**6. And a completeness critic then found two BLOCKING gaps the eight refuters had not, both of the
same shape: the artifacts were richer than the prose and two of them contradicted it.**

- **The commission's explicit fragility guard was verified at one option only, and the other option
  contradicts what I published.** §2 stated the repair unconditionally; at `A_strict` — the option
  AI §2.5c's floors come from — the variant reaches 4 evaluable folds against a floor of 4, keeps
  `thin_fold_frac` 0.2, and newly fails stability and robustness. §2 now carries the four-row table
  and says the concern is relieved at the sealed option and reproduced one level up.
- **The measurement §10 called "the one move this session did not make" was made, and it is the
  armed sleeve's best number in the session.** `sub_xvol_pullback @ target_4R` on RECORDED is in
  `AL_CANDIDATE_DOSSIER_V1.json` at n 85, **+1.3651 R/day, p 0.0080, q 0.1400** — and the doc said
  twice that it was "unswept" and "never gated on the restricted population". Published in §2 now,
  with all four populations, and §10 item 2 restated to what actually remains.

Five further reporting-layer gaps, all closed: the masthead's verification numbers were stale
against §9 (283/13 files → 291/14 files, and it now records the 1 fixed test);
`AL_ASIA_PDL_FRONTIER_V1.json` still encoded the three §5 claims the prose had retracted, which
matters because **AL's own R11 makes the artifact authoritative over the prose** — regenerated with
the twin-column measurement, AB's `_verdict()` run verbatim, tie-resolved argmaxes and the
failing-gate histogram; `AL_POPULATION_INTERSECTION_V1.json` carried no band / option / family stamp
on any arm, which is precisely the R0 defect item 2 above claims to have fixed — regenerated with
all five stamp fields plus an in-file warning that `q` is comparable only within one artifact; the
asia frontier's gate-failure distribution was measured and unreported; and `CANDIDATE_FAMILY_V2`'s
own `note` field still stated the pre-raise counts.

**7. What the refuters confirmed, which is worth as much.** The parity control is not circular: a
refuter recomputed the 88 keys by four independent paths — including two that call the **production**
`SE.cell_coords` + `SE.cell_matches` and contain none of my predicate code — and all four give the
same 88, which is what kills the "a bug in both the recorder and the filter cancels" hypothesis. The
BH arithmetic at m = 35 reproduces by hand; `CANDIDATE_FAMILY_V2` is a strict superset by content
with all three additions logged and the stated price pinned to α/m; the four-population table
reproduces to five decimals with the 53× and 1.9× ranges checking out; and the safety audit found
`config/agent_config.yaml` byte-identical at the merge-base, at HEAD and in the worktree, H1 at
2 UNHYDRATED-LFS / 0 DRIFTED with none of my edited files bound, no broker import in any of the ten
receipt scripts, and nothing merged or pushed.

### 8.7 What the adversarial pass could NOT refute

- The parity controls. C1 (88 vs 88, identical) and C2 (88/88 `r_gross` at 1e-12) are exact, and
  every variant number depends on them rather than on an argument. A refuter recomputed the 88 by
  four paths, two of which call the **production** `cell_coords` + `cell_matches` and contain no
  code of mine, which is what a cancelling-pair-of-bugs hypothesis cannot survive. **What C1 does
  NOT cover, and my framing did not say:** it shares the `GenerationPort`, the bars archive and the
  pooled grid with AA, so a *common-mode* reachability defect is invisible to it — the 6.4 % pre-gap
  drop is precisely such a defect, disclosed two paragraphs earlier but not inside the C1 claim.
  What makes the generalisation independently safe is that `_generate_intents` applies every
  reachability gate upstream of the generator call (`book_engine.py:576`) with no
  candidate-count-dependent filter, so the reachable set is threshold-independent by construction.
- C3's reproduction of AI's RECORDED figures to six decimals with three extra sleeves in the run,
  which in turn reproduced AF's independently published 232 / +0.3894 / 0.0064.
- The ridge (A1): two adjacent admitting cells and a monotone rise into an interior optimum is not
  a spike, and the grid median of +0.481 R/day is above the ADMIT threshold's effect requirement.
- The headroom (A5), read asymmetrically: the largest family admitting at α = 0.10 is **90** and at
  α = 0.05 is **45**, against a declared 35 — so the admission does not depend on the family being
  small, but the Bonferroni half has only 1.29× of room and dies at m ≥ 46, *including at AA's
  historical 69* where the BH half still admits at q 0.0759. It fails at 276 / 298 either way. And
  it still admits at V1's un-raised 32, so the raise is conservative rather than load-bearing.
- The refutation of AB B658. I looked hard for a way the variant's worse p could be an artefact of
  my regeneration — the pre-gap deficit, the labelling path, the fold count, the population, and
  **the cost band, which is the route I omitted from this list and the one where my published stamp
  was wrong** (§8.8 item 2) — and the controls close each one. The direction reproduces at flat,
  low, mid and high bands and on both populations. The variant's p really is worse.

---

## 9. Verification — the §2 scoped receipt

**Blast radius**, `python3 scripts/pytest_failset.py scope --base fff431c6b --include-worktree`:
**28 changed paths → 14 test files** by import closure and path literal, no escapes, no unresolved,
no deleted tests.

| side | scope | result |
|---|---|---|
| **HEAD** | all 14 files | **291 passed / 1 skipped / 0 failed / 0 errored** |
| **merge-base `fff431c6b`** (source reverted) | the 12 files on both sides | **274 passed / 1 failed** |
| **HEAD** | the same 12 files | **275 passed / 0 failed** |
| `pytest_failset.py diff` | mechanical | **unchanged 0, fixed 1, REGRESSED 0 — "No regressions"**, exit 0 |

The one **fixed** test is `test_implementation_state_block_citations.py::test_the_in_flight_wave_range_is_declared_and_shrinking`,
and it is a repair announcing itself in the agreement §2.3 sense: writing blocks B1150–B1169 raised
the block ceiling past AL's own `IN_FLIGHT_WAVE_RANGES` floor, which made that entry **DEAD** by the
test's own definition — below the ceiling and exempting nothing. The test named the remedy in its
assertion message ("Drop it"); AL's entry is retired and AM's `B1200–B1249` stays, because it is
still a live pre-declaration above the ceiling. That is the ACTIVE / PRE-DECLARATION / DEAD split
Session U's adversarial pass added, working as designed on the first session to trip it.

**+17 new tests**: 11 in `test_fidelity_threshold_variant.py`, 6 in
`test_candidate_family_v2_ratchet.py` (16 passing, 1 skipped by design — the `supersedes`
parametrisation skips V1, which supersedes nothing). Reconciliation: 275 + 17 = 292 = 291 passed +
1 skipped.

**How the A/B was run, and the one thing the receipt cannot record.** The base side was produced
**in-worktree** by reverting `src/research_infra/walkforward/fidelity.py` and
`tests/test_implementation_state_block_citations.py` to their merge-base bytes and restoring them
afterwards, because agreement §4 warns that a fresh worktree at the merge-base is not a usable A/B
for tests that read sparse-excluded artifacts. The consequence, stated because a reader would
otherwise be misled: **`SESSION_AL_AB.md` records both captures at the same commit with
`dirty: true`, so nothing inside the receipt distinguishes the before side from the after side** —
the discriminator is the reverted source, which the tool has no field for. The captures are 1 bad →
0 bad on identical scopes, which is the comparison; the commit label is not.

**One process note against myself:** restoring the citations test with `git checkout` silently
discarded the uncommitted `IN_FLIGHT_WAVE_RANGES` edit, and the only reason it was caught is that
the next thing run was a grep for it. Reverting an uncommitted file for an A/B is a way to lose work
and the restore has to be a copy-back, not a checkout.

**Also verified:** `main` moved forward by one commit (`b48441e4c`, the wave-9 train integration)
after this branch was cut, so the A/B base is the merge-base `fff431c6b` and not `main`. The first
scope I ran used `--base main` and pulled in three files this session never touched; the corrected
scope is the one above.

**H1**: the R2 contract's drift check reports **2 UNHYDRATED-LFS and 0 DRIFTED** in this worktree,
which per `CLAUDE.md` §3's 2026-07-30 amendment is a property of local LFS hydration and not of any
commit. **No bound file was edited** — `walkforward/fidelity.py`, `walkforward/candidate_family.py`,
`walkforward/gate.py`, `regime_spine/conditions.py` and `components/ultimate_book/sleeves/substrate*.py`
are all **unbound**, checked before editing. `config/agent_config.yaml` is **byte-identical at the
merge-base, at HEAD and in the working tree** (independently verified by blob hash); it was read only
as a config dict for the research override AA already uses (`ultimate_book_include_clean3: True` in
memory). No broker module is imported by any of the ten receipt scripts, and nothing was merged or
pushed.

## 10. What is next, and for whom

**For Borhen / whoever owns agreement §4 — one decision, and it changes an admission.**
Which era-quality field defines the restricted population: `era_class == RECORDED` (the standing
rule, under which `mx_btcusd @ target_5R` **ADMITS** at the sealed α at low and mid bands), or the
spread model's own `decidable` (under which it **REJECTS**), or their intersection (**REJECTS**).
The evidence for all three is in `AL_POPULATION_INTERSECTION_V1.json` and the arithmetic is in §3.4.
This is not a sizing or arming call — it is a measurement-protocol call — but it decides whether the
estate has an admitted candidate, so it should not be made by whichever driver runs next.

**For the next session, in value order:**

1. **`mx_btcusd`'s sample, not its exit.** The exit is a ridge and the bill is paid; what is left is
   318 trades on one symbol over nine years. AF refuted the 9-symbol crypto cluster as
   *diversification* (dispersion ratio 4.74) — that is a different question from pooling for
   *power*, and pooling `mx_btcusd` with its donchian siblings for a single significance test has
   never been run. It would also raise the bill, and the bill's arithmetic is now mechanical.
2. **`sub_xvol_pullback`'s regime conditioning, because the exit is now spent.** `target_4R` on
   RECORDED *was* gated here — +1.3651 R/day at p 0.0080, the armed sleeve's best cell in the
   session, still 2.8× short (§2). Breadth is refuted and the exit is measured, so what is left is
   AB's regime dials and more RECORDED-era trades. Its evidence also vanishes entirely on the two
   decidability populations (n 56 / 53, NOT_EVALUABLE) — a coverage fact an arming discussion
   should carry.
3. **`asia_pdl_fade`'s regime conditioning.** The exit surface is exhausted — 150 gated / 120
   distinct crossed cells, **MIXED by AB's own 0.60 rule** at `frac_positive` 0.5933, and the level
   is mechanism rather than selection (§5). And read the shortfall correctly: only **26 of 150 cells
   fail `significance` alone**; 124 also fail expectancy, lifetime, robustness or stability, so
   "significance is what is left" describes the *best* cell and not the surface. AB's dials are
   untouched for it.
4. **The `require_decidable` wiring.** One keyword argument, already in `estimate`'s signature and
   already exercised by two tests, that **no production path passes** — plus the sharper half of the
   same gap: an undecidable **`RECORDED`** era does not degrade `Coverage` at all
   (`spread_model.py:440-441`), so a 204,058×-wide band prices as `MEASURED` and every
   `restrict_to_priced` consumer takes it. Whichever population rule wins, the rule should be expressed through the model's
   own switch rather than reimplemented per driver — this session reimplemented it three times.

**Not mine and untouched:** the VPS, arming, tokens, gates, α, sleeve composition, ratifying the
family (extended mechanically via the ratchet; the *rule* is Borhen's), merging to `main`,
`config/agent_config.yaml`.
