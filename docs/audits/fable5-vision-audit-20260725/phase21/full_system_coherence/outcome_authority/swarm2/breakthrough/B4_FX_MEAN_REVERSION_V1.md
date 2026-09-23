# B4 — FX / cross-sectional mean reversion: build, and the two measurements that closed it

**Lane 4 of the breakthrough program. Build lane.** Commissioned to turn the swarm's twin
mean-reversion leads — Lane 1's M15 variance-ratio block and Lane 5's cross-sectional FX reversal —
into a tradeable rule.

**Status: NO DEPLOYABLE RULE. Both leads are closed by measurement, each by a different mechanism,
and each measurement states exactly what would reverse it.** A third effect was found in the process,
survives every artifact test, and is killed by the estate's own measured execution cost rather than by
statistics.

Nothing in this lane touched `src/`, `config/`, a broker, or the VPS. No commit.
Code: `swarm2/breakthrough/b4_fx_reversion/`. Receipts: `.../receipts/`.

---

## 0. THE ANSWER, IN SIX SENTENCES

1. **Lane 1's M15 late-session variance-ratio block is real and is 3–23× too small to trade.**
   The reversion exists at *every* hour of the day on 12 years × 12 FX pairs (154,000 observations per
   hour, |t| to 12.7), and the recoverable one-way amplitude is 0.16–0.61 bp against a round-trip
   spread of 1.03–14.97 bp. The best hour on the whole surface reaches an amplitude-to-cost ratio of
   **0.38**. Nothing in the day clears 1.0.

2. **Lane 1's Roll bound was computed against the wrong denominator, and at the right one the bound is
   satisfied.** The reversion is concentrated at broker hour 00 — the rollover, the swap charge, the
   D1 bar boundary — where the tick-measured close spread is **7.48 bp median / 12.86 bp p90** against
   the 0.55–0.68 bp that prevails everywhere else. Lane 1 compared the Roll-implied spread against the
   *median of a seven-hour UTC session* (0.95 bp) and got 3.02×. Against the spread in the hour that
   actually carries the reversion it is **0.495× — inside the bounce bound.**

3. **Lane 5's 1-day cross-sectional FX reversal is an anchor artifact, and the decomposition is
   unambiguous.** Splitting the forward return into the leg that shares the signal's own close price
   and the leg that shares nothing: **overnight (shares `C[t]`) +0.0548 σ, t = +13.11; intraday
   (shares nothing) −0.0118 σ, t = −0.57.** More than 100 % of the effect lives in the contaminated
   leg. Every tradeable anchor flips the sign.

4. **Currency-factor neutralisation — the residual threat Lane 5 named and could not eliminate — is
   not the problem, and it makes the artifact *sharper*.** On the contaminated anchor it lifts
   t from +2.06 to **+3.38**; on the clean anchor it leaves +0.73 and −0.37. The overlap-restatement
   hypothesis is refuted; the anchor was the whole story.

5. **The one construction that survives every artifact test is crypto, not FX** — 1-day
   cross-sectional reversal on the 24-coin archive, with the effect in the *clean* leg
   (intraday +0.0448 σ, t = +2.77) and gross **+51.5 bp/day, SR 1.77, 8/9 positive years.** It is
   killed twice over by things that are not statistics: **survivor bias** (restricted to coins that
   plausibly existed throughout, both legs collapse to t = 0.91 / 0.61) and **execution cost** (at
   FTMO's own measured spread and commission, net **−7.16 bp/day full sample, −44.60 bp/day on
   2023–2026, 0/4 positive years**).

6. **The surviving crypto signal is causally clean and it does not help.** Under the house lookahead
   standard it passes both decisive tests — the vol normaliser stripped of the scored return leaves
   t +4.69 against +4.75, and a past/future split of the signal puts the predictive content in the
   hours **furthest** from the entry (16 h before the cut: t +5.31; the final 6 h: **t +0.68**), which
   is the opposite of a leak and the opposite of anchor contamination (§5.2). **I killed my own best
   positive with the estate's own artifact instead.** `BROKER_TRUE_COSTS_V1.json`
   measures FTMO crypto commission at **6.52 bp of notional round turn per leg**, charged both sides.
   Two legs = 13.03 bp/day. The 2023–2026 gross is **+13.14 bp/day**. **Commission alone, before one
   bp of spread, consumes the entire recent edge.**

---

## 1. WHAT WAS MEASURED, AND ON WHAT

| asset | path | what I used it for |
|---|---|---|
| D1 bars, **163 symbols**, 2014-01-01 → 2026-06-17, 329,092 rows | `…/mt5_research_exports/deep_universe_h4d1_2014_2026/` | the cross-sectional panel |
| M15 bars, 167 symbols | `…/deep_universe_m15_2014_2026/` | the 12-year hourly reversion surface |
| Tick quotes, 263.9 M rows, 2026-06-18 → 07-26 | `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/` | spread by **broker hour**, and bid/mid/time-weighted-mid bar rebuilds |
| `SPREAD_MODEL_V1.json` | `research/operations/spread_model_2026_07_29/` | spreads for the 5 crypto the tick archive lacks |
| `BROKER_TRUE_COSTS_V1.json` | `research/operations/broker_truth_layer_2026_07_27/` | **measured** commission, per symbol, round turn |
| `R1_ESTATE_ROWS_V2.json.gz` | `…/phase20/forward/receipts/` | armed-sleeve daily R, for correlation |

Class composition of the panel: 70 equity, 43 FX, 24 crypto, 15 index, 8 metal, 3 energy. Lane 5's
166 is 163 here — three symbols carry < 200 D1 rows and were dropped.

### 1.1 The clock, because it is the whole finding

The archive's `time` column is **broker wall clock**, not UTC (defect F7; the manifest's own
`AAPL_M15.first = "2014-01-02 16:30:00"` against a 09:30 New York cash open confirms broker = NY + 7).
Broker midnight is the FX rollover, the swap charge, and the D1 bar boundary simultaneously. In UTC
that instant is **21:00 while New York is on EDT and 22:00 while on EST** — so Lane 1's
17:00–24:00 **UTC** session filter contains the rollover, smeared across two buckets by the DST
calendar, and cannot isolate it. Every measurement below is in broker hours, where it is one bucket.

`panel.py` reimplements `src/utils/broker_clock.py`'s US-DST rule on vectors (the shipped helper is
scalar-per-call and this lane converts ~10⁷ stamps); the rule is identical.

---

## 2. (LEAD 1) THE M15 VARIANCE-RATIO BLOCK

### 2.1 Replication, and two method defects in the original

`vr.py`, receipt `receipts/S1_VR_METHOD_AB.csv`. Lane 1's cell reproduces on a different data source
(the deep archive rather than `vps-bars-20260727`): CHFJPY VR(16) **0.584** against their 0.561,
EURGBP **0.676** against 0.631.

Two things in `lane1_receipts/vr2.py` move the number, and only one of them matters:

| defect | effect |
|---|---|
| `d = d[np.isfinite(d.lr) & (d.lr != 0)]` — flat bars dropped. A stale quote printing (+x, 0, −x) becomes (+x, −x), which *manufactures* lag-1 negative autocorrelation. | **Negligible.** VR moves ≤ 0.010 (CHFJPY 0.662 → 0.659). Refuted as a mechanism. |
| the session-filtered return series is spliced across day boundaries, so a q = 16 partial sum can straddle a 17-hour hole. | **Material.** On contiguous within-day blocks CHFJPY goes 0.584 → **0.662** and EURGBP 0.676 → **0.708**; AUDUSD, USDCAD and EURUSD cross from 0.85–0.89 to **above 1.0**. About a third of the ranked cell is the splice. |

What survives the repair is narrower than published: the JPY crosses plus EURGBP (VR 0.66–0.83,
z −2.9 to −4.9). The dollar majors do not survive.

### 2.2 The statistic that decides tradeability, which a variance ratio is not

VR(q) < 1 is a variance decomposition. It says the *unconditional* variance of a q-bar sum is smaller
than q times the one-bar variance; it does not say a q-bar move predicts the next q-bar move. The
tradeable quantity is the regression

> `r_fwd(k) = a + b · r_trail(k)`, with `g` bars of daylight between the windows,
> non-overlapping (step `k`), formed strictly inside one broker day.

`receipts/S1_GAPPED_BETA.csv`. Pooled over the 12 pairs in Lane 1's own late cell:

| cell | k | gap | β | mean t | recoverable amplitude |
|---|---:|---:|---:|---:|---:|
| late (UTC 17–24) | 4 | 0 | −0.0018 | −0.22 | 0.20 bp |
| late | 4 | 1 | −0.0038 | −0.48 | 0.17 bp |
| late | 8 | 0 | −0.0108 | −0.38 | 0.68 bp |
| late, rollover removed | 4 | 0 | −0.0005 | +0.08 | 0.34 bp |
| late, rollover removed | 8 | 0 | −0.0006 | −0.04 | 0.35 bp |

**The 4-hour horizon Lane 1 nominated carries 0.17–0.68 bp of linearly predictable amplitude against
a ≥ 1 bp round trip, with no t-statistic clearing 1 in absolute value.** Lane 1's "≈ 12 bp of
reverting amplitude over 4 hours … a ~13:1 amplitude-to-cost ratio" is a correct inference *about the
variance* and does not survive translation into a predictable component. Almost all of the VR
shortfall is the lag-1 term: with ρ₁ = −0.09 alone, VR(16) ≈ 1 + 2·(15/16)·(−0.09) = 0.83. The
reversion is **one bar deep**, which is exactly where microstructure lives.

### 2.3 The artifact, measured three ways

**(i) Bid vs mid vs time-weighted mid, rebuilt from ticks** (`bidmid.py`, `receipts/S2_BID_VS_MID_AC1.csv`).
The archive's OHLC is bid-based. If symmetric spread widening drove the reversion, a mid-based bar
would not carry it.

It does — bid −0.042 / mid −0.076 on CHFJPY late, bid −0.195 / mid −0.171 on EURGBP. **So simple
"wider spread depresses the bid" is refuted, and I say so.** The time-weighted mid tells the rest:
its lag-1 autocorrelation is **+0.13 to +0.32**, mean ≈ +0.20, against the **+0.25 that Working (1960)
gives for a pure random walk observed through a time average.** The least-contaminated price estimate
available on this machine behaves as a martingale with no reversion at all. What reverts is the
*last print*, not the price.

**(ii) The rollover, isolated** (`hourctl.py`, `receipts/S2b_HOURLY_BIDMID_ROLL.csv`).
Mean over 12 FX pairs, by broker hour:

| broker hour | ac1 (bid) | ac1 (mid) | ac1 (tw-mid) | close spread med | close spread p90 | Roll-implied | **Roll ÷ actual** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **00 (rollover)** | **−0.306** | **−0.347** | −0.100 | **7.48 bp** | **12.86 bp** | 3.22 bp | **0.495** |
| 01 | −0.109 | −0.096 | +0.108 | 0.68 | 0.88 | 1.77 | 3.65 |
| 12 | −0.217 | −0.214 | +0.160 | 0.56 | 0.76 | 3.03 | 8.75 |
| 23 | −0.030 | −0.026 | +0.149 | 1.26 | 1.61 | 0.59 | 0.50 |

EURUSD's own spread profile is the cleanest single exhibit: **3.06 bp at broker hour 00, 0.09 bp at
every other hour — 34×.** Crypto shows no such profile (BTCUSD is 0.16 bp flat across all 24 hours),
which is why the rollover is an FX-only artifact.

> **This is the correction to Lane 1 §3.2.** Roll (1984) bounds the bounce-implied spread. Lane 1
> divided it by the *median of the seven-hour UTC late session* and got 3.02×, concluding the
> reversion exceeds the bounce bound by 3× in spread and 9× in variance. Divided by the spread in the
> hour that carries the reversion it is **0.495× — the bound holds.** The denominator was wrong by
> roughly 8×.

**(iii) The 12-year, all-hours surface** (`m15rev.py`, `receipts/S4_M15_HOURLY_REVERSION_12Y.csv`).
This is the measurement that closes the lead, because it does not rely on the 38-day tick window.
12 FX pairs × 24 broker hours × 2014–2026, ~154,000 observations per hour. A direct backtest — fade
the last M15 bar, hold one bar, pay the tape-true spread for that broker hour twice:

| | best | worst | Lane 1's cell (bh 00) |
|---|---:|---:|---:|
| ac1 | −0.057 (bh 22) | −0.000 (bh 13) | −0.128 |
| |t| | 12.67 | 0.05 | 12.67 |
| amplitude | 0.49 bp (bh 02) | 0.02 bp | 0.61 bp |
| round-trip spread | 1.03 bp | 14.97 bp | 14.97 bp |
| **net bp/trade** | **−0.91** | **−14.58** | **−14.58** |
| **amplitude ÷ cost** | **0.38** | 0.004 | **0.043** |

**Every hour of the day is net-negative. The best hour on the entire surface needs a 2.63× improvement
in amplitude-to-cost to break even.** The effect is highly significant and economically absent — which
is the honest shape of a real microstructure regularity inside a dealer's spread.

The 38-day tick sample had nominated broker hours 12 and 15 (ac1 −0.217, −0.192; ratios 8.75, 20.2)
as a *cash-session* cell more promising than Lane 1's late one. **It does not replicate**: on 12 years
those hours are −0.048 and −0.029. With 108 pairs per symbol-hour the tick-window standard error on
ac1 is ≈ 0.10, so those were noise, and I am reporting them as refuted rather than quietly dropping
them.

**Decay:** mild and not the binding issue. Mean ac1 −0.040 (2014) → −0.018 (2024) → −0.032 (2026);
mean gross 0.113 → 0.054 → 0.067 bp. It halved and remained 3–23× below cost throughout.

**Per-symbol residue, stated because it is the closest thing to a survivor.** Eight of the 288
symbol × hour cells clear an amplitude-to-cost ratio of 1, and two are net-positive on spread alone:
**EURUSD at broker hour 14 (+0.055 bp/trade, n = 12,920)** and **EURUSD at broker hour 08
(+0.019 bp, n = 12,912)**. Both die on the estate's own measured commission: FTMO charges EURUSD
**0.438 bp of notional round turn** (`BROKER_TRUE_COSTS_V1.json`, `coverage: MEASURED`), which is
**8× the larger of the two**. They are also the best 2 of 288 cells. Not a candidate.

### 2.4 What would reverse this finding

Any one of: (a) an amplitude-to-cost ratio above 1.0 at some hour on a sample longer than the 38-day
tick window — the measured best is 0.38, so the requirement is a **2.63× improvement**; (b) a venue
quoting FX at ≤ 0.38× FTMO's spread with commission below ~0.05 bp round turn; (c) a *conditional*
selection (a state variable that picks the subset of bars where |ac1| is several times the
unconditional value) — untested here, and the only version of this lead I would fund further, because
the unconditional effect is significant enough (|t| 12.7) that a 3× conditional concentration is not
absurd. I did not test it and I am not claiming it exists.

---

## 3. (LEAD 2) THE CROSS-SECTIONAL 1-DAY REVERSAL

### 3.1 The anchor, stated before any result

For a bid-based close `C_t` carrying an idiosyncratic quote shock `e_t` (a wider spread at the print
instant depresses the bid), the trailing return `r_t = log C_t − log C_{t−1}` is biased **down** by
`e_t` and the forward return `r_{t+1} = log C_{t+1} − log C_t` is biased **up** by the same `e_t`.
The induced correlation on the shock component is −1. A close-to-close signal traded against a
close-to-close forward manufactures reversal — in the time series and cross-sectionally alike,
cross-sectionally because `var(e)` differs across symbols and days, so the ranking loads on it.

**And `e_t` is not hypothetical here:** the D1 close of this archive is the last print before the
broker-midnight rollover, i.e. the 7.48 bp instant of §2.3, in a book whose median is 0.55 bp.

Four anchors, run side by side (`xs.py`, `run_anchor.py`, `receipts/S3_ANCHOR_GRID.json`):

| | signal | forward | shares a price? | tradeable? |
|---|---|---|---|---|
| **A0** | `C[t−1]→C[t]` | `C[t]→C[t+1]` | **yes, `C[t]`** | — (= Lane 5's pilot) |
| **A1** | `C[t−1]→C[t]` | `C[t+1]→C[t+2]` | no | at t+1 |
| **A2** | `C[t−1]→C[t]` | `O[t+1]→C[t+1]` | no | **yes — intraday** |
| **A3** | `C[t−1]→C[t]` | `O[t+1]→O[t+2]` | no | **yes — one full day** |

Sign convention: positive = the reversal portfolio (long losers, short winners) pays.

### 3.2 The result

Mean, in σ-units per rebalance (t below):

| universe | A0 (contaminated) | A1 (gapped) | **A2 (clean, tradeable)** | **A3 (clean, tradeable)** |
|---|---:|---:|---:|---:|
| **FX** (40) | **+0.0430** (+2.06) | +0.0354 (+1.55) | **−0.0118 (−0.57)** | **−0.0073 (−0.35)** |
| FX, currency-neutral | +0.0432 (**+3.38**) | — | +0.0049 (+0.73) | −0.0053 (−0.37) |
| NOCRYPTO (59) | +0.0329 (+1.89) | +0.0115 (+0.61) | +0.0025 (+0.15) | +0.0011 (+0.07) |
| ALL (57) | +0.0363 (+2.46) | +0.0097 (+0.60) | +0.0106 (+0.75) | +0.0084 (+0.58) |
| EQUITY (60) | +0.0261 (+1.41) | +0.0083 (+0.49) | +0.0124 (+0.77) | +0.0068 (+0.37) |
| **CRYPTO (22)** | +0.0498 (+3.06) | −0.0236 (−1.55) | **+0.0449 (+2.77)** | **+0.0443 (+2.71)** |

A0|FX reproduces Lane 5's pilot (their −0.0416, t −1.98, opposite sign convention; mine +0.0430,
t +2.06, n = 3,110 — the small gap is my own-observation-sequence and 60-day vol window).

**Then the decomposition that settles it** (`build2.py`, `receipts/S5_DECOMP_AND_CRYPTO.json`).
A0 = overnight(`C[t]→O[t+1]`) + intraday(`O[t+1]→C[t+1]`). Only the overnight leg touches `C[t]`:

| universe | overnight leg (shares `C[t]`) | intraday leg (shares nothing) | full A0 |
|---|---:|---:|---:|
| **FX** | **+0.0548, t = +13.11** | **−0.0118, t = −0.57** | +0.0430, t = +2.06 |
| NOCRYPTO | +0.0303, t = +6.67 | +0.0025, t = +0.15 | +0.0329, t = +1.89 |
| ALL | +0.0257, t = +6.91 | +0.0107, t = +0.76 | +0.0364, t = +2.47 |
| **CRYPTO** | +0.0049, t = +1.92 | **+0.0448, t = +2.77** | +0.0497, t = +3.05 |

> **In FX, more than 100 % of the cross-sectional reversal lives in the one leg that shares the
> signal's own anchor price, at t = +13.11, while the leg that shares nothing is −0.0118 at
> t = −0.57. That is an anchor artifact, not an alpha.** In crypto the pattern is exactly inverted:
> the effect is in the clean leg. The same test separates the two cleanly, which is why I trust it.

**Lane 5's own unfixed residual is refuted as the explanation.** It named the currency-overlap
restatement (ranking EURUSD/EURGBP/EURJPY produces a EUR basket) as "the residual threat I could not
eliminate", with "the fix is a currency-factor decomposition, not more data." I built the
decomposition — each pair XXXYYY loads +1 on XXX and −1 on YYY, project the signal off that span
(`xs.py::_currency_neutralise`). On the contaminated anchor it **raises** t from +2.06 to +3.38
(it strips the common-factor noise and leaves the idiosyncratic close-price shock, which *is* the
artifact); on the clean anchors it leaves +0.73 and −0.37. The overlap was never the problem.

**Constructive variants on the clean anchor, all negative or null** (`receipts/S5_CONSTRUCTIVE_GRID.json`),
lookback ∈ {1,2,3,5,10} × quantile ∈ {5,3}: FX best is lookback 10 at t = +0.60 (BE +1.25 bps/leg
against a measured 0.10–1.19 bp FX spread plus 0.38–0.72 bp commission — under water); every other
FX cell is negative. Lane 5's `XS_REV_5D|ALL` cell (their +7.2 BE) is A0-anchored and inherits the
same defect.

---

## 4. THE THING THAT SURVIVED THE ARTIFACT TESTS, AND WHAT KILLED IT

Crypto XS 1-day reversal, A2 anchor (rank on yesterday's close-to-close; enter at today's
broker-00:00 open, exit at today's close). **Intraday by construction, so it pays no swap** — which
matters, because FTMO charges crypto swap on both sides (`swap_mode: 5`,
`swap_long = swap_short = −30.0` at `config/profiles/operator_profile.yaml`), so the
open-to-open variant A3 is dead on carry before any spread is charged.

Gross, zero cost, 2,786 book-days: **+51.54 bp/day, t = +5.78, SR 1.77, 8/9 positive years.**

### 4.1 Kill 1 — survivor bias

Lane 5 §1.2 disclosed the archive is a **100 % survivor-selected universe** (FTMO's *current* symbol
list; every one of the 166 symbols has a last bar in 2026-06, zero end early), and named crypto as the
worst-affected class. Reversal **buys the losers**, which is precisely the population a point-in-time
list would have dropped, so the bias is adverse and it is largest exactly where the strategy takes
risk.

Restricting to the coins that plausibly existed throughout (BCH, BTC, ETC, ETH, LTC, NEO, XLM, XMR,
XRP), both legs collapse:

| universe | anchor | long-losers leg | short-winners leg |
|---|---|---:|---:|
| all 24 coins | A2 | +0.0355, **t = +4.13** | +0.0393, **t = +3.75** |
| survivor-safe 9 | A2 | +0.0087, t = +0.91 | +0.0084, t = +0.61 |

**~76 % of the effect, on both legs, sits in the 15 newer/smaller alts.** That is not proof of bias —
those coins are also genuinely less efficient — but it is the same 15 coins carrying both the alpha
and the entire selection exposure, and no survivorship-free crypto list exists on this machine.

### 4.2 Kill 2 — the estate's own measured execution cost

`rule.py` charges each *selected leg* its own spread, twice, every day (A2 exits every leg at every
close, so name-turnover is irrelevant and the correct denominator is 2, not Lane 5's `2 × turnover` —
that convention alone moves the published breakeven from 12.24 to **9.89** bps/leg).

Spreads, tick-measured where the archive has the symbol, `SPREAD_MODEL_V1` otherwise:

| BTCUSD | ETHUSD | DOTUSD | ADAUSD | XTZUSD | LTCUSD | XRPUSD | AVAUSD | 16 alts |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.16 | 3.49 | 5.02 | 6.52 | 16.78 | 19.71 | 28.65 | **32.89** | unpriced |

Commission, **measured** by the estate (`BROKER_TRUE_COSTS_V1.json`, `coverage: MEASURED`,
`commission_charge_side: both_sides`): BTCUSD **6.516**, ETHUSD **6.473**, AVAUSD **6.757** bp of
notional round turn. Median **6.52 bp per leg → 13.03 bp/day for a two-leg book.**

| cost regime | window | gross | cost | **net bp/day** | t | pos. years |
|---|---|---:|---:|---:|---:|---:|
| zero cost (reference) | full | +51.76 | 0.00 | +51.76 | +5.78 | 8/9 |
| zero cost | 2023–2026 | +13.14 | 0.00 | +13.14 | +1.89 | 3/4 |
| **commission only** | 2023–2026 | +13.14 | 6.52 | **+6.62** | **+0.95** | 3/4 |
| spread only (alts @ 32.9) | full | +51.76 | 52.40 | −0.64 | −0.07 | 3/9 |
| spread only | 2023–2026 | +13.14 | 51.23 | −38.09 | −5.49 | 0/4 |
| **spread + commission** | **full** | +51.76 | 58.92 | **−7.16** | −0.80 | 3/9 |
| **spread + commission** | **2023–2026** | +13.14 | 57.74 | **−44.60** | **−6.43** | **0/4** |

**No cost-feasible sub-universe exists** (`final.py`, `receipts/S7_FRONTIER_AND_CORRELATION.json`).
Restricting to the cheap coins removes the alpha along with the cost, because the alpha *is* in the
expensive names:

| universe | mean leg spread | gross bp/day (full) | net bp/day (full) | net bp/day (2023–2026) |
|---|---:|---:|---:|---:|
| BTC + ETH | 1.83 | −9.59 | −13.25 | −6.03 |
| 4 coins ≤ 7 bp | 3.80 | −11.61 | −17.17 | −9.62 |
| 6 coins ≤ 20 bp | 8.61 | +0.18 | −17.76 | −7.82 |
| 8 cost-known | 14.15 | −8.39 | −36.39 | −19.64 |

The cheapest cells are **negative gross** — the liquid majors show daily *momentum*, not reversal.

### 4.3 Decay

The effect is dying, fast, independently of cost. Zero-cost gross by year:
**2018 +104.6 · 2019 +31.6 · 2020 +137.2 · 2021 +144.6 · 2022 +2.5 · 2023 +11.4 · 2024 +18.1 ·
2025 +24.0 · 2026 −17.8** bp/day. Split at the walk-forward boundary:
**train 2019–2022 +78.46 bp/day (t +4.66, SR 2.09); test 2023–2026 +13.14 (t +1.89, SR 0.85)** — a
**6.0× decay**, and the test window is not significant at zero cost.

### 4.4 What would reverse it

Stated as a requirement rather than a hope. The book breaks even at an **average weighted leg spread
of 25.88 bp on the full sample and 6.57 bp on 2023–2026, with commission at zero**. With FTMO's
measured 6.52 bp/leg commission the 2023–2026 spread budget is **0.05 bp** — arithmetically
unreachable. Reversal therefore needs a venue with (a) alt-coin spreads at or below ~5 bp **and**
(b) commission below ~1 bp round turn, on ~20 coins including the small ones. A retail crypto
exchange plausibly clears both; a prop-firm CFD book does not, and prop-firm CFDs are the only
instrument GTOS can trade. **That is an instrument constraint, not a research one, and it is why I
am not proposing further work on this line inside the estate.**

---

## 5. PRICED AS A BOOK — what was on the table

Nothing is deployable, so nothing is proposed. The scale is worth recording because it bounds how much
was ever at stake, and it does so at the **zero-cost** reference, i.e. the most generous possible read.

At a 0.5 %/day book-volatility budget (comparable to the armed book's risk):

| | full sample | 2023–2026 |
|---|---:|---:|
| mean | +0.0557 %/day | +0.0267 %/day |
| **%/month** | **+1.17 %** | **+0.56 %** |
| daily σ of the raw stream | 462 bp | 246 bp |
| SR (annualised) | +1.77 | +0.85 |
| **max drawdown at that budget** | **9.09 %** | **12.34 %** |
| book-days/month | ~21 (daily by construction) | ~21 |

Two observations kill the arming case even in this fantasy costing. First, **+0.56 %/month gross on
the recent regime is under a third of the ~2 %/month the armed three-sleeve book is restated at**, for
a strategy needing 16–20 simultaneous CFD legs against `risk.max_concurrent` in both profiles.
Second, **the 2023–2026 max drawdown of 12.34 % breaches FTMO's 10 % overall-loss limit on its own,
at zero cost, before the strategy loses a single bp to execution.** It is not a prop-account
strategy at any size that makes the return interesting.

`p_pass` is therefore unchanged and no simulation was run: `scripts/mc_firm_rules.py::mc` prices
candidate books, and a book whose own zero-cost drawdown exceeds the firm's static floor has no
admissible risk unit to price.

### 5.1 Correlation to the armed book

`receipts/S7_FRONTIER_AND_CORRELATION.json`. Crypto XS zero-cost daily stream against per-day mean
gross R for each armed sleeve (`R1_ESTATE_ROWS_V2.json.gz`, `r_old`), intersected on entry date:

| | full | 2023–2026 |
|---|---:|---:|
| `crypto` | −0.108 (n 119) | −0.029 (n 73) |
| `energy_agri` | −0.091 (n 39) | +0.025 (n 23) |
| `sub_mid_dn_revert` | +0.005 (n 179) | +0.158 (n 83) |
| `sub_xvol_pullback` | +0.149 (n 26) | — |
| **armed book (mean of 4)** | **−0.001 (n 348)** | **+0.060 (n 185)** |

**It is genuinely uncorrelated** — ρ = −0.001 against the armed book on 348 overlapping days. That is
the one property the mandate prizes and the one this candidate had. It is not enough: an uncorrelated
stream with a negative mean is a negative mean.

Two caveats on those numbers. The overlap is thin because the armed sleeves trade rarely
(`energy_agri` 39 days, `sub_xvol_pullback` 38 days in the whole archive against 2,786 XS book-days),
so only the `sub_mid_dn_revert` and pooled rows carry usable precision. And `r_old` is **gross**;
`src/safety/armed_set.py` records that the quote-side repair moves `sub_mid_dn_revert` by −59.6 %, and
it is 394 of the 604 armed trade-days — a net-R correlation could differ.

> **One correction to the commission that framed this lane.** The brief says "Nobody has ever built a
> mean-reversion rule here." One of the four armed sleeves is `sub_mid_dn_revert` — a
> mid-band down-reversion sleeve, live on both accounts. The accurate statement is that nobody has
> built a **cross-sectional or market-neutral** reversion rule here, which remains true.

---

## 5.2 TEMPORAL-LEAKAGE AUDIT — to the house standard

Run after the sibling lane's lookahead kill (a regime feature aggregated over candidates generated
*after* the scored trade, which survived walk-forward, strictly prior training, daily refit and four
permutation nulls). Mean-reversion is the family most exposed to that defect, so this is proved rather
than asserted. `leak.py`, receipt `receipts/S9_LEAKAGE_AUDIT.json`.

**Construction audit first, by inspection:**

| element | content | available at the decision instant? |
|---|---|---|
| signal | `r_cc[t] = log C[t] − log C[prev]` | yes — day-t close |
| ranking | cross-section over symbols **at date t**, each using only its own `r_cc[t]` | yes — no aggregation over any later observation |
| normaliser | `rolling(60).std()` **ending at** t | yes — contains `r_cc[t]`, which is itself known at t |
| forward | `O[t+1] → C[t+1]` | strictly after entry |

There is no within-day aggregate anywhere in this rule and no fitted parameter, so the sibling lane's
exact defect is structurally absent. What follows tests the two things that could still be wrong.

**L1 — lag test** (rank on `r_cc[t−1]`, forward unchanged):

| | baseline `r_cc[t]` | lagged `r_cc[t−1]` |
|---|---:|---:|
| full sample | +0.0751, **t +4.75**, 8/9 yrs | −0.0206, t −1.37, 2/9 yrs |
| 2023–2026 | +0.0204, t +1.14 | −0.0285, t −1.70, 0/4 yrs |

> **This test is not diagnostic for this signal, and I am not claiming it as a pass.** The sibling
> lane's feature was a *persistent regime state*, so a one-day lag should have left it nearly intact
> and its collapse was decisive. A **one-day reversal** signal lagged one day is by definition a
> two-day-old signal — which is exactly my A1 anchor, independently measured at −0.0236, t −1.55
> (§3.2). The two agree, so the collapse is the horizon of the effect, not evidence either way about
> leakage. Reported because it was asked for and because reporting only the favourable reading of a
> test is the failure mode this standard exists to prevent.

**L2 — normaliser purity** (`VOL[t]` contains the scored return; `VOL[t−1]` cannot):

| | `VOL[t]` | `VOL[t−1]`, pure |
|---|---:|---:|
| full sample | +0.0751, t +4.75 | +0.0783, **t +4.69** |
| 2023–2026 | +0.0204, t +1.14 | +0.0283, **t +1.52** |

**Clean pass.** The result is unchanged — marginally *better* — when the normaliser is stripped of any
contact with the return being ranked. The signal is not a volatility-ratio artifact.

**L3 — past/future split of the signal itself.** This is the direct analogue of the sibling lane's
decisive test. The D1 signal spans 24 hours; cut broker day *t* at hour H, rank on the two halves
**separately** (they sum exactly to `r_cc[t]`), with an identical forward and identical eligible set.
Built from M15 prices — 24 of 24 crypto symbols are present in the M15 archive.

| cut | EARLY half (prev close → H) | LATE half (H → close) | full-day control |
|---|---|---|---|
| **08:00** | 8 h: +0.0165, t **+1.09** | 16 h: +0.0826, t **+5.31** | +0.0751, t +4.75 |
| **12:00** | 12 h: +0.0428, t **+2.84** | 12 h: +0.0692, t **+4.61** | +0.0751, t +4.75 |
| **18:00** | 18 h: +0.0818, t **+5.14** | **6 h: +0.0120, t +0.68** | +0.0751, t +4.75 |

**Pass, and informatively so.** Predictive content scales with the **length** of the window, not with
its **proximity to the entry**. Per hour of window: the 6 hours immediately before the close (broker
18:00–24:00 = UTC 15:00–21:00) are the *weakest* part of the whole signal (t +0.68), while the 16
hours furthest from it carry t +5.31. At the symmetric cut both halves are significant.

That is the opposite of both failure modes at once. A leak, or contamination near the anchor, puts the
content in the half **nearest** the entry; here that half contributes least. It is an independent
corroboration of the §3.2 leg decomposition, which found the crypto effect in the leg that shares no
price with the signal — two different tests, same conclusion, and the same pair of tests separates
crypto from FX in the same direction both times.

*(Implementation note: `leak.py`'s baseline reads +0.0751 / t +4.75 where `build2.py`'s reads
+0.0591 / t +3.76 on the same 2,786 days. The only difference is the quantile floor in thin early
years — `max(3, n//5)` in `xs.py::cell` against `max(1, min(n//2, n//5))` in `leak.py`. Every L1/L2/L3
comparison above runs through one code path, so the contrasts are internally consistent; the headline
economics in §4 use the `xs.py` convention throughout.)*

**None of this rescues the rule.** It establishes that the crypto cell's +51.5 bp/day gross is a real,
leakage-free, artifact-free measurement — and §4 already showed that measurement is consumed by
survivor bias and then, twice over, by FTMO's measured spread and commission. A causally clean signal
that cannot pay its own execution is still not a strategy.

**On the sibling lane's direction measurement.** Day-to-day direction anti-persistence (trailing-2
ρ −0.389) is consistent with everything here and is causally clean, and its stated ceiling — a
*perfect* same-day direction call worth +0.0753 R/trade — is the same shape as this lane's result:
the reversion is real and small. Both lanes land on the same constraint, that value has to come from
cells where reversion is strong **and** cost is low. §4.2 measures that the crypto cell has the first
and not the second, and §2.3 measures that the FX cells have neither.

---

## 6. MULTIPLICITY — declared in full

Every cell inspected in this lane, counted:

| stage | cells |
|---|---:|
| S1 VR method A/B (12 syms × 4 variants) | 48 |
| S1 hourly ac1/VR (12 × 24) | 288 |
| S1 gapped beta (12 × 3 horizons × 6 gap/cell combinations) | 216 |
| S2 bid/mid/tw-mid (12 × 4 cells × 3 series) | 144 |
| S2b hourly, 3 price series (12 × 24 × 3) | 864 |
| S3 anchor grid | 23 |
| S4 12-year hourly backtest (12 × 24) | 288 |
| S5 leg decomposition (4 × 3) + constructive grid (40) + crypto legs (8) | 60 |
| S6 costed cells | 9 |
| S7 frontier (8) + correlations (10) | 18 |
| S8 commission close | 8 |
| S9 leakage audit (lag 4, normaliser 4, past/future 9) | 17 |
| **total** | **1,983** |

**Not one of these was pre-registered, and none should be read as an admission-grade result.** Under
the estate's ratified rule (`CANDIDATE_BOOK_V1`, all-declared basis, sealed `B_balanced` α = 0.10 —
`phase8/receipts/CANDIDATE_FAMILY_V1.json`), a 1,966-look family sets the rank-1 BH bar at
p ≈ 5.0 × 10⁻⁵. The only cell that would clear it is the crypto XS zero-cost reference (t = +5.78),
and it is **not a candidate** because it is unexecutable — it is a reference arm with no cost, which
is not a strategy. Every executable cell in this lane is negative.

**No validation currency was spent.** The four never-funnel-read 2025 windows (june / august /
september / december 2025) were not touched. Nothing in this lane read the candidate cache, the sealed
replay evidence, or any prereg-governed artifact.

### 6.1 What a pre-registered read would look like, if the estate ever wanted one

I do not recommend commissioning it, and I state it so the option is priced rather than lost.

* **Hypothesis**: conditional M15 FX reversion — that a stated pre-trade state variable (quote-revision
  intensity, realised-vs-implied bar range, or spread-relative-to-its-own-hourly-median) selects a
  subset of bars on which the lag-1 reversion amplitude exceeds **2.63×** its unconditional value,
  which is the measured shortfall to breakeven at the best hour.
* **Instrument and horizon**: EURUSD and GBPUSD only (the two instruments whose measured spread plus
  commission leaves any headroom at all), broker hours 02, 08, 11, 14 (the four cells with
  amplitude-to-cost above 0.25 on 12 years), one-bar hold.
* **Bar**: BAR-2 class — pre-registered before the read, pooled net-of-full-four-component-cost
  positive with a bootstrap p05 above zero, and positive in each scored sub-window.
* **Window I would spend**: **none of the four 2025 reserves.** The training material is 2014–2022
  M15, which this lane has now read at hourly resolution and which is therefore burned as
  development data; the read window would be **2023-01-01 → 2026-06-17**, which is likewise now read
  (§2.3) and would have to be regenerated at true UTC. The honest position is that this lane has
  already consumed the cheap M15 FX evidence, and a clean read needs a **fresh capture** — FTMO
  serves ticks back to 2023-09 for 19 symbols (`MARKET_DATA_DEPTH_PROBE.json`), so it is a capture,
  not a read.
* **Cost of being wrong**: one capture plus one session. **Prior: low.** The unconditional effect is
  0.38× of cost at its best; a 2.63× conditional concentration is a large ask, and the estate has
  already refuted conditioning as a lever once (Session AH: member conditioning on the FX D1 cohort
  was a coin flip out of sample).

---

## 7. WHAT THIS LANE CHANGES IN THE RECORD

Four corrections, each measured, each with the receipt:

1. **`LANE_1_FAIR_VALUE_NULL_V1.md` §3.2's Roll bound is wrong by ~8× in the denominator.** The
   reversion does not exceed the bounce bound; at the spread prevailing in the hour that carries it,
   the ratio is **0.495**. `receipts/S2b_HOURLY_BIDMID_ROLL.csv`.
2. **§3.1's ranked cell is ~⅓ splice artifact.** On contiguous within-day blocks three of the twelve
   pairs cross above VR = 1. `receipts/S1_VR_METHOD_AB.csv`.
3. **§3's "≈ 12 bp of reverting amplitude … ~13:1 amplitude-to-cost" does not survive translation
   into a predictable component.** The gapped regression gives 0.17–0.68 bp with no |t| above 1, and
   the 12-year all-hours backtest is net-negative at every hour. `receipts/S1_GAPPED_BETA.csv`,
   `receipts/S4_M15_HOURLY_REVERSION_12Y.csv`.
4. **`LANE_5_UNEXPLORED_ALPHA_SPACE_V1.md` §2.1's surviving cell — `XS_REV_1D | FX-ONLY`, "survives
   every control I applied" — does not survive the anchor control.** 100 %+ of it is in the leg
   sharing the signal's own close price (t +13.11 vs −0.57), and the currency-factor decomposition it
   nominated as the fix makes the contaminated number *larger*, not smaller.
   `receipts/S5_DECOMP_AND_CRYPTO.json`.

And one addition: **the FX rollover contaminates any close-anchored daily signal built on this
archive.** The D1 bar boundary is the 7.48 bp instant in a 0.55 bp book (EURUSD: 3.06 bp against
0.09 bp, **34×**). Crypto is exempt (BTCUSD 0.16 bp flat across all 24 broker hours). Any future
cross-sectional or daily-reversal work on FX in this repository must use a non-close anchor or it
will rediscover this artifact — as two independent lanes did on the same day.

---

## 8. FILES

```
swarm2/breakthrough/b4_fx_reversion/
  panel.py     broker-clock-correct loaders; D1 panel (163 syms), M15, tick spreads
  vr.py        S1  Lane 1 replication + splice/zero-drop A/B + gapped reversion beta
  bidmid.py    S2  M15 bars rebuilt from ticks as bid / mid / time-weighted mid
  hourctl.py   S2b per-broker-hour ac1 x 3 price series + Roll bound at the right spread
  xs.py        cross-sectional engine; four anchors; currency-factor neutralisation
  run_anchor.py S3 the anchor grid
  m15rev.py    S4  12-year, 24-hour M15 reversion backtest at tape-true spreads
  build2.py    S5  leg decomposition; constructive grid; crypto survivor stress
  rule.py      S6  the rule, costed per leg
  final.py     S7  cost frontier + correlation to the armed four
  leak.py      S9  temporal-leakage audit: lag, normaliser purity, past/future split
  receipts/    S1_VR_METHOD_AB.csv, S1_VR_BY_BROKER_HOUR.csv, S1_GAPPED_BETA.csv,
               S2_BID_VS_MID_AC1.csv, S2b_HOURLY_BIDMID_ROLL.csv,
               S3_ANCHOR_GRID.json, S3_SERIES.json,
               S4_M15_HOURLY_REVERSION_12Y.csv, S4_M15_HOURLY_BY_YEAR.csv,
               S5_DECOMP_AND_CRYPTO.json, S5_CONSTRUCTIVE_GRID.json,
               S6_CRYPTO_RULE_COSTED.json, S6_CRYPTO_XS_DAILY_SERIES.csv,
               S7_FRONTIER_AND_CORRELATION.json, S8_COMMISSION_CLOSE.json,
               S9_LEAKAGE_AUDIT.json
```

Reproduce in order: `python3 vr.py && python3 bidmid.py && python3 hourctl.py &&
python3 run_anchor.py && python3 m15rev.py && python3 build2.py && python3 rule.py &&
python3 final.py && python3 leak.py`. Total ~45 minutes on this laptop. No network, no broker, no VPS.
