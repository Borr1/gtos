# Why the signals take so long — and what going early is worth

**For Borhen. 2026-08-06. Wave 19, the earliness swarm: six lanes (x1–x6), January 2026,
all 27,658 candidates measured, nothing sampled.**

You asked:

> *"is market state being got at all times each second and the system is running literally
> every second or what's taking so long for the signals to come, can't we go early exactly
> when the signal tells us?"*

---

## THE ANSWER, IN SIX LINES

**The machine is not slow. It wakes every 60 seconds and it already does a full broker-facing
pass on every wake.** What it does *not* do is think. One line of code
(`launcher.py:323`) says: if no bar has closed since last time, return and do nothing.
On an H4 sleeve — which is what the core of your armed book is — that means **the book
generates entries on 1 of every 240 wakes: 0.417 % of the time.** [x1 Q4]

**The delay is not latency. It is that the system is only allowed to look at *finished* bars.**
By the time a 15-minute bar closes, the move it describes is over: **28.6 % of that bar's
range printed in its first minute and 75.9 % by minute 7.** [x1 Q3, 27,239 bars rebuilt from
the minute data, zero reconstruction error]

**The setup was almost always already true.** Of the 27,108 January decisions whose defining
condition can be located in time, **96.69 % were already true before the instant the system
made them — median 14 minutes early.** [x2 headline]

**Yes, you can go early, and it is worth a lot on paper — but a large majority of that
number is not reachable by moving an order.** Measured three separate ways on three
populations, entering at the start of the trigger bar instead of its close is worth
**+0.14 to +0.74 R/trade**. An exact mirror test says **82.5 % of it is the trigger bar's
own move** — which is *the reason the candidate exists*. You cannot have that part without a
generator that fires on a half-finished bar, and when we built one and ran it over every
January bar, it fired on **three to six times too many** setups. [x5 §0, x3 §4b]

**The genuinely reachable pieces are smaller and they are real.** The side-free part of
earliness is **+0.065 R/trade**. And a new discriminator turned up: **the single minute
*after* the decision separates good from bad more than twice as well as anything the estate
has ever measured** — Cohen's d 0.335, AUC 0.591 against a standing ceiling of 0.152. It
refuses 29.8 % of the pool that books **−0.665 R each**. [x5 §0, x4 §0/§5]

**And the honest ceiling: none of this makes this research pool profitable.** Cost is
larger than every timing lever combined. The best honest, fill-realistic construction in the
whole swarm is **statistically indistinguishable from flat**, not positive. [x5 §2.1]

---

## Terms, explained once

| Term | Meaning here |
|---|---|
| **R** | One risk unit. If the stop is 40 points away, 1 R = 40 points. "+2 R" = the trade made twice what it risked. |
| **bps** | Basis point = 0.01 % of the instrument's price. |
| **M15 / M1 / H4** | 15-minute / 1-minute / 4-hour bars. |
| **The pool** | The 27,658 candidates the research selector considered in January 2026. It is a diagnostic set — none of these were live trades. |
| **Decision bar** | The M15 bar that *closes* at the moment of the decision. Verified exactly: the entry price equals that bar's close on 14,809 of 14,809 rows, zero error. |
| **The close-entry families** | 7 of 10 setup families whose entry price literally *is* `bar.close`. 14,909 rows, 53.9 % of the pool. |
| **The zone families** | The other 3 (`current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry`). Their entry is the midpoint of a pre-existing price zone, so "earliness" means something different for them. |
| **Gross / net** | Before / after broker cost (spread + commission + slippage + swap). |
| **Cohen's d** | How far apart two groups are, in standard deviations. Below 0.1 is not worth naming; 0.2 is small; the estate's best-ever field was 0.152. |
| **AUC** | How well a score ranks winners above losers. 0.50 = a coin flip. |
| **Day-block bootstrap** | Robustness test that resamples whole trading days, so one lucky day cannot carry a result. `p(≤0) = 0.000` means the effect was positive in essentially every resample. |
| **Look-ahead** | Using information that did not exist yet. Flagged everywhere below — some of the biggest numbers in this report are look-ahead and are labelled as an *upper bound on the prize*, not a strategy. |

**Scope, stated up front.** Everything here is the **broad V4 research pool**, January 2026.
It is not your live book. `crypto`, `energy_agri`, `sub_xvol_pullback` and `mx_btcusd` on
FTMO, and the four core sleeves on redacted_account, are a different family on H4 and D1 with
holding horizons up to 320 hours; this pool's entire measurement window is 2 hours — 160×
shorter. **Nothing in this report is a
reason to touch either armed account today.** Two findings reach the live code and are
flagged in Part 5.

---

# PART 1 — Why it takes so long

## 1.1 The machine already runs faster than it decides

| what runs on a wake with no new bar | file:line | runs? |
|---|---|---|
| heartbeat write | `launcher.py:268` | yes |
| kill / halt flag read | `launcher.py:269-272` | yes |
| broker connection health, reconnect | `launcher.py:282-309` | yes |
| **manage open positions** — exits, TP/SL moves, scale-outs, time stops, off the live tick | `launcher.py:314` | **yes, every 60 s** |
| check whether a bar closed | `launcher.py:319-324` | yes |
| **generate / admit / size / place** | `launcher.py:329` | **NO** |

The gate is one line, `launcher.py:323`. No bar advance → `return {"action": "no_new_bar"}`.

`--poll-seconds` defaults to **60.0** (`run_book.py:99`) and the live supervisor passes
`"60"` explicitly for both accounts (`run_book_supervisor.ps1:109`).

| sleeve timeframe | wakes per entry decision | share of wakes that decide |
|---|---:|---:|
| **H4 — the core of the armed book** (`crypto`, `energy_agri`, `sub_xvol_pullback`) | **240** | **0.417 %** |
| M15 — the 10 M15 specs in the registry | 15 | 6.67 % |
| D1 — the 1 D1 spec | 1,440 | 0.069 % |

(Measured on the registry as it resolves on this worktree. The armed `--tags` set on the host
has changed since — `mx_btcusd` was added on FTMO 2026-07-31 — but the H4 row is the one that
governs the sleeves generating most of your entries, and the arithmetic is per timeframe, not
per sleeve count.)

**The machine is idle by design, not by weakness.** [x1 Q4, x6 §1]

## 1.2 The bar is over before the system is allowed to look

Every one of the 27,239 January decision bars was rebuilt from its own 15 one-minute bars.
The reconstruction reproduces the 15-minute file's high, low and close with **maximum
relative error 0.000000**. So this is measurement, not modelling.

**Mean share of the decision bar's final range already printed, by minute:**

| minute | 0 | 1 | 3 | 5 | **7** | 9 | 11 | 13 | 14 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| share of final range printed | **0.286** | 0.400 | 0.549 | 0.665 | **0.759** | 0.833 | 0.906 | 0.971 | 1.000 |

Median minute of the bar's high: **6**. Of its low: **5**.

Two consequences that price the whole convention:

| | share of the pool |
|---|---:|
| **take-profit level already reached inside the trade's own decision bar** | **19.90 %** |
| **stop level already traded through inside the trade's own decision bar** | **13.29 %** |
| best price available inside the decision bar, in the trade's own direction, vs the entry used | median **0.6034 R** better, mean **1.2831 R** better |

One in five setups had already completed its intended 2R move before the system was
permitted to look at it. One in eight was already dead at birth. [x1 Q3]

## 1.3 M15 is a choice, not architecture — and the minute data is already in the room

Four literals and two hardcoded `15`s produce the entire 15-minute convention:

| site | what it does |
|---|---|
| `data_ingestion.py:55` | `TIMEFRAMES = ("D1","H4","H1","M15")` — the fetch set, shared by replay and live |
| `market_state.py:1352` | `for tf in ("D1","H4","H1","M15")` in the market-state builder |
| `v4_timewarp:315` | `PRIMARY_DECISION_TIMEFRAMES` — the 4-tuple handed to the decision function |
| `broader_origin_generators.py:293` | `timeframe="M15"` — **the single line that makes every pool row M15** |
| `v4_timewarp:58993` | `row_time + timedelta(minutes=15)` — the replay decision grid |
| `broader_origin_generators.py:988` | `previous_leader_time = latest_lag.time − timedelta(minutes=15)` — the cross-asset lead offset |

**And the part worth pausing on: the one-minute data is already resolved and sitting in the
replay process at every single decision, and is deliberately withheld from the decision
function by name.**

`PRIMARY_SOURCE_TIMEFRAMES` (`v4_timewarp:316`) **includes M1**. `PRIMARY_DECISION_TIMEFRAMES`
(`:315`) omits it. Every decision stamps its own metadata recording the omission:
`post_decision_path_timeframes_available_but_not_attached`,
`m1_or_tick_attached_to_decision: False`, and a reason string
`"replay_source_separation_predecision_uses_d1_h4_h1_m15_closed_bars_only"`.

The source states the doctrine outright at `data_ingestion.py:190-206`: *"The live MT5 rate
buffer can expose the in-progress bar immediately after a close. That bar is not valid
production market-state evidence."* That was a deliberate correctness decision — and it is
also the thing this report is about. [x1 Q2]

**The live book is already multi-timeframe**: `book_engine.py` carries `_TF_MINUTES = {1:1,
5:5, 15:15, 30:30, 16385:60, 16388:240, 16408:1440}` and the launcher's own comment names
M1 as an active decision timeframe. One sleeve (`vp_euidx_pocgrav`) already pulls **20,000
M1 bars every cycle on the live terminal** (`registry.py:58`, `book_engine.py:626-628`).

---

# PART 2 — What the system could have seen earlier

Every one of the ten setup families' conditions was transcribed from source with line
numbers and then re-evaluated minute by minute over the January data. The reconstruction is
exact: **recall 1.0000 and 100 % side match** against the pool.

## 2.1 How early each family was already true

`earliness` = minutes between the first minute the condition was true and the moment the
system acted. A 60-second poller — which is what you already run — would have seen it then.

| family | n | fired at **minute 1** | median earliness | genuinely needs the last minute |
|---|---:|---:|---:|---:|
| `cross_asset_lead_lag` | 2,055 | **94.70 %** | **14 min** | 0.15 % |
| `structural_distance_extreme` | 1,969 | 35.80 % | **12 min** | 5.8 % |
| `session_open_range_break` | 987 | 20.77 % | **10 min** | 4.6 % |
| `liquidity_sweep_reclaim` | 4,451 | 14.13 % | **9 min** | 4.7 % |
| `regime_transition_break` | 297 | 5.39 % | 6 min | 13.5 % |
| `volatility_compression_expansion` | 605 | 3.47 % | 5 min | 9.9 % |
| `displacement_continuation` | 4,445 | 3.58 % | 5 min | 9.4 % |

**Only 4.6–13.5 % of decisions in any family genuinely require the final minute of the bar.**

Pooled: **96.69 % were already true before the decision instant; 84.57 % at least 5 minutes
early.** For the 15,704 whose condition lives inside the decision bar, median earliness is
**9 minutes** — the system waits, on average, **8.60 minutes after it could already have
known**. [x2 §2]

## 2.2 The three zone families are not "minutes" early at all

Their setup is a pre-existing object, not an event:

| family | n | zone already valid at minute 1 | how long the setup had existed |
|---|---:|---:|---|
| `current_fvg_fill` | 6,794 | **99.04 %** | median **135 minutes** before the decision bar even opened (p90 968 min) |
| `current_ob_retest` | 1,326 | 97.81 % | median 3,485 min continuous proximity |
| `current_breaker_re_entry` | 4,179 | 98.92 % | median 4,320 min (≥ 3 days for half of them) |

And one finding that follows straight from it: **40.59 % of `current_fvg_fill` entry levels
had already been traded inside their own detectable window — a median 61 minutes before the
decision** — while the zone was still formally "unfilled", because the code marks an FVG
filled only when price reaches its *far* boundary while the entry sits at the *midpoint*
(`market_state.py:851, :866`). **The system arrives at a price the market already visited,
on average an hour late.** [x2 §2, §5c]

## 2.3 Only three things in the whole estate genuinely need a finished bar

1. **`displacement_continuation`'s body test — and its SIDE.** `sign(close − open)` does not
   exist until the bar closes. This is the one family whose *identity* is a bar-close property.
2. **`liquidity_sweep_reclaim`'s reclaim leg** — "closed back inside" is a statement about
   where the bar finishes.
3. **`cross_asset_lead_lag`'s quietness leg** — "the lagging instrument has not responded"
   is a claim about the whole bar.

Everything else is either a constant known before the bar opened, or a level test that is
true the instant price does it.

**The price of acting without waiting for the close** — measured over all January bars, not
just pool rows:

| family | bars firing early | still true at the close | same side |
|---|---:|---:|---:|
| `displacement_continuation` | 6,237 | **83.05 %** | 81.98 % |
| `volatility_compression_expansion` | 946 | 76.74 % | 76.53 % |
| `regime_transition_break` | 513 | 66.67 % | 66.67 % |
| `liquidity_sweep_reclaim` | 8,602 | 63.80 % | 63.80 % |
| `session_open_range_break` | 1,636 | 62.71 % | 61.37 % |
| `cross_asset_lead_lag` | 5,294 | 52.49 % | 52.49 % |
| `structural_distance_extreme` | 8,482 | **35.22 %** | 35.22 % |

That column is the false-positive rate of going early, per family, and it is the whole
argument in Part 3.4. [x2 §3]

## 2.4 The single most legible defect in the pool

**`cross_asset_lead_lag` spends its entire declared edge waiting for a bar boundary it does
not need.**

Its premise is an explicit 15-minute lead — the code literally reads
`previous_leader_time = latest_lag.time − timedelta(minutes=15)`
(`broader_origin_generators.py:988`) — and its admission gate is *"the lagging instrument
has NOT responded yet"* (`if leader_impulse < 1.0 or lag_response > 0.5: continue`, `:1023`).
The leader's bar closes exactly when the lagging instrument's bar *opens*. So the entire
signal is complete before the decision bar starts, and the system then waits 15 minutes for
that bar to finish.

| entry point | R/trade |
|---|---:|
| at the leader's own bar (15 min early) | **+0.9668** |
| 10 min early | +0.6204 |
| 5 min early | +0.2258 |
| **when the lag bar OPENS** | **−0.1343** |
| as the system actually ran | −0.0746 |

By the time the lagging bar even opens, the trade is already negative. [x1 F4]

---

# PART 3 — What earliness is worth

Three lanes measured this independently, on three different populations, with three
different contracts. **They agree on the shape and differ on magnitude exactly as the
population differs.** All three are reported, because the spread between them is itself the
honest answer.

## 3.1 The curve — and it is a V with its vertex at the close

Whole pool with complete minute data, structural stop held fixed, identical 120-bar holding
period, **n = 26,316 at every single rung**:

```
minute:  -14   -12    -9    -6    -3    -1     0    +1    +3    +6    +9   +15   +30   +60
R/trade +.179 +.118 +.037 -.048 -.127 -.174 -.191 -.170 -.147 -.128 -.115 -.115 -.088 -.055
                                                 ^^^^ the worst minute in the whole window
```

**The M15 close is the single worst instant to enter in the entire 44-minute window around
it.** Every minute earlier and every minute later is better, monotonically, on both sides.

Paired day-block bootstrap versus the incumbent (same rows both arms, 2,000 day-resamples):
acting at minute 1 of the trigger bar instead of at its close is **+0.3702 R/trade
[+0.3482, +0.3914], p(≤0) = 0.0000**. All 34 non-reference rungs are significant at
p(≤0) = 0.0000. [x5 §0]

A second lane found the same V independently on the at-market cohort, and its floor is one
minute *before* the close:

| | k = −15 (bar open) | k = −1 | **k = 0 (shipped)** | k = +5 |
|---|---:|---:|---:|---:|
| gross R/trade | **+0.07904** | −0.08261 | **−0.06184** | −0.00504 |
| win rate | 0.4484 | 0.3713 | 0.3750 | 0.3964 |
| **stop rate** | **0.4736** | 0.5158 | 0.5089 | 0.4830 |
| target rate | 0.1986 | 0.1746 | 0.1835 | 0.1977 |

Earliness is not buying a better price at the cost of more stop-outs. **It buys both** —
the stop rate falls 3.5 points and the target rate rises 1.5. [x3 §1]

**And this unifies the two findings that looked contradictory.** "Wait 5 minutes, it's worth
+0.067" is the small right-hand hump (this lane reproduces it independently at +0.0568).
"Go early" is the left-hand climb, **2.48× larger**. Both are true. They are two points on
one curve whose floor is the moment the system transacts.

## 3.2 Three measurements, one shape

| lane | population | n | at the close | earliest measured | **gap** |
|---|---|---:|---:|---:|---:|
| **x1** | 5 continuation families, risk distance held fixed | 8,417 | −0.0771 | **+0.6669** (1 bar early) | **+0.7440** |
| **x5** | whole pool, structural stop, equal 120-bar hold | 26,316 | −0.1910 | +0.1792 (min −14) | **+0.3702** |
| **x3** | 5 early families, **net of broker-true cost** | 10,034 | −0.2075 | **+0.1183** | **+0.3258** |
| **x3** | at-market cohort, all 7 close-entry families | 13,692 | −0.0618 | +0.0790 | **+0.1409** |
| **x2** | 7 close-entry families, entry moved to the **actual first-detect minute**, stop/target levels held fixed | 14,809 | −0.0593 | −0.0039 | **+0.0554** |

Read the last row as the conservative floor: it uses each candidate's *real* first-detectable
minute (median 5–9 for the continuation families) rather than the start of the bar, and holds
the exit levels where they were. It still moves the seven close-entry families almost exactly
to zero.

Read the first row as the ceiling of the prize. It is **look-ahead** — at minute −15 the
system does not yet know the setup will fire.

**x1's day-by-day robustness on the continuation set: 21 of 21 trading days positive,
day-clustered t = 34.5.** The decay is monotone across the whole 30-minute window at
**≈0.026 R/trade per minute of waiting.**

**x3's instrument robustness: 24 of 24 instruments improve. Zero reversals.** Largest
BTCUSD +0.2862, ETHUSD +0.2653, UK100 +0.2381; smallest USDJPY +0.0063.

## 3.3 Who gains and who is destroyed — do NOT apply one rule to all families

Net of broker-true cost. `k*` is each family's own best entry offset in minutes from the
close (negative = inside the forming bar).

| family | n | net R at bar open | net R at the close | **k\*** | lift vs the close | 95 % CI |
|---|---:|---:|---:|---:|---:|---|
| **displacement_continuation** | 4,165 | **+0.5452** | −0.1877 | **−15** | **+0.7329** | [+0.7111, +0.7553] |
| **regime_transition_break** | 281 | **+0.4411** | −0.0385 | **−15** | **+0.4796** | [+0.4396, +0.5211] |
| **session_open_range_break** | 986 | **+0.2689** | −0.1631 | **−15** | **+0.4319** | [+0.3910, +0.4708] |
| **volatility_compression_expansion** | 509 | **+0.1456** | −0.1440 | **−15** | **+0.2896** | [+0.2663, +0.3127] |
| liquidity_sweep_reclaim | 4,093 | −0.3780 | −0.2580 | **−5** | +0.1153 | [+0.0805, +0.1505] |
| structural_distance_extreme | 1,765 | **−1.2685** | −0.5970 | **+5** | +0.2034 | [+0.1317, +0.2755] |
| cross_asset_lead_lag | 1,890 | −0.4409 | −0.3598 | +15 | +0.1190 | [+0.0487, +0.1778] |

**Four families want the bar's open. Two want to be later. One wants the middle.**

The exceptions have legible mechanisms, which is why they are believable rather than noise:

- **`structural_distance_extreme` is destroyed by earliness** — it loses 0.67 R/trade *more*
  at the open than at the close. It fires the instant price reaches an extreme, and the bar
  close is doing real work as a *persistence filter*: it only fires if price is *still* at the
  extreme fifteen minutes later. Acting at the touch means selling into a move still running
  — win rate falls 31.3 % → 17.0 %. Separately measured: waiting **improves** its entry price
  by **1.087 R**.
- **`liquidity_sweep_reclaim` has an interior optimum at −5 minutes**, which is exactly what a
  sweep-then-reclaim mechanism should do: the sweep has to happen first. It is the family that
  hands back the most by waiting — **+0.2566 R of entry price given up per trade**, against a
  family loss of only 0.040 R. The wait is six times the size of the loss.

**Earliness is not one lever. It is at least two, with opposite signs, and the family is the
switch.** [x3 §2, x2 §4, x1 F4]

The five early families entered at the bar's open form the **first net-positive book this
substrate has produced**: **+0.1183 R/trade, +10.24 bps, +1,186.7 R for January**, day-block
CI [+0.0873, +0.1511], p(≤0) = 0.000 over 27 days. **And its positive window closes at
minute 8 of the bar** — net-positive offsets are exactly k ∈ {−15, −13, −11, −10, −9, −8};
k = −7 is already −0.0201. **You must fire in the first 7 minutes or the prize is gone.**

## 3.4 The honest bill — three charges, all measured

### Charge 1: trades that die before the signal exists — already paid

Entering at the bar's open, **22.41 % of trades are stopped out before the M15 close** and
1.25 % hit target: **23.66 % of the population is fully resolved before the signal that
justified it even exists.** Every number in §3.1–3.3 is already net of this. [x3 §4a]

### Charge 2: 82.5 % of the prize is the trigger bar's own move — and it is unreachable by moving an order

This is the most important number in the report, so here is the test in full.

Take the same candidate, same entry price, same risk distance — but flip the side and reflect
the stop through the entry. That is an **exact mirror**. If earliness were just "the market
drifts and you catch it", the mirror would gain too. If earliness is "the bar has already
moved your way, which is *why* the setup exists", the mirror loses by the same amount.

| | value |
|---|---:|
| total earliness gain (minute −14 vs the close) | **+0.37022** |
| of which **side-free drift** (the mirror gains it too — reachable) | **+0.06474** |
| of which **directional** (the trigger bar's own move — the reason the candidate exists) | **+0.30548** |
| **directional share** | **82.51 %** |

**Capturing the directional part requires a generator that emits on a partial bar. It cannot
be had by moving an order.** The side-free residue — **+0.065 R/trade** — is what you can get
by changing when you place. [x5 §0]

The same lane measured *where* the direction lives, minute by minute. `info < 0` means the
signal's own side is right:

| minute of the trigger bar | −14 | −10 | −9 | **−8** | −6 | −4 | **−1** | 0 (close) | +2 | +15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| info | **−.0874** | −.0305 | −.0143 | **+.0057** | +.0368 | +.0703 | **+.0896** | +.0744 | +.0146 | +.0062 |

One sentence: **the signal is right for the first ~7 minutes of its own trigger bar, crosses
to wrong between minute 6 and 7, is most wrong one minute before it is allowed to act, and by
two minutes after the close it knows nothing at all.** Total swing 0.177 R/trade.

The estate's framing — *"a bar closing is the moment the move it describes has already
finished"* — is now measured, and it is sharper than that: **the move is finished at minute
7 of 15.**

### Charge 3: setups that never form — the real bill

We built the obvious partial-bar trigger and ran it over **every one of 71,437 January M15
bars on 24 symbols** — fire at minute *j* when the running move from the bar's open reaches
a threshold, direction = sign of the move, same walk, same broker-true cost.

| threshold | minute | fired | **precision** | net R when it was a real setup | net R when it was not | net R, whole book |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 3 | 5,369 | 0.2824 | **+0.23105** | −0.31147 | −0.15828 |
| 0.75 | 3 | 2,311 | 0.3626 | +0.21707 | −0.34068 | **−0.13843** |
| 1.00 | 5 | 2,008 | 0.4248 | +0.17193 | −0.41283 | −0.16442 |
| *baseline: the real candidates at the M15 close* | | 12,892 | — | — | — | **−0.23410** |

Three things this settles:

1. **The prize survives a real trigger.** When the trigger caught a genuine setup it earned
   **+0.17 to +0.23 R/trade net** — a swing of +0.42 to +0.47 R against those same names
   entered at the close.
2. **Even the bare trigger already beats the shipped contract** (−0.138 vs −0.234). It is
   still negative, so this is a better way to lose money on this pool, not an edge.
3. **"Enter early, then flatten if the bar doesn't confirm" is refuted by measurement.** It
   is the obvious design — the book already re-evaluates at each close — and it is wrong in
   **every one of 30 cells**. Flattening pays a second toll and locks in the drift: the
   unconfirmed leg goes from −0.24 (let it run) to −0.47 (flatten it). Letting a phantom run
   is strictly cheaper. [x3 §4b]

### The number that defines the remaining work

`net = precision × net_confirmed + (1 − precision) × net_phantom`

| cell | achieved precision | **break-even precision** | gap |
|---|---:|---:|---:|
| threshold 0.50, minute 3 | 0.2824 | **0.5741** | **+0.292** |
| threshold 0.75, minute 3 | 0.3626 | **0.6108** | **+0.248** |
| threshold 1.00, minute 5 | 0.4248 | 0.7060 | +0.281 |

**An intra-bar trigger must reach roughly 0.57–0.61 precision at minute 3 for earliness to
pay outright. The bare version reaches 0.28–0.44. The gap is about 0.25 of precision on
2,300–5,400 firings a month.** That is the whole remaining question. [x3 §4c]

## 3.5 A control that refuted the obvious story — and made the answer more useful

x1 built the honest, implementable version: enter at the *first minute the family's own
predicate is true* using only the bars that had printed by then, at the original risk
distance so cost is unchanged. It is worth **+0.155 R/trade** on the four families that want
it, **21 of 21 days positive**.

Then it ran the control: enter at a **fixed minute 7, ignoring the predicate entirely**.

| arm | pooled | excluding `structural_distance_extreme` |
|---|---:|---:|
| as ran (entry at the close) | −0.05591 | −0.05213 |
| **detect-the-signal, act at that minute** | **+0.00125** | +0.10311 |
| **placebo: act at a fixed minute 7, no signal** | **+0.00123** | +0.13343 |
| **difference** | **−0.00004 (t −0.03)** | −0.03024 |

**They match to four decimal places.** An arm that has no idea whether the setup will fire
scores the same as the arm that waited for it. **The value is not the signal turning true —
it is the minute of the clock.** [x1 F2]

This is a refutation of x1's own first reading and it is the more useful result: it says the
defect is the **entry anchor**, not detection lag. It also means the *simple* version — move
the anchor — captures most of what the *clever* version would.

## 3.6 The levers do NOT add up — a correction to something already published

The estate has two published earliness-adjacent levers: **"refuse the first-minute fills"
(+0.22 R/candidate)** and **"delay entry 5 minutes" (+0.067 R/trade)**. They have been
reported separately. **They must never be summed.**

Measured on the same rows, at-market contract:

| | Δ R per candidate |
|---|---:|
| delay to +5 min alone | +0.0619 |
| cancel the immediate fill alone | +0.1266 |
| **naive sum** | +0.1887 |
| **actual joint** | **+0.0439** |
| **over-count** | **+0.1448 — the naive sum is 4.3× the truth** |

The joint is *worse than the cancel alone.* The reason is mechanical: the delay lever is
measured on precisely the rows the cancel deletes — 75.8 % of at-market candidates have their
entry touched on the first bar. [x5 §3]

And a related mechanism finding worth having: **the adversely-selected immediate fill is a
property of limit orders, not of the bar boundary.** It re-creates itself at every placement
offset and gets *worse* the later you place: the first fill after placement books −0.2686
(place at 0), −0.4291 (place at +5), −0.6712 (place at +60). It is ordinary limit-order
adverse selection — an immediate fill means the market is coming through your level. The
estate's cancel rule is right, for a reason it had not stated.

---

# PART 4 — Does anything inside the bar tell a good setup from a bad one?

This was the mission's core question — the piece the estate has never had. The answer has
two halves, and they point in opposite directions.

## 4.1 Bar SHAPE: no. Measured exhaustively, and the null is clean.

**87 intra-bar features** were built on 27,230 candidates (x4), plus **18 more** built
independently (x2). Everything the question implies was tested.

| what was tested | best \|Cohen's d\| |
|---|---:|
| where in the bar the move happened | 0.057 |
| how many minutes trended vs retraced | 0.053 |
| close position within the range | 0.054 |
| range-expansion profile | 0.082 |
| volume / tick distribution across the 15 minutes | 0.037 |
| shape of the approach to the entry level | 0.077 |
| touched once vs repeatedly | 0.045 |
| late momentum / exhaustion | 0.042 |
| prior-bar context | 0.054 |
| minute of the high / minute of the low (x2) | 0.031 / 0.014 |
| path efficiency — how straight the move was (x2) | 0.134 |
| body size and range size vs ATR (x2) | 0.141 / 0.135 |

**Conventionally d < 0.2 is negligible and d < 0.1 is not worth naming. Not one shape
feature reaches 0.09.** The estate's own prior record was 0.152.

Cross-fitted properly (grouped by trading day so no day appears in both training and test):

| feature set | AUC |
|---|---:|
| everything knowable strictly **before** the decision, 87 features, gradient boosting | **0.5528** |
| same, logistic | 0.5568 |
| **+ the single minute after the decision**, logistic | 0.5786 |
| **+ the single minute after the decision**, gradient boosting | **0.5884** |

The estate's prior range across its entire emitted schema was 0.44–0.57. **So everything
inside the forming bar, before the decision, is worth roughly nothing beyond what the engine
already emits — and the single minute after it is worth +0.035 AUC.**

**Stop looking inside the bar for shape. It is measured. The money is not there.** [x4 §8,
x2 §6]

## 4.2 The one minute AFTER the decision: yes, and it is the strongest single discriminator the estate has

Define `c0` = where price sits relative to the entry at the close of the first minute after
the decision, in risk units. Negative means price has already run against you.

Inside the 55.65 % adversely-selected cohort the estate could not decompose:

| cohort | n | R/trade | 95 % day-block CI | stop rate | odd days | even days |
|---|---:|---:|---|---:|---:|---:|
| all | 12,933 | −0.17335 | [−0.20260, −0.14431] | 0.542 | −0.16920 | −0.17719 |
| **first minute did NOT run against you** (`c0 > −0.15`) | 8,458 | **−0.06174** | [−0.09506, −0.02932] | 0.465 | −0.05641 | −0.06668 |
| **first minute DID run against you** (`c0 ≤ −0.15`) | 4,389 | **−0.38238** | [−0.42524, −0.33782] | 0.687 | −0.38000 | −0.38461 |
| strict cut (`c0 > −0.05`) | 5,563 | **−0.03352** | [−0.06992, **+0.00634**] | 0.451 | −0.04269 | −0.02477 |

**Cohen's d = 0.3348, AUC = 0.5912 — 2.2× the estate's standing ceiling of 0.152.** Right
sign on **23 of 24 symbols, 8 of 8 families, 24 of 26 sessions**. Stable to the third decimal
across odd/even days. Not an order-type artifact: at-market rows show a gap of +0.305,
resting-limit rows +0.342.

**On the whole pool:**

| rule | refused | **what the refused set books** | 95 % CI | kept | kept books |
|---|---:|---:|---|---:|---:|
| none | 0 | — | — | 27,230 | −0.23551 |
| **refuse `c0 ≤ −0.15`** | **8,111 (29.8 %)** | **−0.66506** | [−0.69693, −0.63193] | 19,119 | **−0.05327** |
| refuse `c0 ≤ −0.05` | 11,008 (40.4 %) | −0.52044 | [−0.55048, −0.48800] | 16,222 | −0.04215 |

**That is the largest identified loss cohort in the whole wave.**

**Three honesty notes that must travel with it.**

1. **It is not a new field.** It is byte-for-byte a quantity the estate already computed
   (`mkt_r_close`) and used only as a *binary* classifier — max difference 5e-7, Pearson
   1.0000 over 27,033 rows. What is new is that as a *continuous* quantity inside the
   takeable population it is the strongest single discriminator in the entire schema.
2. **It is legal at your current cadence.** It is an observable at T+1 minute, and
   `run_book.py --poll-seconds 60` already puts the poll exactly there. **This needs no new
   infrastructure at all.**
3. **It has not travelled.** January only. Testing it on February / April / May is one
   command and it is the single highest-value next measurement in this report.

## 4.3 The two axes are substitutes, and the confirm minute wins

The best strictly-before-the-decision field the estate now has is
`stop_dist_over_bar_range` = the stop distance divided by the range the market just made in
the last 15 minutes. **A stop set inside the noise the market just made is hit 70 % of the
time** (bottom decile stop rate 0.696 vs top decile 0.207). Its d is **−0.183** — it also
beats the old 0.152 ceiling.

But when the two are combined:

| test | refused n | what the refused set books | verdict |
|---|---:|---:|---|
| geometry applied **after** the confirm filter | 3,822 | −0.04851 [−0.12038, +0.03263] | **adds nothing** — it refuses rows that were *better* than what it keeps |
| confirm applied **after** the geometry filter | 5,638 | **−0.65047** [−0.68794, −0.60750] | **the whole effect survives** |

The 5 × 5 joint surface says the same without any modelling: the most-adverse confirm-minute
quintile books −0.84 to −0.91 across **all five** geometry quintiles. **One variable owns the
surface.** [x4 §6]

## 4.4 The one *condition* that beats the clock

Every conditional rule enters at a different minute, so its advantage may be nothing but the
clock. The control is to price the whole population at that rule's own distribution of entry
minutes and subtract. 1,132 arms were priced this way. Almost everything failed:

- **Directional confirmation is worth nothing, and its opposite scores the same** — requiring
  the bar to be moving your way scores +0.0795; requiring it to be moving *against* you
  scores +0.0704. Two opposite conditions, same value ⇒ the value was "the row qualified
  early", not what it qualified on. **Refuted by symmetry.**
- **Stronger directional confirmation is actively harmful**: −0.0950.
- **Aborting on the first adverse close destroys value** at almost every rung.

**One survived.** Call it *level-crossing*: price was on the *wrong* side of the candidate's
own entry level when the trigger bar opened, then traded through that level and **stayed**
there for N consecutive minutes; then enter at market. For N ≥ 18 every entry lands at or
after the M15 close — **nothing is acted on early, and the level is known at the decision
instant — so this is honest and fill-realistic.**

| N | n | survival | R/trade | matched control | **value over the clock** | p(≤0) | days + | symbols + |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 4,855 | 18.4 % | −0.0502 | −0.1133 | **+0.0631** [+0.0186, +0.1125] | 0.001 | 14/21 | 18/24 |
| **18** | 4,008 | 15.2 % | −0.0437 | −0.1048 | **+0.0611** [+0.0169, +0.1151] | 0.004 | 15/21 | 17/24 |
| **25** | 2,601 | 9.9 % | **−0.0170** | −0.0923 | **+0.0753** [+0.0149, +0.1400] | 0.010 | 15/21 | 18/24 |

De-duplicating to first emissions moves it the *right* way, so it is not repeated-setup
inflation. Stop rate falls monotonically with N (0.371 → 0.261); win rate rises
(40.0 % → 44.1 %).

**This is the piece the estate has never had: a condition computable from information
available at the decision instant that is worth +0.06 R/trade over the same population
entering at the same minutes.** It does not make January positive; it removes about a third
of the honest deficit on the 10–15 % of candidates it keeps.

**And the finding that must not be buried: its exact inverse is positive at every N**
(+0.049 to +0.074 R/trade, p 0.000–0.055). The crossing filter *halves* the pool-wide
direction inversion but does not remove it. That is a known estate phenomenon surviving a
strong filter, not a new one — and it is one month. **Reported, not recommended.** [x5 §5]

---

# PART 5 — What it would take on the live book

## 5.1 The change is one call site, and the traffic is trivial

Do **not** move sleeves to a 1-minute decision grid. Measured cost of that:

| cadence | broker `copy_rates` calls/day | bars/day |
|---|---:|---:|
| H4 today | 120 | 31,200 |
| full M1 re-decide | 28,800 | **7,488,000** (240×) |

**Do this instead — the early-trigger seam.** Most "go early" rules have the form *price
crossed a level the last closed bar already defined.* That needs a **quote**, not a bar
series.

1. Keep the decision grid. When a cycle runs, persist alongside each intent the **trigger
   level** the sleeve's rule implies for the forming bar.
2. In `BookLauncher.tick()`, between `:316` and `:318`, evaluate those levels against
   `owner._tick(symbol)` — **one `get_tick` per armed symbol per poll, ≈20 calls/minute.**
   That is the same kind and volume of read `manage_open_positions` already performs every
   60 seconds.
3. Place through the existing path, so the placement ledger, cluster cap, governor and cost
   screen all still apply unchanged.
4. Gate it behind a **default-off `run_book.py` flag** — the estate's established pattern,
   and on the command line because `agent_config.yaml` bytes are hashed into the live
   activation token.

**Cost: ~28,800 tick reads/day, zero extra bars.** At the measured round-trip (FTMO 3,536 µs,
redacted_account 1,698 µs) that is about **2 minutes of network time per day**. **Effort: 1–2
sessions.** [x6 §6]

## 5.2 Data is not a blocker, and it is not close

| | FTMO-Server3 | redacted_account-Server 2 |
|---|---|---|
| symbols probed | 19 | 23 |
| **M1 available** | **19/19** | **23/23** |
| M1 depth, median | 98.6 days | 98.2 days |
| `terminal_maxbars` | 100,000 | 100,000 |

The binding limit is the **client-side terminal setting**, not the broker — raisable by an
operator without touching code. And what an intrabar decision actually needs is far less:
**240 M1 bars for an H4 bar, 15 for an M15 bar, against ~141,000 available.** Three orders of
magnitude of headroom. A 20,000-bar M1 pull has already run on the live terminal.
[x6 §4, probe dated 2026-07-26 — no VPS was touched for this report]

## 5.3 Five guards that mis-fire on a finer cadence — one of them silently

**(a) THE BLOCKER — `_entry_too_late` would shadow roughly half of all entries, and log a
reason that reads as healthy.** `book_owner.py:397-410` allows an entry within
`frac × bar_period`, with `frac = 0.5` (`agent_config.yaml:1390`). At H4 that is a 120-minute
window. **At M1 it is 30 seconds — against a 60-second poll.** Entries land uniformly 0–60 s
after the close, so about half exceed it and are shadowed with the reason
`stale_late_entry_after_restart`. It is fail-open by design: **nothing errors and no alert
fires.** Any intrabar work must re-derive that window from the *trigger* instant, or it will
measure a lever it has already thrown away.

**(b) The recency guard's margin collapses from 8 hours to 2 minutes** (`book_engine.py:601`),
so one slow poll drops the decision entirely.

**(c) A finer grid silently *tightens* the correlated-cluster cap.** Two sleeves in one
cluster firing anywhere inside one H4 bar are the same decision bar today and both place; on
a finer grid they become different bars and the second is refused. Nothing warns.

**(d) A finer cadence is a size-UP, not neutral.** The Kelly-lite running conviction count
reaches the day's higher bin sooner, so more of the day's trades are sized at the higher
multiplier — up to **+25.2 %** on every unit that day. Same day-end value, different intraday
path.

**(e) One line already does most of the safety work.** `already_placed_today(sleeve, symbol,
day)` caps entries at one per sleeve per symbol per day. **A 15× decision cadence therefore
does NOT produce 15× more trades** — the first qualifying moment wins and every later one is
refused. That is exactly the intent ("take the setup early"), already enforced. It does
change *which* trade is taken.

**(f) Pre-existing bug that a finer grid would inherit**: H4 and D1 get a *list* of reference
symbols so cycles still fire over the weekend; M15 and M1 carry a single `"USDJPY"`, so no M1
cycle would ever fire on a weekend. [x6 §5]

## 5.4 The cost model is already fine enough — this is not a spread problem

Measured over **128,150,823 FTMO ticks** (June–July 2026; mechanism only, never used to score
a January candidate):

| | value |
|---|---:|
| **spread component of the 5-minute-delay lever** | **+0.000516 R/trade** |
| the lever itself | +0.0670 R/trade |
| **share** | **0.77 %** |

There *is* a real bar-close spread premium, but it is an FX phenomenon and it is essentially
absent on your armed surface:

| cohort | median premium at the boundary minute |
|---|---:|
| **armed symbols** | **+0.66 %** (BTCUSD 0.00 %, USOIL_cash 0.00 %, US30_cash 0.00 %, XAUUSD +0.49 %) |
| everything else | +5.74 % |
| worst outside the armed set | USDJPY **+50.79 %** at H4-close hours |

And the decomposition corrects the intuitive read: the M15 close itself is nearly free
(+1.04 %); almost all of the boundary premium sits at the **hour** close (+8.11 %).

**Making the cost model minute-aware is not the work.** [x6 §3]

---

# PART 6 — What is thin, and what is wrong in the record

**These are the caveats. They are real, and they do not erase Part 3 or Part 4.**

1. **One month.** Everything is January 2026, one replay arm. There is **no out-of-window
   test of any earliness finding.** February is used-once validation data and was not
   touched; March is deliberately outcome-unread; April and May belong to another lane.
   Travel testing is the next stage's job and it is cheap — the feature builders run
   unchanged on any month and the source data exists for all of them.
2. **Multiplicity is not corrected anywhere, deliberately.** This was a discovery brief where
   under-reporting was the named failure mode. x4 built 87 features and ~700 cells; x5 priced
   1,132 arms; x3 swept 51 offsets. **Nothing here has been corrected for how many things
   were looked at.** Treat single cells with suspicion; treat the effects that hold across
   21/21 days, 24/24 symbols and 8/8 families as the ones that will probably survive.
3. **Cost is the ceiling and nothing in this report clears it.** Mean cost on this pool is
   **0.53–0.65 R/trade** against timing levers of 0.06–0.15 R. The best honest,
   fill-realistic construction in the whole swarm — a limit placed 8 minutes after the
   decision, cancelling any first-bar fill — books **−0.0078 R per candidate
   [−0.0254, +0.0106]**: indistinguishable from flat, not positive. The source itself named
   the cause years ago: *"the measured 0.25×ATR(M15) stops put routine M1 noise and ~0.17R
   costs above the realizable exit edge."* **Earliness and stop geometry are two different
   repairs and this pool needs both.**
4. **A substrate defect that bounds several published numbers, including one you have been
   told.** The minute-by-minute path data used by every earlier lane **starts at
   decision + 1 minute**. The first 60 seconds of live exposure is in no path at all. So
   *"55.65 % of candidates have their entry touched within 60 seconds"* actually means
   **within 120 seconds**; the true within-60-seconds rate is **70.53 %**. 3,097 candidates
   (11.37 % of the pool) had their entry traded inside that missing minute and are invisible
   to the flag. Including the true first minute costs the shipped contract −0.00299 R/trade.
   Fixing it is a re-materialisation, not a new measurement.
5. **The two published levers have been double-counted wherever they were added.** §3.6:
   the naive sum is **4.3× the truth** on this pool.
6. **The look-ahead half of the curve is not a strategy.** Every number at a negative minute
   offset assumes the system knows a setup will fire before it fires. Those rungs are an
   **upper bound on the prize**. The implementable numbers are +0.155 R/trade (x1's confirm
   arm), +0.065 (the side-free residue), +0.061 (level-crossing), and the refusal economics
   in §4.2.
7. **A replication hazard in the zone families.** `current_breaker_re_entry`'s 4,263 pool
   rows are only **225 distinct zones** — the same setup re-offered ~19 times. The estate's
   de-duplication keys on an ID that is stable for FVGs but not for breakers, so it does not
   catch this. Any significance test on that family computed on 4,263 rows is inflated ~19×.
8. **A unit defect found on the way past**, worth knowing because it is a decision-time
   arithmetic error rather than a timing one: the proximity gate that admits zone candidates
   is denominated in **fraction of price** (1 %) while the trade's risk unit is the zone
   half-width. For an H1 breaker that admits candidates a **median 6.4 risk units** away
   (p99 22.9). Dropping the rows whose stop was already past at the decision close moves the
   pool **−0.2148 → −0.1004 R/trade (+0.1144)** — and it needs no minute data at all.

---

# PART 7 — WHAT TO BUILD, IN ORDER

Value figures are January, gross unless stated, and none has travelled out of window.
"Effort" is engineering sessions on this machine unless it says otherwise.

### 1. Travel-test the confirm-minute refusal — **highest value per hour of work in this report**

**What:** one variable, one threshold, no fitting. Refuse a candidate whose first minute
after the decision has already run ≥ 0.15 R against the entry.
**Worth:** refuses 29.8 % of the pool booking **−0.66506 R each** [−0.697, −0.632]; the kept
set goes −0.236 → **−0.053**. Cohen's d 0.335, AUC 0.591 vs a standing 0.152 ceiling.
**What it takes:** run the existing builder on February, April, May. **No new code, no new
data, no infrastructure — the live book already polls at 60 seconds.** ~1 session.
**Decision it changes:** if the refused-set mean is ≈ −0.6 R in another month, the estate has
its first entry-timing rule with an out-of-window number, and it is wireable behind a
default-off flag immediately.

### 2. Build the early-trigger seam, default off

**What:** persist each intent's trigger level, evaluate it against a live quote inside the
existing 60-second tick, place through the existing path. **~20 `get_tick` calls per minute,
zero extra bars, ~2 minutes of network time per day.**
**Worth:** it is the *enabler* for everything in Part 3, not itself an R figure. Nothing in
this report can be acted on live without it.
**What it takes:** **1–2 sessions**, plus one precondition that has not been checked — whether
a trigger level can be expressed as a pure function of the last closed bar **for the armed
sleeves specifically**. That is a per-sleeve read of the generators and should be done first.
**Do not** move sleeves to an M1 decision grid; that costs 240× the broker traffic and
inherits five broken guards.

### 3. Re-derive `_entry_too_late` from the trigger instant — do this *with* item 2, not after

**What:** one derivation change (or one config key).
**Worth:** without it, an intrabar seam would shadow roughly **half of all entries** while
logging a reason an operator reads as a healthy restart guard. It is fail-open, so nothing
errors and no alert fires.
**What it takes:** hours, inside item 2. **It is the single biggest blocker and it is
invisible.**

### 4. Re-materialise the minute paths from the decision instant, not one minute later

**What:** rebuild the path substrate starting at T instead of T+1 minute.
**Worth:** correctness. **11.37 % of the pool is currently booked against a fill the
substrate cannot see**; the estate's published "touched within 60 seconds = 55.65 %" is
actually 70.53 % measured properly. Every fill-honest number in wave 19 inherits the gap.
**What it takes:** ~1 session, mechanical.

### 5. Fix the proximity-gate unit defect — cheapest R in the report, and it is not a timing fix

**What:** `_zone_proximity_pct` (`broader_origin_generators.py:1711-1717`) compares a
fraction-of-price against a 1 % tolerance while the trade's risk unit is the zone half-width.
**Worth:** **+0.1144 R/trade on the pool** (−0.2148 → −0.1004) by dropping the candidates
whose stop was already past at the decision close. Needs no minute data.
**What it takes:** ~1 session including the re-derivation of what the tolerance should be in
risk units.

### 6. Travel-test level-crossing (the one condition that beat the clock)

**Worth:** +0.0611 R/trade at N=18 over the same population entering at the same minutes,
honest and fill-realistic, 15/21 days, 17/24 symbols, survives de-duplication.
**What it takes:** one command per month. ~0.5 session. **Test its inverse in the same run** —
the inverse is positive at every N and that is either a real inversion or a warning.

### 7. Fix `cross_asset_lead_lag`'s anchor — small, legible, and currently absurd

**What:** the family's own premise is a 15-minute lead and it waits for the lagging bar to
close anyway. Entering at the leader's own bar is **+0.9668 R/trade**; when the lag bar opens
it is already **−0.1343**.
**Worth:** +1.04 R/trade on that family (n=2,083) in January. **But the family is not armed,
the pool is negative, and this has not travelled.** It is on this list because it is the
clearest single mechanism defect found, not because it is bankable.
**What it takes:** one line plus a re-run. ~0.5 session.

### 8. The big one, and it is blocked on a measurement, not on engineering

**What:** a partial-bar generator for the four families that want the bar's open —
`displacement_continuation`, `regime_transition_break`, `session_open_range_break`,
`volatility_compression_expansion`.
**Worth if it works:** **+0.29 to +0.73 R/trade** on those families; the five-family early
book is **+0.1183 R/trade net of broker-true cost, +1,186.7 R for January**, 27/27 days.
**What blocks it:** the trigger must reach **0.57–0.61 precision at minute 3**. The bare
version reaches **0.28–0.44**. That gap — ~0.25 of precision on 2,300–5,400 firings a month —
is the entire remaining question, and **bar shape has been measured and cannot close it**
(|d| < 0.09 on all 87 features; cross-fitted pre-decision AUC 0.553).
**Do not build the obvious mitigation.** "Enter early, flatten if the bar doesn't confirm" is
measured and it is wrong in all 30 cells: flattening pays a second toll and books −0.47
against −0.24 for letting the phantom run.
**What it takes:** an honest separator lane first. Until that number moves, this is a
research target, not a build.

### 9. Price a 15-second poll (optional, and it is not a new signal)

**Worth:** 60 % of the confirm-minute displacement already exists at 15 seconds, with ~70 %
sign agreement; 76–98 % of bar boundaries have already moved within **one second** of the
close. So a faster poll buys **earlier action on the same information**, not new information.
**What it takes:** the measurement exists (x4 §9, out-of-window mechanism). The open question
is whether acting 45 seconds earlier is worth the 30 % of sign disagreement it buys.

---

## One paragraph, if you read nothing else

**The system is not slow — it wakes every minute and refuses to think on 239 of every 240
wakes, because of one line that says "no new bar, return".** The setup was already true a
median of 14 minutes earlier; by the time the bar closes, 76 % of its move has printed and
one candidate in five has already reached its take-profit *inside its own decision bar*.
Going early is worth **+0.14 to +0.74 R/trade** depending on the population, and **82.5 % of
that is the bar's own move** — real, but only reachable by a generator that fires on a
half-finished bar, and the bare version of that fires on 3–6× too many setups. **What is
reachable now, with no new infrastructure at all, is the minute *after* the decision: it
identifies 29.8 % of the pool that books −0.665 R each, and it is the strongest single
discriminator the estate has ever measured.** Test whether it travels to another month —
that is one command, and it is the highest-value hour of work on this list.

---

### Where every number comes from

All under
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`:

| lane | receipt | what it owns |
|---|---|---|
| **x1** | `x1_RESULT.md` / `.json` | the source trace, the live-poll behaviour, staleness, the entry-anchor curve, the placebo control |
| **x2** | `x2_RESULT.md` / `.json` | the ten conditions transcribed from source, first-detectable minute per family, the structural split, M5/M1 native analogues |
| **x3** | `x3_RESULT.md` / `.json` | the offset curve, the per-family prize net of broker-true cost, the 71,437-bar phantom scan, the break-even precision |
| **x4** | `x4_RESULT.md` / `.json` | 87 intra-bar features, the cross-fitted ceiling, the confirm-minute split, the missing-minute defect |
| **x5** | `x5_RESULT.md` / `.json` | the entry-minute ladder, the exact mirror decomposition, the cancel × delay ablation, level-crossing |
| **x6** | `x6_RESULT.md` / `.json` | live feasibility, the five guards, the tick-measured spread model, the implementation sketch |

Prior swarm receipts relied on: `l3_RESULT.md` (the 0.152 ceiling, inverted confidence),
`l7_RESULT.md` / `L7_RESULT.md` (the +0.0670 delay lever, the inversion),
`l8_RESULT.md` (the 55.65 % cohort, the realised 1.1768:1 payoff and its 45.94 % break-even
against an achieved 34.68 %), `l12_RESULT.md` (the 15-component score vs a coin flip),
`e6_RESULT.md` (the five-month, 124,722-candidate, 101/101-day robustness of the cancel rule).
