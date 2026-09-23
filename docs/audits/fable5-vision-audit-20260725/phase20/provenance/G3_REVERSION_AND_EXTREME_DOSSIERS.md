# g3 — THE REVERSION AND EXTREME FAMILIES: three dossiers

**Lane g3, wave 20, phase 20. 2026-08-07.**
Owner's commission: *"they came from somewhere tho, they came from a research or an idea …
see for all the candidates from the different sleeves and their life cycles and see what is
wrong there from the sleeve's idea or why are we having the idea."*

Families owned: `range_extreme_reversion` (`src/components/broader_origin_generators.py:682`/`:696`),
`liquidity_sweep_reclaim` (`:713`/`:730`), `structural_distance_extreme` (`:865`/`:883`).

**This lane wrote no production code.** Every economic number below is either a count, a
definition, a ratio, or a *difference between two contracts measured on the identical rows* —
the classes the concurrent instrument repair (bid-series quote side, worth −0.0696 R/fill with a
constant sign) cannot flip. Where an absolute level is quoted it is labelled as such.

Scripts and artifacts: `phase20/provenance/g3_receipts/`.

---

## 0. THE HEADLINE

**The stop is not the defect. The TARGET is, and it is one config key shared by all ten
origin families.**

On 382,356 emissions regenerated from the true-UTC M15 tape over twelve months (24 symbols,
2025-06-01..2026-06-10), deleting the fixed take-profit while changing nothing else is worth,
trade-weighted, with a day-block bootstrap CI95:

| family | 2h | 24h |
|---|---|---|
| `structural_distance_extreme` | **+0.6623** [+0.3953, +0.9756] | **+0.6477** [+0.1349, +1.1504] |
| `liquidity_sweep_reclaim` | **+0.5110** [+0.3059, +0.7127] | **+1.4958** [+0.7927, +2.1450] |
| `range_extreme_reversion` | **+0.2465** [+0.0766, +0.4324] | **+1.4643** [+0.6409, +2.3478] |

bps of price per trade, tested at the 2R take-profit the sealed pool carries. **All six CIs
exclude zero.** The take-profit that costs this is `take_profit_1 = entry ± target_rr · risk`
with `target_rr = _target_rr(config)` (`broader_origin_generators.py:2461-2464`), and
`_target_rr` reads exactly one key: **`risk.min_rr`**. On mainline that key is
`config/agent_config.yaml:39` → `min_rr: 1.5  # vNext sanity floor only; dynamic policy sets
live targets.` In the sealed replay it is overridden to 2.0 by a CLI flag
(`phase19/receipts/pbg/pbg_run.py:89-90`), which is why every pool row carries
`policy_target_r = 2.0` and `tp1/risk = 2.0` exactly (verified on all 1,993
`structural_distance_extreme` rows).

**A risk sanity floor is the take-profit of every broader-origin family.** Its own comment says
it is not supposed to be. There is no per-family target anywhere in the file: one scalar sets the
take-profit for a minutes-scale sweep reclaim, a days-scale regime transition and everything
between.

And the second half, stated in the same breath so nobody reads half of it: **with the target
deleted, all three families are still 1.9–2.7 bps short of the 3.02 bps round-trip toll.**
Best repaired cell in the whole lane is `range_extreme_reversion` stop-only at 24h,
+1.1546 bps [+0.2127, +2.2113], 5/5 quarters positive — and that is 1 cell of 42 and still
**−1.87 bps net**.

**Widening the stop is worth nothing.** The estate already contains the controlled experiment
and nobody had noticed: **76.8 % of every `structural_distance_extreme` emission is a same-side
`range_extreme_reversion` emission on the same bar, same symbol, same instant, same entry —
differing only in a 2.83× stop width.** Paired on those 28,268 rows, with no target:
**+0.0329 bps [−0.3460, +0.4349].** Zero.

---

## 1. `structural_distance_extreme` — the deepest dossier

### 1.1 Origin

**Two births, one day apart.**

**The name** was born 2026-05-26 in commit `d6f09c5a2` *("research: build moonshot dynamic
execution substrate checkpoint")*, in `src/research/universal_candidate_origin_registry.py`, as
one of 16 rows in a **coverage-boxing registry** — not a strategy. Its entire justification, verbatim:

```
name="structural_distance_extreme", category="geometry_topology",
current_gtos_status="passive_feature_or_prompt_context",
boxes_out_if_missing="geometry extremes remain prompt context instead of candidate origins",
next_replay_action="build_structural_distance_origin_generator",
```

The registry's own docstring: *"The list is not a ranking and is not an exhaustive claim about
all possible market science. It is the minimum route-local registry required before Stage05 can
say candidate-origin boxing has been repaired structurally."*
Its summary artifact: `activation_status: research_registry_only_no_runtime_candidate_generation_change`,
`default_off: true`.

**There is no edge claim at the name's birth. There is a coverage argument.**

**The geometry** was born the next day, 2026-05-27, in commit `69d000fb3` *("vnext: activate
moonshot production replacement")* — a 4,000-file commit with a five-word message. `pos50 >= 0.97`,
`stop = bar.high + 0.25 * atr14`, entry at the bar close. **Never changed since.** Only five
commits have ever touched `broader_origin_generators.py`, and the last three are a doc snapshot,
a VPS package and the phase-18 breaker repair.

### 1.2 Premise

*After price closes within 3 % of its own 50-bar high (or low), it reverts.*

That is the classic overextension/mean-reversion premise and it is a documented effect at daily
and weekly scale. **It was not measured here at birth** — the registry offered coverage, not
evidence.

### 1.3 Claimed at birth vs known now — an 18× gap that has never been closed

The same commit shipped a replay:
`research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_2026-05-26.json`.
Verbatim, `family_summary.structural_distance_extreme`:

| field | value |
|---|---|
| `activation_ready_dynamic_metrics.expectancy_r` | **+1.196255130294** |
| `win_rate` | **0.837274173921** |
| `total_r` | **+63,897.97** |
| `performance_rows` | 53,415 |

Engine: `src/research/dynamic_execution_policy.py::simulate_policy`, `selected_dynamic_policy =
be_after_trigger`, path window opened at `entry_first_touch_utc` (`build_..._stage13_...py:360`).

**An 83.7 % win rate on a 2R target with a 3 bps stop.** Nothing in the estate has since come
within an order of magnitude:

| measurement | value | source |
|---|---|---|
| birth claim, 2026-05-26 | **+1.1963 R/trade** | Stage13 summary above |
| wave-19 d1b, market contract, 8 windows | **+0.06639 R/trade** (8/8 windows) | `d1b_RESULT.md` §1 |
| wave-19 d1b, **price units** | **−0.0350 bps** CI [−0.2722, +0.2025] | `d1b_RESULT.md` §4.1 |
| wave-19 pbg, close-only January, net | **−0.59110 R/trade**, 0/21 days | `PARTIAL_BAR_GENERATOR_RESULT.md` §4.4 |
| **this lane**, 12 months, shipped contract, 2h | **−0.2505 bps** [−0.4145, −0.0807], **1/5 quarters** | `a15_final.py` |

**The birth number is 18× the best subsequent measurement and the opposite sign of the shipped
contract.** It has never been retracted, and it is the reason this family was built.

### 1.4 Parameters — every constant, and where it came from

| constant | site | provenance | ever validated OOS |
|---|---|---|---|
| `0.97` / `0.03` (pos50 threshold) | `:866`, `:877` | `69d000fb3`, no artifact, no comment | **never** |
| `50` (lookback) | `_close_position(series, index, 50)` `:864` | same | never |
| **`0.25 * atr14`** (stop buffer) | `:870`, `:888` | same — **and the identical value appears in `liquidity_sweep_reclaim` `:718`/`:735` and `displacement_continuation` `:747`. Copied, not chosen.** | never |
| `target_rr` (take-profit) | `:2461-2464` → `risk.min_rr` | `config/agent_config.yaml:39` = **1.5**, commented *"vNext sanity floor only"* | never as a target |
| ATR definition | `_atr` `:2275-2279` = `mean(high − low)` | **not true range** — ignores gaps | never |

**The stop is not a risk decision; it is a constant, and the entry rule forces it small.**
Measured over all 36,803 emissions in the 12-month archive (`a9_regan.py`):

| | median |
|---|---:|
| total risk distance | **3.046 bps** |
| of which the trigger bar's own wick (`high − close`) | 0.855 bps |
| of which `0.25 × atr14` | **2.082 bps = 71.0 % of the stop** |
| M15 `atr14` itself | 8.329 bps |

`pos50 >= 0.97` means the close sits within 3 % of the 50-bar range top, so `bar.high − bar.close`
is **near zero by construction of the admission rule.** The same `0.25 × atr14` constant produces
a 3.05 bps stop here and a **7.68 bps** stop in `liquidity_sweep_reclaim` (where the wick is
70.2 % of the stop and *is* a real structural level). **Same constant, opposite role: in
`liquidity_sweep_reclaim` it is a buffer on a structure; here it *is* the stop.**

That is the exact answer to *"is a 1.3–2.1 bps stop a strategy or an artifact of how the stop is
derived"* — **it is an artifact**, and the arithmetic is `0.25 × (M15 mean bar range)`.

### 1.5 Geometry vs premise — the separable experiment, run both ways

The commission asked for two experiments. Both were run.

**(a) Hold the idea, vary the stop.** January S0R0 pool, 1,993 emissions, fill-honest, R paths
rescaled by k ∈ [0.5, 32] (`a5_sep2.py`):

| k | stop (bps) | gross **R** | gross **bps** | signal vs side-mirror (bps) |
|---:|---:|---:|---:|---:|
| 0.5 | 1.50 | −0.4158 | −1.234 | −0.414 |
| 1.0 | 3.00 | −0.2732 | −1.775 | −0.573 |
| 4.0 | 12.00 | −0.1008 | −2.582 | −1.326 |
| 12.0 | 36.01 | −0.0317 | −2.159 | −0.563 |
| 32.0 | 96.02 | −0.0107 | −1.028 | +0.245 |

**The R number decays as 1/k and the price number does not move.** R is a fixed price quantity
divided by the stop; a family whose stop is 3 bps gets a 3× flattering R against one whose stop is
9 bps. **`structural_distance_extreme`'s famous 15-window persistence is a denominator effect.**
Independently corroborated by the estate's own `d1b_RESULT.md` §4.1 quintile table: gross R
+0.17168 at a 1.324 bps stop, +0.00473 at 12.769 bps — monotone in 1/d, and the price-unit
direction value is −0.0350 bps.

**(b) Hold the stop, vary the idea.** 21-cell price-space grid, stop 2.5→80 bps × target 5→160 bps,
identical for every family, signal = (real − side-mirror)/2 (`a6_price_grid.py`). For
`structural_distance_extreme`, **20 of 21 cells are negative** and the 21st is +0.021 ± 0.652. At
the common (10 bps stop, 20 bps target) cell it is −0.531 ± 0.207 against `liquidity_sweep_reclaim`'s
−0.060 ± 0.143 and `displacement_continuation`'s −0.804 ± 0.149 — **once every family is given
the same stop, `structural_distance_extreme` is not distinguishable from its siblings.**
(The side-mirror control is valid only for at-market families. The POI families' mirror rows in
that receipt are contaminated by fill asymmetry and must be ignored.)

**(c) The estate's own natural experiment, previously unnoticed.** 76.8 % of
`structural_distance_extreme` emissions are a **same-side** `range_extreme_reversion` emission on
the identical bar — same symbol, same instant, same entry price, same direction — with a 2.83×
wider stop (`a17_paired.py`, n = 28,268):

| horizon | tight stop (3.05 bps) | wide stop (8.26 bps) | **paired difference** |
|---|---:|---:|---:|
| 2h, shipped S1/T2 | −0.1738 [−0.360, +0.014] | +0.0549 [−0.503, +0.596] | +0.2286 [−0.177, +0.650] |
| 2h, **no target** | +0.4001 [+0.017, +0.864] | +0.4331 [−0.248, +1.121] | **+0.0329 [−0.346, +0.435]** |

**Widening the stop 2.83× on the identical setups is worth zero.** The stop width is neither the
edge nor the defect.

**Timescale.** On the January M1 paths (`a3_timing.py`, n = 1,993): **98.1 % resolve at stop or
target inside 2 hours; median time to resolution is 5 minutes; median time to stop is 3 minutes;**
p90 is 32 minutes. **The decision clock is M15.** The median trade lives and dies inside one third
of the bar that generated it. Over 12 months the shipped contract stops out on **80.4 % of trades
within 2 hours** while the target is *also* reached on 68.6 % of them — the outcome is decided by
which of two levels 3 bps and 6 bps away is touched first, inside noise.

*(One hypothesis tested and refuted: intrabar tie-breaks. On M1 running extremes only 0.1 % of
resolutions have stop and target first crossed on the same minute at k=1. The tie rule is not the
mechanism.)*

### 1.6 Life cycle

January S0R0, 1,993 emissions (`a2_lifecycle.py`):

| stage | n | % |
|---|---:|---:|
| emitted | 1,993 | 100 % |
| selector `reject` | 1,915 | **96.1 %** |
| blocked by `cost_authority` | 1,856 | **93.1 %** |
| reached `new_position` | 69 | **3.5 %** |
| entry ever touched | 1,952 | 97.9 % |
| duplicate setup rows | 29 | 1.5 % |
| **already past its own stop at birth** | **0** | **0.0 %** |

**Borhen's "a lot of what we generate is already irrelevant" is false for this family and true
for its neighbour.** `past_stop_rate_by_family` (`E2_COMPOSITION_V1.json`) is **0.0000** for
`structural_distance_extreme` and `liquidity_sweep_reclaim` in all five months, and **0.814 /
0.694 / 0.818 / 0.796** for `current_breaker_re_entry`. The attrition here is one gate — cost —
and the cost gate is right: median `cost_r` **0.6118 R**, the highest of all ten families
(`a1_census.py`), because the cost is a broker constant and the denominator is 3 bps.
`spread_r` alone is 0.3555 R. `E2_LEVER_PRICE_V1.json` ranks it last of ten on real cost, 0.4914 R.

### 1.7 Verdict — GEOMETRY_WRONG, with the ceiling stated

The shipped contract is **significantly value-destroying**: −0.2505 bps/trade [−0.4145, −0.0807],
p(≤0) = 0.998, 1 of 5 quarters positive, over 36,803 emissions and 12 months. Deleting the
take-profit flips it to **+0.4118 bps [+0.0750, +0.7814]**, 4 of 5 quarters positive — a
**+0.6623 bps [+0.3953, +0.9756]** repair on identical rows.

**And the repair does not make it tradeable: +0.41 bps against a 3.02 bps round-trip toll is
7.3× short.** Its persistence across 15 windows is a 1/d artifact, not an idea. Its birth claim
of +1.196 R at an 83.7 % win rate has never been reproduced and should be formally retracted.

**Repair, and what it is worth:** stop shipping a risk floor as a take-profit
(`_target_rr` → `risk.min_rr`). Worth +0.66 bps/trade here and +0.25…+1.50 across the three
families, all CIs excluding zero. It does not open a book. It is worth doing because the same
line governs ten families and any future one.

---

## 2. `liquidity_sweep_reclaim` — the right premise on the wrong clock

### 2.1 Origin

Same commit, same registry, same day: `d6f09c5a2`, 2026-05-26. Verbatim:

```
name="liquidity_sweep_reclaim", category="liquidity_and_stop_cascade",
source_requirements=("M1/M5/M15 OHLC", "swing_high_low_liquidity_levels"),
candidate_clock="event_time_or_bar_close",
current_gtos_status="shadow_or_partial_diagnostic",
boxes_out_if_missing="stop-cascade reversals outside static POIs are invisible",
```

Geometry born 2026-05-27, `69d000fb3`, unchanged since.

**Read `source_requirements` and `candidate_clock` again.** The registry that commissioned this
family specified **M1/M5** data and an **event-time** clock. The generator that was built the next
day reads M15 closes only and fires on `bar_close`. **The implementation dropped the two
requirements its own specification named**, and nothing records the decision.

### 2.2 Premise

*Price runs the prior 20-bar high, fails, and closes back inside the range; the trapped breakout
buyers become fuel for the move down.*

This is a real, widely documented microstructure effect (stop-run / liquidity-grab / failed
breakout). Of the three families here it is the only one whose premise is uncontroversial.

### 2.3 Claimed at birth vs known now

Stage13, same file, `family_summary.liquidity_sweep_reclaim`:
**expectancy +0.20175 R/trade, win rate 39.7 %, total +20,241 R over 100,326 rows.**

Since:

| measurement | value |
|---|---|
| birth claim | **+0.2018 R/trade** |
| wave-19 d1b, market contract, 8 windows | +0.02754 R, **5/8 windows** |
| wave-19 pbg, close-only January, net | **−0.25271 R/trade**, 0/21 days |
| **this lane**, 12 months, shipped contract, 2h | **−0.1973 bps** [−0.5134, +0.1084], **0/5 quarters** |
| **this lane**, 24h | **−0.5795 bps** [−0.9680, −0.1826] |

### 2.4 Parameters

| constant | site | provenance | validated |
|---|---|---|---|
| `20` (sweep lookback) | `_prior_high(series, index, 20)` `:620` | `69d000fb3`, no artifact | never |
| `0.25 * atr14` | `:718`, `:735` | **same value as `structural_distance_extreme` and `displacement_continuation`** | never |
| `target_rr` | `:2461-2464` → `min_rr: 1.5` | risk floor | never |

**One thing is genuinely right here and is worth saying.** Its stop is **not** the constant: the
wick is **5.394 bps of a 7.675 bps stop (70.2 %)** and the constant only **28.3 %**
(`a9_regan.py`). The stop sits above the actual sweep extreme — the structurally correct place.
**This is the only one of the three families whose stop is derived from the setup rather than
from a copied number.**

### 2.5 Geometry vs premise — the mismatch, in minutes

The premise is a **1-to-5-minute event**: a stop run and an immediate reclaim.

| quantity | measured | source |
|---|---|---|
| detector resolution | **15 minutes** (both the sweep and the reclaim must fall inside one M15 bar) | `:713-745` |
| realised time to resolution, median | **25 minutes** | `a3_timing.py`, n=4,475 |
| median time to stop | **19 minutes** | same |
| median time to target | **41 minutes** | same |
| p75 / p90 | **51 / 82 minutes** | same |
| fraction resolving inside 2 h | 76.6 % | same |
| **time stop in the shipped contract** | **none** | family has no `time_stop_bars`; it is not a sleeve |

So: **a premise that resolves in one to five minutes is detected on a fifteen-minute clock,
resolves in twenty-five, and is given a contract with no time limit at all and a 1.5R take-profit
inherited from a risk floor.** The detector is 3–15× coarser than the event it is looking for.
The 15-minute close condition is the load-bearing one: **an M15 bar that sweeps and reclaims is a
different and much rarer object than a minute that sweeps and reclaims**, and the family has only
ever been built, measured or judged as the former. `[UNMEASURED]` — no M1/M5 variant of this
detector exists anywhere in the estate.

**And with the geometry corrected it still delivers nothing.** 14 arms (`a15_final.py`):

| arm | 2h bps/trade | CI95 | qtrs + |
|---|---:|---|:---:|
| shipped S1/T2 | −0.1973 | [−0.5134, +0.1084] | 0/5 |
| S3/T6 | +0.0598 | [−0.4782, +0.6396] | 3/5 |
| S6/T12 | +0.0273 | [−0.6191, +0.6700] | 2/5 |
| **stop-only S1** | **+0.3136** | [−0.0580, +0.6743] | 3/5 |
| naked hold | −0.0825 | [−0.7768, +0.5869] | 1/5 |

At 24 h the target repair is its largest: **+1.4958 bps [+0.7927, +2.1450]**, taking it from
−0.5795 [−0.968, −0.183] to **+0.9163 [+0.2446, +1.6410]**, 4/5 quarters. Still **−2.10 bps**
against the toll, before 24 h of swap.

### 2.6 Life cycle

January S0R0, 4,475 emissions: 81.9 % selector-rejected, **77.4 % by `cost_authority`**,
16.1 % reach `new_position`, 98.5 % entry-touched, **0.0 % born past their own stop**, 0.67 %
duplicates. Median `cost_r` 0.2935 R, `spread_r` 0.1638 R.

### 2.7 Verdict — GEOMETRY_WRONG

The idea is real and its stop is the only structurally-derived stop in this lane. What is wrong
is the **clock and the target**: a minutes-scale premise on a 15-minute close detector with a
1.5R risk-floor take-profit and no time bound.

**Repair, and what it is worth:** (1) delete the fixed take-profit — **+0.51 bps at 2h
[+0.306, +0.713]**, +1.50 bps at 24h; (2) build the detector on M1/M5 as its own founding
registry specified — **unpriced, and it is the one unpriced thing in this dossier worth pricing**,
because every measurement above tests the M15 transcription of the idea and none tests the idea.
Even so the repaired ceiling is 2.1 bps short of the toll, so this is a research question, not a
book.

---

## 3. `range_extreme_reversion` — mined, wired, gated off, and never measured until now

### 3.1 Origin — a real mine, and the only one of the three with statistical support at birth

Not from the 2026-05-26 registry. It was added later, citing
`ULTIMATE_ORIGIN_DISCOVERY_MINE_V2` in its own `source_fields` (`:677`).

**That artifact is not on disk anywhere in this worktree.** It exists only in git, at
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_ORIGIN_DISCOVERY_MINE_V2.json`
(commits `86cccd08d`, `41425481e`), together with `origin_discovery_miner.py`. Recovered and read
in full for this dossier.

The miner's own docstring states the pivot: *"instead of testing hand-designed setups, scan every
M15 bar-close decision point across the 46-symbol year for feature-state cells with significant
forward drift."* Method: day-clustered t across symbol-days, Benjamini-Hochberg Q=0.05 over all
cells, an effect floor of 0.06 ATR net of a per-cell measured spread proxy, then **one**
out-of-time confirmation pass on the pre-registered survivors.

Measured, from the artifact:

| field | value |
|---|---:|
| `bar_observations` | 1,082,287 |
| `cells_tested` | **4,496** |
| `bh_survivors` | 1,823 |
| `effect_floor_survivors` | 974 |
| `confirmed_total_evaluable` | 964 |
| `confirmed_out_of_time_same_sign` | **622 → 64.5 %** |

Of the top-200 confirmations, **166 are conditioned on `pos=high` or `pos=low`** and **all 166
have the reversion-consistent sign** (high → down, low → up). `|t|` runs 8.08 to 21.03; horizons
are 72 at H=4 and 61 at H=8 M15 bars, i.e. **the effect is concentrated at one to two hours**.

**This is a genuine mine and the family's premise is its finding.** Two qualifications the code
comment does not carry: 4,496 cells built from **6 overlapping feature pairs × 4 overlapping
horizons over the same bars**, so the BH correction is applied across cells that are not
independent; and 64.5 % same-sign is measured against a 50 % null with no test attached.

### 3.2 Premise

*A close in the outer quartile of the recent range drifts back toward the middle of it over the
next one to two hours.*

### 3.3 Claimed at birth vs known now

The code comment at `:665-671` is the claim:

> *"close in the outer quartile of the 50-bar range drifts back toward the range with
> +0.7..1.35 ATR net-of-measured-cost over 4-32 bars (day-clustered t 8-14; 64.5 % same-sign
> out-of-time). Reversion geometry: 1.0xATR stop matched to the drift scale; thrust-capped bars
> only (thrust=mid dominated the confirmed cells)."*

Checked against the artifact: `net_effect_atr` over the 166 pos-conditioned confirmations runs
**0.0730 (min) / 0.3935 (median) / 1.3504 (max)**. The comment quotes **"+0.7..1.35"** — the
**top of the distribution presented as its range**. The median confirmed cell is 0.39 ATR, not
0.7–1.35. The `t 8-14` and `64.5 %` figures are exact.

**Known now — and until this lane, "now" was empty.** `range_extreme_reversion` is gated on
`runtime_cfg.get("moonshot_mined_origin_families_enabled", False)` (`:312-314`). **That key
appears in no config file in this repository.** It is absent from every wave-19 family census
(`E2_COMPOSITION_V1.json`, `E5_DECOMPOSITION_V1.json`, `E2_LEVER_PRICE_V1.json` — all ten
families, none of them this one). **It has been in production source for fourteen months and has
never emitted a measured candidate.**

This lane emitted **276,246** of them.

### 3.4 Parameters — three deviations from the evidence it cites

| constant | shipped | the mine's own | consequence, measured |
|---|---|---|---|
| range definition | `_prior_high/_prior_low(…, 50)` — **prior 50 bars, EXCLUDING the current bar** (`:2472-2479`) | `pos = (c − lo48)/(hi48 − lo48)` over `[i−47, i]` — **48 bars, INCLUDING it** (`miner.py:79-80`) | `range_pos` is **unbounded**: min −1.684, max **+3.403**. **9.04 % of emissions fall outside [0,1]** — impossible under the mine's definition. 5.61 % above 1.0 are **breakouts being faded as range extremes.** |
| bucket edges | 0.25 / 0.75 | 0.25 / 0.75 | matches; net side agreement with the mine's own `pos48` bucket is **97.19 %** |
| thrust filter | `bar_range < 1.5 * atr14` | `thrust=mid` ≡ `0.5·atr ≤ rng ≤ 1.5·atr`; `small` (< 0.5) appears in **1 of 166** confirmations | shipped admits `small` too: **10.49 %** of emissions |
| stop | `1.0 * atr14` from the close | **the mine tested no stop at all** — it measured naked forward close-to-close drift | untested geometry |
| target | `min_rr = 1.5` risk floor | **the mine tested no target** | untested geometry |
| horizon | none | confirmations concentrate at **H=4 and H=8 M15 bars (1–2 h)** | untested |

**The stop is 100 % constant** — `1.0 × atr14` from the close, zero structural content
(`a9_regan.py`): median risk 8.458 bps = median atr14 8.458 bps exactly.

**Three definitions of "range position" live in one file.** `_close_position(…, 50)` inclusive
(`structural_distance_extreme`), `_prior_high/_prior_low(…, 50)` exclusive
(`range_extreme_reversion`), and `_RANGE_POS_N = 48` inclusive in the microstructure block
(`:525`, `:561-566`). **Only the third matches the mine that all three cite.**

### 3.5 Geometry vs premise, and the two firing sites

`:682` and `:696` are **one long/short pair**, not two rules — a single `if range_pos <= 0.25` /
`elif range_pos >= 0.75` inside one block, mutually exclusive by construction. **They have never
been measured separately because the family has never been measured.** Measured here, shipped
contract, 2h, trade-weighted (`a16_side.py`):

| leg | n | bps/trade | CI95 | qtrs + |
|---|---:|---:|---|:---:|
| LONG (`range_pos ≤ 0.25`) | 110,941 | **−0.2615** | [−0.8190, +0.2963] | 3/5 |
| SHORT (`range_pos ≥ 0.75`) | 165,305 | **+0.2716** | [−0.1246, +0.6957] | 4/5 |

**The two legs disagree in sign** — which the mine's own confirmations (102 `pos=low` and 64
`pos=high`, all reversion-consistent) did not predict. Neither CI excludes zero.

The two parameter deviations, priced (2h, shipped contract):

| split | n | bps/trade | CI95 |
|---|---:|---:|---|
| `range_pos` inside [0,1] — a real range extreme | 251,272 | +0.0655 | [−0.2720, +0.4158] |
| **outside [0,1] — a breakout being faded** | 24,974 | −0.0239 | [−0.6693, +0.5719] |
| `range/atr` in [0.5, 1.5) — the mine's `thrust=mid` | 247,257 | +0.0236 | [−0.2972, +0.3335] |
| `range/atr` < 0.5 — the mine's `thrust=small` | 28,989 | +0.3462 | [−0.4769, +1.1489] |

Both deviations are **harmless in effect** — they neither create nor destroy anything. That is
itself the finding: the parameters do not match the evidence, and it does not matter, because
there is nothing there to protect.

Full contract sweep (`a15_final.py`), 2h and 24h, trade-weighted, day-block bootstrap:

| arm | 2h | qtrs + | 24h | qtrs + |
|---|---:|:---:|---:|:---:|
| shipped S1/T2 | +0.0575 [−0.268, +0.403] | 3/5 | −0.3098 [−0.795, +0.183] | 1/5 |
| S3/T6 | +0.1406 [−0.434, +0.734] | 4/5 | −0.7804 [−2.484, +0.993] | 1/5 |
| **stop-only S1** | +0.3040 [−0.118, +0.731] | 3/5 | **+1.1546 [+0.213, +2.211]** | **5/5** |
| naked hold | −0.1271 [−0.810, +0.549] | 1/5 | +0.5405 [−3.842, +4.795] | 2/5 |

The 24h stop-only cell is the **best in this whole lane** and is 1 of 42 tested. At the mine's own
1–2 h horizon it is +0.30 [−0.12, +0.73]. Against a 3.02 bps toll it is **−1.87 bps**.

### 3.6 Life cycle

**There is none to trace.** Zero emissions have ever reached a selector, a gate, a fill or an exit
in any campaign-grade window, because the enabling key does not exist. The 276,246 emissions
measured here are synthetic-forward: generated from the tape with the shipped arithmetic and
walked on the same tape. No admission, no fill model, no cost gate was applied — which is why the
comparison above is against the toll rather than net of it.

### 3.7 Verdict — PARAMETERS_WRONG

The idea has real statistical support (its mine is the only genuine discovery artifact behind any
family in this lane). Every constant that turns it into a trade was chosen without validation,
three of them contradict the mine, and the two the mine actually established — a 1–2 hour horizon
and a naked drift measurement — are the two the shipped contract does not implement.

**Repair, and what it is worth:** implement the mine's own predicate (`_close_position(…, 48)`,
which already exists three lines away in the same file), restore `thrust=mid` as a band rather
than a cap, and give it the horizon its evidence has (1–2 h) with no fixed target. Measured
ceiling: **+0.30 bps [−0.12, +0.73]** at 2h, **+1.15 [+0.21, +2.21]** at 24h. Against a 3.02 bps
toll that is a **−1.87 bps** book. **Do not enable it.** The value of the repair is that it
retires a fourteen-month-old unmeasured claim sitting in production source, not that it opens
anything.

---

## 4. What this lane found that is bigger than any one family

1. **`min_rr` is the take-profit of ten families and it is documented as a risk floor.**
   `broader_origin_generators.py:2461-2464` → `config/agent_config.yaml:39` (1.5 on mainline,
   2.0 in the sealed replay via `pbg_run.py:89-90`). Deleting the fixed target is worth
   +0.25…+1.50 bps/trade, six of six CIs excluding zero. **This is the only repair in this lane
   whose sign is established**, and it is one line that governs every broader-origin family
   including any future one.
2. **Three definitions of "range position" in one file, and only the one nobody cites is right.**
   `:864` inclusive-50, `:672` exclusive-prior-50, `:561` inclusive-48. All three families cite
   the same mine; the mine used 48-inclusive.
3. **`0.25 * atr14` is a copied constant appearing in three families**, where it is a 28 %
   buffer on a real level in one and **71 % of the entire stop** in another. A constant that
   plays two different roles in two families was chosen for neither.
4. **`_atr` is `mean(high − low)`, not true range** (`:2275-2279`). Every stop in the file is
   scaled by a volatility estimate that cannot see a gap.
5. **A family can sit in production source for fourteen months, carrying a quantitative claim in
   its own comment, gated by a config key that exists in no config.** Nothing in the estate's
   machinery detects that. `range_extreme_reversion` needs a register entry, not a repair.
6. **The Stage13 birth numbers have never been retracted.** +1.196 R at 83.7 % win rate for
   `structural_distance_extreme` and +0.202 R for `liquidity_sweep_reclaim` are still the only
   evidence any reader of `69d000fb3` would find. They are 18× and 7× the best subsequent
   measurement and the opposite sign of the shipped contract. **They should be struck at source.**
7. **Borhen's "a lot of what we generate is already irrelevant" is precisely true of one family
   and precisely false of these three.** `current_breaker_re_entry` emits 69–82 % of its
   candidates already past their own stop; `structural_distance_extreme` and
   `liquidity_sweep_reclaim` emit **0.0 %**. Their attrition is a single correct gate — cost.

---

## 5. Method, and what would overturn it

- **Population**: whole. 382,356 regenerated emissions over 24 symbols × 12 months; 27,658
  January S0R0 pool rows with M1 paths; 28,268 paired rows. Nothing sampled.
- **Instrument**: bps of price, not R. R divides by the generator's own stop and these stops
  span 3.0 to 44.5 bps across families, so R is not comparable between them and is not comparable
  across stop widths within one.
- **Estimator**: trade-weighted mean with a **day-block bootstrap** (2,000 reps, days resampled
  with replacement). An earlier day-clustered estimator in `a13_contract.py` gave much larger
  numbers for wide-stop arms (`structural_distance_extreme` S6/T12 +3.77 bps, t +2.32) that the
  trade-weighted estimator does not support (+0.15 [−0.60, +0.89], 2/5 quarters). **The
  day-clustered figures in `a13_contract.py`/`a14_oos.py` are superseded by `a15_final.py`** and
  are retained only to show the discrepancy: heavy tails on thin days.
- **A control that was built and then discarded**: a matched within-ISO-week placebo
  (`a12_placebo.py`) shows large positives for all three families at 24 h. **It is invalid for
  range-position-conditioned families by construction** — conditioning on being at the top of a
  range guarantees you are above that week's mean, so forward returns against a random bar in the
  same week are negative by arithmetic. Reported here so nobody rebuilds it.
- **The bid-series correction strengthens the direction of every conclusion.** The estate's
  measured quote-side error is a constant *price* offset (~half a spread, ~0.36 bps). In R it is
  worth 0.12 R against a 3 bps stop and 0.01 R against a 36 bps stop, so it inflates tight-stop
  arms far more than wide ones — the shipped contract is the arm it flatters most, and the shipped
  contract is the one measured negative here.
- **What would overturn this**: an M1/M5 `liquidity_sweep_reclaim` detector built to its own
  founding specification. Every number in §2 tests the M15 transcription of that idea. It is the
  one thing in this lane that is unpriced.
- **Multiplicity, stated plainly**: 42 contract cells × 3 families + 21 grid cells × 10 families +
  an 11-point stop ladder. **Nothing here admits at any honest correction.** Every positive above
  is a lead, and the largest of them is 1.87 bps short of the toll before it is corrected for
  anything.

---

## 6. Receipts

| file | what |
|---|---|
| `g3_receipts/a8_regen.py` | the regeneration (382,356 emissions, ~90 s) |
| `g3_receipts/G3_REGEN_SUMMARY_V1.json` | stop decomposition, side mix, per-symbol counts |
| `g3_receipts/a9_regan.py` | stop decomposition + `range_extreme_reversion` predicate audit |
| `g3_receipts/a15_final.py` | **the definitive table** — trade-weighted, day-block bootstrap |
| `g3_receipts/a16_side.py` | side split, out-of-range leak, **the target's cost** |
| `g3_receipts/a17_paired.py` | the 28,268-row paired stop-width experiment |
| `g3_receipts/a5_sep2.py`, `SEP_V2.json` | the k = 0.5…32 stop ladder (January) |
| `g3_receipts/a6_price_grid.py`, `PRICE_GRID_V1.json` | the 21-cell price-space grid |
| `g3_receipts/a3_timing.py` | realised time-to-resolution, all ten families |
| `g3_receipts/a2_lifecycle.py` | life-cycle census |
| `g3_receipts/a7_drift.py`, `DRIFT_V1.json` | per-minute drift curves |
| `g3_receipts/a13_contract.py`, `a14_oos.py` | **superseded** day-clustered estimator, kept for §5 |
| `g3_receipts/a12_placebo.py` | **invalid** control, kept for §5 |

Raw regenerated rows (97 MB) are held at `/tmp/g3/REGEN_V1.jsonl.gz`, deliberately uncommitted;
`a8_regen.py` rebuilds them from the tape at
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m15_20250601_20260610`.
