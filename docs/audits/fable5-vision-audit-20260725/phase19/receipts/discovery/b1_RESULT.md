# b1 — BUILD THE BOOK

**One specification, priced jointly, ablated, controlled, stressed, and read once on two
months it never saw.**

Every number below is produced by a script in this directory and lands in
`b1_RESULT.json` (343 KB) plus the eleven step artifacts `B1_*_V1.json`. Nothing is
estimated.

---

## 0. THE ANSWER, IN THREE SENTENCES

**b1-BOOK-V1 is net-positive on the window it was built from and net-negative on the
window it was not.** On January+February+March 2026 it earns **+0.076498 R/trade
(+0.5673 bps) net of the strictest broker-true toll in the wave**, edge:toll **2.6391**,
on 3,728 trades — 8.52 % of the 43,755-trade book — turning the swarm's −0.18199 R/trade
into a profit and surviving a **doubling of the toll**. On April+May 2026, read once at
the frozen specification, it earns **−0.044700 R/trade**, edge:toll **0.064**, because its
**gross collapsed 97 %** (+0.11498 → +0.00308) while its toll barely moved (0.04646 →
0.04778). The failure is diagnosed exactly: the gate has two limbs, the instrument limb
travels (cost rank Spearman **0.9922**, the same three instruments in all five months) and
the hour limb **inverts** — in-window the cheap hours beat the expensive hours by
+0.136 R/trade, out of window they lose to them by 0.099.

**And the caveat that outranks both:** dropping the best **18 trades of 3,728** (0.5 %)
takes the in-window book to **−0.004307**. Capping gains at +5R takes it to **−0.021465**.
The entire expected value lives in **106 trades (2.84 %)** that run past +5R inside two
hours. This is a convexity book, and a convexity mean measured on 63 days is exactly the
kind of number that does not replicate — and did not.

---

## 1. SUBSTRATE AND REPRODUCTION

| | |
|---|---|
| substrate | `h5_SUBSTRATE_5M.jsonl.gz`, **69,480** live-expressible at-market candidates |
| months | 2026-01 (14,905) · 02 (13,966) · 03 (14,884) · **04 (13,837) · 05 (11,888)** |
| hunt window | 43,755 — the swarm's own live-placeable book |
| held out | 25,725 (April+May), built by h5 with the **unmodified** `e_build_atmkt.py` |
| cost join | h1's four-term broker-true cost, **43,755 / 43,755 joined, 0 missed** |

**Four cost bases, all reproduced:**

| basis | R/trade | bps | source |
|---|---:|---:|---|
| frozen (shipped) | 0.663161 | — | pool |
| flat tick-median spread (swarm) | 0.181834 | 2.4571 | `cost_true` |
| **hour-true three-term** | 0.220328 | 2.6692 | `cost_true_hour` — the only basis that exists on Apr/May |
| **h1 four-term broker-true** | **0.245214** | **2.9744** | `+ BTCUSD/ETH commission fix + swap` — **strictest, used for every hunt-window headline** |

**Reproduction of the lanes this book is built from** (`B1_REPRO_V1.json`):

| target | published | b1 |
|---|---|---|
| swarm headline, whole book | gross +0.038342 / cost 0.181834 / net −0.143492 | **identical** |
| h6 cell B | n 3,807 / gross +0.114982 / cost 0.046457 / net +0.068525 / ratio 2.475 | **identical** |
| h5 five-month book | n 69,480 / gross 0.03831 / toll 0.23020 / net −0.19188 / ratio 0.1664 | +0.038313 / 0.230196 / −0.191884 / 0.166434 |
| h3 `regime_transition_break` | n 828 / net +0.01526 | +0.015260 |
| h1 four-term toll | 0.245214 R / 2.9744 bps | **identical** |

**Independent validation.** `b1_06_placebo.py` re-walks all 3,728 book rows straight off
the M1 CSVs with its own bar reader and its own exit walk. Max absolute difference against
the substrate: **4.98 × 10⁻⁹** on 3,728 of 3,728 rows. The chain from bars to book is
verified end to end.

---

## 2. THE SPECIFICATION — `b1-BOOK-V1`

Every limb was published by another lane **before** b1 ran. Nothing here is a b1 invention.

```
UNIVERSE   all 24 pool instruments. No instrument name appears in the rule.

GATE       At the decision instant compute the candidate's own broker-true
           round-trip toll in basis points of notional:

               toll_bps = spread_bps(symbol, broker_hour)      # tick-median, hour-aware
                        + commission_bps(symbol)               # broker schedule
                        + slip_bps(symbol)                     # measured live entry slip
                        + swap_bps  if  decision+120min crosses a rollover

           ADMIT if toll_bps <= 0.60.   REJECT otherwise.
           All four terms are knowable at the decision instant -> the gate is EX-ANTE.
           [threshold from h6 cell B]

ENTRY      Place NOTHING at the decision. Wait 3 minutes.
           Enter at MARKET on the close of minute 3.
           [k=3 from h6 cell B; k in {1,2,3} is a plateau, k=0 is negative]

EXIT       Stop at -1R, measured from the FILL price (R frame rebased by the
           3-minute drift), fixed, never moved.
           NO take-profit.
           NO trailing stop.
           Close at MARKET at decision + 120 minutes.
           [h6 cell B. Trail-free by construction, so no number in this receipt
            contains the +0.084 R/trade bar-resolution premium a next-bar-checked
            trail manufactures — B613 / AD 95.8% intrabar / h6-F8]

SIZING     Fixed fractional on the declared risk distance (constant-R book).

NOT USED   no family filter, no side filter, no probability filter,
           no execution-fill-probability floor (identically zero on this
           cohort — h6-F4, confirmed here), no cancel band (there is no
           resting order to cancel), no regime filter.
```

**What the gate resolves to — and it is the same in every month, including the two it
never saw:**

| window | n | instruments |
|---|---:|---|
| January only | 1,307 | GER40, NAS100, US30_cash |
| February only | 1,237 | GER40, NAS100, US30_cash |
| March only | 1,263 | GER40, NAS100, US30_cash |
| **April only** | 1,181 | GER40, NAS100, US30_cash |
| **May only** | 1,041 | GER40, NAS100, US30_cash |

Admission share inside those three: US30_cash **97.4 %**, GER40 **57.5 %**, NAS100
**40.3 %**; every other instrument **0 %**. The instrument set is therefore *not*
hindsight — it is what a purely-cost, purely-ex-ante rule returns in each month
independently.

---

## 3. Q1 — PRICED JOINTLY, JANUARY + FEBRUARY + MARCH

At the **h1 four-term broker-true** cost (`B1_FINAL_V1.json` → `HEADLINE_hunt3m_h1cost`):

| | |
|---|---:|
| trades | **3,728** (8.52 % of 43,755) over **63 days**, 3 instruments |
| gross | **+0.123169 R** — **+1.028972 bps** |
| cost | 0.046671 R — 0.461624 bps |
| **NET** | **+0.076498 R/trade** — **+0.567348 bps** |
| **edge : toll** | **2.6391** in R · **2.2290** in bps |
| win rate | 36.11 % net · 36.56 % gross |
| t(net) | **+2.267** trade-level · **+1.612** day-clustered |
| day positivity | **32 / 63** days net-positive |
| total | **+285.19 R** · max drawdown **−79.77 R** · return/DD **3.58** |
| months | Jan **+0.11345** · Feb **+0.05627** · Mar **+0.05771** — 3 / 3 positive |
| **truncation share** | **49.25 %** exit at the 120-minute bell · 50.75 % stop out |
| day-block bootstrap | 95 % CI **[−0.01176, +0.17082]**, **P(net ≤ 0) = 0.0480** |

**The cost model does not matter for this book, and that is measurable.** On these 3,728
rows the h1 four-term basis and the hour-true three-term basis are **byte-identical** —
`max |Δ| = 0.0` on 3,728 of 3,728 rows — because the three admitted instruments are index
CFDs on which FTMO charges **zero commission**, **zero** of the admitted rows cross a
rollover, and both models read the same hour-aware tick spread table and the same measured
slippage. Book-wide the two models differ on **31,407 of 43,755** rows (0.245214 vs
0.220328 R). So the in-window number and the April/May number are on exactly the same cost
arithmetic, with no basis mismatch to explain the gap. The flat swarm basis gives
**+0.077650** (ratio 2.7059) — a 1.5 % difference.

**Charging swap at the gate is itself worth +0.014348 R/trade.** The three-term gate admits
**79 extra rows**, all at broker hours 22–23, all swap-crossing; at the h1 basis those 79
book **−0.61476 R/trade**. Gating on the four-term toll (n = 3,728, +0.076498) instead of
the three-term one (n = 3,807, +0.062150 *at the same h1 cost*) is a free improvement that
the swarm's cost model could not express.

**Return distribution — this is the book's real shape:**

| | |
|---|---:|
| stopped at −1R | 50.75 % |
| ran to the bell | 49.25 %, averaging **+1.2806 R** |
| p50 gross | **−1.000** |
| p75 / p90 / p95 / p99 | +0.580 / +2.035 / +3.438 / +7.852 |
| max | **+38.70 R** (US30_cash, 2026-01-21, a 1.246 % move against a 3.22 bps stop) |
| share > +2R | 10.14 % · share > **+5R** | **2.84 %** (106 trades) |

**Daily economics** (`B1_DAILY_V1.json`):

| | hunt | OOS | pooled 5m |
|---|---:|---:|---:|
| trades/day | 60.4 | 58.5 | 59.7 |
| **R/day mean** | **+4.141** | **−2.614** | +1.600 |
| R/day **median** | **+0.011** | — | — |
| R/day sd | 22.21 | 18.31 | 21.00 |
| worst day | −29.97 | −38.97 | −38.97 |
| best day | +71.05 | — | — |
| daily Sharpe (ann. ×√252) | 0.186 (2.96) | −0.143 | 0.076 (1.21) |

**Concurrency is a hard constraint on all of it.** Each trade occupies 120 minutes:
**max 31 simultaneous open positions, mean 3.40** over the span. A constant-R book at 3.4
mean concurrency is running 3.4× nominal risk on average and 31× at the peak, so the
+4.141 R/day is *not* bankable at full per-trade risk — it must be divided by roughly the
concurrency before any account-level claim is made.

---

## 4. Q2 — IS IT NET-POSITIVE? THE PLAIN ANSWER

### 4.1 On the window it was built from: **YES**

**+0.076498 R/trade**, edge:toll **2.6391**, 3/3 months, P(net ≤ 0) = 0.048. It survives
every cost stress:

| stress | cost R | net R | edge:toll | t_day |
|---|---:|---:|---:|---:|
| base (h1 four-term) | 0.04667 | **+0.07650** | 2.639 | +1.61 |
| × 1.25 | 0.05834 | +0.06483 | 2.111 | +1.37 |
| × 1.50 | 0.07001 | +0.05316 | 1.759 | +1.12 |
| **h4 all-in live-grounded × 1.577** | 0.07360 | **+0.04957** | 1.673 | +1.04 |
| × 2.00 | 0.09334 | **+0.02983** | **1.320** | +0.63 |
| + l10-F9 exit slippage on stop exits | 0.06303 | +0.06014 | 1.954 | +1.26 |
| + exit slippage **and** × 2.0 | 0.10970 | **+0.01347** | **1.123** | +0.28 |
| January-era spread regime | 0.04729 | +0.07588 | 2.605 | +1.60 |
| + entry slippage doubled | 0.05851 | +0.06466 | 2.105 | +1.36 |

**The cost model is not what is holding it up.** Doubling the entire toll and adding the
estate's measured exit slippage still leaves it above 1.

### 4.2 On the two months it never saw: **NO**

Read **once**, at the frozen specification, at the hour-true basis (the only one that
exists on April/May):

| | hunt (Jan–Mar) | **OOS (Apr+May)** |
|---|---:|---:|
| n | 3,807 | **2,222** |
| gross | +0.114980 | **+0.003080** |
| cost | 0.046460 | 0.047780 |
| **net** | **+0.068530** | **−0.044700** |
| edge : toll | 2.475 | **0.064** |
| day-clustered t | +1.49 | −0.88 |
| days positive | 32 / 63 | **11 / 38** |
| bootstrap P(net ≤ 0) | 0.048 | **0.827** |

Month chain: **+0.10906 · +0.04997 · +0.04475 · +0.00584 · −0.10203** — monotone decay,
slope **−0.0466 R/trade per month** on net and **−0.0499** on gross.

### 4.3 How far short, and what would have to change

To break even out of sample the book needs its gross **× 15.505**, or a **93.55 %** cut in
its toll. Neither exists: h3 measured the mechanical toll floor at commission-only, a
**4.32×** cut, and the book is already inside the cheapest 8.5 % of the estate's rows.

### 4.4 The mechanism of the failure — measured, not asserted

**It is not the contract.** The ungated 24-instrument cohort at the *identical* contract
(k=3, STOPONLY) is flat across all five months: gross **+0.0262 · +0.0350 · +0.0267 ·
+0.0021 · +0.0184**, slope −0.0048/month. The rows the gate *rejects* are equally flat
(+0.0121 · +0.0291 · +0.0224 · −0.0028 · +0.0256). Only the gated cells decay.

**It is the hour limb of the gate, and it inverts.**

| limb | hunt net | **OOS net** | 5-month net | 5-month ratio |
|---|---:|---:|---:|---:|
| both limbs (b1-BOOK-V1) | +0.06853 | **−0.04470** | +0.02680 | 1.571 |
| instrument limb only (3 survivors, all hours) | +0.02327 | −0.00983 | **+0.01082** | **1.169** |
| **hour limb: cheap hours** inside the 3 | **+0.06853** | **−0.04470** | +0.02680 | 1.571 |
| **hour limb: expensive hours** inside the 3 | **−0.06756** | **+0.05398** | −0.02013 | 0.792 |

In-window the cheap hours beat the expensive hours by **+0.1361 R/trade**. Out of window
they *lose* to them by **0.0987**. A complete sign reversal on the limb carrying most of
the in-window effect.

**Rank persistence, hunt → OOS, at this book's own contract, all 24 instruments:**

| quantity | Spearman | Pearson |
|---|---:|---:|
| **cost** | **0.9922** | 0.9998 |
| **gross edge** | **0.1478** | 0.1492 |

This reproduces h5's control (0.826 cost / 0.024 gross) on a different contract and a
different population. **Affordability is a persistent property of the broker; edge is
not a persistent property of the instrument.** A book selected on affordability
re-discovers the fee schedule.

### 4.5 The concentration caveat, which is larger than either

| the book with … | net R/trade | edge:toll |
|---|---:|---:|
| all 3,728 trades | **+0.076498** | 2.639 |
| the best 3 trades (0.1 %) removed | +0.051587 | 2.107 |
| the best **18** trades (0.5 %) removed | **−0.004307** | 0.907 |
| the best 37 (1.0 %) removed | −0.050382 | — |
| the best 186 (5.0 %) removed | −0.261513 | — |
| gains winsorised at the p99 gross | +0.027138 | — |
| gains **capped at +5R** | **−0.021465** | — |
| gains capped at +3R | −0.105256 | — |
| gains capped at +2R | −0.184944 | — |

The top 1 % of trades supply **165 %** of total net; the top 10 supply **73.6 %**. The
tail is not an artifact — the twenty largest are ordinary index moves (median implied move
for a >5R trade is **0.568 %**, max 1.903 %) against unusually tight risk distances
(2–5 bps against a book median of 16.1 bps). But an expected value carried by 106 trades
in 63 days is a **convexity** claim, and it is the reason a 2-month read can and did
reverse it.

---

## 5. Q3 — ABLATION, ON THE SAME ROWS

**Leave one out** (all on the identical 3,728 rows, identical cost):

| variant | n | net R | edge:toll | Δ vs book |
|---|---:|---:|---:|---:|
| **BOOK (all limbs)** | 3,728 | **+0.07650** | **2.639** | — |
| no gate (all 24 instruments) | 43,755 | −0.21604 | 0.119 | **+0.29254** |
| gate replaced by the shipped R rule (`total_r ≤ 0.15`) | 26,571 | −0.08913 | 0.056 | +0.16563 |
| no entry delay (k = 0, the shipped instant) | 3,728 | −0.00991 | 0.788 | **+0.08641** |
| entry delay k = 5 (the swarm's) | 3,728 | +0.02832 | 1.607 | +0.04818 |
| exit = swarm TRAIL025 | 3,728 | −0.00105 | 0.978 | **+0.07755** |
| exit = shipped 2R target (INC) | 3,728 | +0.00360 | 1.077 | +0.07290 |
| exit = 3R target | 3,728 | +0.03257 | 1.698 | +0.04393 |
| exit = 90-minute time stop | 3,728 | +0.06219 | 2.332 | +0.01431 |
| exit = 60-minute time stop | 3,728 | +0.03544 | 1.759 | +0.04105 |
| **nothing (swarm repaired contract, whole book)** | 43,755 | **−0.20687** | 0.156 | +0.28337 |

**Add one in**, starting from the swarm's repaired contract on the whole book:

| | n | net R | edge:toll |
|---|---:|---:|---:|
| swarm repaired contract (baseline) | 43,755 | −0.20687 | 0.156 |
| + gate only | 3,728 | +0.00275 | 1.059 |
| + entry k = 3 only | 43,755 | −0.20932 | 0.146 |
| + trail-free exit only | 43,755 | −0.22334 | 0.089 |
| + gate + k = 3 | 3,728 | −0.00105 | 0.978 |
| + gate + exit | 3,728 | +0.02832 | 1.607 |
| + k = 3 + exit | 43,755 | −0.21604 | 0.119 |
| **+ all three (= BOOK)** | 3,728 | **+0.07650** | **2.639** |

**No single limb pays. No pair pays. Only the triple pays.** Add-one deltas from the
baseline sum to **+0.19070** against a joint gain of **+0.28337** — the limbs
**under-count by 32.7 %**, the opposite sign to the wave-1 levers' 66.8 % double-count and
consistent with h6-F1. Entry timing, exit geometry and affordability act on different
objects, so they compose rather than overlap.

**The gate is a cliff, not a slope** (k=3, STOPONLY, h1 cost):

| gate bps | n | share | gross | cost | net | edge:toll | months + |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.40 | 757 | 1.7 % | +0.07455 | 0.03448 | +0.04007 | 2.162 | 1/3 |
| 0.45 | 1,334 | 3.0 % | +0.11524 | 0.04418 | +0.07107 | 2.609 | 3/3 |
| 0.50 | 3,191 | 7.3 % | +0.10575 | 0.04507 | +0.06068 | 2.346 | 2/3 |
| 0.55 | 3,570 | 8.2 % | +0.12700 | 0.04552 | +0.08148 | 2.790 | 3/3 |
| **0.60** | **3,728** | **8.5 %** | **+0.12317** | **0.04667** | **+0.07650** | **2.639** | **3/3** |
| 0.65 | 4,408 | 10.1 % | +0.11564 | 0.05052 | +0.06512 | 2.289 | 3/3 |
| **0.70** | 6,948 | 15.9 % | +0.08326 | 0.08046 | **+0.00281** | **1.035** | 1/3 |
| 0.80 | 9,276 | 21.2 % | +0.08181 | 0.09116 | −0.00935 | 0.897 | 1/3 |
| 1.00 | 13,945 | 31.9 % | +0.06312 | 0.11594 | −0.05281 | 0.544 | 0/3 |
| none | 43,755 | 100 % | +0.02917 | 0.24521 | −0.21604 | 0.119 | 0/3 |

The marginal band **[0.60, 0.70] bps** has edge:toll **0.310**. Everything above the cliff
destroys the book. The plateau 0.45–0.65 is contiguous, which is why 0.60 is a choice
inside a region and not a spike. (The grid's own argmax was 0.55 — its extra value comes
from a 379-trade band at ratio 6.205, which is a spike, and was deliberately not taken.)

**The delay is a plateau too** — an equal-weight blend across k ∈ {1,2,3} books
**+0.06970** (ratio 2.493) against the single best k's +0.07650, so the entry-timing choice
is worth ~9 % of itself, not the whole result:

| k | 0 | 1 | 2 | **3** | 5 |
|---|---:|---:|---:|---:|---:|
| net R | −0.00991 | +0.07477 | +0.05784 | **+0.07650** | +0.02832 |
| edge:toll | 0.788 | 2.602 | 2.239 | **2.639** | 1.607 |

---

## 6. CONTROLS — the part that decides whether any of this is a signal

### 6.1 Intraday placebo anchors (9 shifts, identical rows, cost, side, risk unit)

Real **+0.07650**. Placebo mean **−0.02721**. Real beats **9 of 9**.

| shift (min) | −2880 | −1440 | −120 | −60 | +60 | +120 | +180 | +1440 | +2880 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| net R | −0.0416 | −0.0315 | −0.1348 | −0.0223 | +0.0250 | −0.0212 | +0.0250 | **+0.0759** | −0.1195 |

The +1 day anchor books **+0.0759** against the real book's **+0.0765** — which is why four
draws could not settle it.

### 6.2 The 20-draw whole-day null — THE deciding control

Shift the decision instant by ±1…±10 calendar days. This preserves the instrument, the
**broker hour**, the side, the risk unit, the cost and the gate **exactly**, and destroys
only the intraday timing the signal supplies.

| | |
|---|---:|
| real net R | **+0.076498** |
| null mean | −0.013470 |
| null sd | 0.059830 |
| null min / max | −0.11946 / **+0.09174** |
| null p90 / p95 | +0.07656 / +0.08279 |
| **z (net)** | **+1.5038** |
| **empirical p (net)** | **0.1429** |
| empirical p (gross) | 0.1905 |

**Three of twenty null draws (−4, +1, +4 days) match or exceed the real book.** The
signal's timing is worth about **+0.090 R/trade** over the null mean — a real quantity —
but at **1.5 σ** it is **not distinguishable** from a same-structure, different-day book
at any conventional threshold. This is the honest reading and it should be quoted with
the headline, not after it.

### 6.3 Side randomisation

Randomising each trade's direction on the true instants collapses gross from **+0.12317**
to **+0.03699** (net −0.00968). So the *direction* the signal calls carries real
information — and note that the day-null preserves direction and still only reaches
+0.033 gross on average. The direction is worth something; the intraday *timing* is what
cannot be separated from noise.

---

## 7. Q4 — THE MULTIPLICITY BILL, STATED HONESTLY

**b1's own contribution: 3,207 cells.**

| | cells |
|---|---:|
| declared grid: k(11) × exit(5) × gate(12) × window(4) | **2,640** (2,420 non-empty) |
| gate curve (fine) | 20 |
| marginal cost bands | 11 |
| k × exit at four gates | 264 |
| composition cells (7 axes) | 168 |
| placebo anchors (9 intraday + 20 whole-day) | 29 |
| stress variants | 11 |
| BOOK-B / cost-R m-sweeps | 16 |
| limb decomposition | 5 |
| OOS gate and k curves | 43 |
| **b1 total** | **3,207** |

**The wave's total is above 150,000 cells**: h1 3,472 · h2 4,213 · h5 4,130 + 39,835
exploratory · h6 103,200 · h3's cell and composite grids · plus the 29-lane discovery
swarm that preceded them.

Of the 471 cells in b1's own grid that clear edge:toll > 1, **14** pass the pre-declared
survival rule (ratio > 1, net > 0, 3/3 months positive, n ≥ 1,000, day-clustered t ≥ 1.5).
b1-BOOK-V1 is one of them.

**None of this is multiplicity-corrected significant, and it should not be presented as
such.** h5 already ran a Westfall–Young maxT over its own 4,130 cells and returned **zero
survivors at p ≤ 0.05, 0.10 or 0.20**; the best cell in that grid was *less* extreme than
the maximum pure noise routinely produces. b1's specification is drawn from the same pool.
The book's day-clustered t of +1.612 and its whole-day-null p of 0.143 are the correct
strength to quote, and both are well short of anything a family-wise correction would pass.

---

## 8. THE ALTERNATIVE BOOKS — the full menu, all five months

All at k=3, stop −1R, no target, no trail, close at +120 min, hour-true cost.

| book | Jan | Feb | Mar | **Apr** | **May** | hunt | **OOS** | 5m net | 5m ratio | P(≤0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** cost gate ≤ 0.60 bps | +0.1091 | +0.0500 | +0.0447 | +0.0058 | −0.1020 | **+0.0685** | **−0.0447** | +0.0268 | 1.571 | 0.221 |
| **C** 3 gate-reachable instruments, all hours | +0.0124 | +0.0328 | +0.0256 | +0.0386 | −0.0668 | +0.0233 | −0.0098 | +0.0108 | 1.169 | 0.353 |
| **D** gate **and** broker hours 08–20 | +0.1296 | +0.0671 | +0.0212 | +0.0656 | −0.1273 | +0.0728 | −0.0259 | **+0.0369** | **1.923** | 0.171 |
| **E** 3 instruments **and** broker hours 08–20 | +0.0553 | +0.0697 | +0.0127 | **+0.1313** | −0.1153 | +0.0456 | **+0.0160** | +0.0349 | 1.724 | **0.159** |
| **F** gate **and** exchange cash session | +0.0586 | +0.0210 | +0.0038 | +0.0327 | −0.0742 | +0.0282 | −0.0187 | +0.0110 | 1.357 | 0.387 |

**Book E is the only one net-positive in both windows** (+0.0456 hunt, +0.0160 OOS,
+0.0349 pooled at edge:toll 1.724, P(net ≤ 0) = 0.159, 44/101 days). Its hour limb —
broker hours 08–20 — was **published by h1 before b1 ran** and was one of the four windows
in b1's declared grid, so it is not a post-hoc invention. **But b1 read April and May
before choosing to put E forward**, so E's five-month numbers are *indicative*, not
out-of-sample. E is the right thing to hand to the next stage; it is not a validated book.

Every one of the five is **negative** under a cost × 2 stress on the five-month window
(A −0.02015, C −0.05304, **D −0.00307**, E −0.01327, F −0.01982). **May 2026 is negative
for all five** — and the ungated cohort was *fine* in May (gross +0.0184), so May is a
failure specific to the index complex, not a market-wide event.

### Books measured and rejected

- **Instruments ranked by mean cost in bps** (`b1_10`): January's order is US30_cash,
  NAS100, **EURUSD**, GER40 — and EURUSD tests at **−0.13058** (ratio 0.312) because its
  toll *in R* is 4.4× the index complex. **A constant-R book must rank in R, not in bps.**
  Every m from 1 to 8 tests negative on Feb–May.
- **Instruments ranked by mean cost in R** (`b1_11` Part 2): order NAS100, US30_cash,
  **XAUUSD**, GER40 — every m from 1 to 10 also tests negative on Feb–May
  (best m=2 at −0.00669).
- **h2's exchange cash-session rule**: 5m +0.0102 at ratio 1.330, OOS −0.0187.
- **Outside the cash session**: 5m +0.0112 at ratio 1.134 — i.e. the cash session is *not*
  the discriminating axis on this contract.

### One forward lead, honestly labelled

Splitting the gated book by **risk-distance quintile** (cuts fixed on January, ex-ante),
two of five quintiles are positive in **both** windows: Q1 (rdp ≤ 4.77 bps) hunt +0.2841 /
OOS +0.0293 / 5m +0.1891 at ratio 2.216, and Q4 (15.1–26.3 bps) hunt +0.1344 / OOS +0.0402
/ 5m +0.1021 at ratio 5.369 — while Q2 and Q5 are negative in both. **The pattern is not
monotone, so it reads as tail noise rather than mechanism**, and Q1 is precisely where the
convexity tail lives. It is recorded because a later stage should test it, not because it
is believed.

---

## 9. THE IMPLEMENTABLE CONTRACT

```python
# ---- decision time t0, candidate c on symbol s, side d, entry E, stop S -------------
rd        = abs(E - S)                       # declared risk distance, price units
rdp       = rd / E
bh        = broker_hour(t0)                  # NEW_YORK_PLUS_7; src/utils/broker_clock.py

toll_bps  = ( spread_bps_median[s][bh]                       # tick archive, hour-aware
            + commission_bps[s]                              # broker schedule
            + entry_slip_bps[s]                              # measured live deals
            + (swap_bps[s][d] if crosses_rollover(t0, t0+120min) else 0.0) )

if toll_bps > 0.60:  return REJECT           # ~91.5% of candidates; leaves 3 instruments

# ---- entry -------------------------------------------------------------------------
sleep_until(t0 + 3 minutes)
fill = market_order(s, d, risk = fixed_fraction_of_equity / rd)
#   no resting order is ever placed, so there is nothing to cancel and the
#   0.45 fill-probability floor never binds (it is identically 0.92/0.95 here)

# ---- exit --------------------------------------------------------------------------
stop_price = fill - d * rd                   # -1R from the FILL, not from E
set_broker_stop(stop_price)                  # server-side, set once, never moved
#   no take-profit, no trail, no break-even move, no scale-out
at t0 + 120 minutes: close_at_market()       # if the stop has not fired
```

**Operating facts a live implementation must respect**

1. **Concurrency**: up to **31** simultaneous open positions, mean **3.40**. Size for the
   concurrency, not the per-trade risk.
2. **50.75 %** of trades stop out at −1R. The median trade is a full loss and the **median
   day is +0.011 R**. Long flat stretches are normal.
3. **49.25 %** of trades are closed by the clock, not by a level, so the 120-minute close
   is a load-bearing part of the contract, not a backstop.
4. The book is **long convexity**: capping gains at +5R makes it negative. Any live change
   that truncates winners (a target, a trail, a tighter time stop, a partial) destroys it —
   which the ablation shows directly (2R target → +0.0036; TRAIL025 → −0.0011).
5. **Nothing here should be armed.** The specification is out-of-sample negative, its
   whole-day-null p is 0.143, and it is drawn from a >150,000-cell search with a
   family-wise correction already known to admit nothing.

---

## 10. FINDINGS INDEX

| id | finding |
|---|---|
| **b1-F1** | A net-positive book exists on Jan–Mar: +0.076498 R/trade (+0.5673 bps) at the strictest broker-true toll, edge:toll **2.6391**, on 3,728 trades / 63 days, 3/3 months, bootstrap P(≤0)=0.048, +285.19 R against a −79.77 R drawdown. |
| **b1-F2** | It survives **doubling** the toll (edge:toll 1.320) and the h4 all-in live-grounded basis (1.673) and exit slippage plus ×2 (1.123). Cost modelling is not what holds it up. |
| **b1-F3** | It is **out-of-sample negative**: −0.044700 R/trade on Apr+May, edge:toll 0.064, 11/38 days, P(≤0)=0.827. Gross collapsed 97 % while cost moved 2.8 %. |
| **b1-F4** | The failure is the **hour limb**, and it inverts: in-window cheap hours beat expensive by +0.1361; out of window they lose by 0.0987. The instrument limb travels (same 3 instruments in all 5 months; cost Spearman 0.9922 vs gross 0.1478). |
| **b1-F5** | The **contract did not break** — the ungated 24-instrument cohort at the identical contract is flat across all 5 months (slope −0.0048). Only the selected cells decay (slope −0.0499). |
| **b1-F6** | **No limb pays alone and no pair pays**: gate +0.0028, delay −0.2093, exit −0.2233, gate+delay −0.0011, gate+exit +0.0283, delay+exit −0.2160, all three **+0.0765**. Add-one deltas under-count the joint by 32.7 % — the limbs are complements. |
| **b1-F7** | The gate is a **cliff at 0.70 bps**, not a slope: the marginal band [0.60,0.70] has edge:toll 0.310 and takes the book from +0.0765 to +0.0028. The plateau 0.45–0.65 is contiguous. |
| **b1-F8** | **The whole book is 106 trades.** Removing the best 18 of 3,728 (0.5 %) makes it negative; capping gains at +5R makes it negative. It is a convexity book, which is why a 2-month read could reverse it. |
| **b1-F9** | Against a **20-draw whole-day null** that preserves instrument, broker hour, side, risk unit and cost, the book sits at **z=+1.50, p=0.143**. Three of twenty null draws match it. It beats 9/9 intraday anchors, but is not separable from same-structure noise. |
| **b1-F10** | **Book E** (3 gate-reachable instruments × broker hours 08–20) is the only variant net-positive in **both** windows: +0.0456 hunt, +0.0160 OOS, +0.0349 pooled at edge:toll 1.724, P(≤0)=0.159. Both limbs were published before b1, but b1 chose it after reading the OOS — indicative, not validated. |
| **b1-F11** | **A constant-R book cannot rank instruments in bps.** The bps ranking admits EURUSD third and tests at −0.1306; the R ranking admits XAUUSD third and also tests negative. Only the row-level bps gate — which happens to resolve to three instruments — produces a positive in-window book. |
| **b1-F12** | The multiplicity bill is **3,207 cells for b1** and **>150,000 for the wave**; h5's Westfall–Young maxT over 4,130 of them already returned zero survivors at p ≤ 0.20. Nothing in this receipt is corrected-significant. |

---

## 11. FILES

| file | what |
|---|---|
| `b1_RESULT.md` / `b1_RESULT.json` | this receipt (343 KB of numbers) |
| `b1_lib.py`, `b1_np.py` | the loader and the one scorer every step uses |
| `b1_01_repro.py` → `B1_REPRO_V1.json` | reproduction of h1/h2/h3/h5/h6 |
| `b1_02_costjoin.py` → `b1_COST_JOIN_V1.jsonl.gz`, `B1_COSTJOIN_V1.json` | h1's four-term cost joined, 43,755/43,755 |
| `b1_03_grid.py` → `b1_GRID_V1.jsonl.gz`, `B1_GRID_V1.json` | the 2,640-cell declared grid |
| `b1_04_surface.py` → `B1_SURFACE_V1.json` | gate curve, marginal bands, k×exit, composition |
| `b1_05_book.py` → `B1_BOOK_V1.json` | the book, ablation, bootstrap, truncation, robustness |
| `b1_06_placebo.py` → `B1_PLACEBO_V1.json` | 9 shifted anchors + side flip + the bar-level rebuild check |
| `b1_07_daynull.py` → `B1_DAYNULL_V1.json` | the 20-draw whole-day null |
| `b1_08_oos.py` → `B1_OOS_V1.json` | April+May, read once |
| `b1_09_decay.py` → `B1_DECAY_V1.json` | what collapsed: 21 population×contract month chains + rank persistence |
| `b1_10_bookB.py` → `B1_BOOKB_V1.json` | the cost-bps-ranked book (rejected) |
| `b1_11_decompose.py` → `B1_DECOMPOSE_V1.json` | limb decomposition, cost-R ranking, stress |
| `b1_12_final.py` → `B1_FINAL_V1.json` | consolidated headline, gate resolution, k plateau, multiplicity |
| `b1_13_daily.py` → `B1_DAILY_V1.json` | R/day, concurrency, hour-rule comparison |
| `b1_14_composite.py` → `B1_COMPOSITE_V1.json` | books A/C/D/E/F over all five months |
