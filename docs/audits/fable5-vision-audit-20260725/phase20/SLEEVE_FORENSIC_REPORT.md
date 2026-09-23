# SLEEVE FORENSIC — every generator in GTOS, one dossier each

**Phase 20 synthesis. 2026-08-07.** Commissioned by Borhen: *"we can also add an analysis to
literally every sleeve there on the family that got hit and to understand exactly what was wrong
with the sleeve or maybe the parameters or the configuration or the way it goes… if the idea is
clearly bad, then there must be some reason that we added it in the first place."*

**51 generators. 51 dossiers. Plus 2 shared code paths that every one of them rides.**
Machine-readable: `SLEEVE_FORENSIC_V1.json` (same directory, same numbers, generated from the same
script that generated Sections A–K below).

**Nothing in this document is a recommendation to arm, disarm or resize anything.** Those are yours.
This describes; you decide. No live-forward P&L was read, no VPS was touched, no broker script was
run, no production code was changed by this lane.

---

## 0. THE ANSWER, IN FIVE SENTENCES

1. **The most common defect is the contract, not the idea** — `GEOMETRY_WRONG` is the single largest
   verdict class at **11 of 51**, and with `PARAMETERS_WRONG` the "the idea may be fine, the contract
   is wrong" group is **15 of 51 (29.4 %)**.
2. **And it is almost never the binding constraint.** Of those 11 geometry verdicts, only **2** show
   any measurable directional signal once you strip the contract away, and exactly **1** —
   `asia_pdl_fade` — has a confidence interval that excludes zero. Fixing a contract on a family with
   no signal arrives at a peak made of noise.
3. **What actually orders the economics is information, and the estate has very little of it.**
   Median information ratio: broad-V4 families **0.0034**, sleeves **0.0821** — **24×** — and every
   geometry variable's partial correlation with the outcome collapses to near zero once information
   is in the model.
4. **91.98 % of everything the broad-V4 generator produces is irrelevant before any gate has an
   opinion** — 1,114,008 of 1,211,077 emissions, decidable at the instant of generation without
   seeing one future bar. Borhen's instinct here was not approximately right; it was an
   understatement.
5. **Not one of the 51 has a birth commit that names it, and exactly one has ever cleared the
   standard GTOS now judges by — reversed six days later.** The reason ideas were added is almost
   never recorded, because almost nothing was added on evidence.

---

## 1. THE VERDICT CENSUS

Every generator got one of eight verdicts. Definitions first, because they carry the whole report.

| verdict | means | what you would spend money on |
|---|---|---|
| `IDEA_WRONG` | the market behaviour it claims does not exist, or exists but not here | nothing — retire |
| `PARAMETERS_WRONG` | the idea holds but its constants were never chosen for it | a sweep, on existing data |
| `GEOMETRY_WRONG` | stop / target / horizon do not match the premise's own timescale | a re-label of stored intents, usually free |
| `IMPLEMENTATION_WRONG` | the code does not implement the design that justified it | a port, or a deletion |
| `STALE` | superseded, quarantined, or has never emitted a row | deletion |
| `SOUND_BUT_TOO_SMALL` | the idea and contract are right and the size is not worth the bill | sample, or pooling |
| `SOUND` | nothing to repair | nothing |
| `UNDETERMINED` | the estate cannot currently answer the question | a data fetch |

### 1.1 The census

| verdict | n | share |
|---|---:|---:|
| `SOUND_BUT_TOO_SMALL` | 11 | 21.6 % |
| **`GEOMETRY_WRONG`** | **11** | **21.6 %** |
| `IDEA_WRONG` | 7 | 13.7 % |
| `UNDETERMINED` | 7 | 13.7 % |
| `STALE` | 5 | 9.8 % |
| `PARAMETERS_WRONG` | 4 | 7.8 % |
| `IMPLEMENTATION_WRONG` | 3 | 5.9 % |
| `SOUND` | 3 | 5.9 % |
| **total** | **51** | **100 %** |

Plus both shared-machinery records: `IMPLEMENTATION_WRONG`.

### 1.2 The census by population — this is the part that tells you where to spend

| population | n | SOUND | S_B_T_SMALL | GEOM | PARAM | IDEA | IMPL | STALE | UNDET |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| core W7 — **armed** | 4 | **3** | 1 | | | | | | |
| core W7 — armed & pulled | 2 | | | **2** | | | | | |
| core W7 — never armed | 3 | | 1 | | 1 | 2 | | | |
| core W7 — never measured | 1 | | | | | | | | 1 |
| candidate book — live | 9 | | 1 | 3 | | 2 | | | 3 |
| candidate book — quarantined | 3 | | | | | | | **3** | |
| market-expansion `mx_*` | 14 | | **7** | | | 2 | | 2 | 3 |
| broad-V4 POI frameworks | 3 | | 1 | 1 | | 1 | | | |
| broad-V4 production families | 10 | | | **5** | 3 | | 2 | | |
| sizing-only, no generator | 1 | | | | | | 1 | | |

**Read the first two rows together.** Every `SOUND` verdict in the estate is in the armed book, and
every `GEOMETRY_WRONG` verdict in the core book is a sleeve that was armed and pulled. The estate's
own arming decisions have, so far, sorted correctly — including the two reversals.

**Read the bottom two rows together.** 13 of 13 broad-V4 generators are defective in idea, geometry,
parameters or implementation. Not one is sound. Wave 19 reached that from pooled economics; this
wave reaches it from thirteen independent forensics that never looked at the pool.

---

## 2. BORHEN'S HYPOTHESIS — TESTED PROPERLY

> *"some of the sleeves are more of the quicker ones not waiting for hours and hours for a trade to
> happen from start to finish so maybe that's part of it and the movement and the geometry instead
> of being on the conservative and passive way."*

### 2.1 Why every previous number in the estate could not answer this

Every accumulation curve GTOS owns is measured **through a walker** — stopped at −1R, taken at the
target. So the number at horizon *h* is censored by the very stop and target whose appropriateness is
the question. That is circular. Lane x1 removed the contract entirely:

> **signal(h)** = mean[ side × (close(i₀+h) − close(i₀)) / close(i₀) ] × 10⁴, minus the identical
> quantity on a seeded random side. Anchored at the decision-bar close. Day-block bootstrap over
> decision days. **No stop, no target, no horizon in the measurement.**

Built for all 10 origin families (1,211,077 deduped emissions, 8 windows) and all 30 sleeves with
trades, at 11 horizons from 15 minutes to 320 trading hours. Anchor verified: for all seven
at-market families the roster's own entry price equals the decision-bar close on **100.00 %** of rows.

### 2.2 The decomposition that replaces the argument

Every family's economics factors **exactly** — this is an identity, verified row by row to three
decimals on all 39 rows:

```
RATIO  =  signal(T_res) / toll  =  IR(T_res)  /  ( TIGHT@res  ×  cost_r )
```

| term | what it is | what it measures |
|---|---|---|
| `IR` | information ratio at the family's own realised hold | **the idea** |
| `TIGHT` | stop ÷ σ(T_res) | **the stop geometry** (RATIO ∝ 1/TIGHT, so *lower is better*) |
| `cost_r` | toll ÷ stop | **the cost geometry** — Borhen's mechanism, in its true economic form |

**Medians, broad-V4 vs sleeves:**

| term | broad-V4 | sleeves | direction |
|---|---:|---:|---|
| `IR` — the idea | **0.0034** | **0.0821** | **24× against broad** |
| `cost_r` — cost geometry | 0.2328 | 0.1735 | 1.34× against broad |
| `TIGHT` — stop geometry | 0.2405 | 0.5313 | **2.2× IN FAVOUR of broad** |

**The stop-geometry term is the only one of the three that favours the broad families, and they
still lose by an order of magnitude.** That is a mechanical identity, not a correlation, and it is
why no contract sweep was ever going to save them — wave 19's 282 zero-positive cells now have a
reason.

### 2.3 The half that is right, quantified

Because spread, commission and slippage are fixed in **price** units while R is not, `cost_r`
splits cleanly by contract speed:

| contract speed | n | median `cost_r` | range |
|---|---:|---:|---|
| resolves ≤ 4 h | 15 | **0.339** | 0.123 – 0.877 |
| resolves > 4 h | 24 | **0.126** | 0.046 – 0.315 |

**A quick, tight contract hands the broker 0.339 of one R at the median against 0.126 for a slow
one — a 2.7× handicap that is pure geometry and nothing else.** `liq_asia_up_low_metal` pays
**0.877 R per trade in toll before the trade has an opinion**. Borhen is right about this, it is
worth 3–10× on any sleeve that has information, and it is exactly why widening a stop is the
highest-value lever on `asia_pdl_fade` and worthless on the broad families.

### 2.4 The half that is wrong

Rank-correlating RATIO against each candidate driver (Spearman, two-sided permutation null, 20,000
reps, n = 37–39):

| driver | ρ | p | **partial ρ**, controlling for common-horizon IR |
|---|---:|---:|---:|
| information ratio at a common 24 h horizon | +0.725 | 0.0000 | **+0.446** |
| log₁₀ stop width (bps) | +0.654 | 0.0001 | +0.268 |
| log₁₀ realised resolution time | +0.614 | 0.0002 | +0.164 |
| accumulation exponent β | +0.422 | 0.0095 | +0.265 |
| `TIGHT` | +0.375 | 0.0229 | **+0.014** |
| `SHORT` (hold shorter than drift peak) | −0.297 | 0.0779 | +0.155 |
| **the mismatch as literally stated**, log₂(T_look / T_res) | **−0.130** | **0.4420** | **−0.009** |

Wider stops and longer holds *do* rank with better economics. But **every geometry variable's
partial correlation collapses to near zero once the information ratio is in the model.** The
information term is the ordering; the geometry terms are its shadow.

### 2.5 The two controls that settle it

**Control 1 — a wide stop on a slow clock does not manufacture accumulation.** `idxrev` is H4, its
stop is **73.11 bps = 7.6× the broad family's 9.68**, it passes the cost gate easily, and it has
**5,597 trades** — and its drift ladder is the broad family's shape: +1.5 / +1.5 / +0.4 / −4.4 /
+0.3 / +2.9 bps. Signal ÷ toll at its own hold: **0.28×**.

**Control 2 — a fast, tight, M15 contract can carry real information.** Measured *inside the broad
windows only* (2025-10 … 2026-05, same tape, same instrument, same bootstrap), `asia_pdl_fade` —
M15 clock, 13.3 bps stop, 1-hour hold — reads **t = 1.62 / 2.37 / 2.47 / 2.73 / 1.96 / 1.48 / 2.33 /
2.00 / 1.13** across nine horizons on 770 trades. Across the ten broad families' 110 ladder cells,
**zero reach t = +2.0**; the maximum is +1.64. `current_fvg_fill` has **910× more emissions** than
`asia_pdl_fade` and cannot produce a t above +1.06.

**Fast and tight can carry information. Slow and wide can carry none. Geometry is neither necessary
nor sufficient.**

### 2.6 The same-clock pair, which is the only one that controls for everything

Ten of the eleven natural experiments confound clock with symbol set, era and selection. One does
not: **`session_open_range_break` (broad, M15) vs `orb_crypto_london` (sleeve, M15)** run the same
premise on the same clock, and the sleeve still has **12.2× the information ratio** at a common 24 h
horizon.

### 2.7 The verdict on the hypothesis

> **HALF RIGHT — and the half that is right is the COST term, not the SIGNAL term.**
>
> `GEOMETRY_WRONG` is the most common **diagnosis** (11 of 51) and the rarest **binding** one: of
> those 11, only 2 show measurable signal at the contract-free instrument, and exactly 1 has a
> ceiling interval excluding zero.
>
> The broad families' `SHORT` values are *large* (+2.0 to +6.7) — their drift's argmax genuinely
> sits well past their realised hold, **so the owner's hypothesis looks true for them** — but the
> drift *at that argmax* is itself indistinguishable from zero, so the too-short diagnosis is
> vacuous. **That distinction is the single most important methodological point this wave produced
> and it is not available from any walked curve.**

### 2.8 The ceiling test — the prior question a contract sweep cannot ask

At the horizon where its own drift is largest, does a family's drift exceed its own broker toll?
`signal(h*) − toll(h*)` is an **upper bound** on what *any* same-direction contract at that horizon
can earn per trade.

| population | positive point estimate | **CI excludes zero at any of 11 horizons** |
|---|---:|---:|
| broad-V4 families | 5 of 10 | **0 of 10** |
| sleeves | 22 of 29 | **4 of 29** |

The four: `sub_xvol_pullback` (+691.04 bps [+27.9, +1374.3]), `mx_ethusd` (+250.81 [+16.5, +494.2]),
`mx_btcusd` (+203.17 [+32.6, +397.3]), and **`asia_pdl_fade` (+78.03 [+18.5, +141.4])**. Three were
already known to the estate. **The fourth was not, and it is this wave's single most valuable find.**

*Honest multiplicity: 331 ladder cells + 108 control cells + 21 correlation looks, and h\* is a
per-row maximum, so every net-at-peak interval is optimistic. Nothing here is offered as an
admission.*

---

## 3. THE IRRELEVANT-BY-CONSTRUCTION NUMBER

> Borhen: *"maybe a lot of what we generate is already irrelevant."*

Measured here for the first time as a **union**, so the reasons do not double-count. Whole
population: the eight-window close-only roster, **1,211,077 emissions**, no sampling. Four reasons,
each decidable **at the instant of generation without seeing one future bar**:

| code | reason | why it is irrelevant |
|---|---|---|
| **R1** | `route_session == off_configured_session` | hard-rejected unconditionally, `selector_v4.py:2553-2570` + `agent_config.yaml:816-817` |
| **R2** | limit order already past its own stop at the decision close | the order could not have been placed |
| **R3** | limit order whose reward (rr × risk) is already **behind** the market | the target is behind you before you start |
| **R4** | priced against a bar that closed before the decision instant | stale |

### 3.1 The table

| family | emissions | R1 off-session | R2 past stop | R3 target behind | R4 stale | **UNION** | clean |
|---|---:|---:|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 700,947 | 76.76 % | 0.00 % | **84.28 %** | 6.88 % | **96.80 %** | 22,404 |
| `current_ob_retest` | 270,354 | 65.26 % | 0.13 % | **91.55 %** | 3.89 % | **97.01 %** | 8,097 |
| `current_breaker_re_entry` | 95,051 | 65.62 % | **26.19 %** | 62.32 % | 3.92 % | **95.55 %** | 4,228 |
| `volatility_compression_expansion` | 5,341 | **80.79 %** | 0 | 0 | 1.89 % | **80.79 %** | 1,026 |
| `structural_distance_extreme` | 23,923 | 64.42 % | 0 | 0 | 3.43 % | **64.42 %** | 8,512 |
| `cross_asset_lead_lag` | 21,678 | 62.20 % | 0 | 0 | 4.54 % | **62.68 %** | 8,090 |
| `liquidity_sweep_reclaim` | 43,751 | 59.98 % | 0 | 0 | 2.49 % | **60.09 %** | 17,460 |
| `displacement_continuation` | 39,517 | 54.66 % | 0 | 0 | 2.22 % | **54.93 %** | 17,812 |
| `regime_transition_break` | 2,320 | 46.34 % | 0 | 0 | 0.47 % | **46.34 %** | 1,245 |
| `session_open_range_break` | 8,195 | 0.00 % | 0 | 0 | 0.00 % | **0.00 %** | 8,195 |
| **POOL** | **1,211,077** | **70.93 %** | 2.08 % | 74.11 % | 5.48 % | **91.98 %** | **97,069** |

*Receipt: `provenance/syn_receipts/SYN_IRRELEVANT_V1.json`, script `syn_irrelevant.py`. The R2/R3
columns reproduce lane r2's independent census (`receipts/r2/R2_CENSUS_V1.json`) to four decimals on
all three POI families — two different scripts, same answer.*

### 3.2 What that means

- **91.98 % of the whole pool is waste.** 1,114,008 of 1,211,077. Only **97,069 emissions — 8.02 %**
  — are orders that could have been placed, into a session the gate accepts, with the target still
  in front of the market, priced against a current bar.
- **The single biggest bin is not the exotic one.** `R3 target already behind` is 74.11 % of the
  pool, and it is 88 % of a POI family's own volume. These are limit orders whose 1.5R reward had
  *already happened* before the order was proposed.
- **The second biggest is a calendar lookup.** 70.93 % off-session — a property of the bar's
  timestamp, decidable at generation, and the generator does not check it. Of that, a measurable
  slice is a **one-line naming defect**: `SESSION_WINDOWS['BTCUSD']` and `['ETHUSD']` are
  `(('off_configured_session','00:00','23:59'),)` at `broader_origin_generators.py:94,:100` — a
  24-hour trading window given the exact string the selector uses as its *no-session sentinel*, so
  **every BTCUSD and ETHUSD candidate from every origin family is permanently hard-rejected**
  — **93,332 emissions in this population**, 10.9 % of all off-session rows
  (`syn_receipts/SYN_OFFSESSION_V1.json`). It is a one-line naming defect masquerading as a policy
  and it is not confined to the broad lane; check it against the live path before acting on
  anything else here.
- **One family is 100 % clean and it is instructive.** `session_open_range_break` fires only inside
  its own windows and has no stale rows — its waste is not in the emission, it is in the *window
  definition* (only 15.5 % of exchange-instrument emissions have an opening range that contains
  their own cash open).
- **The R3 repair is already wired and switched off.** `broad_origin_emission_contract.py` carries
  `DEFAULT_MAX_ADMISSION_GAP_R = None` with its own docstring naming the right value. Setting
  `gtos_vnext_runtime.broad_origin_poi_max_admission_gap_r = target_rr` removes the whole bin with
  no new code.
- **Honest caveat, which is lane r2's own:** removing the waste does **not** make the families
  positive. r2 landed the R2 and R4 refusals and the roster went −0.02256 → **−0.00170** R/emission
  (92.5 % of the gross negativity was the waste) — and it is still negative. Do it because ~90 % of
  the estate's candidate volume, and every multiplicity bill computed over that volume, is an
  artifact.

### 3.3 The sleeve side of the same question

For the sleeves, "irrelevant by construction" takes a different form and it is much smaller.
Duplicate-setup rows run **0.0000** on all four armed sleeves (`S1_DISCRIMINATOR_V1.json`,
`lifecycle.duplicate_frac`), against a broad-side identity inflation of roughly **34× for
`current_fvg_fill`** (700,947 emissions → 20,900 distinct POI identities) and **38× for
`current_ob_retest`** (270,354 emissions → 5,296 zones). The sleeve waste is not emission waste —
it is **excursion waste**:

| sleeve | mean MFE reached | realised gross | **capture** |
|---|---:|---:|---:|
| `sub_xvol_pullback` | 2.26 R | 1.268 R | **56.0 %** |
| `energy_agri` | 2.35 R | 0.779 R | 33.1 % |
| `crypto` | 2.02 R | 0.567 R | 28.1 % |
| `sub_mid_dn_revert` | 1.81 R | — | 26.4 % |
| `metals_core` (pulled) | 1.76 R | 0.195 R | **11.1 %** |
| `fx_jpy` (pulled) | 1.57 R | — | **4.4 %** |
| `metals_ob_micro` | 1.53 R | — | **−14.1 %** |

`metals_core` gives back **89 % of everything it reaches**. That is the sleeve-side answer to
"a lot of what we do is already pointless", and it is a different problem with a different repair.

---

## 4. THE KILL LIST

Ordered by how little argument there is. Each row is a deletion or a retirement, with the reason.

| # | generator | verdict | why | what you lose |
|---|---|---|---|---|
| 1 | `ny_index_momentum` | STALE | nine-constant clone of an unresolved sleeve; its own leave-one-out says the book improved without it; **zero rows anywhere, ever** | nothing |
| 2 | `mx_aus200_cash_d1_volume_surge_reversal` | STALE | negative in its own birth ledger after swap; no archive series; no profile mapping — the resolver produces a name on **neither broker** | nothing |
| 3 | `mx_spn35_cash_d1_volume_surge_reversal` | STALE | same four reasons | nothing |
| 4 | `structural_retest` | STALE | a **completed kill**: negative on every split at the daily-unit level, the level that decides a book | lift its 3-cell table into the g1 dossier first |
| 5 | `vol_squeeze` | STALE | never emitted a row; its cited generator does not exist; quarantined 14 months with no redesign | **unless** you ask the cluster question in §6 |
| 6 | `mx_nzdjpy_d1_donchian_20_breakout` | IDEA_WRONG | **0 of 5** folds positive, p 0.9701, on the cohort's longest history and largest sample | it is the control that proves Donchian is a crypto rule |
| 7 | `mx_cadjpy_d1_volume_surge_reversal` | IDEA_WRONG | "volume" on an FX cross is a tick-update count; fails expectancy p 0.89; the fix needs data that does not exist | nothing |
| 8 | `kz_london_crypto_low` | IDEA_WRONG | fails every core gate at its own best cell; 6 of 9 constants are its sibling's; 42.7 % of its trades duplicate `orb_crypto_london` | re-declare as a **cell**, not a sleeve |
| 9 | `liq_asia_up_low_metal` | IDEA_WRONG | 4 of 4 constants inherited; two gates chosen in-sample on 496 trades; **`cost_r` 0.877 — the worst in the estate** | demote to a **flag on its parent** and test on 2,827 rows instead of 157 |
| 10 | `metals_ob_micro` | IDEA_WRONG | capture **−14.1 %**; drift negative at 5 of 6 horizons with the 8 h CI excluding zero *on the negative side*; n=34 | nothing; its own KB already said this |
| 11 | `idxrev` | IDEA_WRONG | MFE/\|MAE\| **0.954 — below one**; 0.28× on 5,597 trades | **keep the row as the estate's negative control** |
| 12 | `current_fvg_fill` (as a standalone family) | IDEA_WRONG | its founding evidence was never about a standalone entry — it is a **feature on the OB retest**, and it reproduces as one at +5.02 pp | 57.9 % of the estate's POI emission volume, which is the point |
| 13 | `volatility_compression_expansion` (M15 instantiation) | GEOMETRY_WRONG | strip the squeeze and expansion clauses, which are measurably value-destroying, and it is a plain 20-bar breakout | nothing — its D1 sibling carries the premise |
| 14 | `structural_distance_extreme` | GEOMETRY_WRONG | resolves at the **median in 5 minutes**; its 21-cell price grid is negative in 20 of 21 | nothing; **strike its STAGE13 birth claim at source** |
| 15 | `session_leadlag_genuine` | IMPLEMENTATION_WRONG | sized at 0.15 confidence and **can never fire** — no importer | either remove it or build the cross-symbol channel |

**Also strike at source, on all ten broad families:** the STAGE13 founding numbers
(`+0.41278 R/trade` pooled; `structural_distance_extreme` at `+1.196255 R/trade` and an 83.7 % win
rate; `liquidity_sweep_reclaim` at `+0.20175`). Wave 19 measured the same machinery at
**−0.29226 R/trade** — a 0.705 R gap and a sign flip. They have never been retracted and they are
still the only evidence a reader of the activating commit would find.

---

## 5. THE KEEP LIST — sound ideas wearing the wrong contract

This is the class the wave was run to find. It has **one confirmed member** and **four candidates**.

### 5.1 CONFIRMED — `asia_pdl_fade`

The only generator outside the armed set whose **contract-free ceiling interval excludes zero**.

| | |
|---|---|
| premise | Asian-session sweep of the prior day's low, then a reclaim — buy it |
| contract | 32 M15 bars (8 h) declared; **realised median hold 4 bars, ~1 h** |
| drift argmax | **320 trading hours** |
| ceiling at h\* | **+78.03 bps [+18.45, +141.44]**, n = 2,761 over 194 days |
| both mechanisms bind | `TOO_SHORT` **and** `TOO_TIGHT` (`cost_r` 0.358) |
| how much cost matters | R/day swings **0.98** across cost bands (−0.0873 flat → −1.0649 high) — nothing else in the estate is close |
| **the defect** | **the stop is an accident of the sweeping bar.** A sweep that barely pierces gives a tiny stop, so *the more cleanly the setup qualifies, the worse its cost-to-risk gets* |
| **the repair** | floor the stop at a fixed ATR multiple — `max(wick + 0.10·ATR, k·ATR)` — sweep k, and **re-label the stored intents.** No generator re-run. No new data. No machine time beyond a walk |

The same "the qualifying condition builds the stop that kills it" pattern was found **independently**
by two other lanes on two other families (`cross_asset_lead_lag`, `structural_distance_extreme`).
It is a design pattern, not three coincidences, and it is the highest-value single repair this wave
identified.

*Second-order, and it matters before any sizing: its corr-cluster is `liquidity_sweep` — **one
cluster for thirty instruments** spanning FX, metals, crypto, energy and indices. As configured it
is a single risk unit that can hold thirty correlated positions.*

### 5.2 CANDIDATES — repairable, unpriced, in priority order

| generator | the mismatch, in the units of the mismatch | the repair | why it is not confirmed |
|---|---|---|---|
| `asian_fade` | docstring says the trade *"needs to ride the return move"*; **95.8 % of 1,319 trades resolve inside the bar they entered on**. The 0.6-ATR stop sits inside one M15 bar of its own noise, so the trail **and** the 12-hour horizon are dead letters | stop ladder at 1.0 / 1.5 / 2.0 ATR on the same entries — a pure re-label through `walkforward.exits.replay` | its claim rests on 2014-2026; the gate sees 2.5 years. **Fetch deep M15 first** |
| `liquidity_sweep_reclaim` | premise is a **1–5 minute** event; detector resolution is **15 minutes** (both legs must fall inside one M15 bar); realised resolution 25 min; and the contract has **no time stop at all** | **build the detector on M1/M5 as its own founding registry specified.** Every measurement so far tests the M15 *transcription* of the idea; none tests the idea | unpriced — and it is the one unpriced thing in the broad estate worth pricing |
| `current_breaker_re_entry` | 26.19 % born already past their own stop; `risk.sl_buffer_breaker_atr_multiplier: 0.5` **exists in config and is read by no code**, so it gets 23.9 % of its specified stop | read the buffer (4.18× wider stop); add an invalidation field to `BreakerBlock` (it has none); set `poi_state_required` | strip the born-past-stop bin and its MFE/MAE is **above** the at-market reference at every horizon (1.033/1.082/1.091/1.111, n=3,433) — but still economically negative at 7.9 bps |
| `regime_transition_break` | its own birth registry **required H1/H4/D1** and it shipped on M15 — 16× to 96× too fast, and the violation is written in the artifact that authorised it | enter one bar later: **+2.2949 bps/trade**, 0.75 of its entire toll, flipping the sign at 3 of 5 horizons, for 15 minutes | best post-repair capture/toll ~1.26× with **no CI excluding zero** — a real repair on a family that remains untradeable |

### 5.3 The four that need only data

| generator | what is missing | cost |
|---|---|---|
| `vp_euidx_pocgrav` | an M1 aux feed — it has **never been walked**, the only live-surface sleeve with unknown hold, excursion, capture and exit mix | `AV_DEEP_H4_INGEST_V1.json` is already the harness; M1 bridge exports exist on this machine |
| `mx_eu50_cash`, `mx_fra40_cash` | D1 series for two FTMO index CFDs. **They carried 22 % of their own book's birth evidence and have zero rows in every modern artifact** | the cheapest possible acquisition |
| `ny_crypto_momentum`, `orb_crypto_london`, `vss_fxcross_london_up_low` | deep M15 history — birth claims rest on ~3× the sample the gate can see | one fetch unblocks all three, plus `asian_fade` and `metal_session_reversion` |
| `mx_avausd` | not data — a **coverage** question: why do 155 of 189 trades fall outside RECORDED eras? | under a session, from `POPULATION_RULE_V1.json`'s own conditions |

### 5.4 The pooling repair — the only structure that has ever cleared a family bill

Three declaration changes, no code, no data, and they attack the constraint that is actually
binding (§7):

1. **`mx_btcusd` + `mx_ethusd` + `vol_compression` → one "crypto D1 channel breakout" member with
   three carriers.** `vol_compression`'s BTC/ETH leg is **100 % contained** in the mx Donchian
   sleeves — the estate counts one hypothesis as **two family members at two confidence weights in
   two corr-clusters**. The two mx members are 4/5 and 5/5 folds positive and `vol_compression` is
   positive at all four cost bands; AF's coherence test exists for exactly this and **has never been
   run on the mx cohort**.
2. **Six index volume-surge sleeves → one member with six carriers.** ~100 trades/year pooled
   instead of six hypotheses with sixteen each.
3. **`ny_crypto_momentum` + `kz_london_crypto_low` + `ny_index_momentum` → one killzone family with
   three cells.** They share **seven identical constants**; only `DECISION_HOUR` and `MAXBARS`
   are genuinely per-cell.

---

## 6. WHAT IS THIN — stated here, not buried

**The measurement instrument was being repaired underneath this wave.** Lane r1 landed a quote-side
walker correction worth −0.1405 R/trade on the sleeve estate, and lane r2 landed three generator
repairs worth +0.02086 R/emission. **No verdict in this report rests on walked stop/target
economics** — the x1 instrument is signed close-to-close drift where both legs come from the same
close series and a constant bid–mid offset cancels; the irrelevant-by-construction table is counts;
the provenance findings are git. That was deliberate. But it means: **do not read any absolute R
figure quoted from a pre-repair artifact as current.**

**Everything below is a real limit on what this report can support.**

| # | limit | consequence |
|---|---|---|
| 1 | **`T_res` is calendar hours; the ladder is printed-bar hours.** For H4/D1 sleeves this evaluates drift slightly further forward than the realised hold | flatters accumulating sleeves in **absolute net level**; cannot move an IR comparison at a common horizon, the era-matched control, or any ordering |
| 2 | **Small n on armed money.** `energy_agri` n=67, `sub_xvol_pullback` n=88, `crypto` n=181, `metals_ob_micro` n=34 | every armed-sleeve interval is wide; the ratios are stable, the levels are not |
| 3 | **The candidate book is gated on 2024-2026 only** while birth claims rest on 2014-2026 | four `UNDETERMINED` verdicts are *not* soft verdicts — they are the honest answer, and the fetch is the fix |
| 4 | **h\* is a per-row maximum**, so every net-at-peak interval is optimistic. 331 ladder cells + 108 control + 21 correlation looks | nothing in §2.8 approaches `CANDIDATE_BOOK_V1` at α 0.10 and nothing is offered as an admission |
| 5 | **The +5.02 pp FVG-as-a-feature result has a coverage bias of unestablished direction** — an FVG enters the test only if it was itself emitted | the direction reproduces at the low end of its founding band and does **not** reach significance here |
| 6 | **`mx_eu50_cash`, `mx_fra40_cash`, `mx_aus200_cash`, `mx_spn35_cash`, `vp_euidx_pocgrav`, `vol_squeeze`, `ny_index_momentum`, `structural_retest`** produce zero rows on any substrate | 8 of 51 dossiers rest on provenance and code reading alone. Each says so |
| 7 | **A matched within-ISO-week placebo is INVALID** for range-position-conditioned families and produces large false positives (+10 to +28 bps at 24 h) | built, refuted and **retained** at `g3_receipts/a12_placebo.py` so nobody rebuilds it |
| 8 | **One lane disagreement, recorded rather than smoothed.** s1 filed `mx_btcusd` as `SOUND`; s2 filed it `SOUND_BUT_TOO_SMALL` | this synthesis takes s2's, because the binding constraint is size and family bill rather than idea or geometry. Both readings are in the JSON |

**One correction to a lane, made here.** g4's dossier states `0.10 × ATR14` *"appears only in
`session_open_range_break`"*. It also appears twice in `regime_transition_break`, at
`broader_origin_generators.py:832` and `:850` (x2). The constant spans **8 modules across both code
lineages**, not one.

---

## 7. WHY WE ADDED THEM — the answer to Borhen's second question

> *"they came from somewhere tho, they came from a research or an idea… then there must be some
> reason that we added it in the first place."*

**The reason is almost never recorded, because almost nothing was added on evidence.**

| finding | measurement |
|---|---|
| generators whose **birth commit message names the idea** | **0 of 51.** All 51 enter git inside one of six bulk commits — the largest is 793 files / +2,726,445 lines, titled `deploy-live: lean branch = origin/main + live system + W7 deploy book + VPS operator bundle`. The three POI frameworks entered the decision surface inside a commit whose entire message is `chore(storage): establish non-iCloud GTOS hot workspace snapshot` |
| generators that have **ever cleared the standard GTOS now judges by** | **1 of 51** (`mx_btcusd`) — **reversed six days later** and disarmed 2026-08-05 |
| generators that clear it **today** | **0** |
| **time from birth to activation** | 7 production origin families: **1 day**. 3 POI frameworks: **1 day**. 9 candidate-book sleeves: **0 days**. 14 `mx_*` sleeves: **born and activated in the same commit** |
| **tuning constants that have ever changed value** | **0 of 24** traced across every commit that ever touched six sleeve modules. The one estate-wide exception is `time_stop_bars` 96 → `time_stop_m15(80,'D1')` — a **unit bug**, not a sweep outcome |
| **provenance citations in production source that resolve to nothing** | **6 of 38.** The worst: `CORRECTED_UNIFIED_BOOK_MC_AUDIT.json`, cited by `candidate_registry.py` as the source of **every confidence weight in the nine-sleeve candidate book** — and it **has never existed in this repository on any ref** |
| **generators ever deleted** | **0.** `git log --all --diff-filter=D -- 'src/components/ultimate_book/sleeves/*.py'` returns nothing in 14 months. Quarantine keeps the code, the registry row **and** the multiplicity cost |

**The founding evidence for all ten broad-V4 families is one uncorrected sweep.**
`VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json`: 90,859 cells
evaluated → 79,288 excluded as negative → 10,269 as insufficient → **1,302 kept, of which the count
with expectancy ≤ 0 is ZERO by construction.** `min_group_rows` 20, one exit policy for all 1,302,
**no out-of-sample split, no family declaration, no multiplicity adjustment.** No production Python
references the allowlist it produced. What runs is the unselected superset.

**And the estate already owned today's standard — on 2026-06-12, and applied it only to the three
families it never enabled.** `origin_discovery_miner.py` specifies TRAIN days only, day-clustered t
so overlapping windows cannot inflate significance, Benjamini-Hochberg Q = 0.05 across all cells
with an effect floor net of a measured spread proxy, and survivors **pre-registered** for a single
out-of-time confirmation — materially the rule ratified six and a half weeks later. The three
families mined under it (`microstructure_absorption_reversal`, `microstructure_vdelta_divergence`,
`range_extreme_reversion`) have emitted **0 candidates in 51,897** and are absent from the
activation list. The seven that *are* activated are the seven from the uncorrected sweep.
**The estate did not lack the method. It lacked the requirement to use it.**

### 7.1 The price of that accumulation, in the only unit that matters

BH step-up on the 32 submitted raw p-values (`phase8/receipts/AI_GATE_AT_DECLARED_FAMILY_V1.json`):

| declared family size | `sub_xvol_pullback` (p 0.006099, **ARMED**) | `mx_btcusd` (p 0.011999) |
|---|---|---|
| m ≤ 16 | **ADMITS** at α 0.10 | **ADMITS** at α 0.10 |
| m ≥ 17 | rejects | rejects |

**The estate declared 32 and now bills 59.** Sixteen surplus generators — each added without an
out-of-sample split, a null and a multiplicity correction — are **arithmetically what stands between
the estate's two best sleeves and its own admission standard.**

**This is not an argument to shrink the family.** `candidate_family.py`'s own docstring forbids that
move: *"under a shrinking family, the cheapest way to admit a candidate is to withdraw its
unsuccessful siblings."* The bill is paid and cannot be un-paid. **The number prices the next
generator** — and the bill grew **84 % in 72 hours** after the ratchet was ratified (32 → 59; the
α = 0.10 rank-1 bar tightened 1.84×, permanently). The estate's *research* activity is now the
dominant term in its *admission* arithmetic, and nothing prices that at the moment a look is taken.

### 7.2 The one process change that would stop this

The machinery exists and is the right shape: `src/research_infra/walkforward/candidate_family.py`
is a ratchet loader pinned by a test. Extend it from a list of **names** to a list of **provenance
rows**, and pin five assertions:

| test | catches |
|---|---|
| T1 completeness over every registry that can size or generate | `session_leadlag_genuine` — the 33rd sleeve nobody counted |
| T2 every cited evidence artifact exists at HEAD | all **6** dangling citations |
| T3 every module constant is declared, and a value identical to a same-named constant elsewhere must declare `copied_from` | all **14** clone constants and both universal ATR buffers. It forbids copying *silently*, not copying |
| T4 every truthy activation key requires `gate_verdict == ADMIT` **or** an explicit `owner_risk_acceptance{by, date, quote}` | the `mx` same-commit, the broad next-day and the candidate same-day activations **all fail it**. It does not block owner-accepted risk — it makes the acceptance structural |
| T5 the ratchet on looks, plus `withdrawn rows have no importable module` | opens the retirement path: the **family row stays** (the look happened), the **code goes** |

---

## 8. HOW TO READ THE PER-FAMILY PAGES

Sections A–K below are one page per generator, generated directly from `SLEEVE_FORENSIC_V1.json`.
Terms used in the numeric blocks:

| term | definition |
|---|---|
| `signal at own hold / toll` | placebo-controlled directional drift at the sleeve's own realised median hold, divided by its own measured broker toll. **The estate's working pre-arming screen, written down for the first time** |
| `IR` | information ratio at the realised hold — **the idea** |
| `TIGHT` | stop ÷ σ(T_res) — **the stop geometry**; RATIO ∝ 1/TIGHT, so lower is better |
| `cost_r` | toll ÷ stop — **the cost geometry** |
| `T_res` / `T_peak` | realised time to resolution / horizon at which drift is largest |
| `ceiling` | drift − toll at `h*`. An **upper bound** on what any same-direction contract at that horizon can earn per trade |
| `capture` | realised gross R ÷ mean MFE reached. How much of what it reaches it keeps |
| `frac_over_live_horizon` | share of trades the declared time stop actually binds on. **0.0000 means the horizon is inert** |

**The screen in one line, because it is the most portable thing here:** the four sleeves trading
Borhen's money read **3.58× – 8.51×**. Everything the estate pulled, disarmed or never armed reads
**−0.32× to 2.49×**. The broad-V4 family reads **0.063×**. A clean gap with nothing straddling it,
reproduced from scratch on evidence unrelated to any of those eleven decisions.

---

## Section A — the armed book (4 sleeves, Borhen's money today)

### `crypto` — **SOUND**

**Premise.** After a strong run, a break of the prior 20-bar high/low on a market whose recent returns are positively autocorrelated keeps going.

**Origin.** 86cccd08d (2026-06-15), 793 files / +2,726,445 lines, 'deploy-live: lean branch = origin/main + live system + W7 deploy book + VPS operator bundle'. All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea (x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).

**Claimed at birth vs known now.** Published +0.751 R/trade. Cost-true OOS is now +0.0775 R — a -90% move in the headline with the direction intact. AE's cost-true lane is the only armed sleeve it would size UP (x1.08).

**Parameters.** Stop 2.00 x ATR14(H4) exactly (k measured 2.00 on 181 walked trades). No tuning constant in this module has ever changed value since its first appearance (x2, 24 of 24 constants across six sleeve modules).

**Geometry vs premise.** MATCHES ITS PREMISE. Premise timescale = ac60 over 60 H4 bars = 240 h. Realised median hold 52 h, p90 320 h; bars-to-MFE 7 H4 = 28 h; MFE/|MAE| 2.035. Drift ladder +5.2/+37.4/+76.8/+282.5/+200.9/+484.8 bps at 4/8/24/72/160/320 h — it accumulates. Signal at its own 52 h hold +196.75 bps against a 54.99 bps toll = 3.58x.

**Life cycle.** 181 walked trades, 0 duplicates, 0 same-bar exits; exits 105 stop / 38 target / 38 maxbars; capture 28.1%. Mean archive spread_r 0.0044 against the live gate's 0.10 — the cheapest sleeve in the book relative to its stop.

| | | | |
|---|---|---|---|
| walked trades | 181 | timeframe | H4 |
| realised median hold | 52.0 h | stop | 376.00 bps = 2.00 x ATR |
| toll | 54.99 bps (cost_r 0.1462) | **signal at own hold / toll** | **3.58x** |
| excursion capture | 28.1 % of mean MFE 2.02 R | exits | {'stop': 105, 'target': 38, 'maxbars': 38} |
| estate decision | ARMED both accounts 2026-07-29/30 | gate | REJECT |
| confidence | 0.85 | corr-cluster | `crypto` |
| **X1 mechanism** | **CONTRACT_OK** | max signed t across the ladder | 2.07 |
| IR at own hold (the idea) | 0.2157 | cost_r (cost geometry) | 0.146 |
| TIGHT = stop/sigma (stop geometry) | 0.322 | RATIO signal/toll | 4.580 |
| realised resolution T_res | 52.00 h | drift argmax T_peak | 72.0 h |
| **ceiling at h\*=72.0 h** | drift 314.59 − toll 71.04 = **243.54 bps** | CI95 | [-36.69, 559.06] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 181 |

**Verdict — SOUND. Repair.** Nothing to repair. Two things to know: (1) plan against the cost-true +0.0775 R, not the published +0.751; (2) its net-vs-horizon curve is still rising at 320 h against a 52 h realised hold, so 'is the book cutting this winner short?' is a pre-registerable question worth ~+18 bps/trade at the 320 h argmax — but the carry model is linear-in-hours and the argmax is inside the CI, so it is a question, not a change. r1's quote-side repair costs it 23.5% of gross (+0.5673 -> +0.4339) on five trades of 181 — the largest single-sleeve move on armed money.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/SESSION_R1_QUOTE_SIDE_WALKER.md`

### `energy_agri` — **SOUND**

**Premise.** Crude oil continuation pays in two near-disjoint states — an extreme volatility expansion or a flat trend — and the FVG-retest entry that works on gold works here too, but the persistence gate that powers gold destroys it.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit. All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea (x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).

**Claimed at birth vs known now.** KB +0.653/+0.911; registry +0.433 TRAIN; survivor book UNCONDITIONAL on both accounts. Its OOS/lifetime split (+0.6226 vs +0.047 R/trade) is the widest in the armed book and is the honest reason its confidence is 0.80 and not 1.00.

**Parameters.** Stop 1.31 x ATR14(H4). slope30 over 30 H4 bars. Never changed since birth.

**Geometry vs premise.** MATCHES ITS PREMISE, BUT THE PUBLISHED FIGURE DESCRIBES A DIFFERENT CONTRACT. Realised median hold 48 h, p90 259 h; bars-to-MFE 11 H4 = 44 h; MFE/|MAE| 2.188. Drift ladder +3.7/+47.7/+168.9/+497.5/+577.6/+368.2 bps — accumulates, peaks 72-160 h. Signal at its 48 h hold +333.21 vs a 54.64 bps toll = 6.10x.

**Life cycle.** 67 walked trades — the thinnest armed sleeve; exits 40 stop / 22 target / 5 maxbars; capture 33.1%. Fixed cost 29.2 bps, the highest in the armed book.

| | | | |
|---|---|---|---|
| walked trades | 67 | timeframe | H4 |
| realised median hold | 48.0 h | stop | 258.15 bps = 1.31 x ATR |
| toll | 54.64 bps (cost_r 0.2117) | **signal at own hold / toll** | **6.10x** |
| excursion capture | 33.1 % of mean MFE 2.35 R | exits | {'stop': 40, 'maxbars': 5, 'target': 22} |
| estate decision | ARMED both accounts 2026-07-29/30 | gate | REJECT |
| confidence | 0.80 | corr-cluster | `energy` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.50 |
| IR at own hold (the idea) | 0.2337 | cost_r (cost geometry) | 0.212 |
| TIGHT = stop/sigma (stop geometry) | 0.310 | RATIO signal/toll | 3.556 |
| realised resolution T_res | 48.00 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 418.95 − toll 114.08 = **304.88 bps** | CI95 | [-297.63, 942.50] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 67 |

**Verdict — SOUND. Repair.** ONE REPAIR, AND IT IS A RESTATEMENT NOT A CODE CHANGE: republish this sleeve's economics at its live partial_be_runner exit instead of the plain exit. It is armed, and every figure the estate carries for it prices a contract the book does not run — worth 0.2302 R/day, measured, at every cost band (AU), corroborating AD 6.2's -0.308 R/day at n=67 through a second instrument. Its argmax at 160 h against a 48 h hold says the same thing from a second direction.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `sub_xvol_pullback` — **SOUND**

**Premise.** In a strong up-regime with elevated volatility, when the short horizon disagrees with the long and persistence is neutral rather than trending, buying the dip with a wide target pays.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit. All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea (x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).

**Claimed at birth vs known now.** Highest per-trade gross R in the survivor book (1.30698 on n=90). Structurally absent from the live path until ultimate_book_include_clean3 was set true on 2026-07-29.

**Parameters.** Stop 1.00 x ATR14(H4) exactly. slope50 (200 h) and ac60 (240 h). Confidence 0.45 in admission.py:218-219 — the reason no confidence FLOOR can express the armed set, since metals_softband at 0.50 would be admitted by any floor low enough.

**Geometry vs premise.** BEST GEOMETRY-TO-PREMISE MATCH IN THE ESTATE. Realised hold 64 h, p90 165 h; bars-to-MFE 16 H4 = 64 h — MFE arrives EXACTLY at the realised hold; MFE/|MAE| 2.563 and capture 56.0%, both the highest in the estate. Drift ladder +53.5/+65.9/+121.9/+266.3/+501.5/+670.8 bps and the 95% day-block bootstrap CI EXCLUDES ZERO AT EVERY HORIZON — the only sleeve for which that is true. Signal at its own hold +242.24 vs a 28.45 bps toll = 8.51x, the highest in the estate.

**Life cycle.** 88 walked trades; exits 47 target / 37 stop / 4 maxbars — the horizon binds on 4.5%. Its ceiling at h*=320 h is +691.04 bps [+27.92,+1374.27]: CI EXCLUDES ZERO.

| | | | |
|---|---|---|---|
| walked trades | 88 | timeframe | H4 |
| realised median hold | 64.0 h | stop | 197.72 bps = 1.00 x ATR |
| toll | 28.45 bps (cost_r 0.1439) | **signal at own hold / toll** | **8.51x** |
| excursion capture | 56.0 % of mean MFE 2.26 R | exits | {'stop': 37, 'target': 47, 'maxbars': 4} |
| estate decision | ARMED both accounts 2026-07-30 | gate | REJECT |
| confidence | 0.45 | corr-cluster | `substrate` |
| **X1 mechanism** | **TOO_SHORT** | max signed t across the ladder | 3.54 |
| IR at own hold (the idea) | 0.4818 | cost_r (cost geometry) | 0.144 |
| TIGHT = stop/sigma (stop geometry) | 0.410 | RATIO signal/toll | 8.178 |
| realised resolution T_res | 64.00 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 781.32 − toll 90.28 = **691.04 bps** | CI95 | [27.92, 1374.27] |
| ceiling verdict | CEILING POSITIVE, CI EXCLUDES 0 | n | 88 |

**Verdict — SOUND. Repair.** NOTHING TO REPAIR, AND TWO THINGS BORHEN MUST SEE — described, not recommended. (1) Its train window is NEGATIVE (-0.190/-0.278 R) while its test window is +1.02/+1.37, on armed money (AU). [INFERENCE, flagged:] the two splits are different objects and the KB documented this shape in 2026-06 ('train EV concentrates in 2020 COVID vol n=25 +1.31; calm train years 2022-24 are thin and slightly negative'), so this lane reads it as documented regime-lumpiness rather than new information. What would SETTLE it is one join nobody has run: label AU's folds by realised volatility regime and check the negative folds are the calm ones. (2) Its frontier cell target_4R REJECTS at all four cost bands (p 0.0080 against a 0.002083 rank-1 bar), is wired default-off, and AU's handoff is 'do not propose it'. Also: at a declared family of m<=16 this sleeve ADMITS at alpha 0.10 (p 0.006099); at m>=17 it does not, and the estate now bills 59.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x2_receipts/X2_PROVENANCE_PATTERN_V1.json`

### `sub_mid_dn_revert` — **SOUND_BUT_TOO_SMALL**

**Premise.** During the New York session, in a mid-volatility downtrend where price sits in the middle of its range, compression is normal and recent returns are mean-reverting, go LONG.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit. All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea (x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).

**Claimed at birth vs known now.** Folded at conf 0.20 on the estate's own MC ('mild stress drag -> keep at breadth conf 0.20, not higher'). AE's cost-true lane later demoted it from SIZE_UP x1.23 to HOLD_FLAG on a -0.0183 R OOS mean over 282 trades.

**Parameters.** Stop 1.00 x ATR14(H4) exactly — 44.07 bps, the second-narrowest in the armed book and only 4.5x the broad V4 family's 9.68, which is why it is the sleeve that proves stop WIDTH is not the discriminator.

**Geometry vs premise.** MATCHES, AND IT IS THE CHEAPEST CARRY IN THE BOOK. Realised hold 28 h, p90 99 h; bars-to-MFE 5 H4 = 20 h; MFE/|MAE| 1.702. Drift ladder +1.9/+9.6/+26.9/+63.0/+71.0/+72.2 bps, CI excludes zero from 8 h onward. Carry 0.068 bps/h, by far the cheapest. Signal at its own 28 h hold +29.95 vs a 6.33 bps toll = 4.73x.

**Life cycle.** 533 walked trades; exits 336 stop / 197 target / ZERO maxbars — the horizon never binds.

| | | | |
|---|---|---|---|
| walked trades | 533 | timeframe | H4 |
| realised median hold | 28.0 h | stop | 44.07 bps = 1.00 x ATR |
| toll | 6.33 bps (cost_r 0.1437) | **signal at own hold / toll** | **4.73x** |
| excursion capture | 26.4 % of mean MFE 1.81 R | exits | {'target': 197, 'stop': 336} |
| estate decision | ARMED both accounts 2026-07-30 | gate | REJECT |
| confidence | 0.20 | corr-cluster | `substrate` |
| **X1 mechanism** | **TOO_SHORT** | max signed t across the ladder | 2.96 |
| IR at own hold (the idea) | 0.2146 | cost_r (cost geometry) | 0.144 |
| TIGHT = stop/sigma (stop geometry) | 0.368 | RATIO signal/toll | 4.064 |
| realised resolution T_res | 28.00 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 89.49 − toll 26.14 = **63.35 bps** | CI95 | [-2.10, 146.61] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 526 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** NOT A REPAIR — A CALIBRATION NOTE. Its ratio (4.73x) is healthy but its absolute numbers are an order of magnitude below the rest of the armed book (+29.95 bps at hold against +196 to +333), which is exactly what conf 0.20 encodes. Two live facts: (1) the ratio and AE's cost-true mean disagree in SIGN and neither should be quoted without its population stamp (SLEEVE_DOSSIER_V1 rule R0); (2) its exit frontier on the RE-CLOCKED population moves from -0.106 R/day with expectancy FAILING to +0.092/+0.059/+0.008 with it PASSING, best cell time_stop_20 -> time_stop_40, so every pre-2026-07-30 figure for this sleeve is on the wrong clock.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json`


## Section B — armed and pulled (2 sleeves)

### `fx_jpy` — **GEOMETRY_WRONG**

**Premise.** JPY crosses show genuine intraday directional persistence off the London open that an H4 grid cannot see, because the whole move is inside one H4 bar: take the sign of the first London hour and ride it.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit. All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea (x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).

**Claimed at birth vs known now.** Confidence 0.15, honestly labelled. Session N measured that the broker charged swap on ZERO of its 32 live positions.

**Parameters.** Stop 0.99 x ATR14(M15) = 5.68 bps — SMALLER THAN THE BROAD V4 FAMILY'S 9.68 bps. config/agent_config.yaml:717-729 raises the spread ceiling to 0.35/0.45 FOR THIS SLEEVE BY NAME, stating in its own words that the ordinary GBPJPY spread 'is ~22% of that stop, which the global 0.10 spread / 0.15 total-cost gate CORRECTLY REFUSES'.

**Geometry vs premise.** THE GEOMETRY IS THE WHOLE FAILURE AND THE BOOK'S OWN GATE SAID SO BEFORE ANY OF THIS. Premise timescale is one session hour. Realised hold 0.8 h, p90 2.0 h; bars-to-MFE 2 M15 = 30 min; capture 4.4%. Drift at its own hold is -0.23 bps against a 1.33 bps toll = -0.17x. Ladder flat: -0.2/+0.0/+1.9/+1.3/+8.9/+9.2 bps — THE BROAD FAMILY'S SHAPE. The +9.2 bps at 320 h is real but UNREACHABLE under its own contract (a 2.5R target on a 5.7 bps stop is 14 bps of price; the time stop is 12 h).

**Life cycle.** 3,984 walked trades. Armed 2026-07-30 ~11:52, PULLED ~14:57 the same day on AV's evidence. Mean archive spread_r 0.1132 against the global 0.10 gate.

| | | | |
|---|---|---|---|
| walked trades | 3984 | timeframe | M15 |
| realised median hold | 0.8 h | stop | 5.68 bps = 0.99 x ATR |
| toll | 1.33 bps (cost_r 0.2338) | **signal at own hold / toll** | **-0.17x** |
| excursion capture | 4.4 % of mean MFE 1.57 R | exits | {'stop': 2766, 'target': 1212, 'maxbars': 6} |
| estate decision | ARMED 2026-07-30 ~11:52, PULLED ~14:57 same day (AV evidence) | gate | REJECT |
| confidence | 0.15 | corr-cluster | `jpy` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | -0.02 |
| IR at own hold (the idea) | 0.0178 | cost_r (cost geometry) | 0.234 |
| TIGHT = stop/sigma (stop geometry) | 0.418 | RATIO signal/toll | 0.182 |
| realised resolution T_res | 0.75 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 2.50 − toll 1.47 = **1.03 bps** | CI95 | [-9.22, 11.59] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 3942 |

**Verdict — GEOMETRY_WRONG. Repair.** THE PREMISE MAY WELL BE REAL AND THE CONTRACT CANNOT EXPRESS IT. At a 5.7 bps stop on a JPY cross the spread is 11-22% of R, so the sleeve is transacting inside its own noise the way the broad V4 family does — it is the estate's closest thing to a broad-V4-shaped sleeve on every axis (sub-10 bps stop, M15 clock, sub-hour hold, flat accumulation, spread comparable to R), and it failed in the same units and for the same reason. THAT IS THE STRONGEST SINGLE PIECE OF EVIDENCE THAT WAVE 19'S VERDICT IS ABOUT A CONTRACT CLASS AND NOT ABOUT ONE GENERATOR. A repair would have to give the idea a risk distance large enough that the spread is <10% of it — on a JPY cross at M15 that is a multi-ATR stop and therefore a different, unmeasured contract; or move it to a clock where ATR is 4.5x larger, which is a re-derivation. Its named repair (the meta-label filter) is measured EMPTY.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; config/agent_config.yaml:717-729`

### `metals_core` — **GEOMETRY_WRONG**

**Premise.** After a volatility expansion, when precious-metal returns are positively autocorrelated, price that retraces into the FVG left by an impulse and closes back in the higher-timeframe trend direction continues.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit. Its 0.25 x ATR floor and 0.10 x ATR buffer (metals.py:33-34) are the two universal copied constants, shared with 7 and 8 modules respectively across BOTH code lineages (x2).

**Claimed at birth vs known now.** Armed at confidence 1.00 — the highest in the estate — on a forward mean over n=49 metals trades in a single strong trend-persistence year. Its own KB says the companion OB variant's forward positive 'is carried by 2025, 2026 has only n=2 and is negative'.

**Parameters.** Stop 1.10 x ATR14(H4) = 105.03 bps. Mean archive spread_r 0.1247 against the live pre-trade gate's 0.10 (book_owner._spread_cost_screen :4685-4722; config/agent_config.yaml:715) — it sits AT the book's own refusal line.

**Geometry vs premise.** FOUR THINGS WERE WRONG. (1) The stop is at the book's own refusal line. (2) The exit keeps almost nothing: mean MFE 1.758 R, realised +0.195 R gross = 11.1% capture, the worst of any H4 sleeve. (3) IT DOES NOT ACCUMULATE: drift ladder -4.5/+1.8/+27.4/+17.4/+23.0/+75.8 bps, CI excluding zero at 24 h ONLY; net-of-cost is +4.5 bps at 24 h and NEGATIVE at every other horizon, argmax 24 h against a 36 h realised hold. (4) Signal at its own hold +24.92 vs a 27.22 bps toll = 0.92x — below one, on the sleeve that carried confidence 1.00.

**Life cycle.** 385 walked trades; capture 11.1%. Armed 2026-07-29 12:55, PULLED 14:25. AE's cost-true lane later landed on the same side (DOWN_WEIGHT x0.50 on a 232-trade/118-day OOS at -0.205 R).

| | | | |
|---|---|---|---|
| walked trades | 385 | timeframe | H4 |
| realised median hold | 36.0 h | stop | 105.03 bps = 1.10 x ATR |
| toll | 27.22 bps (cost_r 0.2592) | **signal at own hold / toll** | **0.92x** |
| excursion capture | 11.1 % of mean MFE 1.76 R | exits | {'maxbars': 36, 'stop': 262, 'target': 87} |
| estate decision | PULLED 2026-07-29 14:25 (armed 12:55, pulled 90 min later) | gate | REJECT |
| confidence | 1.00 | corr-cluster | `metals` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.84 |
| IR at own hold (the idea) | 0.0990 | cost_r (cost geometry) | 0.259 |
| TIGHT = stop/sigma (stop geometry) | 0.541 | RATIO signal/toll | 0.706 |
| realised resolution T_res | 36.00 h | drift argmax T_peak | 24.0 h |
| **ceiling at h\*=24.0 h** | drift 18.92 − toll 22.92 = **-4.00 bps** | CI95 | [-24.05, 16.31] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 385 |

**Verdict — GEOMETRY_WRONG. Repair.** THE IDEA IS NOT WRONG AND THE LESSON IS NOT 'DISTRUST METALS'. The FVG-retest premise is the SAME premise energy_agri runs with a different state gate, and energy_agri measures 6.10x. Four things were wrong with the JUSTIFICATION and every one is a population or geometry problem: (a) n=49 in one year; (b) the cost model charged ZERO commission (F38) and credited tick erosion with the WRONG SIGN (F39); (c) its spread sits at the refusal line so a cost error of the size the estate actually had was enough to flip it; (d) it gives back 89% of what it reaches. REPAIR: an exit that keeps more of a 1.758 R excursion is worth up to 8x its current realised R and is the only lever large enough to matter; widening the stop would clear the gate but the drift ladder says there is nothing at 72 h+ to hold for. GENERALISABLE LESSON: confidence 1.00 was assigned on a per-trade forward mean, and the two things that killed it — cost-model direction and excursion capture — are invisible in a per-trade mean by construction.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`


## Section C — core W7, never armed (3 sleeves)

### `idxrev` — **IDEA_WRONG**

**Premise.** A failed breakout of the recent index range reverts: when a bar takes out the 16-bar high but closes back inside it, fade it.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit.

**Claimed at birth vs known now.** DEAD_BEFORE_COST on both accounts in SURVIVOR_BOOK_V1 — one of only two sleeves the estate had already written off before charging a broker cost.

**Parameters.** Stop 1.50 x ATR14(H4) = 73.11 bps; target 0.75R.

**Geometry vs premise.** THIS IS THE MEASUREMENT THAT ANSWERS BORHEN'S QUESTION. It is H4, its stop is 7.6x the broad V4 family's 9.68 bps, and its drift ladder is THE BROAD FAMILY'S SHAPE: +1.5/+1.5/+0.4/-4.4/+0.3/+2.9 bps. A wide stop on a slow clock does not manufacture accumulation. MFE/|MAE| 0.954 — BELOW ONE, the signature of a fade with a 0.75R target: it never gets ahead. Capture -0.4%. Signal at its own 16 h hold +0.94 against a 3.34 bps toll = 0.28x.

**Life cycle.** 5,597 walked trades — by far the largest sample in the core book, so none of this is small-n. Ceiling NEGATIVE at every horizon.

| | | | |
|---|---|---|---|
| walked trades | 5597 | timeframe | H4 |
| realised median hold | 16.0 h | stop | 73.11 bps = 1.50 x ATR |
| toll | 3.34 bps (cost_r 0.0456) | **signal at own hold / toll** | **0.28x** |
| excursion capture | -0.4 % of mean MFE 0.76 R | exits | {'target': 3188, 'stop': 2409} |
| estate decision | never armed; DEAD_BEFORE_COST both accounts | gate | REJECT |
| confidence | 0.15 | corr-cluster | `index` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.94 |
| IR at own hold (the idea) | 0.0207 | cost_r (cost geometry) | 0.046 |
| TIGHT = stop/sigma (stop geometry) | 0.851 | RATIO signal/toll | 0.532 |
| realised resolution T_res | 16.00 h | drift argmax T_peak | 11.0 h |
| **ceiling at h\*=8.0 h** | drift 1.23 − toll 2.75 = **-1.52 bps** | CI95 | [-4.35, 1.33] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 5597 |

**Verdict — IDEA_WRONG. Repair.** NO REPAIR, AND ITS VALUE TO THE ESTATE IS AS A CONTROL RATHER THAN AS A SLEEVE. It is the cleanest available refutation of 'the armed sleeves work because their stops are wide': same H4 clock as the armed four, a stop 7.6x the broad family's, a cost gate it passes easily, 5,597 trades, and a drift curve indistinguishable from the broad family's flat 0.19 bps. KEEP IT IN EVERY FUTURE COMPARISON as the negative control; the estate has been short of one.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `metals_ob_micro` — **IDEA_WRONG**

**Premise.** The same continuation edge as the FVG retest, expressed on a different structure — an order block instead of a fair-value gap — restricted to the strong-persistence tail (ac60 >= 0.20) and deduplicated against the FVG entries.

**Origin.** 86cccd08d (2026-06-15). Shares ATR_STOP_FLOOR 0.25 and STOP_BUF 0.10 with metals.py and structural_retest.py (x2's metals triplet).

**Claimed at birth vs known now.** Its own KB honesty section already said this: the forward positive is one year, n=2 in the following year, and the sleeve was kept explicitly under map-don't-kill rather than on its evidence. Confidence 0.30, default-off.

**Parameters.** Stop 1.13 x ATR14(H4).

**Geometry vs premise.** Realised hold 42 h, p90 320 h; MFE/|MAE| 1.300; capture -14.1% — IT GIVES BACK MORE THAN IT REACHES. Drift ladder -10.2/-36.0/-32.3/+27.2/-39.1/-61.2 bps — negative at five of six horizons, and the 8 h cell's CI EXCLUDES ZERO ON THE NEGATIVE SIDE. Signal at its own hold -9.96 against a 31.42 bps toll = -0.32x, the worst reading in the estate.

**Life cycle.** 34 walked trades over the whole archive — the honest limit on all of it. Mean archive spread_r 0.1107, over the live 0.10 gate.

| | | | |
|---|---|---|---|
| walked trades | 34 | timeframe | H4 |
| realised median hold | 42.0 h | stop | 99.88 bps = 1.13 x ATR |
| toll | 31.42 bps (cost_r 0.3145) | **signal at own hold / toll** | **-0.32x** |
| excursion capture | -14.1 % of mean MFE 1.53 R | exits | {'stop': 26, 'maxbars': 3, 'target': 5} |
| estate decision | never armed; conf 0.30 | gate | REJECT |
| confidence | 0.30 | corr-cluster | `metals` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.64 |
| IR at own hold (the idea) | 0.0313 | cost_r (cost geometry) | 0.315 |
| TIGHT = stop/sigma (stop geometry) | 0.635 | RATIO signal/toll | 0.157 |
| realised resolution T_res | 42.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=4.0 h** | drift 8.31 − toll 13.98 = **-5.67 bps** | CI95 | [-32.22, 27.66] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 34 |

**Verdict — IDEA_WRONG. Repair.** NOT REPAIRABLE AT THIS SIZE AND PROBABLY NOT WORTH REPAIRING. It contributes -0.7% of the book's conf-weighted edge, its capture is negative, and n=34 means no repair can be evaluated. Leave at conf 0.30 default-off or retire under the cleanup policy. NOTE that its premise — 'the SAME edge expressed on a different structure' — is exactly the claim the g1 lane refuted independently for current_ob_retest in the broad family: an order-block retest at an emitted age of days rather than hours is a cohort the founding study has almost no data on and what data exists says is far worse.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_THREE_POI_FAMILIES_DOSSIER.md`

### `metals_softband` — **PARAMETERS_WRONG**

**Premise.** The same FVG-retest continuation as metals_core, but harvesting the persistence band the hard gate rejects (0.04 <= ac60 < 0.10), sized down by a ramp on ac and vr.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit.

**Claimed at birth vs known now.** No independent evidence: the band is DEFINED by what metals_core rejects. Confidence 0.50.

**Parameters.** Five size-ramp constants inherited whole, never swept. Stop 1.16 x ATR14(H4). The KB's own evidence for the ac60 gate is that EV is MONOTONE in the threshold — so a band strictly BELOW the validated threshold is, by the same evidence, the weakest part of the distribution.

**Geometry vs premise.** Realised hold 44 h, p90 320 h; MFE/|MAE| 1.929; capture 25.3%. Drift ladder +13.5/+9.6/+20.0/+20.3/+8.6/+64.2 bps — no monotone shape and no CI excluding zero at any horizon. Net-of-cost NEGATIVE at every horizon, argmax at 1 h. Signal at its own hold +20.15 against a 40.04 bps toll = 0.50x.

**Life cycle.** 237 walked trades. Mean archive spread_r 0.1083, over the live 0.10 gate.

| | | | |
|---|---|---|---|
| walked trades | 237 | timeframe | H4 |
| realised median hold | 44.0 h | stop | 134.76 bps = 1.16 x ATR |
| toll | 40.04 bps (cost_r 0.2971) | **signal at own hold / toll** | **0.50x** |
| excursion capture | 25.3 % of mean MFE 1.87 R | exits | {'stop': 140, 'maxbars': 26, 'target': 71} |
| estate decision | never armed; CARRY_CONDITIONAL both accounts | gate | REJECT |
| confidence | 0.50 | corr-cluster | `metals` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.52 |
| IR at own hold (the idea) | 0.0841 | cost_r (cost geometry) | 0.297 |
| TIGHT = stop/sigma (stop geometry) | 0.489 | RATIO signal/toll | 0.579 |
| realised resolution T_res | 44.00 h | drift argmax T_peak | 16.0 h |
| **ceiling at h\*=16.0 h** | drift 23.07 − toll 24.79 = **-1.72 bps** | CI95 | [-44.20, 50.82] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 237 |

**Verdict — PARAMETERS_WRONG. Repair.** IT IS A RESIDUE, NOT A HYPOTHESIS. What would have to change: derive the band from its own forward evidence rather than from metals_core's complement, and sweep the five ramp constants that were inherited whole. What it would be worth: at 1.7% of the book's conf-weighted edge and a 0.50x ratio, essentially nothing — which is the honest reason to leave it alone rather than repair it. Its confidence of 0.50 is also the reason no confidence FLOOR can express the armed set.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json`

### `fx_jpy_ny` — **SOUND_BUT_TOO_SMALL**

**Premise.** The same session-open momentum ride as fx_jpy but at the New York open, with two extra gates: the opening impulse must be at least 1.0 ATR and it must agree with the 20-bar M15 trend.

**Origin.** 86cccd08d (2026-06-15), the same bulk commit.

**Claimed at birth vs known now.** Honestly labelled forward_only at conf 0.15 and never claimed more — nothing was over-sold. CARRY_CONDITIONAL_LIVE_SUPPORTED on both accounts.

**Parameters.** Stop 0.99 x ATR14(M15) = 7.63 bps. Its two extra gates (1.0-ATR impulse, 20-bar trend agreement) have NEVER been ablated, so it is not established that they do anything.

**Geometry vs premise.** Realised hold 0.8 h, p90 2.5 h; bars-to-MFE 2 M15 = 30 min; MFE/|MAE| 1.214; capture 3.4%. Drift ladder +0.0/+0.4/-1.2/-3.4/-2.6/+0.9 bps — flat and sign-unstable. Signal at its own hold +0.00 against a 1.32 bps toll = 0.00x: the sleeve is exactly a coin flip minus the spread.

**Life cycle.** 1,620 walked trades. Archive spread_r 0.0729 passes the global gate, but it too runs on the 0.35 by-name override.

| | | | |
|---|---|---|---|
| walked trades | 1620 | timeframe | M15 |
| realised median hold | 0.8 h | stop | 7.63 bps = 0.99 x ATR |
| toll | 1.32 bps (cost_r 0.1735) | **signal at own hold / toll** | **0.00x** |
| excursion capture | 3.4 % of mean MFE 1.47 R | exits | {'target': 484, 'stop': 1129, 'maxbars': 7} |
| estate decision | never armed; conf 0.15, forward_only | gate | REJECT |
| confidence | 0.15 | corr-cluster | `jpy` |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.45 |
| IR at own hold (the idea) | 0.0821 | cost_r (cost geometry) | 0.173 |
| TIGHT = stop/sigma (stop geometry) | 0.559 | RATIO signal/toll | 0.846 |
| realised resolution T_res | 0.75 h | drift argmax T_peak | 16.0 h |
| **ceiling at h\*=16.0 h** | drift 2.12 − toll 1.67 = **0.45 bps** | CI95 | [-5.69, 7.31] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 1614 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE VERDICT IS FORMALLY 'TOO SMALL' AND OPERATIONALLY 'IDEA_WRONG HERE'. At 0.00x it has no measurable directional content at its own horizon. It inherits fx_jpy's entire geometry problem: a 7.6 bps stop on a JPY cross puts the spread at ~10% of R and the trade lives 48 minutes. Same repair statement as fx_jpy: this needs a risk distance large enough that the spread is a small fraction of it, which is a different contract on a different clock, not an adjustment. AE gates it to 0.00 on cost-true evidence and it should stay there.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s1_receipts/S1_DISCRIMINATOR_V1.json`


## Section D — core W7, never measured (1 sleeve)

### `vp_euidx_pocgrav` — **UNDETERMINED**

**Premise.** European index price gravitates back toward the prior day's volume-profile point of control when it is far from it and volatility is elevated.

**Origin.** 86cccd08d (2026-06-15). Its port provenance is the best in the registry.

**Claimed at birth vs known now.** W7 cache: 341 trades 2024-01-03..2026-06-11, gross_r 0.29815, legacy charged cost 0.0638, published net 0.23435, at a 320 h structural horizon with 13.4 mean modelled nights. Folded as 'the frequency engine' at ~115 trades/yr.

**Parameters.** Its target is a measured move to a structural level rather than an R multiple, and its stop is one H4 ATR — a geometry that actually matches its premise, and the only sleeve of which that can be said without qualification.

**Geometry vs premise.** UNMEASURABLE ON ANY CURRENT SUBSTRATE. It produced ZERO trades in AQ's 32-sleeve archive walk (n_trades_by_sleeve = 0) because the walk has no M1 aux feed and the sleeve needs 20,000 M1 bars per decision. Its walk-forward gate verdict is NOT_EVALUABLE at n=0.

**Life cycle.** Coverage MEASURED 341 / TRANSFERRED 0. It is the ONLY member of the live decision surface whose realised hold, excursion, capture, exit mix and accumulation curve are entirely unknown, and its only economics are a modelled-held-to-horizon figure on a cache. It carries 0.30 confidence, which feeds sizing and the Kelly-lite day count.

| | | | |
|---|---|---|---|
| confidence | 0.30 | corr-cluster | `volprofile` |

**Verdict — UNDETERMINED. Repair.** THE GAP IS AN INSTRUMENT GAP, NOT AN EVIDENCE GAP, AND IT IS CHEAP TO CLOSE. (1) fetch prior-day M1 for GER40 and UK100 — AV_DEEP_H4_INGEST_V1.json already records the sleeve's exact aux requirement and is the harness for it, and /Users/borr/GTOSActive/repo/data/mt5_research_exports/bridge_ftmo_b7_4_m1_20260601_20260620 shows M1 bridge exports exist on this machine; then (2) run it through the same AQ/AD/AU pipeline as everything else. Until that happens the honest published statement is 'unmeasured' and it should not appear in any count of validated sleeves. This is the most valuable single missing measurement in the core book.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S1_ARMED_SLEEVES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`


## Section E — the candidate book (9 live-registered sleeves)

### `asia_pdl_fade` — **GEOMETRY_WRONG**

**Premise.** During the Asian session, price that pierces the prior day's low and then closes back above it has swept resting stops and reverses — buy the reclaim.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Confidence 0.25, status promotion_candidate_recency_oos_watch_natgas_split_applied. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** ASIA_HI 6, PIERCE 0.05, STOP_BUF 0.10, TARGET_R 3.0 — ALL FOUR shared with liq_asia_up_low_metal (x2's liquidity-sweep clone pair). The stop is wick-derived: a sweep that barely pierces gives a tiny stop.

**Geometry vs premise.** THE ONE FAMILY IN THE ESTATE WHERE THE OWNER'S HYPOTHESIS IS CONFIRMED AT BOTH MECHANISMS AND THERE IS SOMETHING TO CAPTURE. Declared horizon 32 M15 bars (8 h); realised median hold 4 bars, p90 38, 12.2% exceed the horizon. x1 tags it TOO_SHORT AND TOO_TIGHT: its drift peaks at h*=320 trading hours while its contract closes it in ~1 h, and its cost_r is 0.358. Its CEILING IS +78.03 bps [+18.45,+141.44] — CI EXCLUDES ZERO, on 2,761 trades over 194 days. Cost bands move R/day by 0.98 (flat -0.0873 -> high -1.0649), a swing nothing else in the estate comes near.

**Life cycle.** 2,827 trades, 942.3/yr across 30 symbols — the estate's dominant co-firing source; exits stop 69.4% / target 28.1% / maxbars 2.5%; median MFE +1.27 R against a 3.0 R target only 28.9% reach.

| | | | |
|---|---|---|---|
| confidence | 0.25 | corr-cluster | `liquidity_sweep` |
| gated trades | 2827 (942.3/yr) | grid | M15 |
| declared horizon | 32.0 own bars | realised median hold | 4.0 own bars (p90 38.0) |
| resolved inside entry bar | 0.2540 | exceeding live horizon | 0.1220 |
| median MFE | 1.270 R | exit mix | {'stop': 0.6937, 'target': 0.2812, 'maxbars': 0.0251} |
| ratified gate (mid band) | REJECT | R/day | -0.9021 |
| **X1 mechanism** | **TOO_SHORT, TOO_TIGHT** | max signed t across the ladder | 2.65 |
| IR at own hold (the idea) | 0.0594 | cost_r (cost geometry) | 0.358 |
| TIGHT = stop/sigma (stop geometry) | 0.210 | RATIO signal/toll | 0.790 |
| realised resolution T_res | 1.00 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 83.05 − toll 5.02 = **78.03 bps** | CI95 | [18.45, 141.44] |
| ceiling verdict | CEILING POSITIVE, CI EXCLUDES 0 | n | 2761 |

**Verdict — GEOMETRY_WRONG. Repair.** THE DEFECT IS THAT THE STOP IS AN ACCIDENT OF THE SWEEPING BAR, AND THE CURE IS TO STOP DERIVING IT THAT WAY — the same conclusion lane g3 reached independently for cross_asset_lead_lag and structural_distance_extreme. Repair: floor the stop at a fixed ATR multiple (max(wick + 0.10*ATR, k*ATR)), sweep k, and RE-LABEL THE STORED INTENTS — no generator re-run, no new data. Second: its cluster assignment (liquidity_sweep, ONE cluster for thirty instruments spanning FX, metals, crypto, energy and indices) makes it a single risk unit that can hold thirty correlated positions. WORTH: the band spread says cost is ~1 R/day of the answer, and it is the ONLY sleeve outside the armed set whose contract-free ceiling interval excludes zero — the wave's one unambiguous 'sound idea wearing the wrong contract'.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `asian_fade` — **GEOMETRY_WRONG**

**Premise.** The Asian session builds a range; the first break of that range during London or New York that shows a rejection wick is a false break and gets faded back toward the range.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2). Two of its cited artifacts (CMAP_SRMR_ASIANFADE_VERDICT.md, CMAP_SRMR_CORRECT_PLACEBO.json) resolve to NO FILE at HEAD (x2).

**Claimed at birth vs known now.** Birth claim rests on 3,198 EURUSD trades over 2014-2026. Confidence 0.40. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** STOP_K 0.6 ATR; TRAIL_GAP 0.5 shared with metal_session_reversion; 48-bar (12 h) horizon.

**Geometry vs premise.** THE SHARPEST PREMISE-VS-CONTRACT MISMATCH IN THE SLEEVE ESTATE, AND IT IS SELF-DECLARED. The docstring says the trade 'needs to ride the return move'. Measured: median hold ONE M15 bar, p90 ONE M15 bar, 95.8% of 1,319 trades resolved inside the bar they entered on; frac_over_live_horizon 0.0000; median MAE -0.93 R. The 0.6-ATR stop sits inside one M15 bar of the sleeve's own noise, so BOTH the trail (arm 0.5, gap 0.5) and the 12-hour horizon are dead letters. Exits split trail 51.9% / stop 48.1%, but a 'trail' that fires in the first fifteen minutes is a stop with extra steps.

**Life cycle.** 1,319 trades, 439.7/yr, 2024-01 onward only. AU: its published economics DO describe its live contract (true restamp error +0.0000 R/day); the defect is the contract itself, not the labelling.

| | | | |
|---|---|---|---|
| confidence | 0.40 | corr-cluster | `fx_reversion` |
| gated trades | 1319 (439.7/yr) | grid | M15 |
| declared horizon | 48.0 own bars | realised median hold | 1.0 own bars (p90 1.0) |
| resolved inside entry bar | 0.9583 | exceeding live horizon | 0.0000 |
| median MFE | 1.091 R | exit mix | {'trail': 0.5186, 'stop': 0.4814} |
| ratified gate (mid band) | REJECT | R/day | -1.0360 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.54 |
| IR at own hold (the idea) | 0.0599 | cost_r (cost geometry) | 0.277 |
| TIGHT = stop/sigma (stop geometry) | 0.492 | RATIO signal/toll | 0.440 |
| realised resolution T_res | 0.25 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 4.70 − toll 0.67 = **4.03 bps** | CI95 | [-8.62, 15.48] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 1294 |

**Verdict — GEOMETRY_WRONG. Repair.** THE IDEA IS A DOCUMENTED EFFECT AND THE CONTRACT IS THE DEFECT. (1) WIDEN THE STOP UNTIL THE TRADE OUTLIVES ITS ENTRY BAR — a stop ladder at 1.0/1.5/2.0 ATR on the same entries is a pure re-labelling of stored intents through walkforward.exits.replay (the exact operation AD did for 1,631 cells), costs no machine time beyond a walk, and is the ONLY way to find out whether the reversion the docstring describes exists, because the current contract cannot observe it. (2) BEFORE ANY OF IT, FETCH DEEP M15 — do not adjudicate a 2014-2026 claim on 2.5 years. Worth: unknown by construction, and THAT IS THE POINT — the current geometry makes the claim untestable, which is strictly worse than a measured negative.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x2_receipts/X2_PROVENANCE_PATTERN_V1.json`

### `metal_session_reversion` — **GEOMETRY_WRONG**

**Premise.** Each New York session, gold and silver that stretch a long way from the session open — while the higher-timeframe regime is NOT up — snap back toward it.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Confidence 0.40. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF. Its own docstring flags 2015/2016 as negative years.

**Parameters.** STOP_K 0.8 ATR; TRAIL_GAP 0.5 (shared with asian_fade); 24 M15 bars (6 h) horizon.

**Geometry vs premise.** Same shape as asian_fade and for the same reason. Realised median hold ONE M15 bar; 82.7% resolved inside the entry bar; frac_over_live_horizon 0.001; median MAE -0.75 R against a 0.8-ATR stop. A 'session anchor reversion' whose natural timescale is the remainder of the NY session is being decided in fifteen minutes. AU: construction_artifact 0.3054, true restamp_error -0.0004 — so like asian_fade the published economics DO describe its live contract.

**Life cycle.** 837 trades, 279.0/yr. It is one of only two GEOMETRY_WRONG verdicts in the whole estate with measurable signal at x1's contract-free instrument (max signed t 2.83, tags TOO_SHORT + TOO_TIGHT) — but its ceiling CI [-58.65,+95.56] includes zero.

| | | | |
|---|---|---|---|
| confidence | 0.40 | corr-cluster | `metal_reversion` |
| gated trades | 837 (279.0/yr) | grid | M15 |
| declared horizon | 24.0 own bars | realised median hold | 1.0 own bars (p90 2.0) |
| resolved inside entry bar | 0.8268 | exceeding live horizon | 0.0012 |
| median MFE | 0.853 R | exit mix | {'trail': 0.5795, 'stop': 0.4205} |
| ratified gate (mid band) | REJECT | R/day | -0.4080 |
| **X1 mechanism** | **TOO_SHORT, TOO_TIGHT** | max signed t across the ladder | 2.83 |
| IR at own hold (the idea) | 0.0845 | cost_r (cost geometry) | 0.474 |
| TIGHT = stop/sigma (stop geometry) | 0.550 | RATIO signal/toll | 0.324 |
| realised resolution T_res | 0.25 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 34.82 − toll 15.24 = **19.58 bps** | CI95 | [-58.65, 95.56] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 808 |

**Verdict — GEOMETRY_WRONG. Repair.** The same stop-width repair as asian_fade and the same deep-M15 precondition, but the prognosis is worse and the evidence says so plainly: AD's exit sweep found NO cell on this sleeve that clears expectancy, 0 of 5 folds positive, p 0.9998. That is not a contract failing to express an edge; that is no edge in this window. Honest sequencing: (1) fetch deep M15, (2) re-run the stop ladder on the 2015-2026 window its birth claims, (3) if the negative years its own docstring flags are the whole story, retire it. Until then it should not be called a promotion candidate — its registry status string still says promotion_candidate and nothing supports that word.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json`

### `kz_london_crypto_low` — **IDEA_WRONG**

**Premise.** The same clean-directional-move continuation as ny_crypto_momentum, but at the London 12:00 decision bar and only when volatility is LOW.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Its own birth note conceded the drift null was marginal at p~0.085 and that the original weight was 'weak additive'. Confidence 0.10. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** Six of its nine constants are ny_crypto_momentum's.

**Geometry vs premise.** Declared 32 M15 bars (8 h) hold-to-London-close; realised median hold 10 bars, p90 80, 23.4% reach the horizon. No fixed target, correct for the idea. AU prices the live 32-bar contract at +0.2322 R/day BETTER than the published 80-bar walk — THE LARGEST published-understates-live gap in the estate. So its contract is right and its published number is the wrong one. Its ceiling is -7.45 bps [-12.28,-1.89] — CI EXCLUDES ZERO ON THE NEGATIVE SIDE.

**Life cycle.** 286 trades, 95.3/yr. 42.7% of its trades are the same symbol-day-side as orb_crypto_london, which trades the same two coins in the overlapping London window.

| | | | |
|---|---|---|---|
| confidence | 0.10 | corr-cluster | `crypto` |
| gated trades | 286 (95.3/yr) | grid | M15 |
| declared horizon | 32.0 own bars | realised median hold | 10.0 own bars (p90 80.0) |
| resolved inside entry bar | 0.0455 | exceeding live horizon | 0.2343 |
| median MFE | 1.221 R | exit mix | {'stop': 0.8427, 'maxbars': 0.1573} |
| ratified gate (mid band) | REJECT | R/day | -0.6400 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.09 |
| IR at own hold (the idea) | 0.0210 | cost_r (cost geometry) | 0.339 |
| TIGHT = stop/sigma (stop geometry) | 0.434 | RATIO signal/toll | 0.143 |
| realised resolution T_res | 2.50 h | drift argmax T_peak | 0.5 h |
| **ceiling at h\*=0.5 h** | drift 1.79 − toll 9.24 = **-7.45 bps** | CI95 | [-12.28, -1.89] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 286 |

**Verdict — IDEA_WRONG. Repair.** TWO INDEPENDENT REASONS, WHICH IS WHY THIS ONE GETS A HARDER VERDICT THAN ITS NY SIBLING. (1) It fails every core gate at its own best exit cell — expectancy included, 2 of 5 folds, p 0.66 — so unlike ny_crypto_momentum this is not a short-window ambiguity. (2) It is not a distinct object. Retire it as a sleeve and re-declare it as a CELL of the killzone family, which costs nothing, removes a registry row, and makes the family's multiplicity bill honest. At confidence 0.10 the direct sizing effect is small; the value is that it stops a single hypothesis being counted three times in a family where significance is the gate that kills everything.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `liq_asia_up_low_metal` — **IDEA_WRONG**

**Premise.** In metals only, during the Asian session, in a prior-day up regime and a low intraday-vol state, a swept-and-reclaimed prior-day high or low reverses.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** 496 birth trades, of which this archive can see 157. Confidence 0.25. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** ASIA_HI 6, PIERCE 0.05, STOP_BUF 0.10, TARGET_R 3.0 — four of four inherited from asia_pdl_fade. Its two extra gates (D1-up, low-vol) were chosen in-sample on 496 trades.

**Geometry vs premise.** Declared horizon 16 M15 bars (4 h) — the shortest in the candidate book; median hold 3 bars, p90 18, 11.5% exceed it. Median MFE +1.38 R against a 3.0 R target reached by 30.6%; median MAE -1.26 R. AU prices its short horizon at +0.0866 R/day IN ITS FAVOUR — the live 16-bar contract beats the published 80-bar walk. So the geometry is NOT the problem. Its cost_r is 0.877 — THE HIGHEST IN THE ESTATE: it pays 0.877 R per trade in toll before the trade has an opinion.

**Life cycle.** 157 gated trades, 52.3/yr. Signal at own hold -0.070x.

| | | | |
|---|---|---|---|
| confidence | 0.25 | corr-cluster | `metal_liquidity_reversion` |
| gated trades | 157 (52.3/yr) | grid | M15 |
| declared horizon | 16.0 own bars | realised median hold | 3.0 own bars (p90 18.0) |
| resolved inside entry bar | 0.2803 | exceeding live horizon | 0.1146 |
| median MFE | 1.379 R | exit mix | {'stop': 0.7197, 'target': 0.2803} |
| ratified gate (mid band) | REJECT | R/day | -0.8084 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.81 |
| IR at own hold (the idea) | -0.0225 | cost_r (cost geometry) | 0.877 |
| TIGHT = stop/sigma (stop geometry) | 0.368 | RATIO signal/toll | -0.070 |
| realised resolution T_res | 0.75 h | drift argmax T_peak | 72.0 h |
| **ceiling at h\*=72.0 h** | drift 29.06 − toll 12.19 = **16.88 bps** | CI95 | [-54.47, 85.54] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 157 |

**Verdict — IDEA_WRONG. Repair.** READ THE VERDICT PRECISELY: the SWEEP-RECLAIM premise is not refuted — its parent carries it. What is refuted is that this is a DISTINCT MECHANISM deserving its own registry row, its own 0.25 confidence and its own corr-cluster. DEMOTE IT TO A CONDITION ON ITS PARENT: if the D1-up + low-vol pair is real it is a quality flag on asia_pdl_fade's metals rows and can be tested as one on the parent's 2,827-row population instead of on 157 — a strictly stronger test, no new data, no new code. That also deletes a registry row, deletes a corr-cluster, and removes one of the three groups whose collapse moves the Kelly-lite multiplier. If it does not survive as a flag on the parent, it was never a sleeve.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json`

### `vol_compression` — **SOUND_BUT_TOO_SMALL**

**Premise.** After a stretch of unusually quiet daily ranges, the first daily close that breaks the prior 20-day high or low starts a directional move.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Confidence 0.40. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** D1 20-bar channel, 80-D1-bar horizon, 3.0R target. Its own docstring's negative control (coil breakout without the vol-state = NULL every split) is the design note.

**Geometry vs premise.** D1 clock, 1,920 h declared horizon, realised median hold 9 D1 bars, p90 35, frac_over_live_horizon 0.0000. Exits stop 65.0% / target 33.3% / maxbars 1.8%. Median MFE +1.40 R against a 3.0 R target only 33.3% ever reach. It is AU's ladder CONTROL sleeve: monotone RISING to h=20 with h=1 its worst cell, the opposite shape to the mis-scaled mx cohort. Ceiling +78.05 bps at h*=320, CI [-200.14,+343.82].

**Life cycle.** 391 trades, 43.4/yr on three symbols, 2018-2026. Positive at every cost band; only failing gate is significance.

| | | | |
|---|---|---|---|
| confidence | 0.40 | corr-cluster | `crypto` |
| gated trades | 391 (43.4/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 9.0 own bars (p90 35.0) |
| resolved inside entry bar | 0.0614 | exceeding live horizon | 0.0000 |
| median MFE | 1.401 R | exit mix | {'stop': 0.6496, 'target': 0.3325, 'maxbars': 0.0179} |
| ratified gate (mid band) | REJECT | R/day | 0.9050 |
| **X1 mechanism** | **CONTRACT_OK** | max signed t across the ladder | 2.13 |
| IR at own hold (the idea) | 0.1747 | cost_r (cost geometry) | 0.214 |
| TIGHT = stop/sigma (stop geometry) | 0.524 | RATIO signal/toll | 1.557 |
| realised resolution T_res | 216.00 h | drift argmax T_peak | 232.0 h |
| **ceiling at h\*=320.0 h** | drift 296.09 − toll 218.03 = **78.05 bps** | CI95 | [-200.14, 343.82] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 388 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE REPAIR IS SAMPLE, NOT CONTRACT. (1) STOP DOUBLE-COUNTING IT: its BTC/ETH leg is 100% contained in the mx Donchian sleeves, so the estate counts one BTC daily-breakout hypothesis as two family members at two confidence weights in two corr-clusters. Merge them into one declared member with per-symbol carriers. (2) BROADEN THE SURFACE ON THE SAME RULE — its own docstring says 'the mega-factory may extend (XRP 2017+)' and the D1 archive carries ADAUSD, DOTUSD, LTCUSD, XRPUSD, DASHUSD, AVAUSD with deep history. A sample repair with a pre-declared rule and no new parameters — the only kind of failure more data can fix.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `ny_crypto_momentum` — **UNDETERMINED**

**Premise.** When the New York session's crypto move has been clean and one-directional, and volatility is not low, the move continues into the session close.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Birth: +0.2017 R pooled with a correct random-entry null at p=0.0007 on roughly three times the sample the gate can see. Confidence 0.35. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** DE_THRESH 0.50, STOP_MULT 1.3, VOL_LO 0.34, VOL_WIN 480, WINDOW 12, DECISION_MIN 0, VOL_HI 0.67 — SEVEN constants identical to ny_index_momentum and kz_london_crypto_low; only DECISION_HOUR and MAXBARS are genuinely per-cell (x2's killzone triplet). final_target_r None and broker_take_profit_mode none — correct for a hold-to-close idea.

**Geometry vs premise.** THE ONE CANDIDATE SLEEVE WHOSE HORIZON ACTUALLY BINDS, AND IT BINDS AS DESIGNED. Declared 20 M15 bars = hold to ~22:00 session close; realised median hold 8 bars, p90 80, 37.0% hit the horizon (exit_mix maxbars 24.7%). AU prices the live 20-bar contract at +0.2032 R/day BETTER than the published 80-bar walk. The geometry matches the premise; that is not where it fails.

**Life cycle.** 559 trades, 186.3/yr, 2024-2026 only. Ratified gate: -0.248 R/day, p 0.4858, 2 of 5 folds positive.

| | | | |
|---|---|---|---|
| confidence | 0.35 | corr-cluster | `crypto` |
| gated trades | 559 (186.3/yr) | grid | M15 |
| declared horizon | 20.0 own bars | realised median hold | 8.0 own bars (p90 80.0) |
| resolved inside entry bar | 0.1485 | exceeding live horizon | 0.3703 |
| median MFE | 1.055 R | exit mix | {'stop': 0.7531, 'maxbars': 0.2469} |
| ratified gate (mid band) | REJECT | R/day | -0.2481 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.79 |
| IR at own hold (the idea) | 0.0554 | cost_r (cost geometry) | 0.192 |
| TIGHT = stop/sigma (stop geometry) | 0.465 | RATIO signal/toll | 0.620 |
| realised resolution T_res | 2.00 h | drift argmax T_peak | 2.0 h |
| **ceiling at h\*=2.0 h** | drift 7.19 − toll 11.60 = **-4.41 bps** | CI95 | [-21.86, 13.88] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 559 |

**Verdict — UNDETERMINED. Repair.** I WILL NOT CALL THIS IDEA WRONG ON 2.5 YEARS OF DATA WHEN ITS BIRTH CLAIM RESTS ON THREE TIMES THE SAMPLE AND THE RIGHT NULLS. THE REPAIR IS A DATA FETCH — deep M15 history, the same unblock as the rest of the candidate book; AV_DEEP_H4_INGEST_V1.json already built exactly this harness for H4 and nothing equivalent has been scoped for M15. Second, before any re-test: this sleeve, kz_london_crypto_low and ny_index_momentum are ONE RULE with seven shared constants at three (session, asset-class) cells and must be declared as one family with three cells — otherwise the multiplicity bill triple-counts a single hypothesis, which is precisely why significance is the binding gate on 13 of 15 sleeves in this lane.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x2_receipts/X2_PROVENANCE_PATTERN_V1.json`

### `orb_crypto_london` — **UNDETERMINED**

**Premise.** Build the London opening range on crypto; the first bar that closes beyond it continues in that direction, when volatility is low and the higher timeframe is trending.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Birth claim 2,375-2,706 trades — and THE TWO PUBLISHED VERSIONS OF THAT CLAIM DISAGREE WITH EACH OTHER: a reader of candidate_registry.py and a reader of orb_crypto_london.py get different numbers for the same sleeve. Confidence 0.35. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** 80 M15 bars (20 h) horizon, 2.0R target.

**Geometry vs premise.** Declared 80 M15 bars — the longest M15 horizon in the book, and the ONLY candidate sleeve whose MAXBARS equals AA's walk horizon, so its published and live numbers agree exactly (restamp_error 0.0000). Realised median hold 13 bars, p90 38, frac_over_live_horizon 0.0000: the 20-hour horizon never binds. Median MFE +1.16 R against a 2.0 R target reached by 35.5%. Its geometry is the one thing that does NOT need repair.

**Life cycle.** 858 trades, 286.0/yr on two coins, 49% long, 2024-2026 only. Cost band moves it by only 0.14 R/day, so unlike asia_pdl_fade this is not a stop-geometry problem.

| | | | |
|---|---|---|---|
| confidence | 0.35 | corr-cluster | `crypto` |
| gated trades | 858 (286.0/yr) | grid | M15 |
| declared horizon | 80.0 own bars | realised median hold | 13.0 own bars (p90 38.0) |
| resolved inside entry bar | 0.0082 | exceeding live horizon | 0.0000 |
| median MFE | 1.163 R | exit mix | {'stop': 0.6212, 'target': 0.3543, 'maxbars': 0.0245} |
| ratified gate (mid band) | REJECT | R/day | -0.1576 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.92 |
| IR at own hold (the idea) | 0.0312 | cost_r (cost geometry) | 0.182 |
| TIGHT = stop/sigma (stop geometry) | 0.629 | RATIO signal/toll | 0.273 |
| realised resolution T_res | 3.25 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 130.82 − toll 18.34 = **112.48 bps** | CI95 | [-19.22, 248.56] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 847 |

**Verdict — UNDETERMINED. Repair.** Not adjudicable: the gated window is 2.5 years against a birth claim of ~2,500 trades. Sequencing: (1) deep M15 fetch — the same unblock as the rest of the candidate book; (2) reconcile the two birth tuples or strike both at source; (3) declare the crypto continuation family ONCE (this, ny_crypto_momentum, kz_london_crypto_low) instead of three times. Its clean geometry makes it the control for any horizon work on its siblings.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`

### `vss_fxcross_london_up_low` — **UNDETERMINED**

**Premise.** JPY crosses and EURGBP that compress into a narrow box during London, in a prior-day up regime and a low-vol state, break out of the box and run.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** 860 birth trades and an out-of-sample daily mean of +0.001194. Its own author labelled it oos_decay_watch. Confidence 0.12. Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.

**Parameters.** TWELVE free parameters — a box-breakout with a squeeze percentile, a vol percentile, a D1 regime gate and two SMAs. Stop 1.0 ATR and target 2.0 ATR are genuine parameters rather than structure, which is unusual here and defensible.

**Geometry vs premise.** Declared 48 M15 bars (12 h); realised median hold 3 bars, p90 7, frac_over_live_horizon 0.0000 — the horizon never binds, and 27.6% of trades are decided inside the entry bar. Exits stop 58.8% / target 41.2% with NO maxbars exits at all — the cleanest resolution profile in the lane. Median MFE +1.36 R against a 2.0 R target reached by 41.6%.

**Life cycle.** 308 gated trades, 102.7/yr, 2.5 years.

| | | | |
|---|---|---|---|
| confidence | 0.12 | corr-cluster | `fxcross_vol_state_squeeze` |
| gated trades | 308 (102.7/yr) | grid | M15 |
| declared horizon | 48.0 own bars | realised median hold | 3.0 own bars (p90 7.0) |
| resolved inside entry bar | 0.2760 | exceeding live horizon | 0.0000 |
| median MFE | 1.356 R | exit mix | {'stop': 0.5877, 'target': 0.4123} |
| ratified gate (mid band) | REJECT | R/day | -0.1828 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.24 |
| IR at own hold (the idea) | -0.0254 | cost_r (cost geometry) | 0.341 |
| TIGHT = stop/sigma (stop geometry) | 0.541 | RATIO signal/toll | -0.138 |
| realised resolution T_res | 0.75 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 19.44 − toll 1.53 = **17.91 bps** | CI95 | [-13.22, 48.14] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 306 |

**Verdict — UNDETERMINED. Repair.** Twelve free parameters on 860 birth trades is a sleeve that was fitted, but 308 trades on 2.5 years makes 'the idea is wrong' overreach. THE PROPORTIONATE REPAIR IS NOT MORE MEASUREMENT — IT IS PARAMETER REDUCTION BEFORE ANY RE-TEST: ask whether the plain 20-bar box breakout in London on these five crosses carries anything at all. That is a nested-model test on the same rows, costs one walk, and would tell you whether there is a sleeve here or four filters on noise. Until then it should not be sized: at 0.12 confidence and 103 trades/year it cannot move the book either way, so the only thing it currently contributes is one more member to the family bill that is killing everything else.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`


## Section F — the candidate book, quarantined (3 sleeves)

### `ny_index_momentum` — **STALE**

**Premise.** The same clean-directional NY continuation as ny_crypto_momentum, on stock indices, restricted to a mid-volatility state.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2).

**Claimed at birth vs known now.** Its own leave-one-out says the book improved when it was dropped.

**Parameters.** NINE constants, seven of them ny_crypto_momentum's, inherited unmodified onto a different asset class with a different session structure — the same category of transfer lane g4 found when the H4 microstructure book was ported onto an M15 clock.

**Geometry vs premise.** Not measurable: not in CANDIDATE_BUILT, zero rows in the estate walk.

**Life cycle.** Zero rows on either live namespace and in every estate artifact.

**Verdict — STALE. Repair.** DELETE IT. Three independent reasons, each sufficient: it is a nine-constant clone of a sleeve that is itself unresolved; its own leave-one-out says the book improved when it was dropped; and it has produced zero rows anywhere. There is nothing to repair because there is no distinct hypothesis — if the killzone-continuation rule is ever re-tested on deep M15, indices are a CELL of that test, not a sleeve. Keeping it costs a registry import, a catalogue row, a family member in every multiplicity count that enumerates CANDIDATE_NAMES, and a reader's time. THE CLEAREST DELETION IN THE ESTATE.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`

### `structural_retest` — **STALE**

**Premise.** A structural break (order block, breaker, displacement, sweep or FVG) that is retested continues in the higher-timeframe regime direction — fired only in verified (class, session, regime, vol) cells.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2). Shares ATR_STOP_FLOOR 0.25 and STOP_BUF 0.10 with metals.py and metals_ob_micro.py (x2's metals triplet).

**Claimed at birth vs known now.** Per-trade edge at birth +0.057 to +0.143 R — an edge smaller than a typical M15 cost. Its own daily-unit audit then measured it NEGATIVE on every split (-0.071 R daily mean), which is the level that decides a book.

**Parameters.** Fixed 2R with a 32-bar M15 time stop.

**Geometry vs premise.** Not measurable: not in CANDIDATE_BUILT, zero rows in the estate walk.

**Life cycle.** Zero rows anywhere.

**Verdict — STALE. Repair.** A COMPLETED KILL, not an open question, and unlike vol_squeeze the reason is not a clustering artifact. The only reason to keep the file is that its three verified cells are a written statement of where a retest mechanic was thought to work, and lane g1's forensic on the POI families makes that statement worth preserving as prose. RECOMMENDATION: delete the module and the catalogue row, and lift the three-cell table into the g1 dossier as historical intelligence first, exactly as the cleanup policy prescribes ('extract useful intelligence into current summaries before deleting').

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`

### `vol_squeeze` — **STALE**

**Premise.** Indices that compress into a low-ATR regime and then print an expansion bar with a large body, in the higher-timeframe trend direction, keep going.

**Origin.** b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2). Quarantined for fourteen months with no redesign scheduled.

**Claimed at birth vs known now.** Quarantined for a book-level correlated-risk drag on indices. Its cited generator does not exist.

**Parameters.** H4 clock, structural stop plus 0.3 ATR, 3R target, no declared time stop.

**Geometry vs premise.** NOT MEASURABLE: it is not in CANDIDATE_BUILT, so active_specs can never return it, and it produced zero rows in the estate walk.

**Life cycle.** Zero rows anywhere, ever.

**Verdict — STALE. Repair.** Its quarantine reason is the most interesting thing about it and it is now diagnosable: it was dropped for an index correlated-risk drag, and this lane measured that the governor's cluster keying is what makes index sleeves collide (US30_cash sits in four clusters, UK100 and GER40 in four each). So the honest question is whether vol_squeeze was a bad sleeve or a victim of a clustering defect, and it is answerable at ZERO COST by re-running the book MC with index sleeves in ONE cluster. That said: it has never emitted a row and its cited generator does not exist. DELETE IT unless the cluster question is actually going to be asked — in which case preserve its docstring's negative control (coil breakout without the vol-state = NULL every split) as the design note it is.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json`


## Section G — the market-expansion mx_* cohort (14 sleeves)

### `mx_cadjpy_d1_volume_surge_reversal` — **IDEA_WRONG**

**Premise.** CAD/JPY that moves on abnormally high daily volume reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** 286 trades over nineteen years; fails expectancy at p 0.89. AU returned MEASURED_BUT_NOT_PRESCRIBED at h=20 because every cell is negative.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 12; horizon inert. Median MFE +1.04 R — the lowest but one in the cohort; only 37.4% reach 2R and 33.2% never reach 0.5 R. AQ's repair was worth +0.0523 R/day (positive), so it wanted the longer hold.

**Life cycle.** 286 trades, 15.1/yr.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `jpy_fx` |
| gated trades | 286 (15.1/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 12.0) |
| resolved inside entry bar | 0.2273 | exceeding live horizon | 0.0000 |
| median MFE | 1.041 R | exit mix | {'stop': 0.6259, 'target': 0.3741} |
| ratified gate (mid band) | REJECT | R/day | -0.2559 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.49 |
| IR at own hold (the idea) | 0.0921 | cost_r (cost geometry) | 0.053 |
| TIGHT = stop/sigma (stop geometry) | 0.605 | RATIO signal/toll | 2.882 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=72.0 h** | drift 14.84 − toll 5.15 = **9.69 bps** | CI95 | [-17.72, 38.67] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 286 |

**Verdict — IDEA_WRONG. Repair.** THE PREMISE HAS A CATEGORY PROBLEM BEFORE IT HAS AN ECONOMICS PROBLEM: 'volume surge' on a JPY cross is a tick-update count, and VOLUME_Z_THRESHOLD=2.0 was set once for all eight volume-surge sleeves across indices and FX with no per-class derivation. There is no repair worth buying — fixing the volume proxy would require a real volume series that does not exist for an FX cross. RETIRE IT WITH mx_nzdjpy, and note the pattern for the record: BOTH jpy_fx cluster members fail on every gate while the indices_context volume-surge members do not, which is exactly what you would expect if the volume proxy carries information on an exchange-traded index and none on a cross.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_nzdjpy_d1_donchian_20_breakout` — **IDEA_WRONG**

**Premise.** NZD/JPY that closes above its own prior 20-day high keeps going.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Longest history (2007-2026), largest sample (503 trades, 349 gated), most exit cells swept — and ZERO of five chronological folds positive, p 0.9701, failure on every core gate including expectancy.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Longest realised hold in the cohort — median 4 D1 bars, p90 10 — with the horizon still inert at 80. Median MFE +1.18 R, the second-lowest; only 35.0% reach 2R. Its best exit cell is partial_1.5R_be and it is negative there too. x1: IR -0.0709, RATIO -2.250 — the worst mx reading, and its ceiling is negative at every horizon.

**Life cycle.** 503 trades, 25.1/yr, 2007-2026.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `jpy_fx` |
| gated trades | 503 (25.1/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 4.0 own bars (p90 10.0) |
| resolved inside entry bar | 0.1491 | exceeding live horizon | 0.0000 |
| median MFE | 1.177 R | exit mix | {'stop': 0.6461, 'target': 0.3499, 'maxbars': 0.004} |
| ratified gate (mid band) | REJECT | R/day | -0.1562 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | -0.64 |
| IR at own hold (the idea) | -0.0709 | cost_r (cost geometry) | 0.060 |
| TIGHT = stop/sigma (stop geometry) | 0.525 | RATIO signal/toll | -2.250 |
| realised resolution T_res | 96.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=16.0 h** | drift -4.93 − toll 4.28 = **-9.22 bps** | CI95 | [-21.12, 2.49] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 503 |

**Verdict — IDEA_WRONG. Repair.** NOT REPAIRABLE AND IT SHOULD BE SAID PLAINLY, BECAUSE THIS IS THE COHORT'S BEST TEST OF ITS OWN PREMISE. A 20-day channel breakout on a carry-driven FX cross is not the same object as one on crypto, and the measurement says so. The useful consequence is not for this sleeve but for the family: the cohort's three DONCHIAN members split cleanly by asset class (BTC 4/5 folds, ETH 5/5, AVAUSD 5/5 but unevaluable — all crypto; NZDJPY 0/5 — FX). PRESCRIPTION: retire it from the 12-policy, and stop describing the Donchian rule as instrument-agnostic — it is a crypto rule with an FX member attached, and the FX member is the control that proves it.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_btcusd_d1_donchian_20_breakout` — **SOUND_BUT_TOO_SMALL**

**Premise.** Bitcoin that closes above its own prior 20-day high keeps going.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** THE ESTATE'S ONLY GENERATOR THAT HAS EVER CLEARED ITS OWN RATIFIED STANDARD — and the admission was REVERSED SIX DAYS LATER. Raw p 0.0106, 4 of 5 chronological folds positive, +0.53 R/trade OOS at target_5R. Wave 10 measured that the admission DECAYS chronologically: recent folds +0.198 R/day against +1.504 in the early ones (13.2%).

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 10, horizon inert at 80. 82.3% of trades hold past 24 h, which is why AQ's time-stop unit repair was worth +0.2722 R/day here — the largest positive repair delta in the cohort. Median MFE +1.52 R, the highest in the cohort; 45.3% reach 2R, which is what makes the 5R target cell coherent rather than fitted. AU's ladder puts its best cell at h=40. x1: signal at its own 72 h hold +146.74 vs a 58.92 bps toll = 2.49x, ceiling +203.17 bps [+32.62,+397.30] — CI EXCLUDES ZERO.

**Life cycle.** 318 trades, 31.8/yr. ARMED FTMO 2026-07-31 at confidence 0.025; DISARMED 2026-08-05 by owner instruction (host commit 2fa77722d, --tags and --frontier-exits removed, no config byte moved so the token digest is unchanged) after A1b's corrected permutation null flipped it ADMIT -> REJECT (q 0.048 -> 0.129 at mid).

| | | | |
|---|---|---|---|
| walked trades | 318 | timeframe | D1 |
| realised median hold | 72.0 h | stop | 435.97 bps = 1.00 x ATR |
| toll | 58.92 bps (cost_r 0.1352) | **signal at own hold / toll** | **2.49x** |
| excursion capture | 20.0 % of mean MFE 1.74 R | exits | {'stop': 175, 'target': 143} |
| estate decision | ARMED FTMO 2026-07-31, DISARMED 2026-08-05 (owner, host 2fa77722d) | gate | REJECT |
| confidence | 0.03 | corr-cluster | `crypto_alt_or_major` |
| gated trades | 318 (31.8/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 10.0) |
| resolved inside entry bar | 0.2767 | exceeding live horizon | 0.0000 |
| median MFE | 1.521 R | exit mix | {'stop': 0.5503, 'target': 0.4497} |
| ratified gate (mid band) | REJECT | R/day | 0.1172 |
| **X1 mechanism** | **TOO_SHORT** | max signed t across the ladder | 2.61 |
| IR at own hold (the idea) | 0.1639 | cost_r (cost geometry) | 0.135 |
| TIGHT = stop/sigma (stop geometry) | 0.531 | RATIO signal/toll | 2.282 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 317.50 − toll 114.32 = **203.17 bps** | CI95 | [32.62, 397.30] |
| ceiling verdict | CEILING POSITIVE, CI EXCLUDES 0 | n | 317 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE IDEA DID NOT MOVE; THE MULTIPLICITY POSTURE DID. This lane's contract-free instrument reads it 2.49x, positive and CI-clean from 72 h — the directional content is real and the disarm was a governance call on the family bill, not a finding about the setup. LANE DISAGREEMENT, RECORDED: s1 filed SOUND, s2 filed SOUND_BUT_TOO_SMALL; this synthesis takes s2's, because the binding constraint is size and bill rather than idea or geometry, and at registry confidence 0.025 the arming was economically inert by design. Two things stay on its file: (1) it is the estate's proof that an INHERITED TARGET is a real defect — 2R rejects, 5R admits, and the difference IS the admission; (2) AQ's want = budget + 64 hazard: at the repaired 7,680-bar time stop an open mx_* position requests 7,744 M15 bars per tick and the stop degrades to INERT if the terminal returns fewer. Cleared at 7,800 bars on both terminals, but it must be re-measured before any mx_* sleeve is armed again. Merging it with mx_ethusd and vol_compression into one declared member shrinks the family bill that is the only thing it fails on.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_ethusd_d1_donchian_20_breakout` — **SOUND_BUT_TOO_SMALL**

**Premise.** Ether that closes above its own prior 20-day high keeps going.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** 5 of 5 chronological folds positive, +0.426 R/trade OOS at target_5R, raw p 0.0308. Only failing gate is significance.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 10; horizon inert at 80. Median MFE +1.40 R; 41.8% reach 2R. AQ's repair from the 1-bar accident was worth +0.0674 R/day — positive, so it wanted a LONGER hold — and AU's ladder then found the optimum at 10 bars (+0.0838 vs +0.0240 at 80 and -0.0434 at 1). It is the one mx sleeve whose declared short horizon is a genuine intermediate rather than a return to h=1. x1 ceiling +250.81 bps [+16.52,+494.20] — CI EXCLUDES ZERO.

**Life cycle.** 311 trades, 31.1/yr.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `crypto_alt_or_major` |
| gated trades | 311 (31.1/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 10.0) |
| resolved inside entry bar | 0.2508 | exceeding live horizon | 0.0000 |
| median MFE | 1.398 R | exit mix | {'stop': 0.5788, 'target': 0.418, 'maxbars': 0.0032} |
| ratified gate (mid band) | REJECT | R/day | -0.0434 |
| **X1 mechanism** | **TOO_SHORT** | max signed t across the ladder | 2.72 |
| IR at own hold (the idea) | 0.2112 | cost_r (cost geometry) | 0.103 |
| TIGHT = stop/sigma (stop geometry) | 0.591 | RATIO signal/toll | 3.464 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 192.0 h |
| **ceiling at h\*=160.0 h** | drift 354.82 − toll 104.01 = **250.81 bps** | CI95 | [16.52, 494.20] |
| ceiling verdict | CEILING POSITIVE, CI EXCLUDES 0 | n | 311 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** A DECLARATION REPAIR WITH NO CODE AND NO DATA: collapse mx_btcusd + mx_ethusd + vol_compression into a single 'crypto D1 channel breakout' member with a per-symbol breadth check. That is the shape AF's coherence test (dispersion ratio < 1 AND all members positive) was built for and which this trio might actually pass — the two mx members are 5/5 and 4/5 folds positive and vol_compression is positive at all four cost bands. It converts three marginal singletons into one member with three carriers, which is the only structure in this estate that has ever cleared a family bill.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_ger40_cash_d1_volume_surge_reversal` — **SOUND_BUT_TOO_SMALL**

**Premise.** The GER40 cash index that moves on abnormally high daily volume reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Positive at all four cost bands, 4 of 5 folds positive, fails on SIGNIFICANCE ALONE — but fires ~16 times a year on one instrument, so no amount of contract work changes the answer: sample-starved, not broken.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 9, horizon inert at 80. Median MFE +1.20/+1.47/+1.20 R across the trio; 2R reached by 36.4%/42.7%/38.0%. AQ's repair was NEGATIVE for ger40 (-0.1234) and us30 (-0.0837) and POSITIVE for jp225 (+0.0412) — two of three want the first day only and one wants the full research horizon, ON THE SAME RULE AND THE SAME CONSTANTS. That split is the cleanest evidence in the cohort that the horizon is a per-instrument property the shared machinery cannot express.

**Life cycle.** 110-121 trades each, 15.7-18.3/yr each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |
| gated trades | 110 (15.7/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 9.0) |
| resolved inside entry bar | 0.2182 | exceeding live horizon | 0.0000 |
| median MFE | 1.200 R | exit mix | {'stop': 0.6364, 'target': 0.3636} |
| ratified gate (mid band) | REJECT | R/day | 0.1152 |
| **X1 mechanism** | **CONTRACT_OK** | max signed t across the ladder | 2.35 |
| IR at own hold (the idea) | 0.2177 | cost_r (cost geometry) | 0.116 |
| TIGHT = stop/sigma (stop geometry) | 0.684 | RATIO signal/toll | 2.747 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=160.0 h** | drift 67.20 − toll 33.31 = **33.90 bps** | CI95 | [-41.72, 108.30] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 110 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE ONE REPAIR THAT IS BOTH CHEAP AND PRINCIPLED IS A POOLING REPAIR, NOT A PER-SLEEVE ONE. Eight of the fourteen mx sleeves are the identical volume-surge rule with identical constants; six are cash indices. Declaring 'D1 volume-surge reversal on cash indices' as ONE member with six carriers, pooled, is a single hypothesis with ~100 trades a year instead of six hypotheses with sixteen each — the only structure that can clear a family bill on this rule. AF's coherence test is the existing instrument for deciding whether that pooling is legitimate and IT HAS NEVER BEEN RUN ON THE mx COHORT. If the pooled member is built, its horizon must be a DECLARED property of the pool, not inherited.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_jp225_cash_d1_volume_surge_reversal` — **SOUND_BUT_TOO_SMALL**

**Premise.** The JP225 cash index that moves on abnormally high daily volume reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Positive at all four cost bands, 4 of 5 folds positive, fails on SIGNIFICANCE ALONE — but fires ~16 times a year on one instrument, so no amount of contract work changes the answer: sample-starved, not broken.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 9, horizon inert at 80. Median MFE +1.20/+1.47/+1.20 R across the trio; 2R reached by 36.4%/42.7%/38.0%. AQ's repair was NEGATIVE for ger40 (-0.1234) and us30 (-0.0837) and POSITIVE for jp225 (+0.0412) — two of three want the first day only and one wants the full research horizon, ON THE SAME RULE AND THE SAME CONSTANTS. That split is the cleanest evidence in the cohort that the horizon is a per-instrument property the shared machinery cannot express.

**Life cycle.** 110-121 trades each, 15.7-18.3/yr each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |
| gated trades | 110 (18.3/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 9.0) |
| resolved inside entry bar | 0.2000 | exceeding live horizon | 0.0000 |
| median MFE | 1.472 R | exit mix | {'stop': 0.5727, 'target': 0.4273} |
| ratified gate (mid band) | REJECT | R/day | 0.1565 |
| **X1 mechanism** | **TOO_SHORT** | max signed t across the ladder | 2.42 |
| IR at own hold (the idea) | 0.0440 | cost_r (cost geometry) | 0.089 |
| TIGHT = stop/sigma (stop geometry) | 0.588 | RATIO signal/toll | 0.838 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 106.10 − toll 30.13 = **75.97 bps** | CI95 | [-31.30, 186.49] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 110 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE ONE REPAIR THAT IS BOTH CHEAP AND PRINCIPLED IS A POOLING REPAIR, NOT A PER-SLEEVE ONE. Eight of the fourteen mx sleeves are the identical volume-surge rule with identical constants; six are cash indices. Declaring 'D1 volume-surge reversal on cash indices' as ONE member with six carriers, pooled, is a single hypothesis with ~100 trades a year instead of six hypotheses with sixteen each — the only structure that can clear a family bill on this rule. AF's coherence test is the existing instrument for deciding whether that pooling is legitimate and IT HAS NEVER BEEN RUN ON THE mx COHORT. If the pooled member is built, its horizon must be a DECLARED property of the pool, not inherited.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_us100_cash_d1_atr_mean_reversion` — **SOUND_BUT_TOO_SMALL**

**Premise.** The US100 cash index whose previous daily return exceeded 1.25x its own recent average true range reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Eleven trades a year. AU declared a one-day horizon for both at time_stop_m15(1,'D1'), wired and default-off.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 9-10; horizon inert at 80. Median MFE +0.88 R (the LOWEST in the cohort); 2R reached by 26.8% — the two worst rates of the ten. AQ's repair from the 1-bar accident was worth -0.5913 R/day — by far the largest NEGATIVE deltas in the cohort, so both sleeves are strongly better on a ONE-DAY hold and AU declared exactly that.

**Life cycle.** 67-71 trades each, ~11/yr each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |
| gated trades | 71 (11.8/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 10.0) |
| resolved inside entry bar | 0.0986 | exceeding live horizon | 0.0000 |
| median MFE | 0.882 R | exit mix | {'stop': 0.7465, 'target': 0.2535} |
| ratified gate (mid band) | REJECT | R/day | 0.1415 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.98 |
| IR at own hold (the idea) | 0.0956 | cost_r (cost geometry) | 0.079 |
| TIGHT = stop/sigma (stop geometry) | 0.666 | RATIO signal/toll | 1.818 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=16.0 h** | drift 49.13 − toll 5.29 = **43.85 bps** | CI95 | [-2.98, 92.55] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 71 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** The horizon question has been asked and answered for this pair and the answer is unusually clean — one day, declared, wired, default-off, worth +0.59 and +0.56 R/day against the 80-bar contract. What cannot be repaired at this scale is the sample. TWO OBSERVATIONS. (1) THE ONE-DAY RESULT IS THE MOST INTERESTING THING IN THE COHORT and it is not being read that way: a mean-reversion entry whose entire value is in the first day, with the second day actively giving it back, is a statement about how long the reversion lives — and it is the same shape lane g2 found on the at-market broad families (the extreme reverts within one bar) at a different timescale. (2) The coupling AD documented — these two sleeves read the stop distance in their entry signal — means the usual stop-ladder repair is INVALID here and any future work must re-run the generator, not re-label. Anyone who forgets that will produce a look-ahead artifact and call it an improvement.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_us30_cash_d1_volume_surge_reversal` — **SOUND_BUT_TOO_SMALL**

**Premise.** The US30 cash index that moves on abnormally high daily volume reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Positive at all four cost bands, 4 of 5 folds positive, fails on SIGNIFICANCE ALONE — but fires ~16 times a year on one instrument, so no amount of contract work changes the answer: sample-starved, not broken.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 9, horizon inert at 80. Median MFE +1.20/+1.47/+1.20 R across the trio; 2R reached by 36.4%/42.7%/38.0%. AQ's repair was NEGATIVE for ger40 (-0.1234) and us30 (-0.0837) and POSITIVE for jp225 (+0.0412) — two of three want the first day only and one wants the full research horizon, ON THE SAME RULE AND THE SAME CONSTANTS. That split is the cleanest evidence in the cohort that the horizon is a per-instrument property the shared machinery cannot express.

**Life cycle.** 110-121 trades each, 15.7-18.3/yr each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |
| gated trades | 121 (17.3/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 9.0) |
| resolved inside entry bar | 0.2314 | exceeding live horizon | 0.0000 |
| median MFE | 1.200 R | exit mix | {'stop': 0.6198, 'target': 0.3802} |
| ratified gate (mid band) | REJECT | R/day | 0.1449 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.78 |
| IR at own hold (the idea) | 0.0867 | cost_r (cost geometry) | 0.102 |
| TIGHT = stop/sigma (stop geometry) | 0.511 | RATIO signal/toll | 1.661 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 142.55 − toll 51.19 = **91.36 bps** | CI95 | [-58.88, 255.89] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 121 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** THE ONE REPAIR THAT IS BOTH CHEAP AND PRINCIPLED IS A POOLING REPAIR, NOT A PER-SLEEVE ONE. Eight of the fourteen mx sleeves are the identical volume-surge rule with identical constants; six are cash indices. Declaring 'D1 volume-surge reversal on cash indices' as ONE member with six carriers, pooled, is a single hypothesis with ~100 trades a year instead of six hypotheses with sixteen each — the only structure that can clear a family bill on this rule. AF's coherence test is the existing instrument for deciding whether that pooling is legitimate and IT HAS NEVER BEEN RUN ON THE mx COHORT. If the pooled member is built, its horizon must be a DECLARED property of the pool, not inherited.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_us500_cash_d1_atr_mean_reversion` — **SOUND_BUT_TOO_SMALL**

**Premise.** The US500 cash index whose previous daily return exceeded 1.25x its own recent average true range reverses the next day.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** Eleven trades a year. AU declared a one-day horizon for both at time_stop_m15(1,'D1'), wired and default-off.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 9-10; horizon inert at 80. Median MFE +1.15 R; 2R reached by 29.8% — the two worst rates of the ten. AQ's repair from the 1-bar accident was worth -0.5567 R/day — by far the largest NEGATIVE deltas in the cohort, so both sleeves are strongly better on a ONE-DAY hold and AU declared exactly that.

**Life cycle.** 67-71 trades each, ~11/yr each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |
| gated trades | 67 (11.2/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 9.0) |
| resolved inside entry bar | 0.1343 | exceeding live horizon | 0.0000 |
| median MFE | 1.145 R | exit mix | {'stop': 0.7164, 'target': 0.2836} |
| ratified gate (mid band) | REJECT | R/day | 0.0990 |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.26 |
| IR at own hold (the idea) | 0.0159 | cost_r (cost geometry) | 0.090 |
| TIGHT = stop/sigma (stop geometry) | 0.573 | RATIO signal/toll | 0.307 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=16.0 h** | drift 6.82 − toll 4.62 = **2.21 bps** | CI95 | [-50.50, 52.40] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 67 |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** The horizon question has been asked and answered for this pair and the answer is unusually clean — one day, declared, wired, default-off, worth +0.59 and +0.56 R/day against the 80-bar contract. What cannot be repaired at this scale is the sample. TWO OBSERVATIONS. (1) THE ONE-DAY RESULT IS THE MOST INTERESTING THING IN THE COHORT and it is not being read that way: a mean-reversion entry whose entire value is in the first day, with the second day actively giving it back, is a statement about how long the reversion lives — and it is the same shape lane g2 found on the at-market broad families (the extreme reverts within one bar) at a different timescale. (2) The coupling AD documented — these two sleeves read the stop distance in their entry signal — means the usual stop-ladder repair is INVALID here and any future work must re-run the generator, not re-label. Anyone who forgets that will produce a look-ahead artifact and call it an improvement.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_aus200_cash_d1_volume_surge_reversal` — **STALE**

**Premise.** The ASX 200 cash index reverses the day after an abnormally high-volume daily move.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** NEGATIVE in their own birth ledger after swap.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Not measurable: no archive series, no profile mapping, so the resolver produces a name that is on neither broker.

**Life cycle.** 0 rows anywhere. They are the two rows that make registry.py declare 34 SleeveSpecs while the system runs 32.

**Verdict — STALE. Repair.** DELETE BOTH. Four independent reasons and any one is sufficient: negative in their own birth ledger after swap; excluded by the only policy any configuration selects; no archive series so no gate can ever score them; and no profile mapping so the resolver produces a name on neither broker. Every reader who counts the registry has to discover the 34-vs-32 discrepancy for themselves. The one thing worth keeping before deletion is the collision record — mx_aus200_cash_d1_volume_surge_reversal beat mx_aus200_cash_d1_atr_mean_reversion on repaired full-book delta, which is a genuine piece of evidence hygiene worth one line in the cohort's design note.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_spn35_cash_d1_volume_surge_reversal` — **STALE**

**Premise.** The IBEX 35 cash index reverses the day after an abnormally high-volume daily move.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** NEGATIVE in their own birth ledger after swap.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Not measurable: no archive series, no profile mapping, so the resolver produces a name that is on neither broker.

**Life cycle.** 0 rows anywhere. They are the two rows that make registry.py declare 34 SleeveSpecs while the system runs 32.

**Verdict — STALE. Repair.** DELETE BOTH. Four independent reasons and any one is sufficient: negative in their own birth ledger after swap; excluded by the only policy any configuration selects; no archive series so no gate can ever score them; and no profile mapping so the resolver produces a name on neither broker. Every reader who counts the registry has to discover the 34-vs-32 discrepancy for themselves. The one thing worth keeping before deletion is the collision record — mx_aus200_cash_d1_volume_surge_reversal beat mx_aus200_cash_d1_atr_mean_reversion on repaired full-book delta, which is a genuine piece of evidence hygiene worth one line in the cohort's design note.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_avausd_d1_donchian_20_breakout` — **UNDETERMINED**

**Premise.** Avalanche that closes above its own prior 20-day high keeps going.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** THE LOWEST RAW p OF ANY mx SLEEVE — 0.0030, better than mx_btcusd's 0.0106 — with 5 of 5 positive folds and q 0.2001. And the estate CANNOT evaluate it at the ratified rule because only 34 of its 189 trades fall on RECORDED eras.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** Median hold 3 D1 bars, p90 14; horizon inert. Median MFE +1.31 R; 39.7% reach 2R. Its best exit cell is the ONLY trail cell to win anywhere in the cohort (trail_a1_g0.5_prod) — a different geometry from every other mx sleeve, and it was not followed up.

**Life cycle.** 189 trades, 31.5/yr. NOT_EVALUABLE at the ratified population rule. redacted_account cannot trade AVAUSD, so it can only ever be a single-account sleeve.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `crypto_alt_or_major` |
| gated trades | 189 (31.5/yr) | grid | D1 |
| declared horizon | 80.0 own bars | realised median hold | 3.0 own bars (p90 14.0) |
| resolved inside entry bar | 0.2169 | exceeding live horizon | 0.0000 |
| median MFE | 1.312 R | exit mix | {'stop': 0.5926, 'target': 0.3968, 'maxbars': 0.0106} |
| ratified gate (mid band) | NOT_EVALUABLE | R/day | — |
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.69 |
| IR at own hold (the idea) | 0.0281 | cost_r (cost geometry) | 0.090 |
| TIGHT = stop/sigma (stop geometry) | 0.609 | RATIO signal/toll | 0.512 |
| realised resolution T_res | 72.00 h | drift argmax T_peak | 0.2 h |
| **ceiling at h\*=16.0 h** | drift 54.56 − toll 33.78 = **20.78 bps** | CI95 | [-132.73, 173.95] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 189 |

**Verdict — UNDETERMINED. Repair.** THE MOST INTERESTING UNRESOLVED CELL IN THE COHORT AND NOBODY HAS SAID SO. Three things follow. (1) The right question is a COVERAGE question, not an economics one: why does AVAUSD have 155 of 189 trades outside RECORDED, and is that a property of the instrument's era coverage rather than of the sleeve? Answerable from POPULATION_RULE_V1.json's own conditions in under a session. (2) Its winning cell is a TRAIL, unique in the cohort, and no one asked whether the trail is the reason or an artifact of 189 rows. (3) I am DELIBERATELY NOT calling this sound: a p of 0.0030 on the one cell the ratified rule cannot see is exactly the shape of a false positive, and saying so is more useful than promoting it.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_eu50_cash_d1_volume_surge_reversal` — **UNDETERMINED**

**Premise.** The EURO STOXX 50 cash index reverses the day after an abnormally high-volume daily move.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** These two carried 22% of their own book's birth evidence — the highest exact-M1 event count and the highest ordered mean R — and have ZERO rows in every modern artifact.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** UNKNOWN. Not measurable from anything on this machine: no archive series exists for EU50.cash or FRA40.cash.

**Life cycle.** 0 trades in every estate artifact. Live-configured at 0.03 confidence each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |

**Verdict — UNDETERMINED. Repair.** THE ESTATE HAS TWO LIVE-CONFIGURED SLEEVES IT CANNOT MEASURE AND THEY CARRIED 22% OF THEIR OWN BOOK'S BIRTH EVIDENCE. That combination is the single most uncomfortable fact in the mx cohort, because it means the market-expansion book's strongest birth members are precisely the ones no later measurement has touched. THE REPAIR IS A DATA FETCH, not a sealed window: D1 series for two FTMO index CFDs, the cheapest possible acquisition, and it would let EXIT_FRONTIER, AQ and AU all recompute with no new code. Until then neither sleeve should appear in any published count of 'measured' market-expansion members and the cohort's aggregates should be stated as TEN OF TWELVE. Second: nobody has checked whether the FTMO EU50/FRA40 daily bars even align with the exchange session the volume-surge rule assumes — the same fixed-UTC-versus-exchange-session defect lane g4 found in session_open_range_break.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`

### `mx_fra40_cash_d1_volume_surge_reversal` — **UNDETERMINED**

**Premise.** The CAC 40 cash index reverses the day after an abnormally high-volume daily move.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth vs known now.** These two carried 22% of their own book's birth evidence — the highest exact-M1 event count and the highest ordered mean R — and have ZERO rows in every modern artifact.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry vs premise.** UNKNOWN. Not measurable from anything on this machine: no archive series exists for EU50.cash or FRA40.cash.

**Life cycle.** 0 trades in every estate artifact. Live-configured at 0.03 confidence each.

| | | | |
|---|---|---|---|
| confidence | 0.03 | corr-cluster | `indices_context` |

**Verdict — UNDETERMINED. Repair.** THE ESTATE HAS TWO LIVE-CONFIGURED SLEEVES IT CANNOT MEASURE AND THEY CARRIED 22% OF THEIR OWN BOOK'S BIRTH EVIDENCE. That combination is the single most uncomfortable fact in the mx cohort, because it means the market-expansion book's strongest birth members are precisely the ones no later measurement has touched. THE REPAIR IS A DATA FETCH, not a sealed window: D1 series for two FTMO index CFDs, the cheapest possible acquisition, and it would let EXIT_FRONTIER, AQ and AU all recompute with no new code. Until then neither sleeve should appear in any published count of 'measured' market-expansion members and the cohort's aggregates should be stated as TEN OF TWELVE. Second: nobody has checked whether the FTMO EU50/FRA40 daily bars even align with the exchange session the volume-surge rule assumes — the same fixed-UTC-versus-exchange-session defect lane g4 found in session_open_range_break.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_VERDICTS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x1_receipts/X1_CEILING_V1.json`


## Section H — registered for sizing, no generator (1)

### `session_leadlag_genuine` — **IMPLEMENTATION_WRONG**

**Premise.** A session lead-lag effect between two different symbols.

**Origin.** Registered for SIZING at confidence 0.15 in CLEAN4_REGISTRY (admission.py:265-277) with a generator module present (src/components/ultimate_book/sleeves/session_leadlag.py) that sleeves/registry.py NEVER IMPORTS.

**Claimed at birth vs known now.** A claimed forward +0.46 R on n=390, additive on the vol-matched stress MC, Sharpe 0.1522 -> 0.1586. Its cited artifact AA_ESTATE_WALK_RESULT.md resolves to NO FILE at HEAD.

**Parameters.** Unknown — it can never fire.

**Geometry vs premise.** Unmeasurable.

**Life cycle.** A 33rd SLEEVE NOBODY HAS COUNTED. It can be SIZED and can NEVER FIRE. Because CANDIDATE_BOOK_V1 is built from active_specs it is not a family member, so its look is NOT BILLED — the estate took a look and did not pay for it. Its blocker is real and documented: the generator contract (registry.py:37) hands one symbol plus at most one same-symbol aux feed, and this sleeve needs a cross-symbol channel (supply.py -> LIVE_WIRING_GAP).

**Verdict — IMPLEMENTATION_WRONG. Repair.** EITHER remove it from CLEAN4_REGISTRY (it cannot contribute) OR extend the generator contract to a cross-symbol channel and then declare and bill the look. Doing neither is the current state and it is the worst of the three: a sizing weight with no possible generator output and an unbilled look.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/x2_receipts/X2_WHY_DID_WE_BUILD_THESE.md; src/components/ultimate_book/admission.py:265-277`


## Section I — the broad-V4 POI frameworks (3 families)

### `current_breaker_re_entry` — **GEOMETRY_WRONG**

**Premise.** An order block that failed and was traded through flips polarity: the zone that was demand now acts as supply and holds on re-entry.

**Origin.** Added 2026-04-25 by 64d05b8950c4e338358002a09933db980379221d, 'feat(breaker_re_entry): activate explicit framework alongside ob_retest for FTMO challenge' — 1,798 lines, 17 verification tests, 9 canary fixtures. Ported 2026-07-12 in 954f5a15.

**Claimed at birth vs known now.** The best-argued of the three at birth (explicit tests and fixtures), but no return, sample or out-of-sample split was offered.

**Parameters.** risk.sl_buffer_breaker_atr_multiplier: 0.5 EXISTS in config and is read by NO broad-V4 code; the family therefore gets 23.9% of its specified stop. risk.sl_buffer_min_ticks: 5 likewise never read. Entry at midpoint where B-PARAMS says near edge.

**Geometry vs premise.** Zone age at emission median 68.25 h, p95 192.8 h — the oldest of the three; only 1.3% are <=5 h. BreakerBlock (src/models/market_state_models.py:65-75) carries NO invalidation field, so a zone price has blown through is still emitted.

**Life cycle.** 95,051 emissions; 26.19% born already past their own stop, 62.32% target-through, 65.62% off-session, 95.55% irrelevant by construction.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.32 |
| IR at own hold (the idea) | 0.0176 | cost_r (cost geometry) | 0.278 |
| TIGHT = stop/sigma (stop geometry) | 0.082 | RATIO signal/toll | 0.774 |
| realised resolution T_res | 18.25 h | drift argmax T_peak | 72.0 h |
| **ceiling at h\*=72.0 h** | drift 2.48 − toll 2.06 = **0.42 bps** | CI95 | [-9.76, 9.63] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 95051 |
| emissions (8 windows) | 95,051 | **irrelevant by construction** | **95.55 %** |
| off-session 65.62 % · born past stop 26.19 % | | target already behind 62.32 % · stale bar 3.92 % | |

**Verdict — GEOMETRY_WRONG. Repair.** THE MOST REPAIRABLE FAMILY IN THE BROAD LANE. Remove the born-past-stop bin and the honestly-formed resting limits show MFE/MAE 1.033/1.082/1.091/1.111 at 120/480/1440/4320 min — ABOVE the at-market reference at every horizon, n=3,433. Its -0.391 whole-family reading is an artifact of the 26% born past stop. Repairs, all already specified: read the 0.5 H1-ATR buffer (4.18x wider stop); add an invalidation field; set poi_state_required. r2 has already landed the past-stop refusal and the family moves -0.36457 -> -0.04011 R/emission. Still economically negative at 7.9 bps.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_THREE_POI_FAMILIES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r2/R2_CENSUS_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/SESSION_R2_GENERATOR_REPAIR.md`

### `current_fvg_fill` — **IDEA_WRONG**

**Premise.** Price retraces into the fair-value gap left by an aggressive move and then resumes in that move's direction.

**Origin.** String present in the repo's first commit 436c16bd (2026-03-29); framework narrative 744c908a (2026-03-30); ported into the broad-V4 generator 2026-07-12 in 954f5a1573b73615324500d78d316f3a78709096, a 2,845-file commit titled 'chore(storage): establish non-iCloud GTOS hot workspace snapshot' with no design note.

**Claimed at birth vs known now.** Its founding evidence was never about a standalone entry: it is a +7-20pp quality FEATURE on the order-block retest (2026-03-30 spec F4-A). Tested as a feature here it reproduces at +5.02pp (42.06% vs 37.05% at 1.5R, p 0.101, 4/6 months).

**Parameters.** Proximity 1.0% of price (an API-cost prescreen, provenance in commit 2be9fced); entry at zone midpoint; stop buffer applied to M15 ATR where ADR-006 defines it in H1 ATR (ratio measured 2.091). 0 of its own spec's 4 conditions (F1-F4) are implemented.

**Geometry vs premise.** Zone age at emission median 12.25 h, p95 171.5 h against its own spec's 3 h recency window (23.6% conform). Fill to 1.5R-or-stop: median 7 min. Stop 7.42 bps.

**Life cycle.** 700,947 emissions collapse to 20,900 POI identities; 84.28% target-through, 76.76% off-session, 96.80% irrelevant by construction.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.29 |
| IR at own hold (the idea) | 0.0039 | cost_r (cost geometry) | 0.271 |
| TIGHT = stop/sigma (stop geometry) | 0.076 | RATIO signal/toll | 0.192 |
| realised resolution T_res | 9.25 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 7.79 − toll 2.01 = **5.78 bps** | CI95 | [-6.35, 17.33] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 670717 |
| emissions (8 windows) | 700,947 | **irrelevant by construction** | **96.80 %** |
| off-session 76.76 % · born past stop 0.00 % | | target already behind 84.28 % · stale bar 6.88 % | |

**Verdict — IDEA_WRONG. Repair.** REPAIRABLE AS A FEATURE, NOT AS A FAMILY. Demote to a boolean on current_ob_retest — the form its own evidence supports. Worth: removes 57.9% of the estate's POI emission volume and the multiplicity that rides on it. It still misses economically: cost-true breakeven at 1.5R is 47.2%, the conditioned cohort reaches 42.06%.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_THREE_POI_FAMILIES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_FEATURE.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_CENSUS.json`

### `current_ob_retest` — **SOUND_BUT_TOO_SMALL**

**Premise.** After a structural break, price returns to the last balanced zone before the break and continues in the break's direction.

**Origin.** Hand-written framework narrative in 744c908a (2026-03-30, 'Multi-framework PA (4 setups)'); ported into the broad-V4 generator 2026-07-12 in 954f5a15, the same one-line 'chore(storage)' commit.

**Claimed at birth vs known now.** Founding study: first-touch continuation 72.7% on n=23,575 vs 31.5% on n=82,572 for touch-2+. Its trade contract was target 1.25xATR / stop 0.5xATR (2.5R) over 20 H1 bars.

**Parameters.** Proximity 1.0%; entry at zone midpoint where the spec says near edge ('Do NOT use the current candle close price'); ATR key defined in M15 so this family alone is conformant. Touch filter (gate1.touch_count_reject_threshold: 2) stranded on the LLM path.

**Geometry vs premise.** Zone age at emission median 33.50 h, p95 191.5 h; only 26.9% are <=10 H1 bars old. Shipped contract 1.5R resolved in a median 33 min against a founding contract of 2.5R over 20 H1 bars. Stop 9.13 bps.

**Life cycle.** 270,354 emissions for 5,296 zones (~38x identity inflation); 91.55% target-through, 65.26% off-session, 97.01% irrelevant by construction.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.53 |
| IR at own hold (the idea) | -0.0350 | cost_r (cost geometry) | 0.178 |
| TIGHT = stop/sigma (stop geometry) | 0.080 | RATIO signal/toll | -2.463 |
| realised resolution T_res | 37.75 h | drift argmax T_peak | 1.0 h |
| **ceiling at h\*=1.0 h** | drift 0.13 − toll 1.58 = **-1.45 bps** | CI95 | [-1.70, -1.17] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 270354 |
| emissions (8 windows) | 270,354 | **irrelevant by construction** | **97.01 %** |
| off-session 65.26 % · born past stop 0.13 % | | target already behind 91.55 % · stale bar 3.89 % | |

**Verdict — SOUND_BUT_TOO_SMALL. Repair.** REPAIRABLE IN COHORT, NOT IN SIZE. (a) age gate <=10 H1 bars (costs 73.1% of emissions, restores the cohort the evidence describes); (b) carry the touch filter across; (c) restore near-edge entry (+71% relative fill at 1.6x risk distance); (d) restore the 2.5R/20-H1-bar geometry. What it will NOT fix: at 9.13 bps the toll is 0.181 R/fill and cost-true breakeven at 1.5R is 47.2%. This idea's home is a contract where one R is 44-436 bps, not 9.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_THREE_POI_FAMILIES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_CENSUS.json`


## Section J — the broad-V4 production origin families (10 families)

### `liquidity_sweep_reclaim` — **GEOMETRY_WRONG**

**Premise.** Price runs the prior 20-bar high, fails, and closes back inside the range; the trapped breakout buyers become fuel for the move down.

**Origin.** d6f09c5a2 (2026-05-26), same coverage-boxing registry. Generator built the next day, 69d000fb3 (2026-05-27), src/components/broader_origin_generators.py:713-745.

**Claimed at birth vs known now.** The registry that commissioned it SPECIFIED M1/M5/M15 data and an EVENT-TIME clock. The generator reads M15 CLOSES ONLY and fires on bar_close. Both requirements its own specification named were dropped and nothing records the decision. STAGE13 reported +0.20175 R/trade over 100,326 rows — 7x the best subsequent measurement.

**Parameters.** 20-bar lookback; sweep wick + 0.25 x ATR14 buffer (the copied constant; here it is 28.3% of the stop and the wick is 70.2%, so this is the one structurally-derived stop in the lane); target = min_rr.

**Geometry vs premise.** THE MISMATCH IN MINUTES: the premise is a 1-to-5-MINUTE event (a stop run and an immediate reclaim); the detector resolution is 15 MINUTES (both legs must fall inside one M15 bar); realised median time to resolution 25 minutes; and the contract has NO time stop at all. The detector is 3-15x coarser than the event it looks for.

**Life cycle.** 43,751 emissions; 59.98% off-session, 60.09% irrelevant by construction. 100% resting-at-market with 0% past-stop and 0% target-through — structurally the cleanest emitter in the broad estate.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 1.12 |
| IR at own hold (the idea) | 0.0151 | cost_r (cost geometry) | 0.370 |
| TIGHT = stop/sigma (stop geometry) | 0.262 | RATIO signal/toll | 0.156 |
| realised resolution T_res | 0.50 h | drift argmax T_peak | 2.0 h |
| **ceiling at h\*=2.0 h** | drift 0.78 − toll 2.89 = **-2.11 bps** | CI95 | [-3.43, -0.69] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 43751 |
| emissions (8 windows) | 43,751 | **irrelevant by construction** | **60.09 %** |
| off-session 59.98 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 2.49 % | |

**Verdict — GEOMETRY_WRONG. Repair.** Delete the fixed take-profit: +0.5110 bps [+0.3059,+0.7127] at 2 h and +1.4958 [+0.7927,+2.1450] at 24 h, taking it from significantly negative to significantly positive (+0.9163 [+0.245,+1.641], 4/5 quarters). THEN BUILD THE DETECTOR ON M1/M5 AS ITS OWN FOUNDING REGISTRY SPECIFIED — this is UNPRICED and it is the one unpriced thing in the broad estate worth pricing, because every measurement so far tests the M15 transcription of the idea and none tests the idea. Ceiling as it stands +0.92 bps against a 3.02 bps toll: a research question, not a book.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g3_receipts/a15_final.py; research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl`

### `regime_transition_break` — **GEOMETRY_WRONG**

**Premise.** When a market crosses from not-trending into a strong trend and simultaneously breaks its recent range high, it keeps going.

**Origin.** Registry d6f09c5a2 (2026-05-26); implementation and activation 69d000fb3 (2026-05-27). Registry row STAGE05-ORIGIN-010.

**Claimed at birth vs known now.** Its own birth registry REQUIRED H1/H4/D1 OHLC + regime_classifier_state. It shipped on M15 — 16x to 96x too fast, and the violation is written in the artifact that authorised it. STAGE13 gave it 240 rows = 0.26% of available; at family level it was already measured NEGATIVE on all nine exit policies.

**Parameters.** Trend-score thresholds <0.75 -> >=2.0 over a 5-hour lookback; stop 0.10 x ATR14 (shared with session_open_range_break and three sleeve modules); target = min_rr. Never validated out of sample.

**Geometry vs premise.** CATASTROPHIC AND SELF-DECLARED. Its 'transition' is the 5-hour trend score jumping between two ADJACENT 15-minute bars. Trigger bar median range 2.442 x ATR50 — the largest in the module — and entry sits at the 0.890 quantile of that bar's own range. It is a single-largest-bar detector wearing a regime name, and it buys the high.

**Life cycle.** 2,320 emissions; 46.34% off-session, 46.34% irrelevant by construction. Realised p(target first) 0.397 vs 0.400 breakeven — calibrated to lose by 0.3 pp before one basis point of cost. Accumulation 2h->320h = 0.170x. 92.6% of its emissions duplicate another family's same-symbol same-bar same-side proposal.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.15 |
| IR at own hold (the idea) | 0.0077 | cost_r (cost geometry) | 0.074 |
| TIGHT = stop/sigma (stop geometry) | 0.354 | RATIO signal/toll | 0.294 |
| realised resolution T_res | 12.00 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 15.61 − toll 5.19 = **10.43 bps** | CI95 | [-13.10, 35.31] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 2318 |
| emissions (8 windows) | 2,320 | **irrelevant by construction** | **46.34 %** |
| off-session 46.34 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 0.47 % | |

**Verdict — GEOMETRY_WRONG. Repair.** Three repairs, priced. (1) ENTRY INSTANT — enter one bar later: +2.2949 bps/trade averaged over five horizons, flipping the sign at three of five and recovering 0.75 of its entire 3.070 bps toll, for 15 minutes. (2) DROP THE TRANSITION CLAUSE — the clean-room ablation without it has a 1-bar loss 6.3x smaller and a 16-hour figure 1.5x larger: the clause that gives the family its name is the value-destroying part. (3) Move to the registry's own H1/H4/D1 clock — NOT_EVALUABLE here (n=218 at H4). Best post-repair capture/toll ~1.26x with no CI excluding zero: a real repair on a family that remains untradeable.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_TRIGGER.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_DELAY.json; research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl`

### `session_open_range_break` — **GEOMETRY_WRONG**

**Premise.** After a session opens, the first N minutes define a range and the first decisive close outside it starts the day's directional move.

**Origin.** d6f09c5a (2026-05-26) registry row STAGE05-ORIGIN-009 (category session_clock, status not_first_class_candidate_origin); activated one day later by 69d000fb (2026-05-27).

**Claimed at birth vs known now.** NOT_FOUND. No research artifact anywhere justifies the idea with a return — searched git log -S across 8,992 commits on all refs, research/science_program_2026_05/, research/operations/**, .context/02_session_handoffs/, and a whole-tree rg. What exists is a MEASURED NEGATIVE on its own 240-row smoke (-0.11190 R, negative on 7 of 9 exit policies), shipped one day later.

**Parameters.** Session windows are fixed UTC HH:MM constants; range length 30 min is an accident of 'range_start_index + 1'; stop 0.10 x ATR14 (the copied buffer, also in regime_transition_break at :832/:850); target = min_rr = 2.0R.

**Geometry vs premise.** THREE mismatches. (1) WINDOW: constants are fixed UTC while every session they name moves on a DST calendar. Only 33 of 213 exchange-instrument emissions (15.5%) have an opening range containing their own cash open; 34.3% break out BEFORE their own market opens; NAS100|ny and SPX500|ny ranges are 60 min early. (2) TARGET: contract asks 2.0R, median MFE is 0.659R and only 9.5% of paths reach +2R within 2 h. (3) HOLD: mean R goes -0.0170 at 5 min to -0.1576 at 120 min, monotone.

**Life cycle.** 8,195 emissions; 0.00% off-session (it only fires inside its own windows), 0.00% stale — the ONLY broad family with a 0% irrelevant-by-construction rate. Its waste is not in the emission, it is in the window definition. 39.6% fire on the very first bar it is possible to fire on.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.77 |
| IR at own hold (the idea) | -0.0314 | cost_r (cost geometry) | 0.123 |
| TIGHT = stop/sigma (stop geometry) | 0.290 | RATIO signal/toll | -0.878 |
| realised resolution T_res | 3.00 h | drift argmax T_peak | 320.0 h |
| **ceiling at h\*=320.0 h** | drift 7.66 − toll 2.83 = **4.83 bps** | CI95 | [-18.03, 26.85] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 7876 |
| emissions (8 windows) | 8,195 | **irrelevant by construction** | **0.00 %** |
| off-session 0.00 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 0.00 % | |

**Verdict — GEOMETRY_WRONG. Repair.** Cheapest first: (1) anchor windows to exchange-local session opens via zoneinfo — recovers the 84.5% of exchange-instrument emissions whose range is not an opening range and removes the twice-yearly one-hour drift; a table and a tz lookup, no new data. (2) DECLARE the range length. (3) set the target from the family's own excursion. (4) do NOT lengthen the hold. WORTH: the entire same-cell residual is [-3.0,+4.0] bps against a 3.78 bps toll, so a repair must move gross by ~4 bps to matter and only (1) is that large — and it changes WHICH POPULATION is sampled rather than the size of an existing effect. A cheap re-measurement of a question nobody has asked, not a rescue.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_SCHEDULE_V1.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_FINAL_V1.json`

### `structural_distance_extreme` — **GEOMETRY_WRONG**

**Premise.** After price closes within 3% of its own 50-bar high (or low), it reverts back into the range.

**Origin.** NAME: d6f09c5a2 (2026-05-26) in src/research/universal_candidate_origin_registry.py — one of 16 rows in a COVERAGE-BOXING registry, not a strategy. GEOMETRY: 69d000fb3 (2026-05-27). Never changed since; only five commits have ever touched the file.

**Claimed at birth vs known now.** NO EDGE CLAIM AT BIRTH — a coverage argument: boxes_out_if_missing='geometry extremes remain prompt context instead of candidate origins', activation_status='research_registry_only_no_runtime_candidate_generation_change', default_off=true. STAGE13 then reported +1.196255 R/trade at an 83.7% win rate over 53,415 rows — 18x the best subsequent measurement and the opposite sign. Never retracted.

**Parameters.** pos50 >= 0.97 (arbitrary); stop = bar.high + 0.25 x ATR14 — a COPIED constant that is a buffer in liquidity_sweep_reclaim (28.3% of its stop) and IS the stop here (71.0%), because pos50>=0.97 forces the wick term near zero by construction. Target = min_rr. _atr is mean(high-low), not true range, so it cannot see a gap.

**Geometry vs premise.** Premise is a reversion idea with no natural timescale; contract is a 3.05 bps stop / 6.09 bps target on an M15 clock. MEDIAN TIME TO RESOLUTION 5 MINUTES; median time to stop 3 minutes. The median trade lives and dies inside one third of the M15 bar that generated it.

**Life cycle.** 23,923 emissions; 64.42% off-session, 64.42% irrelevant by construction. past_stop and duplicate rates are essentially zero (1.46%) — for THIS family Borhen's 'already irrelevant' is precisely false at the order level and precisely true at the gate level.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.38 |
| IR at own hold (the idea) | 0.0028 | cost_r (cost geometry) | 0.807 |
| TIGHT = stop/sigma (stop geometry) | 0.113 | RATIO signal/toll | 0.031 |
| realised resolution T_res | 0.25 h | drift argmax T_peak | 2.0 h |
| **ceiling at h\*=2.0 h** | drift 0.35 − toll 2.52 = **-2.17 bps** | CI95 | [-3.98, -0.28] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 23923 |
| emissions (8 windows) | 23,923 | **irrelevant by construction** | **64.42 %** |
| off-session 64.42 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 3.43 % | |

**Verdict — GEOMETRY_WRONG. Repair.** Shipped contract is SIGNIFICANTLY VALUE-DESTROYING: -0.2505 bps/trade [-0.4145,-0.0807], 1 of 5 quarters positive. Deleting the take-profit flips it to +0.4118 [+0.0750,+0.7814], 4 of 5 quarters — a +0.6623 bps repair on identical rows. AND THE REPAIR DOES NOT MAKE IT TRADEABLE: +0.41 bps against a 3.02 bps toll is 7.3x short. Widening the stop is worth ZERO (+0.0329 bps [-0.3460,+0.4349] on 28,268 paired rows). Strike the STAGE13 birth claim at source; do not enable or size it.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g3_receipts/a15_final.py; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g3_receipts/a17_paired.py`

### `volatility_compression_expansion` — **GEOMETRY_WRONG**

**Premise.** After a period of compressed volatility, the first bar that expands and breaks the recent range starts a directional move.

**Origin.** First named as a gap 2026-05-12 (a191f5be1/d01d30c25); registered d6f09c5a2 (2026-05-26); implemented and activated 69d000fb3 (2026-05-27). Block src/components/broader_origin_generators.py:797-833.

**Claimed at birth vs known now.** STAGE13's 240-row cap = 4.32% of available executable rows; kept only in-sample-positive cells. Lane09 Meta-Selector V2 (13c038130, 2026-06-01) issued it a REDUCE verdict five days after it shipped and nothing acted on it.

**Parameters.** 20-bar channel and squeeze percentile inherited whole; stop 0.20 x ATR14; target = min_rr. Its live D1 sibling vol_compression uses plateau-validated parameters on the same premise; none of them was carried across.

**Geometry vs premise.** THE NATURAL EXPERIMENT, AND THE MISMATCH IS 96x. The live sibling gives the same premise a prior-20-D1-BAR channel (20 trading days) and a 1,920-hour horizon; this family gives it a prior-20-M15-BAR channel (5 HOURS) and is scored inside 2 hours, by which point 86.9% of its trades have not resolved.

**Life cycle.** 5,341 emissions; 80.79% off-session — the highest in the estate — and 80.79% irrelevant by construction. Realised p(target first) 0.368 against a 0.400 breakeven. Accumulation 2h->320h = -11.60x, a SIGN FLIP: the only family whose signal inverts with holding.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.87 |
| IR at own hold (the idea) | -0.0201 | cost_r (cost geometry) | 0.106 |
| TIGHT = stop/sigma (stop geometry) | 0.312 | RATIO signal/toll | -0.611 |
| realised resolution T_res | 8.25 h | drift argmax T_peak | 160.0 h |
| **ceiling at h\*=160.0 h** | drift 12.29 − toll 4.63 = **7.66 bps** | CI95 | [-20.31, 34.36] |
| ceiling verdict | ceiling positive, CI includes 0 | n | 5341 |
| emissions (8 windows) | 5,341 | **irrelevant by construction** | **80.79 %** |
| off-session 80.79 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 1.89 % | |

**Verdict — GEOMETRY_WRONG. Repair.** REPAIR AS REPLACEMENT, NOT ADJUSTMENT. Its one apparent exception (+22.169 bps at 16 h inside configured sessions) dies on its own concentration audit: 90.0% from two crude symbols on 99 of 1,026 rows, 43.2% from a single day. Killed here so nobody finds it again. Repairs: restrict generation to the sessions admission accepts (81% of output is thrown away); fix the BTCUSD/ETHUSD name collision; delete the squeeze and expansion clauses (measurably value-destroying relative to the breakout they wrap) — at which point it is a plain 20-bar breakout with no distinguishing content. The PREMISE is not dead; its D1 sibling carries it. The M15 instantiation should be retired.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_SESS.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_CURVE.json`

### `microstructure_absorption_reversal` — **IMPLEMENTATION_WRONG**

**Premise.** At a range extreme, a bar with large volume and a small range is a limit wall absorbing the push, so fade it.

**Origin.** Mined 2026-06-12/13. Birth artifacts research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_MICROSTRUCTURE_{MINE_V1,VERIFICATION,GOLIVE_BOOK}.json — ALL DELETED FROM HEAD, recoverable at 86cccd08d.

**Claimed at birth vs known now.** THE BEST BIRTH EVIDENCE IN THE ESTATE: 356 cells tested, 19 BH survivors, a 10-setup go-live book with per-symbol breadth, subperiod stability, bootstrap p05, 2x cost stress and an untouched-2026 validation split; validated +0.14 to +0.74 R/trade OOS. Every candidate is stamped mined_family_evidence='ULTIMATE_MICROSTRUCTURE_GOLIVE_BOOK' (src/components/broader_origin_generators.py:586) and THAT STRING RESOLVES TO NO FILE AT HEAD.

**Parameters.** 2.5 x ATR, 48 and 20 carried onto an M15 series unchanged from an H4 spec. bar.volume on FX/CFDs is MT5 tick_volume — a count of price updates, not traded size: a proxy of a proxy, which the go-live book itself names as reason (3) that live will underperform.

**Geometry vs premise.** THE DOCSTRING SAYS 'Reconciles to research microstructure_engine.py'. IT DOES NOT, ON SIX DECLARED COUNTS: timeframe H4 -> M15; trend conditioning dropped (all 10 book cells are trend-conditional); relv >= 1.5 gate computed but never gated on; entry debounce dropped; 10-cell restriction dropped (it emits on both sides for every symbol); exit contract replaced (+12/+24 H4 bars and vol_exhaust -> target_rr on a 2.5 x M15 ATR stop). Only the two detector predicates and the number 2.5 survive.

**Life cycle.** ZERO emissions in 27,658 (January) and 0 in 24,239 (February). Its enable key moonshot_microstructure_origins_enabled (src/components/broader_origin_generators.py:316) appears in exactly one file in the repository — the generator that reads it.

**Verdict — IMPLEMENTATION_WRONG. Repair.** (a) DO NOT FLIP THE FLAG ON THE CURRENT CODE — the six defects compound in the same direction (more emissions, smaller stops, no conditioning). (b) Port it properly, which needs an H4 series generate_live_broader_origin_candidates does not have (timeframe='M15' hardcoded at src/components/broader_origin_generators.py:293) — that is a new generator, not a patch — or delete it under the cleanup policy. (c) CHEAPEST FIRST STEP, half a session: restore the three deleted artifacts from 86cccd08d so the provenance stamp resolves, and record the six-way divergence beside the code. WORTH: the largest per-trade claim attached to any dormant family in this estate and the only one with bootstrap p05, breadth counts and cost stress behind it.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_LIFECYCLE_V1.json; src/components/broader_origin_generators.py:293,:316,:586`

### `microstructure_vdelta_divergence` — **IMPLEMENTATION_WRONG**

**Premise.** A new range extreme printed while the last three bars' signed volume runs the other way is exhaustion, so fade it.

**Origin.** Identical to its sibling: mined 2026-06-12/13, same three artifacts, all deleted from HEAD, recoverable at 86cccd08d, same dangling provenance stamp at src/components/broader_origin_generators.py:586.

**Claimed at birth vs known now.** S5 is the detector the go-live book leans on hardest: 3 of its 10 cells are S5 (index|short|24|fixed, jpy_fx|short|24|vol_exhaust, metals|short|24|vol_exhaust). The book wrote its own haircuts down — size off the validated 0.14 R, not the 0.58 headline, and prune the thin silver legs — which is more than any other family in the broad estate did.

**Parameters.** Same H4 constants on an M15 series. vdacc weights tick-update counts by body-to-range ratio: a signed ACTIVITY proxy, not signed order flow.

**Geometry vs premise.** Same six-way divergence as S4, plus one of its own: the 3-bar signed-volume window is 45 MINUTES where the spec means 12 HOURS, measured against a range extreme also compressed from 8 days to 12 hours.

**Life cycle.** ZERO emissions in 27,658 (January) and 0 in 24,239 (February). Same absent enable key.

**Verdict — IMPLEMENTATION_WRONG. Repair.** Identical to S4: do not flip the flag on this code; port properly (needs an H4 series the generator does not have) or delete; as the half-session first step restore the three birth artifacts and record the divergence beside the code. If ported, size off the validated 0.14 R (jpy_fx short) and prune the thin silver legs — the book already says so.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; src/components/broader_origin_generators.py:293,:316,:586`

### `cross_asset_lead_lag` — **PARAMETERS_WRONG**

**Premise.** When a leading instrument makes a large move and its correlated partner has not yet moved, the partner catches up.

**Origin.** d6f09c5a (2026-05-26) registry row STAGE05-ORIGIN-014 (category cross_market_context, status risk_gate_context); activated 69d000fb (2026-05-27). Same coverage-map provenance: boxes_out_if_missing='cross-asset context can only size/block, not originate candidates'.

**Claimed at birth vs known now.** No return, sample or citation offered at birth. NOT_FOUND for any post-birth validation. Documented in the literature (Chan 1992 lead-lag, Hasbrouck information shares) — but at a sub-second-to-few-minutes half-life in liquid markets.

**Parameters.** Leader move threshold, lag_response <= 0.5 ATR admission gate, stop = the qualifying bar's own low/high +/- 0.25 x ATR14 (the copied buffer). LOOK-AHEAD: NONE, and conservatively so — the leader bar's information is complete a full bar before the decision.

**Geometry vs premise.** THE GATE BUILDS THE STOP THAT KILLS IT. The stop is anchored to the qualifying bar while the admission gate requires that bar to have barely moved, so close-minus-low is small BY THE CONDITION THAT QUALIFIES THE SETUP: the more strongly a candidate qualifies, the tighter its stop. Median stop 5.94 bps, mean toll 5.5508 bps = 0.93x the ENTIRE risk distance; mean cost_r 0.806; 18.9% of emissions carry cost > 1.0 R before anything happens. Mean MAE at bar 15 is -1.0044 R: the stop is one M15 bar of ordinary noise.

**Life cycle.** 21,678 emissions; 62.20% off-session, 4.54% stale, 62.68% irrelevant by construction.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.36 |
| IR at own hold (the idea) | 0.0069 | cost_r (cost geometry) | 0.537 |
| TIGHT = stop/sigma (stop geometry) | 0.219 | RATIO signal/toll | 0.058 |
| realised resolution T_res | 0.25 h | drift argmax T_peak | 2.0 h |
| **ceiling at h\*=2.0 h** | drift 0.31 − toll 3.22 = **-2.91 bps** | CI95 | [-4.67, -1.27] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 21678 |
| emissions (8 windows) | 21,678 | **irrelevant by construction** | **62.68 %** |
| off-session 62.20 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 4.54 % | |

**Verdict — PARAMETERS_WRONG. Repair.** THE PREMISE IS REFUTED AT ITS OWN TIMESCALE: the share moving in the leader's direction is 44.9%/46.7%/46.3%/48.4%/48.3% at 5/15/30/60/120 min — BELOW A COIN FLIP AT EVERY HORIZON. Repairs: (1) DECOUPLE THE STOP FROM THE QUALIFYING BAR (highest-value change in the g4 lane; at 1.5 ATR the toll falls to roughly a quarter on the FX legs); (2) delete NAS100, SPX500, ETHUSD (cost_r 3.40/3.66/1.79); (3) test the premise at its own timescale on the 263,894,769 verified ticks at /Users/borr/GTOSActive/vps-ticks-20260726/ — cheap, and it settles whether the 15-minute residual is the dead tail of a real effect. Repairs 1-2 make it MEASURABLE; only 3 can make it RIGHT, and it may come back refuted.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G4_FINAL_V1.json`

### `displacement_continuation` — **PARAMETERS_WRONG**

**Premise.** A bar that travels far and closes with a large body relative to recent range is an impulse, and price keeps moving in the impulse's direction.

**Origin.** Registry d6f09c5a2 (2026-05-26, 'research: build moonshot dynamic execution substrate checkpoint'); implementation and activation 69d000fb3 (2026-05-27, 'vnext: activate moonshot production replacement'). Block src/components/broader_origin_generators.py:769-787.

**Claimed at birth vs known now.** STAGE13 replay summary capped at 240 replayed rows = 1.67% of available executable rows; the activation allowlist kept only in-sample-positive cells, so the count with negative expectancy is ZERO by construction.

**Parameters.** Displacement threshold 1.5 x ATR14, stop 0.25 x ATR14 (a constant shared with 6 other modules), target from the global risk.min_rr = 1.5 sanity floor. None was chosen for this family; none has an out-of-sample record.

**Geometry vs premise.** Clock is RIGHT (M15, matching its own birth spec). Entry instant is wrong: its trigger selects bars closing at the 0.861 quantile of their own range, so it buys the high; mean adverse excursion reaches the FULL stop inside 2 h.

**Life cycle.** 39,517 emissions; 54.66% off-session, 2.22% stale, 54.93% irrelevant by construction. Realised p(target first) 0.397 against a 0.400 breakeven.

| | | | |
|---|---|---|---|
| **X1 mechanism** | **NO_SIGNAL** | max signed t across the ladder | 0.08 |
| IR at own hold (the idea) | -0.0012 | cost_r (cost geometry) | 0.195 |
| TIGHT = stop/sigma (stop geometry) | 0.274 | RATIO signal/toll | -0.023 |
| realised resolution T_res | 1.75 h | drift argmax T_peak | 16.0 h |
| **ceiling at h\*=16.0 h** | drift 1.85 − toll 3.19 = **-1.34 bps** | CI95 | [-4.36, 1.85] |
| ceiling verdict | CEILING NEGATIVE at every horizon | n | 39517 |
| emissions (8 windows) | 39,517 | **irrelevant by construction** | **54.93 %** |
| off-session 54.66 % · born past stop 0.00 % | | target already behind 0.00 % · stale bar 2.22 % | |

**Verdict — PARAMETERS_WRONG. Repair.** Three priced parameter repairs: (1) enter one M15 bar later, +0.3859 bps/trade uniformly; (2) raise displacement 1.5 -> 2.5 (monotone, better at every horizon 2-24 h, emissions 63,595 -> 11,314); (3) choose a target instead of inheriting min_rr. Combined ~+0.68 bps against a 3.156 bps toll — not enough to trade, and the ceiling is negative at every horizon.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_TRIGGER.json; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g2/G2_DELAY.json`

### `range_extreme_reversion` — **PARAMETERS_WRONG**

**Premise.** A close in the outer quartile of the recent range drifts back toward the middle of it over the next one to two hours.

**Origin.** NOT from the 2026-05-26 registry. Added later citing ULTIMATE_ORIGIN_DISCOVERY_MINE_V2 in its own source_fields (src/components/broader_origin_generators.py:677). That artifact is NOT ON DISK ANYWHERE at HEAD; it exists only in git at research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_ORIGIN_DISCOVERY_MINE_V2.json (86cccd08d, 41425481e).

**Claimed at birth vs known now.** THE ONLY GENUINE DISCOVERY ARTIFACT BEHIND ANY BROAD FAMILY. The miner scanned every M15 bar-close across a 46-symbol year, used day-clustered t across symbol-days, Benjamini-Hochberg Q=0.05 over all cells, an effect floor net of a measured spread proxy, and ONE out-of-time confirmation on pre-registered survivors — materially the rule the estate ratified six weeks later.

**Parameters.** Implements _prior_high/_prior_low(50) EXCLUSIVE where the mine used _close_position(...,48) INCLUSIVE. The exclusive form makes range_pos UNBOUNDED: min -1.684, max +3.403, with 9.04% of 276,246 emissions outside [0,1] — impossible under the cited definition, and 5.61% are breakouts being faded as range extremes. Thrust cap where the mine used a band.

**Geometry vs premise.** The mine's own geometry is a 1-2 h naked drift. The shipped contract is a fixed 2R target with no horizon. The two parameter deviations are HARMLESS IN EFFECT (in-[0,1] +0.0655 vs outside -0.0239) — which is itself the finding: the parameters do not match the evidence and it does not matter, because there is nothing there to protect.

**Life cycle.** ZERO emissions in 27,658 (January) and 0 in 24,239 (February). It is gated on runtime_cfg.get('moonshot_mined_origin_families_enabled', False) (src/components/broader_origin_generators.py:312-314) and that key is absent from config/agent_config.yaml and every profile. Fourteen months wired, never run.

**Verdict — PARAMETERS_WRONG. Repair.** Implement the mine's own predicate (_close_position(series,index,48) already exists three lines away), restore thrust as a band, and give it the 1-2 h naked-drift horizon its evidence actually has. MEASURED CEILING: +0.3040 bps at 2 h and +1.1546 [+0.2127,+2.2113] at 24 h with 5/5 quarters — the single best cell anywhere in the g3 lane, 1 of 42 tested, and still 1.87 bps short of the 3.02 bps toll. DO NOT ENABLE IT. The value of the repair is that it retires a fourteen-month-old unmeasured claim sitting in production source. The estate needs a register of wired-but-never-enabled generators; this is the entry that proves it.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md; src/components/broader_origin_generators.py:312-314,:677; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/g3_receipts/a15_final.py`


## Section K — shared machinery (not generators; both are code paths every family above rides)

### `machinery_POI_shared` — **IMPLEMENTATION_WRONG**

**Premise.** One code path proposes a resting limit at a price level all three POI families believe price will return to and react from.

**Origin.** Introduced whole in 954f5a1573b73615324500d78d316f3a78709096 (2026-07-12), a 2,845-file commit titled 'chore(storage): establish non-iCloud GTOS hot workspace snapshot', +1,342 lines to src/components/broader_origin_generators.py. Absent at 86cccd08 (2026-06-15). No design note, no cited research, no test named, no A/B, and no branch carries a granular version.

**Claimed at birth.** NOTHING. The specification survives (src/prompts/primary_analyzer_prompt.py + ADR-006) and is detailed; the code implements 0 of its per-family conditions.

**Parameters.** Entry = (zone_low + zone_high)/2 for all three (:1774), where both written specs that name an entry name the NEAR edge. Proximity 1.0% of price. Stop buffers applied to M15 ATR where ADR-006 defines them in H1 ATR (measured ratio 2.091, n=102,507). risk.sl_buffer_breaker_atr_multiplier: 0.5 and risk.sl_buffer_min_ticks: 5 are never read by any broad-V4 code.

**Geometry.** Measured on the M1 tape with the stop held fixed and only the entry moved: near-edge fills 28.8/11.6/36.4% at 11.20/14.82/13.63 bps; the shipped MIDPOINT 22.5/6.8/29.1% at 7.39/9.14/7.93 bps; far edge 17.9/4.1/24.5% at 3.18/3.27/2.01 bps. The midpoint optimises NEITHER leg — it forfeits 20-41% of the near edge's fills and still carries 2.3-4.0x the far edge's risk distance. Nothing in the repository argues for it.

**Life cycle.** 1,066,352 POI emissions over eight windows collapse to a few thousand zones for two of three families (candidate identity keys on poi_id when present and on candle_open_utc when not; only fvg_fill sets poi_id, so ~260,741 distinct candidate identities exist for 7,922 actual zones). Of 212,164 symbol-instants carrying any POI candidate, 31.2% carry 2+ families and 45.8% carry a LONG and a SHORT on the same symbol at the same instant — the port also deleted the design's deterministic 3-level tiebreaker, turning 'one winner per bar' into a two-sided book.

**Verdict — IMPLEMENTATION_WRONG. Repair.** THE PORT IS THE ROOT CAUSE AND IT WAS INVISIBLE. Repairs, cheapest first: (1) the far-side R gate is ALREADY WIRED AND OFF — broad_origin_emission_contract.py has DEFAULT_MAX_ADMISSION_GAP_R = None and its own docstring names the right value; setting gtos_vnext_runtime.broad_origin_poi_max_admission_gap_r = target_rr removes 84.3%/91.6%/62.3% of the three families' emissions with no new code. (2) restore near-edge entry. (3) fix the ATR timeframe conversion. (4) read the two unread risk keys. (5) carry the two validated quality gates off the LLM path (gate1.touch_count_reject_threshold: 2, evidence 72.7% vs 31.5%; filters.max_gap_pct: 1.5). (6) restore the tiebreaker. HONEST CAVEAT, which is r2's own: none of this saves the families — the correctly-formed resting-limit book still books -0.24981 R/fill. Do it because ~90% of the estate's POI candidate volume, and every multiplicity bill computed over that volume, is an artifact.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_THREE_POI_FAMILIES_DOSSIER.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/SESSION_R2_GENERATOR_REPAIR.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/G1_FILL.json`

### `machinery_mx_shared` — **IMPLEMENTATION_WRONG**

**Premise.** One D1 code path proposes three rules — a 20-day Donchian breakout, a volume-surge reversal, and an ATR mean reversion — computed on the last completed daily bar and entered at the next daily open.

**Origin.** 96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT (ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot recorded the package as 'materially built as a default-off code/research package, but not live authority' with five requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).

**Claimed at birth.** All 21 of its own research routes closed promotion_ready: false with five named requirements open, and the config was set true the same day.

**Parameters.** Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 (market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).

**Geometry.** D1 clock matches the D1 premise. Horizon 7,680 M15 bars = 80 D1 bars = 1,920 h after AQ's unit repair; realised median hold 3 D1 bars and frac_over_live_horizon 0.0000 on all ten that trade — the horizon is INERT. Entry timing is deliberate and CORRECT ('signal from the latest completed D1 bar, intent stamped for the next D1 session/open'), which avoids the entry-at-the-extreme defect lane g2 found across the broad-origin families.

**Life cycle.** 10 of 14 sleeves produce rows; 2 have no archive series; 2 have neither series nor profile mapping. Registry declares 34 SleeveSpecs while the system runs 32.

**Verdict — IMPLEMENTATION_WRONG. Repair.** THE VERDICT IS ABOUT WIRING AND GOVERNANCE, NOT ABOUT THE THREE RULES — Donchian breakout, volume-surge reversal and ATR mean reversion are all documented effects and the D1 clock is right for all three. What is wrong is that a book whose every artifact says NOT PROMOTED, with five requirements open by name and never closed, is true in config and carries 0.30 of registry confidence weight for a measured +0.022 %/month. Three repairs, cheapest first: (1) CLOSE OR CITE MX-READINESS-REQ-001..005 — they ARE published at .context/00_core/research_current_state.md:513-517 and NOTHING AT HEAD CLOSES THEM; half a session of archaeology and the highest-value item here. (2) VENDOR THE EVIDENCE OR DELETE THE CLAIM — the 21 routes are on two VPS branches HEAD cannot reach; 41425481e already set the precedent. (3) RENAME OR RE-KEY activation_weight_now: a field that reads 0.0 on every sleeve that is being sized is a trap, the same class of unit-vs-value confusion AQ found in time_stop_bars.

*Evidence:* `/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/S2_REGISTRY_DOSSIERS.md; /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase20/provenance/s2_receipts/S2_REGISTRY_DOSSIER_V1.json; src/components/ultimate_book/sleeves/market_expansion_d1.py; .context/00_core/research_current_state.md:513-517`

---

## Appendix — the master geometry table

Every generator with a measurable contract, one row each. Sorted by `RATIO` (signal at its own
realised hold ÷ its own broker toll). **`RATIO` ∝ IR / (TIGHT × cost_r)** — verified as an identity
to three decimals on all 39 rows.

`X1_VERDICTS_V1.json`. `T_res` = realised median time to resolution (h). `T_peak` = horizon at
which placebo-controlled drift is largest (h). `max t` = largest signed t across the 11-rung ladder.

| generator | class | mechanism | IR | TIGHT | cost_r | **RATIO** | T_res | T_peak | stop bps | max t |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `sub_xvol_pullback` | SLEEVE | TOO_SHORT | 0.4818 | 0.410 | 0.144 | **8.178** | 64.00 | 320.0 | 197.72 | 3.54 |
| `crypto` | SLEEVE | CONTRACT_OK | 0.2157 | 0.322 | 0.146 | **4.580** | 52.00 | 72.0 | 376.00 | 2.07 |
| `sub_mid_dn_revert` | SLEEVE | TOO_SHORT | 0.2146 | 0.368 | 0.144 | **4.064** | 28.00 | 320.0 | 44.07 | 2.96 |
| `energy_agri` | SLEEVE | NO_SIGNAL | 0.2337 | 0.310 | 0.212 | **3.556** | 48.00 | 160.0 | 258.15 | 1.50 |
| `mx_ethusd_d1_donchian_20_breakout` | SLEEVE | TOO_SHORT | 0.2112 | 0.591 | 0.103 | **3.464** | 72.00 | 192.0 | 571.37 | 2.72 |
| `mx_cadjpy_d1_volume_surge_reversal` | SLEEVE | NO_SIGNAL | 0.0921 | 0.605 | 0.053 | **2.882** | 72.00 | 0.2 | 97.42 | 1.49 |
| `mx_ger40_cash_d1_volume_surge_reversal` | SLEEVE | CONTRACT_OK | 0.2177 | 0.684 | 0.116 | **2.747** | 72.00 | 0.2 | 141.52 | 2.35 |
| `mx_btcusd_d1_donchian_20_breakout` | SLEEVE | TOO_SHORT | 0.1639 | 0.531 | 0.135 | **2.282** | 72.00 | 160.0 | 435.97 | 2.61 |
| `mx_us100_cash_d1_atr_mean_reversion` | SLEEVE | NO_SIGNAL | 0.0956 | 0.666 | 0.079 | **1.818** | 72.00 | 0.2 | 163.69 | 1.98 |
| `mx_us30_cash_d1_volume_surge_reversal` | SLEEVE | NO_SIGNAL | 0.0867 | 0.511 | 0.102 | **1.661** | 72.00 | 320.0 | 130.11 | 1.78 |
| `vol_compression` | SLEEVE | CONTRACT_OK | 0.1747 | 0.524 | 0.214 | **1.557** | 216.00 | 232.0 | 720.49 | 2.13 |
| `fx_jpy_ny` | SLEEVE | NO_SIGNAL | 0.0821 | 0.559 | 0.173 | **0.846** | 0.75 | 16.0 | 7.63 | 0.45 |
| `mx_jp225_cash_d1_volume_surge_reversal` | SLEEVE | TOO_SHORT | 0.0440 | 0.588 | 0.089 | **0.838** | 72.00 | 160.0 | 184.98 | 2.42 |
| `asia_pdl_fade` | SLEEVE | TOO_SHORT, TOO_TIGHT | 0.0594 | 0.210 | 0.358 | **0.790** | 1.00 | 320.0 | 11.42 | 2.65 |
| `current_breaker_re_entry` | BROAD | NO_SIGNAL | 0.0176 | 0.082 | 0.278 | **0.774** | 18.25 | 72.0 | 7.41 | 1.32 |
| `metals_core` | SLEEVE | NO_SIGNAL | 0.0990 | 0.541 | 0.259 | **0.706** | 36.00 | 24.0 | 105.03 | 1.84 |
| `ny_crypto_momentum` | SLEEVE | NO_SIGNAL | 0.0554 | 0.465 | 0.192 | **0.620** | 2.00 | 2.0 | 60.32 | 0.79 |
| `metals_softband` | SLEEVE | NO_SIGNAL | 0.0841 | 0.489 | 0.297 | **0.579** | 44.00 | 16.0 | 134.76 | 1.52 |
| `idxrev` | SLEEVE | NO_SIGNAL | 0.0207 | 0.851 | 0.046 | **0.532** | 16.00 | 11.0 | 73.11 | 1.94 |
| `mx_avausd_d1_donchian_20_breakout` | SLEEVE | NO_SIGNAL | 0.0281 | 0.609 | 0.090 | **0.512** | 72.00 | 0.2 | 760.83 | 0.69 |
| `asian_fade` | SLEEVE | NO_SIGNAL | 0.0599 | 0.492 | 0.277 | **0.440** | 0.25 | 320.0 | 2.43 | 1.54 |
| `metal_session_reversion` | SLEEVE | TOO_SHORT, TOO_TIGHT | 0.0845 | 0.550 | 0.474 | **0.324** | 0.25 | 320.0 | 18.03 | 2.83 |
| `mx_us500_cash_d1_atr_mean_reversion` | SLEEVE | NO_SIGNAL | 0.0159 | 0.573 | 0.090 | **0.307** | 72.00 | 0.2 | 122.26 | 0.26 |
| `regime_transition_break` | BROAD | NO_SIGNAL | 0.0077 | 0.354 | 0.074 | **0.294** | 12.00 | 160.0 | 43.54 | 0.15 |
| `orb_crypto_london` | SLEEVE | NO_SIGNAL | 0.0312 | 0.629 | 0.182 | **0.273** | 3.25 | 320.0 | 51.96 | 1.92 |
| `current_fvg_fill` | BROAD | NO_SIGNAL | 0.0039 | 0.076 | 0.271 | **0.192** | 9.25 | 320.0 | 7.42 | 1.29 |
| `fx_jpy` | SLEEVE | NO_SIGNAL | 0.0178 | 0.418 | 0.234 | **0.182** | 0.75 | 160.0 | 5.68 | -0.02 |
| `metals_ob_micro` | SLEEVE | NO_SIGNAL | 0.0313 | 0.635 | 0.315 | **0.157** | 42.00 | 0.2 | 99.88 | 0.64 |
| `liquidity_sweep_reclaim` | BROAD | NO_SIGNAL | 0.0151 | 0.262 | 0.370 | **0.156** | 0.50 | 2.0 | 7.82 | 1.12 |
| `kz_london_crypto_low` | SLEEVE | NO_SIGNAL | 0.0210 | 0.434 | 0.339 | **0.143** | 2.50 | 0.5 | 31.11 | 0.09 |
| `cross_asset_lead_lag` | BROAD | NO_SIGNAL | 0.0069 | 0.219 | 0.537 | **0.058** | 0.25 | 2.0 | 6.00 | 0.36 |
| `structural_distance_extreme` | BROAD | NO_SIGNAL | 0.0028 | 0.113 | 0.807 | **0.031** | 0.25 | 2.0 | 3.12 | 0.38 |
| `displacement_continuation` | BROAD | NO_SIGNAL | -0.0012 | 0.274 | 0.195 | **-0.023** | 1.75 | 16.0 | 16.23 | 0.08 |
| `liq_asia_up_low_metal` | SLEEVE | NO_SIGNAL | -0.0225 | 0.368 | 0.877 | **-0.070** | 0.75 | 72.0 | 13.89 | 0.81 |
| `vss_fxcross_london_up_low` | SLEEVE | NO_SIGNAL | -0.0254 | 0.541 | 0.341 | **-0.138** | 0.75 | 320.0 | 4.50 | 1.24 |
| `volatility_compression_expansion` | BROAD | NO_SIGNAL | -0.0201 | 0.312 | 0.106 | **-0.611** | 8.25 | 160.0 | 33.45 | 0.87 |
| `session_open_range_break` | BROAD | NO_SIGNAL | -0.0314 | 0.290 | 0.123 | **-0.878** | 3.00 | 320.0 | 17.94 | 0.77 |
| `mx_nzdjpy_d1_donchian_20_breakout` | SLEEVE | NO_SIGNAL | -0.0709 | 0.525 | 0.060 | **-2.250** | 96.00 | 0.2 | 101.70 | -0.64 |
| `current_ob_retest` | BROAD | NO_SIGNAL | -0.0350 | 0.080 | 0.178 | **-2.463** | 37.75 | 1.0 | 8.90 | 0.53 |

### The ceiling table — an upper bound on any same-direction contract

`signal(h*) − toll(h*)`, bps per trade. **CI excluding zero is marked.**

| generator | class | h* (h) | drift | toll | **net** | CI95 | n | verdict |
|---|---|---:|---:|---:|---:|---|---:|---|
| `regime_transition_break` | BROAD | 160.0 | 15.61 | 5.19 | **10.43** | [-13.10, 35.31] | 2318 | includes 0 |
| `volatility_compression_expansion` | BROAD | 160.0 | 12.29 | 4.63 | **7.66** | [-20.31, 34.36] | 5341 | includes 0 |
| `current_fvg_fill` | BROAD | 320.0 | 7.79 | 2.01 | **5.78** | [-6.35, 17.33] | 670717 | includes 0 |
| `session_open_range_break` | BROAD | 320.0 | 7.66 | 2.83 | **4.83** | [-18.03, 26.85] | 7876 | includes 0 |
| `current_breaker_re_entry` | BROAD | 72.0 | 2.48 | 2.06 | **0.42** | [-9.76, 9.63] | 95051 | includes 0 |
| `displacement_continuation` | BROAD | 16.0 | 1.85 | 3.19 | **-1.34** | [-4.36, 1.85] | 39517 | includes 0 |
| `current_ob_retest` | BROAD | 1.0 | 0.13 | 1.58 | **-1.45** | [-1.70, -1.17] | 270354 | CI excludes 0 (NEGATIVE) |
| `liquidity_sweep_reclaim` | BROAD | 2.0 | 0.78 | 2.89 | **-2.11** | [-3.43, -0.69] | 43751 | CI excludes 0 (NEGATIVE) |
| `structural_distance_extreme` | BROAD | 2.0 | 0.35 | 2.52 | **-2.17** | [-3.98, -0.28] | 23923 | CI excludes 0 (NEGATIVE) |
| `cross_asset_lead_lag` | BROAD | 2.0 | 0.31 | 3.22 | **-2.91** | [-4.67, -1.27] | 21678 | CI excludes 0 (NEGATIVE) |
| `sub_xvol_pullback` | SLEEVE | 320.0 | 781.32 | 90.28 | **691.04** | [27.92, 1374.27] | 88 | **CI EXCLUDES 0** |
| `energy_agri` | SLEEVE | 160.0 | 418.95 | 114.08 | **304.88** | [-297.63, 942.50] | 67 | includes 0 |
| `mx_ethusd_d1_donchian_20_breakout` | SLEEVE | 160.0 | 354.82 | 104.01 | **250.81** | [16.52, 494.20] | 311 | **CI EXCLUDES 0** |
| `crypto` | SLEEVE | 72.0 | 314.59 | 71.04 | **243.54** | [-36.69, 559.06] | 181 | includes 0 |
| `mx_btcusd_d1_donchian_20_breakout` | SLEEVE | 160.0 | 317.50 | 114.32 | **203.17** | [32.62, 397.30] | 317 | **CI EXCLUDES 0** |
| `orb_crypto_london` | SLEEVE | 320.0 | 130.82 | 18.34 | **112.48** | [-19.22, 248.56] | 847 | includes 0 |
| `mx_us30_cash_d1_volume_surge_reversal` | SLEEVE | 320.0 | 142.55 | 51.19 | **91.36** | [-58.88, 255.89] | 121 | includes 0 |
| `vol_compression` | SLEEVE | 320.0 | 296.09 | 218.03 | **78.05** | [-200.14, 343.82] | 388 | includes 0 |
| `asia_pdl_fade` | SLEEVE | 320.0 | 83.05 | 5.02 | **78.03** | [18.45, 141.44] | 2761 | **CI EXCLUDES 0** |
| `mx_jp225_cash_d1_volume_surge_reversal` | SLEEVE | 160.0 | 106.10 | 30.13 | **75.97** | [-31.30, 186.49] | 110 | includes 0 |
| `sub_mid_dn_revert` | SLEEVE | 320.0 | 89.49 | 26.14 | **63.35** | [-2.10, 146.61] | 526 | includes 0 |
| `mx_us100_cash_d1_atr_mean_reversion` | SLEEVE | 16.0 | 49.13 | 5.29 | **43.85** | [-2.98, 92.55] | 71 | includes 0 |
| `mx_ger40_cash_d1_volume_surge_reversal` | SLEEVE | 160.0 | 67.20 | 33.31 | **33.90** | [-41.72, 108.30] | 110 | includes 0 |
| `mx_avausd_d1_donchian_20_breakout` | SLEEVE | 16.0 | 54.56 | 33.78 | **20.78** | [-132.73, 173.95] | 189 | includes 0 |
| `metal_session_reversion` | SLEEVE | 320.0 | 34.82 | 15.24 | **19.58** | [-58.65, 95.56] | 808 | includes 0 |
| `vss_fxcross_london_up_low` | SLEEVE | 320.0 | 19.44 | 1.53 | **17.91** | [-13.22, 48.14] | 306 | includes 0 |
| `liq_asia_up_low_metal` | SLEEVE | 72.0 | 29.06 | 12.19 | **16.88** | [-54.47, 85.54] | 157 | includes 0 |
| `mx_cadjpy_d1_volume_surge_reversal` | SLEEVE | 72.0 | 14.84 | 5.15 | **9.69** | [-17.72, 38.67] | 286 | includes 0 |
| `asian_fade` | SLEEVE | 320.0 | 4.70 | 0.67 | **4.03** | [-8.62, 15.48] | 1294 | includes 0 |
| `mx_us500_cash_d1_atr_mean_reversion` | SLEEVE | 16.0 | 6.82 | 4.62 | **2.21** | [-50.50, 52.40] | 67 | includes 0 |
| `fx_jpy` | SLEEVE | 160.0 | 2.50 | 1.47 | **1.03** | [-9.22, 11.59] | 3942 | includes 0 |
| `fx_jpy_ny` | SLEEVE | 16.0 | 2.12 | 1.67 | **0.45** | [-5.69, 7.31] | 1614 | includes 0 |
| `idxrev` | SLEEVE | 8.0 | 1.23 | 2.75 | **-1.52** | [-4.35, 1.33] | 5597 | includes 0 |
| `metals_softband` | SLEEVE | 16.0 | 23.07 | 24.79 | **-1.72** | [-44.20, 50.82] | 237 | includes 0 |
| `metals_core` | SLEEVE | 24.0 | 18.92 | 22.92 | **-4.00** | [-24.05, 16.31] | 385 | includes 0 |
| `ny_crypto_momentum` | SLEEVE | 2.0 | 7.19 | 11.60 | **-4.41** | [-21.86, 13.88] | 559 | includes 0 |
| `metals_ob_micro` | SLEEVE | 4.0 | 8.31 | 13.98 | **-5.67** | [-32.22, 27.66] | 34 | includes 0 |
| `kz_london_crypto_low` | SLEEVE | 0.5 | 1.79 | 9.24 | **-7.45** | [-12.28, -1.89] | 286 | CI excludes 0 (NEGATIVE) |
| `mx_nzdjpy_d1_donchian_20_breakout` | SLEEVE | 16.0 | -4.93 | 4.28 | **-9.22** | [-21.12, 2.49] | 503 | includes 0 |

---

## Receipts

| lane | dossier |
|---|---|
| g1 — the three POI frameworks + shared machinery | `provenance/G1_THREE_POI_FAMILIES_DOSSIER.md` |
| g2 — continuation and break families | `provenance/g2/G2_DOSSIERS.md` |
| g3 — reversion and extreme families | `provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md` |
| g4 — schedule, cross-asset, microstructure | `provenance/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md` |
| s1 — the armed sleeves and the core book | `provenance/S1_ARMED_SLEEVES_DOSSIER.md` |
| s2 — the rest of the 32-sleeve registry | `provenance/S2_REGISTRY_DOSSIERS.md` |
| x1 — the geometry hypothesis, tested properly | `provenance/X1_GEOMETRY_HYPOTHESIS.md` |
| x2 — why we built these | `provenance/x2_receipts/X2_WHY_DID_WE_BUILD_THESE.md` |
| r1 — the quote-side walker repair (concurrent) | `SESSION_R1_QUOTE_SIDE_WALKER.md` |
| r2 — the generator repair (concurrent) | `SESSION_R2_GENERATOR_REPAIR.md` |
| **synthesis — its own measurement** | `provenance/syn_receipts/SYN_IRRELEVANT_V1.json`, `SYN_OFFSESSION_V1.json`, scripts beside them |
| **machine-readable, one record per generator** | `SLEEVE_FORENSIC_V1.json` |

**No live-forward P&L was read. No VPS was touched. No broker script was run. No production code
was changed by this lane.**
