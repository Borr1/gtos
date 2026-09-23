# d4 — ARE THE CONDITIONS EVEN TRUE?  Audit of the setup definitions against price

Lane d4, wave 19 broad forensic.  Whole-population measurement, no sampling.

**Population.** Eight regenerated sealed rosters — the CORRECT object, Session PB's
harness (`phase19/receipts/pbg/pbg_run.py`), the unmodified production generator
`src.components.broader_origin_generators.generate_live_broader_origin_candidates`,
`min_rr = 1.5`, true-UTC lane inputs:

| window | roster rows (k=15) |
|---|---:|
| 2025-10 | 174,497 |
| 2025-11 | 151,233 |
| 2025-12 | 170,997 |
| 2026-01 | 153,598 |
| 2026-02 | 129,287 |
| 2026-03 | 130,051 |
| 2026-04 | 147,123 |
| 2026-05 | 154,291 |
| **total** | **1,211,077** |

**144,725** of those are at-market candidates (7 families); **1,066,352** are POI
limit candidates (3 families).  The sealed three (Jun/Aug/Sep 2025) were **not
touched**.

---

## 0. Headline

> **The seven at-market setup definitions are EXACTLY what the source says they
> are — 144,725 of 144,725 emissions verified on condition, entry, stop and
> target; zero violations; zero missed emissions; and no look-ahead.  The bug is
> not in the conditions.  It is in the three POI families' DISTANCE GATE, which is
> denominated in percent-of-price (1.0 %) while the contract it admits is
> denominated in risk units of a median 7.4–8.9 bps — a gate 11.2–13.5 R wide on a
> trade whose target is 1.5 R.  84–92 % of POI emissions are limits whose own
> target the market has already traded through, and 25.7 % of
> `current_breaker_re_entry` emissions are born beyond their own stop, fill 100 %
> of the time, book −1.304 R net each, and carry 91.8 % of that family's entire
> loss.**

---

## 1. Method — an independent re-implementation, not an import

`d4_lib.py` hand-transcribes each family's predicate and geometry from
`src/components/broader_origin_generators.py`, with the file:line each rule came
from.  It imports **nothing** from that module except the config kill-zone
*lookup* (a config read, not a predicate).  Bars come straight from the true-UTC
lane-input M15 CSVs.

Bar resolution follows `_selected_closed_bar_open` (`:2179-2199`): the decision at
instant T uses the LAST bar whose close is ≤ T — not always T−15 min.

`d4_verify.py` then does two things for every window:

* **forward** — for every emitted candidate, does the condition hold on the closed
  bars, and are entry / stop / target where the rule says (relative tolerance
  1e-9; 1e-8 for the target)?
* **reverse** — for every bar the generator actually decided on, does the audit
  predict a candidate the generator did not emit?

---

## 2. RESULT — the at-market conditions are true.  All of them.  Everywhere.

| family | emitted | condition satisfied | entry exact | stop exact | target exact | violation rate |
|---|---:|---:|---:|---:|---:|---:|
| `liquidity_sweep_reclaim` | 43,751 | 43,751 | 43,751 | 43,751 | 43,751 | **0.000000** |
| `displacement_continuation` | 39,517 | 39,517 | 39,517 | 39,517 | 39,517 | **0.000000** |
| `structural_distance_extreme` | 23,923 | 23,923 | 23,923 | 23,923 | 23,923 | **0.000000** |
| `cross_asset_lead_lag` | 21,678 | 21,678 | 21,678 | 21,678 | 21,678 | **0.000000** |
| `session_open_range_break` | 8,195 | 8,195 | 8,195 | 8,195 | 8,195 | **0.000000** |
| `volatility_compression_expansion` | 5,341 | 5,341 | 5,341 | 5,341 | 5,341 | **0.000000** |
| `regime_transition_break` | 2,320 | 2,320 | 2,320 | 2,320 | 2,320 | **0.000000** |
| **total** | **144,725** | **144,725** | **144,725** | **144,725** | **144,725** | **0.000000** |

Reverse check: **0** candidates predicted by the audit and not emitted, in every
family, in every window.  The emitted set is exactly the predicted set.

**This is a stronger statement than "no bug".**  A hand-written closed-bar-only
re-implementation reproducing 144,725 emissions bit-for-bit is a proof that none
of these seven families reads a bar that had not printed — see §6.

*Receipts:* `d4_out/VERIFY_2025{10,11,12}.json`, `d4_out/VERIFY_2026{01,02,03,04,05}.json`.

---

## 3. THE DEFECT — the POI distance gate is denominated in the wrong unit

### 3.1 The gate

`_generate_current_framework_candidates` admits a POI zone on exactly one distance
test (`:1201`, `:1391`, `:1446`):

```python
proximity = _zone_proximity_pct(current_price, zone[0], zone[1])   # :1711-1716
if proximity > proximity_tolerance:                                # :1599-1613
    continue
```

`_zone_proximity_pct` returns **gap / price** — a fraction of price.  The
tolerance is `pre_ai_gates.poi_proximity_tolerance_pct = 0.01`
(`config/agent_config.yaml:4032`) = **1.0 % of price**.

The candidate it then builds is denominated in R: `_current_framework_geometry`
(`:1616-1628`) puts the entry at the zone MIDPOINT and the stop one buffer-ATR
beyond the zone edge; the target is `entry ± 1.5 × risk` (`_candidate`,
`:1872-1873`).  The measured median risk distance is:

| family | median risk | **tolerance in RISK UNITS** |
|---|---:|---:|
| `current_breaker_re_entry` | 7.41 bps | **13.49 R** |
| `current_fvg_fill` | 7.42 bps | **13.47 R** |
| `current_ob_retest` | 8.91 bps | **11.22 R** |

**An 11–13.5 R-wide admission gate on a 1.5 R trade.**  The two quantities are not
commensurate, and nothing downstream reconciles them: `_valid_geometry`
(`:2606-2611`) checks only that stop < entry < target; and **no predicate anywhere
under `src/` compares the current price to the candidate's own stop or target**
(searched `past_stop|stop_breached|beyond_stop|stop_already` — zero hits).

### 3.2 One scalar characterises the whole contract

For a POI candidate at decision price `cp` (= `latest.close`, `:1085`):

```
fill_gap_R = (cp - entry) / risk  × (+1 LONG, −1 SHORT)
```

which partitions every emission exactly:

| bin | condition | meaning |
|---|---|---|
| `past_stop` | `fill_gap_R < −1` | market is already **beyond the stop** |
| `marketable` | `−1 ≤ fill_gap_R < 0` | limit fills now, at a worse price, inside the stop |
| `resting` | `0 ≤ fill_gap_R < 1.5` | **the intended contract** |
| `target_through` | `fill_gap_R ≥ 1.5` | **the target is already behind the market** |

(`fill_gap_R ≥ rr` ⟺ `cp` is past the target, algebraically.)

### 3.3 The partition — eight windows, 1,066,352 POI emissions

| family | n | past_stop | marketable | **resting (intended)** | target_through | median `fill_gap_R` |
|---|---:|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 700,947 | 0.00 % | 1.29 % | **14.43 %** | **84.28 %** | 4.967 |
| `current_ob_retest` | 270,354 | 0.13 % | 0.43 % | **7.88 %** | **91.55 %** | 4.980 |
| `current_breaker_re_entry` | 95,051 | **26.19 %** | 1.75 % | **9.75 %** | 62.32 % | 2.568 |

**Between 7.9 % and 14.4 % of POI emissions are the contract the family
describes.**  The rest are limits the market has left behind by a median 5.0
risk units — or, for the breaker family, limits the market has already blown
through in the wrong direction.

*Receipt:* `d4_out/POI_8MO.json`.

### 3.4 The partition PRICES the estate's headline

Walked on the M1 tape with the estate's own honest resting-limit walker
(`f1_walk.walk_limit2`, 120-minute horizon, target 1.5 R) and the h1 broker-true
four-term cost basis, eight windows pooled.

**Harness cross-check first.**  The measured family fill rates reproduce f1 §10 to
three decimals, independently:

| family | d4 fill rate | f1 fill rate |
|---|---:|---:|
| `current_ob_retest` | 0.0709 | 0.071 |
| `current_fvg_fill` | 0.2262 | 0.227 |
| `current_breaker_re_entry` | 0.3697 | 0.370 |

**`current_breaker_re_entry`** — n = 92,108, gross −0.26166, net **−0.36457 R/emission**

| bin | n | share | fill rate | share of family's FILLS | gross/fill | net/fill | contribution to net | % of family net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **past_stop** | 23,649 | 25.68 % | **1.0000** | **69.46 %** | **−0.9970** | **−1.3038** | **−0.33475** | **91.8 %** |
| marketable | 1,654 | 1.80 % | 1.0000 | 4.86 % | −0.4626 | −0.6926 | −0.01244 | 3.4 % |
| resting | 9,135 | 9.92 % | 0.5093 | 13.66 % | −0.0195 | −0.2257 | −0.01140 | 3.1 % |
| target_through | 57,670 | 62.61 % | 0.0710 | 12.02 % | +0.0812 | −0.1347 | −0.00599 | 1.6 % |

**`current_fvg_fill`** — n = 672,282, gross −0.00560, net **−0.06686 R/emission**

| bin | n | share | fill rate | gross/fill | net/fill | contribution | % of net |
|---|---:|---:|---:|---:|---:|---:|---:|
| marketable | 8,858 | 1.32 % | 0.9940 | −0.2704 | −0.3941 | −0.00516 | 7.7 % |
| resting | 97,807 | 14.55 % | 0.5746 | −0.0145 | −0.2651 | −0.02216 | 33.2 % |
| target_through | 565,617 | 84.13 % | 0.1539 | −0.0065 | −0.3053 | −0.03953 | 59.1 % |

**`current_ob_retest`** — n = 261,379, gross −0.00204, net **−0.01462 R/emission**

| bin | n | share | fill rate | gross/fill | net/fill | contribution | % of net |
|---|---:|---:|---:|---:|---:|---:|---:|
| past_stop | 353 | 0.14 % | 1.0000 | −0.9363 | −1.0876 | −0.00147 | 10.0 % |
| marketable | 1,176 | 0.45 % | 0.9991 | −0.3113 | −0.4994 | −0.00225 | 15.4 % |
| resting | 20,855 | 7.98 % | 0.4020 | +0.0203 | −0.1605 | −0.00515 | 35.2 % |
| target_through | 238,995 | 91.44 % | 0.0360 | −0.0007 | −0.1748 | −0.00576 | 39.4 % |

**This reproduces f1 §4.2 from the geometry side.**  f1: "`current_breaker_re_entry`
… 68.0 % of its fills are born past their stop and book ≈ −0.998 R … removing it
moves roster gross −0.0823 → −0.0180 (−78 %)."  Here the same family, decomposed:
the past-stop bin is **69.46 % of its fills** (f1: 68.0 %), fills **100 %** of the
time because it is marketable by construction, books gross **−0.9970** (f1:
≈ −0.998), and carries **91.8 %** of the family's loss.  Two independent routes,
the same number.

*Receipts:* `d4_out/POIECON_2*.json` (per window), `d4_out/POIECON_POOLED.json`.

### 3.5 What repairing it buys — and what it does not

Re-gating on risk units instead of percent-of-price (require
`fill_gap_R < target_rr`, i.e. "the target must still be in front of the market")
keeps 15.7 % of `current_fvg_fill`, 8.4 % of `current_ob_retest` and 11.5 % of
`current_breaker_re_entry`, and **eliminates the entire past-stop bin**.

The remaining, correctly-formed limit book (`resting` only, all three families,
69,233 fills, eight windows pooled):

* **gross −0.01065 R/fill**
* **toll  +0.23916 R/fill**
* **net   −0.24981 R/fill**

**The bug is worth 91.8 % of one family's loss — the family f1 measured as 74 % of
the estate's published negativity — and fixing it leaves a book with
statistically zero gross edge paying a 0.239 R toll.**  This is the same shape f1
reached on the clean roster (gross −0.01327 against a toll of +0.28118) by a
completely different route.

**Cheapest fix in the estate, and it is one predicate**: at
`broader_origin_generators.py:1201 / :1391 / :1446`, replace
`proximity > proximity_tolerance` with an R-denominated test computed from the
geometry the very next lines build.  It is a **default-off, one-key** change: the
zone, the entry, the stop and `current_price` are all already in scope.

---

## 4. THE ZONES — checked against price, in the candidate's own contract units

The MSO's own mitigation convention (`market_state.py:610`, `:635`) scans only from
the *break* index forward, so "has the tape touched the zone since formation" is
not a fair test of `mitigated=False`.  These tests are convention-free because
they are denominated in the candidate's own geometry.  Anchor = the zone's
`mitigation_time` where stamped (breakers, 3,748/3,748) else `formation_time`.
n = 49,296 captured POI candidates over 10 days across 4 months; zones read from
`candidate_source_detail` (`:387-388`, `_source_detail` `:1728-1750`).

| family | n | **stop already traded since anchor** | in last 24 h | target already traded | entry level already available | median zone age |
|---|---:|---:|---:|---:|---:|---:|
| `current_breaker_re_entry` | 3,748 | **56.56 %** | 53.82 % | 96.02 % | 73.80 % | 62.3 h |
| `current_ob_retest` | 13,280 | 17.41 % | 9.80 % | **98.54 %** | **100.00 %** | 26.8 h |
| `current_fvg_fill` | 32,268 | 0.00 % | 0.00 % | **99.26 %** | 18.65 % | 11.0 h |

Read the third column with the first: **every single `current_ob_retest`
candidate is waiting for a retest that has already happened** — the limit price
has been available at some point since the zone formed (49.5 % of them within the
last 24 hours) — and 98.5 % of them are waiting for a move the market has already
made.  More than half of `current_breaker_re_entry`'s emissions offer a stop the
market has traded through *since the breaker became a breaker*.

`current_fvg_fill` is the one that behaves structurally: 0 % stop-traded and
81.4 % of its gaps genuinely un-revisited.  Its defect is purely the distance gate.

*Receipts:* `d4_out/ZONEVERIFY_V1.json`, `d4_out/ZONEVERIFY_ANCHORED_V1.json`.

---

## 5. THE CLOCK

### 5.1 The tape is true UTC — confirmed, not assumed

First print of every trading week across all 24 symbols and the full lane-input
span: **Sunday 22:00 UTC (n=523)** and **Sunday 21:00 UTC (n=420)** — exactly the
FX open under EU winter and EU summer time.  The lane inputs are true UTC.  CJ's
re-clock holds.

### 5.2 TWO session functions disagree on 65.71 % of candidates

Every candidate carries **two** session labels computed by **two different
functions on two different window sets**:

| field | function | window source | boundary |
|---|---|---|---|
| `session`, `session_bucket` | `_session_at` (`broader_origin_generators.py:2433-2444`) | config `kill_zones` **+ 24 appended `moonshot_hXX_XX` hourly windows** (`:2558-2562`, enabled at `config/agent_config.yaml:623`) | `start ≤ m < end`, wrap-aware |
| `kill_zone`, `route_session` | `derive_session` (`v4_timewarp…:7488-7499`) | the module dict **only** — never reads config | `start ≤ m ≤ end`, no wrap |

Measured: **795,829 of 1,211,077 rows (65.71 %) carry two different session
labels.**  Every top disagreement pair is `moonshot_hXX_XX` (candidate) vs
`off_configured_session` (kill zone) — the extended hourly windows exist for one
function and not the other.  Any downstream analysis conditioned on "session"
gets a different answer depending on which field it read.

### 5.3 Fixed-UTC windows against exchanges that move: 8.22 % of rows mislabelled

Every window is a fixed UTC clock time; the exchanges named track their own DST
calendars.  Measured against each session's own exchange zone (Europe/London,
America/New_York, Asia/Tokyo, Europe/Berlin for GER40), taking northern summer as
the authored regime: **99,606 of 1,211,077 rows (8.22 %) carry a session label
that flips** — 49,435 London, 50,171 NY, all 60-minute shifts.

### 5.4 `session_open_range_break` measures the wrong range for 78 % of its rows

The family walks back to the first bar of the current session and calls that the
open range (`:916-926`).  Where does that bar land in the exchange's own clock?

| session | rows | open-range start, exchange local | correct? |
|---|---:|---|---|
| **ny** (3,637) | 1,720 | **08:00** | no — 90 min early |
| | 1,680 | **09:00** | no — 30 min early |
| | 87 / 79 | 08:30 / 10:00 | no |
| | **66** | **09:30** | **yes — 1.8 %** |
| **london** (3,265) | 1,897 | **07:00** | no — 60 min early |
| | **1,160** | **08:00** | **yes — 35.5 %** |
| | 148 / 60 | 09:00 / 10:00 | no |
| **tokyo** (1,293) | 1,293 | **09:00** | **yes — 100 %** |

**98.2 % of the NY "session open range" candidates and 64.5 % of the London ones
measure a range that starts before the session they are named after opens.**  The
NY window's authored start (13:00 UTC) is 08:00 or 09:00 New York local and can
never be 09:30.  Only Tokyo is right, by the accident that 00:00 UTC is 09:00 JST
year-round (Japan has no DST).

*Receipt:* `d4_out/CLOCK_8MO.json` (`CLOCK_7MO.json`, `CLOCK_2MO.json` retained).

---

## 6. LOOK-AHEAD — refuted twice, independently

**Probe 1 (structural, whole population).**  §2's hand-written re-implementation
uses only bars at index ≤ i and reproduces 144,725 of 144,725 emissions
bit-for-bit on entry, stop and target.  A family that read a future bar could not
be reproduced this way.

**Probe 2 (direct, adversarial).**  `d4_lookahead.py` runs the real generator at
the same decision instant with two source sets: (A) trimmed to [T−75 d, T+2 d] —
what the replay passes, where the only barrier is `raw_data_for_asof`'s asof
filter; and (B) **hard-truncated to [T−75 d, T]** so no row whose close is after T
exists on any timeframe for any symbol, including the cross-asset leaders.

> 24 decision instants, 2 days, 24 symbols, all 10 families, **1,678 candidates in
> each arm — byte-identical on `(origin_family, side, entry_price, stop_loss,
> take_profit_1, candidate_id)` at 24 of 24 instants.  Zero rows differ.**

The asof contract holds.  There is **no look-ahead in the broad-family
generator**, at-market or POI.

*Receipt:* `d4_out/LOOKAHEAD_V1.json`.

---

## 7. Three secondary defects found on the way

### 7.1 Stale-bar decisions: 3.35 % of at-market entries are priced at a level the market has gapped away from

`_selected_closed_bar_open` (`:2196-2198`) walks back to the last closed bar with
**no maximum-age check**.  Across a session gap or weekend the decision at T is
taken on a bar that closed hours earlier, and the at-market families set
`entry = bar.close`.

Measured (2025-11, 2025-12, 2026-04; 54,503 at-market rows):

* **1,826 rows (3.35 %)** are decided on a stale bar.
* Displacement between the emitted entry and the next actual print, in R:
  **median 2.42 R**, p75 5.69, p95 15.94, p99 29.48, max 86.21.
* **67.1 % are displaced by more than a full R** — the "at-market" entry is
  unavailable by more than the entire stop distance.

Pooled across all eight windows, 66,383 of 1,211,077 rows (5.48 %) are stale-bar
decisions; the at-market subset is 3,883 of 144,725 (2.68 %).
`session_open_range_break` is the only family with **zero** stale rows — its
session predicate excludes them by construction.

*Receipt:* `d4_out/STALE_V1.json`.

### 7.2 Two ATR definitions inside one candidate

The at-market families' stops, and every `predecision_features` value, use `_atr`
= **mean(high − low)** (`:2275-2279`) — a simple mean that ignores gaps.  The POI
families' stop buffers and `poi_distance_to_zone_atr` prefer the MSO's `atr_14`,
which is a **Wilder-smoothed TRUE RANGE** ATR (`market_state.py:461-478`, via
`_current_framework_atr` `:1654-1660`).  Measured ratio over 5,585 sampled
bar-instants across all 24 symbols: median **1.0141**, mean 1.0468, p05 0.823,
p95 1.383.  Modest at the median, ±20–38 % at the tails, and the two are used to
size stops inside the same candidate contract.

### 7.3 The fillability model ranks the dead rows highest

Where a fill probability IS computed — `current_fvg_fill` only (`:1246-1258`);
`current_ob_retest` and `current_breaker_re_entry` compute **none at all** —
`predecision_limit_fillability_from_geometry` (`poi_execution_lifecycle.py:163-178`)
sets

```python
limit_marketable = (side == "LONG"  and entry >= current) \
                or (side == "SHORT" and entry <= current)
```

**without reference to the stop**, and awards `limit_marketable` the top score
(0.92 on both components, `:176-178`).  A candidate whose stop the market has
already breached satisfies that test by construction, so it receives the highest
fill probability in the model.  The signal meant to rank executability ranks
structural death first.

---

## 8. Verdict

| question (d4 brief) | answer |
|---|---|
| 1. Do emitted candidates satisfy their defining condition? | **At-market: yes — 144,725/144,725, zero violations, seven families, eight windows.  POI: the condition as coded is satisfied, but the condition as coded admits 11.2–13.5 R of distance on a 1.5 R trade.** |
| 2. Any family with a material violation rate = a BUG, the cheapest fix in the estate | **`current_breaker_re_entry`.  25.7 % of emissions and 69.5 % of its FILLS born past their own stop, 100 % fill rate, −1.304 R net each, 91.8 % of the family's loss.  Fix at `broader_origin_generators.py:1201/:1391/:1446` — one predicate, R-denominated, everything it needs already in scope.** |
| 3. Is the geometry where the logic says?  Is born-past-stop a generator defect or a market gap? | **Geometry exact to 1e-9 on 144,725 at-market rows.  Born-past-stop is a GENERATOR DEFECT and it is entirely a POI phenomenon — at-market entry is the bar close, so `fill_gap_R = 0` by construction.  Root cause: a percent-of-price gate on an R-denominated contract, plus no predicate anywhere comparing current price to the candidate's own stop.** |
| 4. Clock and session-boundary correctness | **Tape is true UTC (confirmed on the weekly open).  But: two session functions disagree on 65.71 % of candidates; 8.22 % of rows carry a DST-wrong session label; and 98.2 % of NY / 64.5 % of London `session_open_range_break` candidates measure a range that starts before the session opens.** |
| 5. Look-ahead | **None.  Refuted twice — by bit-for-bit closed-bar reproduction of 144,725 emissions, and by a hard-truncation A/B at 24 instants where 1,678 candidates are byte-identical in both arms.** |

**Axis.**  The at-market half is a clean **signal** verdict: the setups are exactly
what they claim, they are not corrupted by look-ahead, and they still do not pay —
so their emptiness is a property of the setups, not of a bug.  The POI half is a
genuine repairable defect (**usage** — the emission gate destroys a contract the
rest of the machinery then measures honestly) sitting on top of a **signal**
floor: repair it and the correctly-formed limit book books gross −0.01065 R/fill
against a 0.23916 R/fill toll.

**What would have to be true for the POI half to work.**  With the gate repaired,
the resting book needs +0.24981 R/fill of gross it does not have.  At its measured
payoff that is roughly 8–9 percentage points of win rate on 69,233 fills.  Nothing
in the geometry supplies it; the repair removes a catastrophe, it does not create
an edge.

---

## 9. Files

All under `phase19/receipts/discovery/`:

* `d4_RESULT.md` (this file), `d4_RESULT.json`
* `d4_lib.py` — independent re-implementation of the seven at-market predicates
* `d4_verify.py` — forward + reverse condition/geometry verification
* `d4_poi.py` — the `fill_gap_R` partition
* `d4_poi_econ.py` — walks the partition on the M1 tape with broker-true cost
* `d4_poi_capture.py` — captures the POI zone behind each candidate
* `d4_zoneverify.py` — contract-denominated zone-history tests
* `d4_clock.py` — anchor, two-session-function, DST, session-open alignment
* `d4_lookahead.py` — hard-truncation A/B
* `d4_out/` — every JSON receipt named above

Nothing under `src/` was edited.  No arms, no sealed replays, no broker scripts.
The sealed three (Jun/Aug/Sep 2025) were not opened.
