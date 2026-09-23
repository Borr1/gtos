# x3 — WHAT EARLINESS IS WORTH

Lane key `x3`. January 2026, true-UTC re-clocked S0R0 pool, 27,658 candidates, 24 symbols.
Everything below is measured on this machine from the generator's own M1 sources. No sealed
replay, no VPS, no broker-capable script, nothing committed.

---

## 0. HEADLINE

**Entering at the forming M15 bar's OPEN instead of its CLOSE moves the January at-market
pool from −0.06184 to +0.07904 R/trade gross: +0.14088 R/trade, CI95 [+0.11594, +0.16776],
P(≤0) = 0.000 on a 21-day-block bootstrap, n = 13,692 paired, and 24 of 24 instruments
improve.** In basis points of notional that is **−0.75 bps → +8.90 bps against a measured
2.67 bps toll**.

The optimum is **before the close, at the earliest instant measurable**. The curve is
monotone from k = −8 back to k = −15 with no interior maximum — the boundary is the M15
bar's own open, and the sweep is still climbing when it gets there.

**The prize is real and it is not free.** The direction is only known at the close, so the
early half of the curve is oracle-triggered. A bare partial-bar displacement trigger applied
to all 71,437 January M15 bars captures the entry price but not the selection: its confirmed
leg earns **+0.148 … +0.231 R/trade net of broker-true cost** while its phantom leg pays
**−0.24 … −0.41**, and the unconditional book lands at −0.138 … −0.175 R — better than the
−0.234 R baseline, still negative. **The exact target for an intra-bar separator is a
precision of 0.574–0.734 at minute 3–5; displacement alone reaches 0.282–0.437. The gap is
0.25–0.30 of precision.**

---

## 1. THE CURVE  (`X3_SWEEP_V1.json`, `x3_01_sweep.log`)

At-market cohort (`born_at_limit`, entry price == decision-instant market price), common
support (rows tradable at *every* offset, n = 13,692), POOL contract (target `policy_target_r`,
stop −1R, mark-to-market at T+120, conservative tie to the stop), risk distance and R units
held fixed, geometry re-anchored to the new entry.

```
gross R/trade vs entry offset k (minutes from the M15 close; k<0 is inside the forming bar)
 -15 +0.07904 |#########################*      <-- maximum, at the boundary
 -13 +0.07058 |######################*
 -10 +0.03487 |##########*
  -8 +0.00289 |*                               <-- crosses zero here
  -5 -0.03325 *###########|
  -1 -0.08261 *###########################|    <-- MINIMUM of the whole curve
  +0 -0.06184        *####################|    <-- THE SHIPPED CONTRACT
  +2 -0.00548                           *#|
  +5 -0.00504                           *#|    <-- the estate's "wait 5 minutes"
 +10 +0.00101                             *
 +30 -0.00905                          *##|
```

**This single curve unifies the two findings that looked contradictory.** "Delay 5 minutes is
worth +0.067" is the small right-hand hump: +0.05680 R here (CI95 [+0.04252, +0.06885],
P(≤0) = 0.000), against l7/l2's +0.0661 on a three-month population — the same lever,
reproduced independently. "Go early" is the left-hand climb, **2.48× larger**. Both are true
because the curve is a shallow V whose floor is at **k = −1**, one minute *before* the close:
the last minute of the forming bar is the single worst instant in the whole 46-minute window
to enter.

| | k = −15 | k = −1 | k = 0 (shipped) | k = +5 |
|---|---:|---:|---:|---:|
| gross R/trade | **+0.07904** | −0.08261 | −0.06184 | −0.00504 |
| gross bps | **+8.9042** | −0.2956 | −0.7531 | −0.3279 |
| win rate | 0.4484 | 0.3713 | 0.3750 | 0.3964 |
| target rate | 0.1986 | 0.1746 | 0.1835 | 0.1977 |
| **stop rate** | **0.4736** | 0.5158 | 0.5089 | 0.4830 |
| t (naive) | +7.66 | −8.34 | −6.17 | −0.50 |

**Adverse selection falls with earliness**: the stop rate drops 5.09 → 4.74 pp-points
(−3.53 pp) and the target rate rises +1.51 pp. Earliness is not buying a better price at the
cost of more stop-outs; it is buying both.

The TRAIL025 contract (no target, −1R stop, 0.25R trail, armed-at-i-checked-from-i+1) gives
the same shape with a larger amplitude: **−0.01161 at k = 0 → +0.22515 at k = −15**
(+0.23676 R/trade, t = 44.25). Both contracts, both signs, same story.

---

## 2. WHO GAINS, WHO IS DESTROYED  (`X3_PRIZE_V1.json`, `X3_CUTS_V1.json`)

Net of the **broker-true** toll (per-row, rd-aware: tick-archive median spread bps per symbol
+ commission/slippage from `L10X_POOL_RECOST_V1.json`; swap 0 at a 2 h horizon). This lane's
toll reproduces the estate's band: **0.2139 R over all rows vs L10X's 0.189297**, and
**2.6749 bps on the at-market cohort — inside the measured 2.5–3.9 bps**. The pool's own
frozen model charges 0.5522 R (2.42×) and is not used for any verdict here.

| family | n | net R @ k=−15 | net R @ k=0 | k\* | lift vs k=0 | CI95 | P(≤0) |
|---|---:|---:|---:|---:|---:|---|---:|
| **displacement_continuation** | 4,165 | **+0.5452** | −0.1877 | **−15** | **+0.7329** | [+0.7111,+0.7553] | 0.000 |
| **regime_transition_break** | 281 | **+0.4411** | −0.0385 | **−15** | **+0.4796** | [+0.4396,+0.5211] | 0.000 |
| **session_open_range_break** | 986 | **+0.2689** | −0.1631 | **−15** | **+0.4319** | [+0.3910,+0.4708] | 0.000 |
| **volatility_compression_expansion** | 509 | **+0.1456** | −0.1440 | **−15** | **+0.2896** | [+0.2663,+0.3127] | 0.000 |
| liquidity_sweep_reclaim | 4,093 | −0.3780 | −0.2580 | **−5** | +0.1153 | [+0.0805,+0.1505] | 0.000 |
| structural_distance_extreme | 1,765 | **−1.2685** | −0.5970 | **+5** | +0.2034 | [+0.1317,+0.2755] | 0.000 |
| cross_asset_lead_lag | 1,890 | −0.4409 | −0.3598 | **+15** | +0.1190 | [+0.0487,+0.1778] | 0.001 |
| ALL_AT_MARKET | 13,692 | −0.1379 | −0.2787 | −15 | +0.1409 | [+0.1154,+0.1679] | 0.000 |

**Four families want the bar's open. Two want to be later. One wants the middle.**
`structural_distance_extreme` is *destroyed* by earliness — it loses 0.67 R/trade more at the
open than at the close — and `liquidity_sweep_reclaim` has an interior optimum at k = −5,
which is exactly what a sweep-then-reclaim mechanism should do: the sweep has to happen first.

### The book that follows

The five families whose optimum is early (n = 10,034 of 13,692):

| k | net R/trade | net bps | total net R, January |
|---:|---:|---:|---:|
| **−15** | **+0.1183** | **+10.24** | **+1,186.7** |
| −13 | +0.0998 | +8.64 | +1,001.3 |
| −10 | +0.0481 | +6.24 | +482.3 |
| −8 | +0.0025 | +4.30 | +24.7 |
| −7 | −0.0201 | +3.25 | −201.6 |
| 0 | −0.2075 | −3.62 | −2,082.4 |
| +5 | −0.1717 | −3.26 | −1,722.5 |

Day-block bootstrap at k = −15: **+0.11827, CI95 [+0.08727, +0.15113], P(≤0) = 0.000, 27
days.** The two late families never reach positive at any offset (best −0.3466 at k = +15).

**The operational constraint is sharp: the net-positive window is k ≤ −8. You must fire
within the first 7 minutes of the bar or the prize is gone.**

### Instruments

**24 of 24 improve at k = −15 vs k = 0. Zero reversals.** Largest: BTCUSD +0.2862,
ETHUSD +0.2653, UK100 +0.2381, AUDJPY +0.2250. Smallest: USDJPY +0.0063, XAUUSD +0.0523,
GBPJPY +0.0535, US30_cash +0.0717. Per-symbol curves in `X3_CUTS_V1.json → by_symbol`.

---

## 3. THE MECHANISM — it is not a better price  (`X3_MECHANISM_V1.json`)

| k | mean market offset (R) | median | share with a better price than shipped |
|---:|---:|---:|---:|
| −15 | **+0.0950** | **−0.3044** | **0.6582** |
| −10 | +0.0609 | −0.2336 | 0.6697 |
| −5 | +0.0562 | −0.1044 | 0.6220 |
| +5 | −0.0722 | −0.0443 | 0.5509 |

Fifteen minutes earlier the **median** candidate could be entered **0.3044 R better** and
65.8 % of them could be entered better — but the **mean** price is 0.095 R *worse*. The
population is bimodal, and the barrier contract is what converts it into a gain: continuation
setups get a large head start and their winners run to +2R, fade setups get a worse price and
their losses are capped at −1R.

| forming bar moved | n | gross @ k=−15 | gross @ k=0 | net @ k=−15 |
|---|---:|---:|---:|---:|
| **with the trade** (continuation) | 9,024 | **+0.46784** | −0.06799 | **+0.13394** |
| against the trade (fade) | 4,668 | −0.67257 | −0.04993 | −1.54632 |

On the **delay** side the mechanism is the opposite and completely mundane: capture efficiency
(Δ gross R per R of price concession) runs **0.79–1.02** for k = +1…+30. The +5-minute delay
is a pure entry-price effect — the market hands back 0.0722 R after the close and you take
0.0568 of it. It is worth having and it is not the same lever.

### How early could a detector fire?

| minute of the bar | median share of the final displacement already done | sign already correct |
|---:|---:|---:|
| 3 | 0.196 | 0.667 |
| 5 | 0.358 | 0.727 |
| 7 | 0.514 | 0.785 |
| 9 | 0.655 | 0.836 |
| 11 | 0.796 | 0.881 |
| 13 | 0.922 | 0.920 |

By minute 7 the median setup has half its move done and the direction is right 78.5 % of the
time. There is real information inside the bar by minute 5–7 — and the net-positive window
closes at minute 8.

---

## 4. THE HONEST BILL  (`X3_PHANTOM_V1.json`, `X3_BOOK_V1.json`, `X3_BREAKEVEN_V1.json`)

### 4a. Trades that die before the signal exists — already charged

Entering at the bar's open, **22.41 % of trades are stopped out before the M15 close** and
1.25 % hit target: **23.66 % of the population is resolved before the signal that justified
it exists.** This is charged inside every number above; the walk starts at the entry bar, not
at the decision instant.

| k | stopped pre-decision | targeted pre-decision |
|---:|---:|---:|
| −15 | 0.2241 | 0.0125 |
| −10 | 0.1704 | 0.0048 |
| −5 | 0.1038 | 0.0005 |

### 4b. Setups that never form — the real charge

A trigger that fires inside the bar fires on bars that never become candidates. Scan: **every
one of 71,437 January M15 bars on 24 symbols**; fire at minute j when the running displacement
from the bar's open reaches θ × (that symbol's median candidate risk distance); direction =
sign of the displacement; one risk unit per symbol; walk on the same M1 tape to T+120; charge
the broker-true toll.

| θ | minute | fired | precision | net R confirmed | net R phantom | net R book | vs baseline |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 3 | 5,369 | 0.2824 | **+0.23105** | −0.31147 | −0.15828 | +0.076 |
| 0.75 | 3 | 2,311 | 0.3626 | +0.21707 | −0.34068 | **−0.13843** | +0.096 |
| 0.75 | 5 | 3,847 | 0.3608 | +0.19331 | −0.34994 | −0.15394 | +0.080 |
| 1.00 | 5 | 2,008 | 0.4248 | +0.17193 | −0.41283 | −0.16442 | +0.070 |
| 1.00 | 13 | 5,143 | 0.4863 | −0.19318 | −0.08650 | −0.13838 | +0.096 |
| baseline: the real candidates at the M15 close | | 12,892 | — | — | — | **−0.23410** | — |

Three things this settles:

1. **The confirmed leg is worth +0.19 … +0.23 R/trade NET at minute 3–5** — a swing of
   +0.42 … +0.47 R against the same names entered at the close. The prize survives a real
   trigger; what it does not survive is the trigger's false positives.
2. **Even the bare displacement trigger already beats the shipped contract** (−0.138 vs
   −0.234 R/trade). It is still negative, so this is a better way to lose money, not an edge.
3. **"Confirm or flatten" is refuted.** Flattening the unconfirmed leg at the M15 close pays a
   second toll and locks in the drift: the phantom leg goes from −0.24 net (let it run) to
   −0.47 net (flatten it). Every CONFIRM cell is worse than its UNCOND twin. The book already
   re-evaluates at each close, so this was the obvious implementable design — it is measured
   and it is wrong.

### 4c. The precision target — the number to hand to the separator lane

`net(prec) = prec·net_confirmed + (1−prec)·net_phantom`

| cell | achieved precision | break-even precision | gap | precision merely to beat the M15 close |
|---|---:|---:|---:|---:|
| CONT θ0.50 min3 | 0.2824 | **0.5741** | +0.292 | 0.1426 |
| CONT θ0.75 min3 | 0.3626 | **0.6108** | +0.248 | 0.1911 |
| CONT θ0.75 min5 | 0.3608 | 0.6442 | +0.283 | 0.2132 |
| CONT θ1.00 min5 | 0.4248 | 0.7060 | +0.281 | 0.3056 |
| CONT θ0.25 min3 | 0.2051 | 0.5945 | +0.390 | **0.0208** |

**An intra-bar separator must reach ≈ 0.57–0.61 precision at minute 3 to make earliness pay
outright.** Bare displacement reaches 0.28–0.44. That gap — about 0.25 of precision on
2,311–5,369 firings a month — is the whole remaining question, and it is exactly the object
x2 is hunting.

---

## 5. TWO SUBSTRATE FINDINGS (both new, both cheap, both affect other lanes)

**5a. The sealed path sidecar has a 60-second blind spot.** Its bar 1 is the M1 bar labelled
T+1; the minute [T, T+1) — the first 60 seconds after the decision — is not in any path.
Including it costs the shipped contract **−0.00299 R/trade** (−0.05884 → −0.06184) and changes
26 of 13,692 verdicts. Every published number computed on `w0_R_PATHS`/the sidecar is that
much optimistic. It also means the estate's "touched within 60 seconds" cohort was measured on
the *second* minute: on the true first minute the touch share is **0.7141** of all rows against
**0.6133** using the sidecar's bar 1.

**5b. The clock convention is now proven, not assumed.** `entry_price` equals the close of the
M1 bar labelled T−1 for **14,911 / 14,911 at-market rows at exactly 0.0 relative error**, and
this lane's independent reconstruction of the forward path reproduces the sealed sidecar over
**3,229,819 bars with a maximum absolute difference of 5.0e-5 R** (the sidecar's own rounding)
and **0 length mismatches on 27,658 paths**. `plain_walk_r` reproduces to max 5.0e-5,
mean 7.7e-6. Anything built on `x3_TAPE.npz` inherits that.

---

## 6. AN UNPLANNED FIND — the first 3 minutes mean-revert  (`X3_FADE_V1.json`)

Fading — not continuing — a displacement that completes inside the **first 3 minutes** of an
M15 bar, net of broker-true cost:

| θ | minute 2 | **minute 3** | minute 4 | minute 5 | minute 6 |
|---:|---:|---:|---:|---:|---:|
| 1.00 | −0.1642 (725) | −0.0758 (1107) | −0.1466 | −0.1508 | −0.1659 |
| 1.25 | −0.2515 (420) | **+0.0401 (648)** | −0.1392 | −0.1620 | −0.1617 |
| 1.50 | −0.2787 (259) | **+0.1259 (388)** | −0.0791 | −0.1917 | −0.1234 |
| 1.75 | −0.1326 (184) | **+0.1617 (263)** | −0.0747 | −0.1335 | −0.0614 |
| 2.00 | +0.0078 (133) | **+0.2504 (193)** | −0.0204 | −0.1056 | −0.0779 |

The continuation mirror at minute 3 is monotone in the opposite direction (−0.165, −0.220,
−0.288, −0.333, −0.337), so this is one observation seen twice, not two. **It is the only
early cell in this lane whose PHANTOM leg is profitable** (+0.0232 net R at θ=1.5), i.e. its
break-even precision is negative: it does not need the generator to confirm anything.

**Caveats, stated plainly.** n = 193–648. The day-block bootstrap does **not** clear zero:
θ=1.5/min3 gives +0.12595, CI95 [−0.10983, +0.43674], P(≤0) = 0.165, with 11 of 25 days
positive; θ=2.0/min3 gives P(≤0) = 0.107. It is a **ridge in θ and a spike in minute** — minute
2 and minutes 4–6 are negative — which is the pattern of a real effect with a threshold *or* of
noise, and 60 cells were searched. It concentrates in XAUUSD/XAGUSD/US30_cash but appears on
all 24 symbols. Report it, do not trade it; it is a candidate for the travel stage.

---

## 7. WHAT THIS LANE DID NOT MEASURE

- **February–May.** Everything here is January. The travel test is a later stage's job.
- **Spread by minute-of-bar.** The toll is charged as a per-symbol constant; if spread widens
  inside a displacing bar the early arms are charged too little. The tick archive
  (2026-06-18..07-24) can answer this for mechanism but not for January.
- **A live fill for an early market order.** Same standing gap the estate has for the
  5-minute delay (U5).
- **The POI/limit cohort.** 12,747 rows (`born_resting`, `born_marketable`, `born_past_stop`)
  are carried in `X3_CUTS_V1.json` but the at-market cohort is the one where "enter earlier"
  is a well-posed question; for a resting limit, earliness means placing the order sooner,
  which is a different experiment.
- **Whether a separator can reach 0.57 precision.** That is §4c's handoff, not a result here.

---

## Files

| file | what |
|---|---|
| `x3_TAPE.npz` | 27,658 × 141 × OHLC M1 tape, offsets −20…+120 min, float64, validated against the sealed sidecar |
| `X3_SUBSTRATE_V1.json` | the validation receipt (§5b) |
| `X3_SWEEP_V1.json` | the offset curve, 51 offsets × 2 contracts × 6 cohorts + paired bootstraps |
| `X3_MECHANISM_V1.json` | market path, capture efficiency, pre-decision resolution, blind minute |
| `X3_CUTS_V1.json` | per family / instrument / hour / bar-direction curves |
| `X3_PRIZE_V1.json` | broker-true net curves, per-family lift + CI, the EARLY/LATE books |
| `X3_PHANTOM_V1.json` | 71,437-bar trigger scan, frozen-cost |
| `X3_CONFIRM_V1.json` | confirm-or-flatten at frozen cost (superseded by X3_BOOK_V1) |
| `X3_BOOK_V1.json` | the early books at broker-true cost, both polarities, both modes |
| `X3_BREAKEVEN_V1.json` | required vs achieved precision |
| `X3_FADE_V1.json` | the minute-3 reversion neighbourhood + stress |
| `x3_00_substrate.py` … `x3_09_fade.py`, `x3_lib.py` | every script, with its `.log` |
