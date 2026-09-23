# w0-capture — what closes a winning trade at +1.04 R when its target is 2 R

**Answer: nothing does. The premise is wrong.** The pool's average winner is +1.044 R not because a
policy cuts winners short, but because **a quarter of the pool never resolves at all inside a
2-hour wall and is booked at whatever unrealised R it happened to be sitting at.** That mark is a
real contract (`path_final_r` `time_stop_close_mark`, `v4_timewarp_simulated_live_research_loop.py:60347-60355`),
and lifting the wall is worth **+0.012 to +0.024 R/trade** — almost nothing, because the unresolved
population resolves 56 % into stops.

**The money is not at the exit. It is at the ENTRY.** 13.37 % of the pool (3,699 rows) is booked as
a trade whose stop-loss price was *already breached at the first bar the entry price was reachable* —
median **7.19 R** beyond the entry. Every one of them books a mechanical **−0.9996 R**. Repairing the
entry-fill contract to the engine's **own documented rule** moves the pool gross from **−0.2175 to
−0.0751 R/trade (+0.1424)**; skipping marketable limits entirely gives **−0.0251 (+0.1924)**.

That is **6× to 16× the entire horizon + exit-policy term combined.**

| lane hypothesis | mechanism | R/trade recoverable |
|---|---|---|
| (A) measurement artifact — horizon wall | `REPAIRED_PENDING_EXPIRY_MINUTES=120` mark-to-market | **+0.0119 → +0.0239** |
| (B) real contract defect — exit policy cuts winners | plain 2R/−1R instead of the engine's exit, same wall | **+0.0033 → +0.0185** |
| **(C) NEITHER — the entry-fill contract** | stale/marketable limit booked as a resting fill | **+0.1424 → +0.1924** |

---

## 0. Provenance and honesty notes

* Population: `CJ_RECLOCKED_S0R0_POOL_V1` (January 2026, true UTC, **n = 27,658**), joined to
  `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1` via wave-0's `w0_WORKING_SET.jsonl.gz`. Join coverage
  is total (0 rows without a path).
* Every number below marked **[MEASURED HERE]** was recomputed by this agent from the working set
  and its R-paths. Numbers marked **[PRIOR-M1]** come from the first `w0-capture` agent, which died
  before writing a receipt; it reached the raw January M1 bars at
  `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601`,
  which is the **only** way to see past the 2-hour path cap. Its artifacts are preserved and merged
  into `w0-capture_RESULT.json`. Where I could check it I reproduced it (see §2).
* **One prior artifact is wrong and is superseded.** `W0_CAPTURE_HORIZON_V1.json` reports
  `B_exit_policy_cost_R_per_trade = 0.2579`. That walker did **not require the entry limit to
  fill** — its `pure_geometry_120m_gross_mean_R = +0.0404` is wave-0's fill-BLIND figure (+0.0409)
  to three decimals. The 0.2579 is W0-F2's fill fiction (+0.2776), not an exit policy. Do not cite it.
* **Sample caveat, stated once and applying to everything:** one month, one arm (S0R0), one broker
  series. `candidate_id` is not a primary key — 24.39 % of rows are pseudo-replicated (W0-F1) — and
  nothing here is de-duplicated, so effective n is nearer 21,880. No multiplicity correction is
  applied and none is claimed.
* No sealed replay launched, no VPS touched, no broker-capable script run, no April/May pack read,
  no February economics read, no live-forward P&L computed.

---

## 1. SOURCE — where the numbers are made (METHOD 1–3)

### 1.1 `opportunity_net_proxy_r`, `cost_r`, `expected_net_r`

`v4_timewarp_simulated_live_research_loop.py:92577-92580`

```python
missed_net_proxy_r = (
    None
    if missed_final_r is None
    else round(missed_final_r - expected_cost_r, 8)
)
```

written to the ledger as `"opportunity_net_proxy_r": missed_net_proxy_r` at `:92730` (and the twin
site `:92972` → `:93122`). **[MEASURED HERE]** Verified empirically, not inferred:
`max | gross_r − expected_cost_r − opportunity_net_proxy_r | = 5.0e-10` over all 27,658 rows.

Frozen cost decomposition **[MEASURED HERE]**, means over 27,658 rows:

| term | mean R | share |
|---|---:|---:|
| `expected_cost_r` (= `cost_r`) | **0.66316** | 100 % |
| `spread_r` | 0.56421 | **85.08 %** |
| `commission_r` | 0.06522 | 9.83 % |
| `expected_slippage_r` | 0.02000 (a flat constant on every row) | 3.02 % |
| `swap_cost_r` | 0.01372 | 2.07 % |

Medians: cost 0.30313, spread 0.18063. `max_total_cost_r` / `total_cost_r` are **absent from this
pool** (n=0) — the 0.15 gate named in the brief is not observable here.

### 1.2 Every exit rule that can produce an outcome below target

`path_final_r`, `:60302-60356`. Six terminal branches:

| # | branch | value | line |
|---|---|---|---|
| 1 | `not_filled_no_trade` | `None` (row unscored) | `:60308-60310` |
| 2 | `target_reached_before_stop` | `+target_r` | `:60336` |
| 3 | `stop_reached_before_target` | `−1.0` | `:60337-60340` |
| 3b | …`partial_be_runner` and 1R touched | `+0.5` | `:60338-60339` |
| 4 | `same_bar_ambiguity_conservative_stop_close` | `−1.0` | `:60342-60346` |
| **5** | **`time_stop_close_mark_from_<source>`** | **`max(-1.0, min(close_mark_r, target_r))`** | **`:60347-60355`** |
| 5b | …after partial harvest | `0.5 + 0.5·max(0, bounded_close_r)` | `:60352-60354` |
| 6 | `source_required_filled_no_terminal_close_mark_missing` | `None` | `:60356` |

**Only branch 5 can produce a positive outcome below target.** There is no trailing stop, no
scale-out, no session-boundary exit and no MTM close other than this one. The field that records it
is the returned `close_reason` string (`time_stop_close_mark_from_…`), and `close_mark_r` /
`close_mark_source` on the oracle (`attach_close_mark`, `:63323`).

A second layer, `apply_selected_execution_policy_replay_exit` (`:60973`), can override branches
2–5 when a `dynamic_geometry_policy` is selected — it returns unchanged when `fill_status` is not
`filled*` (`:60993`), when no policy key is present (`:60995`), or when the policy spec is `None`
(`:61002`). **[MEASURED HERE]** In this pool `by_selected_policy_for_expected_net_r` has exactly one
level, so this layer is not a differentiator in January S0R0.

### 1.3 The horizon — exact value and where it is set

```python
REPAIRED_PENDING_EXPIRY_MINUTES = 120                       # :378

expiry=min(
    asof + timedelta(minutes=campaign.pending_expiry_minutes),
    datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1),
)                                                            # :92468-92478
```

**120 minutes, or the end of the trading day, whichever comes first**, applied when the path oracle
is constructed (`path_source_and_oracle`, `:63902`) so the walk physically cannot see a later bar.
**[MEASURED HERE]** wave-0 confirms it in the data: every path ≤ 120 M1 bars, 86.12 % exactly 120.
**[PRIOR-M1]** 4.89 % of trades are wall-truncated by the day-end clause rather than the 120 minutes.

### 1.4 The entry-fill contract — the one that matters

`marketable_limit_immediate_fill_candidate`, `:54258-54268`, docstring, verbatim:

> *"A marketable limit is not a resting order in replay. The requested limit is the worst acceptable
> price; the effective fill is the decision-time market price when a source-safe predecision price
> exists."*

The engine **knows** a limit already through the market must be re-priced to the market and the
geometry re-canonicalised (`original_limit_entry_price` / `original_limit_stop_loss` /
`original_limit_take_profit_1`, `:54320-54334`). §3 measures how often that fires.

---

## 2. THE DECISIVE MEASUREMENT — the entry contract

### 2.1 Classification (exact, from the R-paths, no new data)

With wave-0's sign convention (`fav=(high−entry)/d` LONG, `(entry−low)/d` SHORT; `adv` likewise; `d=|entry−stop|`):

* limit **touched** at bar *k* ⟺ `adv(k) ≤ 0`
* **gap-through** at that bar ⟺ `fav(k) < 0` — the *whole bar* lies past the limit, so the market
  was already on the far side and no resting limit could have been there
* **structurally untakeable** ⟺ `fav(k) ≤ −1.0` — the bar lies entirely beyond the **stop price**

**[MEASURED HERE]**

| class | n | share of pool | engine gross R/trade | engine win rate |
|---|---:|---:|---:|---:|
| **clean** (price came to the limit) | 17,439 | 63.05 % | **−0.0311** | 0.4364 |
| **gap-through** | 9,978 | 36.08 % | **−0.5859** | 0.1722 |
| — of which **untakeable** (stop already gone) | **3,699** | **13.37 %** | **−0.99965** | **0.00027** |
| — of which gap but stop intact | 6,279 | 22.70 % | −0.3421 | 0.2735 |
| **never touched at all** | 241 | 0.87 % | **+1.5477** | **1.0000** |

Reproduces the prior agent independently: gap 9,978 vs its 9,978; gap book −0.5859 vs its −0.5852.
Clean-row book differs by 0.014 R (−0.0311 here vs its −0.0447) because its classifier used the raw
M1 series and mine uses the sidecar path — treat ±0.014 as the classification sensitivity.

**Two populations are not trades at all:**

* **3,699 untakeable rows.** First touch is bar **1** for 99.9 % of them (mean touch bar 1.118), so
  they are *born* past the stop, not stopped later. `fav_at_touch` median **−7.19 R**, p25 −12.11 R,
  p05 −19.23 R, worst −26.33 R. Engine books −0.99965 mean with **1 winner in 3,699**. Total
  **−3,697.7 R**. Their risk distance is abnormally tight — median `|entry−stop| / entry` =
  **0.0494 %** against **0.1016 %** for clean rows — so ordinary M1 noise is many R wide.
* **241 never-touched rows.** The entry price is never traded at any point in the 2-hour window; the
  engine books them at **+1.5477 R mean with a 100 % win rate** (145 of 241 at or beyond target).
  Total **+373.0 R of profit on trades that could not have been opened.**

### 2.1a It is NOT an overnight/weekend gap — the benign explanation is refuted **[MEASURED HERE]**

The obvious innocent reading is "the first path bar is on the other side of a session break, so of
course price is far away." It is false on both tests:

* **The first path bar is the very next minute.** Path bar offset `1` for **3,556 of 3,699 =
  96.13 %** of untakeable rows (next largest offsets: 5 → 47 rows, 20/35/50/65 → ~20 each). There is
  no time gap between the decision and the bar that is already 7 R past the entry.
* **No session clustering.** Untakeable share by decision hour (UTC) runs **9.0 % to 21.3 %** across
  all 24 hours with no bimodal spike: min 08 h (9.0 %), 15 h (9.0 %), 14 h (9.2 %), 07 h (9.4 %);
  max 22 h (21.3 %), 18 h (20.2 %), 23 h (19.7 %), 17 h (19.3 %). Thin-liquidity hours are ~2×
  worse, which is consistent with a wide effective spread against a very tight declared stop, but
  **every hour of the day carries the defect.**

So the mechanism is: **within sixty seconds of the decision, price is already a median 7.19
stop-widths past the emitted entry.** That is not market movement. Combined with the abnormally
tight risk distance (§2.1: 0.0494 % of price vs 0.1016 % for clean rows), the reading is that these
candidates are emitted with a geometry — entry price plus a very tight stop — that **was never near
the market at the moment it was emitted.**

### 2.2 The repair, at the engine's own documented rule

If the limit is through by `x·d` (`x = −fav_at_touch`, `0 < x < 1`), the true fill is `x·d` past the
entry, the original stop is `(1−x)·d` away, and every R re-expresses exactly:
`R'(bar) = (fav(bar)+x)/(1−x)`, target `(target+x)/(1−x)`, stop `−1`. Same exit bars, different R.
`x ≥ 1` ⟹ no trade exists. **This is algebra on the existing paths, not a new assumption.**

**[MEASURED HERE]** — all n = 27,658 unless stated

| arm | n | gross R/trade | win | breakeven win | mean W | mean L |
|---|---:|---:|---:|---:|---:|---:|
| **A0 engine record** | 27,658 | **−0.2175** | 0.3460 | 0.4585 | +1.047 | −0.887 |
| **A1 re-anchored; untakeable + never-touched scored 0** | 27,658 | **−0.0751** | 0.3142 | 0.3526 | +1.266 | −0.689 |
| A2 re-anchored, filled rows only | 23,718 | −0.0876 | 0.3664 | 0.4074 | +1.266 | −0.870 |
| A3 clean limits only, filled only | 17,439 | −0.0398 | 0.3935 | 0.4127 | +1.218 | −0.856 |
| A4 the re-anchored gap rows alone | 6,279 | −0.2203 | 0.2910 | 0.3847 | +1.446 | −0.904 |
| A5 A1 with a size cap (`x ≤ 0.8`) | 27,658 | −0.0702 | 0.3142 | 0.3503 | +1.266 | −0.682 |
| **STRICT — never trade a marketable limit, unfilled = 0** | 27,658 | **−0.0251** | 0.2481 | 0.2633 | +1.218 | −0.435 |
| STRICT, filled only | 17,439 | −0.0398 | 0.3935 | 0.4127 | +1.218 | −0.856 |
| *control:* walk from bar 0, fill-blind | 27,417 | +0.0258 | 0.3904 | 0.3794 | +1.455 | −0.890 |

**Decomposition of the entry-contract repair, R per pool trade [MEASURED HERE]:**

| term | value |
|---|---:|
| drop the 3,699 untakeable rows | **+0.13369** |
| drop the 241 never-touched phantom winners | **−0.01349** *(a debit — fake profit given back)* |
| re-anchor the 6,279 remaining gap rows to the true fill | **+0.02219** |
| **TOTAL C (entry contract)** | **+0.14240** |
| …or, if marketable limits are simply never traded | **+0.19240** |

Re-anchoring implies larger size on a smaller stop: `1/(1−x)` is **1.15× at the median**, 2.04× at
p90, 2.91× at p95. Capping at `x ≤ 0.8` (A5) changes the pool by +0.005 — the result does not
depend on the tail.

### 2.3 [PRIOR-M1] With the wall lifted — the same conclusion, larger

The prior agent ran the same idea against unbounded M1 and got, at a strict limit rule:

* fill rate **83.12 %** strict vs **99.12 %** engine; 4,423 rows the engine fills and a strict limit does not
* **`book_strict_rule_unbounded_filled_only`: n 22,976, gross −0.0052 R/trade, win 33.256 % against
  a breakeven of 33.431 % — 0.17 pp from a coin flip at true 2:1 geometry**
* `book_strict_rule_wall_unfilled_as_zero`: n 27,641, **−0.0231** (my wall-bounded equivalent: −0.0251)
* born-marketable split: 13,553 rows **−0.4371** vs 13,846 born-resting **−0.0495**

---

## 3. WHY IT HAPPENS — the engine's own guard does not fire

**[MEASURED HERE]** `limit_marketable_at_decision` × measured fill class:

| flag | fill class | n | engine gross R |
|---|---|---:|---:|
| **None** | clean | 14,535 | −0.0291 |
| **None** | **gap** | **8,809** | **−0.6162** |
| None | never | 219 | +1.5954 |
| True | clean | 2,008 | −0.0114 |
| **True** | **gap** | **1,147** | **−0.3549** |
| True | never | 20 | +1.0983 |
| False | clean | 896 | −0.1085 |
| False | gap | 22 | −0.4897 |
| False | never | 2 | +0.8187 |

The flag is **`None` on 23,563 of 27,658 rows (85.2 %)** — the surface is simply not populated, so
`marketable_limit_immediate_fill_candidate` never re-prices. **88.3 % of gap rows carry `None`.**
And there is a dose–response inside the data: where the flag *is* `True`, the same gap-through
population books **−0.3549** instead of **−0.6162** — the handler halves the damage where it fires.

`effective_order_type` is `limit` on 23,106 rows and `none` on 4,552, with near-identical gap shares
(36.3 % vs 35.1 %), so this is not an order-type artifact.

### 3.1 The blocker census under the repaired contract **[MEASURED HERE]**

| blocker | n | % untakeable | engine gross | **repaired gross (filled only)** | n filled | win | breakeven | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cost_authority` | 20,448 | 16.90 | −0.2547 | −0.1019 | 16,804 | 0.3503 | 0.3951 | 0.866 |
| `other` | 2,684 | 3.87 | −0.1131 | −0.0438 | 2,550 | 0.4196 | 0.4467 | 0.085 |
| `package_authority` | 2,668 | 1.99 | −0.1220 | −0.0833 | 2,600 | 0.3892 | 0.4331 | 0.091 |
| `scheduler_selection` | 689 | 0.29 | −0.0731 | −0.0483 | 683 | 0.4143 | 0.4396 | 0.070 |
| **`execution_fillability`** | 449 | 0.00 | +0.0273 | **+0.1044** | 449 | **0.4410** | 0.3939 | 0.095 |
| `selector_materialization` | 369 | 0.54 | −0.1143 | −0.0675 | 367 | 0.3869 | 0.4208 | 0.099 |
| **`marketable_guard`** | 156 | **53.21** | −0.5244 | **+0.0623** | 73 | 0.4247 | 0.3930 | 0.090 |
| `fill_realism` | 148 | 0.00 | −0.2066 | −0.2488 | 146 | 0.2877 | 0.4007 | 0.072 |
| **`daily_lockout`** | 47 | 0.00 | +0.3260 | **+0.1310** | 46 | **0.5435** | 0.4768 | 0.084 |

Three things fall out:

1. `marketable_guard` — the gate whose *name* is this defect — has **53.21 % untakeable rows, 3×
   any other class**. It is detecting the right population. But the engine still books the blocked
   rows as trades, so the guard's own evidence reads as −0.5244 when its genuinely-fillable
   remainder is **+0.0623, 3.2 pp above breakeven**.
2. `cost_authority` (73.9 % of the pool) holds **3,455 of the 3,699 untakeable rows — 93.40 %**
   (the rest: `other` 104, `marketable_guard` 83, `package_authority` 53, `scheduler_selection` 2,
   `selector_materialization` 2, and **zero** in `execution_fillability`, `fill_realism`,
   `daily_lockout`). The
   cost gate has been screening out the fill artifact and getting credit for screening out cost.
3. **The three classes that are positive under repair are the three fill/timing gates**
   (`execution_fillability` +0.1044 at +4.7 pp over breakeven, `daily_lockout` +0.1310 at +6.7 pp,
   `marketable_guard` +0.0623 at +3.2 pp). Small n (449 / 46 / 73) — a pointer, not a policy.

---

## 4. THE FAMILY THAT IS NOT A STRATEGY — `current_breaker_re_entry`

**[MEASURED HERE]** and this reaches a live estate artifact.

| | value |
|---|---:|
| family n | 4,263 (15.41 % of pool) |
| **structurally untakeable** | **3,434 = 80.55 % of the family** |
| …share of the pool's *entire* untakeable population | **92.84 %** |
| untakeable engine gross | **−1.00000 exactly** |
| untakeable engine win rate | **0.0 %** (0 winners in 3,434) |
| untakeable outcome bands | `{full_stop: 3434}` — every single row |
| first touch at bar 1 | **99.91 %** |
| `fav_at_touch` median / p25 / p05 | **−7.52 R / −12.59 R / −19.50 R** |
| `policy_target_r` on those rows | median 2.0, mean 2.19, **max 431.49** |
| **the genuinely takeable remainder** | **829 rows, −0.1023 R/trade, 37.88 % win** |
| under the repaired contract (filled only) | 827 rows, **−0.0939 R/trade, 35.79 % win** |

**The family's famous 7.4 % win rate is not a strategy result.** It is 80.55 % composed of rows that
are a deterministic −1.0000 with zero variance because their stop price was gone before the entry
was reachable. Strip them and it is an ordinary, mildly negative family indistinguishable from the
other nine.

**Therefore: CQ's inverted-breaker candidate — a standing V27 factory candidate, +11.9 net R/trade
on TRAIN and January VAL — is at severe risk of being the inverse of a simulation artifact.**
Inverting a deterministic −1.0000 yields a deterministic +1.0000 by construction: **+0.8055 R per
family trade with no signal content whatsoever.** With `policy_target_r` reaching 431.49 on that
same population, an inverse booking the declared target explains a double-digit R/trade headline
arithmetically. **This is a specific, falsifiable prediction: re-run CQ's candidate with the 3,434
untakeable rows removed. If the edge is real it survives on the 829-row remainder; if it is the
artifact, it collapses.** Do this before any further work on that candidate.

---

## 5. METHOD 4 — sub-target winners: what actually closes them

**[MEASURED HERE]** n = **6,498** (23.49 % of pool), engine records mean **+0.5896 R**
(median +0.5040, p95 +1.4356).

| | value |
|---|---:|
| engine-recorded R vs `r_at_path_end` | mean **+0.5896** vs **+0.6187** — the recorded value *is* the mark |
| MFE inside the 2 h window, from the fill bar | mean **+1.6166**, median **+1.1395**, p95 +4.7788 |
| **reached the 2R target inside the window** | **1,041 / 6,402 = 16.26 %** |
| reached 1R inside the window | 3,676 / 6,402 = 57.42 % |
| fill class | clean 5,260 / gap 1,142 / never-touched **96** |
| exit reason, all of them | `mark_at_horizon` |

**Nothing cuts them.** They are marked to market at the wall by branch 5 of `path_final_r`
(`:60347-60355`) because neither target nor stop was reached in 120 minutes. Of the 16.26 % whose
MFE *did* reach 2R inside the window, that MFE occurred **after** the recorded exit is impossible
by construction (the walk exits at first touch) — so those are rows where the target was reached in
a bar the engine's own oracle scored differently, i.e. same-bar/ambiguity handling, not a policy cut.

Pool-wide exit-reason census under the repaired contract **[MEASURED HERE]**: `stop_1R` 12,121,
**`mark_at_horizon` 7,852 (33.1 % of filled)**, `target` 3,713, `same_bar_conservative_stop` 32.

**[PRIOR-M1] What happens to the marked population when the wall is lifted** — this is why (A) is
small. Exit-class census moving from the 120 m wall to unbounded M1:

| horizon | target | stop | mark at horizon |
|---|---:|---:|---:|
| 120 min | 3,620 | 15,691 | 8,073 |
| 240 min | 5,185 | 17,962 | 4,236 |
| 480 min | 5,944 | 19,019 | 2,419 |
| 1,440 min | 6,510 | 19,670 | 1,202 |
| unbounded | 7,104 | 20,159 | 119 |

Of the 7,954 marked trades that eventually resolve, **4,468 (56.19 %) become stops and 3,484
(43.81 %) become targets** (2 to same-bar ambiguity). At 2R/−1R that is +0.314 R per resolved trade against a mark that
already averaged ~+0.28 — hence the whole horizon lift is worth only:

| arm | gross R/trade | delta vs engine |
|---|---:|---:|
| engine wall (120 m) | −0.24143 | — |
| from-fill 120 m | −0.23811 | **+0.00333** |
| from-fill 240 m | −0.23681 | +0.00462 |
| from-fill 480 m | −0.23365 | +0.00778 |
| from-fill 1,440 m | −0.22751 | **+0.01393** |
| unbounded | −0.21749 | **+0.02394** |

**The 2-hour wall costs 0.012–0.024 R/trade. It is a real contract, it is not a measurement bug, and
repairing it is worth roughly one eighth of the entry-fill repair.**

---

## 6. METHOD 5 — full stops: money on the table

**[MEASURED HERE]** n = **15,057** (54.44 % of pool). MFE between the fill bar and the first stop:

| | value |
|---|---:|
| fill class | **gap 7,464 (49.6 %)** / clean 7,593 |
| MFE before stop — median | **+0.1163 R** |
| p25 / p75 / p90 / p95 | −0.9224 / +0.4257 / +0.8883 / +1.2594 |
| share MFE ≥ 0.25 R | 34.69 % |
| share MFE ≥ 0.50 R | 21.04 % |
| **share MFE ≥ 1.00 R** | **8.19 %** |
| share MFE ≥ 2.00 R | 0.39 % |
| hindsight ceiling: exit at 1R whenever MFE ≥ 1R | **+0.0892 R/pool trade** |
| hindsight ceiling: exit at 0.5R whenever MFE ≥ 0.5R | **+0.1718 R/pool trade** |

**Half of the full stops are fill artifacts** (49.6 % are gap rows), and **the median genuine full
stop never went more than a tenth of an R in favour.** There is no large give-back population: the
"winners give money back" story is refuted at n = 15,057. The two hindsight ceilings are upper
bounds under perfect foresight and are **not policies** — they are quoted so later lanes know the
size of the box.

---

## 7. PER-FAMILY, under the repaired entry contract **[MEASURED HERE]**

Filled rows only (A2: clean + re-anchored, wall still at 120 min):

| family | pool n | untakeable | engine gross | **repaired gross** | n filled | win | breakeven | mean W | mean L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 7,146 | 65 | −0.1416 | −0.1034 | 7,075 | 0.3617 | 0.4102 | +1.256 | −0.874 |
| `liquidity_sweep_reclaim` | 4,475 | 29 | −0.0415 | **−0.0233** | 4,381 | 0.3668 | 0.3763 | +1.527 | −0.921 |
| `displacement_continuation` | 4,469 | 7 | −0.0885 | −0.0667 | 4,417 | 0.3991 | 0.4350 | +1.051 | −0.809 |
| `current_breaker_re_entry` | 4,263 | **3,434** | **−0.8254** | **−0.0939** | **827** | 0.3579 | 0.3992 | +1.365 | −0.907 |
| `cross_asset_lead_lag` | 2,083 | 29 | −0.1307 | −0.1473 | 2,006 | 0.2981 | 0.3510 | +1.807 | −0.978 |
| `structural_distance_extreme` | 1,993 | 93 | −0.1820 | −0.2092 | 1,859 | 0.2598 | 0.3291 | +2.026 | −0.994 |
| `current_ob_retest` | 1,340 | 41 | −0.1046 | **−0.0396** | 1,296 | 0.4360 | 0.4600 | +0.888 | −0.757 |
| `session_open_range_break` | 987 | 1 | −0.0747 | −0.0871 | 963 | 0.4185 | 0.4713 | +0.872 | −0.777 |
| `volatility_compression_expansion` | 605 | 0 | −0.0868 | −0.0812 | 603 | 0.4461 | 0.5426 | +0.385 | −0.456 |
| `regime_transition_break` | 297 | 0 | −0.0067 | **−0.0079** | 291 | 0.5052 | 0.5145 | +0.411 | −0.435 |

Under the "never trade a marketable limit" contract (gap + never-touched scored 0), **four families
turn non-negative**: `liquidity_sweep_reclaim` **+0.0280** (win 0.2677 vs breakeven 0.2531),
`regime_transition_break` **+0.0128** (0.3704 vs 0.3505), `current_breaker_re_entry` **+0.0116**,
`current_ob_retest` **+0.0006**. n is large for the first (4,475) and small for the second (297).
No significance claimed.

**Untakeable concentration by symbol** (share of that symbol's rows): GBPUSD **44.8 %** (1,474),
EURJPY **42.0 %** (1,080), USDCAD **36.2 %** (1,243), UK100 **30.5 %** (2,016), EURGBP 20.0 % (828),
AUDJPY 17.0 % (758), USDCHF 14.2 % (906), SPX500 12.3 % (1,943). FX majors and UK100 — instruments
whose declared stop is tightest relative to M1 noise.

---

## 8. WHERE THE POOL ACTUALLY STANDS, net

**[MEASURED HERE]** for gross and frozen cost; the spread-inflation factor is the swarm's
established 7.3–8.5× and is applied here, labelled **[INDICATIVE]** because this lane did not
re-measure it.

| book | gross R/trade | cost R/trade | net R/trade |
|---|---:|---:|---:|
| engine record | −0.2175 | 0.6632 | **−0.8807** |
| entry-contract repaired (A1) | −0.0751 | 0.5687 *(cost paid on 85.76 % of rows only)* | −0.6438 |
| A1 + spread de-inflated 7.3× **[INDICATIVE]** | −0.0751 | 0.1511 | **−0.2262** |
| A1 + spread de-inflated 8.5× **[INDICATIVE]** | −0.0751 | 0.1418 | **−0.2169** |

**Stated honestly: both repairs together still leave the pool negative by ~0.22 R/trade.** But the
character of the problem has changed completely — the *gross signal* deficit is **−0.0751, not
−0.2175**, and the residual is now dominated by a cost term whose own known error bar (7.3–8.5×) is
the same size as the remaining gap. **The gross question and the cost question are now separable,
and they were not before.** Under the strict-limit contract, unfilled orders cost nothing — the
engine has never modelled that: it charges cost on 99.12 % of rows where a strict limit fills 83.12 %.

---

## 9. What later waves should do with this

1. **Re-run CQ's inverted-breaker candidate with the 3,434 untakeable rows removed** (§4). This is
   the single highest-value follow-up in the receipt and it is a yes/no test.
2. **Carry the fill classifier to February / March / April / May.** It is three lines against any
   pool+path pair (`w0cap_verify.py:38-52`) and it re-scores every historical family verdict. Every
   published per-family number in this program is computed on a population that is 36 % gap-filled
   and 13 % untakeable.
3. **Fix the surface, not the walker.** `limit_marketable_at_decision` is `None` on 85.2 % of rows.
   Populating it makes the engine's *existing* handler (`:54258`) do the right thing; no new policy
   is needed.
4. **`execution_fillability`, `daily_lockout`, `marketable_guard` are the three positive classes
   under repair.** Small n. Worth a dedicated lane.
5. **Do not spend effort on the horizon.** It is measured, it is real, and it is worth +0.012 to
   +0.024 R/trade. It is the eighth-largest thing in this receipt.

---

## 10. Artifacts

| file | what |
|---|---|
| `w0-capture_RESULT.md` | this |
| `w0-capture_RESULT.json` | every number above, merged, machine-readable |
| `w0cap_verify.py` → `W0CAP_VERIFY_V1.json` | independent fill classification + books |
| `w0cap_mechanism.py` → `W0CAP_MECHANISM_V1.json` | marketable-flag cross-tab, untakeable, METHOD 4/5 |
| `w0cap_untakeable.py` → `W0CAP_UNTAKEABLE_V1.json` | untakeable characterisation, per-family/symbol |
| `w0cap_breaker.py` → `W0CAP_BREAKER_V1.json` | the `current_breaker_re_entry` decomposition |
| `w0cap_reanchor.py` → `W0CAP_REANCHOR_V1.json` | the engine's-own-rule repair, arms A0–A7 |
| `w0cap_final.py` → `W0CAP_FINAL_V1.json` | per-family repaired books, cost headroom |
| `w0cap_blocker.py` → `W0CAP_BLOCKER_V1.json` | blocker census under repair |
| `W0_CAPTURE_*.json`, `W0CAP_MFE_/WALL_/STALE_*.json` | **[PRIOR-M1]** the dead agent's M1-sourced work, preserved |

**Superseded:** `W0_CAPTURE_HORIZON_V1.json → recoverable_decomposition.B_exit_policy_cost_R_per_trade
= 0.2579` is a fill-blind artifact (§0). Use §2.2 and §5 instead.
