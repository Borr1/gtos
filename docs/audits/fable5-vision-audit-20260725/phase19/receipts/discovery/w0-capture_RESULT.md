# w0-capture V3 — what closes a winning trade at +1.04 R, and what actually kills the pool

**Two answers. Both measured with zero look-ahead. The second is 6.7× the first.**

**(1) The gating question, answered mechanically.** Nothing *cuts* winners. On the tradeable
population, 3,709 winners exit at exactly **+2.002 R** and **4,807 — 56.45 % of all winners — are
marked to market at a 2-hour wall at +0.593 R.** They run out of clock. Lifting the wall into 24 h
of raw M1 is worth **+0.017 R/trade**. That is hypothesis (A), and it is small.

**(2) 58.25 % of the pool's entire deficit sits in 12.72 % of its rows, and those rows are
identifiable from the price at the decision instant alone.** 3,516 candidates were emitted with an
entry price whose **stop-loss had already been breached before the order could be sent** — a median
**7.58 stop-widths** past the entry, quoting a level price last traded a median **499 M1 bars
(8.3 h) earlier**, and for **55.66 % of them a level price has not traded at all in the prior
1,440 bars.** Every one books a mechanical −0.9948 R with a **0.085 % win rate**.

| born state at the decision instant | n | share | engine gross R | win % | **contribution to the pool's −0.21724** |
|---|---:|---:|---:|---:|---:|
| born_at_limit — entry == the decision-instant price | 14,911 | 53.95 % | −0.0904 | 39.47 | −0.04878 |
| born_resting — limit rests on the correct side | 7,949 | 28.76 % | −0.1049 | 41.99 | −0.03017 |
| born_marketable — limit through the market, stop intact | 1,265 | 4.58 % | −0.2566 | 28.70 | −0.01174 |
| **born_past_stop — limit through its own STOP** | **3,516** | **12.72 %** | **−0.9948** | **0.085** | **−0.12654** |
| | 27,641 | | −0.21724 | 34.68 | −0.21724 |

**Drop born_past_stop and the pool goes −0.21724 → −0.10392 over the remaining 24,125 rows:
+0.11332 R/trade, hindsight-free.** **98.61 % of that population is one family**
(`current_breaker_re_entry`, 3,467 of 3,516).

| lane hypothesis | mechanism | R/trade |
|---|---|---:|
| (A) horizon wall | 2-hour mark-to-market, `REPAIRED_PENDING_EXPIRY_MINUTES=120` (`:378`) | **+0.0170** |
| (B) exit policy cuts winners | **refuted — no such mechanism exists in the source** (§1.2) | +0.0033 → +0.0185 |
| **(C) entry contract** | order emitted past its own stop before it could be sent | **+0.1133** |

---

## 0. Provenance, and a correction this lane made to itself

* Population `CJ_RECLOCKED_S0R0_POOL_V1` (January 2026, true UTC, n = 27,658) joined to
  `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1` through wave-0's `w0_WORKING_SET.jsonl.gz`.
* **New in V2/V3:** the market price at the decision instant, reconstructed from the raw M1 series
  at `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601`
  (24 symbols, 44 MB). **27,641 of 27,658 rows anchored (99.94 %)**; 17 rows have no bar at or
  before their decision time and are excluded from every number here.

### 0.1 THE ANCHOR CORRECTION — read this before citing any V2 number

The path sidecar starts at `decision_time + 1 minute`, so no prior lane could see the decision
instant at all. V2 of this receipt anchored on the M1 bar **stamped at the decision minute**. That
was wrong, and this lane caught it by re-running its own headline on the strictly-prior bar and
finding the split moved.

**The bars are OPEN-STAMPED, proved against the M15 series in the same source tree.** Aggregating
M1 bars `T … T+14` versus `T−14 … T` and requiring an exact high *and* low match to the M15 bar
stamped `T`:

| symbol | M15 bars tested | **open-stamped matches** | close-stamped matches |
|---|---:|---:|---:|
| EURUSD | 2,016 | **1,921** | 4 |
| GER40 | 1,903 | **1,704** | 2 |
| BTCUSD | 2,908 | **2,806** | 1 |
| XAUUSD | 1,922 | **1,881** | 0 |

(misses are gaps in the M1 series). **Therefore the M1 bar stamped at the decision minute covers
`[decision, decision+60 s)` and is entirely POST-decision.** The last price observable at the
decision instant is the close of the bar stamped `decision − 1 min`.

This is corroborated by the engine's own doctrine — module docstring
`v4_timewarp_simulated_live_research_loop.py:3-5`:

> *"replays live V4 decisions … using closed D1/H4/H1/M15 FTMO bars for **predecision state** and
> M1/tick rows only for **postdecision** simulated account events."*

and by `predecision_current_price_signal` (`:53726`), which resolves the predecision price from
`predecision_current_price` → `source_fields.current_price` → `source_fields.close` →
`source_fields.m15_close`, gated by
`predecision_market_price_source_time_at_or_before_decision` (`:60482`). **None of those fields
exist in this pool**, which is why reconstruction was necessary.

**Every number in V3 uses the strictly-prior bar.** The V2 arm is retained in
`W0CAP2_NOLOOKAHEAD_V1.json` as a labelled sensitivity and **its results must not be cited**:

| | V2 anchor (60 s of look-ahead) | **V3 anchor (none)** |
|---|---:|---:|
| born_resting n / gross | 14,086 / **−0.0009** | 7,949 / **−0.1049** |
| born_marketable n / gross | 9,035 / −0.2354 | 1,265 / −0.2566 |
| **born_past_stop n / gross** | **3,785 / −0.9985** | **3,516 / −0.9948** |
| classifier agreement between anchors | | **46.41 %** |

**Retracted:** V2's *"the legitimate resting-limit half of the pool books −0.0009 R/trade"* and its
"DEFECT 1 — sub-spread limit placement worth −0.0769 R/pool-trade". Both were manufactured by
classifying on the sign of the first post-decision minute. **The born_past_stop finding and the
entire CQ result survive the correction essentially unchanged** (§6), because a level 7.6
stop-widths away does not move in one minute.

* V1 of this receipt (an earlier agent in this lane, which died before returning) is preserved
  verbatim at `w0-capture_RESULT_V1_PRIORAGENT.md` / `.json` and merged into
  `w0-capture_RESULT.json` under `v1_prior_agent_full`. Numbers labelled **[V1]** are that agent's.
* **Sample caveat, stated once:** one month, one arm (S0R0), one broker series. `candidate_id` is
  not a primary key (W0-F1: 24.39 % pseudo-replication, 91.9 % of it `current_fvg_fill`); nothing
  here is de-duplicated, so effective n is nearer 21,880. No multiplicity correction applied or
  claimed.
* No sealed replay launched, no VPS touched, no broker-capable script run, no April/May pack read,
  no February economics read, no live-forward P&L computed.

---

## 1. SOURCE — where the numbers are made (METHOD 1–3)

### 1.1 `opportunity_net_proxy_r`, `cost_r`, `expected_net_r`

`v4_timewarp_simulated_live_research_loop.py:92577-92580`:

```python
missed_net_proxy_r = (None if missed_final_r is None
                      else round(missed_final_r - expected_cost_r, 8))
```

written as `"opportunity_net_proxy_r"` at `:92730`, twin site `:92972` → `:93122`. Verified
empirically: `max |gross_r − expected_cost_r − opportunity_net_proxy_r| = 5.0e-10` over 27,658 rows.

Frozen cost, means over the pool: `expected_cost_r` **0.66316** = `spread_r` 0.56421 (**85.08 %**)
+ `commission_r` 0.06522 (9.83 %) + `expected_slippage_r` 0.02000 (a flat constant on every row,
3.02 %) + `swap_cost_r` 0.01372 (2.07 %). Medians: cost 0.30313, spread 0.18063.
`max_total_cost_r` / `total_cost_r` are **absent from this pool** — the 0.15 gate named in the brief
is not observable here.

### 1.2 Every exit rule that can produce an outcome below target

`path_final_r`, `:60302-60356`, six terminal branches:

| # | branch | value | line |
|---|---|---|---|
| 1 | `not_filled_no_trade` | `None` | `:60308-60310` |
| 2 | `target_reached_before_stop` | `+target_r` | `:60336` |
| 3 | `stop_reached_before_target` | `−1.0` | `:60337-60340` |
| 3b | …`partial_be_runner` and 1R touched | `+0.5` | `:60338-60339` |
| 4 | `same_bar_ambiguity_conservative_stop_close` | `−1.0` | `:60342-60346` |
| **5** | **`time_stop_close_mark_from_<source>`** | **`max(-1.0, min(close_mark_r, target_r))`** | **`:60347-60355`** |
| 5b | …after partial harvest | `0.5 + 0.5·max(0, bounded_close_r)` | `:60352-60354` |
| 6 | `source_required_filled_no_terminal_close_mark_missing` | `None` | `:60356` |

**Only branch 5 can produce a positive outcome below target.** There is no trailing stop, no
scale-out, no session-boundary exit and no MTM close other than this one — **hypothesis (B) has no
mechanism in the source.** The overriding layer `apply_selected_execution_policy_replay_exit`
(`:60973`) returns unchanged when `fill_status` is not `filled*` (`:60993`), when no policy key is
present (`:60995`), or when the spec is `None` (`:61002`); in this pool
`by_selected_policy_for_expected_net_r` has exactly one level, so it is not a differentiator.

### 1.3 The horizon — exact value and where it is set

```python
REPAIRED_PENDING_EXPIRY_MINUTES = 120                       # :378
expiry = min(asof + timedelta(minutes=campaign.pending_expiry_minutes),
             datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1))  # :92468-92478
```

**120 minutes, or end of trading day, whichever comes first**, applied when the oracle is built
(`path_source_and_oracle`, `:63902`) so the walk physically cannot see a later bar. Confirmed in the
data: every path ≤ 120 M1 bars, 86.12 % exactly 120. **[V1]** 4.89 % are truncated by the day-end
clause rather than the 120 minutes.

### 1.4 The entry-fill contract

`marketable_limit_immediate_fill_candidate`, `:54258-54268`, docstring verbatim:

> *"A marketable limit is not a resting order in replay. The requested limit is the worst acceptable
> price; the effective fill is the decision-time market price when a source-safe predecision price
> exists."*

The engine **knows** the right answer and re-canonicalises the geometry when it fires
(`original_limit_entry_price` / `original_limit_stop_loss` / `original_limit_take_profit_1`,
`:54320-54334`). **[V1]** the input flag `limit_marketable_at_decision` is `None` on **85.2 %** of
rows, so it almost never fires; where it *is* `True` the same gap-through population books
**−0.3549** instead of **−0.6162** — the handler halves the damage wherever it runs.

---

## 2. THE DECISIVE MEASUREMENT — where the market was at the decision instant

### 2.1 Definition (decision-time information only)

```
d      = risk_distance = |entry_price − stop_loss|
mkt_r  = (P − entry_price)/d   for LONG        P = close of the M1 bar stamped decision − 1 min
       = (entry_price − P)/d   for SHORT         (open-stamped ⇒ this bar closes AT the decision)
```

`mkt_r > 0` ⟺ the limit rests on the correct side; `mkt_r = 0` ⟺ the order is at the market;
`mkt_r < 0` ⟺ already through the limit; **`mkt_r ≤ −1` ⟺ the market is already at or beyond the
STOP price.** Every input is available before the order is sent.

### 2.2 The dose–response — the cliff is at the STOP, not at zero

| `mkt_r` at decision | n | engine gross R | win % |
|---|---:|---:|---:|
| ≤ −3 | 3,005 | **−1.0000** | **0.0** |
| −3 … −1 | 511 | **−0.9643** | 0.6 |
| −1 … −0.5 | 236 | −0.5643 | 12.7 |
| −0.5 … −0.25 | 407 | −0.2729 | 27.5 |
| −0.25 … −0.1 | 335 | −0.1169 | 35.5 |
| −0.1 … 0⁻ | 287 | −0.1434 | 35.5 |
| **= 0 (at market)** | **14,911** | **−0.0904** | 39.5 |
| 0⁺ … +0.1 | 320 | −0.1220 | 40.0 |
| +0.1 … +0.25 | 481 | −0.1743 | 34.9 |
| +0.25 … +0.5 | 840 | −0.1361 | 39.2 |
| +0.5 … +1 | 1,715 | −0.1405 | 37.6 |
| +1 … +2 | 2,422 | −0.0919 | 42.9 |
| > +2 | 2,171 | −0.0613 | 47.4 |

**The discontinuity is at `mkt_r = −1`, the stop price** — not at zero. Above it the book is flat
between −0.06 and −0.17 with no structure; below it the outcome collapses to a deterministic −1.
There is no gradual "the further through the market, the worse" effect and **no evidence that
ordinary marketability costs anything**: the small `−1 … 0` cohort (1,265 rows, 4.58 %) is worth
only −0.0117 R/pool-trade. **One cliff, one defect.**

### 2.3 What the past-stop population is

| | value |
|---|---:|
| n | **3,516 (12.72 % of the pool)** |
| `mkt_r` mean / median | **−8.859 / −7.577** |
| `mkt_r` p05 / p95 | −19.599 / −1.697 |
| engine gross | **−0.9948** |
| win rate | **0.085 %** (3 winners in 3,516) |
| total R booked | **−3,497.7** |
| median risk distance as % of price | **0.0499 %** (vs 0.1025 % at market, 0.0937 % resting) |
| mean frozen cost | 0.6687 R |

**[V1]**, from the path side and independently: the same population reached at path bar 1 numbered
3,696, with `fav_at_touch` median −7.19 R, p05 −19.23, worst −26.33, and first touch at bar 1 for
99.9 % of rows. **93.21 % of V1's population is confirmed past-stop at the decision instant with no
look-ahead at all.** V1 also refuted the benign reading directly: the first path bar is the very
next minute for 96.13 % of them, and the untakeable share runs 9.0–21.3 % across **all 24 decision
hours** with no session clustering.

### 2.4 The mechanism — the level is abandoned

Walking backward through the raw M1 series to the most recent bar whose `[low, high]` contains
`entry_price`, over the 3,516 past-stop rows:

| | value |
|---|---:|
| level found within the prior 1,440 bars | **44.34 %** |
| **level never traded in the prior 1,440 bars** | **55.66 %** |
| lag p25 / **median** / p75 | 149 / **499 bars (8.3 h)** / 928 |
| lag mean | 560.6 bars |

By family:

| family | n | share of past-stop | never traded in prior 24 h | median lag |
|---|---:|---:|---:|---:|
| **`current_breaker_re_entry`** | **3,467** | **98.61 %** | **56.42 %** | **521 bars (8.7 h)** |
| `current_ob_retest` | 48 | 1.37 % | 0.00 % | 15 bars |
| `current_fvg_fill` | 1 | 0.03 % | — | — |

**This is one generator emitting one kind of stale level.** `current_breaker_re_entry` quotes a
breaker level price abandoned a median of **8.7 hours** earlier, more than half of them at a price
the market has not traded in a day — and the engine books each as a trade that instantly stops out.

---

## 3. THE GATING QUESTION — METHOD 4, on the tradeable set

**n = 23,884 filled rows** (pool minus born_past_stop), walked at `policy_target_r` / −1R from the
fill bar:

| exit reason | n | share of filled | mean R |
|---|---:|---:|---:|
| **stop** | 12,299 | 51.50 % | −1.000 |
| **mark_at_horizon** | **7,844** | **32.84 %** | **+0.237** |
| **target** | 3,709 | 15.53 % | **+2.002** |
| same-bar conservative stop | 32 | 0.13 % | −1.000 |

**Winners only:**

| winner exit | n | share of winners | mean R | R contribution per filled trade |
|---|---:|---:|---:|---:|
| target | 3,709 | **43.55 %** | +2.002 | +0.311 |
| **mark_at_horizon** | **4,807** | **56.45 %** | **+0.593** | +0.119 |

Book: walked gross **−0.1274**, win **35.66 %**, mean winner **+1.206**, mean loser **−0.867**,
realized payoff **1.392 : 1** against a declared 2 : 1, breakeven win **41.80 %**.

**That is the whole answer to the gating question.** The mean winner of +1.04–1.21 R is the mix of
a full 2R (43.6 % of winners) and a 2-hour mark (56.4 %). **Nothing cuts a winner — the wall
arrives.** The realized 1.39 : 1 payoff is not a policy defect; it is 56 % of winners being valued
mid-flight.

**Sub-target winners** (V2 measurement, born_resting arm): n = 3,099, mean **+0.590**, **99.90 %
exit reason `mark_at_horizon`**, MFE median +0.962. **Only 0.097 % had an MFE that reached the
target inside the window** — as it must be, since the walk exits at first touch. *(V1 §5 reported
16.26 % here; that figure measured MFE across the whole path including pre-fill bars, and is
superseded.)*

**The honest size of the wall.** Continuing marked trades into the raw M1 for up to 24 h past the
wall (V2 arm, n = 4,897 marked born_resting trades):

| | n | share |
|---|---:|---:|
| eventually reach target | 2,023 | 41.31 % |
| eventually stop out | 2,584 | 52.77 % |
| still open at 24 h | 290 | 5.92 % |

mark at the wall **+0.2551** → resolved **+0.3030**; book −0.0460 → −0.0290, **+0.0170 R/filled
trade.** **[V1]** pool-wide against unbounded M1: −0.24143 → −0.21749, **+0.02394**, with the
exit-class census by horizon:

| horizon | target | stop | mark at horizon | R/trade | Δ vs engine |
|---|---:|---:|---:|---:|---:|
| 120 min | 3,620 | 15,691 | 8,073 | −0.23811 | +0.00333 |
| 240 min | 5,185 | 17,962 | 4,236 | −0.23681 | +0.00462 |
| 480 min | 5,944 | 19,019 | 2,419 | −0.23365 | +0.00778 |
| 1,440 min | 6,510 | 19,670 | 1,202 | −0.22751 | +0.01393 |
| unbounded | 7,104 | 20,159 | 119 | −0.21749 | **+0.02394** |

and of 7,954 resolving marks **56.19 % become stops**. **Hypothesis (A) is real, is a genuine
contract rather than a bug, and is worth +0.017 to +0.024 R/trade.**

---

## 4. METHOD 5 — full stops, money on the table

On the tradeable set's stops (n = **12,299**), MFE between the fill bar and the stop:

| | value |
|---|---:|
| **median** | **+0.2391 R** |
| p75 / p90 | +0.624 / +1.134 |
| share MFE ≥ 0.5 R | 31.30 % |
| share MFE ≥ 1.0 R | **12.96 %** |

**[V1]** on all 15,057 pool stops: **49.6 % are gap rows (7,464)**, median MFE **+0.1163 R**,
p25/p75/p90/p95 −0.9224/+0.4257/+0.8883/+1.2594, MFE ≥ 0.25 R 34.69 %, ≥ 0.5 R 21.04 %, ≥ 1 R
**8.19 %**, ≥ 2 R 0.39 %. Hindsight ceilings (perfect foresight, **not policies**): **+0.0892**
R/pool-trade at a 1R exit whenever MFE ≥ 1R, **+0.1718** at a 0.5R exit whenever MFE ≥ 0.5R.

**There is no large give-back population.** The median genuine stop never went more than 0.24 R in
favour. The "winners give money back" story is refuted at n = 12,299.

---

## 5. THE FINDING THAT REACHES A LIVE FACTORY CANDIDATE

`CQ_CURRENT_BREAKER_REPAIR_TRADES_V1` is the inverted-`current_breaker_re_entry` candidate standing
at the **V27** family tip (`phase18/receipts/CANDIDATE_FAMILY_V27.json`), published at **+11.9 net
R/trade on TRAIN and January VAL**, gate NOT_EVALUABLE at one fold of three. All **4,263** of its
trades join to this pool on `source_candidate_id` with **0 unmatched**. Split by the **no-look-ahead**
born state of the source candidate:

| born state at decision | n | share | `r_gross` | **`grid_net_r`** | outcome mix | win % | **contribution to +11.901** |
|---|---:|---:|---:|---:|---|---:|---:|
| **born_past_stop** | **3,467** | **81.33 %** | +17.820 | **+15.127** | 2,908 TARGET / 188 STOP / 371 HORIZON | **83.88** | **+12.303** |
| **born_resting** | **596** | **13.98 %** | **−0.713** | **−2.644** | 6 TARGET / 583 STOP / 7 HORIZON | **1.01** | **−0.370** |
| born_marketable | 200 | 4.69 % | +1.665 | −0.677 | 8 TARGET / 144 STOP / 48 HORIZON | 4.00 | −0.032 |
| **total** | 4,263 | | +14.471 | **+11.901** | | | |

**103.37 % of the candidate's entire headline comes from trades whose entry level had already
breached its own stop at the decision instant.** On the 596 trades that were legitimately takeable
it books **−2.644 R/trade** — it does not merely lose its edge, it **inverts**, winning **1.01 %**
of the time against **83.88 %** on the artifact rows.

**Anchor-invariant.** Under the V2 (look-ahead) anchor the same table gives 81.40 % / +15.127 /
83.89 % and 13.96 % / −2.659 / 0.84 %, artifact share **103.46 %**. The result does not depend on
the correction in §0.1 — a level 7.6 stop-widths away does not move in one minute.

**Why the arithmetic works.** Inverting the side of a trade inverts its born state: a level 8.9
stop-widths through the market *against* the original direction is 8.9 stop-widths *in favour of*
the inverted one. The inverted trade is entered at a price the market abandoned a median **8.7
hours** earlier and is **already deep in profit at the instant of entry**. Regressing `r_gross` on
the decision-time staleness `−mkt_r` over those 3,467 rows: **Pearson r = 0.4637, r² = 0.2150, OLS
slope 0.4669**, mean staleness **+8.953 R** against mean `r_gross` **+17.821**; median `r_gross`
exactly **20.0**. Staleness is the enabling condition, not a 1:1 identity — the born-state split
alone is unambiguous.

**Underlying family, by born state** (V2 anchor, source-pool side, n = 4,260 anchored):

| born state | n | engine gross | win % | `policy_target_r` mean / median / max |
|---|---:|---:|---:|---|
| born_past_stop | 3,470 | **−0.99914** | 0.03 | 2.221 / 2.0 / **431.49** |
| born_resting | 592 | **+0.03326** | **46.62** | 2.036 / 2.0 / 11.27 |
| born_marketable | 197 | −0.34887 | 19.80 | 6.444 / 2.0 / **505.47** |

**The family's famous 7.4 % win rate is not a strategy result.** Strip the 81 % of rows that were
never takeable and the underlying family is ordinary: at the V3 anchor its 793 surviving rows book
**−0.0824 engine / −0.1058 walked at a 36.4 % win rate** — mid-pack, not an inverse signal.

**V1 predicted this and prescribed the test; V2/V3 ran it with a decision-time classifier and the
candidate collapses.** This is the single most consequential number in the receipt.

---

## 6. PER-FAMILY, excluding the past-stop artifact

`walk_ex` = filled rows only, walked at `policy_target_r`/−1R inside the 120 m wall, past-stop rows
removed. Sorted worst to best.

| family | pool n | pool eng. | past-stop % | n ex | eng. ex | **walk ex** | win % ex |
|---|---:|---:|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | 1,993 | −0.1820 | 0.0 | 1,993 | −0.1820 | **−0.2789** | 24.6 |
| `cross_asset_lead_lag` | 2,083 | −0.1307 | 0.0 | 2,083 | −0.1307 | −0.2012 | 29.2 |
| `current_fvg_fill` | 7,136 | −0.1404 | 0.0 | 7,135 | −0.1403 | −0.1398 | 34.7 |
| `current_breaker_re_entry` | 4,260 | **−0.8256** | **81.4** | 793 | **−0.0824** | −0.1058 | 36.4 |
| `session_open_range_break` | 987 | −0.0747 | 0.0 | 987 | −0.0747 | −0.1047 | 40.7 |
| `displacement_continuation` | 4,465 | −0.0888 | 0.0 | 4,465 | −0.0888 | −0.1035 | 39.0 |
| `volatility_compression_expansion` | 605 | −0.0868 | 0.0 | 605 | −0.0868 | −0.0936 | 43.3 |
| `liquidity_sweep_reclaim` | 4,475 | −0.0415 | 0.0 | 4,475 | −0.0415 | **−0.0717** | 36.2 |
| `current_ob_retest` | 1,340 | −0.1046 | 3.6 | 1,292 | −0.0736 | **−0.0561** | 43.7 |
| `regime_transition_break` | 297 | −0.0067 | 0.0 | 297 | −0.0067 | **−0.0202** | 49.1 |

**No family is gross-positive once the artifact is removed and the fill is required.** The best
three are `regime_transition_break` (−0.0202, n = 297, 49.1 % win), `current_ob_retest` (−0.0561,
n = 1,292, 43.7 %) and `liquidity_sweep_reclaim` (−0.0717, n = 4,475, 36.2 %). The artifact is
concentrated in exactly one family; **the other nine are unaffected by it and their published
economics do not change.**

**Per-symbol** — the artifact is instrument-specific, which is itself evidence it is not a market
phenomenon:

| symbol | pool n | eng. | **past-stop %** | eng. ex | walk ex | win % ex |
|---|---:|---:|---:|---:|---:|---:|
| GBPUSD | 1,474 | −0.5312 | **44.2** | −0.1603 | −0.2079 | 31.3 |
| EURJPY | 1,080 | −0.4320 | **41.9** | −0.0233 | −0.0708 | 39.3 |
| USDCAD | 1,243 | −0.4692 | **35.8** | −0.1770 | −0.2052 | 33.4 |
| UK100 | 2,004 | −0.4190 | **30.1** | −0.1793 | −0.2094 | 30.7 |
| EURGBP | 828 | −0.2952 | 19.6 | −0.1237 | −0.1871 | 32.1 |
| AUDJPY | 758 | −0.2293 | 15.6 | −0.0872 | −0.1953 | 34.1 |
| USDCHF | 906 | −0.1357 | 14.6 | **+0.0118** | −0.0491 | 39.5 |
| SPX500 | 1,943 | −0.2134 | 11.6 | −0.1099 | −0.1369 | 36.1 |
| GBPJPY | 777 | −0.1845 | 11.3 | −0.0803 | −0.1212 | 35.1 |
| EURUSD | 808 | −0.2029 | 9.9 | −0.1153 | −0.1022 | 37.6 |
| NZDUSD | 813 | −0.1349 | 9.3 | −0.0457 | −0.1464 | 35.0 |
| NAS100 | 1,622 | −0.3456 | 8.6 | **−0.2842** | **−0.3080** | 28.0 |
| UKOIL_cash | 786 | −0.1197 | 7.0 | −0.0535 | −0.0988 | 37.7 |
| AUDUSD | 654 | −0.0903 | 6.4 | −0.0278 | −0.0702 | 39.9 |
| US30_cash | 1,563 | −0.2026 | 5.4 | −0.1567 | −0.1808 | 33.4 |
| JP225 | 1,348 | −0.0937 | 4.8 | −0.0478 | −0.0865 | 37.2 |
| BTCUSD | 1,203 | −0.0494 | 2.2 | −0.0284 | **−0.0217** | 43.7 |
| ETHUSD | 934 | −0.1901 | 1.9 | −0.1742 | −0.1755 | 33.7 |
| XAUUSD | 2,356 | −0.0870 | 1.1 | −0.0764 | −0.0821 | 35.1 |
| USOIL_cash | 733 | −0.1508 | 1.1 | −0.1414 | −0.1840 | 37.2 |
| GER40 | 1,412 | −0.0115 | 0.9 | −0.0023 | −0.0290 | 39.0 |
| XAGUSD | 928 | −0.1146 | 0.3 | −0.1117 | **−0.0048** | 39.4 |
| USDJPY | 893 | −0.0945 | 0.1 | −0.0934 | −0.0589 | 36.3 |
| CHFJPY | 575 | −0.0755 | 0.0 | −0.0755 | −0.0915 | 38.0 |

GBPUSD carries **44.2 %** past-stop rows and CHFJPY **0.0 %** — a spread no market mechanism
explains. **[V1]** measured the same concentration from the path side (GBPUSD 44.8 %, EURJPY 42.0 %,
USDCAD 36.2 %, UK100 30.5 %) and read it the same way: instruments whose declared stop is tightest
relative to M1 noise. **NAS100 is the worst clean symbol at −0.308 walked, and it carries almost no
artifact** — a genuinely bad instrument, not a defective one.

---

## 7. WHERE THE POOL STANDS, NET — stated honestly

Frozen cost, and with the swarm's established 7.3–8.5× spread over-charge divided out (labelled
**[INDICATIVE]** — this lane did not re-measure the over-charge). Values marked † use the V2 anchor
and are quoted only for the cost sensitivity, not for the gross split.

| book | n | gross | net @ frozen | net @ spread ÷7.3 **[IND]** | net @ ÷8.5 **[IND]** |
|---|---:|---:|---:|---:|---:|
| pool | 27,641 | −0.2172 | −0.8803 | **−0.3935** | −0.3826 |
| **pool ex past-stop** | **24,125** | **−0.1039** | — | — | — |
| † born_resting (V2 anchor) | 14,086 | −0.0009 | −0.6744 | −0.1731 | −0.1619 |
| † born_resting + `cost_r ≤ 0.15` | 4,313 | +0.0024 | −0.0888 | −0.0494 | — |
| † born_resting + `cost_r ≤ 0.05` | 661 | +0.0312 | −0.0122 | **+0.0049** | — |

Mean frozen cost by born state (V3 anchor): at-market **0.5522**, resting **0.8716**, marketable
0.6441, **past-stop 0.6687**. Median risk distance as a fraction of price: at-market 0.1025 %,
resting 0.0937 %, marketable 0.1865 %, **past-stop 0.0499 %** — the artifact population's geometry
is **half as wide** as everything else, which is why its R-denominated cost is inflated too.

**The cost gate has been a proxy for the artifact.** Sweeping `cost_r ≤ t` on the raw pool moves
gross −0.2386 → −0.0974 (at t = 0.15); on the V2 clean population it moves only −0.0460 → +0.0024.
**Cost filtering buys ~3× more on the unfiltered pool than on a fill-clean one** — because
past-stop rows carry the tightest geometry and therefore the highest `cost_r`, so the cost gate
screens them out **for the wrong reason** while also screening out good rows. **[V1]** measured the
same thing from the blocker side: `cost_authority` (73.9 % of the pool) holds **93.40 %** of the
untakeable rows, and the three classes that turn positive under repair are the three fill/timing
gates — `execution_fillability` **+0.1044** (n 449), `daily_lockout` **+0.1310** (n 46),
`marketable_guard` **+0.0623** (n 73), the last of which carries **53.21 %** untakeable rows, 3×
any other class.

**Stated plainly: the repair does not make the pool positive.** It moves the gross deficit from
−0.2172 to −0.1039 and leaves a residual dominated by a cost term whose own error bar (7.3–8.5×) is
larger than the remaining gap. **The gross question and the cost question are now separable, and
they were not before.** **[V1]** adds that under a strict-limit contract unfilled orders cost
nothing — the engine has never modelled that, charging cost on 99.12 % of rows where a strict limit
fills 83.12 %.

---

## 8. What later waves should do

1. **Kill or quarantine CQ's inverted-breaker candidate before any further work on it (§5).** It
   stands at the V27 family tip. 103.37 % of its headline is the artifact; on takeable trades it
   books −2.644 R/trade at a 1.01 % win rate. Anchor-invariant. Already run — this is a yes/no
   result, not a proposal.
2. **Find out why `current_breaker_re_entry` emits levels 8.7 hours stale.** 98.61 % of all
   past-stop rows, 56.4 % quoting a price not traded in the prior 24 h. **One generator, one bug**
   — and it accounts for 58.25 % of the January pool's entire gross deficit.
3. **Carry the decision-time classifier to February / March / April / May.** It needs only the pool
   and the raw M1 bars; `w0cap2_decision_anchor.py` is 60 lines and runs in **2.4 s** over 27,658
   rows. Every published per-family and per-symbol number in this programme is computed on a
   population that is **12.72 % past-stop at emission.**
4. **Use `mkt_r_prev_close`, never the decision-minute bar (§0.1).** Bars are open-stamped; the
   decision-minute bar is post-decision. This lane got it wrong once and the error manufactured
   +0.21 R/trade of fictitious edge. Any lane touching the M1 series should read §0.1 first.
5. **Do not spend effort on the horizon.** Measured twice by two methods: +0.017 to +0.024 R/trade.
   It is a real contract, not a bug, and it is the smallest thing in this receipt.
6. **`marketability` per se is not a defect.** The `−1 < mkt_r < 0` cohort is 4.58 % of the pool and
   worth −0.0117 R/pool-trade. V2's "sub-spread placement" defect was an artifact of its own anchor
   and is retracted. Do not build a repair for it.
7. **The honest residual is −0.1039 gross.** No family is positive once the artifact is removed and
   the fill is required. The best clean families are `regime_transition_break` (−0.0202, n = 297),
   `current_ob_retest` (−0.0561, n = 1,292) and `liquidity_sweep_reclaim` (−0.0717, n = 4,475).

---

## 9. Artifacts

| file | what |
|---|---|
| `w0-capture_RESULT.md` / `.json` | this receipt; the JSON merges every V2/V3 measurement plus V1 verbatim |
| `w0-capture_RESULT_V1_PRIORAGENT.md` / `.json` | the first agent's receipt, preserved unchanged |
| `w0cap2_decision_anchor.py` → `w0cap2_DECISION_ANCHOR_V1.jsonl.gz` | decision-time market anchor, 27,641 rows, both anchors per row |
| **`w0cap2_nla_full.py` → `W0CAP2_NOLOOKAHEAD_FULL_V1.json`** | **the V3 primary: born census, dose–response, staleness, per family/symbol, METHOD 4/5** |
| **`w0cap2_cq_nla.py` → `W0CAP2_CQ_NOLOOKAHEAD_V1.json`** | **the V3 CQ result (§5)** |
| `w0cap2_nolookahead.py` → `W0CAP2_NOLOOKAHEAD_V1.json` | anchor sensitivity, both anchors side by side |
| `w0cap2_crux.py` → `W0CAP2_CRUX_V1.json` | V1's untakeable population re-tested at the decision bar |
| `w0cap2_born.py` → `W0CAP2_BORN_V1.json` | guard miss rate, coherence, phantom winners *(V2 anchor)* |
| `w0cap2_stale.py` → `W0CAP2_STALE_V1.json` | level staleness per born state *(V2 anchor)* |
| `w0cap2_winners.py` → `W0CAP2_WINNERS_V1.json` | METHOD 4/5 *(V2 anchor)* |
| `w0cap2_final.py` → `W0CAP2_FINAL_V1.json` | cost by born state, horizon lift past the wall |
| `w0cap2_sweep.py` → `W0CAP2_SWEEP_V1.json` | decision-time filter sweeps *(V2 anchor)* |
| `w0cap2_mech.py` → `W0CAP2_MECH_V1.json` | through-market distance in spread units *(V2 anchor)* |
| `w0cap2_cq.py` → `W0CAP2_CQ_V1.json`, `W0CAP2_CQJOIN_V1.json`, `W0CAP2_SMOKINGGUN_V1.json` | CQ, V2 anchor |
| `W0CAP_*.json`, `W0_CAPTURE_*.json` | V1 and PRIOR-M1 artifacts, preserved |

**Superseded / retracted.** From V2: the born_resting **−0.0009** headline, the **+0.1896–0.2166**
recoverable figure, and "DEFECT 1 — sub-spread limit placement, −0.0769 R/pool-trade" — all carried
60 s of look-ahead (§0.1). From V1: *"16.26 % of sub-target winners reached 2R inside the window"*
(measured MFE over the whole path including pre-fill bars; the coherent figure is **0.097 %**), and
`W0_CAPTURE_HORIZON_V1.json → B_exit_policy_cost_R_per_trade = 0.2579` (a fill-blind artifact).
**V1's untakeable population and its prescribed CQ test are confirmed, not superseded.**
