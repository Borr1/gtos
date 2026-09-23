# x2 — when was each setup FIRST detectable?

Lane key `x2`. January 2026, true-UTC S0R0 pool, **all 27,658 rows, no sampling**. Every
number below is measured on this machine from the M1/M15 lane-hold sources; every condition is
transcribed from `src/components/broader_origin_generators.py` with line numbers.

**Provenance note.** An earlier x2 attempt in this wave left four receipts
(`x2_EARLINESS_ROWS_V1.jsonl.gz`, `x2_AGG_FAMILY_V1.json`, `x2_AGG_COMPONENT_V1.json`,
`x2_EARLY_ENTRY_WALK_V1.jsonl.gz`, scripts `x2_earliness.py` / `x2_early_entry_walk.py`,
written 13:18-13:21) and no `x2_RESULT`. This session rebuilt the measurement independently
from source before reading them, and **the two agree to the last digit** where they overlap
- e.g. `cross_asset_lead_lag` fires at the first minute on `0.9469586374695864` of pool rows
in both. Its minute index is 1-based (its "minute 1" is this receipt's offset 0). Its
early-entry walk is the economics this session flagged as unpriced, and is folded in at §4b
with attribution. **One repair owed and made:** this session's `x2_bars.py` overwrote the
earlier attempt's file of the same name (both untracked, so git could not recover it); the four
functions its scripts call - `m15`, `m1`, `m15_index_for_decision`, `m1_slice` - have been
re-implemented and verified, so both prior scripts run again.

---

## HEADLINE

**96.69 % of the 27,108 January decisions whose defining condition I can locate in time were
already true before the instant the system made them. Median earliness 14 minutes; 84.57 % were
detectable at least 5 minutes early. For the 15,704 decisions whose condition lives inside the
decision bar, median earliness is 9 minutes — the system waits, on average, 8.60 minutes after
it could already have known.**

The other 11,404 (the three `current_*` POI families) are not "minutes early" at all: their
setups are pre-existing objects. A `current_fvg_fill` zone is detectable a median of **135
minutes** before the decision bar even opens; `current_breaker_re_entry` stands on **225
distinct zones re-emitted 18.95× each**, median 840 minutes from first emission.

---

## 0. Validation — the reconstruction is exact, and it settles the clock

| check | result |
|---|---|
| M15 close at `decision_time − 15 min` == pool `entry_price`, closed-bar families | **14,809 / 14,809** exact (rel < 1e-9) |
| close-time re-evaluation reproduces the pool, 6 single-symbol families | **recall 1.0000**, side match **100 %** |
| `cross_asset_lead_lag` side reproduction | **1,172 / 1,172** |
| `current_fvg_fill` zone recovered by exact midpoint match | **6,879 / 6,879**, 0 misses |
| MSO `atr_14` identified | Wilder ATR-14 on M15; implied-buffer ratio **1.0000** at p10 and p90 |
| zone half-width from `risk_distance − b·atr14` vs exact FVG zone | max rel err **8.3e-12** |
| rows with no M15 decision bar (broker maintenance gaps) | 419 (1.5 %) |

**The pool's session windows are TRUE UTC, not broker+2 h.** `session_open_range_break`
reproduces at **recall 1.0000** under true-UTC session windows and **0.1094** under
broker-clock (+2 h) windows. That settles a live question about what the CJ re-clock did to
session-dependent generators: it moved them.

---

## 1. The ten defining conditions, written down (deliverable)

`bar` = decision M15 bar at index `i`. `_atr(n)` is the module's **mean high−low over the last
n bars including the current one** (`:2275`), *not* Wilder. `_prior_high(20)` = max high over
`bars[i−20:i]`, **excluding** the current bar (`:2265`).

| family | condition (source) | pre-bar constants | bar-dependent part |
|---|---|---|---|
| `liquidity_sweep_reclaim` | `:705-737` — `high > prior_20_high AND close < prior_20_high` → SHORT (mirror → LONG); XOR both sides | `prior_20_high/low` | running high (monotone) + running close (revocable) |
| `displacement_continuation` | `:739-757` — `range/atr14 ≥ 1.5 AND |close−open|/atr14 ≥ 0.75`; side = `sign(close−open)` | none | **bar shape — body and SIDE both need the close** |
| `volatility_compression_expansion` | `:759-797` — `atr14(i−1)/atr50(i−1) ≤ 0.75 AND range/atr14 ≥ 1.25 AND (close > prior_20_high → LONG | close < prior_20_low → SHORT)` | prior compression ratio, prior_20 levels | range + level break |
| `session_open_range_break` | `:902-968` — session's first-bar range `[rl, rh]` from bars < i, no earlier break, then `close > rh` → LONG / `close < rl` → SHORT | **the whole range and `previous_break_seen`** | one level test on running close |
| `regime_transition_break` | `:812-846` — `trend(i)=strong_up` (`(close−close[i−20])/atr50 ≥ 2`) AND `trend(i−1) ∉ {strong_up,up}` AND `close > prior_20_high` | previous trend state, `close[i−20]`, prior_20 levels | two level tests on running close |
| `structural_distance_extreme` | `:848-884` + `_close_position:2282` — `pos50 = (close − low50)/(high50 − low50) ≥ 0.97` → SHORT, `≤ 0.03` → LONG; the 50-bar range **includes** the current bar | 49-bar high/low | position of running close in an expanding range |
| `cross_asset_lead_lag` | `:974-1060` — leader's M15 bar **closing at the lag bar's open**: `|Δclose|/atr14 ≥ 1.0`; lag: `|close−close[i−1]|/atr14 ≤ 0.5`; side = sign of leader move | **the entire leader leg** | a quietness test that starts true and can only break |
| `current_fvg_fill` | `:1157-1341` — unfilled, uninvalidated M15 FVG (`market_state.identify_fvgs:926`), `proximity ≤ 0.01`; entry = zone midpoint, stop = far edge ∓ 0.25·ATR | **the zone** (3 closed M15 bars) | proximity of running price |
| `current_ob_retest` | `:1382-1432` — unmitigated **H1** order block, same proximity gate, buffer 0.5·ATR | **the zone** (H1) | proximity |
| `current_breaker_re_entry` | `:1436-1487` — un-retested **H1** breaker block, buffer 0.25·ATR | **the zone** (H1) | proximity |

---

## 2. First minute the condition became true, on the actual pool decisions

`off` = M1 offset 0…14 inside the decision bar; the condition is known at `T+off+1`; the
decision arrives at `T+15`, so **earliness = 14 − off** minutes. This is a 60-second poller's
view — exactly what `run_book.py:99 --poll-seconds 60` already runs.

| family | n | fires at **T+1** | median off | median earliness | needs the final minute |
|---|---:|---:|---:|---:|---:|
| `cross_asset_lead_lag` | 2,055 | **94.70 %** | 0 | **14 min** | 0.15 % |
| `structural_distance_extreme` | 1,969 | 35.80 % | 2 | **12 min** | 5.8 % |
| `session_open_range_break` | 987 | 20.77 % | 4 | **10 min** | 4.6 % |
| `liquidity_sweep_reclaim` | 4,451 | 14.13 % | 5 | **9 min** | 4.7 % |
| `regime_transition_break` | 297 | 5.39 % | 8 | 6 min | 13.5 % |
| `volatility_compression_expansion` | 605 | 3.47 % | 9 | 5 min | 9.9 % |
| `displacement_continuation` | 4,445 | 3.58 % | 9 | 5 min | 9.4 % |

Full 15-bin histograms are in `x2_RESULT.json → families.*.first_true_offset.histogram`.
**Only 4.6–13.5 % of decisions in any family genuinely require the last minute of the bar.**

For the three POI families the question is different, because the setup is an object, not an
event:

| family | n | proximity true at **T+1** | proximity true all 15 min | detectable window before the bar OPENED |
|---|---:|---:|---:|---|
| `current_fvg_fill` | 6,794 | **99.04 %** | 94.94 % | **median 135 min** (exact: bounded by the FVG's own formation bar); p75 432, p90 968; 11.88 % zone born on the decision bar |
| `current_ob_retest` | 1,326 | 97.81 % | 96.46 % | continuous proximity median **3,485 min**, 43.5 % censored at the 3-day scan limit |
| `current_breaker_re_entry` | 4,179 | 98.92 % | 95.17 % | continuous proximity median **4,320 min** (i.e. ≥ 3 days for 50.3 %) |

---

## 3. The structural split — what is early-detectable and what genuinely needs the close

**A. Pre-bar constants — known before the decision bar opened at all.**
The `cross_asset_lead_lag` leader leg (its bar closes exactly when the lag bar opens); all
three POI zones; `session_open_range_break`'s range *and* its `previous_break_seen` gate;
`volatility_compression_expansion`'s compression ratio; `regime_transition_break`'s previous
trend state; every `prior_20/50` level.

**B. Level tests on the running price — knowable the instant price does it, but revocable.**
The sweep leg of `liquidity_sweep_reclaim` (monotone in the running high — once true, true);
the break legs of `session_open_range_break`, `volatility_compression_expansion` and
`regime_transition_break`; `structural_distance_extreme`'s position test; the POI proximity gate.

**C. Genuinely needs the completed bar.**
Only three legs in the whole estate:
1. **`displacement_continuation`'s body test and its SIDE** — `sign(close−open)` is undefined
   until the bar closes. This is the one family whose *identity* is a bar-close property.
2. **`liquidity_sweep_reclaim`'s reclaim leg** — "close back inside" is a statement about
   where the bar finishes.
3. **`cross_asset_lead_lag`'s quietness leg** — `|lag move| ≤ 0.5 ATR` is a claim about the
   whole bar.

**The price of acting on A+B without waiting for C** (all January bars, not just pool rows):

| family | bars firing early | survive to the close | same side |
|---|---:|---:|---:|
| `displacement_continuation` | 6,237 | **83.05 %** | 81.98 % |
| `volatility_compression_expansion` | 946 | 76.74 % | 76.53 % |
| `regime_transition_break` | 513 | 66.67 % | 66.67 % |
| `liquidity_sweep_reclaim` | 8,602 | 63.80 % | 63.80 % |
| `session_open_range_break` | 1,636 | 62.71 % | 61.37 % |
| `cross_asset_lead_lag` | 5,294 | 52.49 % | 52.49 % |
| `structural_distance_extreme` | 8,482 | **35.22 %** | 35.22 % |

---

## 4. What the wait costs — measured, and it runs BOTH ways

`giveup_r = side_sign · (M15 close − price at the first-detect minute) / risk_distance`.
Positive = the move had already happened before the system transacted.

| family | n | mean | se | median |
|---|---:|---:|---:|---:|
| `liquidity_sweep_reclaim` | 4,451 | **+0.2566** | 0.0042 | +0.2650 |
| `session_open_range_break` | 987 | **+0.1509** | 0.0068 | +0.1262 |
| `regime_transition_break` | 297 | +0.0684 | 0.0074 | +0.0408 |
| `displacement_continuation` | 4,445 | +0.0524 | 0.0036 | +0.0266 |
| `volatility_compression_expansion` | 605 | +0.0386 | 0.0048 | +0.0106 |
| `structural_distance_extreme` | 1,969 | **−1.0870** | 0.0306 | −0.6784 |
| ALL | 12,754 | −0.0449 | 0.0065 | **+0.0595** |

`liquidity_sweep_reclaim` hands back **a quarter of a risk unit** by waiting for the close —
against a family gross of −0.0403 R/trade, the wait is 6× the size of the loss.
`structural_distance_extreme` is the opposite: waiting **improves** its entry by 1.087 R,
because `pos50 ≥ 0.97` fires while price is still extending, and the short is being handed a
better price every minute it waits. **Earliness is not one lever; it is at least two, with
opposite signs, and the family is the switch.**

### 4b. The early entry, actually walked (earlier x2 attempt, re-aggregated here)

`x2_early_entry_walk.py` holds the **stop and target PRICE LEVELS fixed** and moves only the
entry to the first-detect minute, expressing the result in units of the original
`risk_distance`, then walks the remaining minutes of the decision bar on M1 (conservative tie
rule). n = 14,809, the seven close-entry families:

| family | n | plain (at close) | early entry | delta | se | resolved inside the bar |
|---|---:|---:|---:|---:|---:|---:|
| `liquidity_sweep_reclaim` | 4,451 | −0.0178 | **+0.2455** | **+0.2633** | 0.0045 | 13 |
| `session_open_range_break` | 987 | −0.0673 | +0.0646 | **+0.1319** | 0.0056 | 1 |
| `regime_transition_break` | 297 | −0.0035 | +0.0648 | +0.0684 | 0.0074 | 0 |
| `displacement_continuation` | 4,445 | −0.0834 | −0.0379 | +0.0455 | 0.0035 | 1 |
| `cross_asset_lead_lag` | 2,055 | −0.0772 | −0.0364 | +0.0408 | 0.0149 | 147 |
| `volatility_compression_expansion` | 605 | −0.0918 | −0.0556 | +0.0362 | 0.0044 | 0 |
| `structural_distance_extreme` | 1,969 | −0.0746 | −0.4862 | **−0.4116** | 0.0279 | **624** |
| **ALL** | **14,809** | **−0.0593** | **−0.0039** | **+0.0554** | **0.0049** | 786 |

Six of seven families improve; the seventh (`structural_distance_extreme`) is destroyed, and
it is destroyed in a specific way — **31.7 % of its early entries resolve to target inside the
remaining minutes of the decision bar** (624 of 1,969, against 786 in-bar resolutions across
all seven families) and it *still* loses 0.41 R. Entering the extreme early buys a burst of
quick winners and pays for them with the trend that keeps going.

**A tension a later stage must resolve.** This lane's early-entry lever moves the seven
close-entry families −0.0593 → −0.0039 (+0.0554). The wave's own headline lever moves the
at-market book −0.0601 → +0.0069 by **delaying entry five minutes**. Same order of magnitude,
opposite direction in time, overlapping populations. They cannot both be the mechanism; the
family split above says why — `liquidity_sweep_reclaim` wants to be earlier and
`structural_distance_extreme` wants to be later, and a book-level average of the two is
uninformative about either.

**Second-order and unpriced even after 4b:** the early entry also gets a *different* stop if
the stop is re-derived rather than held fixed, because
several families derive the stop from the bar's own extreme. Entering at the first-detect
minute gives `liquidity_sweep_reclaim` a stop only **0.646×** as wide (median; tighter on
83.64 % of trades), `structural_distance_extreme` 0.823×, `displacement_continuation` 0.971×.
A tighter stop is more R per unit of move *and* more likely to be hit. §4b prices the
fixed-levels contract; **the re-derived-stop contract is still unpriced**, and it is the one a
live generator would actually produce, since these families read the stop off the bar's own
extreme. Treat the §4 give-up column as an entry-price measurement only.

---

## 5. M1/M5-native analogues for the close-requiring conditions

**(a) Sweep-leg-only (M1-native level break).** Fire the minute the running high first prints
above `prior_20_high`, without waiting for the reclaim.

* recall **1.0000** (5,488/5,488 — by construction; the M15 rule needs the break)
* precision **0.4895** (5,488 of 11,212 level breaks resolve into a full M15 sweep+reclaim)
* break minute p25 0 / **median 3** / p75 7 → **median earliness 11 minutes**

**(b) M5-native displacement.** The identical shape test on a completed M5 sub-bar against an
M5-native ATR-14 (14 preceding M5 bars).

| known at | earliness | fires on | recall vs M15 | precision | same side when both fire |
|---|---:|---:|---:|---:|---:|
| T+5 (sub-bar 0) | 10 min | 6,248 | 0.4292 | 0.3558 | **0.9555** |
| T+10 (sub-bars 0–1) | 5 min | 10,067 | 0.6693 | 0.3444 | **0.9850** |
| T+15 (all three) | 0 min | 12,911 | 0.8164 | 0.3276 | 0.9981 |

The M5 analogue is a **superset** selector, not a contradictory one: it fires ~2.6× more often
than the M15 rule, but when both fire the direction agrees 95.6–99.8 % of the time. It never
disagrees about *which way*; it only disagrees about *whether*. Outcome on the pool rows is
flat — displacement rows with an M5 pre-fire by T+10 book −0.0934 vs −0.0837 without, so the
analogue selects a similar population at a similar price and buys 5–10 minutes.

**(c) POI families.** The native analogue is not a new trigger at all — it is *leaving the
limit resting at the zone midpoint*. **40.59 %** of `current_fvg_fill` entry levels had already
been traded inside their own exact detectable window (median **61 minutes** before the
decision), while the FVG remained formally unfilled: `identify_fvgs` marks an FVG filled only
when price reaches the **far** boundary (`market_state.py:851, :866`), and the entry sits at the
midpoint. The system arrives at a price the market already visited, on average an hour late.

---

## 6. Does anything inside the FORMING bar separate continuation from reversion?

18 new intra-bar features, all computed from the 15 M1 bars of the decision bar (strictly
pre-decision, and invisible to a system that only reads the completed M15 bar), tested by
Cohen's d between target-first (n=6,654) and stop-first (n=13,747). Estate benchmark on its
own 28 completed-bar fields: **|d| = 0.152**.

**The answer is no, and the null is clean.** Every *timing* feature is null:

| feature | \|d\| |
|---|---:|
| `ib_minute_of_high` | 0.0311 |
| `ib_minute_of_low` | 0.0138 |
| `ib_signed_adverse_minute` | 0.0033 |
| `ib_late_range_share` | 0.0293 |
| `ib_dir_changes` | 0.0757 |
| `ib_extreme_late` | 0.0742 |
| `ib_efficiency` (|close−open| / path length) | 0.1344 |
| `ib_second_half_drift_atr` | 0.0708 |
| `ib_body_atr` / `ib_range_atr` | 0.1407 / 0.1347 |

The two features that do clear the benchmark (`ib_adv_excursion_r` |d| 0.839,
`ib_fav_excursion_r` 0.848) are **not an edge** — they are the stop-breach artifact of §7 in
disguise; their bottom decile is n=2,723 at gross exactly −1.0000.

**The order in which the M15 bar was built carries no information about what happens next,
beyond what the completed bar already shows.** The estate's "no field predicts" result is not
an artifact of measuring at the close — it survives a 15× finer clock.

---

## 7. Corroboration, not discovery: the stop that was already gone

My microscope re-found a known result and should be read as corroboration.
`w0-capture` has it at 3,516 rows / 12.72 %, and lane `x1` at 13.29 %.

| check | n | share | gross R |
|---|---:|---:|---:|
| **close-only** — the decision bar's own close is already past the stop (no M1 needed) | 3,483 | 12.79 % | **−0.9948** |
| intra-bar — the stop was traded through anywhere in the 15 M1 bars | 3,675 | 13.50 % | −0.9554 |
| caught **only** by the intra-bar view | 192 | 0.70 % | −0.2423 |

Dropping the close-only set moves the pool from **−0.2148 → −0.1004 R/trade (+0.1144)**. The
extra 192 rows the M1 microscope adds are worth +0.0012 — **this is a decision-time arithmetic
omission, not an earliness problem**, and my lane's contribution is only the mechanism:

> **NEW — the proximity gate is denominated in the wrong unit.**
> `_zone_proximity_pct` (`:1711-1717`) returns `gap / price` and is compared to
> `poi_proximity_tolerance_pct = 0.01` (`config/agent_config.yaml:4032`) — **a fraction of
> price**. The trade's risk unit is the zone half-width + buffer·ATR, which for an H1 breaker
> is a median **0.000499 of price**. A 1 %-of-price gate therefore admits candidates a median
> **6.425 risk units** away (p99 **22.930**) in `current_breaker_re_entry`; 1.171 R in
> `current_ob_retest`; 0.983 R in `current_fvg_fill`. Nothing downstream reconciles the two
> units: on all 3,675 rows `entry_fill_executable` and `fill_realism_executable` are **True**,
> `source_completeness` is **1.0**, and `limit_marketable_at_decision` is **None** on 95.2 %.

---

## 8. A replication hazard this lane surfaced

`current_breaker_re_entry`'s 4,263 pool rows are **225 distinct zones** — 18.95 emissions each,
median 840 minutes and p90 4,800 minutes from first emission (zone identity = `(symbol, family,
entry_price = zone midpoint, side)`). **`w0_ws.dedup()` does not catch this**: it keys on
`candidate_id`, which is stable for `current_fvg_fill` (78.84 % repeats) but *not* for breakers
(0.99 % repeats by id). Any significance test on `current_breaker_re_entry` computed on 4,263
rows is inflated ≈19×. `current_ob_retest`: 1,340 rows / 333 zones (4.02×).
`current_fvg_fill`: 7,146 rows / 1,510 zones (4.73×).

---

## Artifacts

| file | what |
|---|---|
| `x2_RESULT.json` | every number above, machine-readable |
| `x2_bars.py` | shared M15/M1 loader for the true-UTC lane hold |
| `x2_fvg_recon.py` → `x2_FVG_ZONES_V1.jsonl.gz` | exact FVG zone + formation bar for 6,879 candidates (midpoint match, 0 misses) |
| `x2_closed_families.py` → `x2_CLOSED_FIRSTTRUE_V1.jsonl.gz` | 27,420 rows: per-minute condition evaluation for six families over every January M15 bar |
| `x2_crossasset.py` → `x2_CROSSASSET_V1.jsonl.gz` | 5,440 leader-qualified bars, lag quietness by minute |
| `x2_poi_families.py` → `x2_POI_DETECTABILITY_V1.jsonl.gz` | 12,299 POI rows: zone, proximity by minute, backward continuity, entry-touch |
| `x2_FVG_DETECT_WINDOW_V1.jsonl.gz` | FVG detect window bounded by formation + entry-touch inside it |
| `x2_native_analogues.py` → `x2_NATIVE_ANALOGUES_V1.jsonl.gz` | 48,991 bars: sweep-leg-only and M5-native displacement |
| `x2_intrabar_features.py` → `x2_INTRABAR_FEATURES_V1.jsonl.gz` | 27,230 rows × 18 new intra-bar features |
| `x2_separator_test.py` → `x2_SEPARATOR_V1.json` | Cohen's d and decile tables for all 18 |
| `x2_summarise.py` | aggregation |
| `x2_earliness.py`, `x2_EARLINESS_ROWS_V1.jsonl.gz`, `x2_AGG_FAMILY_V1.json`, `x2_AGG_COMPONENT_V1.json` | **earlier x2 attempt**, independently reproduced by this session |
| `x2_early_entry_walk.py` → `x2_EARLY_ENTRY_WALK_V1.jsonl.gz` | **earlier x2 attempt**: 14,809 early-entry walks, re-aggregated at §4b |

## Caveats

* One month, one arm (January 2026 true-UTC S0R0). No travel test.
* Path horizon is 2 hours (w0 substrate); nothing here speaks to longer holds.
* The give-up column is an **entry-price** measurement. It does not include the changed stop,
  the changed target, or the changed fill probability of an early entry. Do not read it as a
  P&L claim.
* Early-fire survival rates (§3) are computed over all January bars, including bars the
  scheduler would never have reached.
* 419 pool rows (1.5 %) have no M15 decision bar in the lane hold (index/commodity maintenance
  gaps) and are excluded throughout.
* `w0_ws.dedup()` was **not** applied. §8 says why that matters more than the README implies.
