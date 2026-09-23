# p2 — SEALED TEST PRE-DECLARATION

**Written 2026-08-06, BEFORE any economic read of `june_2025`, `august_2025`, `september_2025`.**
Nothing below was written after seeing a sealed outcome. This section is the declaration of record;
the result file (`p2_RESULT.md`) reports against it verbatim and adds no hypothesis.

Lane: `p2` (the sealed-test lane, wave 19). Authority: the wave brief designates this lane the only
one permitted to open the three held-out windows, once.

---

## 0. What has been read so far (and what has not)

Read before declaring: the wave brief; `READ_RESTRICTED_INDEX.md`; the three `.READ_RESTRICTED`
markers (window ids, capture windows, row counts, sha256 — no economics); the pbg harness
(`pbg_run.py`, `pbg_lib.py`, `pbg_econ.py`, `pbg_analyze.py`); the M15/M1 archive **file listings and
timestamps only**.

**Not read: any row of any sealed pool, any sealed arm receipt, any outcome, any R value.**

---

## 1. Object under test

Not the sealed diagnostic pools. Those are the counterfactual missed-opportunity ledger (18.03% of
generator output, admitted by an outcome-decodability gate at `v4_timewarp:28130-28140`), which this
wave established is the wrong object. The test is run on the **reproduced sealed roster** — the
generator's own candidate emissions — built for the three windows by the same harness Session PB
validated at 99.82% geometry-hash match on January and February.

* Generator: `src.components.broader_origin_generators.generate_live_broader_origin_candidates`,
  unmodified, driven by `pbg_run.py` (close-only mode `k=15`, plus partial-bar minutes `k=1..14`).
* Inputs: `LANE_INPUTS_TRUE_UTC_V1` bars (M15 bridge + `deep_universe_h4d1_2014_2026` H4/D1 + the
  `bridge_ftmo_m1_{202506,202508,202509}` M1 tape). All three M1 packs verified present.
* `risk.min_rr = 1.5` (the true config value; the estate's published breakevens used 2.0 and are
  wrong — the wave's own correction).
* Grid: 96 windows/day, 00:00..23:45 UTC. 24 symbols.
* Windows, from the sealed arms' own capture windows in the restriction markers:
  `june_2025` 2025-06-03..06-30, `august_2025` 2025-08-01..08-30, `september_2025` 2025-09-01..09-30,
  weekdays only.

### 1.1 Declared data-availability rule (fixed before any outcome is computed)

The M15 bridge archive begins **2025-06-01T22:00Z**. A decision instant needs 672 closed M15 bars for
the generator's window; that is first satisfied on **2025-06-12**. Therefore:

* **Primary pooled figures use June days from 2025-06-12 only** (13 of 20 June weekdays).
  August and September are unaffected (4,030 and 5,962 bars of lookback at their first day).
* All-June figures are reported as supplementary, labelled, and never substituted for the primary.

This rule is a property of the source archive, not of any outcome, and is fixed here.

---

## 2. Declared contracts

* `d = |entry − stop|`; rows with `d ≤ 0` are dropped.
* **born-past-stop**: at the decision instant the last M1 close strictly before `T` is already at or
  beyond the stop (LONG `mkt ≤ stop`, SHORT `mkt ≥ stop`).
* **CLEAN roster** = all emissions minus the `current_breaker_re_entry` family minus born-past-stop
  rows (f1's definition, unchanged).
* **CORRECTED contract (primary)**: the seven at-market families
  (`displacement_continuation`, `liquidity_sweep_reclaim`, `structural_distance_extreme`,
  `volatility_compression_expansion`, `session_open_range_break`, `regime_transition_break`,
  `cross_asset_lead_lag`) walked as **market orders** filled at the emitted entry price
  (`pbg_econ.walk`, `include_fill_minute=False`); the three POI families walked as **honest resting
  limits** (`pbg_econ.walk_limit`). This is d1b's correction and it is the contract the generator
  actually describes.
* **f1 contract (secondary)**: all ten families walked as honest resting limits.
* Target `2.0R`, horizon `120` M1 bars, stop-wins tie rule, forward path from stamp `D+1`.
* Cost: `pbg_econ.CostModel` — the h1 four-term broker-true basis (hour-aware tick spread +
  broker-true commission + measured price-unit slippage + swap on broker-midnight crossings),
  charged once in price units and divided by `d`.
* "Per fill" means over rows that filled inside the horizon. `no_fill` rows book 0.0 and are excluded
  from per-fill means, included in per-emission means.
* Uncertainty: **day-block bootstrap, 4,000 draws**, resampling trading days with replacement across
  the pooled three windows. 95% CI.

---

## 3. THE HYPOTHESES — declared with thresholds, before the read

### H1 — PRIMARY. The signal is zero.

The wave's verdict is that the broad V4 family's gross expectancy is statistically zero and that the
entire economic loss is the broker toll (f1: clean gross −0.01327 against a 0.28118 toll; d5 at the
broker-correct fill contract: +0.00106; f2's paired signal +0.02877 against a 0.32954 toll).

**Metric**: pooled CLEAN-roster **gross R per fill**, corrected contract, 2.0R, three windows pooled.
**Secondary reported alongside, not substituted**: net R per fill, win rate vs payoff-implied
breakeven, per-window figures, and the same four numbers under the f1 contract.

| outcome | condition | meaning |
|---|---|---|
| **CONFIRMED** | `|gross| ≤ 0.05` **and** `net ≤ −0.10` | the wave's verdict holds out of sample |
| **REFUTED (signal real)** | `gross ≥ +0.05` **and** bootstrap CI low > 0 **and** ≥2/3 windows positive | the family carries material directional edge; the verdict is wrong |
| **REFUTED (signal negative)** | `gross ≤ −0.05` **and** bootstrap CI high < 0 | the family is actively wrong-way, not zero |
| **ECONOMIC REFUTATION** | `net ≥ 0` under any declared contract | the family pays for itself; everything published is wrong |

`0.05` is chosen as 5× f2's measured detection floor (~0.010 R/trade pooled) and ~6× below the
measured toll — large enough to separate "zero" from "materially non-zero", small enough that it is
far short of viability either way.

### H2 — The one family that looked real.

`structural_distance_extreme` is the estate's only reliably gross-positive broad family: +0.06639
R/fill at 2.0R, positive in 8 of 8 in-sample windows, +0.06170 on the two most recent (d1b §5).
Nothing has ever tested it out of sample.

**Metric**: its pooled gross R per fill, corrected contract, 2.0R, clean rows.
**REPLICATES** if pooled gross `≥ +0.03` **and** positive in ≥2 of 3 windows.
**IN-SAMPLE ARTIFACT** otherwise. Its net and its gross/toll ratio are reported either way (in sample
it reaches only 0.107 of its own toll, so replication does not make it viable — it makes it real).

### H3 — The largest USAGE lever with a clean in-sample record.

d2: swapping the shipped `target_2.0R` exit for `stop_only_horizon` is worth **+0.03500 R/trade**,
positive in 8 of 8 months, and the shipped exit is the only layer with negative capture against its
own menu.

**Metric**: pooled Δnet = `net(stop_only_horizon) − net(target_2.0R)` on the same clean rows, where
`stop_only_horizon` walks the same entry/stop with no target and books the close of the 120th bar.
**REPLICATES** if pooled Δnet `≥ +0.02` **and** positive in ≥2 of 3 windows.

### H4 — The fill-contract repair.

d5: reclassifying rows whose entry price the market had already left at the decision instant — the
estate's walker fills them at a price that never traded again — moves the whole family's gross from
−0.07963 to +0.00106 and its net by **+0.02995**, 8/8 windows.

**Metric**: pooled Δnet = `net(side-aware contract) − net(estate contract)` per opportunity, where a
row with `mkt_r0 < 0` (market already through the entry, signed by side) is filled only on a genuine
re-cross of the entry from the correct side rather than on the estate's range-containment test.
**REPLICATES** if pooled Δnet `≥ +0.015` **and** positive in ≥2 of 3 windows.

### H5 — THE SURVIVING CANDIDATE. Forming-bar decision on five at-market families.

The wave's one surviving result: deciding at the first minute inside the forming M15 bar rather than
at its close is worth **+0.1956 / +0.1930 / +0.2366 R/trade** on the `EARLY5` cohort
(`displacement_continuation`, `liquidity_sweep_reclaim`, `session_open_range_break`,
`regime_transition_break`, `volatility_compression_expansion`), positive on 63 of 63 trading days in
Jan/Feb/Mar 2026. Session d6 then argued it is unimplementable, because the +0.19 is a **paired**
delta that exists only on setups which also re-emit at the close, and the phantom leg (setups that
fire early and never confirm) has already lost 98% of its loss by the time the close arrives.

Two declared sub-tests, both on the sealed three, `EARLY5` cohort, partial arm = the setup's
**earliest** emitting minute `k ∈ 1..14`, close arm = `k = 15`, same setup key
`(symbol, family, side, bar)`:

* **H5a — does the paired effect exist out of sample?**
  Metric: pooled paired Δnet (partial − close) over setups present in both arms.
  **REPLICATES** if `≥ +0.10` pooled **and** positive in all 3 windows.
* **H5b — is the candidate tradeable? (this is the verdict)**
  Metric: the **implementable** book — every setup the partial arm emits, phantom leg charged, no
  pairing, deduplicated to one placement per `(family, symbol, decision_day)` per the live
  `PlacementLedger` rule — against the same book built from the close arm.
  **THE CANDIDATE PASSES** if the partial book's pooled net `> 0` **and** it beats the close-only
  book in ≥2 of 3 windows.
  **THE CANDIDATE FAILS** otherwise.

### H6 — Signal vs usage, adjudicated directly: is the direction call better than its own mirror?

Two foundation lanes disagree in **sign** on the only question the owner asked. f2 measures the
family's paired directional signal at **+0.02877** R/trade against PLACEBO-SIDE; d7 measures **−0.04230**
(CI95 [−0.06583, −0.02066]) on the subset where the emitted entry price actually existed. The sealed
windows can settle it.

**Metric**: on **at-market rows filled inside the decision bar** (the cohort where the market and
honest-limit contracts are identical by construction, so no fill selection exists), pooled
`gross(real) − gross(mirror)`, where the mirror is the same row with the side flipped and the stop
reflected about the entry (`stop' = 2·entry − stop`), same target multiple, same toll, same instant.

| outcome | condition |
|---|---|
| **DIRECTION POSITIVE** | `≥ +0.02` and bootstrap CI excludes 0 |
| **DIRECTION NEGATIVE** | `≤ −0.02` and bootstrap CI excludes 0 |
| **DIRECTION ZERO** | otherwise |

---

## 4. Rules of the spend

1. One generation pass, one walk, one analysis. No re-runs against a different threshold.
2. No hypothesis added after the first sealed number is printed. Anything noticed in passing is
   recorded in `open_questions`, never promoted to a result.
3. Every hypothesis is reported per window and pooled, pass or fail, including the ones that fail.
4. On completion the three windows are recorded SPENT, on this declaration, in
   `READ_RESTRICTED_INDEX.md`, and the `.READ_RESTRICTED` markers are annotated (not deleted — the
   record of what they were spent on is the point).
5. If the generation does not complete for a window, that window is reported as NOT RUN rather than
   substituted, and it stays unspent.

---

## 5. What would make me wrong in the direction that matters

The expensive error for this programme is not "we kept a dead family alive"; it is "we killed a live
one". So, stated in advance: **H1 REFUTED (signal real), or H2 REPLICATES with a materially larger
effect than in sample, or H5b PASSES** would each be sufficient to reopen the broad family, and I
will report any of them as such without qualification.

---

## 6. ADDENDUM — written before the sealed read, after harness validation

The harness was validated on **January 2026** (open window, `/tmp/pbg_full_jan`) before any sealed
window was touched. It reproduces Session PB's published figures exactly:

| quantity | published | this harness |
|---|---|---|
| `EARLY5` setup keys, January | 17,237 | **17,237** |
| `EARLY5` paired Δnet, January | +0.19562372 | **+0.19562** |
| `EARLY5` phantom leg, January | −0.93653 (n 5,040) | **−0.93559 (n 5,047)** |
| regenerated January roster rows | 153,598 (d5) | **153,598** |

**One amendment, forced by that validation and made before any sealed number exists.** H4's declared
baseline — "the estate's range-containment test" — is `pbg_econ.walk_limit`, which fills a resting
limit only on a bar whose RANGE contains the entry. Session d5 measured its +0.02995 against a
different walker, one that fills a BUY on `low ≤ e` whatever side of `e` the market is on. Against
the range-containment baseline the repair is worth ≈0 on January (+0.00016), because that walker does
not carry the defect d5 repaired. Testing d5's claim against a baseline that does not have the defect
would be a strawman.

**H4 is therefore reported in two variants, both declared here, before the read:**

* **H4-a** — vs the `pbg_econ.walk_limit` range-containment baseline (as literally declared in §3).
* **H4-b** — vs the d5-style one-sided baseline (`low ≤ e` for a BUY, `high ≥ e` for a SELL), the
  convention in which +0.02995 was measured. Threshold unchanged: `Δnet ≥ +0.015` and ≥2/3 windows.

Nothing else in §3 is altered. No threshold moved.

**Comparators.** Rather than compare sealed figures to other lanes' numbers computed with slightly
different row filters, the same harness is run on the OPEN windows it can reach
(Oct/Nov/Dec 2025, Jan 2026, Apr/May 2026 — all already generated by sessions LP/d6/PB) so that every
sealed number has an in-sample counterpart produced by identical code. This adds no hypothesis and
changes no threshold.

### 6.1 Compute allocation, recorded before any sealed result exists

The partial-bar grid (`k = 1..14`, needed only by H5, because the partial arm is defined as the
setup's EARLIEST emitting minute) costs 4× the close-only grid per day — 422 s/day against 110 s/day
measured on this machine under contention. To get all three sealed windows into H1–H4 and H6 rather
than one window into everything:

* **september_2025** is generated with the **full** grid (`k = 1..14` plus close) — H5 is tested there.
* **august_2025** and **june_2025** are generated **close-only** (`k = 15`) — they serve H1, H2, H3,
  H4 and H6, which need nothing else.
* H5 is therefore reported on **one** sealed window and labelled as such. No threshold changes.

This is a compute decision taken before any sealed number existed, not a response to one.
