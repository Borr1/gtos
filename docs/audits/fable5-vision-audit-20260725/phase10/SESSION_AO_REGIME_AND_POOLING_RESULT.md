# Session AO — the regime dials were already inside the cells, the pair admits on a median, and the p that admits it is the test's own floor

**Wave 10. Branch `phase10/regime-pooling`, from `main` at `8db17b29c`. Blocks B1300–B1349. Not merged.**

**Scoped verification (agreement §2): see §9.**

---

## 0. Headline

The commission set three sleeves against one named lever — regime conditioning on Session AB's
published dials — and a fourth item to pool `mx_btcusd` for power. **The lever does not exist for
two of the three sleeves, and it is arithmetic rather than a result.** The pool does not work, and
the reason is measured rather than argued. And the one thing in the session that *did* reach an
ADMIT was taken apart by its own resolution audit.

> **Every one of Session AB's five published dials takes exactly ONE bucket over every trade
> both substrate sleeves have ever produced.** 88 of 88 for `sub_xvol_pullback`, 533 of 533 for
> `sub_mid_dn_revert` (AM's re-clocked population). Four of AB's five dials ARE
> `substrate_engine`'s confluence coordinates — measured, max |Δ| **0.0** and **zero** bucket
> disagreements over all 3,448 trades of the three sleeves — and `substrate.py:69-79` makes each
> of those coordinates a firing **condition** of the cell. A bucket-level regime gate on them is
> the identity filter. `asia_pdl_fade` pins 1 of 5 (`SURFACE_OPEN`, by construction) and is the
> only sleeve in the set where the commission's question is askable as posed.

So `AL §10 item 2`'s *"AB's regime dials, unexplored for this sleeve"* cannot be executed as
written, and neither can `diagnostics.Prescription.REGIME_GATE_OR_PARK` for either substrate
sleeve — the gate emits it because it cannot see that the sleeve already gates on the variable it
names. Two sessions in a row were routed at a no-op. That is now pinned by a test that needs no
market data (`test_ao_regime_dials_inside_substrate_cells.py`, 14 tests), and it is filed as the
session's primary repair row.

**What conditioning therefore remains is two things, and one of them works.**

| | axis | result |
|---|---|---|
| the free substrate **coordinates** | `sub_xvol_pullback` is depth-4 and leaves `rngpos` / `comp` / `session` free; `sub_mid_dn_revert` is depth-7 and leaves **none** | the pre-declared `rngpos == mid` covers 82 of 88 trades — free in name only — and makes p **worse** (0.0080 → 0.0302). The pre-declared `comp == coil` holds **19** trades and misses the gate's floor by one |
| the dial **level** inside the pinned bucket | `vol=xhi` is `vr ≥ 1.6` with no ceiling; `trend=up` is `slope50 > 1.5` with no ceiling; `persist=rand` is an open interval | **`vr` is strongly monotone in the pre-declared direction**: Spearman **+0.4073** on 78 priced trades, permutation p **0.00025**, tertile net R/trade **0.512 → 1.111 → 2.124**, a 4.1× spread inside the sleeve's own firing range |

**The `vr` level is the session's real regime finding and it is not an admission filter.** The
cell `vr ≥ median` is NOT_EVALUABLE at n 44 — volatility expansions cluster in calendar time, so
the split concentrates trades into fewer folds — and `vr ≥ 2.0`, AB's own published `xhi` value,
holds 18 of 88. It belongs at **sizing**, where a level tilt costs no sample and the runtime
already has the consumer (`admission.py`'s Kelly-lite conviction multiplier).

### The admission, and why it does not stand

Composed in **one** gate run at the declared family of 39 — because BH is a step-up over the
whole submitted vector and hand-composing two artifacts' p-values is the R0 violation AL §3.4
names — `sub_xvol_pullback @ target_4R` conditioned on `ac60 ≥ median` **ADMITS at BH rank 2
alongside `mx_btcusd @ target_5R`**. AI §0's pair structure, which AL §3.1 dissolved, comes back
and closes. On the sleeve that is trading real money today.

**Three independent things kill it, and the third is the one worth having.**

1. **The cut is post-hoc.** The *direction* was pre-declared in source before any number; the
   *cut* is the sample's own median.
2. **At the axis's mechanism cut it is 4.2× worse.** `ac60 ≥ 0` — AB's own published `random`
   boundary and the literal reading of the pre-declared phrase *"the less mean-reverting half"* —
   gives p **0.017498** against the median cut's 0.004200. Bonferroni over the two cut rules
   tried on one pre-declared axis: **0.008399** against a rank-2 bar of **0.005128**. The
   admission does not survive the smallest honest bill for the search that found it.
3. **The p that admits it is a count of duplicate permutation draws, and the verdict flips on
   the seed.** 44 trades → **16 OOS days** → block 2 → **8 blocks**. `perm_null.py:201-202`
   computes `p = (1 + ge)/(n_perm + 1)` where `ge` counts draws beating the observation; when
   the observation is the maximum over all `2⁸ = 256` achievable sign assignments — which it is
   — `ge` is simply how many of the 10,000 draws *duplicated* the identity assignment, i.e.
   `Binomial(10000, 1/256)`: mean 39.06, sd 6.24, so **p = 0.004006 ± 0.000624**. The observed
   0.004200 implies `ge = 41`, z = +0.31. **BH rank 1 (0.002564) is 2.3 sd BELOW that floor and
   therefore unreachable at 8 blocks; the rank-2 window above it is 1.8 sd wide.**

   **Measured on the production path, not argued.** The same cell over 20 permutation seeds:

   | sweep | seeds ADMIT | p range | p sd | control? |
   |---|---:|---|---:|---|
   | **the conditioned cell** | **16 / 20** | [0.003500, 0.005799] | **0.000658** | — |
   | its ungated parent | 0 / 20 | [0.007699, 0.011599] | 0.000954 | never admits |
   | **`mx_btcusd @ target_5R`** — the estate's one admission | **20 / 20** | [0.000700, 0.002000] | 0.000364 | **always admits** |

   The measured sd of **0.000658** against the Binomial prediction of **0.000624** is 5 %
   agreement, which is what turns "the p is at its floor" from a description into a mechanism.
   And the two controls do not move, so the sweep discriminates rather than manufacturing
   instability: **the conditioned cell's verdict is the only one in the set that depends on
   `spec.seed`.** Nobody had checked AL's admission for seed stability; it is stable, and its
   worst seed (p 0.002000) still clears rank 1.

**That third point is a defect in the gate, not just in this cell — and my first statement of it
was wrong in the gate's favour.** `gate.py:849-863` does **not** compare `p_raw` to `p_floor`; it
refuses only when `p_floor ≥ spec.alpha`, i.e. when *no* p on the series could ever be
significant. At 8 blocks that guard is 25× from firing, and **nothing in the gate relates an
observed p to its own resolution.** The mechanism generalises to every conditioned cell in the
estate: **a filter buys a smaller p by destroying the resolution that would justify it** — it
removes trades, which removes OOS days, which removes blocks, which raises `2**-blocks`. Filed as
`SIGNIFICANCE_PASSES_A_P_ONE_STEP_ABOVE_ITS_STRUCTURAL_FLOOR` with a concrete proposal (a 2×
headroom floor, which would catch this arm and nothing else in the session — every other arm runs
7×–659×) and pinned by `test_ao_p_floor_headroom.py`.

**The only conditioned cell that IS admissible in this session — `rngpos == mid`, a declared
member of `CANDIDATE_FAMILY_V3` — rejects at p 0.0302.**

### The cost band, which corrects two wave-9 headlines

`al_asia_pdl_frontier.py:104-106` and `am_submid_reclock.py:457/:528` set no `spread_band`, so
every figure in `AL_ASIA_PDL_FRONTIER_V1.json` and `SUBMID_RECLOCK_V1.json` is at `spec.py:82`'s
**flat 37-day snapshot**. All three published cells reproduce here **to 1e-12 on R/day, p_raw and
n**, which is what licenses the comparison:

| cell | flat (AL's / AM's basis) | mid band | |
|---|---:|---:|---|
| `asia_pdl_fade @ stop_2.5x_tgt_native_ts_none` (AK's winner, AL's rank 1) | **+0.08463** R/day, p 0.0659, 5/5 folds | **−0.27414**, p 1.0 | **sign flip** |
| `asia_pdl_fade` as-walked | −0.06865, p 0.8630 | **−0.88266**, p 1.0 | ×12.9 |
| `sub_mid_dn_revert` re-clocked (AM's headline) | +0.21049, p **0.0198**, retention **+0.3609** | **+0.04004**, p **0.3524**, retention **−3.5673** | |

AG's own rule is that a cell winning only at the flat snapshot has not been shown to win. So
*"`asia_pdl_fade`'s exit surface is exhausted and 23× from the bar"* and *"the re-clock's
robustness statistic changes sign"* are both **flat-snapshot** statements. The re-clock is still a
real repair — it changes which trades exist and reproduces bar-for-bar — but at the banded cost
its retention runs −0.270 (RECORDED) to −3.567 (ALL_ERAS), and the pre-declared level direction
is what partially restores it (§4).

### The pool

`mx_btcusd`'s power pool, AL §10 item 1, never run. **It does not work, and the prediction stated
in the driver's docstring before the run is confirmed quantitatively.** `target_5R`,
RECORDED@mid, m = 39:

| arm | k | trades | OOS days | ×solo trades | ×solo days | R/day | p_raw | |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **solo_btc** | 1 | 232 | 184 | 1.00 | 1.00 | **+0.9817** | **0.0011** | **ADMIT** |
| `pool_all9` | 9 | 594 | 349 | 2.56 | **1.90** | +0.5764 | 0.0067 | REJECT |
| `pool_n_ge_100` (outcome-independent) | 4 | 542 | 338 | 2.34 | 1.84 | +0.6174 | 0.0052 | REJECT |
| `pool_coherent_positive` (**selects on the outcome**) | 5 | 500 | 311 | 2.16 | 1.69 | +0.6808 | 0.0062 | REJECT |

The null is a block sign-flip on the pooled **daily** series, so days buy resolution and trades do
not. A donchian-20 breakout is a common-factor event: trades ×2.56 but days only ×1.90, so **26 %
of the extra sample is a calendar duplicate**, while the effect size falls to 0.587× — p ends
**6.1× worse**. The same arithmetic AL §2 measured on the threshold variant. And the
outcome-independent `n ≥ 100` rule (p 0.0052) **beats** the coherent-positive rule that selects on
the outcome (p 0.0062), reproducing AH §4.2's −0.004525 R/trade on a family AH never covered.

**The band fragility the commission asked about is not repaired: no pooled arm admits at any
band**, and the solo cell's `band_high` REJECT (p 0.005099, inside rank 2's threshold but needing
a partner to hold rank 1) reproduces AL A4 exactly.

**Also settled.** `asia_pdl_fade`'s pre-declared level direction is **refuted at permutation
p 5e-05 in the opposite direction** on 2,717 priced trades — AH's standing precedent for a
reversal mechanism does not transfer to a liquidity sweep. The armed sleeve's DECIDABLE loss is
attributed era by era: 32 of 88 trades sit in eras the model calls **RECORDED but undecidable**,
and the dominant width term names the repair — **20 trades name a MODEL repair** (D1-vs-H4
disagreement, AG's timeframe reconciliation) and 12 are structural, so the majority of the loss is
recoverable **in code, with no new tick capture**. And a two-point boundary discrepancy between
AF's dial bucketiser and the engine's discretizer was found by a test on its first run: latent,
0 of 3,448 trades affected, now pinned.

**`CANDIDATE_FAMILY_V3`: 35 → 39 declared, 32 → 36 looks taken**, written and committed
(`84e39021b`) before a single gate ran. `mx_btcusd @ target_5R` still admits at the raised bar,
consuming 4 of the 51 BH slots and 4 of the 6 Bonferroni slots its headroom had left.

**Nothing was armed, `config/agent_config.yaml` was not read for any live decision, no
broker-capable script was run, and the VPS was never contacted.**

---

## 1. The pinning proof, and the parity that licenses it

AB publishes five dials (`regime_spine/dials.py:124-178`). Four are the substrate's own
coordinates, and `dials.py:97` says so in its own docstring — *"— `substrate_engine`'s
`mtf_align`, by hand."*

| AB dial | `regime_spine` | `substrate_engine` | discretizer |
|---|---|---|---|
| `VOL_REGIME` | `_vol_regime` = `vr_raw` | `compute_state`'s `vr` | `_bucket_vr` |
| `PERSISTENCE` | `_persistence` = `ac60_prim` | `compute_state`'s `ac60` | `_bucket_persist` |
| `TREND_STATE` | `_trend_state` = `slope50` | `compute_state`'s `slope50` | `_bucket_slope` |
| `HORIZON_CONFLICT` | `_horizon_conflict` | `compute_state`'s `mtf_align` | `_MTF_LABEL` |
| `SURFACE_OPEN` | `_surface_open` | — | 1 on any bar a sleeve fired on |

**The identification is measured, not read off the source**, because the two implementations are
not the same code: `primitives.autocorr` uses `statistics.mean` and `substrate_engine._ac` uses
`sum/n`, and AL §8.5 is the case where a two-data-point check asserted a mechanism it could not
resolve. Over all 3,448 trades of the three sleeves:

| | max |Δ| `PERSISTENCE` vs `ac60` | `TREND_STATE` vs `slope50` | `VOL_REGIME` vs `vr` | bucket disagreements | `HORIZON_CONFLICT` vs `mtf_align` |
|---|---:|---:|---:|---:|---:|
| all three sleeves | **0.0** | **0.0** | **0.0** | **0** | **0** |

And the cells, from `substrate.py:69-79`:

```
sub_xvol_pullback   vol=xhi | persist=rand | trend=up | mtf=conflict                   (depth 4)
sub_mid_dn_revert   vol=mid | trend=dn | mtf=neutral | rngpos=mid | comp=norm
                    | persist=revert | session=ny                                      (depth 7)
```

so every AB dial is a firing condition. Measured over each sleeve's own trades:

| sleeve | n | dials pinned | free substrate coordinates |
|---|---:|---:|---|
| `sub_xvol_pullback` | 88 | **5 / 5** | `rngpos`, `comp`, `session` (3 of 7) |
| `sub_mid_dn_revert` | 533 | **5 / 5** | **none** (0 of 7) |
| `asia_pdl_fade` | 2,827 | 1 / 5 | all — it is not a substrate cell |

**Control**: this file's state, recomputed from the archive at each decision bar, reproduces AL's
own recorded `AL_XVOL_REACHABLE_STATE_V1` state on all **88** production trades, max |Δ| **0.0**.
So the pinning is measured on the same state AL's threshold sweep used.

### 1.1 The two boundary points where AF's bucketiser and the engine disagree [B1302]

Found by `test_dial_bucketiser_agrees_with_the_engine_discretizer_except_at_two_points` on its
first run, which asserted plain equality and failed:

| point | engine | `af_repairs.bucket` (AF, AH, AO) | reachable inside a cell? |
|---|---|---|---|
| `ac60 == −0.10` | `revert` (`a <= -0.10`) | `random` (`v < -0.10`) | **yes** — `sub_mid_dn_revert` needs `persist=revert`, which the engine grants at the point |
| `slope50 == 1.5` | `flat` (`s > 1.5`) | `up` (`v >= 1.5`) | no — `sub_xvol_pullback` needs `trend=up`, granted only above 1.5 |

**Measured consequence: zero.** No float lands exactly on either boundary in 3,448 trades, which
is what the `dial_parity` control's 0 disagreements says. It is latent rather than active, and it
is pinned so a future session neither trips over it nor "fixes" AF's committed receipt and
silently moves AF's and AH's published cells.

---

## 2. `sub_xvol_pullback` — item 1

### 2.1 The pre-declaration

Declared in `ao_regime_conditioning.PRE_DECLARED_CELLS` and committed at `84e39021b` before any
gate ran. AH §4.3's discipline: one bucket per mechanism, from what the mechanism IS plus a
production precedent where one exists.

| cell | the mechanism argument | precedent |
|---|---|---|
| `rngpos == mid` | a pullback that is real has come off the high, so `high` is the setup not having happened; one that broke the host trend is `low`. The mechanism wants the middle. | `substrate.py:78` — the sibling `sub_mid_dn_revert` gates `rngpos=mid` |
| `comp == coil` | the trade is a pullback **inside** an expansion, and the pullback is the 5-over-20 true range contracting before the trend resumes. `expand` would be the expansion still running, i.e. nothing to buy. | `substrate.py:78` — the sibling gates the same coordinate at `norm` |

Level directions, also pre-declared: `vr` **+**, `slope50` **+**, `ac60` **+**.

### 2.2 What the pre-declared cells measured

| cell | basis | n of 88 | RECORDED@mid R/day | p_raw | retention | verdict |
|---|---|---:|---:|---:|---:|---|
| ungated @ `target_4R` | control | 85 | +1.3651 | 0.007999 | 0.6516 | REJECT (significance) |
| **`rngpos == mid`** | **declared** | 79 (93 %) | +1.4999 | **0.030197** | 0.7278 | REJECT (significance) |
| **`comp == coil`** | **declared** | **19** | — | — | — | **not gateable** |
| `comp == norm` | enumerated | 52 | +1.6904 | 0.012699 | 0.6925 | REJECT (significance) |
| `rngpos == low` / `high` | enumerated | 0 / 6 | — | — | — | not gateable |
| `comp == expand` | enumerated | 16 | — | — | — | not gateable |

**`rngpos == mid` is free in name only** — 82 of 88 trades at the as-walked labelling — and it
*raises* R/day while *worsening* p, which is AK's warning that the mean and the p must not be
quoted from different cells, arriving inside one cell.

**`comp == coil` misses the gate's floor by one trade**, and that is AF §8 item 2's case exactly
(an `n ≥ 100` floor excluding the mechanistically right bucket by six trades). Published
descriptively rather than silently dropped, because silence in this slot reads as "checked":

| `comp` bucket | n | mean gross R | mean net R (mid, as-walked) |
|---|---:|---:|---:|
| **`coil`** (pre-declared) | 19 | **+1.22987** | **+1.33822** (14 priced) |
| `norm` | 53 | — | gated above |
| `expand` | 16 | +0.82878 | +0.69247 |

So the pre-declared direction — coil beats expand — **holds descriptively and cannot be tested**.
The honest repair is not to lower the floor; it is more trades, and the only source that does not
relax the cell is more RECORDED-era surface (AL measured that relaxing the cell costs more p than
it buys).

### 2.3 The level, which is the finding

On the priced population, net R per trade, with a permutation null beside the normal
approximation:

| axis | declared | ρ | n | p (normal) | p (permutation) | tertile mean net R | sign agrees |
|---|---:|---:|---:|---:|---:|---|---|
| **`vr`** | **+** | **+0.4073** | 78 | 0.0001 | **0.00025** | **0.512 / 1.111 / 2.124** | **yes** |
| `ac60` | + | +0.0409 | 78 | 0.7211 | 0.7189 | 0.667 / **1.810** / 1.231 | yes, vacuously |
| `slope50` | + | −0.0750 | 78 | 0.5123 | 0.5124 | 1.522 / 1.024 / 1.125 | **no** |

**Read `ac60`'s row carefully, because the pair admission rests on it and its ρ is ~0.** The
tertile means are an inverted U with the peak in the middle, and a Spearman is the wrong
instrument for that — the median split works not because the level is monotone but because it
separates the worst tertile (0.667) from the other two. The pre-declaration is *technically*
sign-confirmed and *substantively* refuted as a monotone claim, and the tertile table is what
shows it.

`vr`'s row is the opposite: monotone, in the declared direction, at permutation p 0.00025, with a
4.1× spread from the calmest to the most expanded third of the sleeve's own firing range. **It is
not usable as an admission filter** (§0), and it is exactly what a conviction-weight dial
consumes.

### 2.4 The coverage question, answered from the era ledger

The commission asks why the decidability populations drop the sleeve to n = 56, and whether that
is recoverable. It is not "no data": all 32 lost trades sit in eras the model calls **RECORDED** —
it *did* derive an era ratio from bar history — whose band half-width exceeds the 0.5
decidability threshold. So it is *data that disagrees with itself*, and the era row's own variance
decomposition names which repair:

| population | n of 88 | composition |
|---|---:|---|
| ALL_ERAS | 88 | — |
| RECORDED | 85 | 53 `RECORDED|decidable` + **32 `RECORDED|undecidable`** |
| DECIDABLE | **56** | 53 `RECORDED|decidable` + 2 `SCHEDULE|decidable` + 1 `QUANTIZED|decidable` |

| dominant width term | repair it names | trades |
|---|---|---:|
| `d1_vs_h4_disagreement_log` | **MODEL** — AG's timeframe reconciliation, recoverable in code | **20** |
| `cross_instrument_dispersion_log` | STRUCTURAL — the class disperses; repairable only by a per-symbol era term | 12 |
| `split_half_noise_log` | CAPTURE — more bar history narrows it | 0 |

The same measurement on the other two sleeves: `sub_mid_dn_revert` 28 of 533 (25 MODEL, 3
structural), `asia_pdl_fade` 183 of 2,827 (122 MODEL, 58 structural, 3 CAPTURE). **The majority of
the decidability loss across all three sleeves is a model repair, not a capture requirement** —
which is a more actionable answer than AL's open question and it costs no new tick data.

The other half of the same fact is AL §3.3's unwired hole: an undecidable `RECORDED` era degrades
`Coverage` not at all (`spread_model.py:440-441`), so these 32 trades price as `MEASURED` today.

---

## 3. `asia_pdl_fade` — item 2

The only sleeve in the set whose dials are genuinely free (1 of 5 pinned, and that one is
`SURFACE_OPEN` by construction). 2,827 trades, M15 — and the dials on an M15 series are
M15-horizon quantities, which is stamped on every arm.

### 3.1 The pre-declaration is refuted, in the opposite direction, with confidence

AH's standing pre-declaration for a reversal mechanism (`ah_conditioning.py:93-95`) is
`PERSISTENCE == revert`: *"it is a reversal rule: it needs the exhaustion to revert, not to
trend."* `asia_pdl_fade` is a liquidity-sweep reversal, so the precedent applies directly.

| | declared | ρ | n | p (permutation) | tertile mean net R |
|---|---:|---:|---:|---:|---|
| `PERSISTENCE` | **−** | **+0.0831** | 2,717 | **5e-05** | −0.927 / −0.967 / **−0.712** |

The **most trending** third is the least bad, at permutation p 5e-05 on 2,717 trades. The bucket
gate agrees: `PERSISTENCE == revert` is worse than ungated at every band. **The mechanism reading
that survives is the opposite one** — a prior-day-low sweep in a mean-reverting tape is a real
break, not a stop-run, so the sleeve wants the tape to be *continuing* when it fades. That
inverts AH's precedent for liquidity sweeps specifically, and it should be pre-declared that way
next time rather than inherited.

### 3.2 The enumerated map, with its own bill

22 dial cells at each (band, population). The best at each stamp:

| band | population | best cell | p_raw | Bonferroni within 22 | largest admitting family |
|---|---|---|---:|---:|---:|
| flat | ALL_ERAS | `HORIZON_CONFLICT == aligned` | 0.03470 | 0.7633 | 2 |
| mid | ALL_ERAS | `VOL_REGIME == xhi` | 0.49855 | 1.0000 | 0 |
| mid | RECORDED | `VOL_REGIME == xhi` | 0.40516 | 1.0000 | 0 |
| mid | DECIDABLE | `VOL_REGIME == xhi` | 0.32187 | 1.0000 | 0 |

**At the banded cost there is nothing to condition.** The whole surface is −0.27 to −1.22 R/day.
So the sleeve's blocker is not regime and not exit geometry — it is that AL's exit frontier, the
artifact that made it look 23× away, is a flat-snapshot measurement. §0's table is the finding and
`EXIT_FRONTIER_IS_AT_THE_FLAT_SNAPSHOT_ONLY` is the row.

---

## 4. `sub_mid_dn_revert` — item 4

Its named blocker is `REGIME_GATE_OR_PARK` on both arms, and **it cannot be executed**: the
depth-7 cell pins all six substrate coordinates plus `session`, so there is no free coordinate to
gate on. `PRE_DECLARED_CELLS[MIDDN]` is therefore empty **by declaration**, and that absence is
item 4's answer.

What is left is the level, on AM's re-clocked population:

| arm | band | population | n | R/day | p_raw | drop-best retention | folds+ |
|---|---|---|---:|---:|---:|---:|---:|
| ungated (= AM's headline) | flat | ALL_ERAS | 533 | +0.21049 | **0.019798** | **+0.3609** | 0.80 |
| ungated | mid | ALL_ERAS | 533 | +0.04004 | 0.352365 | **−3.5673** | 0.40 |
| ungated | mid | RECORDED | 325 | +0.12065 | 0.163484 | −0.2704 | 0.60 |
| ungated | mid | DECIDABLE | 493 | +0.01720 | 0.439856 | **−10.4174** | 0.20 |
| **`slope50 < median`** | mid | RECORDED | 162 | **+0.35410** | **0.064094** | **+0.2437** | 0.60 |
| `slope50 < median` | low | RECORDED | 162 | +0.38187 | 0.047795 | +0.3136 | 0.60 |
| `slope50 < median` | high | RECORDED | 162 | +0.30096 | 0.104090 | +0.0727 | 0.60 |
| `ac60 < median` | mid | RECORDED | 158 | +0.14601 | 0.281872 | +0.0283 | 0.80 |
| `vr < 1.0` (mechanism cut) | mid | RECORDED | 166 | +0.14330 | 0.248875 | — | — |

**The commission's target was the robustness gate rather than significance alone, and the
pre-declared direction hits it.** At the banded mid cost on RECORDED the ungated retention is
**−0.2704**; conditioning on the pre-declared `slope50` direction (more oversold is better, for a
sleeve that buys the bounce) restores it to **+0.2437**, and holds positive across the whole band
envelope (+0.3136 low / +0.2437 mid / +0.0727 high). p improves 0.1635 → 0.0641, 2.5×.

**Two honest qualifications.** The cut is the sample median — post-hoc, exactly as in §2 — and
`slope50`'s per-trade ρ is **−0.0062** at permutation p 0.88, so like `ac60` on the other sleeve
this is a day-level effect that the per-trade rank correlation cannot see. **No principled interior
cut exists for this axis**: `trend=dn` is unbounded below on the side the mechanism prefers, so
unlike `sub_xvol_pullback`'s `ac60` there is no published boundary to fall back on. The one
mechanism cut that does exist here — `vr < 1.0`, where ATR equals its own 100-bar mean, the
definitional centre of the pinned `vol=mid` band — gives p 0.2489 and does not help.

At ≤ 5 declared looks the flat-band arm would admit under BH α = 0.10; the declared family is 39.

---

## 5. The power pool — item 3

### 5.1 Two controls, because a pool built from a different artifact proves nothing otherwise

| control | question | result |
|---|---|---|
| **C1** | are AF's and AA's BTC populations the same trades with the same `r_gross`? | **318 / 318 identical to 1e-12**, zero on either side |
| **C2** | does the solo arm reproduce AL's published `mx_btcusd @ target_5R` through this file's pool plumbing? | n **232**, R/day **0.981691**, p **0.0010999** — AL published 232 / +0.98169 / 0.0011 |

C1 matters because the pool has to come from AF's artifact (AA's estate carries only three of the
nine members) while the comparator is AL's, which is AA's. Without it every pool-vs-solo
difference would be partly an artifact difference.

### 5.2 The member basis, on AK §4's rule

Gross and net over the **same** priced rows the gate emitted, at `target_5R` / mid band — AK §4.1's
defect was gross-from-trades against net-from-diagnostics, which are different populations:

| basis | dispersion ratio | members positive | coheres (ratio < 1 **and** all positive) |
|---|---:|---:|---|
| gross | 0.8900 | 8 / 9 | **no** — fails the second clause |
| **net** | **4.0370** | **5 / 9** | **no** — fails both |

AF published 4.74 on gross at its own exit and cost basis; this row is at a different stamp and
the two must not be differenced. What is reproducible is AK §4's **pattern**: the family looks
nearly coherent on gross and is not coherent on net, extended here to a family AK never covered.

### 5.3 Why pooling fails, in the column that measures it

§0's table has the numbers. The mechanism in one line: **trades ×2.56, days ×1.90.** The gate's
null is a block sign-flip on the pooled daily series, so 26 % of the extra sample is a
common-factor calendar duplicate that buys no resolution, while the effect size falls linearly to
0.587×. Blocks go 31 → 50 (√1.61 = 1.27×) against an effect-size loss of 1.70× — so the
t-statistic falls, and p goes 6.1× the wrong way.

**And member selection is worth less than nothing**, measured on a fifth arm the commission did not
ask for: the outcome-**independent** `n ≥ 100` pool reaches p 0.0052 while the
coherent-positive pool that selects on the outcome reaches 0.0062, on 42 fewer trades. AH §4.2's
−0.004525 R/trade, reproduced.

**The band envelope, which is what the commission asked for:**

| arm | low | mid | high |
|---|---|---|---|
| `solo_btc` | **ADMIT** 0.0011 | **ADMIT** 0.0011 | REJECT 0.005099 |
| `pool_all9` | REJECT 0.0063 | REJECT 0.0067 | REJECT 0.0132 |
| `pool_n_ge_100` | REJECT 0.0050 | REJECT 0.0052 | REJECT 0.0099 |
| `pool_coherent_positive` | REJECT 0.0059 | REJECT 0.0062 | REJECT 0.0096 |

No pooled arm admits at any band. **The robustness the solo admission lacks is not available from
breadth.** What is left for that cell is (a) the population rule, which AN owns and which moves
its p by 53×, and (b) more BTCUSD history — the archive starts 2017-08, so this is a capture
requirement with an exact address.

---

## 6. The multiplicity bill, raised and paid before the run

`CANDIDATE_FAMILY_V3.json`: `CANDIDATE_BOOK_V1` **35 → 39** declared, **32 → 36** looks taken.
Written by `ao_family_v3.py`, which imports nothing from either measurement driver, and committed
at **`84e39021b`** — a commit containing no gate result — so "declared before any gate ran" is
checkable in git rather than asserted.

**The rule applied**, and it is AL §6.3's own, extended by one case:

- a **threshold** variant creates a new hypothesis → it joins the family (AL);
- a **regime-conditioning** cell also creates one, because it also moves which trades exist. It
  differs from AL's three in **direction only**: a relaxed threshold fires on a superset of the
  parent's bars, a regime gate on a subset. That asymmetry matters for *fidelity* — a subset is
  covered by the parent's own live recall, so `TRANSFERRED_CLASS` is strictly conservative for it
  — and not for multiplicity;
- a **pool** of nine members judged as one series is neither any member nor the parent → it joins;
- an **exit** cell re-measures an existing hypothesis → it does not (AL, unchanged).

**Price, like for like on each basis** because mixing them is the error AL §6.3 corrected: on
all-declared, rank 1 tightens 0.002857 → **0.002564** and rank 2 0.005714 → **0.005128** (10.3 %);
on looks-taken 0.003125 → 0.002778 (11.1 %). **`mx_btcusd @ target_5R` still admits** at p 0.0011:
AL §8.7 measured its headroom as m ≤ 90 at α 0.10 and m ≤ 45 at α 0.05, so this raise consumes
**4 of 51** remaining BH slots and **4 of 6** remaining Bonferroni slots. Pinned by
`test_ao_candidate_family_v3.py`.

**What is NOT declared, and the price of that choice is printed.** The enumerated dial cells (22
per stamp for `asia_pdl_fade`, 2 for `sub_xvol_pullback`'s free coordinates) and the
derived/mechanism level cells are **not** family members. The rule: a *pre-declared* cell is a
hypothesis this session proposes; an *enumerated* cell is a search over that hypothesis's own
parameter space, priced by a within-enumeration Bonferroni (AH §5.3's instrument) and never
admitted. `REGIME_CONDITIONING_V1.json.enumeration_bills` carries the cell count and
`max_declared_family_that_admits_at_alpha_0.10` for each, and `mechanism_cut_bill` carries the
two-cut-rules-per-axis Bonferroni, so a reader who rejects either split can re-price from the
artifact without re-running anything. AL §3.6 printed the price of its own analogous choice rather
than leaving it implicit; this is the same disclosure.

**Consequence for the pair admission, stated plainly:** it is not in the declaration, so it is not
admissible by this session at any p. That is procedural rather than statistical, and it is the
whole content of a prospective declaration — a cell that could be admitted after the fact would
make `CANDIDATE_FAMILY` decorative.

---

## 7. Artifacts

| file | what |
|---|---|
| `phase10/receipts/REGIME_CONDITIONING_V1.json` | the commissioned deliverable: every (sleeve × exit × cell × band × population) arm, the pinning proof, the dial parity, the level measurements with permutation nulls, the coverage attribution, the one-gate pair composition, the resolution audit, and both bills |
| `phase10/receipts/BTC_POWER_POOL_V1.json` | four member sets × two exits × four bands × three populations, the power accounting (trades vs DAYS), the member two-clause test on both bases, the band envelope, and both controls |
| `phase10/receipts/CANDIDATE_FAMILY_V3.json` | the ratcheted declaration, 39 / 36, with `history`, the price on both bases, and the enumeration split written into it |
| `phase10/receipts/ao_regime_conditioning.py` | driver, with `PRE_DECLARED_CELLS` / `PRE_DECLARED_LEVELS` as source literals |
| `phase10/receipts/ao_btc_power_pool.py` | driver, with `POOL_ARMS` as source literals and the falsifiable prediction in the docstring |
| `phase10/receipts/ao_family_v3.py` | the declaration writer, with its own refusal checks |
| `phase10/receipts/ao_repair_rows.py` | the queue rows, every `evidence` block read from the artifacts |
| `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | **110 → 121 rows**, 11 appended, session `AO`, 0 AO duplicates |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | every look; quote the count as a floor, it grows with each re-run |
| `tests/research_infra/test_ao_regime_dials_inside_substrate_cells.py` | 14 tests — the pinning claim, behaviourally, with no market data |
| `tests/research_infra/test_ao_p_floor_headroom.py` | 7 tests — the floor arithmetic, the conditioning trap, and the gate's silence at 1.048× |
| `tests/research_infra/test_ao_candidate_family_v3.py` | 8 tests — the amendment's content, its price, and that it does not kill AL's admission |

---

## 8. What I got wrong

### 8.1 My first run priced everything at the mid band and did not say so

The band was a constant, not an axis, so my first `asia_pdl_fade` numbers (−0.88 R/day against
AL's −0.069) read as a disagreement with AL rather than as a different cost basis. That is the
exact R0 failure AL §8.8 item 2 recorded against itself, one wave later, in the session that had
read it. The fix is not a caveat: `flat` is now a first-class arm, the three published cells
reproduce to 1e-12 on R/day, p_raw **and** n, and the band travels on every row.

### 8.2 The power-accounting column was `None` on its first run

`row_of` read `gates.significance.n_days`, which does not exist. The day count is at
`telemetry.dependence.n_oos_days` (`gate.py:746-753`). That is AL §8.2's silent-null failure mode
in the one block whose entire subject is the day count — and it was caught only because the print
line showed `days=None`. Now: the key is cited in a comment, `row_of` raises rather than returning
nulls when `dependence` is absent, and the fix brought `n_blocks` and `p_floor_headroom` with it —
which is what found §0's third refutation. **The defect produced the session's best finding, which
is not a defence of the defect.**

### 8.3 My duplicate control refused on other sessions' rows

`ao_repair_rows.py` checked (session, sleeve, prescription) uniqueness over the **whole** queue and
exited non-zero on six pre-existing collisions from AD, AI and AM. Two errors: it would fail on
work that is not mine, and that triple is not a unique key in this ledger by design — AD
legitimately files one prescription for one sleeve at two accounts. Scoped to AO's own rows; the
pre-existing collisions are now reported rather than lost.

### 8.4 I asserted the pinning from source before measuring it

My first reading of `AB_REGIME_DIALS_V1.json` took its `bands` dict at face value and concluded
that `xhi: 2.0` was a cut no implementation honoured. It is not a cut at all — the dict mixes
edges with one representative value for the open-ended top bucket, and reading it as a partition
was the same class of error as AL §8.5. `af_repairs.bucket`'s 1.6 cut is faithful to
`_bucket_vr`. The claim that survives is narrower and true: **2.0 is a boundary AB published and
nothing implements**, which is why `vr >= 2.0` is a weaker post-hoc cut than a median rather than
a defect.

### 8.5 I would have published the pair admission as the headline

My first draft of §0 led with *"the armed sleeve admits at rank 2 and the pair closes."* Three
things kill it and I had only found the first (the post-hoc cut) before the mechanism cut and the
resolution audit were built. The correction is in the numbers rather than a caveat: §0's third
point is now the finding, and it is a gate-level defect rather than a fact about this sleeve.

### 8.6 The scope tool under-reports my blast radius, and it is a glob

`pytest_failset.py scope` resolves import closure and **path literals**. `CANDIDATE_FAMILY_V3.json`
is reached by `test_candidate_family_v2_ratchet.py` through
`AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json")`, which is not a literal, so the tool did not
list it. Added by hand and verified to run; §9 records both the tool's answer and the addition, so
a reader can see the gap rather than trust the tool. This is a defect in the scope tool, not in the
test, and it will bite any session that adds a file a glob-based test discovers.

### 8.7 I described the gate's floor guard wrong, in the gate's favour

My first repair row and the first draft of `test_ao_p_floor_headroom.py` both said
`gate.py:851-857` "refuses only when `p_raw <= p_floor`". It does not: it refuses when
`p_floor >= spec.alpha`. I wrote the sentence from the surrounding code's shape rather than from
the condition, which is the same class of error as AL §8.5 — asserting a mechanism from data that
cannot settle it. The true version is **worse for the gate**, because it means nothing anywhere
relates an observed p to its own resolution, so the correction strengthens the finding rather than
softening it. Corrected in the row, in the test docstring, and in the artifact's
`what_the_gate_actually_checks` field.

### 8.8 My first seed sweep left `mx_btcusd` at the wrong exit and measured the wrong question

The sweep is supposed to ask "does the PAIR admit as a function of the seed", and the pair needs
`mx_btcusd @ target_5R` to hold BH rank 1. My first version left BTC at its as-walked labelling
(p ≈ 0.0064, which cannot hold rank 1), so it was silently asking "does `sub_xvol_pullback` admit
alone" — whose answer is no at every seed — and reported **1 / 20**. The one ADMIT it did report
was BTC's own as-walked p wandering low, not the cell. Caught by reading the per-seed rows rather
than the summary, which is the only reason it was caught at all. At the right population the answer
is **16 / 20**, which is a weaker headline and the true one.

---

## 9. Verification — the §2 scoped receipt

**Full receipt: `phase10/receipts/SESSION_AO_AB.md`.** The short version:

**AO changed nothing under `src/`** — `git diff --name-only 8db17b29c..HEAD -- src/` is empty. So
no production behaviour can have moved and the A/B's only job is to show the artifacts and ledger
appends broke nothing that reads them.

| side | scope | result |
|---|---|---|
| **merge-base `8db17b29c`** (in-worktree, artifacts reverted, restored by copy-back) | the 6 files that exist on both sides | **73 passed / 1 skipped / 0 failed / 0 errored** |
| **HEAD** | the same 6 | **74 passed / 1 skipped / 0 failed / 0 errored** |
| **HEAD** | all 9 in scope | **102 passed / 1 skipped / 0 failed / 0 errored** |
| `pytest_failset.py diff` | mechanical | **unchanged 0, fixed 0, REGRESSED 0 — "No regressions"**, exit 0 |

The **+1** on the shared scope is `test_a_successor_is_a_superset_of_what_it_supersedes`
parametrized over `CANDIDATE_FAMILY_V3.json` — AL's generic ratchet guard working on the first
successor after it, found by its own glob. **+29 new tests** (14 / 8 / 7); 74 + 29 = 103 = 102
passed + 1 skipped.

**One test failed on the first run after the blocks landed, and it was a repair announcing itself.**
`test_the_in_flight_wave_range_is_declared_and_shrinking`: writing B1300–B1343 raised the ceiling
from B1241 to B1343, above AO's own range floor, so AO's `IN_FLIGHT_WAVE_RANGES` entry stopped
exempting anything and the test named the remedy ("Drop it"). Dropped. **And the same append made
AO the owner of that list** per agreement §5 — B1343 is past AN's 1250–1299, so **AN's entry
changed class from PRE-DECLARATION to ACTIVE** rather than going away. Verified with the test's own
predicate: AN's entry now exempts exactly `B1250`, the citation `SESSION_AN_POPULATION_RULE.md`
makes of a block AN has not written; AO's would exempt nothing.

**Scope, and where the tool under-reports it:** `pytest_failset.py scope` listed 6 files.
`test_candidate_family_v2_ratchet.py` reaches `CANDIDATE_FAMILY_V3.json` through
`AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json")`, which is not a path literal, so the tool
cannot see it; `test_candidate_family.py` and `test_fidelity_threshold_variant.py` were added for
the same reason. Three files added by hand, both sides on the same set. §8.6 owns it.

**Safety, all four measured:**

| | |
|---|---|
| bound decision-contract paths changed (H1) | **NONE** of R2's 43 |
| `config/agent_config.yaml` blob | **`eddbe49a…` at the merge-base, at HEAD and in the working tree** — byte-identical three ways |
| broker module imported by any AO receipt | **none** |
| H1 drift check | 2 UNHYDRATED-LFS / 0 DRIFTED — a property of local LFS hydration per `CLAUDE.md` §3 |

**What the receipt cannot record:** both captures carry the same `commit` field and the base one
carries `dirty: true`, because the base side was produced in-worktree (agreement §4 — a fresh
worktree at the merge-base cannot run tests that read the sparse-excluded trial ledger). The
discriminator is the reverted artifacts, which the tool has no field for. The comparison is 0 bad
→ 0 bad on identical scopes. Restore verified: `git status --short` and `git diff --stat HEAD` both
empty afterwards.

---

## 10. What is next, and for whom

**For Borhen — nothing in this session is an owner decision.** No arming, no α, no sizing, no
composition. The one thing worth knowing is that the armed sleeve's best conditioned cell reaches
BH rank 2 and does not survive its own search, so its status is unchanged: REJECT on significance,
highest pooled OOS in the estate wherever it is evaluable.

**For AN, whose lane this touches:** the population rule moves `sub_xvol_pullback` from a p of
0.0080 (RECORDED) to no p at all (DECIDABLE, n 56, NOT_EVALUABLE) — and §2.4 attributes that loss
era by era. **20 of the 32 lost trades name a MODEL repair rather than a capture requirement**, so
the decidability population is partly recoverable in code, which is new input to the rule choice.

**For the next session, in value order:**

1. **The gate's `p_floor_headroom`.** One field on `significance`, a declared threshold, and a
   note naming the mechanism. It would have refused the only ADMIT this session produced, and it
   generalises to every regime-conditioned or exit-conditioned cell in the estate — any repair
   that removes trades removes OOS days and raises the floor. `test_ao_p_floor_headroom.py`
   already pins the arithmetic and names the test that should start failing.
2. **`sub_xvol_pullback`'s vol level, at sizing rather than admission.** ρ +0.4073 at permutation
   p 0.00025, a 4.1× tertile spread, and the consumer already exists
   (`admission.py:920-935`'s conviction multiplier). This is the one form of conditioning the
   sleeve can carry, and it needs no new data and no new family member.
3. **Re-run AL's `asia_pdl_fade` cross at the mid band** before any composition decision quotes
   its frontier. The winner's sign flips.
4. **A prospective declaration of ONE cut on `sub_xvol_pullback`'s `ac60` axis**, if anyone wants
   the pair. Be honest about what is available: a cut chosen because it admitted cannot become
   prospective by being written down later, there is no held-out data (88 trades is the whole
   archive), and the mechanism cut gives p 0.0175. The defensible version of this item is *"declare
   `ac60 ≥ 0` and accept that it rejects"*, which is a smaller claim than the median cell makes and
   the only one the evidence supports.

**Not mine and untouched:** the VPS, arming, tokens, gates, α, sleeve composition, the population
rule (AN's package; Borhen's call), ratifying the family, merging to `main`,
`config/agent_config.yaml`.
