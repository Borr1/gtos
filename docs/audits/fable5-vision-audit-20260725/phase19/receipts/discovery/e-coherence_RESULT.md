# Lane e-coherence — one mechanism or several?

**Population** January 2026 true-UTC S0R0 diagnostic pool, n=27,658, joined to w0's working set and
to w0-capture's no-look-ahead decision anchor. Every number below was re-measured in this lane on one
frame with one set of conventions. Scripts `e_01..e_12` and artifacts `E_*_V1.json` sit beside this file.

**Base frame validation.** `e_build_base.py` reproduces w0-capture's clean born census exactly —
at_limit 14,911 / resting 7,949 / marketable 1,265 / past_stop 3,516 / unanchored 17 — using
`mkt_r_prev_close` (the close of the bar strictly before the decision minute; bars are OPEN-stamped,
so `mkt_r_close` is the look-ahead anchor and reproduces w0-capture's *rejected* V2 numbers
14,086 / 9,035 / 3,785 / 735). `e_03_realcost.py` reproduces L10's broker-true cost to six decimals
(total 0.189297, spread 0.124828, commission 0.057102). `e_08b` reproduces w0's
`fill_honest_walk_r` mean of −0.126526 from the raw R paths. The instruments agree with the lanes
they are auditing before they are used to disagree with them.

---

## 0. THE ANSWER IN ONE PARAGRAPH

There is **one root mechanism**, not twelve. **46.088 % of the January pool (12,747 rows) is
point-of-interest LIMIT orders resting at price levels the market has already left, and the live
engine cannot place a limit order at all** (L10-X3: intended entry equals the executable quote on
296/296 live captures, `TRADE_ACTION_DEAL` only). Ten of the swarm's headline mechanisms are that
one population seen from different angles. Measured directly: the fill-probability inversion is
**100.0 %** inside it, the stale-entry artifact **100.0 %**, pseudo-replication **98.2 %**, and the
exit-contract prescription **reverses sign** outside it. The naive sum of lane headlines is
**1.91271 R/trade** against a pool deficit of **0.21750** — inflated **8.8×**. On the 53.912 % that
can actually be traded the honest ledger is: gross **−0.05965** R/trade, broker-true toll **0.21241**
R/trade. **The toll is 3.6× the size of the entire signal, and the signal is negative.**

And the one thing that is genuinely alive: a composed contract on that placeable cohort
(broker-true cost gate + 5-minute entry delay + 0.25 R trail) is **gross-positive at
+0.017782 R/trade, t = 4.651, 18 of 21 days, +0.0130 / +0.0215 across the two halves of the month,
17 of 22 symbols positive, top symbol only 17 % of total R — and it is SIGNAL, not drift
(direction-neutral SIGNAL +0.01779 t +4.65; DIRECTION +0.00157 t +0.41)**. It is still net −0.050921
because the toll is 3.9× the edge. **Exactly one symbol is net-positive: NAS100, +0.00484 R/trade on
n=498 — the symbol the shipped spread cap makes arithmetically impossible to admit** (minimum frozen
`spread_r` over all 1,622 NAS100 rows is 0.16326 against a 0.10 cap; 0 could ever pass).

---

## 1. THE INSTRUMENT — abstention vs selection

Every lane reporting "+X R/trade from filter F" is reporting a mixture. Exactly:

```
per-opportunity delta = SELECTION + ABSTENTION
SELECTION  = keep_rate * (mu_kept - mu_pool)      genuine discrimination
ABSTENTION = -(1 - keep_rate) * mu_pool           free iff mu_pool<0 and not trading is free
```

Abstention has no ceiling and no skill — declining everything "earns" the whole deficit. Only
SELECTION can build a book. Measured on the honest outcome, n=27,658, mu_pool = −0.236719
(`E_DECOMP_V1.json`):

| filter | n kept | keep | mu kept | delta | **SELECTION** | ABSTENTION | sel share |
|---|---:|---:|---:|---:|---:|---:|---:|
| drop born_past_stop | 24,142 | 0.873 | −0.1265 | +0.1263 | **+0.0962** | +0.0301 | **76.2 %** |
| drop marketable | 26,393 | 0.954 | −0.2330 | +0.0144 | +0.0035 | +0.0108 | 24.6 % |
| drop both stale-adverse | 22,877 | 0.827 | −0.1162 | +0.1406 | +0.0997 | +0.0409 | 70.9 % |
| keep at_limit only | 14,911 | 0.539 | −0.1270 | +0.1682 | +0.0591 | +0.1091 | 35.2 % |
| refuse bar-1 fills (L8) | 10,707 | 0.387 | −0.0380 | +0.2220 | +0.0769 | +0.1451 | 34.7 % |
| refuse bar-1 AND past_stop | 10,706 | 0.387 | −0.0379 | +0.2221 | +0.0770 | +0.1451 | 34.7 % |
| cost gate as shipped | 7,210 | 0.261 | −0.1076 | +0.2087 | +0.0337 | +0.1750 | 16.1 % |
| cost gate, total limb only | 7,584 | 0.274 | −0.0965 | +0.2103 | +0.0385 | +0.1718 | 18.3 % |
| cost gate, spread limb only | 10,399 | 0.376 | −0.1500 | +0.1803 | +0.0326 | +0.1808 | 18.1 % |
| cost gate at spread/7.3 | 16,444 | 0.595 | −0.1881 | +0.1249 | +0.0289 | +0.0960 | 23.1 % |
| **invert fill floor (keep < 0.45)** | 3,407 | 0.123 | −0.0369 | +0.2322 | +0.0246 | +0.2076 | **10.6 %** |
| fill floor 0.45 as shipped | 24,099 | 0.871 | −0.2648 | +0.0060 | **−0.0245** | +0.0305 | negative |
| fill floor 0.80 as shipped | 20,777 | 0.751 | −0.2873 | +0.0209 | **−0.0380** | +0.0589 | negative |
| past_stop then cost gate | 6,984 | 0.253 | −0.0800 | +0.2165 | +0.0396 | +0.1769 | 18.3 % |
| past_stop + not-bar1 + cost | 3,018 | 0.109 | **+0.0024** | +0.2370 | +0.0261 | +0.2109 | 11.0 % |

**Only one mechanism in the entire swarm is majority-SELECTION: dropping the already-breached-stop
rows (76.2 %).** Every other headline is 65–90 % abstention. The as-shipped fill floors have
*negative* selection at both configured thresholds.

---

## 2. THE CLUSTERING — six roots, and five of them are the same root

### ROOT A — THE ORDER-TYPE FICTION (subsumes ten lane findings)

The generator emits a POI *price level* plus a stop. The level is not a price the system can trade at,
and 46.088 % of the time it is not a price the market is at either.

`E_STRUCTURE_V1.json` — family × born state, and it is not a gradient, it is a partition:

| family | n | at-market | resting | marketable | past-stop | **live-placeable** |
|---|---:|---:|---:|---:|---:|---:|
| cross_asset_lead_lag | 2,083 | 2,083 | 0 | 0 | 0 | **1.0000** |
| liquidity_sweep_reclaim | 4,475 | 4,475 | 0 | 0 | 0 | **1.0000** |
| regime_transition_break | 297 | 297 | 0 | 0 | 0 | **1.0000** |
| session_open_range_break | 987 | 987 | 0 | 0 | 0 | **1.0000** |
| structural_distance_extreme | 1,993 | 1,993 | 0 | 0 | 0 | **1.0000** |
| volatility_compression_expansion | 605 | 605 | 0 | 0 | 0 | **1.0000** |
| displacement_continuation | 4,469 | 4,465 | 0 | 0 | 0 | 0.9991 |
| **current_fvg_fill** | 7,146 | 6 | 6,193 | 936 | 1 | **0.0008** |
| **current_breaker_re_entry** | 4,263 | 0 | 593 | 200 | 3,467 | **0.0000** |
| **current_ob_retest** | 1,340 | 0 | 1,163 | 129 | 48 | **0.0000** |

**12,743 of the 12,747 unplaceable rows (99.97 %) are the three `current_*` POI families.**

**Where each published mechanism actually lives** (`E_FINAL_V1.json → mechanism_locations`):

| mechanism, and the lanes that reported it | n rows | share inside the unplaceable 46 % | rows on the live cohort |
|---|---:|---:|---:|
| stop already breached at decision — w0-capture | 3,516 | **100.0 %** | 0 |
| entry the market has left — L4, L7, W0-F2 | 9,214 | **100.0 %** | 0 |
| below the 0.80 fill floor — L4-F8, L6-F3, L9-F1, L12-F1 | 6,729 | **100.0 %** | **0** |
| below the 0.45 fill floor — same four lanes | 3,407 | **100.0 %** | **0** |
| pseudo-replicated rows — W0-F1, L2-F9, L11 | 6,745 | 98.2 % | 120 |
| entry traded in the first minute — L8-F1 | 16,951 | 33.3 % | 11,308 |
| the only positive blocker class (daily_lockout) — L6 | 47 | 76.6 % | 11 |
| stop inside the quoted spread — L2-F5 | 4,188 | 63.7 % | 1,519 |
| arithmetically impossible under the cap — L10-X5 | 3,565 | 62.7 % | 1,328 |

#### A.1 The fill-probability inversion does not exist on a placeable order

Four lanes made this their headline. `E_NESTING_V1.json → T1`:

| | whole pool | **live-placeable cohort** |
|---|---:|---:|
| distinct values of `execution_fill_probability` | 7,399 | **2** |
| value counts | 0.0401 … 0.95 | **0.92 on 14,708 (98.639 %), 0.95 on 107** |
| rows below the 0.45 floor | 3,407 | **0** |
| rows below the 0.70 floor | — | **0** |
| rows below the 0.80 floor | 6,729 | **0** |
| inversion (refused minus kept, honest R) at 0.45 | **+0.227953** | **undefined — nothing is refused** |
| inversion at 0.80 | +0.207222 | **undefined** |

`poi_execution_lifecycle.py:164-176` hardcodes 0.92 for any entry at or through the market. Every
live-placeable order is at the market by definition. **The fill floors cannot fire on a placeable
order, and the +0.23 R/trade inversion four lanes reported is a property of orders that cannot
exist.** L9's own configured-switch finding (`ultimate_candidate_package_soften_selector_fill_floor_enabled`
false at `config/agent_config.yaml:795`) is real as a code fact and worth 0 on the live book.

#### A.2 Pseudo-replication is 98.2 % inside the dead cohort

`E_NESTING_V1.json → T2`: 6,745 repeat rows pool-wide, **6,625 (98.221 %) unplaceable**; only 120
(0.805 %) on the live cohort. Dedup bias on the live cohort is **+0.00027 R/trade** against
w0-F1's pool-wide −0.0228. **No significance test on the placeable book needs a dedup control.**
L2-F9's sign-flip of the stop sweep under dedup, and L11's 1,498 repeats booking +0.4988, are both
properties of `current_fvg_fill`, which contributes 6 placeable rows out of 7,146.

#### A.3 The first-minute effect is NESTED inside the stale-entry effect, not additive

`E_ADJUDICATE_V1.json → A1`. **3,515 of 3,516 past-stop rows are bar-1 fills** — the cohorts are
nested, and the two lanes' headlines are not independent.

| cohort | n | honest R | target rate | stop rate |
|---|---:|---:|---:|---:|
| all bar-1 fills | 16,951 | −0.36227 | 0.1148 | 0.6465 |
| bar-1 **and** past_stop (w0-capture) | 3,515 | −0.99334 | 0.0011 | 0.9986 |
| bar-1 but **not** past_stop (L8's residual) | 13,436 | −0.19717 | 0.1445 | 0.5544 |
| not bar-1 | 10,707 | −0.03795 | 0.1650 | 0.4570 |

Per opportunity: refuse-past-stop +0.12628, refuse-bar-1 +0.22203, **incremental value of the bar-1
rule over the past-stop rule +0.09579**. Naive sum of the two lanes = 0.11332 + 0.22251 = 0.33583,
which is **51 % inflated** against the 0.22203 the combined rule is actually worth.

#### A.4 And L8's rule is not implementable on the half that matters

`E_CONVENTION_V1.json → at_market_touch_conditioning`, on the 14,911 at-market rows, under the
*market* convention (no touch requirement — a market order is filled):

| | n | market-convention R | honest-convention R |
|---|---:|---:|---:|
| entry traded on bar 1 | 11,308 | −0.170705 | −0.170705 |
| entry not traded on bar 1 | 3,603 | **+0.288897** | +0.010119 |

The split is enormous and it is **ex-post only**. For a market order you cannot refuse the fill —
you are already in. The partition says "trades where price immediately came back through the entry
lose; trades where it ran away win", which is a restatement of the outcome, not a decision rule.
**The implementable version of this mechanism is L7's delay repair, and it is worth +0.067, not
+0.22** (independently reproduced below).

---

### ROOT B — R-DENOMINATION (the reason five gates look predictive and none is)

`cost_r = cost_price / risk_distance`, so every cost gate is a stop-width filter (L5-F3: within-symbol
Spearman ≥ 0.9966 on 18 of 24 symbols, exactly 1.0000 on four). `execution_fill_probability` is
monotone decreasing in entry distance. `candidate_probability` is +0.712 rank-correlated with it.
Widening the stop by k divides gross and cost by the same k, so the sign can never change (L2-F6).

**The cleanest single demonstration**, `E_PRICESPACE_V1.json → min_risk_distance_frontier`, on the
live-placeable cohort. Filtering on a minimum risk distance improves the R book monotonically by
**+0.230 R/trade** while the price-space edge gets **worse by 2.65 bps**:

| min risk distance | n | signal bps | toll bps | **edge bps** | **R net at truth** |
|---:|---:|---:|---:|---:|---:|
| ≥ 0 | 14,911 | −0.711 | 2.443 | **−3.154** | **−0.27206** |
| ≥ 4 bps | 11,891 | −0.852 | 2.811 | −3.664 | −0.21073 |
| ≥ 10 bps | 7,582 | −1.075 | 3.661 | −4.736 | −0.17354 |
| ≥ 20 bps | 4,325 | −1.244 | 4.802 | −6.046 | −0.14450 |
| ≥ 50 bps | 1,588 | −0.198 | 6.683 | −6.881 | −0.08955 |
| ≥ 80 bps | 753 | +0.741 | 7.394 | −6.654 | −0.05957 |
| ≥ 120 bps | 380 | +2.245 | 8.043 | **−5.799** | **−0.04185** |
| ≥ 200 bps | 124 | +22.483 | 8.337 | +14.147 | +0.08379 |

The last row is noise: **t = 0.583, 7 of 18 days positive**, 73 of 124 rows one symbol (XAGUSD),
median risk distance 277 bps. Everything above it is a pure denominator artifact — the R column
improves 6.5× while the money gets worse. **Any lane reporting an R improvement from a filter
correlated with stop width has measured the denominator.**

**The toll census**, live cohort, broker-true cost as a share of the risk actually taken:
mean **21.241 %**, median 13.421 %, p10 3.322 %, p90 48.588 %. **61.485 % of trades pay more than
10 % of their risk to the broker; 27.362 % pay more than 25 %; 9.510 % pay more than 50 %; and
1.583 % (236 trades) pay MORE THAN 100 %** — the round trip costs more than the entire distance to
the stop.

---

### ROOT C — THE FROZEN COST MODEL IS SCRAMBLED (genuinely independent of A and B)

L5-F1 and L10-X5/X6 are the same finding and it is real: hardcoded per-symbol constants,
0.017× to 33.902×. Verified here at row level (`E_REALCOST_V1.json`), reproducing L10 to six
decimals. **NAS100 and SPX500 are arithmetically impossible**: minimum frozen `spread_r` over all
their rows is 0.16326 and 0.24479 against a 0.10 cap — 0 of 3,565 index candidates could pass in
the entire month.

---

### ROOT D — EXIT GEOMETRY (real, but its published prescription reverses)

See §3.3. The martingale finding is real; "delete the exit contract" is not.

### ROOT E — DEAD / REDUNDANT MACHINERY (L6, L12, L9)

Six of ten gate predicates have zero unique blocks; two probability floors can never fire; three
score components are constant. Engineering-real, economically ~0 once A and B are removed.

### ROOT F — PSEUDO-REPLICATION — **absorbed into ROOT A** (98.2 % inside it).

---

## 3. THE ADJUDICATIONS — every one re-measured, not taken on trust

### 3.1 A2 — L5 (+0.09512) vs L8 (−0.0316) vs L12 ("makes selection worse")

**All three are right and they answer different questions; and L8/L12 inherited a defective
instrument from the swarm brief.** L8 and L12 both used the flat 7.3× spread divisor. L10 measured
that the frozen model is *scrambled*, not uniformly biased, so a flat divisor is itself wrong.

`E_REALCOST_V1.json → A2_v2`, ex-past-stop, n=24,142, identical rows:

| gate | n | GROSS | cost at truth | **NET at truth** |
|---|---:|---:|---:|---:|
| no gate | 24,142 | −0.12653 | 0.1876 | −0.31415 |
| FROZEN (as shipped) | 6,984 | **−0.08003** | 0.1169 | −0.19697 |
| flat-7.3 corrected (what L8/L12 tested) | 14,837 | −0.10179 | 0.1170 | −0.21880 |
| **per-symbol broker-true (what L5 tested)** | 11,879 | −0.11415 | **0.0671** | **−0.18128** |

The cost repair decomposes into three parts and **only two are money**:

1. **RE-ACCOUNTING −0.030166 R/trade** on the same rows (pool-wide 0.663161 → 0.189297 = **0.473864**).
   Same trades, same broker bill. **Zero dollars move.**
2. **GROSS SELECTION −0.034119** — the corrected gate picks *worse* trades. L8 and L12 are right.
3. **COST SELECTION +0.049814** — it picks *cheaper* trades (0.1169 → 0.0671).

Net real value **+0.015695 R/trade**. **Not L5's +0.09512, and emphatically not L10's +0.473864** —
that figure is an accounting correction and must never be added to an economic ladder. L5's larger
figure comes from a different broker-truth artifact charging the frozen-gate cohort 0.19250 R against
L10's tick-measured 0.1169; the two lanes disagree ~1.6× on what "broker truth" is. Both agree on the
signs: **gross selection negative, net positive.**

### 3.2 A6 — L3 ("the gate anti-selects") vs L8 ("the gate does real work")

**Both are right; they measured different outcomes on the same cut, and on the live cohort both
collapse to nothing.** `E_ADJUDICATE_V1.json → A6`:

| population | side | n | honest R | target rate | median risk dist |
|---|---|---:|---:|---:|---:|
| ALL | kept | 7,210 | −0.10762 | 0.1172 | 0.2147 % |
| ALL | refused | 20,448 | −0.28224 | **0.1403** | 0.0671 % |
| ex past-stop | kept | 6,984 | −0.08003 | 0.1206 | 0.2155 % |
| ex past-stop | refused | 17,158 | −0.14545 | **0.1671** | 0.0739 % |
| ex past-stop, not bar-1 | kept | 3,018 | **+0.00244** | 0.1484 | 0.1760 % |
| ex past-stop, not bar-1 | refused | 7,688 | −0.05368 | **0.1716** | 0.0779 % |

Refused rows hit target more often **at every population** (L3 correct) *and* book worse R at every
population (L8 correct), because they carry a 2.3–3.2× tighter stop and risk distance controls
**resolution, not edge** (L3-F5's own finding). On the live-placeable cohort the gate's R
discrimination is **−0.007219 frozen / +0.006468 broker-true** — i.e. **zero** — while the target-rate
inversion persists (0.113 kept vs 0.215/0.249 refused). **The cost gate's entire published selection
value was the accidental exclusion of unplaceable rows.**

### 3.3 A4 — L1/L11 book the declared 2R/−1R at −0.084151; L2 and w0 book it at −0.126526

A 0.0424 R/trade gap on the most-cited contract in the swarm. **It is the fill convention, and I
identified which one by reconstruction** (`E_EXITADJ_V2.json`, re-walking the raw R paths):

| configuration | mean |
|---|---:|
| touch-bar start, `policy_target_r`, stop-first tie (**= w0's `fill_honest_walk_r`**) | **−0.126526** |
| flat 2.0R target instead of `policy_target_r` | −0.126672 |
| target-first tie rule | −0.122550 |
| start at the bar *after* the touch | −0.119630 |
| no fill requirement, walk from bar 1 | +0.191522 |
| **MIXED: market fill for at-market/marketable, honest for resting** (`E_CONVENTION_V1`) | **−0.083580** |

**−0.08358 vs L1/L11's −0.084151.** L1 and L11 used the MIXED convention (their reported fill rate
is 99.99 %, against L4's and w0's 99.00 % — the tell); L2, L4, L8 and w0 used strict-touch HONEST.
Neither is wrong; they were never reconciled. Corroboration: my no-fill-requirement HOLD-to-wall is
**−0.038405** against L11's **−0.038647**.

**But L11's prescription reverses on the placeable cohort.** `E_NESTING_V1.json → T3`, n=14,911:

| contract | L11's population (24,142) | **live-placeable (14,911)** |
|---|---:|---:|
| incumbent 2R/−1R | −0.084151 | **−0.059650** |
| hold to the 2 h wall | −0.038647 | **−0.085872** |
| incumbent cost vs hold | **+0.045504 (hold WINS)** | **−0.026222 (incumbent WINS)** |
| 0.25 R trail | — | **−0.006054** |

L11's HOLD arm books `cls[-1]` measured from the POI level, and on 7,949 resting rows the market is
already **+1.660 R** past that level — the W0-F2 fiction re-entering through the hold arm. On rows
where the entry *is* the market, holding is **worse** than the incumbent by 0.0262.
**"Every exit level is value-destroying, delete the contract" is a prescription derived from orders
that cannot exist, and it is wrong on the ones that can.** What survives is the trail: 0.25 R is
worth **+0.053596** over the incumbent on the placeable cohort, agreeing with L2-F3 (+0.04646) and
L1-F1 (best of 275 contracts, −0.01904).

### 3.4 The convention over-correction nobody checked

`E_CONVENTION_V1.json`. The swarm switched to fill-HONEST to kill W0-F2's fiction. On the 53.912 %
that are **at-market orders** the honest convention makes you wait for the market to return to a
price you would already have been filled at:

| born state | n | BLIND | HONEST | honest − blind | live-placeable |
|---|---:|---:|---:|---:|---|
| at_limit | 14,911 | −0.05965 | −0.12701 | **−0.06736** | yes |
| marketable | 1,265 | −0.29465 | −0.31408 | −0.01943 | yes (fills worse than entry) |
| resting | 7,949 | **+0.74083** | −0.09468 | −0.83552 | **no** |
| past_stop | 3,516 | −0.99334 | −0.99334 | 0.00000 | **no** |

Pool headline by convention: BLIND +0.040897, HONEST −0.236719, **MIXED −0.199233**, engine
−0.217496. Ex-past-stop: HONEST −0.126526 vs **MIXED −0.083580**. **The swarm's own standard
convention over-charges the at-market majority by 0.06736 R/trade.**

### 3.5 L1-F4's signal/direction result does not reproduce as a pool property

L1-F4 reported pool DIRECTION +0.09049 (t +4.005) and SIGNAL −0.02906 (t −1.286) on 2-hour drift.
On engine gross over all 27,658 I get SIGNAL −0.21711 (t −34.29), **DIRECTION +0.00409 (t +0.65)**.
Different measure (2 h mark-to-market vs scored contract) — not a contradiction, but **the "the only
thing that moved was the market" reading does not survive to the scored outcome**, and it does not
survive on the composed book either (§4).

---

## 4. THE DE-DOUBLE-COUNTED LEDGER

`E_FINAL_V1.json`. One population, one convention, incremental.

| step | n | GROSS R/trade | cost R/trade | **NET R/trade** |
|---|---:|---:|---:|---:|
| 0 — as published (whole pool, engine gross, frozen cost) | 27,658 | −0.21750 | 0.66316 | **−0.88066** |
| 1 — + broker-true cost (**ACCOUNTING ONLY, zero dollars**) | 27,658 | −0.21750 | 0.18930 | −0.40679 |
| 2 — + scope: only orders the live engine can place | 14,911 | −0.05965 | 0.21241 | −0.27205 |
| 3 — + broker-true cost gate | 7,317 | −0.05636 | 0.06870 | −0.12506 |
| 4 — + 5-min entry delay **and** 0.25 R trail | 7,317 | **+0.01778** | 0.06870 | **−0.05092** |

**Naive sum of the thirteen lane headlines: 1.91271 R/trade** (W0-F2 0.2776 + w0cap 0.11332 +
L1 0.2404 + L1 0.1266 + L4 0.1112 + L8 0.22251 + L5 0.09512 + L10 0.473864 + L11 0.0455 + L2 0.0465
+ L9 0.0774 + L7 0.067 + gate 0.0157). The pool deficit being explained is 0.21750.
**Inflation factor 8.8×.** Causes, in order of size: eight of thirteen are the same 46.088 % of rows;
two (0.473864 and part of 0.2776) are accounting corrections that move zero dollars; two reverse sign
on the placeable cohort.

**Honest attribution of what is real:**

| what | R/trade | kind |
|---|---:|---|
| cost-model correction | +0.473864 | **accounting — not money** |
| scope correction (drop unplaceable orders) | +0.157845 gross | **measurement — not money** |
| broker-true cost gate vs frozen, at truth | **+0.015695** | money (cost selection, gross selection is −0.034) |
| 5-minute entry delay | **+0.066890** (paired, ±0.00822) | money |
| 0.25 R trail vs incumbent | **+0.053596** | money |
| everything else the swarm reported | **~0 on the placeable book** | nested or reversed |

### The composed book, and what it is

n = 7,317 · gross **+0.017782** · se 0.003823 · **t = 4.651** · **18 of 21 days positive** ·
H1 +0.013019 / H2 +0.021470 · cost at truth 0.068703 · **net −0.050921**.

**It is signal, not January's drift** (`E_SIGNALTEST_V1.json`):

| book | n | LONG | SHORT | **SIGNAL (t)** | DIRECTION (t) |
|---|---:|---:|---:|---:|---:|
| composed (gated live, delay 5 + trail 0.25) | 7,317 | +0.01936 | +0.01621 | **+0.01779 (+4.65)** | +0.00157 (+0.41) |
| all placeable, incumbent 2R/−1R | 14,911 | −0.03856 | −0.07727 | −0.05792 (−6.06) | +0.01936 (+2.02) |
| whole pool, engine gross | 27,658 | −0.21302 | −0.22119 | −0.21711 (−34.29) | +0.00409 (+0.65) |

**It is broad, not one instrument**: 17 of 22 symbols gross-positive, top symbol 17.0 % of total R.
**Exactly one symbol is net-positive at broker truth — and it is the one the shipped gate forbids:**

| symbol | n | gross R | t | **net at truth** | toll/risk | frozen-gate pass rate | min frozen spread_r |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NAS100** | 498 | +0.04443 | +2.94 | **+0.00484** | 0.0716 | **0.0000** | 0.16326 (cap 0.10) |
| UK100 | 356 | +0.04959 | +2.80 | −0.00467 | 0.1377 | 0.0047 | 0.0789 |
| USDCHF | 329 | +0.03771 | +2.11 | −0.04857 | 0.228 | — | — |
| GER40 | 522 | +0.01875 | +0.97 | −0.02138 | **0.0590** (cheapest) | 0.3024 | 0.0143 |
| SPX500 | 332 | +0.00450 | +0.24 | −0.05813 | 0.1726 | **0.0000** | 0.24479 |
| ETHUSD (worst) | 241 | −0.02152 | −1.09 | −0.10919 | 0.193 | — | — |

**Caveat, stated plainly:** the 5-minute delay and the 0.25 R trail were both selected on January
(L7 swept delays, L2 swept trails). Two parameters on 7,317 rows with 18/21 days and both halves
positive is weak evidence of robustness, not proof. The delay repair itself I reproduced
independently (paired +0.06689 ± 0.00822 at k=5; L7 reported +0.0670 [+0.0550, +0.0786]) — the
**level** −0.05965 → +0.00724 also matches L7's −0.0601 → +0.0069.

---

## 5. THE QUESTION NO LANE ASKED — asked, and answered

**Convert the 12,747 unplaceable POI limit orders into market orders.** Same setup, same stop price,
enter at market at the decision instant. That is a one-line generator change and it makes 46 % of
the book placeable. Nobody tested it. Exact algebra with `d' = (1+m)·d` and `R' = (R−m)/(1+m)`:

| cohort | n | R at 2R/−1R | t | hold | cost at truth | **NET** | edge bps | median scale |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all convertible POI limits | 9,214 | **−0.48201** | **−56.83** | −0.16331 | 0.1073 | **−0.58931** | −20.40 | 1.997 |
| resting only | 7,949 | −0.55920 | −70.36 | −0.51818 | 0.0717 | −0.63087 | −23.62 | 2.196 |
| marketable only | 1,265 | +0.00304 | +0.09 | +2.06656 ⚠ | 0.3311 | −0.32810 | −0.15 | 0.746 |

Per family: current_ob_retest −0.44782 (t −22.31), current_fvg_fill −0.49934 (t −52.06),
current_breaker_re_entry −0.38190 (t −11.06). Split-half −0.53236 / −0.44087. First-emission only
−0.481384. **The answer is a hard, unambiguous NO** — the conversion is catastrophic and stable in
every cut. The POI families' edge, such as it is, *is* the level: entering at market doubles the risk
distance (median scale 1.997) and destroys it. ⚠ the marketable `hold` figure is numerically unstable
(rows with m → −1 give scale → 0); the resting cohort carries the finding and is safe.

**This closes the last escape route.** The 46 % cannot be traded as emitted and cannot be converted.
The January broad book is the 14,911 at-market rows, and nothing else.

---

## 5b. CROSS-CHECK against a concurrent lane — the delay repair is NOT a January artifact

**Provenance, stated first.** While this lane ran, a parallel lane (scripts `e3_*.py`, `e4_*.py`,
timestamps 09:34–09:50, **no RESULT file written yet — in flight, not adjudicated**) produced
`E_ATMKT_POOLED_V1.json`: an at-market factorial over **three months**, D=delay, E=exit, G=gate.
I did not produce it and have not audited its machinery. **What licenses citing it is that its
January cell reproduces my independent measurement exactly** — k0 −0.059658 / k5 +0.007236 /
delta +0.066894 / n 14,905 against my −0.05965 / +0.007236 / +0.06689 / n 14,905.

| month | k0 (enter at trigger close) | k5 (5-minute delay) | **delta** | n |
|---|---:|---:|---:|---:|
| 2026-01 (mine, reproduced) | −0.059658 | +0.007236 | **+0.066894** | 14,905 |
| 2026-02 | −0.056941 | +0.009163 | **+0.066105** | 13,966 |
| 2026-03 | −0.079605 | −0.013881 | **+0.065724** | 14,884 |

**The delay repair replicates to three decimal places across three independent months.** That is by
some distance the most robust economic quantity anywhere in this swarm. Note the *level* is negative
in March even after the repair (−0.013881), so the repair is stable while the underlying book is not.

Their pooled composed cell D1E1G1 (delay + exit + gate, 3 months): n 24,490, gross **+0.01126**
(t_gross +3.15), cost 0.064745, net **−0.053485** — against my January-only n 7,317, gross +0.017782
(t 4.651), cost 0.068703, net **−0.050921**. **The two nets agree to 0.0026 R/trade.** Their
additivity check: delay alone +0.066244, exit alone +0.043106, sum 0.109350, joint 0.103918 —
**overlap only 4.97 %**, so the two repairs are close to independent, corroborating my §4 ladder.

**Two flags for the orchestrator, not for me to resolve.** (1) That artifact reads **March**, which
`CLAUDE.md` §4 designates outcome-unread and "the scarcest resource in the programme". It is already
on disk; the consumption question is an owner/orchestrator call. (2) Their at-market population is
~14,000/month against my 14,911 for January — close, but their born-state derivation is unaudited by
me. Treat the Feb/March cells as **indicative**, the January cell as **measured**.

---

## 6. WHAT IS STILL MISSING — four specific, runnable questions

**M1 — THE HORIZON. Highest value, and the data is on this machine.** Every lane in this swarm is
capped at the 2-hour pending-expiry wall (`v4_timewarp_simulated_live_research_loop.py:378`,
`REPAIRED_PENDING_EXPIRY_MINUTES=120`; 86.12 % of paths are exactly 120 bars) while the armed live
sleeves declare 320-hour horizons (`execution_packets.py:80,84`) — a **160× mismatch**. w0-capture
walked only the 4,897 *marked* trades to 24 h (+0.0170 R/filled trade). **Run: the 14,911 placeable
rows walked to 4 h / 8 h / 24 h / 72 h in PRICE units, from
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601`
(44 MB, confirmed present).** The composed book's edge is +0.0178 R against a 0.0687 toll; if the
edge scales with horizon and the toll does not, the ratio inverts somewhere. **Nobody knows where,
and it is the only structural lever left that is not a denominator artifact.**

**M2 — A PROPER NULL.** Every lane compared the pool to itself. L4's opposite-side placebo (−0.0935)
is a partial null; there is no random-time null anywhere. **Run: shuffle decision times within
symbol × day, hold the entry side, the risk distance and the contract fixed, re-walk, and rebuild the
composed book 200×.** Without it, "SIGNAL +0.01779 at t 4.65" cannot be distinguished from "any
M1-resolution entry with a 5-minute delay and a 0.25 R trail earns this". Cheap: the same R-path
machinery, ~10 minutes.

**M3 — NAS100 AND SPX500, THE INSTRUMENTS THE GATE DELETED.** 3,565 rows, 0 admissible in the entire
month, and NAS100 is the **only net-positive symbol** in the composed book (+0.00484, n=498, gross
t +2.94) with the 2nd-best toll/risk ratio (0.0716). GER40 has the best ratio (0.0590) and passes
only 30.24 %. **Run: the whole composed-book analysis restricted to the index complex
(NAS100, SPX500, GER40, UK100, US30_cash, JP225 — n≈2,567 placeable rows), with the frozen gate
removed and the broker-true gate substituted, plus February as a held-out month
(`CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz`, 24,239 rows, 101 fields, already re-clocked and never read
for this question).** This is the single highest-expected-value follow-up.

**M4 — THE PORTFOLIO.** Every number in this entire swarm is a per-trade mean. Nobody has built the
day-level book: trades per day, within-day correlation, and whether the 21 January days' variance
supports any position size at all. The composed book is 18/21 days positive at +0.0178 R/trade —
**Run: the daily P&L series of the composed book, its day-level Sharpe, and its worst-day drawdown
against the prop firms' 5 % daily-loss rule.** A per-trade edge of 0.018 R with an unmeasured daily
distribution cannot be sized, and sizing is what the charter is for.

---

## 7. FILES

Scripts: `e_build_base.py`, `e_01_decomp.py`, `e_02_adjudicate.py`, `e_03_realcost.py`,
`e_04_convention.py`, `e_05_livebook.py`, `e_06_pricespace.py`, `e_07_structure.py`,
`e_08_exitadjudicate.py`, `e_08b_exitadjudicate.py`, `e_09_convert.py`, `e_10_nesting.py`,
`e_11_final.py`, `e_12_signaltest.py`.

Artifacts: `E_DECOMP_V1.json`, `E_ADJUDICATE_V1.json`, `E_REALCOST_V1.json`, `E_CONVENTION_V1.json`,
`E_LIVEBOOK_V1.json`, `E_PRICESPACE_V1.json`, `E_STRUCTURE_V1.json`, `E_EXITADJ_V1.json`,
`E_EXITADJ_V2.json`, `E_CONVERT_V1.json`, `E_NESTING_V1.json`, `E_FINAL_V1.json`,
`E_SIGNALTEST_V1.json`, plus `e-coherence_RESULT.json`.
