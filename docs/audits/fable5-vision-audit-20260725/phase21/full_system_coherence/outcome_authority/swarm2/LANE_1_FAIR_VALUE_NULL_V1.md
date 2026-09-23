# LANE 1 — THE FAIR-VALUE NULL

**Built 2026-08-11. Read-only: nothing live was touched, no config byte moved, no git write.**
Receipts: `swarm2/lane1_receipts/` (machine-readable summary `LANE1_SUMMARY_V1.json`, plus every
script that produced a number in this file).

---

## 0. The number that matters most

> **Every published GTOS expectancy has been compared against a null of zero. The correct null is
> `−E[cost_r]`, and it is a theorem, not a modelling choice. Against the correct null the estate's
> five-month candidate population earns**
>
> ### **+0.0309 R/trade, 95 % CI [+0.0181, +0.0439], n = 146,745, clustered on 100 trading days (t = 4.63)**
>
> **The selection layer has real, significant, positively-signed skill in all five sealed-read months.
> The book loses money because friction is 0.263 R/trade and the skill is 0.031 R/trade — an 8.5:1
> ratio. The estate has spent the program hunting for a better selector while the entire deficit sits
> in the cost-to-geometry ratio.**

And the adversarial correction, stated up front because it bounds the claim: charging the
tick-measured true stop slippage to the *fill* (§2.3) takes the edge to **+0.0095 R/trade**, which is
no longer significant. The +0.031 is exact at the estate's own accounting; the +0.0095 is exact at
tick truth. **Both are above zero and both are far above the null the estate actually used.**

---

## 1. (A) The geometry-neutral edge

### 1.1 Why the null is not zero, and why it needs no simulation

Optional stopping gives `E[(P_τ − P_fill)/risk] = 0` for a martingale `P`, **for any stop distance,
any target distance, and any bounded time stop**. That is the driftless benchmark, and it is
geometry-free by construction — no Monte Carlo required.

What breaks the zero is that the engine does not execute against one price. It fills on the
**entry-side** quote and exits on the **exit-side** quote:

- `src/research_infra/walkforward/quote_side.py:1239-1247` — per-M1-bar quote transform, entry side =
  ask (long) / bid (short), exit side = bid (long) / ask (short).
- `quote_side.py:1382` — `gross = direction * (price − fill_price) / risk`.

For a long, `fill = B_fill + s` and every exit books on `B_exit`. Writing the bid as the martingale:

```
E[gross] = E[(B_exit − B_fill)/risk] − E[s/risk] = 0 − E[spread_r] = −E[spread_r]
```

and since `terminal_net_r = gross − deductible` where `deductible = slippage + swap + commission`
(`candidate_funnel_analysis.py:164-179`) and `cost_r = spread + slippage + swap + commission`
(`src/costs/model.py:781-797`):

> ### `E[terminal_net_r] = −E[cost_r]` under a driftless martingale. This is the fair-value null.

The identity holds for **both** order types, and the derivation is confirmed by the data rather than
assumed. A LIMIT entry fills when the *ask* touches the limit, so `B_fill = entry − s`, giving the
same `−E[spread_r]`; and the engine books LIMIT barriers at the raw level, which is exactly what is
measured:

| order type | leg | n | mean gross | median | fraction booked **exactly** at the barrier |
|---|---|---:|---:|---:|---:|
| LIMIT | TARGET | 16,136 | **+2.00131** | +2.00000 | **97.60 %** |
| LIMIT | STOP | 40,153 | **−1.00100** | −1.00000 | **97.31 %** |
| MARKET | TARGET | 14,601 | +1.73842 | +1.83235 | 1.54 % |
| MARKET | STOP | 38,054 | −1.04443 | −1.01726 | 2.11 % |

### 1.2 The edge, and why it is robust by construction

```
edge  ≡  realized − fair_value_null  =  terminal_net_r + cost_r  ≡  terminal_gross_r + spread_r
```
(verified as an exact identity, max |dev| 8.9 × 10⁻¹⁶.)

Two robustness properties fall straight out of that algebra and they matter more than any
sensitivity table:

1. **The edge is completely independent of the commission, swap and slippage models.** They appear in
   `terminal_net_r` and in `cost_r` with opposite signs and cancel exactly. Every argument about
   broker-true commission (CN), swap tiers, or the flat `expected_slippage_r = 0.02` is orthogonal to
   this measurement.
2. **The edge is invariant to the *level* of the spread model.** If the true spread exceeds the
   modelled spread by Δ, the true fill is Δ worse **and** the true null is Δ more negative:
   `edge_true = (gross − Δ) + (spread_r + Δ) = edge`. I initially treated spread mis-estimation as
   the headline vulnerability; the algebra refutes that, and §2.2's tick measurement confirms the
   model is accurate anyway.

| ladder | pooled mean | cluster-SE (day, K=100) | t | 95 % CI |
|---|---:|---:|---:|---|
| `terminal_net_r` (what every published result uses) | −0.23209 | 0.00760 | −30.54 | [−0.24617, −0.21702] |
| `terminal_gross_r` | −0.09042 | 0.00660 | −13.70 | [−0.10326, −0.07781] |
| **edge = realized − fair null** | **+0.03087** | 0.00667 | **+4.63** | **[+0.01813, +0.04389]** |

### 1.3 Ranked tables

**By order type — the result that contradicts the estate's frozen rule of record.**

| cell | n | realized | fair null | **EDGE** | 95 % CI | sig |
|---|---:|---:|---:|---:|---|:--:|
| **LIMIT** | 72,496 | −0.1907 | −0.2445 | **+0.0538** | [+0.0300, +0.0798] | **yes** |
| MARKET | 74,249 | −0.2725 | −0.2810 | +0.0084 | [−0.0050, +0.0228] | no |

The February PASS rule (`MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json`) trades only when the top
candidate is MARKET and abstains on LIMIT. **Against fair value, that is the arm with 6.4× less
skill, and the only arm whose edge is not significant.** §2.4 explains why LIMIT looked worse.

**And "order type" is not an order type — it is a family filter.**
`candidate_funnel_analysis.py:81` reads
`return "LIMIT" if row.get("origin_family") in LIMIT_FAMILIES else "MARKET"`, with
`LIMIT_FAMILIES = {current_fvg_fill, current_ob_retest, current_breaker_re_entry}`
(`:49-51`). The mapping is deterministic and total: measured on all 632,934 rows, those three
families are 100 % LIMIT and the other seven are 100 % MARKET, and the three resolved counts sum to
**72,496 = the LIMIT arm exactly**.

> So §1.3's two tables are one finding, not two. **The estate's frozen rule abstains on precisely
> the three origin families that beat fair value** (+0.0545 / +0.0523 / +0.0490) and trades the seven
> that do not. It is not a microstructure preference for market orders; it is a family exclusion that
> was never examined as one.

**By month — five of five positive; leave-one-month-out keeps every CI clear of zero.**

| month | n | realized | fair null | EDGE | 95 % CI |
|---|---:|---:|---:|---:|---|
| apr | 28,709 | −0.2208 | −0.2742 | **+0.0534** | [+0.0269, +0.0794] |
| may | 27,118 | −0.2440 | −0.2815 | **+0.0376** | [+0.0121, +0.0618] |
| feb | 28,969 | −0.1925 | −0.2208 | +0.0283 | [−0.0022, +0.0610] |
| jun | 32,927 | −0.2368 | −0.2568 | +0.0200 | [−0.0109, +0.0527] |
| jul | 29,022 | −0.2664 | −0.2836 | +0.0172 | [−0.0075, +0.0431] |

Leave-one-out: drop-feb +0.0315 · drop-apr +0.0254 · drop-may +0.0294 · drop-jun +0.0340 ·
drop-jul +0.0342, every CI strictly positive.

**By origin family** (full table `lane1_receipts/edge_origin_family.csv`):

| family | n | realized | fair null | EDGE | 95 % CI | sig |
|---|---:|---:|---:|---:|---|:--:|
| `current_fvg_fill` | 60,911 | −0.1976 | −0.2521 | **+0.0545** | [+0.0285, +0.0828] | **yes** |
| `current_breaker_re_entry` | 3,982 | −0.1914 | −0.2438 | +0.0523 | [−0.0234, +0.1317] | no |
| `current_ob_retest` | 7,603 | −0.1347 | −0.1837 | +0.0490 | [−0.0099, +0.1098] | no |
| `cross_asset_lead_lag` | 10,919 | −0.3240 | −0.3562 | +0.0322 | [−0.0003, +0.0643] | no |
| `session_open_range_break` | 4,785 | −0.0977 | −0.1178 | +0.0201 | [−0.0237, +0.0647] | no |
| `structural_distance_extreme` | 11,118 | −0.5688 | −0.5783 | +0.0095 | [−0.0286, +0.0503] | no |
| `displacement_continuation` | 20,737 | −0.1366 | −0.1454 | +0.0089 | [−0.0216, +0.0384] | no |
| `regime_transition_break` | 1,222 | −0.0640 | −0.0725 | +0.0085 | [−0.0393, +0.0570] | no |
| `liquidity_sweep_reclaim` | 23,049 | −0.2916 | −0.2888 | −0.0028 | [−0.0326, +0.0268] | no |
| `volatility_compression_expansion` | 2,419 | −0.1142 | −0.0909 | −0.0234 | [−0.0604, +0.0127] | no |

**The three families that beat fair value are exactly the three `LIMIT_FAMILIES`** — the same
finding as the order-type table above, since the mapping is deterministic.
`liquidity_sweep_reclaim` — the family carrying +13.6 of February's
+14.2 R and the estate's single most-cited positive — has an edge of **−0.0028 [−0.0326, +0.0268]**:
against fair value it is indistinguishable from a coin, and its February result was a cost-band
artifact of *which* trades it happened to take, not skill.

**Where realized is negative but beats fair value.** This is the whole table: **every single cell
above has a negative `realized` and eight of ten have a positive edge.** The most extreme case is
`structural_distance_extreme` at −0.5688 realized against a −0.5783 null — a family the program
has repeatedly written off, which is in fact *ahead* of a coin flip. Its problem is that it selects
candidates whose geometry costs 0.578 R/trade in friction.

**By symbol** (top of `edge_symbol.csv`): BTCUSD **+0.0671** [+0.0173, +0.1147]\*, JP225 **+0.0654**
[+0.0130, +0.1171]\*, EURJPY **+0.0544**\*, GER40 +0.0514, ETHUSD **+0.0500**\*, NAS100 **+0.0456**\*.
Bottom: CHFJPY −0.0113, XAGUSD −0.0104, EURUSD −0.0076.

**By session** — one cell is broken and should be read as a defect, not a result:
`moonshot_h20_21`, n = 874, edge **−0.2747 [−0.3776, −0.1712]**, with `pS = 0.804` and
**`pX = 0.000`** — not one time-stop in 874 trades. A barrier system that never times out in a
one-hour bucket is a clock/rollover artifact. Best cells: `moonshot_h21_22` +0.1711\*,
`moonshot_h13_14` +0.1109\*, `moonshot_h10_11` +0.0850\*, `moonshot_h11_12` +0.0821\*.

### 1.4 Optional-stopping decomposition — where the gross-side shortfall lives

Taking the exact barriers (−1, +2) as the reference, optional stopping forces the time-stop mean to
`(p_S·1 − p_T·2)/p_X`. The residual splits exactly into three measured legs (they sum to `delta`
identically):

| leg | value | reading |
|---|---:|---|
| target-fill | −0.0259 | targets book +1.876 against a +2.0 barrier |
| stop-fill | −0.0118 | stops book −1.022 against a −1.0 barrier |
| **time-stop mark** | **−0.0527** | marks at +0.238 against an OST-fair +0.443 |
| **total (`E[gross]`)** | **−0.0904** | |

**58.3 % of the gross-side shortfall is in the time-stop leg**, which is 25.8 % of the trades. No
prior work has looked at it. It is not a marking defect — §2.1 establishes the time-stop books an
executable price — so it is where the residual anti-selection actually sits.

---

## 2. (B) Are the four fill assumptions true?

Engine of record, and the only place in the repo emitting the four labels:
**`src/research_infra/walkforward/quote_side.py:1032-1482`**, `resolve_post_submission_m1_lifecycle`.
Live twin: `src/research_infra/wave21_forward_shadow/shadow_lifecycle.py:175-192`. The barrier tape
is **M1 only** — never M15, never the family's own timeframe (`quote_side.py:1069`, `:1098`;
`candidate_funnel_analysis.py:104`).

### 2.1 Verdict per assumption

| assumption | verdict | evidence |
|---|---|---|
| (i) the process is a martingale at this horizon | **HOLDS** | §3 |
| (ii) stops fill at exactly −1R | **FALSE as a claim; TRUE for LIMIT** | LIMIT 97.31 % exact; MARKET 2.11 %. Gap-opens book the gapped open (`:1396-1397`), intrabar touches book the exact stop (`:1420-1423`). |
| (iii) targets fill at exactly +target | **TRUE for LIMIT (97.60 %)**, and **correct by design** | A take-profit limit fills *at* the level. §2.3 measures the crossing tick as −0.0397 R *better* than the level; the engine correctly declines that credit. |
| (iv) time stops mark at a tradeable price | **HOLDS** | last complete pre-horizon **exit-side close** — bid for a long (`:1437`, `:1453-1462`). An executable price, not a mid, not a next-open. |

Intrabar ambiguity (the mandate's tie-break question): **neither barrier wins.** When one M1 bar
touches both, the row is censored — `quote_side.py:1415-1419`, `CENSORED_ORDERING_AMBIGUITY`, with no
tie-break and no finer drill-down, because M1 is the engine's data floor. §2.4 shows what that costs.

### 2.2 The spread model against tick truth

n = 18,978 MARKET rows whose fill and exit both fall in the tick window (2026-06-18..07-24), 24
symbols, against `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo` converted with the
`America/New_York + 7 h` rule.

| quantity | value |
|---|---:|
| modelled `spread_r`, mean / median | 0.14852 / 0.08586 |
| **true tick `spread_r`, mean / median** | **0.16155 / 0.09292** |
| median per-row ratio model/true | **1.0000** |

**The spread model is accurate at the median and understates the mean by 8.1 %** — it misses the fat
right tail (news, rollover). Per-symbol median ratios run 0.923 (EURGBP) to 1.103 (USOIL_cash); the
two worst *mean* misses are UK100 (0.096 modelled vs 0.252 true) and USDJPY (0.092 vs 0.128).
Because of §1.2's invariance this does not move the edge — but it does mean any *absolute* cost or
P&L projection built on `spread_r` is 8 % light on average and 2.6× light on UK100.

Entry fill: true entry-side quote minus modelled fill = **+0.0066 R mean, 0.0000 median** — the
engine's entry convention is exact at the median.

### 2.3 The one engine optimism that does **not** cancel

Stops are stop-*market* orders: they trigger when the exit-side quote crosses and fill at the next
available price. The engine books them **at the level**. Measured at the true first-crossing tick,
9,526 stop crossings:

| leg | n | mean | median | p95 | p99 | fraction adverse |
|---|---:|---:|---:|---:|---:|---:|
| STOP | 9,526 | **+0.03932 R** | +0.01706 | +0.1412 | +0.3403 | **99.6 %** |
| TARGET | 3,430 | −0.03969 R | −0.01935 | −0.0014 | −0.0001 | 0.0 % |

Charging stop slippage (and *not* crediting the target overshoot, since a TP limit fills at the
level) gives **+0.0289 R per barrier-resolved trade → +0.0214 R per resolved trade**, and

> **edge after charging tick-true stop slippage to the fill = +0.0309 − 0.0214 = +0.0095 R/trade**,
> CI shifted to approximately [−0.0033, +0.0225] — **positive but no longer significant.**

The constructive half of that, and it is a cheap engine repair: **the estate's flat
`expected_slippage_r = 0.02` is within 7 % of the measured truth (0.0214).** The reason it does not
already fix this is purely accounting — it is deducted from `terminal_net_r` *and* included in
`cost_r`, so it appears on both sides of the comparison and cancels. **Charge it to the fill price
inside `quote_side.py`, not as a post-hoc deduction, and the engine's gross becomes tick-honest at
essentially no cost in model complexity.**

### 2.4 Censoring: where LIMIT actually died

| | fillable candidates | censored | rate |
|---|---:|---:|---:|
| **LIMIT** | 162,054 | 89,558 | **55.26 %** |
| MARKET | 81,968 | 7,719 | 9.42 % |

Of the 97,277 censors, **67,241 (69.1 %) are `CENSORED_SOURCE_INTERVAL_GAP`** — a hole in the M1
archive, a property of the *data*, not of the trade. A selected censored row is charged
**`−1.0 − deductible_cost_r`** by fiat, at two sites:
`candidate_funnel_analysis.py:287-292` (ordering censors only) and
**`postmortem/pm_analysis.py:313` (every censor)**, which is the one the published gates run on.

Excess over fair value: **−0.47165 R per fillable LIMIT candidate**, versus −0.03845 for MARKET.
That asymmetry — not a difference in skill — is what made the LIMIT-bearing `mixed` arm look
catastrophic. The censored fiat charge is **80.4 % / 87.8 % / 70.8 %** of the `mixed` arm's
worst-case loss in Feb / AprMay / JunJul respectively.

**Adversarial check on the LIMIT edge.** If censoring were outcome-correlated the surviving 72,496
resolved LIMIT rows would be a biased sample. Day-level test: corr(censor rate, resolved edge) =
**+0.178, p = 0.076**; high-censor days edge +0.0410 vs low-censor days +0.0239. The correlation is
*positive* — if anything the censored rows would have been better, not worse — so the bias runs
against the finding rather than manufacturing it. Leave-one-month-out on the LIMIT arm keeps every CI
strictly positive (+0.0426 to +0.0594). This is suggestive, not proof; §5 gives the measurement that
would settle it.

### 2.5 A record defect in the estate's single most-cited surviving positive

"Discipline beats naive mixed" is published as **+18.9 (Feb) / +6.6 (AprMay) / +28.96 (JunJul)** and
described as the one positive stable across all three reads. Recomputed from the sealed payloads:

| window | discipline − mixed, **ACTUAL** basis | discipline − mixed, **WORST-CASE** basis | mixed censored / selected |
|---|---:|---:|---:|
| feb | **+18.911** | +37.283 | 18 / 360 (5.0 %) |
| aprmay | **+6.600** | +71.699 | 63 / 317 (19.9 %) |
| junjul | +2.743 | **+28.958** | 31 / 282 (11.0 %) |

> **Feb and AprMay are published on the ACTUAL basis; JunJul is published on the WORST-CASE basis.
> The three numbers are not the same statistic.** On one consistent basis the series is
> **+18.91 → +6.60 → +2.74 — a monotone collapse toward zero**, not a stable positive that jumped
> back up in the latest window. The JunJul JSON names its own field honestly
> (`window_stats.discipline_minus_mixed_worst_case_r`); the defect is in the prose that pooled the
> three into one series.

**What this does not license.** Repricing censors does **not** flip the JunJul verdict. The primary
gate (pooled worst case > −2 R) fails at −16.72 as booked, −12.18 at fair value, and −10.60 with
censors excluded entirely. The censoring rule is a large, real, recoverable distortion of the
*comparison between arms*; it is not the reason the MARKET rule was rejected.

---

## 3. (C) Is the process actually a martingale?

24 symbols × {M15, H4, D1} from `/Users/borr/GTOSActive/vps-bars-20260727` (M15 from 2024-01, H4/D1
to 2000 on FX), broker→UTC converted, Lo–MacKinlay heteroskedasticity-robust variance ratios by
session and volatility tertile. 1,536 cells: `lane1_receipts/VR_SURFACE_V1.csv`.

*(Method note: my first pass carried a spurious `n` in the Lo–MacKinlay `δ_j` and produced |z| < 0.4
everywhere. Corrected in `vr2.py`; the VR values were unaffected, only the z-statistics.)*

| tf | q | k | mean VR | median VR | cells \|z\|>1.96 | mean ac1 |
|---|---:|---:|---:|---:|---:|---:|
| M15 | 16 | 24 | 0.9474 | 0.9491 | — | −0.0156 |
| H4 | 6 | 24 | 0.9782 | 0.9766 | — | −0.0154 |
| D1 | 5 | 24 | 0.9454 | 0.9452 | — | −0.0291 |

**Verdict: the martingale null is correct at the horizons the estate trades.** VR sits within a few
percent of 1 across the whole surface, departures are uniformly VR < 1 (mild mean reversion), and
volatility regime barely moves it (M15 q=4: lo 0.971 / mid 0.974 / hi 0.972). This is the finding
that validates §1 — the fair-value null of `−E[cost_r]` is not an assumption, it is measured.

Independent corroboration from a different instrument: in §4's counterfactual walk the touch
probabilities are **scale-invariant** over a 16× change in barrier width with horizon scaled as k²
(pT 0.222→0.195, pS 0.499→0.472, pX 0.280→0.334). That is a diffusive process, measured across two
orders of magnitude of scale.

### 3.1 Where the process is **not** a martingale — ranked by |VR−1| × √n

| tf | symbol | q | session | n | VR | z | ac1 |
|---|---|---:|---|---:|---:|---:|---:|
| M15 | **CHFJPY** | 16 | late | 18,460 | **0.5608** | **−6.19** | −0.0938 |
| M15 | **EURGBP** | 16 | late | 17,971 | **0.6306** | **−5.26** | −0.1209 |
| M15 | EURJPY | 16 | late | 18,418 | 0.7306 | −3.02 | −0.0693 |
| M15 | NZDUSD | 16 | late | 18,158 | 0.7675 | −4.23 | −0.0657 |
| M15 | GBPJPY | 16 | late | 18,465 | 0.7753 | −2.74 | −0.0589 |
| M15 | USDCHF | 16 | late | 18,201 | 0.8110 | −3.26 | −0.0399 |
| M15 | USDCAD | 16 | late | 18,285 | 0.8231 | −2.21 | −0.0454 |
| M15 | GBPUSD | 16 | late | 18,297 | 0.8267 | −3.44 | −0.0480 |
| M15 | AUDUSD | 16 | late | 18,146 | 0.8384 | −2.47 | −0.0359 |
| M15 | BTCUSD | 16 | late | 25,311 | 0.8560 | −2.72 | −0.0219 |

**The entire non-martingale signature on the 24-symbol surface is one coherent cell: M15,
17:00–24:00 UTC, FX crosses, 4-hour horizon (q=16).** Indices and metals show nothing (JP225 1.095,
NAS100 1.076, GER40 1.072, XAUUSD 1.042, all |z| < 1.2).

### 3.2 The adversarial check on my own positive finding — the Roll bound

Negative autocorrelation in a thin session is the textbook signature of quote bounce, which is not
tradeable. Roll (1984): pure bounce on a martingale gives `cov(r_t, r_{t−1}) = −(s/2)²`. I inverted
that for an implied effective spread and compared it against the **true tick spread measured in the
same session** (`ROLL_BOUND_V1.csv`, `TICK_SPREADS_BY_SESSION_V1.csv`):

| | median across the 16 cells with VR < 0.95 |
|---|---:|
| Roll-implied spread (from ac1) ÷ true late-session spread | **3.02×** |
| Roll-implied spread (from VR) ÷ true late-session spread | **4.35×** |

**The reversion exceeds the bounce bound by ~3× in spread, ~9× in variance. It is not microstructure
noise.** Two caveats I am obliged to state: the bars are bid-based, so classic trade-price bounce
should not apply at all (which strengthens the reading); and the tick spreads come from
2026-06-18..07-24 while the VR spans 2024-01..2026-07, so a historically wider spread would narrow
the ratio — it would have to have been 3× wider to close it.

**Size of the prize.** For CHFJPY-late, implied σ(M15) ≈ 4.7 bp; the variance missing from VR(16)
corresponds to ≈ 12 bp of reverting amplitude over 4 hours against a 0.95 bp quoted spread. That is
a ~13:1 amplitude-to-cost ratio — the first cell in this program with that shape. It is *amplitude*,
not captured profit; capture requires timing, which is §5's experiment.

---

## 4. (D) The constructive conclusion

### 4.1 Which geometry has the most favourable fair value — measured, not argued

`cost_r = cost_price / risk_price`, so widening the stop mechanically shrinks cost in R. Across
width deciles of the real population, `cost_r` falls from 0.484 to 0.098 while `edge` is roughly flat
(mean +0.0309) and `realized` improves from **−0.406 to −0.109**. That looks like the answer, and it
is a composition artifact — different candidates, not the same candidate re-geometried.

So I ran the counterfactual directly: **the same 81,968 entries, barriers × k, horizon × k²** (the
diffusive scaling that holds the barrier/√time ratio fixed), walked on M15 bars.

| k | n resolved | pT | pS | pX | edge | cost | **net** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 77,689 | 0.222 | 0.499 | 0.280 | +0.1840 | 0.3123 | −0.1282 |
| 2 | 78,771 | 0.211 | 0.500 | 0.288 | +0.0803 | 0.1589 | −0.0786 |
| 4 | 78,979 | 0.209 | 0.501 | 0.291 | +0.0331 | 0.0797 | −0.0466 |
| 8 | 79,040 | 0.206 | 0.497 | 0.297 | +0.0117 | 0.0399 | −0.0282 |
| 16 | 79,067 | 0.195 | 0.472 | 0.334 | +0.0031 | 0.0200 | **−0.0169** |

> **Cost falls as 1/k almost exactly (ratios 1.97, 1.99, 2.00, 2.00). The edge falls FASTER
> (2.29, 2.43, 2.83, 3.77). Net improves monotonically toward zero and never crosses it.
> Widening the geometry cannot make this book profitable — the edge is a price-level quantity, and
> scaling the risk unit scales the edge and the cost down together.**

**Limitation, stated because it bounds the claim:** the k=1 control gives +0.184 against the sealed
M1 MARKET value of +0.0084. M15 is a materially coarser tape at the tightest geometry, so **use the
shape across k, not the level**. Anchoring k=1 at the sealed value and fitting the decay gives
break-even at roughly k ≈ 240 — i.e. a stop ~240× wider with a ~57,000× longer horizon. That is not
an engineering target; it is a refutation.

### 4.2 How much of the negativity is geometry+cost vs genuine anti-selection

Decomposing the pooled −0.2321 R/trade:

| component | R/trade | share |
|---|---:|---:|
| friction (the fair-value null, `−E[cost_r]`) | **−0.2630** | **113 %** |
| genuine skill against fair value (engine accounting) | +0.0309 | −13 % |
| — of which given back to true stop slippage | −0.0214 | |
| **genuine skill at tick truth** | **+0.0095** | |

> **All of the estate's measured negativity is geometry and cost. None of it is anti-selection.**
> There is no cell in the five-month population where the process loses to a coin flip by a
> significant margin, and eight of ten origin families beat it.

### 4.3 The queue, cheapest first

1. **Charge stop slippage to the fill, not as a deduction** (`quote_side.py:1420-1423`). Half a day.
   Makes the engine's gross tick-honest and makes every future edge measurement unimpeachable.
   The constant is already known and correct (0.02 vs measured 0.0214).
2. **Stop charging −1R for holes in your own M1 archive** (`pm_analysis.py:313`). One day. Worth
   **+0.47 R per fillable LIMIT candidate** in every arm comparison, and it is the reason the LIMIT
   arm was discarded. Replace with fair value (`−cost_r`) or exclusion, and re-report the three
   sealed reads on **one** basis (§2.5).
3. **Re-run the AprMay and JunJul reads with the LIMIT arm admitted** under the repaired censoring.
   The frozen MARKET-only rule sits on the arm with 6.4× less measured skill — and because order type
   is a deterministic function of origin family (`candidate_funnel_analysis.py:81`), that rule is in
   fact a blanket exclusion of `current_fvg_fill`, `current_ob_retest` and
   `current_breaker_re_entry`, the only three families that beat fair value. This is a re-scoring of
   existing sealed data, not a new window, and it spends no validation currency.
4. **The single cheapest experiment that converts §3 into a rule** — and it is the one I would run
   first:

> **Test a mean-reversion entry on M15 closes, 17:00–24:00 UTC, on the six FX crosses with
> VR(16) < 0.82 (CHFJPY, EURGBP, EURJPY, NZDUSD, GBPJPY, USDCHF), scored against the
> `−E[cost_r]` null rather than zero.**
>
> Every input already exists on this machine — bars at `/Users/borr/GTOSActive/vps-bars-20260727`,
> the resolver at `quote_side.py`, the null at §1.1. It reads **none** of the four never-funnel-read
> 2025 windows, so it costs no validation currency. It is the only place on the whole 24-symbol
> surface where the process is measurably not a martingale, the departure survives the Roll bound by
> 3×, and the amplitude-to-spread ratio is ~13:1.
>
> **And it is the exact opposite of what the estate trades.** The generating families are
> continuation and breakout shapes (`displacement_continuation`, `session_open_range_break`,
> `structural_distance_extreme`); the measured process in the one non-martingale cell is
> mean-reverting. That is a hypothesis nobody in this program has tested.

### 4.4 What would reverse each negative finding here

| finding | the measurement that would reverse it |
|---|---|
| widening geometry cannot pay (§4.1) | Re-run the k-ladder on the **M1** tape rather than M15. If the k=1 control then reproduces +0.0084 and the edge decays *slower* than 1/k, break-even moves into reach. My M15 walk cannot settle it. |
| edge not significant at tick truth (§2.3) | Extend the tick archive beyond 2026-06-18..07-24. The slippage estimate rests on 9,526 crossings in 5 weeks on the MARKET arm only; a LIMIT-arm and a wider-window measurement could move +0.0214 either way. |
| `liquidity_sweep_reclaim` has no edge (§1.3) | It is −0.0028 [−0.0326, +0.0268] — the CI admits up to +0.027. A cost-band-matched re-read on more months would separate it from zero in either direction. |
| censoring bias not proven benign (§2.4) | Resolve the 10,487 `CENSORED_ORDERING_AMBIGUITY` LIMIT rows **at tick resolution** on the June–July overlap. M1 is the engine's floor; ticks are one level finer and settle first-touch exactly. That is the direct test and the data is on disk. |
| the `moonshot_h20_21` cell (§1.3) | `pX = 0.000` on 874 trades is a clock artifact, not a result. Re-derive that bucket's boundaries against `broker_clock` before quoting its −0.2747. |

---

## 5. Provenance

- Population: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`, 632,934 rows.
- Prices/fills: `/private/tmp/laneG-walk/lg_{month}.pkl.gz`, 81,968 MARKET rows.
- Bars: `/Users/borr/GTOSActive/vps-bars-20260727/FTMO_{SYM}_{M15,H4,D1}.csv.gz`.
- Ticks: `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/`, broker→UTC via `new_york_plus_7`.
- Sealed payloads: `FEBRUARY_..._R2.json`, `APRIL_MAY_..._V1.json`, `JUNE_JULY_..._V1.json`.
- All CIs are 4,000-draw **cluster bootstraps on `trading_day`** (K = 100), seed 20260812; SEs are
  cluster-robust on the same key. Nothing here uses a naive i.i.d. SE.
