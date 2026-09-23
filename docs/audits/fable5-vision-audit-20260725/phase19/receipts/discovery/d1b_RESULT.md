# d1b — IS IT THE SLEEVES? An independent re-run of lane d1, and the mechanism

Lane d1, second pass, wave 19 broad-forensic. **This does not replace `d1_RESULT.md`; it
independently re-measures it.** Whole population, eight open windows, **1,118,694 candidate
emissions**, nothing sampled, nothing under `src/` edited, the three sealed 2025 windows
untouched.

Machine-readable: `d1b_SIGNAL_QUALITY_V1.json`. Tables also as text:
`D1B_FINAL.txt`, `D1B_PLACEBO.txt`, `D1B_TERCILE.txt`, `D1B_ATMKT.txt`, `D1B_EXTRA.txt`,
`D1B_CHEAP.txt`. Code: `d1b_rows.py`, `d1b_analyse3.py`, `d1b_entrycheck.py`, `d1b_placebo.py`.

---

## 0. THE ANSWER

**It is the sleeves, and the mechanism is a scale mismatch, not a defect.**

The broad V4 origin families do carry information — a real, month-stable, out-of-sample-stable
moment-selection value of **+0.03915 R/trade** (CI95 [+0.02908, +0.04893], p 0.0000) and a
marginal direction value of **+0.00784** (p 0.0447) on the seven at-market families. **Both
quantities, and the broker toll, rise together as the setup's stop tightens — and the toll rises
faster at every point on the curve.** Across ten broker-toll deciles the family's total measured
value never reaches **24.4 %** of its own toll; the pooled figure is **15.0 %**, i.e. **6.7×
short**, and in the three deciles where the toll is genuinely affordable (0.02–0.08 R, stops of
15–37 bps) the total value is **negative**. The information exists at a price scale finer than
the spread, and every part of the population where the spread is affordable carries nothing.

That is the mechanism the owner asked for, and it is the causal explanation of f2's cost-cap
sweep: capping cost keeps the wide-stop rows, and the wide-stop rows are the ones with no signal.

**The one reliably positive family is real and survives every control except the toll.**
`structural_distance_extreme` is gross-positive in **8 of 8** windows at **both** target
geometries, in both halves of the sample and in the two most recent windows alone
(+0.06170, p 0.0150) — and it pays **10.7 %** of its own toll. Its median stop is 3.17 bps
against a 2.62 bps round-trip cost.

**Two corrections to committed wave-19 artifacts, and one corpse of my own, are below.**

---

## 1. REPLICATION — the primary job of a re-run

An independently written harness (`d1b_rows.py`, 700 lines, sharing only the estate's `Tape`,
`CostModel` and `pbg_lib` loaders) reproduces both committed artifacts.

**Against `f1_BASELINE_V1.json`, under f1's own resting-limit contract — exact to 10 decimals:**

| f1 row | f1 published | this lane |
|---|---:|---:|
| roster, all emissions, gross | −0.024400982646910 | **−0.0244009826** |
| roster, all emissions, toll | +0.083179397186684 | **+0.0831793972** |
| roster, filled (n 331,548), gross | −0.082332672437182 | **−0.0823326724** |
| roster, filled, toll | +0.280660093127874 | **+0.2806600931** |
| roster, filled clean (n 298,537), gross | −0.013268637647645 | **−0.0132686376** |

Per-window emission counts match f1's day-restricted roster exactly in all eight windows
(169,624 / 147,120 / 134,298 / 151,002 / 126,931 / 127,932 / 132,137 / 129,650 = 1,118,694).

**Against `d1_RESULT.md` (pass 1), under its contract — to 3–4 decimals on every family:**

| family | pass 1 | this lane | pass 1 months+ | this lane |
|---|---:|---:|:---:|:---:|
| `structural_distance_extreme` | +0.06639 | **+0.06639** | 8/8 | **8/8** |
| `liquidity_sweep_reclaim` | +0.02747 | **+0.02754** | 5/8 | 5/8 |
| `cross_asset_lead_lag` | +0.02417 | **+0.02428** | 7/8 | 7/8 |
| at-market cohort | +0.02395 | **+0.02402** | 8/8 | **8/8** |
| `displacement_continuation` | +0.00791 | +0.00797 | 5/8 | 5/8 |
| `session_open_range_break` | +0.00250 | +0.00250 | 5/8 | 5/8 |
| whole clean roster | −0.00295 | −0.00289 | 4/8 | 4/8 |
| `regime_transition_break` | −0.00455 | −0.00455 | 3/8 | 3/8 |
| `current_ob_retest` | −0.00457 | −0.00476 | 3/8 | 4/8 |
| `current_fvg_fill` | −0.02213 | −0.02200 | 2/8 | 2/8 |
| POI cohort | −0.02381 | −0.02383 | 2/8 | 1/8 |
| `volatility_compression_expansion` | −0.03314 | −0.03284 | 2/8 | 2/8 |
| `current_breaker_re_entry` | −0.07964 | −0.08144 | 1/8 | 1/8 |

Direction values replicate too: at-market **+0.00787** (pass 1 +0.00780), POI **−0.03693**
(−0.03707), whole roster **−0.01732** (−0.01747), `current_breaker_re_entry` **−0.11727**
(−0.11630), its inverted arm **+0.15310** (+0.15304).

**Pass 1 is confirmed. Nothing in it needs to be withdrawn.** What follows is what it did not
measure.

---

## 2. CORRECTION 1 — f1's committed roster family table prices seven of ten families under the wrong order type

`f1_BASELINE_V1.json → roster.roster_family_pooled` applies the honest **resting-limit** contract
to all ten families. For the seven at-market families that is the wrong instrument, and it is
measurable rather than arguable: **their emitted entry price is EXACTLY the last print before the
decision instant.**

January 2026, whole roster, |entry − last close before the decision| in bps
(`D1B_ATMKT.txt`):

| family | n | p50 | p90 | p99 | as a fraction of its own R, p50 |
|---|---:|---:|---:|---:|---:|
| all seven at-market families | 17,455 | **0.0000** | **0.0000** | **0.0000** | **0.0000** |
| `current_fvg_fill` | 84,503 | 44.48 | 94.10 | 132.55 | 5.17 |
| `current_ob_retest` | 31,733 | 50.36 | 93.39 | 117.89 | 4.78 |
| `current_breaker_re_entry` | 12,232 | 41.80 | 88.35 | 109.27 | 5.30 |

A limit at the last print is a market order. Correcting the contract:

| family | limit contract (f1) | market contract | delta | CI95 |
|---|---:|---:|---:|---|
| `structural_distance_extreme` | +0.00687 | **+0.06639** | +0.05952 | [+0.05204, +0.06830] |
| `cross_asset_lead_lag` | **−0.01934** | **+0.02428** | +0.04361 | [+0.03610, +0.05105] |
| **at-market cohort** | **−0.00486** | **+0.02402** | **+0.02888** | **[+0.02654, +0.03118]** |
| `liquidity_sweep_reclaim` | +0.00273 | +0.02754 | +0.02482 | [+0.02190, +0.02796] |
| `displacement_continuation` | **−0.00645** | **+0.00797** | +0.01442 | [+0.01219, +0.01655] |
| `session_open_range_break` | **−0.00996** | **+0.00250** | +0.01245 | [+0.00878, +0.01606] |
| `volatility_compression_expansion` | −0.03992 | −0.03284 | +0.00708 | [+0.00322, +0.01057] |
| `regime_transition_break` | **−0.01142** | **−0.00455** | +0.00687 | [+0.00163, +0.01266] |

**Five of seven flip sign, and the cohort flips.** The contract choice is worth more
(+0.02888) than the entire at-market edge it decides (+0.02402).

**Mechanism, exactly:** of 135,803 at-market emissions, **92.14 % fill at the same bar under both
conventions and book −0.00337**; **6.91 % fill late under the limit** and book +0.15573 market
against −0.02172 limit; and **0.96 % (1,297 rows) a resting limit never fills at all** and they
book **+1.71403 R/trade** under the market contract. Those two thin slices carry +0.01226 and
+0.01637 of the +0.02402. **The at-market cohort's positive gross is entirely the rows where price
left the entry immediately** — which is exactly what a market order gets and a resting limit does
not.

**This is a correction to f1, not to d1 pass 1** — pass 1 already used the market contract.

---

## 3. CORRECTION 2 — the estate's standard side control is an artifact on POI families, so the unconditional POI direction test does not exist

The estate's direction control mirrors the geometry about the entry and re-walks (f2
PLACEBO-SIDE; d1 pass 1 COIN). That is exact wherever the fill is side-independent. **On a resting
POI limit it is not an order.** A buy limit at a level *below* the market mirrors into a sell at
the same level — marketable at once, at a price the book cannot get, with a stop already breached:

| cohort | real limit fill rate | **mirrored** limit fill rate | mirrored arm gross |
|---|---:|---:|---:|
| `current_fvg_fill` | 0.2272 | **0.9956** | **−0.94863** |
| `current_ob_retest` | 0.0701 | **0.9992** | **−0.98453** |
| `current_breaker_re_entry` | 0.1581 | **0.9881** | **−0.95418** |
| POI cohort | 0.1817 | **0.9960** | **−0.95835** |
| at-market cohort (the control is valid here) | 0.9904 | 0.9908 | −0.01935 |

Run per emission, that arm reports a POI "direction value" of **+0.47584** — pure artifact.
**Pass 1's conditioning on the real arm's fill is therefore forced by the instrument, not a
limitation of pass 1**, and its §8 limit 1 is closed by showing the alternative does not exist.

Every direction number in this lane uses the **ANTI-AT-THE-FILL** arm instead: at the instant
price reaches the level and the real order fills, take the opposite side from that same price with
the mirrored stop. Same price, same trigger, opposite side — and it is an order the broker accepts
(a **stop** order instead of a limit). For at-market rows it is the mirrored market order at the
same instant, so the two cohorts are measured on one construction.

---

## 4. THE MECHANISM — value and toll both rise with stop tightness, and the toll rises faster

At-market cohort, 135,713 fills, ten broker-toll deciles, target 2.0R (`D1B_FINAL.txt`).
**MOMENT** = real − a random instant on the same symbol, same trading day, same side, same risk
distance in bps (3 draws/row on the system's own 96-window grid, 99.93 % resolved).
**DIRECTION** = real − the coin flip at the same instant.

| decile | n | toll R | median stop (bps) | MOMENT | DIRECTION | M+D | (M+D)/toll |
|---|---:|---:|---:|---:|---:|---:|---:|
| D1 | 13,572 | 0.0217 | 37.35 | **−0.01928** | +0.00410 | **−0.01518** | −0.698 |
| D2 | 13,570 | 0.0491 | 19.97 | **−0.01722** | −0.01193 | **−0.02915** | −0.593 |
| D3 | 13,572 | 0.0766 | 14.96 | −0.00497 | −0.01221 | −0.01718 | −0.224 |
| D4 | 13,571 | 0.1079 | 11.70 | +0.01889 | −0.00322 | +0.01567 | +0.145 |
| D5 | 13,571 | 0.1439 | 9.16 | +0.02276 | +0.00254 | +0.02530 | +0.176 |
| D6 | 13,572 | 0.1907 | 7.05 | +0.04629 | +0.00024 | +0.04653 | **+0.244** |
| D7 | 13,571 | 0.2584 | 5.34 | +0.06286 | −0.00385 | +0.05900 | +0.228 |
| D8 | 13,570 | 0.3656 | 3.95 | +0.07024 | +0.01338 | +0.08361 | +0.229 |
| D9 | 13,572 | 0.5511 | 2.89 | +0.07628 | +0.01630 | +0.09259 | +0.168 |
| D10 | 13,572 | 1.3634 | 2.26 | **+0.13565** | **+0.07310** | **+0.20875** | +0.153 |
| **pooled** | **135,713** | **0.3129** | 9.93 | **+0.03915** | **+0.00784** | **+0.04699** | **+0.150** |

Pooled CIs: MOMENT [+0.02908, +0.04893] p 0.0000; DIRECTION [−0.00109, +0.01711] p 0.0447;
M+D [+0.02944, +0.06535] p 0.0000. At the generator's own 1.5R target: MOMENT +0.02751
(p 0.0000), DIRECTION +0.00598 (p 0.0712), (M+D)/toll +0.1071 — **every sign and ordering holds.**

> **Zero of ten deciles pays its own toll. The best is 4.1× short. The pooled cohort is 6.7×
> short. And the three deciles whose toll is affordable are the three with NEGATIVE value.**

(MOMENT and DIRECTION are measured against different nulls and are not strictly additive; the
M+D column is their sum, as pass 1 also reported. The MOMENT placebo draws instants uniformly on
the 96-window grid, so part of its value is "trades at liquid hours" rather than "picks the right
minute" — the same caveat pass 1 recorded.)

### 4.1 The same shape inside the one 8/8 family — and why R flatters it

`structural_distance_extreme`, risk-distance quintiles (`D1B_TERCILE.txt`):

| quintile | median stop (bps) | gross R | **direction value R** | p(≤0) | toll R |
|---|---:|---:|---:|---:|---:|
| Q1 | 1.324 | +0.17168 | **+0.10140** | **0.0000** | **1.1739** |
| Q2 | 2.120 | +0.10166 | **+0.04973** | **0.0150** | 0.6457 |
| Q3 | 3.167 | +0.03888 | −0.00022 | 0.4875 | 0.4511 |
| Q4 | 5.487 | +0.01500 | −0.02291 | 0.7665 | 0.3895 |
| Q5 | 12.769 | +0.00473 | −0.02692 | 0.8245 | 0.4559 |

**The family's entire directional content lives on rows whose stop is at or below the broker's own
round-trip cost** — Q1's toll is **117 % of its risk unit.** The at-market cohort shows the same
monotone shape (Q1 dirval +0.04302 p 0.0000 at toll 0.7341; Q2–Q4 zero or negative).

Consequence for how the estate reports: **R weights each row's price move by 1/d, so a family's
R-edge can be a stop-width effect.** Measured in price units, `structural_distance_extreme`'s
direction value is **−0.0350 bps** (CI [−0.2722, +0.2025]) against a **2.617 bps** toll —
indistinguishable from zero and slightly negative, on the family that looks best in R. The
at-market cohort in price units: gross +0.2155 bps, direction **+0.0605 bps**
(CI [−0.2332, +0.3546]) against **2.9950 bps** of toll → **49.5×** short (`D1B_EXTRA.txt`).

---

## 5. THE FIVE LANE QUESTIONS, ANSWERED

**Q1 — family economics.** §1's table, at both geometries, with per-window signs
(`d1b_SIGNAL_QUALITY_V1.json → family_economics`). At the generator's own **1.5R** target the
ordering is unchanged: `structural_distance_extreme` +0.04312 (8/8), `liquidity_sweep_reclaim`
+0.02111 (5/8), at-market cohort +0.01498 (8/8), whole roster −0.00884 (1/8),
`current_breaker_re_entry` −0.09592 (**0/8**).

**Q2 — does each family beat its own matched random control?** Three of ten do at p < 0.10:
`structural_distance_extreme` **+0.02022** (p 0.0875), `liquidity_sweep_reclaim` **+0.01774**
(p 0.0727), and the at-market cohort **+0.00787** (p 0.0445, 6/8 months). **Four are
significantly WORSE than random**: `current_breaker_re_entry` −0.11727,
`volatility_compression_expansion` −0.03436, `current_fvg_fill` −0.03393, POI cohort −0.03693
(all p(≥0) ≤ 0.009). The whole roster is **−0.01732**, p(≥0) 0.0012.

**Q3 — moments or direction?** Holding each family's own long/short mix fixed inside every
(window, symbol, broker-hour) cell, the at-market cohort's row-level direction call is
**+0.00187 at p 0.309 — nothing.** Exactly one family clears it: `structural_distance_extreme`
**+0.02601, p 0.0037**. The cohort's *lean* is worth +0.00441 (p 0.0045).
**So it is moments and a lean, not a per-setup direction call** — pass 1's finest cut, confirmed
on a differently-built control.

**Q4 — setup or schedule?** No family is a schedule. η² excess over each factor's own permutation
null, at-market cohort: symbol **−0.00001**, broker hour **+0.00042**, symbol×hour +0.00188,
vol tercile −0.00001, trend sign +0.00002, side +0.00004. The largest single schedule effect
anywhere is `volatility_compression_expansion`'s broker hour at +0.03374 — on a significantly
negative family. **New**: the **day** explains as much as or more than instrument and hour for
every cohort (at-market +0.00180 vs symbol −0.00001), so these families **co-move**; breadth
across 24 instruments and 10 families does not buy independence. That is a second, independent
route to AF's breadth refutation.

**Q5 — is any family reliably gross-positive across months?** **Yes, one.**
`structural_distance_extreme`: +0.06639 on 22,612 clean fills, **8/8 windows at 2.0R and 8/8 at
1.5R**, positive on **21 of 24** instruments, first four windows +0.07254 (p 0.0003), last four
+0.05985 (p 0.0080), **the two most recent windows alone +0.06170 (p 0.0150)**. Its spec layer is
positive on **both sides**: LONG +0.08644 (8/8, p 0.0003), SHORT +0.05558 (8/8, p 0.0015) — the
only spec in the estate positive on both sides at both geometries in every month.
**And it pays 10.7 % of its own toll.** Runners-up: `cross_asset_lead_lag` 7/8 (5.5 % of toll),
at-market cohort 8/8 (7.8 %).

---

## 6. THE BREAKER INVERSION, PRICED — and an artifact that must not be quoted

`current_breaker_re_entry` is the estate's one inverted detector. Priced on clean rows
(born-past-stop excluded), target 2.0R:

| arm | gross | toll | net | CI95 (net) | p(≤0) | months gross+ |
|---|---:|---:|---:|---|---:|:---:|
| as shipped | −0.08144 | 0.2410 | −0.32249 | — | — | 1/8 |
| **inverted** | **+0.15310** | 0.2410 | **−0.08795** | [−0.14767, −0.02972] | 0.9985 | 7/8 |
| inverted, 1.5R | +0.12925 | 0.2410 | −0.11180 | [−0.16515, −0.06094] | 1.0000 | 7/8 |

**Inverting it does not make it pay.** It is a signal-side repair, not an economic one — pass 1's
verdict, now with a CI.

> **Do not quote the whole-family inverted figure.** Including born-past-stop rows the inverted
> arm reads **+1.37402 gross / +1.09678 net on 32,668 rows**. That is mechanical: **68.01 % of
> this family's fills are born already past their stop**, and the mirror of a position born past
> its stop is born past its **target**, booking +2R by construction.

---

## 7. A RESULT I BUILT AND KILLED — published so nobody rebuilds it

Sorting the at-market cohort by broker toll first produced a **cheapest-toll decile booking
+0.17209 gross / +0.15356 net, positive in 8 of 8 months and on 16 of 16 instruments**, with a
direction value of +0.12843 (p 0.0000). It disagreed with f2's cost-cap sweep by an order of
magnitude at every tight cap (mine +0.06871 net at cap 0.05, f2's −0.02714), which is what made me
check it rather than publish it.

**It was my own bug.** The stored toll column is zero whenever the *resting-limit* arm did not
fill, and at-market families are priced on the *market* arm. So the **1,297 at-market rows a
resting limit never fills** — the same rows that book **+1.71403 R/trade** (§2) — all carried
`toll = 0` and sorted into the cheapest decile, contributing ≈ +0.164 of the +0.172.
**Recomputed from the market arm's own toll, that decile books +0.01302 gross and its direction
value is +0.00410 at p 0.357.** §4's table is the corrected one.

Three checks that came back clean and are worth recording, because each was a live hypothesis:

- **The entry convention is not an artifact.** Re-walking the at-market cohort with entry = the
  first achievable print at or after the decision (`open[i]`) instead of the shipped `close[i−1]`
  gives **+0.02202 (8/8)** against **+0.02105 (7/8)**. The signed gap between the credited and the
  achievable price is median **0.0000 bps**, mean **−0.0006 bps**, against a 9.98 bps median risk
  distance. Holding the risk distance instead of the stop price: +0.02034.
- **The 120-bar horizon is wall-clock, not printed-bar.** Median wall-clock span of 120 printed
  bars is exactly 120 minutes for all 24 instruments; M1 print density runs 0.596 (UKOIL) to 0.963
  (BTCUSD) and the walker bounds on `i + 120` regardless. No session-gap compression exists.
- **The at-market classification is exact** (§2's table): all seven families emit at the last
  print, at every percentile.

---

## 8. LIMITS

- MOMENT's placebo draws instants uniformly on the 96-window grid, including thin minutes; part of
  its value is liquidity-hour selection, not minute selection.
- The POI direction test is conditional on the real arm's fill **by necessity** (§3), so it is a
  statement about which side to take once price reaches the level — realizable as a stop order —
  not about POI candidates that never fill.
- The 2026-05 tape ends with the month, so a tail of its rows carries a truncated forward path
  (the estate's standing convention; f1, f2 and PB share it).
- All costs are the h1 FTMO four-term basis. f1 §6 row 9 records that the sealed arms' own cost
  model diverges from it on oil CFDs.
- η² is reported against each factor's own permutation null; the raw column must not be read alone.
- **Nothing here touched the sealed June/August/September 2025 windows.**
