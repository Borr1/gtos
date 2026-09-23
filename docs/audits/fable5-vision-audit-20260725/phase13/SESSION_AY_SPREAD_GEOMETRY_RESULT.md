# Session AY — the spread-geometry repair (wave 13, B1800–B1849)

Commission: `phase13/SESSION_AY_SPREAD_GEOMETRY.md`. Charter: AW's §0.7–0.8 and §4.3 — the
cost-geometry defect the separability mine found, taken out of window and repaired at the
generator.

---

## 0. Findings first

1. **The commission's premise was half wrong, in the most useful direction: the sealed limit
   AW recovered from the January ledger IS the live W7 book's own pre-trade contract, at the
   same two numbers, enforced twice on every placement.** `agent_config.yaml:715-716` carries
   `selected_cell_pretrade_max_spread_r: 0.10` and `…max_total_cost_r: 0.15`;
   `broker_net_cost_engine:721-728` enforces them on every W7 order (reached because
   `build_book_trade_params` stamps `gtos_vnext_production_execution_path: True` at
   `execution_packets.py:538`), and
   `book_owner._spread_cost_screen:4240-4280` mirrors them before the send. **So "apply the
   filter" is not a proposal — it is what the live book already does.** The estate's
   *research* population is the thing out of contract, not the book. Same shape as AQ's time
   stop, different axis.
2. **It fires, and hard.** On the read-only 2026-07-25 VPS export's own launcher log:
   **198 legs refused on the two cost paths** across 5,237 cycles — more than
   `already_placed_today` (99) — at observed `spread_r` up to **16.543**. `asia_pdl_fade`, the
   sleeve AW's filter helps most, carries **101 of the 136** `cost_screen_spread_r` refusals.
3. **A live SIZING defect, on armed money, and it is the session's most consequential find.**
   `_running_conviction_override` (`book_engine.py:937-987`) counts the day's distinct firing
   sleeves from **intents**; the cost screen runs later, at send (`book_owner.py:1876`), and is
   not in `precount_intent_filter`'s drop set. `admission.py:1210` takes `na = max(na, override)` — monotone upward. So **a sleeve whose
   every leg the cost gate refuses still raises the day's Kelly-lite multiplier for every
   sleeve that does place**: measured at **16 contaminated account-days, 3 of which moved the
   multiplier, worst **+25.227 %** on every unit that day — and that is the na 3→4 crossing, not the worst
   the bins allow: **na 1→2 is +32.487 %**. The half bins are selected by
   `ultimate_book_kelly_conservative: true` (`agent_config.yaml:1304`); on the non-conservative
   bins the same 3→4 crossing is +45.5 %. Same defect class as the D3 repair,
   whose own docstring calls it CORRECTNESS-CRITICAL.
4. **The floor is built where that defect is — at generation — and it is default-off.**
   `run_book.py --spread-geometry-floor <sleeve>[:<limit>][,...]`, a per-sleeve map like
   `--frontier-exits`, no config byte, no token disturbance. A sleeve named without a limit
   **inherits the limit the send gate will apply to it**, so the two layers cannot drift.
   33 tests pin default-inertness, launch-time refusal of every fail-open shape, fail-closed
   on an unreadable quote *and* on the module's own exceptions, and finding 3 closed by
   construction.
5. **Per sleeve at the ratified rule: 3 REPAIR, 2 HARMFUL, 12 NEUTRAL, 7 NO-OP,
   5 NOT_EVALUABLE.** REPAIR requires, at ≥2 of 3 real bands, Δ > 0 **and** Δ above every one
   of **20** random-drop seeds **and** a negative inverse-cheapest control. On armed money:
   **`sub_mid_dn_revert` REPAIR** (+0.426 R/day at mid, p 0.163 → **0.023**, 46.9 % of its
   trades over the limit) and **`sub_xvol_pullback` REPAIR** (+0.264, p 0.012 → **0.0020**, on
   only **6 dropped trades of 85**); **`crypto` and `energy_agri` NEUTRAL** — inside the random
   envelope at every band. AW's conclusion holds: **a per-sleeve repair, not an estate rule.**
6. **The first version of that measurement would have condemned an armed sleeve, and the bug
   was mine.** The live gate's total is `spread + slippage + swap capped at ONE DAY`, with **no
   commission**; the research total is `commission + realised-hold swap + spread + slippage`.
   Run with the research total, `crypto` read **HARMFUL at −0.725 R/day**; with the live total
   reconstructed it is **NEUTRAL at +0.066**. Only the spread half is exactly reconstructible,
   so only the spread half carries a verdict (§4).
7. **AW's `fx_jpy` row applied a limit the live book does not apply to `fx_jpy`.** AW used a
   global 0.10; the live gate gives `fx_jpy`/`fx_jpy_ny` **0.35** on a dated owner-approved
   trial. At its own live limit the Δ is **+0.0027**, not AW's **−0.1721**. Every other sleeve
   in AW's §5.2 reproduces to four decimals.
8. **An ATR stop floor is not a spread floor, and no generator constant was changed because of
   it.** `metals_core` carries the estate's strongest floor (`max(structural, 0.25*ATR)`) and
   still reaches **`spread_r` 1.137** — a stop narrower than the round-trip spread. The three
   sleeves with no floor reach **28.626**. ATR bounds how far price moves; it says nothing
   about what the broker charges to participate.
9. **AW's near-admission is closed with a number.** `sub_xvol_pullback` at raw **p 0.0020**
   needs a declared family of **≤ 50** (α 0.10) or **≤ 25** (Bonferroni α 0.05); the ratified
   `CANDIDATE_BOOK_V1` is **53** and this session's own is **514**. It misses at every
   defensible bill, by three members at the most generous. Closed, not carried.

**The one-line verdict.** The spread-geometry defect is real, the live book already refuses the
trades at the send layer, and the repair worth shipping is refusing them **earlier** — because
between generation and send a doomed intent silently inflates every other sleeve's size that
day by up to a quarter.

---

## 1. AY-0 — what was declared, before any outcome was read

`AY_SPREAD_GEOMETRY_PROTOCOL_V1.json`, sealed with `cells_sha256`. The declaration records the
arms, the bands, the population, the verdict rule **and the cut rule** — the wave-11 §1
requirement that killed AO's pair admission.

**The cut rule is the live config's, read at run time, not typed here.** `live_cost_contract()`
opens `config/agent_config.yaml`, resolves the five keys, and stamps their line numbers and a
sha256 over the resolved block. A threshold nobody in this session chose cannot have been
chosen to produce an answer, and the per-sleeve `fx_jpy: 0.35` override is honoured because the
live book honours it.

**The ladder (`k ∈ {0.05, 0.15, 0.20}`) is declared as SENSITIVITY, not as a search** — it asks
whether the live constant is a lucky number, which is the only question a pre-registered
threshold can honestly be asked. It is billed like any other look and never reported as a
verdict. What it shows (band `mid`, Δ against the same control):

| sleeve | k=0.05 | **k=0.10 (live)** | k=0.15 | k=0.20 |
|---|---:|---:|---:|---:|
| `asia_pdl_fade` | +1.142 | **+0.998** | +1.015 | +0.977 |
| `sub_mid_dn_revert` | +0.160 | **+0.426** | +0.249 | +0.344 |
| `sub_xvol_pullback` | +0.262 | **+0.264** | +0.171 | +0.077 |

Positive at all four thresholds on all three, so the result is not a knife-edge at 0.10.
`sub_xvol_pullback` decays monotonically as the limit loosens, which is the shape a real cost
effect should have. `sub_mid_dn_revert` is **best at the pre-registered constant**, which is
reassuring about the pre-registration and is also the row a sceptic should look at hardest.

**Family:** `CANDIDATE_FAMILY_V10.json` adds one member per arm to
`B7_5_SEPARABILITY_MINE_V1`, taking it **486 → 514**. The three mis-specified arms of §4 stay
declared: the looks were taken and cannot be un-taken, and the corrected arms are declared
alongside them. The ratchet doing its job on a specification bug is exactly the case it exists
for.

---

## 2. AY-1a — the census, at each sleeve's own live limit

22,354 archive trades, 29 sleeves, priced by the gate's own cost layer at
`BROKER_TRUE_COSTS_V1_1`. Band `mid`: **24.5 % of 21,769 priced trades exceed the spread limit
their own live gate applies to them.**

| | exceeding the live spread limit at `mid` | max `spread_r` |
|---|---:|---:|
| `vss_fxcross_london_up_low` | 98.3 % | 0.61 |
| `liq_asia_up_low_metal` | 91.7 % | 7.50 |
| `mx_nzdjpy_d1_donchian_20_breakout` | 82.1 % | 0.80 |
| `asia_pdl_fade` | 73.0 % | **28.63** |
| **`sub_mid_dn_revert`** ★ | **46.9 %** | 2.46 |
| **`crypto`** ★ | 11.0 % | 0.77 |
| **`sub_xvol_pullback`** ★ | 7.7 % | 0.23 |
| **`energy_agri`** ★ | 3.8 % | 0.17 |
| `fx_jpy` (limit 0.35) | 1.1 % | 0.43 |
| seven `mx_*` / `idxrev` / `fx_jpy_ny` | **0.0 %** | ≤ 0.25 |

★ = armed. This is AW's census corrected in one place (per-sleeve limits) and extended in
another (the total-cost column now reconstructs the live gate's total rather than the research
one — §4).

The seven zero rows are the **identity-filter check** the wave-10 agreement requires: on those
sleeves the gate is a no-op that would otherwise read as a result.

---

## 3. AY-1b/c — the gate and the verdict table

108 gate runs (27 arms × 4 bands), `RECORDED`, `B_balanced`, α 0.10, family 514, band published
alongside, fold table and `maxbars` share on every row.

| verdict | n | sleeves |
|---|---:|---|
| **REPAIR** | 3 | `asia_pdl_fade`, **`sub_mid_dn_revert`** ★, **`sub_xvol_pullback`** ★ |
| **HARMFUL** | 2 | `kz_london_crypto_low`, `metals_softband` |
| NEUTRAL | 12 | incl. **`crypto`** ★, **`energy_agri`** ★, `metals_core`, `mx_btcusd`, `fx_jpy` |
| NO-OP | 7 | the identity-filter rows above |
| NOT_EVALUABLE | 5 | fall below the option's sample floors under the filter |

The armed rows, at `mid`, as activation-grade evidence:

| sleeve | dropped | control | floor | Δ | inverse | random max | p_emp | p raw |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `sub_mid_dn_revert` | 249 | +0.1206 | +0.5466 | **+0.4260** | −0.0601 | +0.1203 | 0.0476 | 0.163 → **0.023** |
| `sub_xvol_pullback` | 6 | +1.0215 | +1.2859 | **+0.2644** | −0.0792 | +0.2083 | 0.0476 | 0.012 → **0.0020** |
| `energy_agri` | 2 | +0.4065 | +0.6183 | +0.2118 | −0.00004 | +0.1751 | 0.0476 | 0.206 → 0.138 |
| `crypto` | 20 | +0.2611 | +0.3275 | +0.0664 | +0.0318 | +0.1941 | 0.333 | 0.134 → 0.121 |

`energy_agri` reaches the random-beating clause at `mid` and `high` but **not** at `low`, where
the filter drops **zero** trades — one band short of REPAIR, and the honest reading is that its
3.8 % exceedance is too thin to decide. `crypto` sits well inside the envelope at every band.

**Nothing admits, at any arm, at any band.** The floor is a fidelity repair.

### 3.0 Two properties of the control, published because an adversarial pass insisted

*(a)* **The controls are matched on the drop count BEFORE the population rule runs, not on the
scored sample.** `era_population.apply(RECORDED)` runs per arm afterwards, so the scored `n`
differs: at `mid`, live **208** against a random mean of **173.9** and inverse **137**, while
the pre-population kept-lists are identical at 284. A uniform subsample is unbiased for the
mean, so the mismatch *widens* the null's spread and makes "beats every random" **harder** —
but "same sample size" is the natural reading of a matched control and it is not what is
matched. Both counts are now published per band
(`n_trades_scored_{control,live_contract,random_mean,inverse}`).

*(b)* **`empirical_p_vs_random = 0.0476` is the resolution floor of a 20-seed null (1/21), not
a measured value**, and it is the same number on all three bands because the seeds are shared
across them. Read `beats_every_random` as the statement; the artifact now carries
`empirical_p_is_the_resolution_floor` so a reader cannot mistake the two.

### 3.1 The fold tables are not always comparable, and this is stated rather than glossed

`build_fold_calendar` derives boundaries from the SPAN of the data it is handed, so an arm that
drops a sleeve's earliest trades **moves every boundary**. On `sub_mid_dn_revert` the control's
fold 1 opens 2008-08-16 and the filtered arm's opens **2012-07-25** — about four years. The
pooled comparison is valid (each arm is scored OOS on its own calendar); a fold-by-fold one is
not, so *"5 of 5 folds positive against 2 of 5"* is a sentence this session does not write.
Published per band as `fold_calendar_identical`: **false** on `sub_mid_dn_revert` and `crypto`,
**true** on `sub_xvol_pullback` and `energy_agri`.

The recent-fold basis (wave-11 §1, for anything that will be sized) at `mid`:
`sub_mid_dn_revert` 0.568 → 0.609; `sub_xvol_pullback` 1.264 → 1.520; `energy_agri` 0.143 →
0.461; `crypto` 0.265 → 0.431. `maxbars` share moves by less than 0.02 on every armed sleeve.

---

## 4. The specification bug that would have condemned an armed sleeve

The live gate's `total_cost_r` is `spread_r + expected_slippage_r + swap_cost_r`, where
`swap_cost_r` is a **pre-trade** estimate off the **contract horizon**, capped at
`selected_cell_swap_cost_horizon_days_cap: 1.0`, and carries **no commission**
(`broker_net_cost_engine._swap_cost_packet:377-391`). The research total is
`commission + swap(REALISED nights) + spread + slippage`. On a multi-night sleeve these are
different numbers, and `crypto` is such a sleeve:

| arm as specified | `crypto` Δ R/day at mid | verdict it produced |
|---|---:|---|
| spread OR **research** total ≤ 0.15 | **−0.7247** | **HARMFUL** — an armed sleeve |
| spread ≤ 0.10 (exact) | **+0.0664** | NEUTRAL |

**It then took a second correction, and an adversarial pass found it.** The fix above charged
`slippage_r` — a per-symbol MEASURED value — and a FULL night of swap, and this document
claimed the result was a **subset** of the live refusal set. Both halves of that were wrong:

- the live gate's slippage is a **flat constant**, `selected_cell_default_expected_slippage_r`
  = 0.02, because nothing in the tree writes the trade_params key that would override it
  (`broker_net_cost_engine:544-548`) — while the research values run to 0.041, up to **2.05×**;
- the live swap horizon is the **sleeve's own contract horizon** capped at one day, and **ten of
  the 34 declared sleeves sit under one day** — `liq_asia_up_low_metal` at 0.1667 d,
  `ny_crypto_momentum` 0.2083, `metal_session_reversion` 0.25, `asia_pdl_fade` and
  `kz_london_crypto_low` 0.3333, four at 0.5, `orb_crypto_london` 0.8333.

Measured: **15,808 of 86,387 priced rows over-charged and 703 flipped outright**, 11 of them on
`sub_mid_dn_revert` — an armed sleeve. **Neither a subset nor a superset: a mixture.** The
claim is withdrawn and the arm now computes the live gate's own arithmetic, with the per-night
drag recovered exactly for every trade (including zero-rollover ones) from a 192-hour pricing
probe, since `swap_r / nights` is `drag/sl` for any `nights > 0`.

Two things follow, and both are now structural rather than remembered:

- **Only the exactly-reconstructible half carries a verdict.** `spread_r` is
  `spread_price / stop` here and `(ask − bid) / sl_distance` there — the same quantity from a
  modelled era-banded spread instead of a live tick. The total half is published beside every
  row and never as one.
- **The commission half of the original claim survives**: the live total sums exactly three
  terms and has none (`broker_net_cost_engine:577-583`).

---

## 5. AY-2 — the floor, and what it is for

`src/components/ultimate_book/spread_geometry.py` + `book_engine._spread_geometry_refusal`,
applied immediately after `spec.generator(...)` and before `intents.append(intent)`. Reached
from `run_book.py --spread-geometry-floor`, validated at LAUNCH against the union of all three
registries (34 sleeves — validating against `BUILT`'s 11 alone refused `asia_pdl_fade`, the
flag's best use, as a typo; found by running the parser, not by reading it).

**What it adds over the send-layer gate that already exists:**

1. The intent never reaches `_running_conviction_override`, so it cannot inflate `na`
   (finding 3 — up to **+25.2 %** on every other unit that day). This is true whether or not
   the filter improves any sleeve's expectancy, because it is about the **other** sleeves.
2. No sizing slot is spent on a trade that cannot place.
3. No operator card for a non-event.

**Fail-closed, and that matches the authority.** An opted-in sleeve whose spread cannot be read
is REFUSED. That is not a preference: `pretrade_cost_refusal_reasons` already answers the same
question with `missing_current_quote_spread_or_sl_distance`, a refusal. `book_owner`'s mirror
fails open, but its own docstring says why — it defers to the authoritative gate, which does
not. A generation floor that failed open would be the only one of three layers letting an
unpriceable leg through. An exception inside the floor is also a refusal, named in
`generation_skips`, so an internal fault reads as a fault rather than as a quiet sleeve.

**Not done, deliberately:** no generator constant changed (§0.8 and
`AY_GENERATOR_STOP_SURVEY_V1.json`), no send-layer limit changed (`agent_config.yaml` is
R2-bound and both tokens hash it), nothing armed.

Activation package: `phase13/AY_SPREAD_FLOOR_ACTIVATION_DOSSIER.md` — exact flag, per-sleeve
recommendation (**ARM `sub_mid_dn_revert`**; `sub_xvol_pullback` owner's call; do not arm
`crypto`/`energy_agri`), the decision-day-boundary ordering hazard, three post-restart
verifications, four stop conditions and a rollback that unwinds no state.

---

## 6. What I got wrong

1. **I specified the `live_contract` arm's total as the research total and it inverted an armed
   sleeve's verdict.** `crypto` read HARMFUL at −0.7247 R/day for one run. The live gate caps
   swap at one day off the contract horizon and charges no commission; I charged full realised
   swap and commission. Caught by asking why a sleeve with 11 % exceedance was losing 0.72 R/day
   — the magnitude was the tell, not the sign. **A filter arm named after a live contract must
   be built from that contract's own arithmetic, not from the nearest available total.** Fixed;
   the mis-specified arms stay in the family, because the looks were taken.
2. **I published a fold table of `None`s.** `sv.folds` rows key the OOS mean as `test_mean_r`;
   I read `oos_mean_r`, which does not exist. A column of nulls where the wave-11 agreement
   requires a decay table reads as "no decay", not as "not measured" — the exact silent-null
   failure mode the agreement re-affirms. Caught by looking at the output instead of trusting
   the writer.
3. **I compared fold tables that are not the same calendar.** Having fixed (2), I nearly wrote
   "5 of 5 folds positive against 2 of 5" for `sub_mid_dn_revert` — whose filtered fold 1 starts
   four years after its control's. Caught by printing the boundaries; now a published flag on
   every band so the next reader cannot make the same error silently.
4. **My first launch-time validation used `registry.BUILT`, which is 11 of 34 sleeves**, so
   `--spread-geometry-floor asia_pdl_fade` — the flag's largest measured use — was refused as an
   unknown sleeve. A validator that refuses the correct input is worse than none, because it
   reads as confirmation that the input was wrong.
5. **Two test fixtures asserted the wrong thing and passed for a while.** A synthetic spread of
   `1e6` on a mid of 60,000 drives `bid` negative, so the "pathological geometry" test was
   exercising the unreadable-quote branch; and `update_and_count({})` returns `{}` because it
   keys its result off its argument, so the conviction assertion was vacuously true in both
   arms. Both fixed to assert what they claim — the second now reads the persisted
   `firing_sleeves.json`.
6. **I read `crossings_charged: 1` as "one half-spread" for a moment** and nearly filed AW's
   "round-trip" wording as an error. It is the full quoted spread charged once, which *is* the
   round trip (enter at ask, exit at bid). AW's wording is right; mine would have been the
   correction that introduced the defect.
7. **My fix for (1) was itself wrong, and I published a false safety claim about it.** Having
   corrected the total term, I asserted the result was a **subset** of the live refusal set —
   "whatever it refuses, the live gate refuses too" — reasoning only about swap and forgetting
   that I was also charging a per-symbol measured slippage against the live flat 0.02, and a
   full night against contract horizons that are **under one day on ten of 34 sleeves**. It was
   a mixture: 15,808 rows over-charged, 703 flips, 11 on an armed sleeve. **A safety claim of
   the form "this errs in only one direction" has to be checked term by term**, and I checked
   one. Found by an adversarial pass, not by me; §4 now carries the arithmetic instead of the
   reassurance.
8. **I cited `execution_packets.py:348` as a placement path. It is
   `native_policy_instrumentation` — the adopt-rehydration helper.** Only `:538`
   (`build_book_trade_params`) stamps the flag on a placement. The claim survives on `:538`
   alone; the citation was decoration that looked like corroboration.
9. **Half my `file:line` citations went stale inside my own commit.** `_spread_cost_screen`
   moved 4232 → 4240 and `_running_conviction_override` 865 → 937 **because of the code I
   added above them**. I wrote the numbers while reading the pre-edit file and never re-read.
10. **I claimed `B1850–B1899` for a pre-declaration that belongs to session AZ.** `main` had
    moved since this branch point and now allocates it as part of a six-session wave-13. The
    copy-back A/B is what surfaced it — restoring the agreement from `main` returned text I had
    never seen. **A branch-point copy of a shared allocation table is not the allocation table.**

---

## 7. Handoff

1. **`sub_mid_dn_revert` is ARMED, 46.9 % of its archive trades exceed the limit its own live
   gate applies, and the floor is a controlled REPAIR at 2 of 3 bands.** The dossier recommends
   arming the floor for it and nothing else. Borhen's call; the measurement is not.
2. **The conviction-count contamination is a live defect that exists whether or not the floor is
   armed** (repair row 1, `BUILT_DEFAULT_OFF`). If the orchestrator does not arm the floor, the
   defect stays open — and the alternative repair, adding a cost screen to
   `precount_intent_filter`, needs a tick at generation, which is precisely what the floor
   already fetches. **Do not close this row by arming nothing.**
3. **Two sleeves are HARMFUL under the live contract** (`kz_london_crypto_low`,
   `metals_softband`): their expensive trades are systematically the profitable ones, below
   every random seed at ≥2 bands. Neither is armed. Whether that is microstructure or sample is
   the mirror-image question to `asia_pdl_fade`'s and takes the same controls.
4. **`asia_pdl_fade` remains the largest unclaimed repair in the estate**: −0.902 → +0.095 R/day
   at mid, inverse −1.825, positive at all four ladder thresholds, 73 % of its trades over the
   limit and a max `spread_r` of **28.6**. It is not armed and it still fails `stability`. Its
   next question is its own stop geometry, not this filter.
5. **Three sleeves deserve a stop-width frontier at the ratified rule** —
   `vss_fxcross_london_up_low` (98.3 % over), `liq_asia_up_low_metal` (91.7 %), `asia_pdl_fade`
   (73.0 %). Repair row 5 carries the measurement; AD's sweep machinery already excludes the two
   `_atr_mean_reversion` sleeves for the right reason and would extend to these.
6. **`config/agent_config.yaml` was read and never written**, and the block it was read from is
   sha256-stamped in every artifact. If the owner ever moves
   `selected_cell_pretrade_max_spread_r`, the floor moves with it by construction — but the
   published numbers here do not, and the census is the thing to re-run.
7. **The block guard needed two edits and they are the third of their kind.** `B1786` is now a
   KNOWN_GHOST (the lower bound of AW's own *"cited nowhere"* retirement note, which `_RANGE`
   excuses at the upper bound only), and `IN_FLIGHT_WAVE_RANGES` carries a pre-declaration of
   **`B1850–B1899`** because retiring AY's own entry emptied a table the guard refuses to see
   empty. **The next wave should take `B1850–B1899` by name**; the agreement now says so.
8. **`research/operations/broker_truth_layer_2026_07_29/` had to be added to this worktree's
   sparse checkout again** (AW's handoff item 7, unresolved). No tracked content changed. It is
   now the second session to pay this cost; the orchestrator may want it in the default cone.
8b. **This branch is BEHIND `main` and two of its edits are reconciliations, not originals.**
   `main` has since allocated wave 13 as six sessions (AY, AZ, BA, BB, BC, BD) and regenerated
   AW's A/B receipt with the tool fence. AY took `main`'s agreement text and re-applied its own
   note on top, and points `IN_FLIGHT_WAVE_RANGES` at **AZ's** `B1850–B1899` rather than
   claiming it. The scoped A/B was run at this branch's tip with `main`'s agreement file in
   place; **it is not a run against `main`'s tip**, which is the orchestrator's job at the
   train.
9. **A latent zero-swap hazard in the LIVE pre-trade gate, filed not fixed (B1825).**
   `_swap_cost_packet` falls back to two config keys — `selected_cell_swap_cost_time_stop_bars`
   and `…_default_hold_days` — and **neither exists anywhere in `config/`**. A trade whose
   params carry no `gtos_vnext_dynamic_time_stop_bars` would get `holding_days = None` → swap
   `None` → `or 0.0` → **a zero-swap total on every multi-night trade**, silently loosening the
   0.15 gate. Unreached today because every W7 placement carries the key from its exit profile.
   The cheap fix is a refusal reason when `holding_days` is None while a swap value is present;
   the gate already fails closed on every other missing input. Repair row 7.
10. **Four of this session's five load-bearing claims survived an adversarial pass; the fifth
    was refuted and is corrected in place** (§4, B1824). What survived: the live gate is
    reached on every W7 placement (driven end-to-end with a stubbed `safe_place_order`); the
    conviction contamination reproduces on the real classes at exactly +25.227 %; the floor is
    default-inert against the **parent commit's** engine module; and `sub_mid_dn_revert`'s
    REPAIR reproduces, with an independent calendar-free instrument agreeing at all three bands
    and the inverse control negative at all three. The refutation and every caveat it produced
    are in the documents rather than in a report nobody reads.
11. **March was not read. No sealed window was run. No R2-bound path was edited** — 43 bound
    paths, 2 UNHYDRATED-LFS, 0 drifted, at session start and at session end.

---

## 8. Artifacts

| path | what |
|---|---|
| `src/components/ultimate_book/spread_geometry.py` | the floor: parse, resolve, evaluate |
| `src/components/ultimate_book/book_engine.py` | `_spread_geometry_refusal`, applied at generation |
| `run_book.py` | `--spread-geometry-floor`, validated at launch |
| `tests/ultimate_book/test_spread_geometry_floor.py` | 33 tests, incl. finding 3 pinned |
| `phase13/AY_SPREAD_FLOOR_ACTIVATION_DOSSIER.md` | the ceremony package |
| `phase13/receipts/AY_SPREAD_GEOMETRY_PROTOCOL_V1.json` | the sealed declaration |
| `phase13/receipts/AY_LIVE_SCREEN_EVIDENCE_V1.json` | the live gate + the conviction contamination |
| `phase13/receipts/AY_LIVE_CONTRACT_CENSUS_V1.json` | the estate vs each sleeve's own live limit |
| `phase13/receipts/AY_SLEEVE_GATE_V1.json` | 108 runs, every verdict, every fold |
| `phase13/receipts/AY_SLEEVE_VERDICT_V1.json` | the REPAIR / NEUTRAL / HARMFUL table |
| `phase13/receipts/AY_GENERATOR_STOP_SURVEY_V1.json` | stop expressions vs measured spread geometry |
| `phase13/receipts/CANDIDATE_FAMILY_V10.json` | the ratchet, 486 → 514 |
| `phase13/receipts/REPAIR_QUEUE_AY.json` | 6 rows, built from the receipts |
| `phase13/receipts/SESSION_AY_AB.md` | the scoped A/B, copy-back, both captures embedded |
