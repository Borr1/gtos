# r2 — THE GENERATOR. Three defects repaired in `broader_origin_generators.py`

**Lane r2, wave 20, phase 20.** Owner of `src/components/broader_origin_generators.py` this wave.
Whole-population measurement, no sampling: 1,211,077 emissions over eight windows.

Receipts under `phase20/receipts/r2/`. Every number below is reproducible from
`R2_CENSUS_V1.json`, `R2_ARM_ECON_V1.json`, `R2_BLAST_V1.json`, `R2_ATR_DEFS_V1.json`,
`R2_RESULT_V1.json` and the five scripts beside them.

**Line numbers are PRE-repair** where a defect is described (they are the ones d4 cites and the ones
in the parent commit) and post-repair where the repair is described; each is labelled. Post-repair
anchors: the three proximity scopes are `:1286`, `:1496`, `:1564`; the tolerance is `:1759`; the bar
selector is `:2365`; the decision price is `:1125`.

---

## 0. Headline

> **Two of the three defects are one defect: a quantity compared in a unit the contract it
> governs does not use.** The repair lands an R-denominated emission contract in a new unbound
> module and wires it into the generator's three POI sites and its bar selector.
>
> Measured on the same walk, eight windows, 1,167,099 priced emissions:
>
> | | legacy | repaired (HEAD default) | delta |
> |---|---:|---:|---:|
> | gross R / emission | −0.02256 | **−0.00170** | **+0.02086 (92.5 % of the gross negativity)** |
> | net R / emission | −0.10704 | **−0.08209** | **+0.02495** |
> | net R / fill | −0.36111 | **−0.28941** | +0.07170 |
> | emissions | 1,167,099 | 1,117,986 | −4.21 % |
>
> **The 4.21 % of emissions the repair refuses were carrying 26.54 % of the roster's entire net
> loss** (−33,151 R of −124,930 R). All 8 of 8 windows improve. `current_breaker_re_entry` goes
> from **−0.36457 to −0.04011** R/emission.
>
> **This is a measurement correction, not new edge.** The refused rows are orders that could not
> have been placed (a stop-loss on the wrong side of the fill price) or priced against a bar that
> closed hours earlier. Removing them does not make the family positive: the estate's number stays
> **−0.082 R/emission**, and wave 19's SIGNAL verdict is untouched.

---

## 1. What was measured first, independently

`receipts/r2/r2_measure.py` re-derives the population from the eight regenerated close-only
rosters (Session PB harness, unmodified production generator) and the true-UTC M15 lane inputs.
It reproduces d4 exactly and by a different route — the roster stamps the *nominal* bar
(`pbg_run.py:213`, `bar_open=T-15min`), so the selected bar is recovered here the way
`_selected_closed_bar_open` selects it, by bisect on bar close ≤ T + 2 s.

| quantity | r2 | d4 |
|---|---:|---:|
| roster rows, 8 windows | **1,211,077** | 1,211,077 |
| stale-bar decisions | **66,383 (5.4813 %)** | 66,383 (5.48 %) |
| at-market stale subset | **3,883 / 144,725 (2.683 %)** | 3,883 / 144,725 (2.68 %) |
| `current_breaker_re_entry` past-stop | **26.1859 %** | 26.19 % |
| `current_ob_retest` past-stop | **0.1306 %** | 0.13 % |
| `current_fvg_fill` target-through | **84.279 %** | 84.28 % |

### 1.1 Every family, checked for the pathology — not just the breaker

`fill_gap_R = (decision_price − entry) / risk × (+1 LONG, −1 SHORT)`, decision price = close of the
selected closed bar (`broader_origin_generators.py:1085`).

| family | kind | n | past_stop | marketable | resting | target_through | median risk | stale |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `current_breaker_re_entry` | POI limit | 95,051 | **26.1859 %** | 1.7485 % | 9.7463 % | 62.3192 % | 7.41 bps | 3.92 % |
| `current_ob_retest` | POI limit | 270,354 | **0.1306 %** | 0.4350 % | 7.8823 % | 91.5522 % | 8.91 bps | 3.89 % |
| `current_fvg_fill` | POI limit | 700,947 | **0.0000 %** | 1.2900 % | 14.4310 % | 84.2790 % | 7.42 bps | 6.88 % |
| `cross_asset_lead_lag` | at market | 21,678 | 0 | 0 | 100 % | 0 | 6.00 bps | 4.54 % |
| `displacement_continuation` | at market | 39,517 | 0 | 0 | 100 % | 0 | 16.23 bps | 2.22 % |
| `liquidity_sweep_reclaim` | at market | 43,751 | 0 | 0 | 100 % | 0 | 7.82 bps | 2.49 % |
| `structural_distance_extreme` | at market | 23,923 | 0 | 0 | 100 % | 0 | 3.12 bps | 3.43 % |
| `session_open_range_break` | at market | 8,195 | 0 | 0 | 100 % | 0 | 17.94 bps | **0.00 %** |
| `volatility_compression_expansion` | at market | 5,341 | 0 | 0 | 100 % | 0 | 33.45 bps | 1.89 % |
| `regime_transition_break` | at market | 2,320 | 0 | 0 | 100 % | 0 | 43.59 bps | 0.47 % |

**The seven at-market families carry `fill_gap_R = 0` on 144,725 of 144,725 rows** — zero rows with
a non-zero gap, in any window. The entry IS the decision-instant close, so the pathology is
structurally impossible there. It is a POI-limit phenomenon and it is concentrated in one family:
`current_breaker_re_entry` supplies **24,890 of the 25,243** past-stop emissions (98.6 %), and
`current_ob_retest` the other 353.

**`current_fvg_fill` has ZERO past-stop emissions in 700,947** — its own `poi_filled` /
`poi_invalidated` checks (`:1275-1290`) deny a gap the market has already traded through, which is
the one place the existing contract already did this job.

### 1.2 The stale-bar age distribution, and why the threshold is one period

| selected-bar age | rows | cumulative |
|---|---:|---:|
| **0 (the bar that just closed)** | **1,144,694** | 94.52 % |
| 15 min (one bar missing) | 8,186 | 95.19 % |
| 30 / 45 / 60 min | 8,138 / 8,117 / 8,109 | 97.21 % |
| 75–180 min | 12,527 | 98.45 % |
| > 180 min (session/weekend, out to 7,335 min) | 18,706 | 100.00 % |

Displacement between the emitted at-market entry and the **next actual print**, in R, per age
bucket — this is the quantity that decides the threshold:

| family | one missing bar (0 < age ≤ 15 min) | 15–60 min | 60–240 min |
|---|---|---|---|
| `cross_asset_lead_lag` | median **1.931 R**, 70.5 % > 1 R | 1.889 R | 3.399 R |
| `structural_distance_extreme` | median **2.768 R**, 74.6 % > 1 R | 2.768 R | 6.394 R |
| `liquidity_sweep_reclaim` | median **1.802 R**, 67.8 % > 1 R | 1.811 R | 2.721 R |
| `displacement_continuation` | median **1.076 R**, 51.5 % > 1 R | 1.076 R | 1.001 R |
| `volatility_compression_expansion` | median 0.982 R, 41.7 % > 1 R | 0.982 R | 0.388 R |

**There is no safe positive age.** The displacement is already ≥ 1 R for half to three quarters of
rows at a *single* missing bar, and it does not start small and grow — it starts large. So the
budget is set to **one timeframe period**: the selected bar must be the bar that just closed, with
no bar missing between it and the decision instant. That is 94.52 % of the population and it is the
only threshold the data supports.

---

## 2. The repairs

New module: **`src/components/broad_origin_emission_contract.py`** — pure predicates, no dependency
on the generator, unit-tested separately. Wired into `broader_origin_generators.py` at four sites.

### 2.1 Defect A — born past its own stop. REFUSE TO EMIT.

The brief asked for the choice to be argued. **Refuse**, and the argument does not rest on any
walker convention:

> For a LONG with `fill_gap_R < −1`, the decision price sits BELOW the stop. A buy limit above the
> market is marketable, so the order fills at once — and it opens with its **stop-loss above its own
> fill price**. That is a stop on the wrong side of the trade. There is no market state in which it
> expresses the family's thesis, and no broker that treats it as a valid stop.

It is algebraically guaranteed, not incidental: `gap < −1 ⟺ price < entry − risk = stop < entry`.
Pinned behaviourally in `tests/test_broad_origin_emission_contract.py::
test_a_past_stop_candidate_has_its_stop_on_the_wrong_side_of_the_market` and end-to-end on the
generator's own published geometry in `tests/test_broad_origin_emission_repairs.py::
test_the_legacy_escape_hatch_emits_that_same_malformed_candidate`.

The measured consequence, priced on the estate's own walker and broker-true cost basis:

| | n | share of walked roster | fill rate | net R / row | CI95 |
|---|---:|---:|---:|---:|---|
| **refused: past_stop** | 23,773 | 2.04 % | **100.00 %** | **−1.30135** | [−1.30615, −1.29656] |
| refused: stale bar | 25,340 | 2.17 % | 19.98 % | −0.08737 | [−0.09407, −0.08066] |
| kept | 1,117,986 | 95.79 % | 28.37 % | −0.08209 | [−0.08329, −0.08090] |

> **The stale row's economics is the weakest number here, and in the direction that understates it.**
> The walk covers 1,167,099 of the 1,211,077 emitted rows (96.4 %) but only **25,340 of the 66,383
> stale rows (38.2 %)** — a row is dropped when the M1 tape has no forward prints at its decision
> instant, which is precisely what a deep session gap looks like. So −0.08737 R/row is measured on
> the *least* stale 38 % of the population; the 62 % the walker could not price are the ones sitting
> in the deepest holes. The stale repair does not rest on this number in any case: those entry prices
> were never available at all, which is a correctness argument, not an economic one.

**Emit-and-mark was considered and rejected**, for a measured reason: the only executability model
on the path, `predecision_limit_fillability_from_geometry`
(`poi_execution_lifecycle.py:163-178`), scores `limit_marketable` at the top (0.92) **without
reference to the stop**, so a past-stop candidate would be ranked first by the very signal meant to
rank executability (d4 §7.3). Refusing closes that exposure at the source without touching another
lane's file. Everything that IS emitted is marked — see §2.2.

> **A correction to d4 §7.3, from this lane's own measurement.** The claim is structurally true of
> the predicate and has **zero measured incidence**. The fillability model is computed at exactly
> one call site — `broader_origin_generators.py:1348`, inside the `fvg_fill` branch — and
> `current_fvg_fill` produces **0 past-stop emissions in 700,947**. The two families that DO produce
> them compute no fill probability at all. Measured over 238,624 fvg rows carrying a probability
> (three DIAG windows), the top fillability decile is 81.0 % `resting`, 16.6 % `marketable`,
> 2.4 % `target_through` and **0 `past_stop`**. The model does not, in fact, rank structural death
> first — because it never sees any.

### 2.2 Defect B — the unit mismatch. THE RADIUS IS NOW IN R, BOTH SIDES.

`_current_framework_proximity_tolerance` (pre-repair `:1599`, now `:1759`) returns a fraction of
price (1.0 %) and was the sole admission test at pre-repair `:1200`, `:1390`, `:1445`. Against a median risk of 7.41–8.91 bps that is an
**11.2–13.5 R-wide gate on a 1.5 R trade**.

The repair keeps the percent test as what it actually is — a **visibility scope**, "which zones are
near enough to consider" — and adds the **admission** test in the trade's own risk unit:

```
fill_gap_r ∈ ( −1 , +max_admission_gap_r )      # equivalently:  stop < price < target
```

with `refuse_past_stop` (the hard floor, default **ON**), `min_admission_gap_r` (near side, default
**None**) and `max_admission_gap_r` (far side, default **None**). Every emitted POI candidate now
publishes `poi_fill_gap_r` and `poi_admission_bin` at top level, and the generation audit carries a
reconciled per-family partition (`gtos.broad_origin_poi_admission_partition.v1`). That is the
emit-and-mark half: the two families that compute no fill probability now publish an executability
quantity for the first time.

**The two radius dials ship OFF, and that is an evidence decision, not caution.** Net R per FILL
across the far-side sweep, pooled:

| far-side radius | emissions kept | net R / emission | **net R / fill** |
|---|---:|---:|---:|
| **None (default)** | 95.79 % | −0.08209 | **−0.28941** |
| `rr` = 1.5 | 23.62 % | −0.23134 | −0.29097 |
| 3.0 | 38.83 % | −0.17009 | −0.28838 |
| 5.0 | 54.90 % | −0.13245 | −0.28869 |
| 10.0 | 77.95 % | −0.09917 | −0.28887 |

**The far-side radius is economically inert**: it discards up to 76 % of emissions to move net per
fill by ±0.002 R. It also makes the per-*emission* headline much worse, because what it deletes is
the zero-cost non-fill population. It is a ranker-hygiene dial, priced and available, not a repair.

The near-side dial at `0.0` (refuse already-marketable limits) is the one with real content —
net/fill −0.28356 (+0.00585) and roster gross turns **positive, +0.00137** — and it still ships OFF,
because that bin's measured economics are **convention-dependent**: `walk_limit2` fills a marketable
limit AT the limit price, whereas a real marketable buy limit fills at the market, which for a LONG
is a *better* price than the limit. The measurement is biased against that bin in both tails. It is
1.0 % of POI emissions and it is a priced owner dial, not a correctness fix.

### 2.3 Defect C — stale bars. MAX AGE = ONE TIMEFRAME PERIOD, FAIL CLOSED.

`_selected_closed_bar_open` (pre-repair `:2179-2199`, now `:2365`) gains a maximum-age budget, applied to **both** paths —
the walk-back and the `candle_open_utc`/`candle_close_utc` fast path, so declaring a stale bar
cannot bypass it. The newest closed bar is the only candidate the test needs to consider (every
earlier bar is strictly older), so one check decides the walk. Refusal returns no candidates for
that symbol-instant with generation-audit status `stale_selected_closed_bar` and a selected-bar
receipt carrying the measured age.

The same budget is passed to the **cross-asset leader** series (`:1028-1035`): a leader whose last print
is stale cannot establish a lead-lag impulse against a fresh lag bar. Measured effect of that
choice: **zero additions** across 120,518 frozen rows (see §3) — the leader path in principle could
substitute the next leader in `LEAD_LAG_PAIRS`, and in the measured population it never does.

---

## 3. Blast radius — two-sided, against a frozen pre-repair snapshot

`receipts/r2/r2_blast.py`. Both directions are required: reproduction alone would pass a repair that
did nothing; subtraction alone would pass a repair that also perturbed the survivors.

**(1) Reproduction.** With the escape hatch set to the legacy contract, the regenerated roster is
**exactly** the frozen wave-19 roster on `(decision_time, symbol, family, side, entry, stop, target,
candidate_id)`.

**(2) Subtraction.** At HEAD defaults the emitted set equals the frozen set MINUS exactly the rows
an independent recomputation predicts, with no additions and no survivor whose geometry moved.

| window | frozen | repaired | added | removed | **removed == predicted** | survivors moved |
|---|---:|---:|---:|---:|:---:|---:|
| 2025-10 | 174,497 | 163,297 | **0** | 11,200 | **yes** | 0 |
| 2025-11 | 151,233 | 139,890 | **0** | 11,343 | **yes** | 0 |
| 2025-12 | 170,997 | 150,074 | **0** | 20,923 | **yes** | 0 |
| 2026-01 | 153,598 | 144,419 | **0** | 9,179 | **yes** | 0 |
| 2026-02 | 129,287 | 122,440 | **0** | 6,847 | **yes** | 0 |
| 2026-03 | 130,051 | 124,109 | **0** | 5,942 | **yes** | 0 |
| 2026-04 | 147,123 | 134,538 | **0** | 12,585 | **yes** | 0 |
| 2026-05 | 154,291 | 142,093 | **0** | 12,198 | **yes** | 0 |
| **total** | **1,211,077** | **1,120,860** | **0** | **90,217** | **8 / 8 exact** | **0** |

Removals decompose to **66,383 stale-bar + 23,833 past-stop + 1 stale cross-asset leader** (a
further 1,410 past-stop rows sit inside the stale set and are attributed there, which is why this
23,833 is below the census's 25,243).

**The single stale-leader row is worth naming**, because it is the one case where the repair could
in principle have *substituted* rather than subtracted: `USOIL_cash`, 2025-12-31 20:15 UTC. WTI
printed a 20:00 bar; Brent (`UKOIL_cash`, its only leader) stopped at 19:45 on New Year's Eve. The
legacy contract built a lead-lag candidate from the stale leader; the repair refuses it. One
emission in 1,211,077, and **zero additions in any window** — the substitution path never fired.

Test-suite A/B against the parent state, `scripts/pytest_failset.py`, full suite, both sides
captured this session (`receipts/r2/FAILSET_R2_{BEFORE,AFTER}.json`):

| | before | after |
|---|---:|---:|
| bad (failed + errored) | **95** | **95** |
| regressed | — | **0** |
| passed | 12,426 | **12,464 (+38, exactly the new tests)** |

The two failure sets are **identical as sets**, not merely equal in count.

> **One tooling note, because it silently voids any capture taken in this shell.**
> `scripts/pytest_failset.py` matches `^(FAILED|ERROR)` against pytest's short summary. This
> environment exports `FORCE_COLOR=3`, so pytest emits `\x1b[31mFAILED` even into a pipe and the
> regex never matches: the first capture here recovered **0 ids against 94 reported failures**. The
> tool flags that (`usable_as_baseline: false`), so nothing was silently wrong — but every capture
> must be taken as `env -u FORCE_COLOR NO_COLOR=1 python3 scripts/pytest_failset.py …`, which is how
> both sides above were taken.

---

## 4. Isolation from armed money — verified, not assumed

**BOTH funded accounts are armed.** The broad-origin generator has never traded live, and this was
verified rather than taken on trust:

- `run_book.py`'s transitive import closure is **107 modules and contains neither
  `broader_origin_generators` nor `broad_origin_emission_contract`.** Pinned behaviourally by
  spawning a clean interpreter, importing the live entrypoint and reading `sys.modules`
  (`tests/test_broad_origin_emission_repairs.py::test_the_live_book_entrypoint_does_not_import_this_generator`).
- The live book generates through `src/components/ultimate_book/book_engine.py`, whose sleeve set
  comes from `sleeves/registry.py::active_specs` (`book_engine.py:33`). The five armed tags —
  `crypto`, `energy_agri`, `sub_xvol_pullback`, `mx_btcusd_d1_donchian_20_breakout` — resolve
  through that registry and **none of their generator callables lives in either module**.
- No origin family this generator emits is a sleeve name.

**H1, re-derived this session rather than quoted.** `src/components/broader_origin_generators.py` and
the new `src/components/broad_origin_emission_contract.py` are in **neither** R2's 43 bound paths
**nor** `code_authority_paths` (`replay_acceleration_attempt5_typed_sparse_runner.py:1405-1484`).
**No config byte moved**: all four runtime keys are absent from every file under `config/`, so the
code default is the shipped behaviour and the bound `config/agent_config.yaml` is untouched. No
sealed contract was regenerated and no new option was spent.

---

## 5. What this does NOT do

- It does not make the broad V4 family tradeable. Repaired, the roster still books
  **−0.08209 R/emission**; wave 19's three limbs (sub-spread scale, no accumulation, bid-side bars)
  are untouched and the SIGNAL verdict stands.
- It does not repair the bid/ask geometry (wave-19 defect 1). Every number here is on the same
  bid-series walker as wave 19, so the comparison is like-for-like; the constant-sign trigger
  displacement applies equally to both arms.
- It does not touch `poi_execution_lifecycle.py`'s fillability model. §2.1 measures that the model's
  known flaw has zero incidence once past-stop candidates are refused.
- It does not touch the clock defects d4 §5 found (two disagreeing session functions, DST-wrong
  labels, `session_open_range_break` measuring the wrong range). Those are a separate repair.

## 6. A fourth defect, measured and NAMED rather than changed

d4 §7.2 found two ATR definitions inside one candidate. Re-measured here on the whole population —
**611,854 M15 bar-instants across all 24 symbols**, 110x d4's 5,585-instant sample
(`receipts/r2/R2_ATR_DEFS_V1.json`):

| | MSO `calculate_atr` / module `_atr` |
|---|---:|
| median | **1.0234** (d4 sample: 1.0141) |
| p05 / p95 | 0.833 / 1.365 (d4: 0.823 / 1.383) |
| **share outside +/-10 %** | **48.30 %** |

The POI stop buffer is built from the market-state **Wilder true-range** ATR
(`market_state.py:461-478`, via `_current_framework_atr`), while every `predecision_features` value —
including `stop_distance_atr`, the field that says how wide the stop is in ATRs — normalises by the
module's own **mean(high - low)** ATR. Nearly half the time those differ by more than 10 %, so the
published "stop is X ATRs wide" is not the X the geometry used.

**The repair is a provenance stamp, not a geometry change.** Every POI candidate and the generation
audit now carry `atr14_source`. Which ATR *should* size a stop is a strategy decision with no
measured economic case either way, and it is Borhen's; silently switching it would have moved every
POI stop in the estate. Proven purely additive: three days spanning October 2025 (19,240 emissions)
regenerated after the stamp are **identical on every compared key** to the same days generated
before it.

## 7. Files

| path | what |
|---|---|
| `src/components/broad_origin_emission_contract.py` | new, unbound: the R-denominated predicates and the policy |
| `src/components/broader_origin_generators.py` | wired at the three POI sites, the bar selector, the leader series and the audit |
| `tests/test_broad_origin_emission_contract.py` | 20 unit tests of the predicates |
| `tests/test_broad_origin_emission_repairs.py` | 17 behavioural tests: refusals, marks, ledgers, blast radius, live isolation |
| `phase20/receipts/r2/R2_CENSUS_V1.json` | the whole-population census |
| `phase20/receipts/r2/R2_ARM_ECON_V1.json` | arm economics, gap_r bands, the stale-age table |
| `phase20/receipts/r2/R2_BLAST_V1.json` | the two-sided blast-radius proof |
| `phase20/receipts/r2/r2_*.py` | every script that produced them |
