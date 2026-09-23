# LANE x5 — THE CONFIRMATION TRADE-OFF, PRICED PROPERLY

Wave 19 broad forensic. January 2026 diagnostic pool, CJ true-UTC re-clock, 27,658 candidates;
**26,316 (95.15 %) carry a complete M1 window for their own trigger bar** and are the common
population every rung below is priced on. Nothing is sampled. Every rung is priced on the SAME
rows, with the same conservative tie rule (same-bar target+stop → STOP) and **no same-bar credit
anywhere** — every walk starts at the bar AFTER the entry bar.

Machine-readable: `x5_RESULT.json`. Measurement files: `x5_LADDER_V1.json`, `x5_MIRROR_V1.json`,
`x5_COND_V1/V2.json`, `x5_CANCEL_V1.json`, `x5_COST_V1.json`, `x5_LIMIT_V1.json`,
`x5_JOINT_V1.json`, `x5_MATCHED_V1.json`, `x5_LEVELXM_V1.json`. Substrate:
`x5_WINDOW_JAN.npz` (built by `x5_10_window.py` from the lane hold's
`bridge_ftmo_m1_202601` M1 CSVs — 24/24 symbols).

---

## 0. HEADLINE

**The M15 close is the single worst minute to enter in the entire 44-minute window around it.**
Unconditional mean R/trade by entry minute, structural stop held fixed, equal 120-bar holding,
n=26,316 at every rung:

```
minute:  -14    -12     -9     -6     -3     -1     0     +1    +3    +6    +9   +15   +30   +60
R/trade +.179  +.118  +.037  -.048  -.127  -.174 -.191 -.170 -.147 -.128 -.115 -.115 -.088 -.055
                                                   ^^^^ the minimum of the whole curve
```

Paired day-block bootstrap versus the incumbent (2,000 day-resamples, same rows both arms):
acting at minute 1 of the trigger bar instead of at its close is **+0.3702 R/trade
[+0.3482, +0.3914], p(≤0)=0.0000**. The curve is monotone in |k| on both sides of the close and
**all 34 non-reference rungs are significant at p(≤0)=0.0000** — including the whole honest
half: **+0.0585 [+0.0485, +0.0694] at +5 min**, **+0.0845 [+0.0703, +0.0982] at +13 min**,
**+0.1355 [+0.1126, +0.1578] at +60 min**.

**And 82.5 % of that prize is unattainable.** The exact mirror (same entry price, same risk
distance, stop reflected through the entry, opposite side) splits it:
`Δ = Δdrift − Δinfo = +0.0647 (side-free) + 0.3054 (directional)`. The directional part is the
trigger bar's own move — which is *why the candidate exists*. Capturing it needs a generator
that emits on a partial bar; it cannot be had by moving an order.

**The side-free residue is real and it is +0.065 R/trade.**

---

## 1. WHERE THE SIGNAL'S DIRECTIONAL CONTENT ACTUALLY LIVES  [the mechanism]

Measured on the geometry-free cell — the 14,403 candidates whose entry price IS the decision-
instant market price, with the risk distance held fixed so the mirror is exact and no geometry
can bias it. `info = (r_inverse − r_original)/2`; **info < 0 means the signal's own side is
RIGHT.**

| entry minute | −14 | −12 | −10 | −9 | **−8** | −6 | −4 | **−1** | 0 | +1 | +2 | +5 | +15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| info | **−.0874** | −.0590 | −.0305 | −.0143 | **+.0057** | +.0368 | +.0703 | **+.0896** | +.0744 | +.0424 | +.0146 | +.0061 | +.0062 |
| 95 % lo | −.1127 | −.0788 | −.0539 | −.0384 | −.0147 | +.0125 | +.0470 | +.0648 | +.0489 | +.0115 | −.0166 | −.0207 | −.0184 |
| 95 % hi | −.0635 | −.0372 | −.0058 | +.0106 | +.0264 | +.0609 | +.0940 | +.1127 | +.0982 | +.0706 | +.0309 | +.0299 | +.0299 |

Read it as one sentence: **the signal is right for the first ~7 minutes of its own trigger bar,
crosses to wrong between minute 6 and minute 7, is most wrong one minute before it is allowed to
act, and by two minutes after the close it knows nothing at all.** Total swing +0.177 R/trade.
The value at the close, +0.0744, reproduces L7's +0.0764 independently (different substrate,
different horizon convention, same cell).

The estate's framing — "a bar closing is the moment the move it describes has already finished" —
is now measured, and it is sharper than that: **the move is finished at minute 7 of 15.**

---

## 2. THE LADDER — how many survive, and what they earn

Rung = "act only when the setup's own condition has held for N consecutive M1 closes"; N=15 means
the condition held the whole trigger bar and you act at the close; N>15 means it also had to
survive N−15 minutes past the close. Conditions tested (all on closed M1 bars):

* **DIR / ANTI** — the forming bar has moved ≥ θ R in (against) the trade's direction, measured
  from the trigger bar's open. θ ∈ {0, .05, .10, .25, .50}.
* **POST / POSTANTI** — the same, anchored at the M15 close and evaluated only on bars at or
  after D. Uses nothing unknown at the decision instant.
* **LEVEL / LEVELX / LEVELXM** — price reached the candidate's own entry level. LEVELX adds
  "was on the wrong side of it at the trigger bar's open" (a genuine crossing). LEVELXM is
  LEVELX with a MARKET entry at the qualifying minute instead of an impossible fill at a level
  the market left N−1 minutes ago.

**1,132 arms were priced in total** (490 unconditional ladder cells across 4 exit contracts x 2
risk denominators x 2 horizons, 308 conditional rungs, 308 in the V1 pass, 14 LEVELXM, 12 limit
placements) — no multiplicity correction is applied anywhere. The full conditional table is in
`x5_COND_V2.json`; the shape:

| rung | n taken | survival | R/trade | book R/candidate | median entry stamp |
|---|---:|---:|---:|---:|---:|
| incumbent (act at the close) | 26,316 | 100.0 % | **−0.1910** | −0.1910 | 0 |
| DIR θ0 N=1 | 23,716 | 88.6 % | +0.1269 | +0.1156 | −15 |
| DIR θ0 N=15 (whole bar, act at close) | 13,443 | 43.7 % | −0.1280 | −0.0508 | 0 |
| DIR θ0 N=30 | 8,349 | 31.7 % | −0.0659 | −0.0209 | +15 |
| POST θ0 N=21 | 5,539 | 21.0 % | −0.0696 | −0.0147 | +21 |
| POSTANTI θ0 N=30 | 4,210 | 16.0 % | −0.0730 | −0.0117 | +29 |
| LEVELXM N=18 | 4,008 | 15.2 % | −0.0437 | −0.0067 | +16 |
| LEVELXM N=25 | 2,601 | 9.9 % | **−0.0170** | −0.0017 | +22 |

### 2.1 max R/trade vs max total R — and which one the owner should care about

**No rung that is both honest and fill-realistic is positive.** The two optima:

* **max R/trade** — `LEVELXM N=25`: **−0.0170 R/trade [−0.0789, +0.0465]**, 9.9 % survival.
* **max total R** — is *degenerate*. Every honest rung has a negative mean, so total R is
  maximised by taking the fewest trades; the ranking is an artifact of survival, not of edge.
  The non-degenerate best is the limit-contract joint in §3: **−0.0078 R per candidate over all
  26,316, 95 % [−0.0254, +0.0106]** — the only construction in this lane that is statistically
  indistinguishable from flat.

**Which matters:** under fixed-fractional sizing each trade risks the same cash, so what compounds
is **total R**, and R/trade only binds when trade slots are scarce. In January the book saw
26,316 candidate-opportunities across 21 days and takes a handful a day — **slots are not the
scarce resource, so the owner should optimise total R (equivalently book R per candidate), which
means the rule that refuses most candidates.** The R/trade optimum is the wrong objective here and
would push toward the thinnest, least reliable cells.

---

## 3. THE 60-SECOND CANCEL × EARLINESS — they are NOT substitutes, and the naive sum is 4.3× wrong

The established cancel rule only exists under a **limit** contract (an order resting at
`entry_price`); the earliness lever is measured under an **at-market** contract. They are
different trades, and the numbers behave in opposite directions.

**Under the estate's own limit contract** (order rests at `entry_price`, placed at stamp p,
filled at the first bar whose adverse extreme reaches the level, walked from the next bar,
0.0 R booked if never filled — p=0 is the shipped contract):

| place p | fill % | book, no cancel | book, cancel 1st-bar fill | delay alone | cancel alone | joint | mean of the kept trades |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 99.8 % | −0.2068 | **−0.0186** | 0 | **+0.1882** | +0.1882 | −0.0627 |
| 5 | 97.4 % | −0.2599 | −0.0140 | −0.0531 | +0.1882 | +0.1928 | −0.0349 |
| **8** | 96.4 % | −0.2790 | **−0.0078** | −0.0722 | +0.1882 | **+0.1990** | **−0.0194** |
| 30 | 91.1 % | −0.3437 | −0.0092 | −0.1369 | +0.1882 | +0.1976 | −0.0260 |

* The cancel reproduces the estate's number: **+0.1882 R/candidate** on the first-bar-fill rule,
  **+0.2185** using the pool's own `bars_to_entry_touch == 1` (l8 measured +0.2225).
* **Delaying placement is NEGATIVE on its own** (−0.053 at p=5, −0.137 at p=30) and worth only
  **+0.0108 on top of the cancel**. The cancel is **94.6 %** of the joint value.
* **The adverse selection is not a property of the M15 boundary at all.** The first fill after
  placement is the worst fill at *every* placement offset: −0.2686 (p=0), −0.4291 (p=5),
  −0.6712 (p=60). It is ordinary limit-order adverse selection — an immediate fill means the
  market is coming through your level — and it re-creates itself wherever you place.
* Why the rule works, mechanically: `bte==1` share by born state is **at_limit 75.8 %,
  marketable 95.1 %, past_stop 99.97 %, resting 9.5 %**. The cancel is largely a born-state
  filter — "refuse the ones the market has already run through".

**Under the at-market contract** (the geometry-free at_limit cell, fixed risk distance, where
L7's +0.0670 delay lever lives) the two levers are **antagonistic**:

| lever | Δ R per candidate |
|---|---:|
| delay to k=+5 alone | +0.0619 |
| cancel alone | +0.1266 |
| naive sum | +0.1887 |
| **actual joint** | **+0.0439** |
| **over-count** | **+0.1448 — the naive sum is 4.3× the truth** |
| joint + confirmation filter (θ=0) | +0.0457 |
| joint + confirmation filter (θ=0.10) | +0.0460 |

The joint is *worse than the cancel alone*. The delay lever is measured on precisely the rows the
cancel deletes: 75.8 % of at-market candidates are `bte==1`. **Any published figure that adds a
cancel value to a delay value has double-counted; on this pool the over-count is +0.145 R per
candidate.**

The honest delay lever itself is robust where it applies: at-market cell, fixed geometry,
k=0 → k=+5 is **+0.0619 R/trade, 95 % [+0.0475, +0.0759], p(≤0)=0.0000, positive on 19 of 21
days and 22 of 24 symbols**, moving that book from −0.0624 to −0.0005 — across zero, reproducing
L7 §3.4.

---

## 4. COST — earliness buys price, and fixed-fractional sizing takes some of it back

| entry minute | −14 | −5 | 0 | +5 | +15 | +60 |
|---|---:|---:|---:|---:|---:|---:|
| price improvement, median bps | **+0.689** | +0.290 | 0 | **+0.504** | +0.948 | **+2.360** |
| price improvement, mean bps | +2.758 | +0.949 | 0 | +1.129 | +2.031 | +4.559 |
| share of rows with a better price | 54.3 % | 53.2 % | — | 55.7 % | 56.9 % | 58.8 % |
| median cost in R at the rung | 0.2487 | 0.2125 | 0.2000 | 0.2077 | 0.2075 | 0.1982 |
| median d_k / d_0 | 1.390 | 1.225 | 1.000 | 1.177 | 1.269 | 1.424 |

* Median all-in cost is **2.434 bps of price**, median spread **1.561 bps**. So delaying five
  minutes recovers **32 % of the median spread**; going fourteen minutes early recovers **44 %**;
  waiting an hour recovers **151 %** (but pays for it in the R column).
* **bps and R disagree in sign at the early end.** Mean R improvement at k=−14 is **−0.1364**
  while mean bps improvement is **+2.758**: a fat left tail of small-risk-distance rows where a
  small price move is a large R move. Use the medians; the mean R improvement is not a
  representative statistic on this pool.
* **The R-denominated cost gets worse, not better, when the entry moves.** Median cost rises
  0.2000 → 0.2077 (k=+5) and → 0.2487 (k=−14) even though the median risk distance *widens*.
  The rows whose entry moves closer to the structural stop are disproportionately the expensive
  ones, and fixed-fractional sizing scales the position by exactly `d0/d_k`, so it pays that
  spread over a smaller unit. Any earliness claim priced on gross R overstates its net by this
  amount.
* Robustness of the price gain: **23 of 24 symbols** improve at k=−14 and **22 of 24** at k=+5
  under fixed geometry (exceptions USDJPY and USDCHF, both by <0.0003 R).

---

## 5. THE JOINT OPTIMUM, WITH THE ABLATION — and the one separator that beats the clock

### 5.1 Joint optimum

| construction | R per candidate | 95 % |
|---|---:|---|
| incumbent (at-market at the close) | −0.1910 | — |
| incumbent limit contract, p=0, no cancel | −0.2068 | — |
| **limit at `entry_price`, placed at p=+8, cancel any fill on the first bar after placement** | **−0.0078** | **[−0.0254, +0.0106]** |
| LEVELXM N=25 (market entry, 9.9 % survival) | −0.0017 | — |

**Ablation** (§3, both contracts): standalone values must never be summed. Limit contract:
cancel +0.1882, delay −0.0722, joint +0.1990 → delay contributes **5.4 %**. At-market contract:
cancel +0.1266, delay +0.0619, joint **+0.0439**, over-count **+0.1448 (4.3×)**.

### 5.2 The entry-time-matched control — the test that separates "confirmation" from "clock"

Every conditional rung enters at a different minute, so its advantage may be nothing but the
clock. Control: price the whole core population at the rung's **own distribution of entry
stamps** and subtract. `CONFIRMATION_VALUE = mean(taken) − matched control`.

| condition | best CONFIRMATION_VALUE | verdict |
|---|---:|---|
| DIR θ=0 | +0.0795 at N=1 — but **ANTI θ=0 scores +0.0704 at N=1** | **refuted by symmetry**: two opposite conditions score the same, so the value is "the row qualified early", not what it qualified on |
| DIR θ=0.25 | **−0.0950** | actively harmful |
| POST / POSTANTI (all θ, all N) | ≤ +0.021 | nothing |
| **LEVELXM** | **+0.0611 … +0.0753**, monotone in N | **survives** |

### 5.3 LEVELXM — stressed

*Price was on the wrong side of the candidate's own entry level at the trigger bar's open, then
traded at/through that level and stayed there for N consecutive M1 closes; enter at market at
that minute.* For **N ≥ 18, 100 % of entries land at or after the M15 close** — nothing is acted
on early, and the level itself is known at D — so the rung is **honest and fill-realistic**.

| N | n | survival | R/trade [95 %] | matched control | CONFIRMATION_VALUE [95 %] | p(≤0) | days + | symbols + | first-emission only |
|---:|---:|---:|---|---:|---|---:|---:|---:|---:|
| 15 | 4,855 | 18.4 % | −0.0502 [−0.0926, −0.0033] | −0.1133 | **+0.0631** [+0.0186, +0.1125] | 0.001 | 14/21 | 18/24 | −0.0458 |
| **18** | 4,008 | 15.2 % | −0.0437 [−0.0903, +0.0087] | −0.1048 | **+0.0611** [+0.0169, +0.1151] | 0.004 | 15/21 | 17/24 | −0.0377 |
| 21 | 3,356 | 12.8 % | −0.0352 [−0.0904, +0.0221] | −0.1001 | +0.0649 [+0.0097, +0.1200] | 0.007 | 14/21 | 17/24 | −0.0307 |
| **25** | 2,601 | 9.9 % | **−0.0170** [−0.0789, +0.0465] | −0.0923 | **+0.0753** [+0.0149, +0.1400] | 0.010 | 15/21 | 18/24 | −0.0095 |
| 30 | 1,837 | 7.0 % | −0.0205 [−0.0808, +0.0432] | −0.0888 | +0.0683 [+0.0059, +0.1301] | 0.018 | 15/21 | 18/24 | −0.0140 |

De-duplicating to first emissions moves it the *right* way (−0.0437 → −0.0377 at N=18), so it is
not pseudo-replication. Stop rate falls monotonically with N (0.371 → 0.261) and win rate rises
(40.0 % → 44.1 %). **This is the piece the estate has never had: a condition, computable from
information available at the decision instant, that is worth +0.06 R/trade over the same
population entering at the same minutes.** It does not make January positive; it removes about
a third of the honest deficit on the 10–15 % of candidates it keeps.

### 5.4 The finding that must not be buried: LEVELXM's inverse is positive

| N | LEVELXM original | **LEVELXM inverse** [95 %] | p(≤0) | LEVELXM info | unconditional info at the same stamps |
|---:|---:|---|---:|---:|---:|
| 10 | −0.0714 | **+0.0739** [+0.0491, +0.0980] | 0.000 | +0.0727 | +0.105 |
| 15 | −0.0502 | +0.0509 [+0.0143, +0.0862] | 0.003 | +0.0506 | +0.105 |
| 18 | −0.0437 | +0.0534 [+0.0180, +0.0856] | 0.002 | +0.0486 | +0.092 |
| 25 | −0.0170 | +0.0610 [+0.0088, +0.1122] | 0.009 | +0.0390 | +0.082 |
| 30 | −0.0205 | +0.0491 [−0.0113, +0.1043] | 0.055 | +0.0348 | +0.082 |

The crossing filter **reduces** the pool-wide inversion (info 0.082–0.105 → 0.035–0.073) but does
not remove it. The single best-performing honest, fill-realistic construction in this lane is
therefore **"wait for a genuine crossing of the entry level, let it hold ~10–25 minutes, then take
the OTHER side"** — +0.049 to +0.074 R/trade. That is L7's inversion surviving a strong filter,
not a new phenomenon, and it is one month. It is reported, not recommended.

---

## 6. WHAT DID NOT WORK — reported because under-reporting is the failure mode

* **Directional confirmation of any strength is worth nothing at matched entry time.** DIR at
  θ ≥ 0.25 is *negative* (−0.095 at N=2). Requiring the bar to be going your way before acting is
  a cost, not a filter.
* **DIR N=1 (+0.1305 R/trade) is worse than simply acting at minute 1 unconditionally
  (+0.1792).** At matched earliness the condition subtracts 0.049.
* **POST and POSTANTI both improve the book (+0.03…+0.12 per candidate) by opposite mechanisms** —
  POST is selection (+0.75) minus timing (−0.63); POSTANTI is timing (+0.65) minus selection
  (−0.53). Their common factor is "not entering at the close", which the unconditional delay
  already buys. At matched entry time both are worth ≤ +0.021.
* **Aborting on the first adverse close destroys value** at almost every rung (−0.03 to −0.31).
* **LEVEL and LEVELX as first constructed are not implementable**: they fill AT the entry level
  after the market has been beyond it for N−1 minutes. They dominate every unfiltered leaderboard
  (up to +0.82 R/trade) and are excluded by the `fill_realistic` flag in `x5_RESULT.json`.
  This is a trap for any lane that reads the frontier without the flag.
* **`born_past_stop` rows are not a trade under a structural-stop contract**: the −1R level ends
  up on the opposite side of the market from the stop. 12.7 % of the pool. Restricting to rows
  whose stop is on the correct side of the entry (`STOPOK`, 87.3 % at the close) moves the
  incumbent −0.1910 → −0.2173 and leaves the whole ladder shape intact.

---

## 7. CAVEATS THAT BIND EVERY NUMBER ABOVE

1. **January 2026 only** — 21 trading days, one month, one arm (S0R0). Discovery. **No
   multiplicity correction anywhere**; ~600 rungs were priced across condition families, θ, N,
   four exit contracts, two risk denominators and two horizon conventions — **1,132 priced arms**. A later stage tests
   travel; February is used-once VAL, March is outcome-unread.
2. **Gross of cost** unless the row says otherwise. Mean frozen `cost_r` is **0.6363 R**; charging
   it makes every rung in this receipt deeply negative (best sane-subset net −0.41 at k=−14,
   −0.70 at the close). Nothing here is a claim about a net-positive book.
3. **The horizon is 120 M1 bars from entry.** Nothing about holding beyond 2 hours is measurable
   on this substrate. The WALL variant (exit at D+119 for every rung) is emitted as a control and
   moves no conclusion by more than 0.003 R.
4. **Everything at k<0 is look-ahead in the side and the levels** — the candidate does not exist
   until its bar closes. Rungs are flagged `honest` in `x5_RESULT.json` iff every taken row's
   entry stamp is ≥ 0. The k<0 half is an *upper bound on the prize*, not a strategy.
5. **The 2R target is held at 2.0** for all rungs; 26,428 of 27,658 pool rows carry
   `policy_target_r` 2.0, and the FIXLEV contract (both levels at their original prices) is
   emitted alongside as the sensitivity.
6. 1,342 rows (4.85 %) are excluded for want of a complete trigger-bar M1 window — mostly
   session edges and crypto weekend gaps.

---

## 8. WHAT THIS LANE HANDS FORWARD

1. **The prize from earliness is +0.370 R/trade and 82.5 % of it needs a partial-bar generator.**
   The remaining +0.065 is side-free and available by moving an order.
2. **The window is minutes 1–7 of the trigger bar.** A generator that can emit on a 5-minute
   partial M15 bar is worth measuring; one that emits at minute 12 is not.
3. **Stop summing the cancel and the delay.** They are measured under incompatible fill contracts
   and, where they overlap, the naive sum is 4.3× the truth.
4. **The adverse first-minute fill is a limit-order property, not a bar-boundary property.** It
   re-appears, worse, at every placement offset. The estate's rule is right for a reason it has
   not stated.
5. **LEVELXM is the first condition that beats the clock** (+0.061 R/trade at N=18, honest,
   fill-realistic, 15/21 days, 17/24 symbols, survives de-duplication) — and its inverse is
   positive. Both belong in the travel test.
