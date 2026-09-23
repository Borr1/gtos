# Does the edge ever pay for its own costs? — the hunt, in plain language

**For Borhen. 2026-08-06. Six investigation lanes (h1–h6) plus two cross-lane checks written for this
report. 69,480 trades, five months (January–May 2026), 24 instruments, every number measured on this
machine.**

---

## THE ANSWER, IN ONE LINE

**Yes — in one place. GER40 (the DAX), entered at market three minutes after the signal, held on a
plain stop with no trailing, closed at the two-hour mark, and only in the hours when the DAX round
trip costs 0.60 basis points or less: 1,630 trades over five months, +0.0475 R per trade net of every
broker charge — 2.4× what the broker takes, and it still earns 1.75× its toll in the two months
nobody had looked at.**

That is the only thing left standing out of more than 200,000 candidate cells. It is a lead, not a
result: the probability its five-month edge is really zero is 14%, and 40% on the out-of-sample half
alone. Everything else the hunt turned up either dies when the exit rule is priced honestly, or dies
in the two unseen months, or both.

---

## Words, defined once

| Term | Meaning here |
|---|---|
| **R** | One risk unit. If your stop sits 40 points away, 1 R = 40 points. "+0.05 R/trade" = each trade makes 5% of what it risks. |
| **bps** | Basis point = 0.01% of the instrument's price. Used when R would mislead — see the box in §6. |
| **Gross** | Before broker costs. The raw price move. |
| **Net** | After spread + commission + slippage + swap. |
| **The toll** | Total broker cost per round trip. |
| **edge ÷ toll** | Gross divided by cost. **Above 1.0 = the trade pays for itself.** Below 1.0 = you are feeding the broker. |
| **A cell** | A slice of the book: one instrument, one hour, one signal family, or a combination. |
| **The hunt window** | January + February + March 2026 — the three months every lane searched. |
| **Out of sample (OOS)** | April + May 2026. Built from real bars, never looked at while searching. This is the honest test. |
| **The book** | 43,755 candidate trades over the hunt window (69,480 over five months) that the live engine could actually have placed — market orders only, no limits. |

**None of this touches your live accounts.** This is the broad V4 research selector: a 2-hour-horizon
strategy family that has never traded live. Your armed sleeves (`crypto`, `energy_agri`,
`sub_xvol_pullback`, `mx_btcusd` on FTMO; four core sleeves on redacted_account) hold for up to 320 hours —
160× longer. **One finding does reach the live books and it is flagged in §8.**

---

## 1. THE HEADLINE NUMBERS, SIDE BY SIDE

| | value | source |
|---|---:|---|
| Gross edge, whole book, published | **+0.038342 R/trade** (t +12.35) | swarm, reproduced digit-for-digit by 3 lanes |
| Gross edge, whole book, **with no trailing stop** (needs no assumption) | **+0.029170 R/trade** | b2 Part A |
| Broker toll, published | 0.181834 R / **2.457 bps** | swarm |
| Broker toll, hour-true (spread charged at the hour you actually traded) | 0.220328 R / **2.669 bps** | h1, h2, h3, h5, h6 — five lanes, independently, agree |
| Broker toll, all-in (+ live commission truth + exit fill quality) | **3.875 bps** | h4, from 289 real broker positions |
| Edge ÷ toll, whole book | **0.13 – 0.06** depending on which toll | — |
| Cells searched across all six lanes | **> 200,000** (lane h6 alone: 197,891) | — |
| Cells that cleared edge ÷ toll > 1 on the hunt window | **several hundred** (h1: 651 · h2: 191 · h5: 193) | — |
| Cells that survive an honest exit rule **and** April+May | **one instrument** | this report |

**The gap is roughly 8× at the whole-book level, not 10×.** And it does not close by trading better —
it closes only by refusing to trade most of the book.

---

## 2. WHAT WAS FOUND — lead with this

The hunt worked. Cells where the edge beats the broker exist and there are hundreds of them. Here is
the best of each lane, on the hunt window, at hour-true broker cost.

| # | Cell (the rule) | Lane | n | Gross R | Cost R | **Net R** | **edge÷toll** | Months + |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | GER40 only, London session | h1/h2/h5 | 504 | +0.0909 | 0.0330 | **+0.0579** | **2.76** | 3/3 |
| 2 | GER40 at UTC hour 14 | h5 | 120 | +0.2046 | 0.0330 | **+0.1716** | **6.20** | 3/3 |
| 3 | GER40 at UTC hour 08 (Xetra open) | h5 | 213 | +0.1279 | 0.0287 | **+0.0992** | **4.45** | 3/3 |
| 4 | Any trade costing ≤ 0.50 bps, broker hours 08–20 | h1 | 2,759 | +0.0568 | 0.0398 | **+0.0170** | **1.43** | 3/3 |
| 5 | NAS100 only, cost ≤ 0.50 bps | h1 | 554 | +0.0732 | 0.0315 | **+0.0417** | **2.32** | 3/3 |
| 6 | GER40 + NAS100, inside their own cash session | h2 | 1,557 | +0.0654 | 0.0313 | **+0.0341** | **2.09** | 3/3 |
| 7 | `regime_transition_break` signal family | h3 | 828 | +0.0492 | 0.0405 | **+0.0087** | **1.22** | 3/3 |
| 8 | No-retrace ≥10 min + 6 cheapest instruments | h3 | 814 | — | — | **+0.0142** | **2.11** | 3/3 |
| 9 | US30_cash, London session | h1 | 406 | +0.0925 | 0.0582 | **+0.0343** | **1.59** | 3/3 |
| 10 | **No trail, 3-min wait, cost ≤ 0.60 bps** (3 index names) | **h6** | **3,807** | **+0.1150** | **0.0465** | **+0.0685** | **2.48** | **3/3** |

Every one of these is real arithmetic on the whole population. Nothing was sampled.

**And two things the hunt established that stand regardless of what follows:**

**(a) The cost dispersion is on the INSTRUMENT, not the family.** The swarm's closing observation was
"real cost per family disperses 12.1×". Measured in money that is **3.08×** across families — and only
**1.23×** among the eight families with real depth. The 12.1× was 77% an artifact of dividing by stop
width. The real dispersion is across instruments: **24.3×**, from US30_cash at 0.52 bps to ETHUSD at
12.55 bps. Statistically, the instrument explains **86%** of what a trade costs; instrument × hour
explains **98.5%**; the signal family explains **0.5%**.

**(b) Cost is a function of the HOUR and nothing in this estate had ever charged it that way.** The
same tick archive that gives the per-symbol spread also carries a per-broker-hour spread, on all 24
instruments, and it had never been used. Within one instrument the spread ranges up to **34.7×**
(EURUSD) between its cheapest and dearest hour. Charging the hour you actually traded raises the whole
book's toll by 21% — and it is what finds the cheap cells.

---

## 3. THE TWO CHECKS NOBODY HAD RUN — and they change the answer

I ran two things across all six lanes before writing this.

### Check 1 — the exit rule the whole hunt was measured on cannot be measured at this resolution

Every headline above (except #10) uses the same exit: a stop that **trails 0.25 R behind the best
price seen**. The trade paths are one-minute bars: open, high, low, close. A one-minute bar does not
tell you whether the high came before or after the low. The scoring code arms the trailing stop off
the bar's high and then only checks whether it was hit **starting from the next bar** — so any
pullback through the trail *inside the same minute* is never charged.

**Your estate already ratified the conservative fix for exactly this** (B613; AD measured 95.8% of
these events are intrabar). Nobody had applied it to this hunt. Applying it:

| Cell | Lane | n | Gross as published | Gross under the honest rule | **Net published** | **Net honest** |
|---|---|---:|---:|---:|---:|---:|
| **Whole book** | — | 43,755 | +0.0383 | **−0.0457** | −0.1820 | −0.2660 |
| Cost ≤0.50 bps, hours 08–20 | h1 | 2,759 | +0.0568 | −0.0303 | +0.0170 | **−0.0701** |
| NAS100, cost ≤0.50 | h1 | 554 | +0.0732 | −0.0136 | +0.0417 | **−0.0451** |
| GER40 \| London | h1/h2/h5 | 504 | +0.0909 | +0.0119 | +0.0579 | **−0.0211** |
| GER40+NAS100 cash session | h2 | 1,557 | +0.0654 | −0.0262 | +0.0341 | **−0.0575** |
| GER40 \| UTC hour 14 | h5 | 120 | +0.2046 | +0.0291 | +0.1716 | **−0.0039** |
| `regime_transition_break` | h3 | 828 | +0.0492 | +0.0335 | +0.0087 | **−0.0069** |
| US30_cash \| London | h1 | 406 | +0.0925 | −0.0001 | +0.0343 | **−0.0583** |
| GER40 \| broker hours 16–19 | h1 | 390 | +0.0590 | −0.0591 | +0.0225 | **−0.0957** |
| **GER40 \| UTC hour 08** | **h5** | **213** | **+0.1279** | **+0.0592** | **+0.0992** | **+0.0305** ✅ |
| **No trail, 3-min wait, cost ≤0.60** | **h6** | **3,807** | **+0.1150** | **+0.1150** | **+0.0685** | **+0.0685** ✅ |

*Full table: `B2_VERIFY_V1.json → part_a_honest_trail_bound`. Script: `b2_verify.py`.*

**The trailing stop is worth +0.084 R/trade of pure bar-resolution — 2.2× the entire published
headline.** Of fourteen headline cells, **two survive**: h5's GER40 at hour 08 (thin, 213 trades) and
h6's cell, which carries no trailing stop at all and is therefore immune by construction.

**Read this correctly, because the pessimistic reading is also wrong.** The honest rule is a *bound*,
not a measurement. The truth sits between the two columns; only tick data settles it. What the check
proves is that **any number resting on a trailing stop, measured on one-minute bars, cannot be
distinguished from its own measurement artifact.** That is why the survivor matters: it uses a plain
stop, so both columns are identical.

**The signal itself survives this.** With no trailing stop at all — nothing to argue about — the whole
book is still gross-positive at **+0.029170 R/trade**. The edge is real. It is the specific exit rule
the hunt optimised into that is unmeasurable at this resolution.

### Check 2 — April and May exist, and nobody had read the best cell on them

One lane claimed no April/May bars exist on this machine. **They do** —
`bridge_ftmo_m1_202604` and `202605`, and lane h5 already built 25,725 tradeable candidates from them.
What nobody did was read h6's no-trail cell — the one thing that survived Check 1 — on those two
months. It is directly readable, because that cell is exactly the shipped `K3_STOPONLY` column.

| Cost cap | Hunt (Jan–Mar) n | Hunt net R | Hunt ratio | **OOS (Apr+May) n** | **OOS net R** | **OOS ratio** | 5-month net |
|---:|---:|---:|---:|---:|---:|---:|---:|
| no cap | 43,755 | −0.1912 | 0.13 | 25,725 | −0.2373 | 0.04 | −0.2083 |
| ≤ 1.0 bps | 16,037 | −0.0833 | 0.36 | 9,460 | −0.1523 | −0.01 | −0.1089 |
| ≤ 0.8 bps | 9,873 | −0.0233 | 0.76 | 5,861 | −0.1074 | −0.04 | −0.0546 |
| ≤ 0.7 bps | 7,110 | −0.0038 | 0.95 | 4,146 | −0.0631 | 0.24 | −0.0256 |
| **≤ 0.60 bps (h6's cell)** | **3,807** | **+0.0685** | **2.48** | **2,222** | **−0.0447** | **0.06** | **+0.0268** |
| ≤ 0.50 bps | 3,270 | +0.0518 | 2.15 | 1,871 | −0.0189 | 0.59 | +0.0260 |
| ≤ 0.45 bps | 1,356 | +0.0642 | 2.46 | 766 | +0.0017 | 1.03 | +0.0416 |

**The cell as a whole does not travel.** Broken out by instrument:

| Instrument | Hunt n | Hunt net R | Hunt ratio | **OOS n** | **OOS net R** | **OOS ratio** | 5-month net R | 5-month ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **GER40** | 1,069 | +0.1194 | 4.22 | 589 | **+0.0027** | **1.09** | **+0.0780** | **3.24** |
| US30_cash | 1,942 | +0.0737 | 2.31 | 1,127 | −0.0500 | 0.17 | +0.0283 | 1.49 |
| NAS100 | 796 | −0.0125 | 0.65 | 506 | −0.0881 | −1.17 | −0.0419 | −0.12 |

**GER40 is the only one that stays above 1.0 in the two unseen months.** Every entry delay from 0 to
30 minutes is negative out of sample on the pooled cell (k=0 −0.177 · k=1 −0.046 · k=3 −0.045 ·
k=5 −0.070 · k=20 −0.080 · k=30 −0.071), and so is every alternative exit contract — **except the
0.25 R trailing stop**, at +0.008, which is precisely the one contract Check 1 showed cannot be
measured on one-minute bars. The instrument, not the rule, is what carries this.

---

## 4. ONE MORE DEFECT I FOUND WHILE MEASURING IT — and it costs 40% of the headline

Lane h1 flagged, and did not price, that **ten of the twenty-four instruments have ZERO ticks at
broker hour 00** in the 300-million-tick archive — every index CFD, both metals, both oils. They are in
their daily trading break. The market is *shut*. The candidate generator emits trades on them anyway,
and the cost model quietly falls back to the all-hours median, because there is no quote at that hour
to charge.

There are only **261 such rows in 69,480 (0.38%)**. They are worth:

| | n | Gross R/trade | Net R/trade | Total R |
|---|---:|---:|---:|---:|
| GER40's closed-market rows | 28 | +1.996 | **+1.855** | **+51.9 R** |
| All closed-market rows inside the 0.60 gate | 88 | +0.640 | +0.520 | +45.8 R |
| GER40 cell's entire 5-month P&L | 1,658 | — | +0.0780 | +129.3 R |

**28 trades placed while the Frankfurt exchange was closed carry 40% of the five-month result.** They
are not tradeable and their prices are not priceable. Remove them, and here is the honest cell:

| GER40 cell | n | Net R/trade | edge÷toll | Days + | Months + |
|---|---:|---:|---:|---:|---:|
| as first measured (includes closed-market rows) | 1,658 | +0.0780 | 3.24 | 48/101 | 4/5 |
| **open market only — the number to use** | **1,630** | **+0.0475** | **2.44** | **48/101** | **4/5** |
| — its hunt-window half (Jan–Mar) | 1,053 | +0.0618 | 2.73 | 31/63 | 3/3 |
| — **its out-of-sample half (Apr+May)** | **577** | **+0.0213** | **1.75** | **17/38** | **1/2** |

**Cleaning the closed-market rows out makes the out-of-sample half better, not worse** — GER40's
forward read goes from edge÷toll 1.09 to **1.75**, because those unpriceable trades were concentrated
in the hunt window. That is the right direction for a cleanup to move a result.

---

## 5. THE SURVIVOR, IN FULL — everything about it, good and bad

> **The rule.** Trade **GER40 only**. When the signal fires, wait **3 minutes**, then send a **market
> order**. Stop at −1 R. **No target, no trailing stop.** Close at the **2-hour mark** if neither has
> been hit. Only take the trade if GER40's round-trip cost at that hour is **≤ 0.60 bps**.

| | value |
|---|---|
| Sample | **1,630 trades, 101 trading days, 5 months** (Jan–May 2026) |
| Gross / cost / **net** | +0.080511 / 0.033063 / **+0.047448 R per trade** |
| **edge ÷ toll** | **2.44** (hunt window 2.73 · out of sample **1.75**) |
| Total | **+77.3 R** over five months (~16 trades/day) |
| Day-clustered t | +0.78 (out of sample +0.19) |
| Bootstrap, 5 months | 95% range **[−0.0388, +0.1354]**, **probability it is really ≤ 0: 14.0%** |
| Bootstrap, out-of-sample only | probability it is really ≤ 0: **40.2%** |
| Days positive | 48 of 101 |
| Survives the honest exit rule? | **Yes — by construction. There is no trailing stop to argue about.** |
| Survives doubling the broker's whole toll? | **Yes** — +0.0144 R/trade |
| Both directions? | Yes — LONG +0.107, SHORT +0.053 (before the closed-market removal) |

**Month by month:**

| Month | n | Net R/trade | edge÷toll | Days + | Seen during the hunt? |
|---|---:|---:|---:|---:|---|
| 2026-01 | 344 | +0.0236 | — | 9/21 | yes |
| 2026-02 | 339 | +0.0168 | — | 9/20 | yes |
| 2026-03 | 370 | +0.1385 | — | 13/22 | yes |
| **2026-04** | **315** | **+0.0642** | — | 10/20 | **no** |
| **2026-05** | **262** | **−0.0303** | — | 7/18 | **no** |

**The three things wrong with it, stated plainly:**

1. **It is carried by a handful of days.** The single best day is **27.8%** of the whole five-month
   total; the best three days are **73.5%**. Drop those three days and it is +0.0130 R/trade — still
   positive, but a fifth of the headline. (Some concentration is expected: this is a 36%-win-rate,
   fat-right-tail profile. 73.5% in three days out of 101 is more than expected.)
2. **It is not statistically established.** A 14% chance the five-month result is really zero, and a
   40% chance the out-of-sample half is. Against the estate's own admission bar (α = 0.10, and a
   multiplicity bill for having looked at 100,000+ cells) it does not come close. Lane h5 ran the
   formal multiplicity test on 4,130 cells: **zero cells survive at any threshold.** The best cell in
   the entire grid is less extreme than what pure noise routinely produces at that many looks.
3. **Its own cost gate does not travel, and may be doing negative work.** GER40 with **no cost gate at
   all** books +0.0092 R/trade over five months — *worse* in-sample, but **+0.0765 out of sample**,
   better than the gated version. The 0.60 bps cap was chosen after seeing three months, and the two
   fresh months disagree with it. What is durable here is the *instrument*, not the threshold.

---

## 6. THE COST SURFACE — see it yourself

### 6.1 What the toll is actually made of

| Term | bps | Share | Where it dominates |
|---|---:|---:|---|
| Spread (quoted, hour-true) | 2.0225 | **68.0%** | every zero-commission CFD: oil 98%, silver 98%, UK100 94%, GER40 92% |
| Commission | 0.6942 | 23.3% | BTCUSD **91%**, EURUSD 56%, ETHUSD 52%, USDJPY 50% |
| Entry slippage | 0.1373 | 4.6% | nowhere — it is a rounding term |
| Swap (overnight carry) | 0.1203 | 4.0% | only at broker hours 22–23, where it is the biggest single term |
| **Total (h1 basis)** | **2.9744** | | |
| + live commission truth + exit fill quality (h4) | **3.8746** | | |

**How much of that can execution remove? Not enough.** A round trip crosses the spread once. If you
could rest every order passively and never slip, the floor is **commission only: 0.5686 bps** — a
**4.3× cut**. You need **10.6×**. And at that unreachable floor the edge still earns only **41%** of
its toll. *Buying the entry passively was measured and it loses money under both quote conventions:
76% of passive fills arrive in the first 60 seconds and that cohort's edge is −2.64 bps.*

### 6.2 The 24 instruments, by what the broker actually charges

Hour-true, broker-true, at the swarm's contract. This is the table where the dispersion lives.

| Instrument | n | Cost bps | Cost R | Gross R | Net R | edge÷toll |
|---|---:|---:|---:|---:|---:|---:|
| US30_cash | 1,942 | **0.517** | 0.0654 | +0.0325 | −0.0329 | 0.50 |
| NAS100 | 1,904 | 0.701 | 0.0605 | +0.0237 | −0.0368 | 0.39 |
| EURUSD | 1,863 | 0.762 | 0.1962 | +0.0586 | −0.1376 | 0.30 |
| **GER40** | 1,858 | **0.860** | 0.0871 | +0.0647 | −0.0225 | **0.74** |
| GBPUSD | 2,054 | 1.010 | 0.2420 | +0.0344 | −0.2076 | 0.14 |
| SPX500 | 1,850 | 1.025 | 0.1254 | +0.0249 | −0.1006 | 0.20 |
| USDJPY | 2,442 | 1.037 | 0.2632 | +0.0643 | −0.1989 | 0.24 |
| USDCAD | 2,010 | 1.182 | 0.3949 | +0.0205 | −0.3744 | 0.05 |
| EURJPY | 1,564 | 1.376 | 0.2670 | +0.0278 | −0.2392 | 0.10 |
| XAUUSD | 1,996 | 1.412 | 0.0787 | +0.0466 | −0.0321 | 0.59 |
| AUDUSD | 1,627 | 1.505 | 0.2024 | +0.0294 | −0.1730 | 0.15 |
| EURGBP | 1,865 | 1.630 | 0.4888 | +0.0377 | −0.4512 | 0.08 |
| USDCHF | 1,854 | 1.638 | 0.3095 | +0.0443 | −0.2652 | 0.14 |
| JP225 | 1,627 | 1.664 | 0.0895 | +0.0348 | −0.0548 | 0.39 |
| GBPJPY | 1,978 | 1.726 | 0.3419 | +0.0457 | −0.2962 | 0.13 |
| UK100 | 2,002 | 1.965 | 0.2845 | +0.0615 | −0.2230 | 0.22 |
| AUDJPY | 1,604 | 2.208 | 0.2907 | +0.0361 | −0.2546 | 0.12 |
| CHFJPY | 1,547 | 2.395 | 0.3579 | +0.0428 | −0.3150 | 0.12 |
| NZDUSD | 1,943 | 2.582 | 0.3883 | +0.0371 | −0.3512 | 0.10 |
| BTCUSD | 1,415 | 7.189 | 0.1917 | +0.0422 | −0.1495 | 0.22 |
| UKOIL_cash | 1,699 | 9.303 | 0.3577 | +0.0152 | −0.3425 | 0.04 |
| XAGUSD | 1,968 | 9.712 | 0.2072 | +0.0360 | −0.1713 | 0.17 |
| USOIL_cash | 1,777 | 10.054 | 0.3472 | +0.0353 | −0.3120 | 0.10 |
| ETHUSD | 1,366 | **12.549** | 0.2451 | +0.0023 | −0.2428 | 0.01 |

**The cheapest instrument costs 24.3× less than the dearest. Every affordable cell in the entire hunt
lives in the top four rows of this table.**

### 6.3 The two structural costs nobody had ever charged

| Object | Share of trades | Share of the whole book's toll | What it is |
|---|---:|---:|---|
| **Broker hour 00** | 2.12% | **13.19%** | The FX rollover. Spread is **7.0×** the flat basis there — EURUSD 34.7×, GBPUSD 33.9×. Ten instruments are *closed* at this hour (see §4). |
| **Swap at broker hours 22–23** | 3.81% | 4.95% | Overnight carry on a 2-hour trade, charged per rollover crossing. Every prior pass set it to zero. |

Dropping hour 00 alone cuts the whole book's toll **11.3%** for 2.1% of its trades.

### 6.4 The unit warning — this one has bitten three lanes

> **A cost quoted in R is not a cost. It is a cost divided by your stop width.**
>
> `cost_in_R = cost_in_money ÷ stop_distance`. Widen the stop by 3× and the cost in R falls by exactly
> 3× while the broker charges you **exactly the same money** — verified to seven decimals.
>
> Consequence: the shipped affordability gate is denominated in R, and stop width has *more* variance
> than the broker does (it explains 44% of the variance in R-cost against the instrument's 30%). So
> the gate is mostly a stop-width filter wearing a cost-filter's clothes. At matched admission depth,
> a gate written in **money** buys **1.43× more edge per unit of toll** than the tightest R gate that
> reaches break-even.
>
> This is also why several cells read positive in bps and negative in R — NY hour 13 reads edge÷toll
> 1.54 in money and **−0.13 R/trade** in money-you-keep. R is what compounds under your sizing. Never
> accept a cell quoted in only one of the two.

---

## 7. WHY THE HUNT DID NOT FIND MORE — the mechanism, in one paragraph

The premise was: *edge is roughly flat across instruments, cost varies twelvefold, so there must be
cells where edge already beats cost.* The first half is false in a specific and decisive way.

**Cost is stable and edge is not.** Ranking the 24 instruments by what they cost in Jan–Mar and
re-reading Apr–May, the rank correlation is **0.83**. Ranking them by their gross edge and re-reading,
it is **0.02** — nothing. Cells whose edge beat their cost in the hunt window do carry real
information into April and May (28% of them still pay, against a 4.5% base rate — a 6.2× lift), **but
the information is the broker's fee schedule, not an edge.** Hold cost fixed within its decile and
that 6.2× lift collapses to 1.6×.

So selecting on affordability re-discovers which instruments are cheap. It does not locate edge,
because instrument-level edge does not sit still. That is the honest reason this is one cell and not
a portfolio.

---

## 8. THE ONE THING HERE THAT REACHES YOUR LIVE ACCOUNTS

**Your live cost model charges ZERO commission on both oil symbols, and one of your four armed sleeves
trades them.**

- `energy_agri` is **ARMED on both FTMO and redacted_account** and its instruments are
  `USOIL_cash, UKOIL_cash, CORN_c, COTTON_c` (`src/components/ultimate_book/admission.py:168-177`).
- The live cost artifact — the one Session CN made the default fourth cost term on both books —
  carries FTMO `UKOIL.cash` and `USOIL.cash` as `kind: "zero"`, `coverage: "TRANSFERRED"`, transferred
  from **FTMO's *index* class**, which genuinely is zero-commission.
- On **redacted_account**, h4 read the actual deal records: **$5.00/lot on both oils = 5.17 and 5.37 bps
  round turn** — and FTMO's oil contract is the same 100-barrel spec.

Neither number is a measurement of FTMO oil (FTMO never traded oil in the captured window). But one
transfer is from *a different instrument at the same broker* and the other is from *the same
instrument at a different broker with an identical contract*. The second is the better-matched peer.

At a 1%-of-price stop, 5.3 bps is about **0.05 R per trade** of cost currently set to zero on an armed
sleeve. **Worth an hour to check against an FTMO statement.** Same lane also measured two other live
defects: BTCUSD commission is modelled **1.47× too low** and ETHUSD **1.81× too low**, both because a
fee measured as a fixed price amount at one price level was reapplied at a much higher one.

---

## 9. WHAT IS THIN — no burying

| Claim | How thin |
|---|---|
| The GER40 survivor | 1,630 trades, 5 months, P(≤0) = 14%. Out-of-sample half is a coin flip (P = 40%). 73.5% of the P&L is 3 days. |
| Its cost gate | Chosen after seeing 3 months. Ungated GER40 is *better* out of sample. Treat the threshold as unproven. |
| The honest exit rule | It is a **bound**, not a measurement. Truth lies between the two columns in §3. Only tick data settles it — and that is the single biggest open number in the estate. |
| The hour-true spread model | A *median* per broker hour, transferred from a June–July tick capture onto Jan–May. Better than one constant per symbol (measured 27% lower error at 149 real fills) — not the tick-exact quote. |
| Multiplicity | Formally, **nothing survives.** Zero of 4,130 cells clear the Westfall–Young test at any threshold. Everything in this report is a lead. |
| All costs are FTMO | redacted_account's BTCUSD spread was measured at **21.9× FTMO's**. None of this surface transfers between your two brokers. |
| April/May is the last data | There are no June/July 2026 M1 bars on this machine. The next honest test needs a capture. |

---

## 10. WHAT TO DO NEXT — ordered, with what each is worth

| # | Action | What it is worth | Cost |
|---:|---|---|---|
| **1** | **Settle the trailing-stop question with tick data.** Re-walk the exits at tick resolution instead of one-minute bars. | **±0.084 R/trade on every exit number this estate has ever published** — 2.2× the entire headline. It decides whether nine of the ten cells in §2 are real or artifacts, and it also reaches your armed sleeves' published exit economics. This is the biggest single number outstanding. | Ticks already exist for 2026-06-18…07-24 (263.9 M rows, outside the repo). Jan–May ticks would need a capture. |
| **2** | **Capture June + July 2026 M1 bars.** | Two more never-seen months for the GER40 object — roughly +650 trades on 1,630, and the only way to move P(≤0) from 14% toward a decision. Nothing else can. | One bar export. Cheapest decisive thing on this list. |
| **3** | **Check FTMO oil commission against a statement** (§8). | Fixes a live cost term currently set to zero on an armed sleeve; ~0.05 R/trade. Also fixes BTCUSD (1.47×) and ETHUSD (1.81×) in the research cost library. | One statement, one hour. |
| **4** | **Re-denominate the affordability gate from R to basis points**, and key the spread on the broker hour. | Measured: **1.43× more edge per unit of toll at matched admission depth**. The shipped gate, even fed broker-true costs, buys 0.19. It is currently admitting half the book on a number that is mostly stop width. | A contained code change; note the config file is decision-contract-bound (H1). |
| **5** | **Refuse candidates generated while the instrument's own market is closed.** | 0.38% of rows; **40% of the surviving cell's headline**. Removing them makes every future number honest and costs nothing. | Trivial — ten instruments, one hour each. |
| **6** | **Do NOT build an instrument-selection or cell-selection layer on this evidence.** | Instrument-level gross edge has rank persistence **0.024** across windows. Any such layer would be re-discovering the fee schedule. The one exception is GER40, and it is a single lead pending #1 and #2. | — |

---

## 11. THE HONEST BOTTOM LINE

The signal is real: with no trailing stop and nothing to argue about, the whole book is gross-positive
at **+0.0292 R/trade** across 43,755 trades. The broker charges **0.2203 R**. That is a **7.6× gap**,
and no execution improvement closes it — even at zero spread and zero slippage the pooled book still
loses money, because commission alone is 2.5× the edge.

The gap closes only by not trading — and after charging the broker by the hour, applying your own
ratified honest exit rule, reading two months nobody had seen, and removing trades placed into a shut
market, exactly one thing is left: **GER40, plain stop, cheap hours, +0.0475 R/trade on 1,630 trades
at 2.4× its own toll (1.75× out of sample) — positive in four months of five, and not yet
significant.**

That is a lead worth two cheap measurements (#1 and #2 above). It is not yet a strategy, and nothing
in it is a reason to touch either armed account.

---

## 12. WHERE THE NUMBERS LIVE

| File | What |
|---|---|
| `h1_RESULT.md` / `.json` | the cost surface at full resolution; 651 paying cells; the ex-ante money gate |
| `h2_RESULT.md` / `.json` | the cash-session rule; the permutation null; edge-vs-cost independence |
| `h3_RESULT.md` / `.json` | how much toll is mechanically removable (4.32× ceiling); passive entry; every lever ranked |
| `h4_RESULT.md` / `.json` | live broker truth — 289 positions, 589 deals, 149 reconciled fills; the commission defects |
| `h5_RESULT.md` / `.json` | the full 4,130-cell enumeration; April+May; the multiplicity bill; the cost-vs-edge persistence control |
| `h6_RESULT.md` / `.json` | the joint contract sweep (28,800 contracts); the trailing-stop bar premium; the no-trail cell |
| **`B2_VERIFY_V1.json`** | **this report's Check 1 and Check 2** — every lane's cell under the honest exit rule, and April+May |
| **`B2_GER40_V1.json`**, **`B2_GER40_OPEN_V1.json`** | **the survivor, measured to the floor** |
| **`B2_CLOSED_V1.json`** | **the closed-market rows, priced** |
| `b2_verify.py`, `b2_ger40.py`, `b2_closed.py` | scripts for all three; ~25 seconds total |

No sealed replay was run, no VPS was touched, no broker-capable script was executed, nothing was
committed.
