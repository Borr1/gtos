# Session CD — the broad family under the repaired stack

**Wave 14, blocks B2250–B2299. Branch `phase14/broad-regeneration`.**
Commission: `phase14/SESSION_CD_BROAD_REGENERATION.md`. Owner authority: the
2026-07-31 training-lane ratification. Receipts: `phase14/receipts/`.
A/B: `phase14/receipts/SESSION_CD_AB.md` (tool-emitted `gtos-ab-receipt-v1`).

**Surface disclosure, carried into the prose because the agreement requires it
there and not only in the row:** every economic number in this document is
measured on **January 2026, which is `VAL` on the lane's surface axis** — the
survivor book's own selection surface (`d.year >= 2025`,
`build_survivor_book.py:74` / `KB7_growth_kelly_sizing.py:130`). Ranking and
gradient checks only. Nothing here is admission evidence, nothing here bills the
candidate family, and no headline expectancy is quoted from VAL alone.

---

## 0. Findings first

**1. Two of the four commissioned repairs reach the B7.5 replay path, and they
push in opposite directions.** The commission named broker-true commission, the
spread-geometry floor, the broker clock and the time-stop contract. Measured
against the code:

| repair | reaches replay? | direction | mechanism |
|---|---|---|---|
| broker-true commission | **YES** | charges **more** | `v4_timewarp:58965` hardcodes `"commission_r": 0.0` |
| swap horizon | **YES** (a defect of the same CLASS as AQ's) | charges **less** | the swap model prices 32 M15 bars = 8 h on a path whose expiry is 120 min |
| spread-geometry floor at generation | **NO** | — | already enforced at admission; the generator never sees a tick |
| broker clock | **NO** | — | baked into the sealed source *and* the prepared day packs |
| AQ's time-stop contract | **NO** | — | the replay has no sleeve identity in its exit path at all |

The two that do not apply are findings, not failures, and each is filed with its
cite in `train_engine/repairs.py::REPAIRS_THAT_DO_NOT_APPLY` so the next session
is refused with the reason rather than left to rediscover it.

**2. F38 is worse than "the sum omits a term": the control exists and it
passes.** `broker_net_cost_engine.py` requires a commission model
(`selected_cell_commission_model_required: true`, `agent_config.yaml:730`) and
checks it by asking whether a STRING is in an allow-list
(`:729-735`). The replay stamps that string itself —
`gtos_vnext_commission_model_status = "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK"`
at `v4_timewarp:58899` — and then writes `commission_r: 0.0` at `:58965` with the
source `"commission_included_in_selected_cell_risk_status"`. So the requirement
is satisfied by an assertion about the accounting, and the accounting is zero.
A gate that reads a self-emitted claim is not a gate.

**3. The clock under the sealed January window is broker wall clock mislabelled
as UTC, and the whole month is +2.0 h ahead of true UTC.** [MEASURED, B2255.]
The replay path contains no clock code at all — `broker_clock|pytz|ZoneInfo|EET|
America/New_York` across the timewarp loop, both B7.5 runners, the allocator,
`selector_v4`, the prepared-day-pack module, the integrated typed source and the
wave4r microstructure returns one hit and it is a prose comment. Every timestamp
is relabelled naive→UTC by `wave4r_replay_microstructure.parse_utc:130-142`. The
sealed bundle's own series settles the timebase: across 54 weeks of
`006_AUDUSD_M15.csv` the weekly open is `Mon 00:00` in **54 of 54** weeks,
DST-invariant across both the US and the EU transitions, which a true-UTC FX
series cannot be. The exporter that produced it did
`datetime.fromtimestamp(ts, tz=timezone.utc)` on a broker-wall-clock epoch and
was repaired on 2026-07-26 — **three days after the January bundle was sealed on
2026-07-23**. Consequence for the estate: **every hour-of-day statement about the
January pool is shifted two hours**, including AW's 81-cell `B_TIME` axis. It is
not repairable by rebind (§2.4) and it is not a reason to distrust the
economics — a uniform shift moves no R.

**4. THE REGENERATION IS DONE, AND THE REPAIRS MAKE THE FAMILY WORSE.** Four
January arms, full month, measured against the SEALED arms of record streamed in
place through AW's own reader — which reproduces his published aggregates
**exactly** on all four (scoreable-row delta **0**, net-R relative gap
**0.00e+00**), so the frozen column is the artifact the estate's verdict rests on
and not a lookalike:

| arm | frozen | repaired | **Δ** | gross frozen | gross repaired | trades |
|---|---:|---:|---:|---:|---:|---:|
| S0R0 | −0.858511 | −0.882234 | **−0.023723** | −0.219928 | −0.219755 | 63 |
| S1R0 | −0.858142 | −0.882060 | **−0.023918** | −0.219779 | −0.219744 | 55 |
| S0R1 | −0.858310 | −0.882112 | **−0.023802** | −0.219805 | −0.219677 | 61 |
| S1R1 | −0.857873 | −0.881931 | **−0.024058** | −0.219608 | −0.219638 | 54 |

**21 of 21 trading days negative, on every arm, on both sides.** The commission
the ENGINE charged is **0.065462** against AW's independent post-hoc estimate of
**0.0654** — two different computations, four decimal places. Swap falls
**4.01×**. And **gross moves by +0.000145**: the repairs cannot touch the
directional edge, because the pool loses **0.22 R/row before any cost is charged**
and the entire repair budget is 0.024.

Killing the 17.71 % cost tail takes the pool from **−0.882 to −0.493 R/row** — an
enormous move that still lands nowhere near break-even. AW's out-of-window result
(the sealed limit taking `asia_pdl_fade` from −0.902 to +0.095 R/day) does not
transfer; §3.4 says why.

**5. The two switches move the trade set and not the pool.** 63 / 55 / 61 / 54
trades across the factorial — a 17 % spread — for 0.0003 R/row of pool
difference. Charging commission at the 0.15 ceiling changed the refusal set on
**18,728 of 154,390 candidates (12.1 %)** and the pool did not care.

**6. AW's separability answer survives the repairs, and narrows.** Re-asked of
the regenerated pool with the split, the cut rules and both outcomes declared
first: **0 of 71–76 cells are net-positive on TRAIN**, frozen or repaired, on
either arm tested. Gross-positive cells go **2 → 1** under repairs and none
survives the holdout. The run's TRAIN baseline reproduces AW's published
`−0.917554` / `−0.200465` to six decimals, which is what licenses reading the two
as the same measurement.

**7. DISK, not RAM, bounds a month-scale arm here — and CB's RSS assumption is
PARTLY FALSIFIED at month scale (§4.2), including by my own earlier reading of it
in this session.** Peak RSS is **3.66–4.49 GB** per month arm against **2.46 GB**
on the 2-day fixture: it grows ~1.5–1.8× with window length, not "not
materially". I published the opposite mid-session on a 60-second `ps` trace that
cannot see a spike lasting seconds. Separately and still true: a 2-day January
fixture writes a **927,473,101-byte** route with one working day in it — MISSED
473 MB / 8,807 rows, DECISION 239 MB / 4,608 rows, SCORECARD **174 MB / 96 rows**
(1.8 MB per row) — so one unprojected January arm is ~16 GB against the 21 GiB
free at the time, and four concurrent arms could not run. CB measured memory and
concluded four arms were affordable; both measurements are right and the binding
one had not been taken.

**8. The lane logs itself now, and Session CD's runs are the first rows the
iteration ledger has ever carried** — 10 looks, all `VAL`, all `billed: false`. `--purpose LANE_ITERATION` authorizes a
window on the SURFACE axis without consulting the fitting axis — which is the
only reason a `SEALED`-role January window is legal to iterate on — and every arm
auto-writes one unbilled row with the surface computed from the days the guard
enumerated, not from a caller's label.

**9. Every declared prediction about the repairs landed, and the one that did
not was falsified in DIRECTION.** `CD_PREDICTION_V1.json` was written before any
month arm was launched, because AW's decomposition already prices every term this
session injects and a prediction written afterwards is not one. On the one
working day of the sealed fixture, pool mean R per scoreable row:

| run | repairs | mean R/row | Δ vs frozen | commission | swap |
|---|---|---:|---:|---:|---:|
| VB | none | **−1.131641** | — | 0.000000 | 0.069139 |
| VD | commission only | −1.193523 | **−0.061882** | 0.064053 | 0.069054 |
| VE | swap horizon only | −1.082818 | **+0.048823** | 0.000000 | 0.017218 |
| VF | both, commission gated | −1.152236 | **−0.020595** | 0.064203 | 0.017225 |

Predicted −0.065 / +0.041 / −0.024. The swap term falls **4.015×**, i.e. exactly
linear in the 32 → 8 bar change. The sum of the singles is −0.013059 and the
combination measures −0.020595, so **−0.007536 of it is the gating interaction** —
the one number here that had to be measured rather than derived from AW.

**10. The family is negative before a single unit of cost, and the entire repair
budget is an order of magnitude too small to matter.** Gross-before-any-cost is
**−0.223571** frozen and **−0.230830** fully repaired, against AW's sealed-month
−0.2199. The repairs move the pool by 0.02 R/row and the hole is 0.22 R/row. This
is the finding the session exists to produce, and it says the honest label for
the broad family is no longer `UNTESTED_UNDER_REPAIRS` — but it is also not
"dead": what the evidence supports is **negative under repairs, on VAL, with the
repairs measured and the gross deficit unexplained by cost**.

---

## 1. CD-1 — the lane-iteration purpose

`train_engine/guard.py` (amended) and `train_engine/lane.py` (new).

### 1.1 The third purpose, and why the surface gate is unconditional

Sessions CB and CC built two halves that had never been connected. CB's guard
knows whether a day may be **FITTED** on (`Disposition.trainable`); CC's
`SurfaceMap` knows whether the lane may **ITERATE** against it. They disagree on
purpose, and the disagreement is what makes this session legal:

```
2026-01-01 .. 2026-01-31   role = SEALED (not trainable)   surface = VAL (iterable)
```

`PURPOSE_LANE_ITERATION` checks the second and never the first. Consequently it
can never emit a TRAINING artifact — not by a flag, but because
`may_emit_training_evidence` reads `trainable_checked`, which a lane look never
sets.

The surface gate itself is applied on **every** path, including
`ACCEPTANCE_REPRODUCTION`, and that is the ratification's own tie-break ("the
more restrictive disposition wins"): reading a day is reading it whatever the
purpose says, and there is no purpose under which the live forward stream is
readable. It is strictly a tightening — CB's 24 guard tests pass unchanged, and
the new refusals are the live stream (2026-07-29 →) and the declared uncovered
gap (2026-06-01 … 07-28).

One bug avoided by having read CB's own §5.1 first: `SurfaceMap.assert_iterable`
raises `SurfaceRefusal`, which is **not** a `PartitionRefusal`, so a caller
writing `except WindowRefused` — which the module's own docstring invites — would
have let a TEST-surface refusal escape as an unrelated error. It is re-raised as
this module's type, with a test.

### 1.2 What a lane run emits

| purpose | artifact | gate |
|---|---|---|
| `TRAINING` | `TRAIN_TRADE_TABLE.jsonl` | `trainable_checked` |
| `LANE_ITERATION` | `LANE_TRADE_TABLE.jsonl` + one iteration-ledger row | `surface_checked` |
| `ACCEPTANCE_REPRODUCTION` | neither | — |

Two emitters, two stamps, two authorization properties. Each checks the
**authorization object**, never the caller's intent, so the stamp on a file
cannot outrun the gate that actually ran. Both crossings are pinned by tests.

### 1.3 The look, and the three things it cannot forge

`lane.log_look` passes `days=authorization.days` rather than a span, on purpose:
the guard already enumerated the calendar the ENGINE will replay, so the surface
stamp covers exactly the days that were read. A span would let a caller widen or
narrow the recorded window relative to the run.

No `engine_reserved_blackout` is declared, and that is a claim rather than an
omission — the guard refuses the blackout on every path, so a window that reaches
the logger contains no blackout day to drop, and declaring one would be refused
by the ledger as "a filter, not a blackout".

The ledger's own refusals do the rest: the surface is computed, `billed` is
written `false` by the module, and `admitted`/`rejected`/`graduated` raise. That
last one matters most for **this** session — Session CD is the one most tempted
to write down "the family is rejected" — and there is a test that says so.

---

## 2. CD-2 — the repairs, one at a time, each with a control

### 2.1 The control pattern, and why "the flag is off" is not one

Every repair ships with an inert twin that installs the **same wrapper on the
same symbol** and computes the **same per-candidate quantity**, then applies a
neutral value. Running without the flag proves only that an un-applied patch does
nothing; running the wrapper with a neutral charge proves the *plumbing* is inert,
so every difference the live repair produces is attributable to the NUMBER.

Measured on the sealed 2-day January S1R1 fixture, at zero tolerance, over the
trade multiset, the order multiset, all four ledger row counts and the
missed-opportunity pool aggregate:

| comparison | verdict |
|---|---|
| safe cut set → + `ledger_scalar_projection` | **`OUTCOME_IDENTICAL`** |
| + projection → + both repair wrappers, neutral | **`OUTCOME_IDENTICAL`** |
| CB's default 6-patch set → the H-CB-2 safe 4-patch set | **`OUTCOME_IDENTICAL`** |

The third row was free and is worth more than it cost. The orchestrator's H-CB-2
run measured three of CB's memos disagreeing per call — `probability_debate_v4.
_stable_sha256` on **100 %** of its 8,810 hits — and concluded the values do not
feed a decision on that fixture. This measures the same conclusion from the other
side: with those memos **off**, the arm produces the same trades. Both directions
now agree.

### 2.2 Repair 1 — broker-true commission (F38)

`v4_timewarp.broker_calibrated_replay_cost_packet` is rebound. The charge is
AW's, verbatim, so the regenerated pool is charged with the same number AW
charged the sealed pool with:

```
commission_r = commission_usd_per_lot(entry_price)
             / (sl_distance_price * usd_per_price_unit_per_lot)
```

— `src/costs/model.py` over
`research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`,
FTMO account, symbols resolved through
`config/profiles/operator_profile.yaml`. Commission in R is a property of
the **trade**, not of the instrument, because the denominator is the stop
distance; a test pins that halving the stop doubles the charge.

An instrument the layer cannot price is **counted and left uncharged**, never
defaulted to zero — defaulting to a plausible number with no basis is what F38
was. A test asserts all 24 replay symbols price.

**Two variants, because a post-hoc charge and an in-gate charge are different
experiments.** `build_pretrade_cost_packet` computes `refusal_reasons` and sets
PASSED/REFUSED *before* returning (`:701-704`), and one of those reasons is
`total_cost_r_exceeds_limit` against `selected_cell_pretrade_max_total_cost_r`
(0.15). So:

* `commission_broker_true` — selection held fixed, accounting repaired. Isolates
  "what did the missing term cost", which is F38's own question.
* `commission_broker_true_gated` — the ceiling is a ceiling on TOTAL cost, so a
  candidate that only passed because commission was invisible is now refused.
  Changes which candidates execute.

Running only the second would confound the accounting effect with a selection
effect with no way to separate them afterwards.

### 2.3 Repair 2 — the swap horizon (AQ's defect class, pointing the other way)

`attempt5:10276-10278` sets
`broad_live_as_if_replay_pretrade_swap_cost_time_stop_bars = 32` and
`selected_cell_swap_cost_minutes_per_bar = 15`, so the swap model prices
`holding_days = 32 × 15 / 1440 = 0.3333` — **eight hours**
(`broker_net_cost_engine.py:372-382`). The replay's expiry is
`min(asof + 120 min, decision_day 00:00Z + 1 day)`
(`REPAIRED_PENDING_EXPIRY_MINUTES = 120`, `attempt5:116`, applied at `:16164`
and `:16745`; expiry built at `v4_timewarp:85864-85866`), and the same bound
clamps the terminal path query — so **no B7.5 position can be held for 121
minutes**.

The replay therefore charges a 4×-too-long carry on every candidate. It is the
same class of defect AQ repaired live — a horizon constant that does not describe
the contract the engine runs — pointing the opposite way: AQ's live stop was 80×
too **short**, this one is 4× too **long**.

### 2.4 The three repairs that do not apply, with their cites

**AQ's time-stop contract has nothing to port into.** The B7.5 replay never
imports `execution_packets`, never reads `SLEEVE_EXIT_PROFILES`, and has no
sleeve identity in its exit path at all. Its exit is first-touch target/stop
(`wave4r_replay_microstructure._infer_ordered_path`) with an expiry
mark-to-market that is *named* `filled_time_stop_close_mark`
(`v4_timewarp:63411-63412`) and is a wall clock, not a bar count. A
`PolicySpec.time_stop_bars` exists in a diagnostic overlay and is inert on the
sealed config for two independent reasons: the geometry contract puts
`time_stop_bars` under `thesis_horizon` while the replay reads
`target_destination` (a real key-path miss), and the router returns
`momentum_exhaustion` for every candidate, whose horizon keys all resolve `None`.
A live sleeve's 7,680 M15 bars is 80 days.

**The spread-geometry floor is already enforced at admission, and a
GENERATION-time floor is not rebind-reachable.** `agent_config.yaml:715-716`
declares `selected_cell_pretrade_max_spread_r: 0.10` and
`selected_cell_pretrade_max_total_cost_r: 0.15`;
`pretrade_cost_refusal_reasons:718-728` and `:772-776` enforce them and
`v4_timewarp:86204-86224` turns the refusal into `risk_decision: "reject"` with
`final_approved_risk_pct: 0.0`. The broad generator sees closed OHLC bars and
never a tick (`rg -n "spread" src/components/broader_origin_generators.py` → no
hits). AY's `ultimate_book/spread_geometry.py` is imported by `run_book.py` and
`book_engine.py` only — a live-path artifact that does not reach replay.

> **And a correction to AW that any future citation must carry.** AW's headline
> "4,701 rows (16.5 %) carry a cost above 1 R" masks on **`cost_r`** — the
> packet's `total_cost_r` = spread + slippage + swap — not on `spread_r`
> (`aw_separability_mine.py:939` sets `cost = jan["cost_r"]`, `:962` counts
> `(cost > 1)`), while his inline note at `:960` describes `spread_r`. The two
> are different columns. Session CD's loss-concentration table restates the band
> on the column it actually measures and says which.

**The broker clock is refused on a sealed window by three independent
fail-closed layers**, not by absence. (1) There is no clock code on the path at
all. (2) The typed cache's identity key includes
`normalizer_code_root_sha256 = _file_sha256(...)`
(`replay_acceleration_integrated_source.py:111-118`, `:237`), and a runtime
rebind moves no file byte, so the key is unchanged and the cached partition is
reused. (3) A cold rebuild fails closed anyway — `load_or_build_partition`
compares the fresh rows digest against the bundle's sealed
`normalized_root_sha256` (`:345-349`). And the clock is already baked into the
sealed prepared day packs, whose candidates carry `kill_zone` / `session` /
`utc_hour_bucket` computed at pack-build time. A clock repair here is a
**re-materialisation, not a rebind** — a different session, and one that would
have to re-seal.

### 2.5 The enabling cut — `ledger_scalar_projection`

Finding 4 made this mandatory rather than optional: without it the commissioned
regeneration cannot run on this disk at any speed.

`append_jsonl` in the attempt5 runner is the ONE function every ledger write goes
through, and the path names the ledger. The cut wraps it with a **generator**, so
nothing is materialised, and writes top-level scalars only to the DECISION and
SCORECARD ledgers, where 91.6 % and 87 % of a row respectively is nested
provenance. Row counts are unchanged — and counts are what
`identity.compare_economics` gates. `bench._prune_row` already drops every
dict/list before comparison, so the scalars the cut writes are exactly the
scalars the comparator compares.

`MISSED_OPPORTUNITY` is left whole. It is AW's substrate, its aggregate IS gated,
and the pool reader digs three columns out of one nested container on it.

Measured: **927 MB → 489 MB, 1.90×**, `OUTCOME_IDENTICAL`.

A second, sharper cut exists and is **off by default**:
`missed_pool_projection` writes only the declared pool columns — 101 names
**derived from `b7_5_diagnostic_pool.FEATURE_FIELDS`** rather than typed out, so
a column added to the reader is kept automatically. Predicted 17.7 % of bytes
from a sample; **measured in production at 428 MB → 77 MB per working day, 5.56×,
with 77 keys kept and 399 dropped per row**. It is the one cut in the lane that
can lose something a later session wanted, so the posture is: keep a reference
arm whole and project the arms measured against it.

**Session CD did not follow its own posture, and the reason is worth stating
rather than hiding.** Every arm here — including the frozen comparand — is
projected, because concurrency was re-planned on the disk measurement (§4) and
an unprojected reference arm cost 9 GB of the 18 GiB available. The posture is
still satisfied, by a different artifact: **the full-fidelity frozen January
arms already exist as the sealed arms of record**, all four, on disk, with a
reader (`b7_5_diagnostic_pool`) that reproduces their aggregates to eight
decimal places. Duplicating them was never the point; bridging to them was.

---

## 3. CD-3 — the regeneration

Four January arms, full month, under the repaired stack
(`commission_broker_true_gated` + `swap_horizon_true`), safe cut set plus both
ledger projections. Wall 2.99–3.03 h each, all four concurrent. Receipt:
`phase14/receipts/CD_DELTA_TABLE_V1.json`.

### 3.1 The frozen column is the sealed artifact, and it reproduces exactly

The comparand is not a re-run: `cd_pool.py --sealed-arm` streams each sealed arm
of record through AW's own reader, which resolves the cold zstd shards in place
and verifies each shard's hash as it inflates it. On all four arms it reproduces
the published aggregate **exactly** — scoreable-row delta **0**, net-R relative
gap **0.00e+00**. A third, independent reproduction comes free in §5: the
gradient's TRAIN-split baseline lands on AW's own published
`mean_r_raw = −0.917554` and `mean_r = −0.200465` to six decimals.

So "frozen January" here is the artifact the estate's negative verdict rests on,
not a lookalike.

### 3.2 The delta table

| arm | frozen R/row | repaired R/row | **Δ** | gross frozen | gross repaired | Δ gross | trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| **S0R0** | −0.858511 | −0.882234 | **−0.023723** | −0.219928 | −0.219755 | +0.000173 | 63 |
| **S1R0** | −0.858142 | −0.882060 | **−0.023918** | −0.219779 | −0.219744 | +0.000035 | 55 |
| **S0R1** | −0.858310 | −0.882112 | **−0.023802** | −0.219805 | −0.219677 | +0.000128 | 61 |
| **S1R1** | −0.857873 | −0.881931 | **−0.024058** | −0.219608 | −0.219638 | −0.000030 | 54 |

**Every one of the 21 trading days is negative, on every arm, frozen and
repaired.** 21 of 21, four times, both sides.

**CD-P3 predicted −0.024 and the four arms measure −0.0237 to −0.0241.** The
prediction was arithmetic over AW's decomposition, declared before any month arm
launched; it survives at month scale on all four arms to three decimal places.

### 3.3 The cost decomposition, against what AW measured on the sealed pool

Arm S0R0, R per scoreable row:

| term | AW, sealed (frozen) | CD, repaired | Δ |
|---|---:|---:|---:|
| **gross before any cost** | −0.219900 | **−0.219755** | **+0.000145** |
| spread | 0.563800 | 0.563361 | −0.000439 |
| slippage | 0.020000 | 0.020000 | 0.000000 |
| **swap** | 0.054800 | **0.013656** | **−0.041144** |
| **commission** | **0.000000** | **0.065462** | **+0.065462** |
| pool mean R/row | −0.858500 | −0.882234 | −0.023734 |
| binary hit rate | 0.168850 | 0.168297 | −0.000553 |

Three things in that table are worth reading twice.

**The commission the engine charged is 0.065462. AW's post-hoc estimate on the
same pool was 0.0654.** Two independent computations — his a pandas pass over a
finished ledger, mine the engine pricing each candidate as it decided — agree to
four decimal places. F38 is now not merely confirmed but *quantified in the
engine*.

**The swap term falls 4.01×**, exactly the ratio the 32 → 8 bar horizon change
implies, which is what makes it a modelling repair rather than a tuning.

**Gross moves by +0.000145.** The repairs do not touch the directional edge, and
they cannot: they are cost terms. The pool loses **0.22 R per row before a single
unit of cost is charged**, and the entire repair budget is 0.024 R.

### 3.4 The loss concentration, and the counterfactual CD-3 asks about

Arm S0R0 repaired:

| band | rows | share of rows | share of pool loss | pool mean R **without** the band |
|---|---:|---:|---:|---:|
| cost > 1 R | 5,056 | 17.71 % | **54.00 %** | −0.493192 |
| cost > 2 R | 2,113 | 7.40 % | 33.44 % | −0.634132 |
| cost > 5 R | 345 | 1.21 % | 9.71 % | −0.806291 |

AW's sealed figures were 16.5 % of rows carrying 49.6 % of the loss; under
repairs the tail grows to 17.71 % / 54.00 %, which is what charging commission
must do — it pushes rows over the 1 R line.

**So: does killing the cost tail move the pool the way the estate's
out-of-window numbers say?** It moves it enormously and it does not rescue it.
Deleting 17.71 % of the rows takes the pool from **−0.882 to −0.493 R/row** — and
−0.493 is still four times the break-even distance away. AW's out-of-window
result (the sealed `spread_r ≤ 0.10` limit taking `asia_pdl_fade` from −0.902 to
+0.095 R/day) does not transfer, and the reason is visible in §3.3: out of window
the tail was the whole problem, here it is half of a problem whose other half is
that the mechanism has no directional edge.

### 3.5 What the factorial says

The two switches move the **trade set** — 63 / 55 / 61 / 54 trades, a 17 % spread
— and move the **pool** by 0.0004 R/row frozen and 0.0003 repaired. The S and R
axes the campaign was built to test change *which* candidates execute and change
essentially nothing about what the pool is worth. That is consistent with AW's
observation that the four sealed arms differ by ~16 rows in 28,500, measured here
at the level of economics rather than row counts.

The gate churn is larger than the net change makes it look: charging commission
at the 0.15 ceiling changed the refusal set on **18,728 of 154,390 candidates
(12.1 %)** — the fixture's 13.2 %, reproduced at month scale.

### 3.6 The family verdict, in the agreement's language

**On the VAL surface (January 2026, the survivor book's own selection surface —
ranking and gradient checks only), the broad V4 family under the repaired stack
is negative on every arm, on every one of 21 trading days, and the repairs make
it measurably worse rather than better.** The honest label is no longer
`UNTESTED_UNDER_REPAIRS`: the two repairs that reach this path have been
measured, and they are worth −0.024 R/row against a −0.220 R/row deficit that
exists before any cost is charged.

It is still not "dead", and the distinction is not politeness. Three of the
commissioned repairs never reached the replay path (§2.4) and two of those —
the clock and a generation-time spread floor — are not testable here at all
without re-materialising the sealed source. What the evidence supports is:
**negative under the repairs that reach it; the remainder untestable on a sealed
window; and the deficit is in the mechanism, not the cost model.**

Nothing here bills the candidate family. No candidate is filed for the sealed
gate, because nothing in this pool is close: `breakeven_precision` is 0.6488
against a base rate of 0.2791, and the pure 2R-target/1R-stop population hits
**16.83 % against a 33.3 % break-even**.

---

## 4. CD-4 — the month-scale measurement

### 4.1 The wall clock, measured for the first time at month scale

| | |
|---|---:|
| four repaired arms, concurrent | **2.99 – 3.03 h** |
| four-arm January window, frozen (estate's published figure) | ~16.5 h |
| **ratio** | **~5.45×** |
| per working day, pooled over the four arms | **437.4 s** |
| CB's solo train marginal working day (6 cuts, 2-day fixture) | 366.5 s |
| CB's frozen marginal working day (2-day fixture) | 628.1 s |

Read the 5.45× with its caveat: the numerator is measured here and the
denominator is the estate's published figure, not one I re-measured. The clean
measured statement is the per-day one — **628.1 → 437.4 s, 1.44×** — and that is
*with* four-way contention and the weaker safe cut set, because H-CB-2 bound this
session to the four memos it measured clean.

**The window speedup is not the engine.** Per-arm compute buys 1.4–1.7×. The rest
is that four arms now fit at once, which came from CB's GC cut (memory) and this
session's two ledger projections (disk).

### 4.2 CB's RSS assumption — and the correction to my own §0

CB's extrapolation rested on one assumption: *per-arm peak RSS does not grow
materially with window length*. **Measured at month scale, it grows ~1.5–1.8×,
and my own earlier reading of it in this session was wrong.**

| | peak RSS |
|---|---:|
| 2-day fixture, safe set (`CD_VA`) | **2.46 GB** |
| month arms, 4-up | **3.66 / 3.66 / 4.27 / 4.49 GB** |

Earlier in this session I published "the assumption HOLDS" on the strength of a
**60-second `ps` sampling trace** of the solo arm that showed 0.852–1.948 GB. That
instrument cannot see the answer: CLAUDE.md H3 already records that RSS spikes to
its peak *at the instant of the day-end heap collapse*, and a 60-second sampler
walks straight past a spike that lasts seconds. `ru_maxrss` is the authoritative
number and it says 4.49 GB.

**What survives of the earlier finding** is the shape, not the magnitude: RSS does
collapse at every day boundary and does not ratchet monotonically. **What does
not survive** is "peak RSS is a property of ONE DAY's accumulation, not of the
window". It is a property of the worst day in the window, and a longer window
contains a worse worst day.

Practical consequence: four concurrent month arms peak at ~16 GB of nominal
headroom on a 17 GB machine, and they ran only because the peaks are staggered
rather than simultaneous. Anyone planning six or eight concurrent arms on this
box should size on 4.5 GB, not 2.3.

### 4.3 Disk, which is what actually bound this session

Measured per arm, at month scale, with both projections on: **~2.3 GB route +
~0.42 GB semantic-diagnostic sidecar**. Unprojected it is ~16 GB. With 14 GB free
that is the difference between four concurrent arms and **zero**.

Where the bytes are, one arm, 16 working days in:

| | MB | |
|---|---:|---|
| `MISSED_OPPORTUNITY_LEDGER` | 1,025 | the pool — the substrate, already projected 5.6× |
| `compact-event-shards` | 346 | CB's H-CB-1 node |
| `DECISION_LEDGER` | 273 | already projected 10× |
| `SEMANTIC_ORDER_PREIMAGE` (sidecar) | 308 | **unprojected, nothing in the lane reads it** |
| `SCORECARD_LEDGER` | 129 | already projected 21× |
| `SEMANTIC_CANDIDATE` + `STATE_CHECKPOINT` (sidecar) | 112 | same |
| everything else | ~110 | |

The `.semantic-diagnostic` sidecar is **18 % of an arm and entirely unprojected**;
it is filed as the next cheapest cut.

---

## 5. CD-5 — the first gradient pass

Two axes, and the commission's own fallback taken deliberately rather than by
default: with the pool negative on 21 of 21 days there is no near-miss to
iterate, so the map of **where the loss is** is the honest deliverable, and the
varied axis rides on top of it.

### 5.1 AW's separability question, re-asked of the repaired pool

`cd_gradient.py`, everything declared before a cell was scored: AW's chronological
13/8 split restated, categorical level-wise cuts at ≥200 train rows, numeric cuts
at TRAIN tertiles, and **both** outcomes — net and gross.

| | declared cells | F1 train-positive (net) | F1 train-positive (**gross**) | F2 holdout-positive |
|---|---:|---:|---:|---:|
| sealed frozen S0R0 | 71 | **0** | **2** | 0 |
| repaired S0R0 | 76 | **0** | **1** | 0 |
| sealed frozen S1R1 | 70 | **0** | 2 | 0 |
| repaired S1R1 | 75 | **0** | 1 | 0 |

**The repaired stack does not open the map. It closes it slightly.** The two
gross-positive cells on the sealed pool are `symbol==GER40` (train +0.0270,
holdout −0.0380) and `final_blocker_class==execution_fillability` (train +0.0113,
holdout −0.0192); under repairs the second goes negative and only GER40 survives
F1, still failing the holdout. Zero cells are net-positive on either side, which
is AW's answer at his own resolution — and this run's TRAIN baseline reproduces
his published `mean_r_raw = −0.917554` / `mean_r = −0.200465` to six decimals,
which is what licenses reading the two results as the same measurement.

### 5.2 The varied axis — the total-cost ceiling on a `--days` sub-window

One axis, four cells, arm S0R0, `--days 2` (one working day), repaired stack,
each cell declared in code as a named patch so it appears in its own receipt and
in the iteration-ledger spec. `selected_cell_pretrade_max_total_cost_r` is 0.15
sealed; once commission is counted, whether 0.15 is still the right ceiling
becomes a question the sealed campaign could not ask.

| ceiling | trades | orders | scoreable | pool mean R/row | gross | mean cost | PASSED→REFUSED |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | **0** | **0** | 1,545 | −1.144228 | −0.227095 | 0.917133 | 1,851 |
| **0.15** (sealed) | 5 | 10 | 1,537 | −1.152236 | −0.230830 | 0.921406 | 1,164 |
| 0.25 | 5 | 10 | 1,537 | −1.149694 | −0.228287 | 0.921406 | 681 |
| 0.50 | 5 | 10 | 1,537 | −1.150174 | −0.228768 | 0.921406 | 467 |

**The axis is flat, and that is the answer.** Across a **10× range** the pool
mean moves **0.008 R/row**, and not monotonically. Above the sealed 0.15 nothing
about execution changes at all — 0.25 and 0.50 produce identical trades, orders,
scoreable rows and mean cost, differing only in how many candidates the gate
refuses on the way (681 vs 467), which reshuffles pool membership without
reshaping it. Below it, 0.05 is the only cell that moves the trade set, and it
moves it to **zero**: the best cell for the pool is the one that stops the book
trading.

So the ceiling is a **trade-count dial with no pool authority**, which is the
same shape §3.5 found in the S and R switches: the levers this campaign exposes
change *which* candidates execute and do not change what the pool is worth. Three
independent dials, one answer.

The 0.15 cell reproduces `VF` — the earlier 2-day full-repair run — **bit for
bit** (5 trades, 10 orders, 1,537 scoreable, −1.152236), on a different launch
path hours apart, which is a free determinism check on the whole repair stack.

### 5.3 What the loop leaves behind

Ten looks in `TRAINING_LANE_ITERATION_LEDGER.jsonl`, every one `VAL`, every one
`billed: false`, ten distinct spec digests — the first rows that ledger has ever
carried. Seven rows in `REPAIR_QUEUE_CD.json`, the primary one a **generator**
repair with its blocker named (`broader_origin_generators.py` has no `spread`
token and never sees a tick, so a stop-to-cost floor needs plumbing, not a
rebind). Nothing was graduated, nothing was billed, and the family declaration is
untouched at 53 members.

## 6. What I got wrong

**6.1 — I named a repair variant after a property it does not have.**
`commission_broker_true` is documented as "selection held fixed, the accounting
repaired", and it does not hold selection fixed at all: on the fixture it took
the trade count from **5 to 3**. `cost_r` is not only a reporting column — it is
written onto the candidate at `v4_timewarp:67414-67416` and feeds
`expected_net_r = ev_r − cost_r`, which the selector and the allocator both
read. What the variant actually isolates is *the refusal check not re-run*,
which is a narrower and less interesting claim than the one I wrote on it. The
swap repair moves the same lever the other way (5 → **6** trades): a cheaper
candidate ranks higher. Both are now stated in the receipt.

**6.2 — CD-P5 was falsified in direction, and the reasoning behind it was too
simple.** I predicted that re-gating with commission would make the diagnostic
pool LARGER (the pool is the rejected set, so a tighter gate should feed it).
It got smaller: 1,539 → 1,537. The gate genuinely churned — it changed the
refusal set on **1,164 of 8,812 candidates, 13.2 %** — but a candidate refused
earlier can also stop being *scoreable*, and the two effects nearly cancel. I
had reasoned about one of the two and written the prediction as if I had
reasoned about both.

**6.3 — I extrapolated the month-arm disk cost from the wrong quantity and was
2× out.** I multiplied the whole 927 MB two-day route by 21 trading days and
predicted ~19 GB. The route contains a fixed component, and the honest
extrapolation is the per-working-day growth of the ledgers, which measured
428 MB → ~9 GB. The prediction receipt records both. The conclusion — four
concurrent unprojected month arms do not fit — survived being wrong by 2×,
which is luck, not method.

**6.4 — my first attempt at the verification runs was a zsh word-splitting bug,
and the engine caught it, not me.** I wrote `for spec in "A safe none" ...; do
set -- $spec` — zsh does not word-split an unquoted variable, so all three runs
received `--prefix "CD_VA safe none_B7_5_S1R1"` and died on
`post_acceleration_prefix_invalid`. That is the same class as
`IMPLEMENTATION_STATE.md` B2075 (the fake A/B that "reported the answer its
author wanted") and the same trap CB recorded nearly falling into. It cost about
a minute because the runner **fails closed on its prefix**; had the mangled
prefix been accepted, three runs would have produced results under names I would
then have compared. The A/B driver for this session is written in Python for
exactly this reason.

**6.5 — an adversarial pass on my own repair found a provenance inconsistency I
shipped, and it is inert only by luck.** `swap_horizon_true` rewrites
`trade_params["gtos_vnext_dynamic_time_stop_bars"]` before the cost packet is
built, so the swap is priced at 8 bars — but the ENCLOSING function then stamps
`replay_swap_cost_time_stop_bars: swap_time_stop_bars` onto the same packet from
its own local, which is still **32**. A repaired arm therefore carries a packet
that reports the sealed horizon beside a swap computed at the repaired one. It
moves no economics, and the reason it moves nothing is that **the field is
written at `v4_timewarp:58968` and read nowhere in `src/`** — which is luck, not
design. Filed rather than patched mid-run, because changing it would invalidate
four running month arms for a field nothing reads.

The same pass checked the thing that would NOT have been cosmetic: the estate
has two independent cost readers, and only one of them is the pool path. The
trade side reads `executable_broker_calibrated_cost_r_from_packets`
(`v4_timewarp:70146`), whose first source is `packet["total_cost_r"]` — the
value the commission repair bumps. So the trade economics and the pool
economics see the same repaired cost, and a repaired arm cannot show a charged
pool beside uncharged trades.

**6.6 — I blamed my own A/B for a hang it did not cause, twice, before measuring
it.** Three `--days 12` sweep cells launched and stalled at 0 % CPU with ~9 s of
CPU consumed. My first explanation was that the A/B's `git checkout` of BASE
files had poisoned their prewarm `ProcessPoolExecutor` children — I had assessed
that risk earlier, concluded it was past because the MONTH arms were long out of
prewarm, and then applied that conclusion to runs launched eight minutes before
the A/B. That reasoning was wrong in a way worth naming: **I checked the risk
against the wrong processes.** My second explanation was that three simultaneous
cold launches collide in that pool. Also wrong.

What the measurement said: a single cell at `--days 2` with the same ceiling
patch runs clean (rc 0, 486.3 s, all nine patches applied); a single cell at
`--days 12` stalls with no spawn children, no cache files open, and the main
thread in `lock_PyThread_acquire_lock`. **The discriminator is `--days 12`, not
concurrency, not the A/B, and not the repair.** Filed as a lane defect — `--days`
is CB's CB-3.3 gate and it is proven only at the small end.

I also raised — and then disproved — a worry that the orchestrator's storage
cleanup had removed sealed replay inputs. It had not: the tick tree is intact at
12 GB with a readable manifest. Recorded because I nearly reported it as a
finding on a coincidence of timing.

**6.7 — I planned a month-scale frozen comparand twice and shipped neither, both
times for the same resource I had already measured.** The first attempt was the
solo CD-4 arm, killed at four days to re-plan concurrency (§6.7). The second ran
alongside the four repaired arms and was killed at **day 7 of 31**, when the
per-arm footprint measured out at 174 MB per working day and five arms projected
to leave **~1.3 GB** free at completion. Losing all five arms at 90 % is a far
worse outcome than losing one comparand, so the comparand went; the four
commissioned arms are the deliverable and they finish with ~5 GB of headroom.

What that costs is precise and it is not the delta table: **the sealed arms of
record ARE frozen January**, so CD-3's frozen column is measured against them
directly. What is lost is the BRIDGE — the month-scale demonstration that this
lane reproduces the seal — which was my own addition to the commission rather
than part of it. It is filed as H-CD-6 with the exact command, and it is the
single cheapest thing the next lane session can run.

The honest lesson is not "disk was tight". It is that I measured the per-day
footprint at 14:37, launched on it, and did not multiply it out to completion
until 15:11 — by which point two arms had already been killed for the same
arithmetic I could have done once.

**6.8 — I did not run the commissioned solo month arm to completion, and I will
not present four days as if I had.** CD-4 asks for one full arm solo, and I
killed it after four replayed days to re-plan concurrency on the disk
measurement — which the same commission item explicitly invites ("re-plan
concurrency before launching the other three, and say so"). What that buys is
the RSS answer, which is what the assumption needed and which four days settle
as well as thirty-one would (the trace collapses at every day boundary and never
ratchets). What it costs is a full-month solo **wall clock**, which this session
does not have and does not claim. §4 states the marginal working-day rate
instead.

## 7. Handoff

**H-CD-1 — the clock defect in the sealed source is the estate's, not just this
window's, and it is a re-materialisation.** The January bundle's `time` column is
broker wall clock relabelled UTC (§0.3), so the sealed window sits +2.0 h ahead
of true UTC and April sits +3.0. Nothing in the replay can repair it: the typed
cache's identity key is a file hash that a rebind cannot move, a cold rebuild is
refused against the bundle's sealed `normalized_root_sha256`, and the prepared
day packs already carry `kill_zone` / `session` / `utc_hour_bucket` computed
under the wrong label. **What this costs today**: every hour-of-day statement
about the January pool is shifted two hours, including AW's `B_TIME` axis (81
cells). What it does NOT cost: a uniform shift moves no R, so the economics
stand. Whoever wants an honest hour axis on B7.5 has to re-materialise, and that
breaks the seal — an owner decision, not a session's.

**H-CD-2 — `commission_usd_per_lot_for_packet` is still unbound, and it is the
LIVE half of this repair.** `src/costs/model.py:789` is a prepared, tested
adapter whose own docstring calls it "the OD-J1 prepared change" for
`broker_net_cost_engine`. Session CD bound the REPLAY path by rebind; the live
path still charges the same zero, and the live path is where money is. That is a
commissioned change to an R2-bound file, not a lane rebind, and it belongs in
front of Borhen with the re-seal cost priced.

**H-CD-3 — the arm summary contradicts the repair and nobody would notice.**
`replay_acceleration_attempt5_typed_sparse_runner.py:18001` and `:18853`
hardcode `cost_authority_sources.selected_cell_cost_gate_status =
"commission_included_in_selected_cell_risk"` into the SUMMARY the semantic
verifier reads. A repaired arm therefore ships a summary asserting the thing the
arm just stopped doing. It is cosmetic for the lane (nothing reads it to decide)
and it is exactly the shape of claim that gets quoted later.

**H-CD-4 — the pool projection's keep-list is the one place this lane can lose
something, and it is worth one review.** `missed_pool_projection` drops 593 of
670 top-level keys and derives its keep-list from
`b7_5_diagnostic_pool.FEATURE_FIELDS`, so anything AW's mine could ask of the
sealed pool can be asked of a projected one. What it cannot answer is a question
nobody has framed yet. The frozen reference arm was kept whole for exactly that
reason; a session that projects everything has traded optionality for disk
without saying so.

**H-CD-6 — the seal bridge is one command and it is the cheapest thing left.**
This session could not afford a month-scale frozen comparand alongside the four
repaired arms (§6.6), so the claim "the train lane reproduces the sealed arm of
record over a full month" is *unmeasured*. It is worth measuring, because it is a
stronger identity check than CB's H-CB-5 proposed: H-CB-5 compares a fresh train
run to a fresh frozen run, while this compares a train run to the ARTIFACT THE
ESTATE'S NEGATIVE VERDICT RESTS ON. `cd_delta_table.py` already carries AW's
sealed aggregates (`SEALED_ARM_POOLS`) and its `bridge()` computes the gap, so
the only missing input is the run:

```bash
python3 -m src.research_infra.train_engine.runner --arm S0R0 \
  --prefix CD_BRIDGE_B7_5_S0R0 --purpose LANE_ITERATION \
  --patches safe+projection+pool --repairs none --session CD \
  --keep-outputs --out /tmp/cdbench/CD_BRIDGE.json
# then: cd_pool.py over its MISSED ledger, and cd_delta_table.py reads the rest.
```

Solo it is ~2.1 h and ~2.9 GB. Its expected answer is stated so a reader can
judge the result rather than accept it: the sealed arms ran under contract R1 and
this lane binds R2, which moved two never-executing verifiers into
`verification_tooling`, so the economics should match and the provenance should
not.

**H-CD-7 — `--days N` is proven at the small end only, and hangs at 12.**
CB's CB-3.3 gate ("one day costs one day") was measured at `--days 1` and
`--days 2`. Session CD ran `--days 2` many times (clean) and `--days 12` four
times (stalls at 0 % CPU, ~9 s in, no spawn children, no cache files open, main
thread in `lock_PyThread_acquire_lock`). A full window with no `--days` at all
runs fine — four month arms did. So the defect lives in the bounded path
somewhere above 2 days, and the most likely suspect is
`sealed_inputs.build_january_args`'s narrowing of
`expected_prepared_day_pack_roots` (`{k: v for k, v in roots.items() if
str(k[1]) <= stop_after_day}`) interacting with the prewarm's worker pool. It is
the one thing standing between this lane and cheap mid-size gradients, and it is
a bounded debugging job: the reproduction is one command and takes 90 seconds to
show the symptom.

**H-CD-8 — the next question is a MECHANISM question and it needs no new replay.**
The pool loses 0.22 R/row before any cost is charged and the pure 2R/1R
population hits 16.83 % against a 33.3 % break-even, so the family is wrong about
direction by roughly a factor of two. Nobody has asked *why* — whether it is the
entry rule, the 2R target, the 1R stop, or the first-touch exit model. The
cheapest first cut holds the entry set fixed and varies the target/stop geometry
over the regenerated pool's own rows, which are committed here as
`phase14/receipts/pools/CD_REPAIRED_POOL_*_V1.jsonl.gz` (4 × 5.9 MB, 28.5k rows
each, 78 columns). That costs no replay at all. It is queue row 2 and it is the
one I would take next.

**H-CD-5 — what this session did NOT do, deliberately.** No sealed arm was
re-run under the sealed contract; every run is a lane run under R2, stamped
`LANE_ITERATION_EVIDENCE`. No bound byte moved (H1 checked at start, at each
commit and at the end: 43 bound paths, 2 non-matching, both the known unhydrated
LFS pointers). March is outcome-unread and refused by the guard on both axes on
every path. No VPS contact, no broker-capable script, no config edit, and
nothing here bills the candidate family.
