# x1 — the exact anatomy of a decision, in source and in time

Lane key `x1`. January 2026, true-UTC S0R0 pool, **all 27,658 rows, no sampling**.
Everything below is measured on this machine from the M1/M15 sources the sidecar itself
names, or read from source with `file:line`.

**Provenance note.** An earlier x1 attempt in this wave left three receipts
(`x1_A_ANCHOR_V1.json`, `x1_B_STALENESS_V1.json`, `x1_C_PRICE_V1.json`, scripts
`x1_a_anchor.py` / `x1_b_staleness.py` / `x1_c_price.py`, written 13:16–13:21) and no
`x1_RESULT`. This session read them, reproduced their two load-bearing results
independently, and then measured the things they did not: the source trace, the
timeframe-constraint question, the live-poll behaviour, and **what earliness actually
books**. Their numbers are cited as `x1-A/B/C` and are marked where I re-derived them.

---

## HEADLINE

**8,417 January candidates in the five continuation-shaped families book −0.0771 R/trade
entered at their own bar's close — the contract the system runs — and +0.6669 R/trade
entered one M15 bar earlier, at the same risk distance, the same target and the same
120-minute horizon. 21 of 21 trading days positive, day-clustered t = 34.5. The gap is
+0.744 R/trade, and the decay across the 30-minute window is monotone at
≈0.026 R/trade per minute of waiting.**

The bar close is not a neutral sampling instant. For continuation setups it is the single
worst price in the half hour around it, and the system transacts there by construction.

---

## Q1 — how a candidate is produced, in source

### The chain, with line numbers

| step | site | what happens |
|---|---|---|
| 1 | `v4_timewarp_simulated_live_research_loop.py:58990-59006` | `ReplayClock.decision_times_for_day` builds the day's decision grid as `{M15 bar open + 15 min}` unioned over the 24 symbols. The `+timedelta(minutes=15)` is a literal. |
| 2 | `:90549` | `for window_ordinal, asof in enumerate(window_times)` — one pass per grid instant. |
| 3 | `:90694` → `:59313-59343` | `live_replay.snapshot(symbol, asof)` calls **the live ingestion function** `ingest_live_data` (`data_ingestion.py:73`) through `HistoricalMT5Adapter`. Replay and live share this code path. |
| 4 | `:59456-59473` (`raw_data_for_asof`) | for each of `PRIMARY_DECISION_TIMEFRAMES` (`:315` = `("D1","H4","H1","M15")`) it reads `closed_bar_rows_until(...)`. |
| 5 | `:4964-5000` | the closed-bar filter: a bar is admissible iff `bar_open + timeframe_minutes <= asof + 2 s` (`:4985`, `:4995-4996`). The newest M15 bar admitted is exactly the one **closing at `asof`**. |
| 6 | lookbacks `agent_config.yaml:3822-3826` / `data_ingestion.py:59` | D1 30, H4 80, H1 168, **M15 672**. Every decision reads 950 bars. |
| 7 | `market_state.py:1352` | `compute_market_state` builds the MSO: `for tf in ("D1","H4","H1","M15")` — structure, FVGs, order blocks, breakers, per timeframe. |
| 8 | `broader_origin_generators.py:290-295` | `_series_from_raw_data(..., timeframe="M15")`; `index` = the latest closed M15 bar. `< 51` bars → no candidates. |
| 9 | `broader_origin_generators.py:608-899` and `1065-1531` | the ten families' predicates and geometry. |
| 10 | `broader_origin_generators.py:1856-1962` (`_candidate`) | stamps `candle_open_utc`, `candle_close_utc = open + 15 min`, `timeframe = series.timeframe`, `market_timeframe = series.timeframe`. **This is why every pool row reads `decision_timeframe = M15`: it is the series literal at step 8, not a policy setting.** |

### What EXACTLY is knowable at the bar close that was not knowable at the bar open

**Exactly one scalar per symbol: `bar.close`.** Every other input to every predicate is
either

* a **prior-closed-bar** quantity, fully known at the decision bar's open —
  `prior_20_high/low` and `prior_50_high/low` (`:2265-2272`, windows are `[index-N:index]`,
  the current bar is **excluded**), `_previous_trend_state` (`:2307`), the prior-bar ATR
  ratio used by `volatility_compression_expansion` (`:765-772`), the session open range
  (`:915-925`), the FVG/OB/breaker zones (`:1098`, `:1384`, `:1439`), and the leader's move
  in `cross_asset_lead_lag` (`:988`, which reads the leader bar **15 minutes older still**);
  or
* a **running** quantity that only ratchets during the bar — `bar.high`, `bar.low`,
  `bar_range`, and `atr14`/`atr50` (`:2275-2279`, windows are `[index-N+1:index+1]`, i.e.
  they *include* the forming bar's own range).

And the close is used as **the price the system will transact at**. Directly measured:

```
entry = bar.close    for 7 of 10 families, 14,909 of 27,658 rows (53.90 %)
  _candidate(...) call sites at broader_origin_generators.py:
  712 / 729 (liquidity_sweep_reclaim), 749 (displacement_continuation),
  776 / 794 (volatility_compression_expansion), 826 / 844 (regime_transition_break),
  864 / 882 (structural_distance_extreme), 936 / 954 (session_open_range_break),
  1031 (cross_asset_lead_lag), 681 / 695 (range_extreme_reversion, default-off)
entry = zone midpoint (low+high)/2   for the 3 current_* families, 12,749 rows (46.10 %)
  broader_origin_generators.py:1616-1628 (_current_framework_geometry)
```

x1-A verified the anchor and I reproduce it: of the 14,909 close-entry rows,
**14,809 match the close of the bar OPENING at `decision_time − 15 min`** and 129 match the
bar opening at `decision_time` (coincidental equalities). The decision bar is the bar
**closing at** `decision_time_utc`.

x1-A also reproduced every close-entry family's **stop** from the M15 series:
**13,822 / 13,822 exact, worst relative error 0.000000**, across
`cross_asset_lead_lag`, `displacement_continuation`, `liquidity_sweep_reclaim`,
`regime_transition_break`, `structural_distance_extreme`,
`volatility_compression_expansion`. The whole feature stack reconstructs exactly.

**My own independent validation of the substrate** (`x1_INTRABAR_ROWS_V1.jsonl.gz`):
rebuilding each decision M15 bar from its own 15 M1 bars reproduces the M15 file's
high, low and close on **27,239 / 27,239 bars with maximum relative error 0.000000**.
95.22 % of decision bars carry all 15 M1 bars (mean 14.65).

---

## Q2 — is M15 architectural, or a configured choice?

**It is a choice, expressed as four literals and two hardcoded `15`s. Nothing downstream
structurally requires it, and the live book already runs three other decision timeframes
today.**

### Every site where the timeframe is set, derived or assumed

| site | form | blocks a finer grid? |
|---|---|---|
| `data_ingestion.py:55` | `TIMEFRAMES = ("D1","H4","H1","M15")` | **literal** — this is the live fetch set, and replay uses the same function (Q1 step 3) |
| `data_ingestion.py:56` | `TF_MAP` — 4 entries | literal; `TF_MINUTES` at `:57` **already carries `M5: 5` and `M1: 1`** |
| `data_ingestion.py:59` / `agent_config.yaml:3822-3826` | `DEFAULT_LOOKBACKS` 4 keys | config; `.get(tf, 100)` / `.get(tf, 500)` fallbacks exist |
| `market_state.py:1352` | `for tf in ("D1","H4","H1","M15")` | **literal** in the MSO builder |
| `market_state.py:105` | `_TF_MINUTES = {"M15":15,"H1":60,"H4":240,"D1":1440}` | **the one real hazard**: `:803` reads it with `.get(timeframe, 15)`, so an M5 or M1 timeframe would silently be scaled as M15 in the BVC order-flow proxy |
| `v4_timewarp:315` | `PRIMARY_DECISION_TIMEFRAMES` | **literal** |
| `v4_timewarp:58993` | `row_time + timedelta(minutes=15)` | **hardcoded 15** in the replay decision grid |
| `broader_origin_generators.py:293` | `timeframe="M15"` | **literal** — the single line that makes every pool row M15 |
| `broader_origin_generators.py:988` | `previous_leader_time = latest_lag.time - timedelta(minutes=15)` | **hardcoded 15** — the cross-asset lead offset |
| `broader_origin_generators.py:1098 / 1384 / 1439` | FVG source = MSO **M15**; OB and breaker sources = MSO **H1** | literal per framework |
| `broader_origin_generators.py:1094, 1879` | `TIMEFRAME_MINUTES.get(series.timeframe, 15)` | generic, with a 15 default |
| `broader_origin_generators.py:1655` | `_current_framework_atr` → `_mso_timeframe(mso,"M15")` | literal |
| `data_ingestion.py:190-206` | `filter_closed_candles` — *"The live MT5 rate buffer can expose the in-progress bar immediately after a close. That bar is not valid production market-state evidence."* | **this is the doctrine, stated in the source**: the forming bar is deliberately discarded |

### What is generic

Every indicator in the generator is index-based on `series.bars`
(`_atr`, `_prior_high/_low`, `_close_position`, `_trend_state`, `_predecision_features`) and
carries no minute arithmetic. `_build_timeframe_state` (`market_state.py:1157`) is
parameterised on `tf_name`. `swing_detection_min_bars` and `fvg_min_gap` are per-timeframe
config maps read with `.get(tf, default)`. The generator's only size requirement is
`len(series.bars) >= 51` (`:294`) — 255 minutes of history at M5.

### The decisive facts

1. **M1 is already resolved and in memory at every decision, and deliberately withheld.**
   `PRIMARY_SOURCE_TIMEFRAMES = ("D1","H4","H1","M15","M1")` (`v4_timewarp:316`) while
   `PRIMARY_DECISION_TIMEFRAMES` (`:315`) omits M1. Each decision's own metadata records the
   omission by name: `post_decision_path_timeframes_available_but_not_attached`
   (`:59331-59335`, `:59534`), `m1_or_tick_attached_to_decision: False` (`:59551`), and
   `predecision_tick_features_disabled_reason =
   "replay_source_separation_predecision_uses_d1_h4_h1_m15_closed_bars_only"` (`:59342`).
   The data is in the process. The decision function is handed a 4-tuple that omits it.

2. **The live book is already multi-timeframe.** `active_specs` resolves 20 specs at
   `timeframe` ∈ {16388 (H4) ×9, **15 (M15) ×10**, 16408 (D1) ×1}; `launcher.py:106-109`
   builds `_tf_tags` generically from `spec.timeframe`;
   `book_engine.py` `_TF_MINUTES = {1:1, 5:5, 15:15, 30:30, 16385:60, 16388:240, 16408:1440}`
   and `launcher.py DEFAULT_REF_SYMBOL` carries a **`1:` (M1) key**. The launcher's own
   comment names `M1 (1, vp_euidx)` as an active decision timeframe. Nothing in the live
   loop needs changing to decide on a finer grid.

**Verdict: M15 is a source-selection decision. Moving the broad-origin generator to M5 or
M1 needs four literal edits, two `15`s replaced by `TIMEFRAME_MINUTES[tf]`, one config key
per new lookback, and one entry added to `market_state._TF_MINUTES` so BVC does not
silently mis-scale.** Two semantics *change* rather than break: the session opening range
is defined as the first two bars of the session (`:915-925`), and the cross-asset lead is
one bar.

---

## Q3 — staleness: how much of the bar has printed by the time the condition is true

### The bar is over before the system looks

Mean fraction of the decision bar's **final** high-low range already printed by minute k,
pooled over 27,239 reconstructed bars:

```
k0 0.286  k1 0.400  k2 0.481  k3 0.549  k4 0.607  k5 0.665  k6 0.715  k7 0.759
k8 0.798  k9 0.833  k10 0.871  k11 0.906  k12 0.941  k13 0.971  k14 1.000
```

**28.6 % of the bar's range is printed in its first minute. 75.9 % by minute 7.** The
median bar makes its high at minute 6 and its low at minute 5 (means 6.62 / 6.05).

Two consequences that price the whole convention:

* **13.29 % of candidates had their own stop level already traded through, inside their own
  decision bar** — the trade was already dead when it was born.
* **19.90 % had their `take_profit_1` level already reached inside the decision bar** — one
  in five setups had completed its intended 2R move before the system was allowed to look.
* The best price available inside the decision bar, in the trade's own direction, is a
  **median 0.6034 R and a mean 1.2831 R better than the entry actually used.**

### When the defining condition first became true, per family

x1-B measured this on 27,074 rows; I re-derived it independently for the five
exactly-reproducible families in `x1_D_EARLYWALK_ROWS_V1.jsonl.gz` and the confirm-minute
distributions agree (pooled median k\* = 7, mean 6.61).

| family | n | median confirm minute (0-based) | **minutes early vs the close** | median range already printed at confirm |
|---|---:|---:|---:|---:|
| `current_fvg_fill` | 6,879 | 0 | **14** | 0.283 |
| `current_ob_retest` | 1,332 | 0 | **14** | 0.271 |
| `current_breaker_re_entry` | 4,219 | 0 | **14** | 0.270 |
| `cross_asset_lead_lag` | 2,055 | 0 | **14** | 0.327 |
| `structural_distance_extreme` | 1,968 | 2 | **12** | 0.549 |
| `liquidity_sweep_reclaim` | 4,451 | 5 | **9** | 0.789 |
| `regime_transition_break` | 297 | 8 | **6** | 0.819 |
| `displacement_continuation` | 4,445 | 9 | **5** | 0.885 |
| `volatility_compression_expansion` | 605 | 9 | **5** | 0.874 |
| `session_open_range_break` | 987 | 11 | **3** | 0.966 |

Pooled: **mean 10.65 minutes early, median 14** (x1-C, n=27,074). The three `current_*`
zone families are the extreme case — their entry price is the midpoint of a POI zone built
from bars that closed **before** the decision bar started, so it is knowable at minute 0 on
essentially every row, and for `current_ob_retest` / `current_breaker_re_entry` the zone is
an **H1** object (`:1384`, `:1439`), older still. Their setups persist:
`current_fvg_fill` re-emits the **same** setup a mean of **15.49 times**, max **140**, and
**91.88 % of its rows sit on a repeated setup** (x1-C; `candidate_id` hashes `poi_id` and
`entry`, so a repeat is a bit-identical entry price re-offered 15 minutes later).

---

## Q4 — the live path on the 14 of 15 wakes where no bar closed

**It manages open positions and it does not decide. Plainly: no signal generation, no
candidate evaluation, no order placement.**

`launcher.py` `tick()`, in order:

| line | what runs every 60 s |
|---|---|
| `:268` | heartbeat write |
| `:269-273` | kill/halt read + brake-transition alert |
| `:278-311` | MT5 connection + broker-link health, reconnect, outage alert |
| **`:314`** | **`self.owner.manage_open_positions(now_utc=now)` — exits, adoptions, TP/SL moves, scale-outs, time stops. Halt-independent.** |
| `:318-324` | `for tf in self._tf_tags:` compare `_latest_closed_bar_iso(tf)` to `_last_bar_by_tf[tf]` |
| **`:325-327`** | **`if not advanced: return {"action": "no_new_bar", ...}`** |
| `:329` | `self.owner.run_cycle(now_utc, tags, place)` — *only* reached when a bar advanced |

`run_forever` is `tick(); sleep(self.poll_seconds)` (`:359-368`), `--poll-seconds` default
`60.0` (`run_book.py:99`, passed at `:681`).

**Priced against the armed book:** the three armed sleeves — `crypto`, `energy_agri`,
`sub_xvol_pullback` — all resolve `timeframe = 16388` (H4). So the live FTMO book wakes
**240 times per entry decision and generates on 1 of them: 0.417 % of its wakes.** For the
ten M15 specs in the registry it is 1 in 15 (6.67 %); for the D1 spec 1 in 1,440. The
machine is not slow. It is idle by design, and the design is `if not advanced: return`.

---

## Q5 — decision-to-fill latency, separated from the bar-close effect

### A precision correction that reaches every prior finding built on `bars_to_entry_touch`

**An M1 bar exists at exactly `decision_time_utc` on 27,036 of 27,658 rows (97.75 %), and
the sidecar's path starts at `decision_time + 1 min` on 97.77 %.** The first minute of live
exposure is therefore **dropped from every path in the substrate**, and
`bars_to_entry_touch == 1` denotes the minute beginning **60 s after** the decision, i.e.
first touch within **120 seconds**, not 60. The claim "55.65 % of candidates have their
entry price touched within 60 SECONDS" should read *within two minutes*; the first minute
itself has never been measured.

Measured cost of that dropped minute: walking the identical trade with the path starting at
`T` instead of `T+1min` moves the pooled result from −0.055648 to −0.058788 R/trade
(n = 11,767) — **the dropped minute is itself adversely selected, by −0.00314 R/trade.**

### The latency distribution the pool implies (x1-C, n as shown)

| cohort | n | never touched | touched in path bar 1 | within 5 min | median min | mean min |
|---|---:|---:|---:|---:|---:|---:|
| close-entry families (7) | 14,909 | 1.54 % | **75.83 %** | 87.96 % | 1 | 3.87 |
| zone families (3) | 12,749 | 0.09 % | 44.28 % | 50.11 % | 5 | 25.00 |
| `current_breaker_re_entry` | 4,263 | 0.05 % | 86.91 % | 88.25 % | 1 | 6.46 |
| `current_fvg_fill` | 7,146 | 0.08 % | 24.04 % | 32.83 % | 19 | 32.05 |
| `current_ob_retest` | 1,340 | 0.22 % | 16.57 % | 20.90 % | 43 | 46.43 |

**Separating the bar-close effect: there is essentially no latency to separate.** For the
53.90 % of the pool where `entry = bar.close`, the entry price *is* the last print of the
15-minute window, so a touch in the next minute is not a fill event — it is the same price
still being there. The genuine wait is the zone families', and it is a property of a
resting limit at a POI midpoint, not of any system delay. The system's own latency to act
is **zero minutes and 15 minutes at once**: zero from bar close to order, fifteen from the
moment the market made the move to the moment the system was allowed to see it.

---

## DISCOVERY — what earliness is actually worth

All arms below use the **same M1 source**, the **w0 tie rule** (stop wins inside a bar), and
the **same 2R target**. Where an arm preserves the original risk distance `d0` the pool's
own `cost_r` applies unchanged, so the comparison is net-honest.

**Walker validation.** ARM A (as-ran: entry at the M15 close, generator's stop and target,
path `T+1min .. T+120min`) reproduces the shipped `plain_walk_r`:
mean **−0.055648 vs −0.055543**, mean absolute difference **0.000114 R**, 99.99 % of rows
within 0.01 R, **100.00 % sign match**, n = 11,767.

### F1 — acting at the confirm minute is worth +0.155 R/trade, causally, today

Five families whose predicate is exactly reproducible from closed M15 bars, n = 11,713
paired (54 side-flips and 72 missing decision bars excluded). k\* = the first minute of the
decision bar at which the predicate is true using bars `0..k` only — no look-ahead.

| arm | pooled | excl `structural_distance_extreme` |
|---|---:|---:|
| **A** — as ran (entry at bar close) | **−0.05591** | −0.05213 |
| **E1** — entry at k\*, generator's stop/target prices, R in `d0` | +0.07629 | — |
| **E2** — entry at k\*, running geometry at k\*, R in its own risk | **+0.09141** | **+0.21822** |
| **E3** — entry at k\*, **`d0` preserved** (cost identical to A) | +0.00125 | **+0.10311** |
| Δ E2 − A | **+0.14732** (t 12.86, **21/21 days**) | +0.27035 (t 31.0, 21/21) |
| Δ E3 − A | **+0.05716** (t 5.58, **20/21 days**) | **+0.15524** (t 20.6, **21/21 days**) |

Mechanism, not noise: A exits `5,745 stop / 2,088 target / 3,880 path-end`; E2 exits
`5,773 stop / 3,063 target / 2,877 path-end`. **E2 hits target 46.7 % more often at the same
stop count** — the extra targets come out of the path-end bucket. Win rate A 38.05 % →
E3 41.27 %. E2's risk distance is 0.827× `d0` (median 0.860) because the bar's extreme has
not finished printing; that is why E2 > E3 gross and why E3 is the arm that survives cost
(net A −0.5914 → net E3 −0.5343, same +0.0572).

### F2 — the control refutes the obvious story: the confirm minute carries no information

Placebo arms P0/P3/P7/P11 use the **identical E3 geometry entered at a fixed minute,
ignoring the predicate**.

| arm | pooled | excl structural |
|---|---:|---:|
| P0 (minute 0) | +0.08204 | +0.24897 |
| P3 | +0.05702 | +0.21484 |
| **P7** | **+0.00123** | +0.13343 |
| P11 | −0.06575 | +0.02592 |
| **E3 (confirm minute, median k\* = 7)** | **+0.00125** | +0.10311 |
| **Δ E3 − P7** | **−0.00004 (t −0.03)** | −0.03024 (t −2.91) |

**E3 equals P7 to four decimal places.** An arm that does not know the setup will fire
matches the arm that waited for it to fire. The gain is not the signal turning true — it is
**the minute of the clock**. That is a refutation of my own first reading and it is the
more useful result: it says the defect is the *entry anchor*, not the *detection lag*.

### F3 — the entry-anchor time curve, and where the money is

Fixed-minute arms across a 30-minute window (m < 0 = the previous M15 bar), `d0` preserved,
both horizon conventions computed (same-end-time and equal-120-minute-duration; they agree
to ≤0.003 R, so extra holding time is not the driver). Table shows equal-duration.

| minute m | ALL close-entry (7 fam, n≈14,700) | **CONTINUATION 5 (n≈8,300)** | excl structural (6 fam) |
|---:|---:|---:|---:|
| −15 | +0.10708 (t 6.9, 20/21) | **+0.66689 (t 34.5, 21/21)** | +0.22691 (t 14.7, 21/21) |
| −10 | +0.09314 | +0.58018 | +0.21523 |
| −5 | +0.07495 | +0.48526 | +0.20090 |
| −1 | +0.07423 | +0.38825 | +0.20300 |
| 0 | +0.06914 | +0.34140 | +0.19531 |
| +3 | +0.04157 | +0.23291 | +0.15989 |
| +5 | +0.01324 | +0.15443 | +0.12178 |
| +7 | −0.00976 | +0.09655 | +0.08987 |
| +11 | −0.06188 | −0.01962 | +0.00714 |
| +14 ≈ the close | −0.06281 | **−0.07755 (2/21 days)** | −0.05829 |
| **A as ran** | **−0.05909** | **−0.07714** | −0.05671 |
| **peak − as-ran** | **+0.16617** | **+0.74403** | +0.28362 |

CONTINUATION 5 = `displacement_continuation`, `regime_transition_break`,
`volatility_compression_expansion`, `session_open_range_break`, `cross_asset_lead_lag`.
The decay is monotone over the full 29 minutes at **≈0.0257 R/trade per minute**, and
**0.0299 R/trade per minute** over the decision bar itself (m0 → m14).

### F4 — per family, the sign is not the same, and the reason is legible

| family | n | m−15 | m−5 | m0 | m+7 | m+14 | as ran | shape |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `cross_asset_lead_lag` | 2,083 | **+0.9668** | +0.2258 | −0.1343 | −0.1374 | −0.0782 | −0.0746 | edge fully consumed before the bar even opens |
| `displacement_continuation` | 4,445 | +0.6332 | **+0.6630** | +0.5853 | +0.2034 | −0.0808 | −0.0834 | flat-topped, then collapses |
| `regime_transition_break` | 297 | **+0.5207** | +0.5008 | +0.4446 | +0.2103 | −0.0103 | −0.0035 | monotone decay |
| `session_open_range_break` | 987 | **+0.4698** | +0.3750 | +0.3105 | +0.1022 | −0.0712 | −0.0673 | monotone decay |
| `volatility_compression_expansion` | 605 | **+0.2952** | +0.2461 | +0.1884 | +0.0386 | −0.0952 | −0.0918 | monotone decay |
| `liquidity_sweep_reclaim` | 4,451 | −0.5963 | −0.3354 | −0.0795 | **+0.0772** | −0.0220 | −0.0181 | **inverted U, peak mid-bar** |
| `structural_distance_extreme` | 1,969 | −0.6684 | −0.7442 | −0.7497 | −0.6609 | **−0.0925** | −0.0746 | **rises toward the close** |

* **`cross_asset_lead_lag` is the sharpest indictment in the pool.** Its premise is an
  explicit 15-minute lead (`previous_leader_time = latest_lag.time - timedelta(minutes=15)`,
  `broader_origin_generators.py:988`) and its admission gate is *"the lag has NOT responded
  yet"* (`if leader_impulse < 1.0 or lag_response > 0.5: continue`, `:1023`). Entering at
  the leader's own bar is worth
  **+0.9668 R/trade**; by the time the lag bar opens it is **−0.1343**. The family spends
  its entire declared edge waiting for a bar boundary it does not need.
* **The two families that do NOT want earliness are the two whose only confirmation is the
  close.** `structural_distance_extreme` fires when `pos50 >= 0.97` — the instant price
  reaches the extreme — and the bar close is doing real work as a *persistence filter*:
  it only fires if price is still at the extreme fifteen minutes later. Acting at the touch
  means selling into a move still running (win rate 31.3 % → 17.0 % at E3). It is also
  untradeable at any anchor: **mean `cost_r` 1.2290 R/trade**, against a pool mean of
  0.5341 (median 0.2355). `liquidity_sweep_reclaim` needs its sweep to have happened, so it
  peaks mid-bar (+0.0772 at m+7) and is negative before the sweep.

### F5 — a retrospective limit does NOT harvest it

Resting limit at the decision bar's own open price, live from the decision to +120 min,
unfilled books 0.0: **LOPEN = +0.00339 R/trade** on the five-family set (fill rate 61.43 %,
median fill minute 17, **net on fills −0.5258**); LMID = +0.02200. On the other two
close-entry families both are negative. **The value is in deciding earlier, not in pricing
earlier** — a limit back at the good price only fills when the move has failed.

### F6 — the ceiling, stated honestly

Mean `cost_r` on the five-family set is **0.5341 R/trade** (median 0.2355), dominated by
`structural_distance_extreme` at 1.2290 and `liquidity_sweep_reclaim` at 0.5616.
**No anchor timing makes this pool profitable**: the best measured arm on the whole
close-entry set is +0.107 R/trade gross against that cost. The source itself names the
cause — *"the measured 0.25xATR(M15) stops put routine M1 noise and ~0.17R costs above the
realizable exit edge"* (`broader_origin_generators.py:421-429`, the `stop_width_scale`
docstring). Earliness and stop geometry are two different repairs and the pool needs both.
The arm ranking is unaffected by cost because every arm carries the identical `d0` and
therefore the identical `cost_r`.

---

## Caveats

1. **One month, one arm.** January 2026, S0R0, true-UTC. No out-of-window test; F1–F6
   travel is a later stage's job. Day-clustered t-statistics over 21 trading days are
   reported everywhere, and the day-positive counts are the honest robustness statement.
2. **Multiplicity is not corrected and the brief says not to self-censor.** F3/F4 sweep 30
   entry minutes × 7 families. F1's E3 arm was pre-specified from the source predicates, not
   selected from a grid; F2's placebo was run *because* F1 looked too good.
3. **m < 0 arms are not contracts.** At minute −1 the system does not know the setup will
   fire. They measure where the price advantage sits; they are the prize for a leading
   indicator, not a strategy. The implementable slice is F1's +0.155 R/trade
   (excl-structural, E3, 21/21 days).
4. **Pseudo-replication.** The five reproducible families are 98.5 % first-emission
   (`current_fvg_fill`'s 91.9 %-repeated problem does not touch them), so the F1/F3 samples
   are close to independent setups. The zone families are not, and no zone-family economics
   are claimed here.
5. **Horizon.** Every path is capped at 120 M1 bars. Nothing here speaks to holding beyond
   two hours.
6. **Cost scaling.** Only arms that preserve `d0` (A, A1, E3, P\*, LOPEN, LMID) are
   cost-honest. E1/E2 change the risk distance; their cost-adjusted figures were computed by
   scaling `cost_r` by `d0/d_new` and that scaling is an approximation for a
   price-denominated cost — treat E2's net as indicative and E3's as measured.

---

## Artifacts (all under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`)

| file | what |
|---|---|
| `x1_RESULT.md` / `x1_RESULT.json` | this receipt |
| `x1_intrabar.py` → `x1_INTRABAR_ROWS_V1.jsonl.gz`, `x1_INTRABAR_BUILD_V1.json` | 27,658-row intrabar reconstruction: range-printed-by-minute, minute of high/low, first-tradeable minute, stop/target already hit inside the decision bar, M1-vs-M15 exactness check |
| `x1_d_early_walk.py` → `x1_D_EARLYWALK_V1.json`, `x1_D_EARLYWALK_ROWS_V1.jsonl.gz` | confirm-minute k\*, arms A/A1/E1/E2/E2h |
| `x1_e_validate_e3.py` → `x1_E_E3_V1.json`, `x1_E_E3_ROWS_V1.jsonl.gz` | walker validation vs shipped `plain_walk_r`; arm E3; per-family and per-day |
| `x1_f_placebo.py` → `x1_F_PLACEBO_V1.json` | the placebo control (P0/P3/P7/P11) with day-clustered t |
| `x1_g_anchor_curve.py` → `x1_G_ANCHOR_CURVE_V1.json`, `x1_G_ANCHOR_ROWS_V1.jsonl.gz` | 30-minute entry-anchor curve, both horizon conventions, LOPEN/LMID limits, five families |
| `x1_H_ANCHOR2_CURVE_V1.json`, `x1_H_ANCHOR2_ROWS_V1.jsonl.gz`, `x1_H_SEED_V1.jsonl.gz` | same curve for `cross_asset_lead_lag` + `session_open_range_break` |
| `x1_I_COMBINED_CURVE_V1.json` | pooled curve over all seven close-entry families and the CONTINUATION-5 cut |
| `x1_A_ANCHOR_V1.json`, `x1_B_STALENESS_V1.json`, `x1_C_PRICE_V1.json` (+ their scripts) | the earlier x1 attempt's receipts, cited above as x1-A/B/C |
