# m4 — WHAT ELSE IS BENT

**Lane m4, wave 20, phase 20. Find and price; repair nothing.**

Four defects were found by accident this wave. That is evidence there are more, not evidence
we found them all. This lane went looking, systematically, on the axes the four share — *a
quantity expressed in one unit consumed as if it were another*.

Whole population everywhere. Nothing sampled. Every number traced to one of three committed
scripts under `phase20/receipts/m4/`:

| script | receipt |
|---|---|
| `m4_gapfill.py` | `M4_GAPFILL_V1.json`, `M4_GAPFILL_ROWS_V1.json.gz` |
| `m4_cost_truth.py` | `M4_COST_TRUTH_V1.json` |
| `m4_probes.py` | `M4_REGISTER_V1.json` |

The estate re-walk carries the same control r1 used: it must reproduce the published
`r_gross` on every one of 22,354 rows or refuse to write. It reproduces at
**`max_abs_err = 0.0`**, so everything below is about the estate's own labelling and not
about a private reimplementation.

---

## 0. HEADLINE

**The next foundational defect is a unit error in HOLDING TIME, and the estate is running two
incompatible conventions at once.** Seven sites in six files write
`hold_hours = bars_held x nominal_bar_minutes` — *trading* time — and hand it to
`costs.model.cost_r`, whose `rollover_nights` reads its `holding_hours` argument as *wall*
time and counts calendar midnights. `walkforward/panel.py:120-121` does it right
(`exit_utc - entry_utc`). The two disagree by up to **93 % of the charged nights**
(`mx_ger40_cash` 3.909 → 7.545), and the swap term is under-charged by **+0.003669 R/trade
pooled (20.81 % of the term)** — including on four of the five armed sleeves and on the
estate's one standing admission.

**And the finding that reaches armed money is a coverage hole, not an arithmetic one:
`energy_agri` is ARMED ON redacted_account and 0 of its 67 trades are priceable on the redacted_account
cost table.** Both of its instruments (`USOIL.cash`, `UKOIL.cash`) are absent from
`BROKER_TRUE_COSTS_V1.json`'s redacted_account block *and* from the redacted_account spread model.
`sub_xvol_pullback`, also armed there, prices **45.45 %** — below the ratified
`min_retained_trade_frac` of 0.60, i.e. NOT_EVALUABLE. Across the estate FTMO prices
**100.00 %** and redacted_account **63.76 %**.

**The cost model is otherwise in better shape than the hunt expected, and that is a result.**
Its decomposition on the estate is spread **66.65 %**, commission **21.19 %**, swap **6.13 %**,
slippage **6.03 %** — and the largest term is the one term that *is* era-corrected. The three
new cost findings below are all second-order next to that.

---

## 1. THE RANKED REGISTER

| # | defect | file:line | population | measured magnitude | invalidates | repair cost |
|---|---|---|---|---|---|---|
| **M4-1** | holding time: trading-time hours consumed as wall-clock hours | `phase6/receipts/aa_estate_generate.py:305` (+6 sites in 5 more files); consumed at `phase6/receipts/aa_cost_geometry_frontier.py:117`, `phase8/receipts/ah_entry_gate.py:127`, `phase20/receipts/r1/r1_estate_net.py:169-170` | all 22,354 estate trades; every artifact built on `hold_hours` | swap under-charged **+0.003669 R/trade (20.81 %)**; nights under-counted **34.8–93.0 %** on 10 sleeves; armed: `sub_xvol_pullback` +0.02347, `sub_mid_dn_revert` +0.01746, `energy_agri` +0.01583, `mx_btcusd` +0.00910 | AD's 1,631-cell exit frontier, AH's entry-hour lever, r1's published net | one line per site — pass `exit_utc - entry_utc`; then re-run the affected receipts (no new data) |
| **M4-2** | redacted_account cannot price the book it is armed on | `BROKER_TRUE_COSTS_V1.json` (76 FN instruments vs 167 FTMO); `spread_model_2026_07_29/SPREAD_MODEL_V1.json` | 22,354 estate trades | FTMO **100.00 %** priceable, redacted_account **63.76 %**. `energy_agri` **0.00 %** (armed on FN), `sub_xvol_pullback` **45.45 %** (armed, below the 0.60 floor), `sub_mid_dn_revert` 77.49 %, `crypto` 80.66 % | any redacted_account economic claim about `energy_agri`; any FN/FTMO cost comparison on the estate | a capture, not a code change: redacted_account tick/spec coverage for `USOIL.cash`, `UKOIL.cash`, the index CFDs and the metal crosses |
| **M4-3** | the spread era model's decidability guard is inverted | `src/costs/spread_model.py:440-458`, `SPREAD_MODEL_V1.json → class_halfwidth_floors` | 645/645 FTMO + 222/222 redacted_account `SCHEDULE` eras | `require_decidable=True` removes **0** placeholder eras and **134 of 1,119** RECORDED ones. **25.48 %** of the estate's total spread charge (spread = 66.65 % of cost) sits on a non-RECORDED era; `crypto` 44 % non-RECORDED, `sub_mid_dn_revert` 39 % | the strongest available "remove unpriceable eras" switch; every `require_decidable` robustness run | make the guard read era CLASS as well as half-width; ~1 function + tests |
| **M4-4** | slippage charged as a constant in R across 110x of stop distance | `BROKER_TRUE_COSTS_V1.json → slippage`, its own conventions block; `src/costs/model.py:709-716` | every priced trade in the estate (6.03 % of cost) | within ONE symbol the p95/p05 stop ratio is **109.7x** (`USOIL.cash`), 97.7x (`UKOIL.cash`), 93.7x (`DASHUSD`), 37.4x (`BTCUSD`, armed). Implied price slippage on `USOIL.cash` spans **0.067 → 7.37 bps** | the slippage term at both tails of every sleeve's stop distribution | re-express as a price (or as a multiple of spread) — needs one number per symbol, from the same W7 capture |
| **M4-5** | the walker fills a stop AT the stop through a gap | `src/components/ultimate_book/primitives.py:83-84` / `:46-48` (the VENDORED live primitive) and its copy `walkforward/exits.py:388-391` | 13,221 stop exits + 7,552 target exits | **125** stop exits and **99** target exits were gapped through. Standalone **−0.00103 R/trade** (targets nearly offset stops); **−0.01024** on top of r1's quote-side correction, and **−0.065**/**−0.110** on the two highest spread/risk sleeves | nothing on its own; it is a *composition* risk with r1 | a gap-aware fill is 2 lines — but `primitives.py` is parity-locked, so it is a switch, not an edit |
| **M4-6** | `usd_per_price_unit_per_lot` is FX-rate dependent and frozen at 2026-07-25 | `src/costs/model.py:230-238`; 65 of 167 FTMO instruments | 7,803 estate trades on `per_lot`-commission non-USD-profit symbols | commission **over**-charged **−0.001821 R/trade** pooled; per-symbol snapshot/true ratio median **1.49x** (`NZDJPY`, `CADJPY`), max **2.16x** | deep-history commission on every JPY/EUR/GBP-quoted symbol | a date-indexed conversion series; the D1 archive already carries every rate needed |
| **M4-7** | pre-2007 US DST rule applied with no year guard | `src/utils/broker_clock.py:126-137` | archives from 1993/2000; 127 estate trades pre-2007 | **11 of 22,354** trades sit in a window where the 1987–2006 rule disagreed (9 of them in armed `sub_mid_dn_revert`) | nothing published, at this size | a 3-line year branch, or a documented refusal below 2007 |
| **M4-8** | the live stress-derisk overlay uses a static broker offset | `book_engine.py:260-261` → `admission.py:439`, against `governor_state.py:103` which uses the calendar-aware `broker_clock.daily_reset_offset_hours` | LIVE, both accounts | `governor_daily_reset_offset_hours: 3.0` is correct while New York is on EDT and 1 h wrong from **2026-11-01**; the in-progress server day then leaks into the "fully-realized prior days" window for one UTC hour per day | the de-risk overlay's leak-free claim, ~19 weeks a year | pass `broker_clock.daily_reset_offset_hours` — the function already exists and the governor already calls it |

### Notes, not findings

* **`primitives.wins`'s −1.3 winsorisation floor is unreachable under the shipped walker.**
  Minimum `r_gross` over all 22,354 estate trades is **exactly −1.0**. The floor was written
  for outcomes worse than the stop, and the walker cannot produce one — which is the
  structural tell behind M4-5. (`M4_GAPFILL_V1.json → control`.)
* **B613's intrabar trail assumption is not 95.8 %, it is 99.91 %.** Across every trailing
  sleeve, **1,168 of 1,169** trail exits have their level set on their own exit bar. The
  published figure was `asian_fade`'s alone.
* **`day_aggregation = "mean"`** (`walkforward/spec.py:170`) makes the gate's daily
  observation the mean across a day's simultaneous trades while a book earns their sum. It
  is **exactly inert on all ten `mx_*` D1 sleeves (1.000 trades/traded day), including the
  standing admission**, and material elsewhere: `sub_xvol_pullback` 2.316 (max 9/day),
  `energy_agri` 1.718, `idxrev` 3.623 (max 18), `fx_jpy` 6.000 on 100 % of its days.
* **`symbol_damage_guard.compute_symbol_metrics` carries the same static-offset shape and is
  NEVER CALLED.** Zero call sites in `src/`, `scripts/` or `tests/`; the live path passes
  `symbol_damage_metrics=None` (`book_engine.py:1093`, and its own docstring at `:1068-1070`
  says so). It is therefore excluded from M4-8 rather than counted in it.
* **150 of 22,354 trades are right-censored** — `end` was clamped by `len(bars)-1` rather
  than by `maxbars`, so they are labelled `maxbars` because the archive stopped.
* **`poi_proximity_prescreen_tolerance_pct: 1.0`** (`agent_config.yaml:4036`) is a PERCENT
  four lines from `poi_proximity_tolerance_pct: 0.01`, a FRACTION, under the same suffix. It
  has **zero consumers** in `src/` or `scripts/` — a dead key, but the naming collision is
  the exact shape of the defect d4 measured.
* **Four symbols cost more than one full R to trade, on a MODELLED spread anchor.** At their
  own estate stop distances the median total `cost_r` is `XPDUSD` **1.8395 R** (n=124),
  `XPTUSD` **1.4190 R** (n=139), `LTCUSD` **1.0240 R** (n=113), `XRPUSD` **0.5735 R** (n=98)
  — 474 of them inside `asia_pdl_fade` alone. None has a tick file; all four anchors are the
  bar-recorded level times a class factor. See §7.3.
* **`verification.py:1083`'s `max_gap_pct` gate is the POI defect's twin** — a percent-of-
  price admission radius on an R-denominated trade, and it is one-sided (a long limit that
  price has fallen arbitrarily far *below* scores a negative gap and passes). It is **not on
  the live book path**: `run_book.py`'s import closure is 84 `src.` modules and
  `components.verification` is not one of them.

---

## 2. M4-1 IN FULL — the holding-time unit

`cost_r`'s contract is unambiguous (`src/costs/model.py:420-452`):

```python
def rollover_nights(entry_utc, holding_hours, *, server, rollover3days_weekday):
    """Count swap-charged nights over the hold, on the broker's own wall clock."""
    end = utc_to_broker_naive(entry_utc + timedelta(hours=float(holding_hours)), rule)
```

`holding_hours` is added to a wall-clock instant. Passing trading hours therefore ends the
trade early by every market closure it spanned, and a night that is not inside the span is
not charged.

`walkforward/panel.py:120-121` gets it right:

```python
@property
def holding_hours(self) -> float:
    return (self.exit_utc - self.entry_utc).total_seconds() / 3600.0
```

The estate artifact carries **both**: a real `exit_utc` (the exit bar's close) and a
`hold_hours` field that is `bars x nominal_minutes`. Receipts that build a `Trade` and go
through `panel.py` inherit the right one; receipts that read `hold_hours` or recompute
`bars_held * TF_MINUTES / 60` inherit the wrong one. Measured over all 22,354 trades:

| sleeve | nights (bar-count) | nights (true) | under-count | Δ swap R/trade |
|---|---:|---:|---:|---:|
| `mx_ger40_cash_d1_volume_surge_reversal` | 3.909 | 7.545 | **93.0 %** | +0.04899 |
| `mx_us30_cash_d1_volume_surge_reversal` | 3.595 | 5.521 | 53.6 % | +0.02946 |
| **`sub_xvol_pullback`** (ARMED) | 2.954 | 4.557 | **54.2 %** | **+0.02347** |
| `metals_ob_micro` | 3.794 | 5.647 | 48.8 % | +0.06033 |
| `metals_softband` | 4.067 | 5.688 | 39.8 % | +0.04529 |
| `metals_core` | 3.340 | 4.748 | 42.2 % | +0.03485 |
| **`sub_mid_dn_revert`** (ARMED) | 1.850 | 2.493 | 34.8 % | +0.01746 |
| **`energy_agri`** (ARMED) | 4.358 | 5.582 | 28.1 % | +0.01583 |
| **`mx_btcusd_d1_donchian_20_breakout`** (ADMISSION) | 4.811 | 5.340 | 11.0 % | +0.00910 |
| **`crypto`** (ARMED) | 4.983 | 5.320 | 6.8 % | +0.00702 |
| **pooled** | — | — | — | **+0.003669** |

The 24/7 sleeves (`asian_fade`, `fx_jpy`, `vss_fxcross_london_up_low`, …) are exactly
0.00000 — which is the control that says this is a market-closure effect and not an
arithmetic slip somewhere else.

**Direction: the estate's published NET is too GOOD by 0.0037 R/trade pooled**, and by 5–16x
that on the metals and index-CFD sleeves.

---

## 3. M4-2 IN FULL — the account the cost layer cannot price

`scripts/run_book_supervisor.ps1:86-87`, read verbatim:

```
FTMO       tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"
redacted_account tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"
```

Priceable fraction of each sleeve's estate trades, by account:

| sleeve | n | FTMO | redacted_account | armed on FN |
|---|---:|---:|---:|---|
| `energy_agri` | 67 | 100.0 % | **0.0 %** | **yes** |
| `sub_xvol_pullback` | 88 | 100.0 % | **45.45 %** | **yes** |
| `sub_mid_dn_revert` | 533 | 100.0 % | 77.49 % | yes |
| `crypto` | 181 | 100.0 % | 80.66 % | yes |
| `mx_btcusd_d1_donchian_20_breakout` | 318 | 100.0 % | 100.0 % | no (FTMO only) |
| **estate** | **22,354** | **100.00 %** | **63.76 %** | — |

`energy_agri` trades only `USOIL.cash` (33) and `UKOIL.cash` (34). Neither appears in
`BROKER_TRUE_COSTS_V1.json`'s redacted_account instrument table, and neither appears in the
redacted_account half of `SPREAD_MODEL_V1.json`. There is therefore **no redacted_account-costed number
for a sleeve that is placing real orders on that account**, and the ratified BALANCED spec
would return NOT_EVALUABLE for it and for `sub_xvol_pullback` (45.45 % < the 0.60
`min_retained_trade_frac`).

This is not a reason to disarm anything — it is a statement about what is *measured*, and
the honest reading is that redacted_account's half of every cost-true comparison rests on 63.76 %
of the population. It is a capture requirement, and the cheapest one in this register.

---

## 4. M4-3 IN FULL — a guard that removes the real data and keeps the placeholder

The era ratio that scales 66.65 % of the cost basis is built from the MT5 bar `spread`
column. Measured over the whole H4 archive, **25 symbols carry at least one year in which
that column takes exactly ONE distinct value on every bar**:

```
EURUSD H4, distinct values per year
  2000  n=1185  distinct=1  mode=50 (100.0%)
  2001  n=1564  distinct=1  mode=50 (100.0%)
  2002  n=1566  distinct=1  mode=50 (100.0%)
  2003  n=1565  distinct=1  mode=50 (100.0%)
  2004  n=1572  distinct=1  mode=40 (100.0%)
  2005  n=1560  distinct=1  mode=30 (100.0%)
  2006-2008              distinct=1  mode=20 (100.0%)
```

USDJPY and GBPUSD carry the **same integers in the same years**. That is the broker's own
historical spread schedule, backfilled — which is exactly what the model calls it
(`class: SCHEDULE`) and exactly what its `honest_limit` field admits: *"NOTHING validates it
at the 5x-25x ratios the pre-2010 FX eras imply."* The classification is good engineering.

**The guard built on top of it is not.** `decidable` is computed from the era's band
half-width, and a stamped constant's four dispersion terms are all exactly `0.0`
(`cross_instrument_dispersion_log`, `split_half_noise_log`, `d1_vs_h4_disagreement_log`,
`band_halfwidth_log`), so the band is entirely the class floor of 0.18229 — well inside the
0.5 decidability threshold. Result:

| account | era class | eras | undecidable |
|---|---|---:|---:|
| FTMO | **SCHEDULE** | **645** | **0** |
| FTMO | QUANTIZED | 246 | 20 |
| FTMO | FLOORED | 86 | 41 |
| FTMO | **RECORDED** | **1,119** | **134** |
| redacted_account | **SCHEDULE** | **222** | **0** |
| redacted_account | RECORDED | 252 | 48 |

**`require_decidable=True` — the switch a caller reaches for when an unpriceable era should
leave the population rather than merely be stamped — removes 0 % of the broker-placeholder
eras and 12.0 % of the real ones.** *Within-era dispersion* is being consumed as *estimate
uncertainty*, and for a stamped constant the first is zero because the data is synthetic,
not because the estimate is good. That is the same unit-substitution shape as the other four.

Estate exposure: **25.48 % of the total spread charge** sits on a non-RECORDED era
(SCHEDULE 7.59 %, QUANTIZED 17.65 %, FLOORED 0.23 %); armed sleeves `crypto` 44 % and
`sub_mid_dn_revert` 39 % of trades non-RECORDED.

---

## 5. M4-5 — the fill defect, and why it is ranked FIFTH rather than first

`primitives.simulate_detail:83-84` (and `simulate:46-48`) fills a stop at the stop level unconditionally. A bar that
OPENS beyond the stop never traded there; MT5 fills at the first available price. The same
arithmetic runs the other way on the target.

This started as the lane's headline candidate and the measurement demoted it. Whole
population, three fill conventions:

| convention | estate gross R/trade |
|---|---:|
| LEVEL (ships today) | **+0.112763** |
| SYM (both legs at the open) | +0.113961 |
| ASYM (stop at the open, target still at its level) | +0.111732 |

**125** of 13,221 stop exits and **99** of 7,552 target exits gapped through, and the two
nearly cancel: **−0.00103 R/trade** at the conservative convention. Composed with r1's
quote-side correction — which moves the stop one spread NEARER in tape space and so exposes
more of it — it is **−0.01024** (−0.027726 → −0.037966), and up to −0.065 (`asia_pdl_fade`)
and −0.110 (`liq_asia_up_low_metal`) on the sleeves whose spread/risk ratio is largest.

**The first version of this measurement was wrong by 60x and the correction is worth
recording.** Treating a `trail` exit as gappable reported 1,280 gap-throughs and an estate
delta of −0.0626. It was measuring B613, not gaps: `simulate` arms and fills a trail on one
bar at `bar.h - gap`, so `b.o` is below the level *by construction*. Admitting a trail exit
to the gap test only when its own bar did not set the running extreme drops the count to 0 —
because **1,168 of 1,169 trail exits set their level on their own exit bar.**

---

## 6. WHAT WAS CHECKED AND FOUND SOUND

Negative results, because a hunt that only reports hits is not a measurement.

* **The bar archive's timebase conversion.** Every file in `vps-bars-20260727` carries a
  `.timebase.json` declaring `broker_server_wall_clock`, and `CsvBarSource._rule_for`
  (`replay_policy/generation.py:197-252`) refuses a file without one rather than assuming
  UTC. No research path reads those CSVs raw.
* **Commission fitting.** `build_broker_true_costs.derive_commission:197-290` sums BOTH legs
  of a round turn and normalises `notional_bp` by the entry notional, which is exactly how
  `commission_usd_per_lot` re-expands it. The `notional_bp` kind is provably FX-invariant in
  `commission_r` (the fit's `1/X_snap` and the consumption's `upu` cancel) — which is why
  M4-6 is confined to the `per_lot` kind.
* **Swap night counting.** `rollover_nights` weights Saturday/Sunday midnights at 0 and the
  `swap_rollover3days` weekday at 3, summing to exactly 7 over a full week. `_mt5_dow`'s
  Sunday=0 numbering matches `ENUM_DAY_OF_WEEK`.
* **The spread crossing count.** One crossing per round trip, which is arithmetically right
  for a bid-tape walk (r1's finding is about *where* it is charged, not how many).
* **The statistics layer.** `day_block_bootstrap_p` centres before resampling (imposes H0),
  wraps circularly so no observation is under-weighted, and uses the add-one estimator.
  Benjamini-Hochberg is a correct step-up with monotone q-values; Bonferroni is correct; both
  coerce a non-finite p to 1.0 so an uncomputable null cannot shrink the family.
* **Fold construction.** Calendar-based rather than row-based, purge on label-span overlap,
  embargo measured from the sleeve's own realised holds taken from the *train-side prefix*
  only.
* **Contract geometry.** For every USD-profit instrument on FTMO,
  `trade_tick_value / trade_tick_size == trade_contract_size` exactly (0 exceptions in 102).
  Three redacted_account symbols fail (`LTCUSD`, `XLMUSD`, `VIX`) and none is in any traded
  universe.
* **Live isolation of the percent-denominated gates.** `run_book.py`'s import closure is 84
  `src.` modules; `components.verification`, `side_aware_sizing`, `costs.model` and
  `walkforward.*` are all absent from it.

---

## 7. WHAT I WOULD MEASURE NEXT

1. **The redacted_account capture (M4-2).** It is the only item here that cannot be closed by
   editing code, it blocks a cost-true statement about a sleeve placing real orders, and the
   instruments needed are five: `USOIL.cash`, `UKOIL.cash`, and the index CFDs.
2. **The slippage anchor (M4-4).** One number per symbol — the price displacement, not its R
   — from the same W7 lifecycle capture that produced `0.0132`. Until it exists the term is
   unidentifiable and 6.03 % of the cost basis is a shape rather than a measurement.
3. **The four `MODELLED`-anchor symbols whose cost exceeds one full R.** `XPDUSD`,
   `XPTUSD`, `LTCUSD` and `XRPUSD` have no tick file, so their spread anchor is the bar-
   recorded level times a class factor (`anchor_coverage: MODELLED`). At their own estate
   stop distances the median **total** cost is **1.8395 R** (XPDUSD, n=124), **1.4190 R**
   (XPTUSD, n=139), **1.0240 R** (LTCUSD, n=113) and **0.5735 R** (XRPUSD, n=98) — i.e. no
   win rate makes them profitable under a 1.5R contract. **474 of `asia_pdl_fade`'s 2,827
   trades are on those four symbols**, so a good chunk of a large sleeve's published gross is
   arithmetically dead on a MODELLED number. Nothing in the estate distinguishes "genuinely
   untradeable" from "the bar-to-tick class factor is wrong here"; one tick capture on four
   symbols decides it.
