# h3 — how much of the 2.457 bps toll can actually be removed

**Lane** `h3` · **Date** 2026-08-06 · **Population** the LIVE-EXPRESSIBLE book, 43,755 at-market
opportunities, 24 instruments, 63 trading days, January–March 2026, true UTC.
**Machine receipt** `h3_RESULT.json` beside this file. Every number below reproduces from the
scripts named in §12. Nothing here is estimated.

---

## 0. The answer in six lines

| | measured |
|---|---:|
| **Toll now** | **2.4571 bps** = spread 1.8104 (73.68 %) + commission 0.5686 (23.14 %) + slippage 0.0782 (3.18 %) |
| **Toll if the entry leg were passive** | 1.4738 bps (−40.02 %) |
| **Toll at the absolute mechanical floor** (both legs passive, zero slippage) | **0.5686 bps — commission only** |
| **Maximum removable** | **76.86 %, a 4.32× cut** |
| **Reduction required to pay at the pooled edge** | **10.63×** |
| **edge : toll at that unreachable floor** | **0.4066** |

**The toll cannot be cut ten-fold. The mechanical ceiling is 4.32×, and even standing on it — zero
spread, zero slippage, commission only — the pooled edge still earns 41 % of its own toll.** No
execution repair closes this gap at the pooled level. That is the lane's first and most important
number, and it is arithmetic, not inference: commission alone is 2.46× the edge.

**But the hunt succeeds anyway, because the answer to "can execution close the gap" is not the same
as "are there cells where it is already closed".** Three cells clear edge:toll > 1 with n in the
hundreds-to-thousands and three-of-three months; one of them clears it in **both** price space and
R space at **both** cost bases, is spread over all 24 instruments, and needs no new order type.
They are in §9, with their caveats attached.

---

## 1. Substrate, and the anchor

The lane works on `e_JAN/FEB/MAR_ATMKT_V1.jsonl.gz` — the cohort `e_build_atmkt.py` built for
lane e-stack: entries where `entry_price` equals the decision-instant close, i.e. the only orders
l10-X3 measured the live engine can actually place (296/296 live entries equal the executable quote
to floating-point exactness; `TRADE_ACTION_PENDING` is defined once and never used for entry).

**The published headline reproduces to every decimal it was published at.**

| | published | h3 recomputation | abs diff |
|---|---:|---:|---:|
| n | 43,755 | 43,755 | 0 |
| gross R/trade | +0.03834 | +0.038342 | 2.0e-06 |
| broker-true cost R/trade | 0.18183 | 0.181834 | 3.8e-06 |
| edge | +0.231 bps | +0.231192 bps | 1.9e-04 |
| toll | 2.457 bps | 2.457133 bps | 1.3e-04 |

Zero rows were dropped for missing tick truth — all 24 instruments price. The independent path
rebuild in `h3_02_passive_build.py` reproduces `e_build_atmkt.py`'s walked values **exactly on
100.000 % of 43,755 rows** at both K0 and K5 (max abs diff 0.0), so every arm below is scored by
machinery validated against the lane it is extending.

**Price space.** `rdp = risk_distance / entry_price`; `bps(x_R) = x_R · rdp · 1e4`. Every bps
figure is a per-trade quantity averaged over trades, never a ratio of averages. Where a number
matters, it is given in **both** bps (which decides affordability) and R (which decides money) —
§9 shows they can disagree in sign.

---

## 2. The toll, decomposed — and what is mechanically removable

| component | R/trade | bps | share | rows charged |
|---|---:|---:|---:|---:|
| quoted spread | 0.115198 | **1.8104** | **73.68 %** | 43,755 |
| commission | 0.059994 | 0.5686 | 23.14 % | 29,096 |
| slippage | 0.006641 | 0.0782 | 3.18 % | 11,571 |
| **total** | **0.181834** | **2.4571** | 100 % | |

A round trip crosses the quoted spread **once** — half on the way in, half on the way out. So the
toll partitions into three parts with three different removability:

| part | bps | removable by | verdict |
|---|---:|---|---|
| entry half-spread | 0.9052 | resting a limit instead of taking the market | **h3-F2: measured, does not pay** |
| exit half-spread | 0.9052 | exiting on a resting take-profit | **h3-F15: 0 % available under the headline contract** |
| slippage | 0.0782 | any passive fill | free rider on the above |
| commission | 0.5686 | nothing | **irreducible** |

**The exit half is not available at all under the contract the swarm chose.** Under `TRAIL025`,
**93.70 % of exits are stops and 0.00 % are limit-able targets** (2,756 path-ends, 40,999 stops,
zero targets). Under `INC` (2R target) 19.48 % of exits rest, worth **0.176 bps** — and `INC`'s edge
is 0.526 bps *worse*, so buying the exit saving costs three times what it pays.

For contrast, the frozen model the engine ships charges **6.389 bps**, 2.58× the broker truth,
including **0.173 bps of swap** on trades that cannot be held overnight (§7).

---

## 3. Item 1 — entry mechanics, priced in bps

### 3.1 The four mechanics, on one table

All on the same 43,755 opportunities. Toll for market arms = spread + commission + slippage;
for passive arms = half spread + commission (mid convention — see §3.4).

| mechanic | n | fill | edge bps | toll bps | net bps | e/t | net bps / opportunity |
|---|---:|---:|---:|---:|---:|---:|---:|
| at-market, no delay | 43,755 | 1.000 | −0.5030 | 2.4571 | −2.9601 | −0.205 | −2.96015 |
| **at-market, +5 min (headline)** | 43,755 | 1.000 | +0.2312 | 2.4571 | −2.2259 | 0.094 | −2.22594 |
| at-market, +20 min | 43,683 | 0.998 | +0.5395 | 2.4571 | −1.9172 | 0.220 | −1.91408 |
| resting limit at the decision price | 42,942 | 0.981 | −1.7915 | 1.4799 | −3.2714 | −1.211 | −3.21065 |
| resting limit, re-rest after a 60 s cancel | 42,638 | 0.974 | −2.1873 | 1.4796 | −3.6669 | −1.478 | −3.57331 |
| **resting limit + ABSTAIN if touched < 10 min** | 3,005 | 0.069 | +2.1412 | 1.4724 | **+0.6687** | **1.454** | +0.04593 |
| same filter, market order on the touch | 3,005 | 0.069 | +2.1412 | 2.5583 | −0.4171 | 0.837 | −0.02865 |

Read the last two rows together: **the entry half-spread is exactly the difference between a cell
that pays and one that does not** — 1.454 against 0.837 on the identical 3,005 trades. That is the
sharpest demonstration in this lane that the removable 40 % of the toll is decision-relevant, and
also the sharpest demonstration that it is not enough on its own.

### 3.2 Why the naive resting limit is catastrophic

**76.2 % of passive fills arrive in the first 60 seconds, and that cohort's edge is −2.6402 bps.**

| fill bar | n | share | edge bps | toll bps | net bps |
|---|---:|---:|---:|---:|---:|
| bar 0 (first 60 s) | 33,330 | 0.762 | **−2.6402** | 1.4908 | −4.1309 |
| bars 1–2 | 3,547 | 0.081 | +0.7212 | 1.4156 | −0.6943 |
| bars 3–5 | 1,937 | 0.044 | +0.5884 | 1.4352 | −0.8468 |
| bars 6–15 | 2,001 | 0.046 | +1.6615 | 1.4792 | +0.1823 |
| bars 16–60 | 1,645 | 0.038 | +2.0871 | 1.4446 | **+0.6425** |
| bars 61–120 | 482 | 0.011 | +1.2637 | 1.5062 | −0.2426 |

This is the swarm's adverse-selection finding, measured for the first time in price space on the
live-expressible book. Note the tell in the table: **cancelling and RE-RESTING is worse than not
cancelling at all** (row 5 of §3.1, −2.1873 bps). Refusing an early fill and then taking the next
one buys a later, worse fill in the same trend. The value is only in ABSTAINING.

### 3.3 The 60-second cancel, priced on the cohort it actually lives on

`born_resting` is 29.90 % of the pool (23,436 rows) — a passive limit at a price away from the
market, which l10-X3 established the live engine cannot place.

| | n | edge bps | toll bps | net bps | e/t |
|---|---:|---:|---:|---:|---:|
| all resting fills | 23,426 | +0.9371 | 2.0194 | −1.0823 | 0.464 |
| touched inside 60 s | 2,788 | −2.3877 | 1.9803 | −4.3681 | −1.206 |
| **touched after 60 s (the cancel survivors)** | 20,638 | **+1.3863** | 2.0247 | −0.6384 | **0.685** |

**The cancel is worth +0.4492 bps of EDGE and +0.0053 bps of toll.** It is not a cost lever at
all — the toll of the survivors is statistically the toll of the population. Keep rate 88.10 %.
And the whole thing sits on a cohort no live order can express. (h3-F14)

### 3.4 The quote-convention bracket — and why the conclusion survives it

The passive arm's arithmetic depends on whether the archived M1 bars are BID or MID, and **the
archive does not record it** — the CSV header is `time,open,high,low,close,volume`, no spread
column. So both were measured:

* **MID** — path is the mid. Market in/out = half spread each. A limit at `E` fills when the mid
  touches `E` and saves the entry half (0.905 bps).
* **BID** — path is the bid. For a long you buy the ask and sell the bid, so the whole spread is
  charged against a bid-measured path at entry and nothing at exit. A limit at `E` fills only when
  the **ask** reaches `E`, i.e. when the bid has fallen a full spread below `E`, and then costs no
  spread at all (saves 1.810 bps).

| arm | n | fill | edge bps | toll bps | net bps | e/t |
|---|---:|---:|---:|---:|---:|---:|
| at-market baseline | 43,755 | 1.000 | +0.2312 | 2.4571 | −2.2259 | 0.094 |
| MID limit at E, take first touch | 42,942 | 0.981 | −1.7915 | 1.4799 | −3.2714 | −1.211 |
| BID limit at E, fill when ask ≤ E | 41,962 | 0.959 | −2.8415 | 0.5791 | −3.4206 | −4.907 |
| MID + no-retrace ≥ 10 min | 3,005 | 0.069 | +2.1412 | 1.4724 | **+0.6687** | **1.454** |
| BID + no-retrace ≥ 10 min | 5,345 | 0.122 | −1.0783 | 0.3997 | −1.4780 | −2.697 |

**Two conclusions, and only one of them is convention-invariant.**

1. **INVARIANT: a naive resting limit at the decision price is net-negative under both
   conventions.** MID −3.2714, BID −3.4206, against a baseline of −2.2259. The bid convention saves
   twice as much toll and destroys 50 % more edge, because the deeper fill trigger *is* the adverse
   selection. This can be stated without settling the quote side.
2. **NOT INVARIANT: the passive no-retrace cell.** +1.454 under MID, −2.697 under BID. **This lane
   therefore does not lead with any passive arm.** The cell reported in §9 is entered at MARKET on
   the touch, which charges the full spread and is algebraically identical under both conventions
   (long: buy ask ≈ E+s, sell bid → P&L = r_exit − spread_r; short: sell bid = E, buy ask →
   the same), so it needs no convention to be settled.

### 3.5 The delay curve — a bigger bps lever than the whole removable half-spread

Toll is **identical at every delay** (2.4571 bps; cost is not a function of entry minute).

| delay (min) | edge bps | e/t | Jan | Feb | Mar |
|---:|---:|---:|---:|---:|---:|
| 0 | −0.5030 | −0.205 | −0.081 | −0.476 | −0.951 |
| 2 | +0.2356 | 0.096 | 0.116 | 0.490 | 0.116 |
| 5 (headline) | +0.2312 | 0.094 | 0.390 | −0.027 | 0.314 |
| 10 | +0.3293 | 0.134 | 0.335 | 0.372 | 0.284 |
| **20** | **+0.5395** | **0.220** | 0.306 | 0.636 | 0.683 |
| 30 | +0.4815 | 0.196 | 0.375 | 0.543 | 0.530 |
| 60 | +0.3991 | 0.163 | 0.200 | 0.581 | 0.427 |

**+0.7342 bps from minute 0 to the headline minute 5, and +1.0425 bps from minute 0 to minute 20,
at zero opportunity cost, three of three months positive** — against 0.9052 bps of removable entry
spread that measurement says cannot be captured.
The synthesis's chosen k=5 is not the best point on its own curve. (h3-F13)

---

## 4. Item 2 — session and hour

### 4.1 The hour model, and its validation

`L10X_TICK_SPREAD_V1.json` carries `spread_bps_median_by_broker_hour` per symbol from the 263.9 M
tick archive. Nothing in this estate had ever used it: every published cost number, including the
2.457 bps headline, charges one flat per-symbol median to all 24 hours.

The tick capture ran 2026-06-18..07-24 (US EDT, broker clock = UTC+3); the pool runs Jan–Mar
(EST = UTC+2 until 2026-03-08, EDT after). Session shape follows the **New York** wall clock, not
UTC, so the profile is transferred through NY local hour: `ny_hour = (broker_hour − 7) mod 24`.

**The mapping validates itself.** The spread must peak at broker midnight = NY 17:00, the daily
rollover. It does, on **13 of 24 instruments** — AUDJPY 9.2× its own median at NY 17, EURUSD 34.7×.
The remaining 11 peak at their own cash-session boundaries (GER40 at NY 16, NAS100 at NY 16). The
naive `broker−3` mapping used elsewhere in the estate is carried as a robustness arm and gives
2.6247 bps against the NY-correct 2.6692.

### 4.2 Hour-aware costing raises the toll 8.63 %

| basis | toll bps | edge bps | net bps |
|---|---:|---:|---:|
| flat per-symbol median (the estate's basis) | 2.4571 | 0.2312 | −2.2259 |
| **hour-aware** | **2.6692** | 0.2312 | −2.4381 |

**The pool trades in hours that are more expensive than the flat median claims**, by 8.63 %. The
rollover hour alone is the extreme case: **NY 17 costs 8.5091 bps hour-aware against 1.8826 bps
flat — the flat model understates it 4.52×** — and it is 2.12 % of the book. (h3-F5)

### 4.3 The ex-ante frontier — cheapest hours first

Hours ranked by mean hour-aware toll only (no outcome information), cumulative.

| hours kept | keep | edge bps | toll bps | net bps | e/t | net bps / opportunity |
|---:|---:|---:|---:|---:|---:|---:|
| 1 (NY 3) | 0.081 | 0.9690 | **2.2437** | −1.2747 | 0.432 | −0.10386 |
| 2 | 0.118 | 0.3287 | 2.2732 | −1.9445 | 0.145 | −0.22994 |
| 4 | 0.246 | 0.3468 | 2.3238 | −1.9770 | 0.149 | −0.48580 |
| 8 | 0.416 | 0.2170 | 2.3707 | −2.1537 | 0.092 | −0.89613 |
| 12 | 0.542 | 0.1837 | 2.4120 | −2.2283 | 0.076 | −1.20751 |
| 18 | 0.784 | 0.2790 | 2.4879 | −2.2088 | 0.112 | −1.73219 |
| 23 (drop only NY 17) | 0.979 | 0.2412 | 2.5430 | −2.3017 | 0.095 | −2.25303 |
| 24 (all) | 1.000 | 0.2312 | 2.6692 | −2.4381 | 0.087 | −2.43805 |

**Hour selection is the weakest lever in this lane by an order of magnitude.** Going all the way to
the single cheapest hour buys **0.4255 bps** of toll (2.6692 → 2.2437) and surrenders **91.85 % of
the book** — an efficiency of **0.4633 bps per unit of opportunity surrendered**, against **6.3804**
for the instrument lever, a **13.8× gap**. The whole hour frontier sits in a band of 0.447–0.511;
there is no point on it that is not dominated. Even the free-looking move — dropping the rollover
hour, 2.12 % of the book — buys only **0.1262 bps**.

*(Efficiencies here are computed hour-aware on both sides. §8's table charges every lever against the
one flat 2.4571 bps baseline so the levers are comparable to each other, which understates the hour
lever's `d_toll`; the hour-consistent numbers in this paragraph are the ones to quote for the hour
lever alone, and they are still 13.8× below the instrument lever.)* (h3-F4)

The ex-ante hour cost *ranking* is also unstable across months (Spearman 0.490 / 0.103 / 0.054),
because the pooled hour toll is dominated by which instruments happen to trade in that hour. The
within-symbol quoted-spread ratio *is* deterministic — but filtering on it buys almost nothing:
refusing every row where the symbol's own quoted spread exceeds 1.2× its median drops 12.7 % of the
book and **raises** the toll of what is kept by 0.2201 bps, because it removes cheap instruments in
their own expensive hours and keeps dear ones in their cheap hours.

### 4.4 Session and weekday, for the record

| session | n | share | edge bps | toll bps | net bps | e/t |
|---|---:|---:|---:|---:|---:|---:|
| tokyo | 2,900 | 0.066 | 0.4458 | **1.4483** | −1.0026 | 0.308 |
| london | 9,271 | 0.212 | 0.3073 | 2.4302 | −2.1228 | 0.126 |
| ny | 8,857 | 0.202 | 0.2180 | 2.2899 | −2.0719 | 0.095 |
| off_configured_session | 22,727 | **0.519** | 0.1779 | **3.0704** | −2.8925 | 0.058 |

**51.9 % of the live-expressible book is generated outside any configured session, and it is the
most expensive slice (3.0704 bps) and the thinnest edge (0.1779 bps).** That is one clean,
implementable observation the hour frontier does not surface: session, not hour, is where the
cost/opportunity trade sits, and it still only takes the toll to 2.29–2.43.

Weekday: Tuesday carries edge 0.6475 bps against 0.08–0.15 on the other four; toll is flat
2.58–2.77. Reported, not recommended — one axis, five cells, no correction applied.

---

## 5. Item 3 — instrument selection, the efficient frontier

### 5.1 The affordability census, at the headline contract

| symbol | n | edge bps | toll bps | e/t | net R/trade | months net+ | months edge+ |
|---|---:|---:|---:|---:|---:|---:|---:|
| **GER40** | 1,858 | 0.9107 | 0.5012 | **1.817** | **+0.01804** | 2/3 | 3/3 |
| US30_cash | 1,942 | 0.3747 | 0.4027 | 0.930 | −0.01935 | 2/3 | 3/3 |
| JP225 | 1,627 | 1.2972 | 1.4622 | 0.887 | −0.04477 | 1/3 | 3/3 |
| UK100 | 2,002 | 0.7264 | 0.8222 | 0.883 | −0.03992 | 1/3 | 3/3 |
| XAUUSD | 1,996 | 0.9061 | 1.2820 | 0.707 | −0.02465 | 1/3 | 2/3 |
| SPX500 | 1,850 | 0.4287 | 0.9408 | 0.456 | −0.09349 | 1/3 | 2/3 |
| NAS100 | 1,904 | 0.2592 | 0.5754 | 0.450 | −0.02787 | 2/3 | 2/3 |
| USDJPY | 2,442 | 0.3167 | 0.8294 | 0.382 | −0.11936 | 0/3 | 3/3 |
| … 12 more … | | 0.026 → 0.244 | 1.02 → 1.88 | 0.026 → 0.181 | | | |
| UKOIL_cash | 1,699 | 0.5302 | 8.7096 | 0.061 | −0.32351 | 0/3 | 2/3 |
| XAGUSD | 1,968 | 0.5606 | 9.6702 | 0.058 | −0.17021 | 0/3 | 1/3 |
| USOIL_cash | 1,777 | 0.3481 | 9.7724 | 0.036 | −0.30758 | 0/3 | 2/3 |
| ETHUSD | 1,366 | −2.1221 | 9.8318 | −0.216 | −0.18857 | 0/3 | 0/3 |

**One of 24 clears 1.0.** Real cost per instrument runs **0.403 → 9.832 bps, a 24.41× spread** —
far wider than the 7.35× the same instruments show in R (§6).

### 5.2 The ex-ante frontier — and why it is the one that counts

**The per-symbol cost ranking is deterministic: Spearman 0.9948 / 0.9939 / 0.9991 between the three
months. The per-symbol EDGE ranking is noise: 0.1739 / 0.1226 / 0.0078.** Picking instruments on
cost travels by construction; picking them on edge does not travel at all. (h3-F3)

| kept | added | n | keep | edge bps | toll bps | net bps | e/t | net bps / opp |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | US30_cash | 1,942 | 0.044 | 0.3747 | 0.4027 | −0.0280 | 0.930 | −0.00124 |
| **2** | **GER40** | **3,800** | **0.087** | **0.6368** | **0.4509** | **+0.1859** | **1.412** | **+0.01614** |
| 3 | NAS100 | 5,704 | 0.130 | 0.5107 | 0.4924 | +0.0183 | 1.037 | +0.00238 |
| 4 | EURUSD | 7,567 | 0.173 | 0.4054 | 0.5402 | −0.1348 | 0.750 | −0.02332 |
| 6 | UK100 | 11,623 | 0.266 | 0.3825 | 0.6252 | −0.2426 | 0.612 | −0.06445 |
| 12 | USDCHF | 23,208 | 0.530 | 0.2669 | 0.7935 | −0.5267 | 0.336 | −0.27935 |
| 18 | AUDJPY | 33,587 | 0.768 | 0.3190 | 0.9744 | −0.6554 | 0.327 | −0.50311 |
| 24 | ETHUSD | 43,755 | 1.000 | 0.2312 | 2.4571 | −2.2259 | 0.094 | −2.22594 |

The frontier's maximum in net-per-opportunity is at **k = 2**, and it is the only point in the whole
lane where a fully live-implementable arm is positive per opportunity.

**Out of sample.** Ranking instruments by **January cost only** and reading Feb+Mar:

| k | TRAIN Jan e/t | TEST Feb+Mar e/t | TEST n | TEST net bps |
|---:|---:|---:|---:|---:|
| **2** | 1.157 | **1.544** | 2,501 | +0.2459 |
| 3 | 1.261 | 0.919 | 3,732 | −0.0400 |
| 6 | 0.725 | 0.554 | 7,682 | −0.2794 |
| 24 | 0.160 | 0.061 | 28,850 | −2.3167 |

The top-6 cost order chosen on January is **identical** to the pooled order. Ranking by January
*net* instead does not travel — its k=1 reads 0.552 on test.

### 5.3 The efficiency answer

Dropping the six most expensive instruments buys **1.4827 bps of toll for 23.23 % of the
opportunities — 6.3804 bps per unit of opportunity surrendered**, the best ratio of any lever
here. Going further has diminishing efficiency (k=2: 2.197) because you start giving up cheap
instruments too.

---

## 6. Item 4 — stop width is 100 % denominational, and the estate's 12.1× is mostly stop

`cost_r = cost_price / risk_distance` is an identity, so widening the stop by factor *f* divides
`cost_r` by exactly *f* and cannot touch `cost_bps`. **Verified numerically on the real rows:**

| widen factor | mean cost_r | ratio | mean cost_bps | ratio |
|---:|---:|---:|---:|---:|
| 1.0 | 0.181834 | 1.000000 | 2.4571331 | 1.000000 |
| 1.5 | 0.121223 | 0.666667 | 2.4571331 | 1.000000 |
| 2.0 | 0.090917 | 0.500000 | 2.4571331 | 1.000000 |
| 3.0 | 0.060611 | 0.333333 | 2.4571331 | 1.000000 |
| 5.0 | 0.036367 | 0.200000 | 2.4571331 | 1.000000 |

**Log-variance decomposition**, `ln cost_r = ln cost_bps − ln rdp_bps`, identity residual
**−2.2e-16** (exact):

| term | variance | share of Var(ln cost_r) |
|---|---:|---:|
| Var(ln cost_r) | 1.14351 | 1.000 |
| Var(ln rdp_bps) — the **stop** | 1.42277 | **1.244** |
| Var(ln cost_bps) — the **money** | 0.86647 | 0.758 |
| 2·Cov | 1.14573 | 1.002 |

**The stop-width denominator contributes more variance to R-denominated cost than the real money
cost does.** Spearman(cost_r, 1/rdp) = 0.6729; Spearman(cost_r, cost_bps) = only **0.3073** — the
R-space cost number is a poor proxy for the real one.

### 6.1 The 12.1× family dispersion, re-expressed

| space | family spread (n ≥ 100) | family spread (all 10) | symbol spread |
|---|---:|---:|---:|
| cost_r (the estate's number) | **12.40×** | 12.40× | 7.35× |
| cost_bps (real money) | **1.23×** | 2.81× | **24.41×** |
| rdp_bps (the stop itself) | 14.85× | 14.85× | 18.67× |

*(The all-10 column's 2.81× is set by `current_ob_retest`, which has **three rows** in the
live-expressible book. Among the eight families with n ≥ 100 the real-money cost spread is
**1.230×** — 2.6345 bps at `cross_asset_lead_lag` against 2.1425 at `session_open_range_break`.)*

**R-denomination manufactures family cost differences and hides instrument cost differences.**
The swarm's closing observation — *"real cost per family disperses 12.1×, so there may be cells
where edge/cost > 1"* — has a premise that is **wrong** and a conclusion that is right anyway. In
price space the eight real families disperse **1.23×, not 12.1×**: the 12.4× is the stop, almost
exactly (14.85× of stop dispersion, 1.23× of money). The dispersion that actually exists and can be
harvested is across **instruments — 24.41× — and the swarm never looked there.**

**The concrete correction (h3-F7).** l10-X7.2 reports `regime_transition_break` as paying
0.0405 R and being *"the closest thing to breakeven anywhere in the estate"*. In price space that
family pays **2.6255 bps — above the 2.4571 pool mean.** It is not cheap. It looks cheap because it
emits the widest stops in the pool: **97.85 bps of price per 1R against `structural_distance_extreme`'s
6.59**. Its edge:toll of 1.375 is **entirely edge** (3.6099 bps), which is a much better reason to
like it. Symmetrically, `structural_distance_extreme` is the *most* expensive family in R (0.4208)
and **below** the pool mean in bps (2.1835).

### 6.2 And the dial does not buy affordability anywhere

Ten deciles of stop width, from 0.47 bps of price to 1,624 bps:

| decile | rdp range (bps) | cost_r | edge bps | toll bps | e/t | net R |
|---:|---|---:|---:|---:|---:|---:|
| 1 | 0.47–2.90 | 0.5309 | 0.2393 | 0.9879 | 0.242 | −0.39852 |
| 2 | 2.90–4.61 | 0.2803 | 0.3288 | 1.0288 | **0.320** | −0.19089 |
| 5 | 9.11–12.28 | 0.1352 | 0.2979 | 1.4262 | 0.209 | −0.10682 |
| 8 | 23.48–36.68 | 0.1079 | 0.7722 | 3.1374 | 0.246 | −0.08129 |
| 10 | 66.75–1624.22 | 0.0603 | −0.9639 | 6.9593 | −0.139 | −0.06477 |

**cost_r falls 8.8× across the deciles and edge:toll never exceeds 0.320.** The R-denominated cost
improves monotonically and affordability does not move. This is the sign-invariance result the
swarm established, now shown as the denominational identity it is. (h3-F6)

---

## 7. Item 5 — holding time and swap

**There is no swap lever on this horizon, and the frozen model charges one anyway.**

| | measured |
|---|---:|
| trades whose 2 h holding window can reach a broker rollover (NY 17:00) | **363 of 43,755 = 0.83 %** |
| broker-true swap charged in the 2.4571 bps toll | **0.0 bps** |
| frozen model's swap charge | 0.0118 R = **0.1727 bps** |
| frozen model's total | 6.3891 bps |
| share of the frozen toll that is uncollectable carry | **2.70 %** |

Closing before the swap boundary changes nothing because essentially nothing crosses it. (h3-F8)

**The real lever on this axis is amortisation, and it is measured negative.** A round-trip toll is a
fixed charge, so holding longer spreads it over more gross move:

| contract | mean hold (min) | edge bps | toll bps/hour held | e/t |
|---|---:|---:|---:|---:|
| TRAIL025 (headline) | 27.7 | +0.2312 | 5.3304 | 0.094 |
| INC (2R/−1R) | 65.5 | −0.2954 | **2.2525** | −0.120 |

**`INC` more than halves the toll per hour held and its edge goes negative.** The whole contract
menu at k=5 says the same thing — every alternative to `TRAIL025` costs edge and none costs less
toll, because one round trip is charged whatever the exit:

| contract | edge bps | toll bps | e/t | net R |
|---|---:|---:|---:|---:|
| **TRAIL025** | **+0.2312** | 2.4571 | **0.094** | −0.14349 |
| STOPONLY | −0.1321 | 2.4571 | −0.054 | −0.15996 |
| INC | −0.2954 | 2.4571 | −0.120 | −0.18117 |
| TS90S1 | −0.3192 | 2.4571 | −0.130 | −0.16309 |
| T3S1 | −0.3238 | 2.4571 | −0.132 | −0.17522 |
| TS60S1 | −0.4479 | 2.4571 | −0.182 | −0.17258 |

Conditioning on *realised* hold (descriptive, not tradeable — the hold is an outcome): the 6–15 min
bucket carries 52.8 % of trades at edge +2.0878 bps against a 2.4037 bps toll (e/t 0.868); trades
that run to the 2 h horizon carry edge −12.4134 bps.

---

## 8. Item 6 — every lever ranked

Ranked by **bps of toll recovered per unit of opportunity surrendered**. `d_edge` is carried in the
same row because ranking on toll alone is exactly how the passive lever looks best and performs
worst.

| lever | keep | d_toll bps | d_edge bps | efficiency | net bps / opp | live today |
|---|---:|---:|---:|---:|---:|:--:|
| resting limit at the decision price | 0.981 | **+0.9772** | **−2.0227** | 52.594 | −3.21065 | no |
| **drop 6 dearest instruments** | 0.768 | **+1.4827** | +0.0878 | **6.380** | −0.50311 | **YES** |
| keep 12 cheapest instruments | 0.530 | +1.6636 | +0.0357 | 3.543 | −0.27935 | YES |
| keep 8 cheapest instruments | 0.367 | +1.7727 | +0.0787 | 2.802 | −0.13757 | YES |
| keep 6 cheapest instruments | 0.266 | +1.8320 | +0.1513 | 2.495 | −0.06445 | YES |
| keep 3 cheapest instruments | 0.130 | +1.9647 | +0.2795 | 2.259 | **+0.00238** | YES |
| **keep 2 cheapest instruments** | 0.087 | +2.0063 | +0.4056 | 2.197 | **+0.01614** | **YES** |
| passive + no-retrace ≥ 5 min | 0.104 | +0.9886 | +1.2552 | 1.104 | +0.00186 | no |
| **passive + no-retrace ≥ 10 min** | 0.069 | +0.9847 | **+1.9100** | 1.057 | **+0.04593** | no |
| passive + no-retrace ≥ 15 min | 0.051 | +0.9953 | +1.5736 | 1.049 | +0.01766 | no |
| delay to minute 20 | 0.998 | +0.0004 | +0.3083 | 0.265 | −1.91408 | YES |
| keep 2 cheapest NY hours | 0.118 | +0.1840 | +0.0975 | **0.209** (0.449 hour-consistent) | −0.22994 | YES |
| keep 6 cheapest NY hours | 0.364 | +0.1045 | −0.0348 | 0.164 (0.498 hour-consistent) | −0.78465 | YES |
| drop the rollover hour NY 17 | 0.979 | −0.0858 | +0.0101 | −4.057 | −2.25303 | YES |
| **stop widening, any factor** | 1.000 | **0.0000** | 0.0000 | — | −2.22594 | YES |
| **swap avoidance** | 1.000 | **0.0000** | 0.0000 | — | −2.22594 | YES |
| exit contract change (4 arms) | 1.000 | 0.0000 | −0.363…−0.555 | — | −2.59…−2.78 | YES |

**Ranking, in one sentence: instrument selection is the only lever that moves the toll materially
and is ex-ante and travels; the passive entry lever is the only one that could move it more and it
is destroyed by the fill it requires; hour selection is a tenth the size; and stop width, swap and
exit contract move the toll by exactly zero.**

### 8.1 Composites, priced JOINTLY

e-stack proved a naive sum of this estate's levers over-counts by 66.8 %, so nothing here is summed.

| composite | n | keep | edge bps | toll bps | net bps | e/t | net bps/opp | months e/t≥1 | live |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| A. instruments(2) | 3,800 | 0.087 | 0.6368 | 0.4509 | +0.1859 | 1.412 | +0.01614 | 3/3 | YES |
| B. instruments(2) + drop NY17 | 3,780 | 0.086 | 0.6386 | 0.6056 | +0.0330 | 1.054 | +0.00285 | 1/3 | YES |
| C. instruments(2) + delay 20 | 3,792 | 0.087 | 0.3806 | 0.4508 | −0.0702 | 0.844 | −0.00608 | 1/3 | YES |
| E. instruments(6) + delay 20 | 11,605 | 0.265 | 0.1866 | 0.6251 | −0.4385 | 0.299 | −0.11630 | 0/3 | YES |
| G. no-retrace≥10, market on touch | 3,005 | 0.069 | 2.1412 | 2.5583 | −0.4171 | 0.837 | −0.02865 | 0/3 | YES |
| **H. no-retrace≥10 + market on touch + instruments(6)** | **814** | 0.019 | 1.3118 | 0.6231 | **+0.6887** | **2.105** | +0.01281 | **3/3** | **YES** |
| I. PASSIVE no-retrace≥10 | 3,005 | 0.069 | 2.1412 | 1.4724 | +0.6687 | 1.454 | +0.04593 | 3/3 | no |
| **J. PASSIVE no-retrace≥10 + instruments(6)** | 814 | 0.019 | 1.3118 | 0.3509 | +0.9609 | **3.739** | +0.01788 | 3/3 | no |
| K. PASSIVE no-retrace≥10 + instruments(12) | 1,577 | 0.036 | 0.8682 | 0.4954 | +0.3729 | 1.753 | +0.01344 | 3/3 | no |

**Two interactions worth naming.** (1) The delay lever, worth +0.31 bps alone, is **negative** on
the cheap-instrument cell (A 1.412 → C 0.844): the two levers are substitutes, exactly the structure
e-stack found. (2) Dropping NY 17 from the cheap-2 cell *hurts* (1.412 → 1.054) — but that comparison
also switches the cost basis to hour-aware, and the honest number is that **cheap-2 under hour-aware
costing is 1.053 with or without the rollover hour**. Which is the real caveat on that cell, and it
is in §9.

---

## 9. The cells — what was actually found

Reported with n and caveat, no multiplicity correction claimed. Two cost bases and two value spaces
are shown for every cell because **they disagree, and the disagreement is informative**.

### 9.1 The cell that survives every check: `regime_transition_break`

**Rule:** trade only the `regime_transition_break` origin family, at the plain headline arm
(at-market, +5 min, 0.25R trail). No conditioning, no threshold search, one pre-existing
categorical cut.

| | flat cost | hour-aware cost |
|---|---:|---:|
| n | 828 | 828 |
| edge | 3.6099 bps | 3.6099 bps |
| toll | 2.6255 bps | 2.7836 bps |
| **edge : toll** | **1.375** | **1.297** |
| net bps | +0.9844 | +0.8263 |
| **net R / trade** | **+0.01526** | **+0.00874** |

| month | n | e/t | net bps | net R |
|---|---:|---:|---:|---:|
| 2026-01 | 297 | 1.339 | +0.8908 | +0.01100 |
| 2026-02 | 253 | 1.715 | +1.7882 | +0.02226 |
| 2026-03 | 278 | 1.129 | +0.3527 | +0.01345 |

**Why it is the strongest thing in this lane.** Positive in **both** value spaces at **both** cost
bases; **3 of 3 months** above 1 and R-positive; spread across **all 24 instruments** (17–44 rows
each) and all 24 NY hours; and **net R stays positive in all 24 leave-one-instrument-out arms**
(+0.00617 … +0.02498). It is not one symbol.

**Caveats, stated plainly.** n = 828. Day-block bootstrap p(net R ≤ 0) = **0.156**, p(net bps ≤ 0) =
0.277 — **not significant**. 32 of 63 days are R-positive and the best single day carries 29.0 % of
the R total (top three, 74.6 %). In bps the day concentration is worse than that — the top day is
100.3 % of the bps total, i.e. the rest of the sample nets out. And it is one of ten origin
families, so it carries a 10-look bill it has not been charged. (h3-F10)

### 9.2 The best fully live-implementable cell: NO-RETRACE + cheap instruments

**Rule, executable with the engine that exists today.** At the decision, place nothing. Watch. If
price has **not** traded back through the decision price for 10 minutes, then send a **market**
order the moment it next does. Restrict to the six cheapest instruments by broker-true cost
(US30_cash, GER40, NAS100, EURUSD, GBPUSD, UK100). Exit on the 0.25R trail.

| | flat cost | hour-aware cost |
|---|---:|---:|
| n | 814 | 814 |
| edge | 1.3118 bps | 1.3118 bps |
| toll | 0.6231 bps | 0.8894 bps |
| **edge : toll** | **2.105** | **1.475** |
| net bps | +0.6887 | +0.4225 |
| net R / trade | **+0.014213** | −0.023865 |
| bootstrap p(net bps ≤ 0) | **0.0625** | 0.190 |
| bootstrap p(net R ≤ 0) | 0.2825 | — |

Months: e/t **1.331 / 2.149 / 2.888** (3/3 above 1). Entry is at MARKET, so the cell is
**convention-invariant** (§3.4) and pays the full spread — no order type the estate lacks.

The whole threshold curve, so the argmax is visible in context rather than quoted alone:

| no-retrace ≥ (min) | n | e/t | net bps | net R | p(net bps ≤ 0) |
|---:|---:|---:|---:|---:|---:|
| 0 | 11,425 | −2.063 | −1.9147 | −0.21554 | 1.000 |
| 1 | 2,608 | 1.142 | +0.0895 | −0.01528 | 0.376 |
| 5 | 1,220 | 1.687 | +0.4300 | −0.00704 | 0.159 |
| 9 | 871 | 1.993 | +0.6188 | +0.01099 | 0.087 |
| **10** | **814** | **2.105** | **+0.6887** | **+0.01421** | **0.062** |
| 12 | 736 | 1.786 | +0.4904 | +0.01673 | 0.135 |
| 15 | 637 | 1.506 | +0.3157 | +0.01956 | 0.265 |
| 20 | 499 | 1.168 | +0.1040 | +0.00408 | 0.426 |
| 30 | 351 | 0.571 | −0.2667 | −0.02292 | 0.670 |

It is a smooth hump above 1.0 from minute 1 to minute ~24, not a spike — but **the peak was chosen
in sample from ~30 thresholds** and must be read that way.

**Caveats.** n = 814. **Top 3 days carry 56.6 % of the bps total**; 33 of 63 days positive.
Per-symbol the cell is carried by GER40 (e/t 6.733) — dropping GER40 leaves e/t 1.381 in bps but
takes net R to **−0.00035**. Two of the six instruments are net-negative inside it (EURUSD 0.753,
GBPUSD 0.203). Under hour-aware costing net R goes negative. (h3-F11)

### 9.3 The cost-only cell that travels out of sample

**Rule:** trade only the two cheapest instruments by broker-true toll. Selection uses **no outcome
data at all** and the cost order is 0.994–0.999 stable, so it travels by construction.

| | TRAIN (Jan) | TEST (Feb+Mar) | pooled |
|---|---:|---:|---:|
| n | 1,299 | 2,501 | 3,800 |
| edge:toll | 1.157 | **1.544** | 1.412 |
| net bps | +0.0704 | +0.2459 | +0.1859 |

**Caveats.** Positive in bps and **negative in R** (−0.00107/trade). Under hour-aware costing
edge:toll falls to **1.053** and months-above-1 falls 3/3 → 1/3. Bootstrap p(net bps ≤ 0) = 0.261.
Extending to three instruments breaks it on test (0.919). (h3-F12)

### 9.4 Cells that look like they pay in bps and do not pay in money

**NY hour 13** reads edge 3.9942 bps, toll 2.5893, **e/t 1.543 — and net R = −0.1301/trade, negative
in all three months.** The two cheapest instruments read +0.1859 bps and −0.00107 R. These cells are
carried by wide-stop trades that dominate a price-space average and are small in risk-units.

**This is a standing hazard for the whole swarm, not just this lane.** bps decides whether a trade
is affordable; R is what compounds under fixed-fractional sizing. **Any cell quoted in bps alone can
be a denomination artifact.** Only two cells in this lane are positive in both spaces:
`regime_transition_break` and the no-retrace/cheap-6 cell. (h3-F9)

There is a live corollary: **if position size were set by price risk rather than by R, more of these
cells would pay** — that is a sizing-policy question, and it is Borhen's, not this lane's.

### 9.5 Smaller cells, listed rather than recommended

From the symbol × no-retrace grid (n ≥ 200, full table in `H3_CELLS_V1.json`):
XAUUSD no-retrace≥5 delay 5 (n=285, e/t 3.839, 2/3 months); GER40 no-retrace≥5 delay 5 (n=224,
3.209, 2/3); XAGUSD no-retrace≥10 delay 10 (n=210, 1.551, **3/3**, but on a 9.67 bps toll);
US30_cash delay 30 unconditional (n=1,941, 1.650, **3/3**); JP225 delay 20 (n=1,624, 1.210, 2/3).
These are reported because under-reporting is the failure mode; none has been checked to the depth
of §9.1–9.3.

---

## 10. Findings

| id | finding |
|---|---|
| **h3-F1** | **The toll cannot be cut 10×. Floor = commission only = 0.5686 bps, a 4.32× cut (76.86 % removable). 10.63× is required. At the floor edge:toll is still 0.4066.** |
| h3-F2 | Passive entry is the largest removable component and pays under **neither** quote convention: MID saves 0.905 bps and destroys 2.02; BID saves 1.810 and destroys 3.07. 76.2 % of passive fills land in the first 60 s at edge −2.6402 bps. |
| h3-F3 | Instrument selection is the only large toll lever and it is ex-ante: cost rank Spearman 0.994–0.999 across months, edge rank 0.008–0.174. Dropping the 6 dearest buys 1.4827 bps for 23.2 % of the book. |
| h3-F4 | Hour selection is an order of magnitude weaker: 0.4255 bps of toll for 91.85 % of the book, efficiency **0.4633** against the instrument lever's **6.3804** — a 13.8× gap, and the whole hour frontier sits in 0.447–0.511. |
| h3-F5 | Hour-aware costing **raises** the toll 8.63 % (2.4571 → 2.6692). The rollover hour costs 8.5091 bps against the 1.8826 the flat model charges — understated 4.52×. Mapping validated: 13 of 24 instruments peak at NY 17:00. |
| h3-F6 | Stop width is 100 % denominational (cost_bps invariant to any widen factor, verified to 7 decimals). Family cost disperses 12.40× in R and only **1.23×** in bps among the eight families with n ≥ 100 (2.81× including a 3-row family); instruments invert, 7.35× in R against **24.41×** in bps. |
| h3-F7 | **Correction to l10-X7.2:** `regime_transition_break` is not cheap. It pays 2.6255 bps, above the 2.4571 pool mean; its 0.0405 R is a 97.85 bps stop. Its edge:toll 1.375 is entirely edge. |
| h3-F8 | No swap lever exists: 0.83 % of trades can reach a rollover, broker-true swap is 0.0 bps, and the frozen model bills 0.1727 bps (2.70 % of its own toll) of uncollectable carry. |
| h3-F9 | bps and R disagree in **sign** on several cells (NY13 +1.410 bps / −0.130 R). Any cell quoted in bps alone can be a stop-width artifact. |
| h3-F10 | **CELL** `regime_transition_break`: e/t 1.375 flat / 1.297 hour-aware, net R +0.01526, **3/3 months, both spaces, both cost bases, robust to dropping any instrument**. n=828, bootstrap p 0.156, 1 of 10 families. |
| h3-F11 | **CELL** no-retrace ≥10 min + market on touch + 6 cheapest instruments: e/t **2.105**, net R +0.014213, 3/3 months, **live-implementable today**, convention-invariant. n=814, p 0.0625, top-3 days 56.6 %, GER40-carried in R. |
| h3-F12 | **CELL** two cheapest instruments chosen on January cost only: TRAIN 1.157 → **TEST 1.544** on never-used Feb+Mar. Positive in bps, negative in R; 1.053 under hour-aware cost. |
| h3-F13 | The entry delay is a bigger bps lever than the whole removable half-spread and costs zero opportunity: **+1.0425 bps** from minute 0 to minute 20 (+0.7342 to the headline minute 5), toll identical at every delay, 3/3 months. |
| h3-F14 | The 60-second cancel is an EDGE lever worth +0.4492 bps and a toll lever worth +0.0053 bps — and it lives on `born_resting`, which the live engine cannot place. Re-resting after a cancel is worse than not cancelling. |
| h3-F15 | Under the headline trailing contract the exit half-spread is 0 % addressable (93.70 % stops, 0.00 % targets). Under a target contract it is worth 0.176 bps and costs 0.526 bps of edge. |

---

## 11. What would change these answers

1. **The quote side of the M1 archive.** Settling bid vs mid changes the passive-entry arithmetic by
   up to the whole spread. It does not change h3-F1 or the sign of h3-F2, and it does not touch the
   §9.2 cell, which is entered at market.
2. **A tick-measured hour profile from the pool's own months.** The hour model transfers a
   2026-06/07 capture onto Jan–Mar via NY local hour. The level is already a transfer (the flat
   median is from the same capture); adding the hour shape is the same class of assumption, and the
   naive-mapping arm moves the pooled toll by only 0.045 bps.
3. **Commission truth per account.** Commission is 23.14 % of the toll and the *whole* irreducible
   floor. Session LN's broker-true commission landed as the fourth cost term after this cohort was
   built; if the live commission differs from `e_lib`'s ported map, h3-F1's floor moves one-for-one.
4. **Sizing basis.** Every "negative in R, positive in bps" cell in §9.4 flips if size is set by
   price risk. That is an owner decision, not a measurement.
5. **A fourth month.** Every cell in §9 rests on 63 days and n in the hundreds. The bootstrap
   p-values are 0.06–0.28. None of them is established; all of them are worth carrying forward.

---

## 12. Files and reproduction

**Scripts** (all in this directory, run in order):
`h3_lib.py` · `h3_01_anchor.py` · `h3_02_passive_build.py` · `h3_03_hours.py` · `h3_04_passive.py` ·
`h3_05_entry2.py` · `h3_06_instruments.py` · `h3_07_cells.py` · `h3_08_denom_swap.py` ·
`h3_09_rank.py` · `h3_10_strict.py` · `h3_11_topcell.py` · `h3_12_result.py`

**Artifacts:** `H3_ANCHOR_V1.json` · `H3_HOURS_V1.json` · `H3_ENTRY_MECHANICS_V1.json` ·
`H3_ENTRY2_V1.json` · `H3_INSTRUMENTS_V1.json` · `H3_DENOM_SWAP_V1.json` · `H3_CELLS_V1.json` ·
`H3_RANK_V1.json` · `H3_STRICT_V1.json` · `H3_TOPCELL_V1.json` ·
`H3_PASSIVE_ROWS_2026{01,02,03}.jsonl.gz` (43,755 rows, the passive ladder) ·
`H3_STRICT_ROWS_V1.jsonl.gz` (43,755 rows, both fill conventions) · **`h3_RESULT.json`**

**Inputs consumed, none modified:** `e_JAN/FEB/MAR_ATMKT_V1.jsonl.gz`,
`e_JAN/FEB/MAR_BASE_V1.jsonl.gz`, `L10X_TICK_SPREAD_V1.json`,
`L10X_LIVE_COST_PRICEUNITS_V1.json`, `e_lib.py`, `e_build_month.py`, and the true-UTC M1 bars at
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/`.

Total wall time ≈ 6 minutes. No sealed replay, no VPS, no broker-capable script, no commit.
