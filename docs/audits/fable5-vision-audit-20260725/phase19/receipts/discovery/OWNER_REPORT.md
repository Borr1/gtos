# What we found — the January–May forensic, in plain language

**For Borhen. 2026-08-06. Phase 19 discovery swarm: 21 investigation lanes, five months of replay,
124,722 candidate trades examined one by one.**

---

## Read this first: what this is, and what it is not

**What was examined.** Every trade the *broad V4 research selector* considered in January, February,
March, April and May 2026 — taken, rejected, and killed. 27,658 candidates in January alone, plus the
minute-by-minute price path of each one for two hours after the decision. This is the research stack
that has never traded live.

**What was NOT examined.** Your live book. `crypto`, `energy_agri`, `sub_xvol_pullback` and
`mx_btcusd` on FTMO, and the four core sleeves on redacted_account, are a different family with a different
holding horizon (they run to 320 hours; this pool's entire measurement window is 2 hours — 160× shorter).
**Nothing in this report is a reason to touch either armed account.** One finding does reach live
indirectly and it is flagged in bold in section 1, find 5.

**Vocabulary, once.**

| Term | What it means here |
|---|---|
| **R** | One risk unit. If the stop is 40 points away, 1 R = 40 points. "+2 R" = the trade made twice what it risked. Everything is quoted per trade in R unless it says bps. |
| **bps** | Basis point = 0.01% of the instrument's price. Used when R would mislead (see the box in section 4). |
| **Gross** | Before any broker cost. The raw price move. |
| **Net** | After spread + commission + slippage + swap. |
| **The pool** | The 27,658 January candidates. It contains *no executed trades* — it is by construction the set the engine considered and did not headline-execute. |
| **Fill-honest** | The trade only counts if the market actually traded the entry price. The old convention scored trades that were never fillable; that alone manufactured +0.2776 R/trade of fake profit. |
| **t** | How many standard errors from zero. Above 2 is unlikely to be luck; above 5 is essentially certain not to be luck. |
| **Born state** | What kind of order the candidate actually was at the instant it was created — see section 3. |

---

## 1. The finds

### FIND 1 — The signal is real, and it is present on every single instrument

Take only the orders the live engine can actually place (see find 3), delay the entry by five minutes,
and exit with a 0.25 R trailing stop instead of the declared 2 R target / 1 R stop. Across January,
February and March, 43,755 trades:

**Every one of 24 instruments is gross-positive.** Not eight. Not nineteen. All twenty-four.

Pooled: **+0.038342 R/trade gross, t = +12.35**, 95% bootstrap interval [+0.030076, +0.046177],
p(≤0) = 0.0000 over 63 trading days, and **53 of those 63 days are positive**.

| Instrument | n | Gross R/trade | Cost R/trade | Net R/trade | t (net) | Win % | Edge (bps) | Cost (bps) | Edge÷Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GER40 | 1,858 | +0.0646 | 0.0466 | **+0.0180** | +1.23 | 76.7 | +0.911 | 0.501 | **1.387** |
| US30_cash | 1,942 | +0.0325 | 0.0519 | −0.0194 | −1.43 | 75.8 | +0.375 | 0.403 | 0.627 |
| XAUUSD | 1,996 | +0.0466 | 0.0713 | −0.0247 | −1.77 | 76.8 | +0.906 | 1.282 | 0.654 |
| NAS100 | 1,904 | +0.0237 | 0.0516 | −0.0279 | −2.05 | 76.3 | +0.259 | 0.575 | 0.460 |
| UK100 | 2,002 | +0.0615 | 0.1014 | −0.0399 | −2.78 | 77.3 | +0.726 | 0.822 | 0.607 |
| JP225 | 1,627 | +0.0348 | 0.0795 | −0.0448 | −2.96 | 76.1 | +1.297 | 1.462 | 0.437 |
| BTCUSD | 1,415 | +0.0422 | 0.1227 | −0.0805 | −4.77 | 75.3 | −0.255 | 4.593 | 0.344 |
| SPX500 | 1,850 | +0.0249 | 0.1184 | −0.0935 | −6.50 | 75.5 | +0.429 | 0.941 | 0.210 |
| EURUSD | 1,863 | +0.0586 | 0.1692 | −0.1106 | −6.61 | 76.2 | +0.083 | 0.686 | 0.346 |
| USDJPY | 2,442 | +0.0643 | 0.1837 | −0.1194 | −9.04 | 77.5 | +0.317 | 0.829 | 0.350 |
| GBPUSD | 2,054 | +0.0344 | 0.1557 | −0.1214 | −7.42 | 75.1 | −0.037 | 0.746 | 0.221 |
| AUDUSD | 1,627 | +0.0294 | 0.1518 | −0.1224 | −7.89 | 75.3 | −0.139 | 1.155 | 0.194 |
| USDCHF | 1,854 | +0.0443 | 0.2121 | −0.1679 | −10.26 | 76.1 | +0.125 | 1.117 | 0.209 |
| XAGUSD | 1,968 | +0.0360 | 0.2062 | −0.1702 | −11.37 | 75.0 | +0.561 | 9.670 | 0.174 |
| EURJPY | 1,564 | +0.0278 | 0.2143 | −0.1865 | −10.49 | 75.6 | +0.087 | 1.094 | 0.130 |
| ETHUSD | 1,366 | +0.0022 | 0.1908 | −0.1886 | −11.44 | 72.6 | −2.122 | 9.832 | 0.012 |
| CHFJPY | 1,547 | +0.0428 | 0.2385 | −0.1957 | −10.13 | 75.9 | +0.244 | 1.348 | 0.179 |
| AUDJPY | 1,604 | +0.0361 | 0.2321 | −0.1961 | −11.86 | 76.5 | +0.101 | 1.801 | 0.155 |
| GBPJPY | 1,978 | +0.0457 | 0.2455 | −0.1998 | −14.44 | 78.7 | +0.146 | 1.274 | 0.186 |
| USDCAD | 2,010 | +0.0205 | 0.2621 | −0.2416 | −15.61 | 74.1 | −0.118 | 0.851 | 0.078 |
| NZDUSD | 1,943 | +0.0371 | 0.2824 | −0.2454 | −14.61 | 75.2 | +0.020 | 1.883 | 0.131 |
| EURGBP | 1,865 | +0.0377 | 0.3166 | −0.2789 | −19.47 | 78.5 | +0.026 | 1.015 | 0.119 |
| USOIL_cash | 1,777 | +0.0352 | 0.3428 | −0.3076 | −18.91 | 75.6 | +0.348 | 9.772 | 0.103 |
| UKOIL_cash | 1,699 | +0.0152 | 0.3387 | −0.3235 | −18.98 | 74.8 | +0.530 | 8.710 | 0.045 |
| **Pooled** | **43,755** | **+0.038342** | **0.181834** | **−0.143492** | **−44.88** | ~76 | **+0.231** | **2.457** | **0.094** |

*Source: `E_ATMKT_PERSYMBOL_V1.json`, `E_ATMKT_POOLED_V1.json`, `E_ATMKT_BOOTSTRAP_V1.json`.*

**Honest qualification on the same table, stated immediately rather than in a footnote.** The R column
is positive 24/24; the price column (bps) is positive on **19 of 24** — BTCUSD, GBPUSD, AUDUSD, USDCAD
and ETHUSD are negative once you stop letting tight-stop trades count for more. Both facts are real;
the price column is the more conservative one and it is the one I use everywhere below.

### FIND 2 — The edge is one tenth of the toll, and that is the whole problem

Pooled across the same 43,755 trades:

- What the signal earns: **+0.231 bps** per trade.
- What the broker charges: **2.457 bps** per trade.

The edge is **9.4%** of its own cost. That is the single number that governs this entire system. It is
not a modelling artifact — it is measured against 300,538,915 real broker ticks and validated against
296 real order captures from your own two accounts.

**One instrument beats its toll: GER40, ratio 1.387, net +0.0180 R/trade, positive in all three months
(+0.012 / +0.019 / +0.023).** At n = 1,858 and t = +1.23 that is a lead, not a result. It is the
cheapest instrument on the FTMO surface (0.501 bps round trip) and it carries a middling signal — which
is exactly the shape you would expect the first survivor to have.

### FIND 3 — 46% of the research book is an order type your live engine cannot place

This is the biggest single disconnect between the research stack and reality, and nobody had checked it.

Every candidate is one of four things at the instant it is born:

| Born state | n | Share | Gross R/trade | Win % | Can live place it? |
|---|---:|---:|---:|---:|---|
| **At market** — entry price = the price right now | 14,911 | 53.9% | −0.0904 | 39.5% | **Yes** |
| **Resting limit** — entry sits away from the market, waiting | 7,949 | 28.8% | −0.1049 | 42.0% | **No** |
| **Marketable limit** — entry already through the market | 1,265 | 4.6% | −0.2566 | 28.7% | **No** |
| **Stop already broken** — the stop price is *already gone* | 3,516 | 12.7% | **−0.9948** | **0.085%** | **No** |

*Source: `W0CAP2_NOLOOKAHEAD_FULL_V1.json`. Measured with zero look-ahead — from the last bar that
closed strictly before the decision.*

**The live engine has never placed a limit order and cannot.** On 296 captured live orders from your
own accounts, the requested entry price equals the broker's executable quote — bid for a short, ask for
a long — on **296 of 296**, to floating-point exactness. Zero displacement, zero exceptions
(`L10X_LIVE_BORNSTATE_V1.json`; the only entry `order_send` in the tree is
`src/components/execution.py:3534`, action `TRADE_ACTION_DEAL`, i.e. a market order).

So 46.088% of the research book describes orders that do not exist in your system. And it is not spread
evenly — it is three families:

| Family | Share that is live-placeable |
|---|---:|
| cross_asset_lead_lag, liquidity_sweep_reclaim, regime_transition_break, session_open_range_break, structural_distance_extreme, volatility_compression_expansion | 100.0% |
| displacement_continuation | 99.91% |
| **current_fvg_fill** | **0.08%** (6 of 7,146) |
| **current_ob_retest** | **0.00%** (0 of 1,340) |
| **current_breaker_re_entry** | **0.00%** (0 of 4,263) |

**And the obvious fix does not work — it was priced, not assumed.** Converting those POI limits into
market orders at the same setup with the same stop (a one-line generator change) books **−0.482 R/trade,
t = −56.83, on 9,214 trades**, holding in both halves of the month and after de-duplication
(`E_CONVERT_V1.json`). The edge in those families *is the level*. Entering at market destroys it
completely. They are not repairable by re-typing the order; they need a limit-order capability the
engine does not have.

### FIND 4 — 12.7% of January's candidates were dead before they were born

3,516 candidates were emitted with a stop-loss price the market had **already passed** — median 7.58
stop-widths past the entry. Every one books a mechanical −0.9948 R at a 0.085% win rate. 51.7–55.7% of
them quote an entry the market had not traded in the prior 24 hours. They are not orders that lost; they
are levels the generator never retired.

Removing them moves January from **−0.21724 to −0.10392 R/trade** with no look-ahead whatsoever
(+0.11332 R/trade). It persists in every month: 12.71% / 7.54% / 5.76% / (April, May similar), and
**98.61% of them are one family** — `current_breaker_re_entry`.

### FIND 5 — **A candidate standing at the live factory tip is 103.4% artifact**

This is the one finding that reaches your live decision surface.

Session CQ's inverted-breaker candidate — published at **+11.9 net R/trade** on both TRAIN and January
validation, standing at the V27 family tip as a factory candidate — was matched trade-by-trade back to
its source candidates. **81.33% of its trades come from candidates whose stop was already broken before
the order could be sent.** On those it "wins" 83.88% of the time and books +15.127 R/trade. On the 596
trades that were genuinely takeable it wins **1.01%** of the time and books **−2.644 R/trade**.

Artifact share: **103.37%**. The published edge is not merely inflated — it is entirely the artifact,
and the real trades lose money. *Source: `W0CAP2_CQ_NOLOOKAHEAD_V1.json`, corroborated independently in
`W0CAP2_CQJOIN_V1.json`.*

**Action: that candidate should be struck from the factory family, not promoted.**

### FIND 6 — The cost model is not "too expensive". It is scrambled, per instrument, by up to 33.9×

The frozen research cost model charges a **single hardcoded constant per symbol** for 16 of 24 symbols —
no session, no hour, no volatility, no era. For nine symbols that constant is the config's
`max_spread_cents` value, which is the *refusal ceiling* ("reject if wider than this"), being charged as
the *expected* spread.

| Symbol | Frozen spread (R) | Real spread (R) | Frozen ÷ Real | Passed frozen gate | Would pass real gate |
|---|---:|---:|---:|---:|---:|
| NAS100 | 1.6422 | 0.0484 | **33.90×** | **0** | 1,277 |
| SPX500 | 1.8083 | 0.0996 | **18.16×** | **0** | 973 |
| ETHUSD | 0.8320 | 0.0894 | 9.31× | 7 | 326 |
| JP225 | 0.6285 | 0.0961 | 6.54× | 12 | 698 |
| UK100 | 0.6994 | 0.1164 | 6.01× | 3 | 760 |
| EURJPY | 0.8177 | 0.1963 | 4.17× | 28 | 309 |
| US30_cash | 0.2490 | 0.0614 | 4.06× | 300 | 1,105 |
| GER40 | 0.2164 | 0.0540 | 4.01× | 235 | 1,050 |
| GBPUSD | 0.1830 | 0.0557 | 3.29× | 230 | 507 |
| CHFJPY | 0.3019 | 0.1124 | 2.69× | 42 | 240 |
| USDJPY | 0.0547 | 0.0277 | 1.97× | 407 | 518 |
| AUDUSD | 0.0793 | 0.0473 | 1.68× | 265 | 376 |
| NZDUSD | 0.2021 | 0.1371 | 1.47× | 99 | 229 |
| EURGBP | 0.2435 | 0.1781 | 1.37× | 67 | 148 |
| USDCAD | 0.0709 | 0.0685 | 1.04× | 233 | 371 |
| USDCHF | 0.0875 | 0.0854 | 1.03× | 296 | 431 |
| AUDJPY | 0.1066 | 0.1098 | 0.97× | 194 | 257 |
| GBPJPY | 0.1352 | 0.1413 | 0.96× | 227 | 259 |
| XAGUSD | 0.0703 | 0.1238 | 0.57× | 605 | 364 |
| XAUUSD | 0.0511 | 0.0905 | 0.57× | 1,986 | 1,265 |
| EURUSD | 0.0073 | 0.0168 | 0.44× | 526 | 478 |
| USOIL_cash | 0.0270 | 0.2949 | **0.09×** | 574 | 86 |
| UKOIL_cash | 0.0258 | 0.3088 | **0.08×** | 659 | 75 |
| BTCUSD | 0.0001 | 0.0059 | **0.02×** | 215 | 527 |

*Source: `L10X_POOL_RECOST_V1.json` — real spread from 300,538,915 broker ticks across 61 series,
cross-validated against 296 live broker quotes (median agreement 1.008×).*

Read the two extremes together: the model charges the index book **12–34× too much** and the oil and
crypto book **7–41× too little**. The consequence is exact and it is not subtle: **the minimum frozen
spread over all 1,943 SPX500 rows is 0.24479 R and over all 1,622 NAS100 rows is 0.16326 R, against a
0.10 R cap. Not one index candidate could have passed in the entire month, under any circumstance.**
Meanwhile oil, whose true cost is 97–99% of the money it risks, sailed through.

**The correction to everyone's headline, including the lane that found it.** The frozen model overcharges
the pool by +0.4739 R/trade — but **100% of that error sits on rows the gate refuses**. On rows it
*admits*, the error is **−0.0315** (it slightly *under*charges). The gate selects almost perfectly on
its own error. So the +0.4739 is a bookkeeping correction, not recoverable money.

| Month | Overcharge, all rows | Overcharge, ADMITTED rows | Overcharge, REFUSED rows |
|---|---:|---:|---:|
| January | +0.4739 | −0.0315 | +0.6521 |
| February | +0.3332 | −0.0186 | +0.4643 |
| March | +0.2798 | +0.0213 | +0.4182 |
| April | +0.4423 | +0.0231 | +0.5670 |
| May | +0.4635 | −0.0293 | +0.5971 |

*Source: `E1_SELECTION_ON_ERROR_V1.json`.*

---

## 2. "Do the trades we take look like the shape of trades we want?"

**No — and the reason is not the win rate.**

### The shape as shipped

| | Declared contract | Actually realized |
|---|---:|---:|
| Target | +2.00 R | average winner **+1.044 R** |
| Stop | −1.00 R | average loser **−0.888 R** |
| Payoff (win size ÷ loss size) | 2.00 : 1 | **1.18 : 1** |
| Win rate needed to break even | 33.3% | **45.94%** |
| Win rate achieved | — | **34.68%** |
| Shortfall | — | **11.25 percentage points** |

The framing that has been circulating — "we win 34.7% against a 33.3% breakeven, eight of ten families
beat breakeven" — compares the achieved win rate against the breakeven of a payoff we *do not achieve*.
Measured against the payoff we actually realize, **zero of ten families beat breakeven.**

### Where the winners go

Of 23,884 tradeable candidates walked honestly:

| Exit | n | Share | Mean R |
|---|---:|---:|---:|
| Stop | 12,299 | 51.50% | −1.000 |
| Marked at the 2-hour wall | 7,844 | 32.84% | +0.237 |
| Full target | 3,709 | 15.53% | +2.002 |
| Same-bar ambiguous | 32 | 0.13% | — |

**56.45% of all winners never reach the target — they are valued mid-flight at +0.593 R when the
measurement window closes.** That is what produces the 1.18:1 payoff. It is a property of the research
instrument, not a policy defect: nothing in the source cuts a winner short. Continuing those trades on
raw price data for 24 hours past the wall resolves them 41.31% target / 52.8% stop and improves the book
by only **+0.017 R/trade** — so the wall is not hiding money either.

### What the machine finally chooses

Of 24,125 tradeable candidates in a full month, the selector says "trade" on **21**. Of those 21,
**none reaches the 2 R target.** 33.3% take a full stop; 57.1% touch neither target nor stop.

Fifteen stages of machinery, 27,658 candidates, and the surviving twenty-one are indistinguishable from
noise.

### The belief layer is pointed backwards

The engine's own confidence score is *negatively* related to the outcome it forecasts:

| Confidence decile | Stated probability | Actually reached +2 R |
|---|---:|---:|
| Bottom 10% | 0.6547 | **20.47%** |
| Top 10% | 0.9276 | **4.02%** |

It is 5.09× more likely to hit target in the decile the system trusts *least*. The mechanism is
mechanical, not mystical: `candidate_probability` is 0.712 rank-correlated with fill probability and
−0.478 with cost — it is measuring *quietness*, not edge. It has never once printed a negative expected
value in 27,658 rows, against a pool that loses 0.2175 R/trade.

---

## 3. "Do the ones we missed look better?"

**On paper, spectacularly. On orders you could actually have placed, no. This is the most important
correction in the report.**

Several lanes found gates refusing profitable cohorts, and those numbers are real:

| What refused it | n | Gross R/trade (all rows) |
|---|---:|---:|
| `numeric_confluence_structured_disagreement` — "my own numbers disagree" | 484 | **+0.1533** |
| `execution_fillability` blocker class | 449 | **+0.1044** |
| `same_symbol_daily_loss_lockout` — the revenge-trade guard | 55 | **+0.1265** |
| `daily_lockout` blocker class | 47 | **+0.1268** |

I then asked the question no lane had asked: **how many of those refused-and-profitable candidates were
orders the live engine could actually place?** Measured directly (new this session,
`OWNER_REPORT_GATE_CHECK_V1.json`):

| What refused it | n, all | Gross, all | n, live-placeable | Gross, live-placeable | t |
|---|---:|---:|---:|---:|---:|
| numeric_confluence_structured_disagreement | 484 | +0.1533 | **20** | **−0.2481** | −1.09 |
| execution_fillability | 449 | +0.1044 | **0** | — | — |
| marketable_guard | 156 | −0.5175 | 62 | +0.0932 | +0.67 |
| same_symbol_daily_loss_lockout | 55 | +0.1265 | 16 | +0.5774 | +1.77 |
| daily_lockout | 47 | +0.1268 | 11 | +0.4763 | +1.32 |
| cost_authority (the big one) | 20,448 | −0.2822 | 10,174 | −0.1435 | −12.32 |
| package_authority | 2,668 | −0.1278 | 2,013 | −0.1094 | −4.80 |
| scheduler_selection | 689 | −0.0734 | 485 | −0.0445 | −0.89 |
| off-session entry block | 1,079 | −0.1107 | 542 | −0.0390 | −0.92 |

**On the 14,911 orders the live engine can place, not one gate is refusing a materially positive
cohort.** The two that stay positive (the daily-loss lockout and the daily lockout) carry 16 and 11
rows. The theory that we are strangling a live edge with gates is **false for placeable orders** — and
true only for POI limit orders that cannot be placed at all.

For completeness, the frozen cost gate on that same placeable population:

| | n | Gross R/trade |
|---|---:|---:|
| Population baseline (all live-placeable) | 14,911 | −0.1270 |
| Kept by the cost gate | 4,737 | −0.0916 |
| Refused by the cost gate | 10,174 | −0.1435 |

The gate does pick slightly better trades on placeable orders (+0.052 R/trade separation), but almost
all of its apparent value elsewhere is **abstention** — declining a losing pool is worth money whenever
the pool loses, and it requires no skill at all. Decomposed across every filter in the swarm, only ONE
mechanism is majority-selection: dropping the already-broken-stop rows (76.2% selection). Everything
else is 65–90% abstention.

---

## 4. Where exactly the edge is lost

Every step measured on the same rows, additively, in order:

| Step | n | Gross R/trade | Cost R/trade | Net R/trade | Gain |
|---|---:|---:|---:|---:|---:|
| 0 — as published | 27,658 | −0.2175 | 0.6632 | **−0.8807** | — |
| 1 — charge the real broker cost (accounting only; no dollars move) | 27,658 | −0.2175 | 0.1893 | −0.4068 | +0.4739 |
| 2 — keep only orders the live engine can place | 14,911 | −0.0597 | 0.2124 | −0.2721 | +0.1348 |
| 3 — apply a broker-true cost gate | 7,317 | −0.0564 | 0.0687 | −0.1251 | +0.1470 |
| 4 — 5-minute entry delay + 0.25 R trailing exit | 7,317 | **+0.0178** | 0.0687 | **−0.0509** | +0.0742 |

*Source: `E_FINAL_V1.json`. The book turns gross-positive at step 4 and is still net-negative because
the toll is 3.9× the edge.*

### The four repairs, ranked by what each is actually worth

| # | Repair | Worth | Replicates? | Confidence |
|---|---|---:|---|---|
| 1 | **Do not enter at the trigger bar's close.** Wait 5 minutes. | **+0.0662 R/trade** | Jan +0.06689, Feb +0.06610, Mar +0.06572 | Very high — three months within 0.0012 R |
| 2 | **Cancel, don't chase.** If the level is not touched in 60 s, stand down. | **+0.1283 R/trade** | 5 of 5 months, 101/101 days positive, 569 conditioning cells with 11 tiny negatives | Very high |
| 3 | **Replace the 2 R target / 1 R stop with a 0.25 R trailing stop.** | **+0.0431 R/trade** | 15 of 15 test cells, beats a holding-time-matched permutation at p = 0/200 in all 3 months | High |
| 4 | **Fix the per-symbol cost model.** | +0.0157 R/trade of real money (the +0.4739 is bookkeeping) | 5 of 5 months | High — and it is what un-deletes the index book |

**Repairs 1 and 3 are 95.0% additive** — they fix different things and stack almost cleanly
(alone +0.06624 and +0.04311, together +0.10392). **Everything else in the swarm overlaps.** Priced
alone the six main levers sum to +1.266 R/candidate; together they deliver +0.421. **66.8% is
double-counting** (65.5% in February, 63.4% in March). Any future claim that adds two of these numbers
together is wrong by roughly two thirds.

### The mechanism behind repair 1, measured not inferred

All seven generating families set `entry = bar.close` — the extreme of the very bar whose extremeness
triggered the signal. The market gives that back inside sixty seconds:

| Month | Mean signed R against the signal, 1 minute after entry | In bps |
|---|---:|---:|
| January | −0.064669 | −0.657 |
| February | −0.076711 | −0.831 |
| March | −0.067815 | −1.131 |

That concession is **27–46% of the entire 2.457 bps round-trip cost**, paid voluntarily, on top of the
spread. And it is adverse selection, not drift: candidates whose entry is touched within the first 60
seconds book −0.19754 R against −0.03861 for everything else, and the faster the first minute moves the
worse the fill is — from −0.207 R when the first minute is quiet to **−0.737 R** when it is violent, a
24× separation.

> ### The one piece of arithmetic that has misled every prior session
>
> Cost is quoted in R, and R is defined by the stop. So `cost_in_R = cost_in_price ÷ stop_distance`.
> **Halving the stop doubles the measured cost with no change to the trade whatsoever.**
>
> This is why the cost gate looked predictive: within a symbol, `cost_r` is rank-correlated with
> 1 ÷ stop-distance at **0.9966 or better for 18 of 24 symbols, and exactly 1.0000 for four of them.**
> The cost gate has never been a cost gate. It is a stop-width filter wearing a cost costume — and the
> stop-width ordering it accidentally implements is real (widest-decile minus tightest-decile is
> +0.0931 R/trade, positive in 5 of 5 months). We got a real effect by accident, through a broken model,
> in the wrong units.
>
> The same arithmetic is why "R improved" claims must always be checked in price space. Removing the
> stop entirely changes January's price-space expectancy by **+0.00264 R** — the stop is fairly priced
> to three decimals — while looking dramatic in R terms.

---

## 5. "Is any strong point actually blossoming?"

Three, in descending order of how much I would trust them.

### Lead 1 — GER40 (highest confidence, smallest claim)

Net **+0.0180 R/trade** at broker truth on the live-placeable cohort under the repaired contract.
Positive in all three months (+0.012 / +0.019 / +0.023). n = 1,858, t = +1.23. The only instrument of 24
whose edge exceeds its own toll (ratio 1.387). It is the cheapest instrument on the surface at 0.501 bps.

**What it is:** a genuine, replicated, live-expressible cell that clears no significance bar. It is the
right first candidate for a forward-only paper record.

### Lead 2 — XAUUSD × current_fvg_fill (largest number, largest caveat)

Net **+0.284 R/trade** in January, **+0.251** February, **+0.276** March. It survives every
de-duplication cut (one row per setup per day: +0.328 / +0.345 / +0.337), both sides are positive in all
three months, and 83–85% of individual trades are positive. It is by a wide margin the biggest number
anyone found.

**And it is a resting limit order, which means two things, both disqualifying today.**

1. Your engine cannot place it (find 3).
2. **The measured population is conditioned on the fill.** The pool physically cannot contain a resting
   limit that failed to fill — the code returns `None` and the pool filter drops it. Measured
   consequence: at a depth of 1 R or more, the entry level is touched **100.00%** of the time in the
   pool, against **17.6–18.7%** for an identical mirror limit the same distance on the other side. A
   **5.4–5.7× magnet ratio**. At 2 R depth it is 8.4–10.8×.

   In plain terms: we are only ever shown the limits that filled, and they filled roughly five times
   more often than a fair coin would allow. The size of that bias is roughly **0.179 R/trade** — larger
   than the +0.15 net the cell claims.

The same instrument entered **at market** — the version you could actually trade — is gross +0.0466,
cost 0.0713, **net −0.0247, t = −1.77**.

**Verdict: do not trade this. It is the strongest reason to build a limit-order capability, and the
strongest reason not to believe it until an unconditioned measurement exists.**

### Lead 3 — the cheapest cost band

Restricting to trades whose broker-true cost is under 0.02 R, under the repaired contract:

| Month | n | Gross | Cost | Net |
|---|---:|---:|---:|---:|
| January | 613 | +0.0320 | 0.0139 | **+0.0181** |
| February | 807 | +0.0043 | 0.0136 | −0.0093 |
| March | 1,543 | +0.0152 | 0.0125 | +0.0027 |

Pooled ≈ **+0.0026 R/trade** on 2,963 trades. Essentially breakeven. Its value is not the number — it is
that it confirms the diagnosis exactly: *the edge is roughly constant and the outcome is decided by what
the trade costs.* Across a 43× range of stop width and a 43× range of cost, the edge-to-cost ratio never
exceeds **0.31** in any of ten deciles in any of three months.

### One more that is real but not a trade

The entry-timing repair (find 4 / repair 1) is the most reproducible quantitative fact in the whole
swarm — three independent months within 0.0012 R of each other, confirmed by four separate lanes using
different code. It is not an edge; it is a leak we are choosing to pay.

---

## 6. What was tested and did *not* pan out

Short, because you asked for finds and not refutations — but these close off expensive directions.

| Hypothesis | Verdict | The number |
|---|---|---|
| The stop is too tight and kills winners | **No.** Removing the stop entirely changes price-space expectancy by +0.00264 R. The stops are 4.03× the 1-minute ATR, not tight. | n = 24,142 |
| We give money back — winners retrace before stopping | **No.** Median stop never went more than +0.239 R in favour. | n = 12,299 |
| A better exit contract rescues it | **No.** 3,472 contracts × 16 conventions: zero gross-positive cells. Every fixed exit *level* is value-destroying at all 22 levels tested. | — |
| Breadth / more instruments diversifies the problem away | **No.** 246 members × 30 families × 134,027 trades: 0 admit. | prior wave |
| The win rate is the problem | **No.** The payoff is. 34.68% against a 45.94% realized breakeven. | — |
| Correcting the cost model releases trapped profit | **Mostly no.** 100% of the overcharge is on refused rows. The real repair value is +0.0157 R/trade plus un-deleting the index book. | 5 months |
| Break-even stops help | **No — they destroy.** Moving to break-even at +0.25 R converts 5,220 winners into scratches for +0.00275 R/trade. | n = 24,142 |
| Inverting the signal (it loses, so do the opposite) | **Partially real, not harvestable.** +0.0764 R/trade on at-market rows, t = 8.71 — but 81% of it is gone after two minutes and it is worth 0.783 bps against a 1.566 bps two-leg spread. | n = 14,911 |

---

## 7. The five-month picture

Everything above was found on January and then checked on four other months. The structure is stable:

| Month | Candidates | Gross R/trade | Frozen cost | Real cost | Net at real cost | Overcharge ratio |
|---|---:|---:|---:|---:|---:|---:|
| January | 27,658 | −0.2175 | 0.6632 | 0.1893 | −0.4068 | 3.50× |
| February | 24,239 | −0.1506 | 0.4895 | 0.1562 | −0.3068 | 3.13× |
| March | 26,500 | −0.1767 | 0.4046 | 0.1247 | −0.3015 | 3.24× |
| April | 25,056 | −0.2319 | 0.6233 | 0.1810 | −0.4129 | 3.44× |
| May | 21,285 | −0.2387 | 0.6644 | 0.2009 | −0.4396 | 3.31× |

All 25 month × book cells are negative. No month is an outlier. **January is the *worst* of the five,
so every headline computed on January is the pessimistic end of the range, not the optimistic one.**

Per-family gross for January (the family names are the pattern generators):

| Family | n | Win % | Gross R/trade | Winner / Loser | Realized payoff |
|---|---:|---:|---:|---:|---:|
| regime_transition_break | 297 | 51.5% | −0.007 | +0.403 / −0.442 | 0.91 |
| liquidity_sweep_reclaim | 4,475 | 40.5% | −0.042 | +1.253 / −0.921 | 1.36 |
| session_open_range_break | 987 | 42.8% | −0.075 | +0.855 / −0.769 | 1.11 |
| volatility_compression_expansion | 605 | 45.0% | −0.087 | +0.351 / −0.445 | 0.79 |
| displacement_continuation | 4,469 | 41.0% | −0.088 | +0.934 / −0.799 | 1.17 |
| current_ob_retest | 1,340 | 44.1% | −0.105 | +0.745 / −0.775 | 0.96 |
| cross_asset_lead_lag | 2,083 | 35.4% | −0.131 | +1.405 / −0.973 | 1.44 |
| current_fvg_fill | 7,146 | 39.2% | −0.142 | +0.965 / −0.855 | 1.13 |
| structural_distance_extreme | 1,993 | 33.2% | −0.182 | +1.457 / −0.995 | 1.46 |
| current_breaker_re_entry | 4,263 | 7.4% | −0.825 | +1.210 / −0.988 | 1.22 |

Note the last row against find 4 and find 5: `current_breaker_re_entry`'s famous 7.4% win rate is not a
strategy result. **81.4% of that family is candidates whose stop was already gone.** Once removed, it
books −0.1058 on 793 rows — an ordinary mediocre family, not a freak.

---

## 8. What to build next — ordered, with what each is worth

Each line is a concrete build, its measured value, and the evidence that licenses it.

**1. Kill the stale-level generator bug. Worth +0.113 R/trade in January, +0.047 to +0.128 across five
months.** Candidates whose stop price has already been passed at the decision instant must not be
emitted. This is a validity check, not a strategy decision: the order is arithmetically impossible. It
is the only mechanism in the entire swarm that is majority *selection* rather than abstention (76.2%).
Half a day of work. *`W0CAP2_NOLOOKAHEAD_FULL_V1.json`.*

**2. Strike the CQ inverted-breaker candidate from the V27 factory family.** It is 103.4% artifact and
its takeable half loses 2.644 R/trade at a 1.01% win rate. This one is a live-consequence item — it is
standing at the factory tip today. *`W0CAP2_CQ_NOLOOKAHEAD_V1.json`.*

**3. Stop entering at the trigger bar's close.** There are three distinct versions of this and they are
not the same operation — the difference is worth knowing before anyone builds the wrong one:

| Version | What it does | Worth |
|---|---|---:|
| **A — delay** | Enter at market five minutes later, at whatever price that is | **+0.0662 R/trade** (Jan +0.06689, Feb +0.06610, Mar +0.06572) |
| **B — cancel** | Place it; if the level is not touched within 60 s, stand down entirely | **+0.1283 R/opportunity** (5 of 5 months, 101 of 101 trading days positive) |
| **C — defer** | Wait 60 s, then still take the same level when it comes back | **−0.0063** — negative in all five months |

A and B are measured on different denominators (per trade taken vs per candidate seen) and must not be
added. B is the larger and it also subsumes item 1 — 99.98% of the already-broken-stop rows fill inside
the first minute, so cancelling removes them without needing any of item 1's machinery. C is the version
that feels most natural and it is the one that loses money. *`E6_CONFIRM_V1.json`,
`E_ATMKT_POOLED_V1.json`.*

**4. Replace the fixed 2 R / 1 R contract with a 0.25 R trailing stop. Worth +0.0431 R/trade and it
stacks 95% cleanly on item 3.** It is the only exit component that is not disguised position-sizing —
it beats a holding-time-matched permutation control at p = 0/200 in all three months. Caveat: it wins
by taking many small wins (~76% win rate); it is a different psychological product from a 2:1 target.
*`E5_TRAIL_V1.json`, `E_CONTRACT_SELECT_V1.json`.*

**5. Replace the per-symbol frozen spread constants with the broker-true model that is already in the
repo (`src/costs/spread_model.py`).** Worth +0.0157 R/trade of real money, and it un-deletes the index
book — SPX500 and NAS100 currently cannot pass the gate on any candidate in any month, because the model
charges them the config's *refusal ceiling* as their expected spread. This is the difference between a
research stack that can see the cheapest instruments and one that structurally cannot. *`E1_*.json`,
`L10X_POOL_RECOST_V1.json`.*

**6. Re-express the cost gate in money, not in R.** A $1,000-risk trade should not be allowed to spend
$150 on costs. The measured zero-crossing is between **$25 and $30 per $1,000 of risk (2.5–3.0%)** on
both truth sources. Today's gate permits $150 on a 1%-risk candidate and $300 on a 2% one. This is also
what stops the gate from silently acting as a stop-width filter. *`l5_RESULT.md` §5.*

**7. Decide the POI-limit question, deliberately.** 46% of the research book is resting-limit orders the
live engine cannot place. Converting them to market orders is measured and it is catastrophic
(−0.482 R/trade, t = −56.83). So the choice is binary: either **build a genuine pending-order capability
in the execution layer**, or **stop generating those three families** and accept the book is 54% of what
the research shows. Do not leave it undecided — today the research stack is measuring a strategy the
production system cannot run, which is how the CQ candidate reached the factory tip. *`E_CONVERT_V1.json`,
`L10X_LIVE_BORNSTATE_V1.json`.*

**8. If and only if item 7 goes the "build it" way: fix the fill-conditioning defect first.** No
resting-limit result in this estate can be believed until the replay records limits that did *not* fill.
The bias is 5.4× at 1 R depth and roughly 0.179 R/trade — bigger than every resting-limit edge anyone has
reported, including the XAUUSD one. *`E_FILLCOND_V1.json`.*

**9. Only then, a forward paper record on GER40 under the repaired contract.** +0.0180 R/trade net,
positive in three months, the only instrument whose edge exceeds its toll. It is n = 1,858 and t = 1.23 —
a candidate for a forward record, not for capital.

### What NOT to build

- **Do not build more gates or more selection layers.** The full 10-predicate stack improves gross by
  0.0168 R/trade; six of its ten predicates have exactly zero marginal effect and two can never fire at
  all because the belief layer's own minimum output sits above their floor. The stack is strictly
  dominated by its own first gate.
- **Do not chase exit geometry any further.** 3,472 contracts × 16 conventions, zero positive cells.
  Items 3 and 4 are the whole of the available exit value.
- **Do not run a sealed replay to test any of this.** Every repair above was measured on evidence already
  on disk, which is why nine of them cost hours rather than the ~16.5 machine-hours a window costs.

---

## 9. The bottom line, stated plainly

**You are right that there is something there.** Under a repaired entry and exit contract the signal is
gross-positive on 24 of 24 instruments, 19 of 24 in price terms, 53 of 63 trading days, in three
independent months, at t = +12.35. That is not noise and it is not a fit — it survived every control
anyone threw at it.

**You are also right that we are doing something to kill it — four things, and they are now named and
priced:** we enter at the worst price of the bar (−0.066 R), we exit on a contract that does not match
the paths (−0.043 R), we generate 46% of the book as an order type we cannot place, and 12.7% of one
month's candidates were dead before they existed.

**But the honest constraint is not a gate and not a layer.** After all four repairs the signal is
+0.231 bps and the broker takes 2.457 bps. The edge is 9.4% of its toll. The gates are not strangling
a live edge — measured directly on the 14,911 orders the engine can actually place, not one gate refuses
a materially positive cohort. What is strangling it is that the thing we found is roughly ten times too
small to pay for itself at the instruments and horizons we are trading it on.

That is a *solvable* shape of problem, and it points somewhere specific: **the same edge on cheaper
instruments, or the same edge held longer.** GER40 is the first instrument where the arithmetic already
works. This pool cannot answer the "held longer" question at all — its entire window is two hours, which
is 1/160th of what your armed sleeves hold. That is the next measurement, and it needs a different
dataset, not a better statistic.

---

## Appendix — where to check anything here yourself

All paths relative to `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`.

| Claim | File |
|---|---|
| The repaired contract, per symbol and pooled | `E_ATMKT_PERSYMBOL_V1.json`, `E_ATMKT_POOLED_V1.json`, `E_ATMKT_BOOTSTRAP_V1.json` |
| The five-step ledger | `E_FINAL_V1.json` |
| Born state / stop-already-broken | `W0CAP2_NOLOOKAHEAD_FULL_V1.json` |
| The CQ factory candidate | `W0CAP2_CQ_NOLOOKAHEAD_V1.json` |
| Live engine order type (296/296) | `L10X_LIVE_BORNSTATE_V1.json` |
| Cost model per symbol, broker truth | `L10X_POOL_RECOST_V1.json`, `E1_ERATRUE_RECOST_V1.json` |
| Cost gate selects on its own error | `E1_SELECTION_ON_ERROR_V1.json` |
| Five-month replication | `E2_FIVE_MONTHS_V1.json` |
| Entry delay / cancel rule | `E6_CONFIRM_V1.json`, `E6_SWEEP_V1.json` |
| Trailing exit | `E5_TRAIL_V1.json`, `E_CONTRACT_SELECT_V1.json` |
| XAUUSD cell and its de-duplication | `E5_CELL_V1.json`, `E5_XAU_ROBUST_V1.json` |
| Fill-conditioning bias | `E_FILLCOND_V1.json` |
| Gates on live-placeable orders (new this session) | `OWNER_REPORT_GATE_CHECK_V1.json`, script `owner_report_gate_check.py` |
| Double-counting across levers | `E_STACK_MAIN_V1.json`, `e-stack_RESULT.md` |
| Field-by-field data dictionary | `w0_DATA_DICTIONARY.md` |

Each investigation lane also wrote a full receipt: `l1_RESULT.md` … `l12_RESULT.md`,
`e1_RESULT.md` … `e6_RESULT.md`, `e-stack_RESULT.md`, `e-coherence_RESULT.md`,
`w0-capture_RESULT.md`. Every number in this report appears in one of them with its script.
