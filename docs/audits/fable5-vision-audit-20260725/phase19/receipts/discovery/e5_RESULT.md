# Lane e5 — L2-F6 extended: does the adaptive stop, and its zero ceiling, travel?

**Posture: extension.** The finding handed over was L2-F6 — a per-row spread-floored stop
`k_i = max(1, c·spread_r)` plus a 0.25R trail recovers **+0.674 R/trade at frozen cost and
+0.224 at the corrected spread**, with a ceiling asserted to be **zero by algebra** because
`net_new(k) = (gross_price − cost_price)/(k·d)` and both numerator terms were "measured
k-invariant".

Three things were done: reproduce it exactly; measure the empirical premise the algebra
rests on; and carry the whole instrument to **February and March**, two months it was never
found on.

---

## 0. Reproduction — EXACT

`l2_13_combined.py` re-run at HEAD reproduces L2's published table to the last digit:

| rule | gross | win % | net FROZEN | net /7.3 |
|---|---:|---:|---:|---:|
| baseline k=1 | −0.12653 | 35.291 | −0.78888 | −0.30216 |
| S(20) + 0.25R trail | −0.01483 | 76.758 | **−0.11481** | **−0.07786** |

n = 24,142. Recovery +0.67407 frozen / +0.22430 corrected — L2's exact figures.
An independently written library (`e5_lib.py`) reproduces `l2_07_adaptive_stop.py` too:
S(10) net_frozen **−0.19976** against L2's published **−0.19983** (7e-5, storage rounding).

### 0.1 Instrument validation before extending

The extension needs paths for months that have none, so a builder was written
(`e5_build_month.py`) that reconstructs fill-honest R paths from the true-UTC M1 lane
sources under CQ's own contract (observations strictly after the decision minute, through
decision+120 min; `mkt_r_prev_close` = close of the last fully-closed bar strictly before
the decision minute, i.e. the open-stamping correction w0-capture established).

Rebuilt against January and compared bar for bar to CQ's sidecar:

| check | value |
|---|---|
| rows compared | **27,658 / 27,658** |
| unmatched | 0 |
| length mismatches | 0 |
| max abs diff, `fav` / `adv` / `cls` | **5e-05** each (= the 5-dp storage rounding) |
| rows with any diff > 1e-4 | **0** |
| `past_stop` count | 3,515 vs w0-capture's 3,516 (one boundary row) |
| `no_fill` count | 241, exact |

`E5_JAN_VALIDATION_V1.json`. The instrument is the same instrument.

### 0.2 What was spent

| window | source | status |
|---|---|---|
| January 2026 | `CJ_RECLOCKED_S0R0_POOL_V1` + CQ sidecar + `bridge_ftmo_m1_202601` | already spent |
| February 2026 | `CP_FEBRUARY_S0R0_POOL_V1` + `bridge_ftmo_m1_202602` | already read once (CP) |
| March 2026 | `FA2_M_R0_MISSED_OPPORTUNITY_LEDGER` + `bridge_ftmo_m1_202603` | already read once (fa2 March confirm). **Only the diagnostic pool was read** — the same object class as January's CJ pool. No trade ledger, no headline economics, no arm outcome. |
| **April 2026** | — | **NOT SPENT.** M1 sources exist (`bridge_ftmo_m1_202604`) but **no candidate pool exists** — no replay output. A paths-based extension is impossible without launching a sealed replay, which this lane may not do. |
| **May 2026** | — | **NOT SPENT**, same reason (`bridge_ftmo_m1_202605` present, no pool). |

New artifacts: `e5_january_WS_V1.jsonl.gz` (27,658), `e5_february_WS_V1.jsonl.gz` (24,239),
`e5_march_WS_V1.jsonl.gz` (26,484 of 130,004 ledger rows at the same scoreability gate —
20.4 %, against January's 18.03 %).

---

## 1. E5-F1 — the RULE replicates in all three months, and shrinks

Population per month: filled inside the walk, ex-`born_past_stop`.

| rule | JAN n=23,902 | FEB n=22,074 | MAR n=24,694 |
|---|---:|---:|---:|
| | gross / netFROZEN / net7.3 | | |
| baseline k=1 | −0.12784 / −0.79307 / −0.30375 | −0.12164 / −0.58616 / −0.25357 | −0.14078 / −0.54804 / −0.26063 |
| S(2) | −0.09982 / −0.41991 / −0.21960 | −0.10627 / −0.38800 / −0.20815 | −0.12324 / −0.38685 / −0.21837 |
| S(5) | −0.07599 / −0.28077 / −0.17027 | −0.08402 / −0.27008 / −0.16535 | −0.10468 / −0.28582 / −0.18208 |
| S(10) | −0.05700 / −0.19976 / −0.13401 | −0.06371 / −0.19396 / −0.12968 | −0.07911 / −0.20720 / −0.14245 |
| S(20) | −0.03949 / −0.13948 / −0.10255 | −0.04623 / −0.13586 / −0.09906 | −0.06280 / −0.15073 / −0.11366 |
| flat k=3 | −0.04214 / −0.27722 / −0.11411 | −0.04442 / −0.21260 / −0.10173 | −0.05312 / −0.20220 / −0.10640 |

**Recovery, S(20) vs baseline (no trail):**

| | frozen | /7.3 |
|---|---:|---:|
| January | **+0.65359** | **+0.20120** |
| February | **+0.45030** | **+0.15451** |
| March | **+0.39731** | **+0.14697** |

The effect **HOLDS in all three months and SHRINKS**: February is 69 % of January at frozen
cost (77 % corrected), March 61 % (73 %). The ladder is monotone in `c` in every month.
Most of the month-to-month shrinkage is the frozen cost base itself falling
(C_frozen 0.665 → 0.465 → 0.407) — the rule's leverage is proportional to the cost it
divides down.

---

## 2. E5-F2 — the CEILING claim replicates, and its premise is now measured

L2's premise is that `G(k)` (price-space gross, in original R units) is k-invariant. That
had never been measured over a ladder. It is now, over k ∈ {1, 1.25, … 100, ∞} and under
both target conventions:

* **Convention A** — structural price target held fixed while the stop moves (L2's own).
* **Convention B** — proportional target, moving to 2k when the stop moves to k.

| | JAN | FEB | MAR |
|---|---:|---:|---:|
| G_A range over the whole ladder | **0.01314** | 0.02314 | 0.04199 |
| G_A min … max | −0.13171 … −0.11819 | | |
| G_B range | **0.05866** | 0.02716 | 0.04396 |
| G_B min … max | −0.12795 … −0.06933 | | |
| C_frozen | 0.66516 | 0.46446 | 0.40726 |
| C /7.3 | 0.17591 | 0.13193 | 0.11985 |
| **max_k G − C/7.3** | **−0.24524** | **−0.24475** | **−0.21676** |

**Verdict: the ceiling is zero — confirmed in all three months — but not for the stated
reason.** `G(k)` is *not* invariant; it moves by up to **0.0587 R** once the target is
allowed to scale with the stop, which is 4.5× the movement under L2's fixed-target
convention. The premise is convention-dependent. The claim survives anyway because the
movement is an order of magnitude smaller than the cost gap it would have to close.

Two by-products of the same ladder, January, price space:

* **The 2R target cap costs +0.0461 R/trade.** With no stop at all, capping winners at the
  structural 2R gives G = −0.1251; removing the cap gives −0.0790.
* At k ≥ 20 under convention A the stop fires on **0.25 %** of rows and the outcome mix is
  frozen at 27.1 % target / 72.6 % mark — there is nothing left to buy by widening further.

Full ladders: `E5_JAN_CEILING_V1.json`, `E5_THREE_MONTHS_V1.json → ladder_A / ladder_B`.

---

## 3. E5-F3 — THE RECOVERY FACTORISES, AND THE STOP MOVE ITSELF IS WORTH ZERO

This is the sharpest thing this lane found. L2 *inferred* "loss reduction identical to
trading smaller" from the algebra. With the per-row `k_i` in hand the recovery splits into
three exactly additive parts:

```
SHRINK = mean[(R_i(1)    − c_i)/k_i] − mean[R_i(1) − c_i]     same outcome, smaller bet
WIDEN  = mean[(R_i(k_i)  − c_i)/k_i] − mean[(R_i(1) − c_i)/k_i]   the stop move itself
TRAIL  = mean[(R_i(k_i,trail) − c_i)/k_i] − mean[(R_i(k_i) − c_i)/k_i]
```

**FROZEN cost, 15 rule × month cells:**

| rule | month | k_med | as-shipped | SHRINK | **WIDEN** | TRAIL | total |
|---|---|---:|---:|---:|---:|---:|---:|
| S(2) | jan | 1.00 | −0.79307 | +0.38143 | **−0.00544** | +0.04062 | +0.41661 |
| S(2) | feb | 1.00 | −0.58616 | +0.20420 | **−0.00404** | +0.03937 | +0.23953 |
| S(2) | mar | 1.00 | −0.54804 | +0.16584 | **−0.00299** | +0.05444 | +0.21730 |
| S(5) | jan | 1.00 | −0.79307 | +0.51976 | **−0.00181** | +0.03411 | +0.55206 |
| S(5) | feb | 1.00 | −0.58616 | +0.32599 | **−0.00528** | +0.03134 | +0.35205 |
| S(5) | mar | 1.00 | −0.54804 | +0.27228 | **−0.00607** | +0.04669 | +0.31290 |
| S(10) | jan | 1.62 | −0.79307 | +0.60206 | **−0.00057** | +0.03285 | +0.63434 |
| S(10) | feb | 1.28 | −0.58616 | +0.40126 | **−0.00187** | +0.02470 | +0.42408 |
| S(10) | mar | 1.24 | −0.54804 | +0.34979 | **−0.00221** | +0.03495 | +0.38253 |
| S(20) | jan | 3.23 | −0.79307 | +0.66244 | **+0.00208** | +0.02471 | +0.68924 |
| S(20) | feb | 2.55 | −0.58616 | +0.46066 | **−0.00021** | +0.01701 | +0.47746 |
| S(20) | mar | 2.49 | −0.54804 | +0.41122 | **−0.00394** | +0.02768 | +0.43497 |
| k=3 flat | jan | 3.00 | −0.79307 | +0.52872 | **+0.00047** | +0.02133 | +0.55052 |
| k=3 flat | feb | 3.00 | −0.58616 | +0.39078 | **−0.00387** | +0.01983 | +0.40673 |
| k=3 flat | mar | 3.00 | −0.54804 | +0.36536 | **−0.00619** | +0.02503 | +0.38419 |

**At the corrected spread:**

| rule | month | as-shipped | SHRINK | WIDEN | TRAIL | total |
|---|---|---:|---:|---:|---:|---:|
| S(10) | jan | −0.30375 | +0.17847 | −0.00057 | +0.03285 | +0.21076 |
| S(10) | feb | −0.25357 | +0.13294 | −0.00187 | +0.02470 | +0.15577 |
| S(10) | mar | −0.26063 | +0.12713 | −0.00221 | +0.03495 | +0.15987 |
| S(20) | jan | −0.30375 | +0.21005 | +0.00208 | +0.02471 | +0.23684 |
| S(20) | feb | −0.25357 | +0.16487 | −0.00021 | +0.01701 | +0.18166 |
| S(20) | mar | −0.26063 | +0.16088 | −0.00394 | +0.02768 | +0.18463 |

**WIDEN never exceeds 0.7 % of the recovery in magnitude and is NEGATIVE in 13 of 15
cells.** L2-F6's characterisation is not merely defensible — it is exact to three decimal
places, in three independent months. **The spread-floored stop, considered as a stop, does
nothing at all. 87–99 % of its published value is bet-size reduction; the remaining 3–13 %
is the trail, which is a different lever entirely.**

### 3.1 Where the stop move IS worth something (and how little)

Per-family and per-symbol `WIDEN` for S(10). Three cohorts are positive in all three months:

| cohort | JAN | FEB | MAR |
|---|---:|---:|---:|
| family `current_breaker_re_entry` | +0.00573 | +0.02490 | +0.03757 |
| symbol GER40 | +0.02739 | +0.01093 | +0.03461 |
| symbol CHFJPY | +0.00843 | +0.01885 | +0.01056 |

Worst by minimum: JP225 −0.03111, EURJPY −0.02737, AUDJPY −0.02666. `USOIL_cash`,
`UKOIL_cash`, `BTCUSD` are exactly 0.00000 because their `spread_r` never trips the floor,
so `k_i = 1` on every row.

---

## 4. E5-F4 — the SHRINK is NOT purely mechanical: 19–54 % of it is genuine cost targeting

The shrink term factorises again. With `w_i = 1/k_i` and `x_i = R_i(1) − c_i`:

```
mean(w·x) − mean(x) = mean(x)·(mean(w) − 1)   +   cov(w, x)
                      ^ MECHANICAL                ^ TARGETING
```

The first term is what *any* uniform down-sizing of a negative book yields. The second is
only nonzero if cost-based sizing down-weights the rows that were actually worse.

**Corrected spread, all 12 cells:**

| month | rule | mean_w | total | mechanical | **targeting** | targeting % |
|---|---|---:|---:|---:|---:|---:|
| january | S(2) | 0.8591 | +0.09241 | +0.04280 | **+0.04962** | 53.69 |
| january | S(5) | 0.7174 | +0.14094 | +0.08583 | **+0.05511** | 39.10 |
| january | S(10) | 0.5915 | +0.17847 | +0.12407 | **+0.05441** | 30.48 |
| january | S(20) | 0.4533 | +0.21005 | +0.16605 | **+0.04400** | 20.95 |
| february | S(2) | 0.9003 | +0.05145 | +0.02528 | **+0.02617** | 50.86 |
| february | S(5) | 0.7687 | +0.09813 | +0.05864 | **+0.03948** | 40.24 |
| february | S(10) | 0.6409 | +0.13294 | +0.09105 | **+0.04189** | 31.51 |
| february | S(20) | 0.4925 | +0.16487 | +0.12869 | **+0.03618** | 21.94 |
| march | S(2) | 0.9168 | +0.04691 | +0.02169 | **+0.02522** | 53.76 |
| march | S(5) | 0.8004 | +0.08861 | +0.05202 | **+0.03658** | 41.29 |
| march | S(10) | 0.6627 | +0.12713 | +0.08791 | **+0.03921** | 30.85 |
| march | S(20) | 0.5011 | +0.16088 | +0.13003 | **+0.03085** | 19.18 |

**`cov(1/k, net)` is +0.031 to +0.055 R/trade and positive in every one of the 12 cells.**
This is a real, replicating, non-mechanical component that L2's algebra explicitly denied.
It says the R-denominated cost term is a genuinely informative pre-trade feature: expensive
rows really are worse rows, by more than their cost. It is capped at ~+0.055 R/trade, so it
does not change the sign either — but it is the correct thing to build a *sizing* rule on,
and its magnitude peaks at S(5)–S(10), not at S(20).

---

## 5. E5-F5 — the TRAIL is the only exit lever that survives a control, replicates 3/3, and is
half illusion

The trail is the one non-shrink component. Two controls.

**Control 1 — the best FIXED-TIME exit.** If the trail only helps because it exits sooner
in a negatively-drifting instrument, some fixed `t` should match it. Price space, stop −1R,
structural target:

| t (bars) | JAN | FEB | MAR |
|---:|---:|---:|---:|
| 1 | −0.14507 | −0.15289 | −0.14088 |
| 10 | −0.14081 | −0.14879 | −0.13800 |
| 45 | −0.13622 | −0.13834 | **−0.13534** |
| 90 | −0.12874 | −0.13065 | −0.13882 |
| 120 (as shipped) | **−0.12784** | **−0.12164** | −0.14078 |
| **best fixed time** | t=120, +0.00000 | t=120, +0.00000 | t=45, +0.00544 |
| **trail 0.25R** | **−0.08080 (+0.04704)** | **−0.08008 (+0.04156)** | **−0.08187 (+0.05891)** |

No fixed time comes close. The trail is not a holding-time effect.

**Control 2 — holding-time-matched permutation.** Exit each trade at a bar *drawn from the
trail's own exit-bar distribution*, independent of that trade's path: same marginal holding
time, zero path information. 200 draws, seed 20260806.

| | JAN | FEB | MAR |
|---|---:|---:|---:|
| trail 0.25 observed | −0.08080 | −0.08008 | −0.08187 |
| permutation control mean | −0.13916 | −0.14395 | −0.13849 |
| **excess over control** | **+0.05836** | **+0.06386** | **+0.05663** |
| p (draws ≥ observed / 200) | **0.0000** | **0.0000** | **0.0000** |

**The trail carries real path information in all three months, 0/200 in every one.**

**Trail ladder — monotone, tighter is better, down to the smallest measured (0.1R):**

| trail | JAN G (Δ) | FEB G (Δ) | MAR G (Δ) | median exit bar |
|---|---:|---:|---:|---:|
| 0.10 | −0.02389 (+0.10395) | −0.02523 (+0.09641) | −0.02664 (+0.11414) | 9–10 |
| 0.15 | −0.04829 (+0.07955) | −0.04621 (+0.07543) | −0.04909 (+0.09169) | 12–14 |
| 0.20 | −0.06756 (+0.06028) | −0.06850 (+0.05314) | −0.06463 (+0.07615) | 16–17 |
| 0.25 | −0.08080 (+0.04704) | −0.08008 (+0.04156) | −0.08187 (+0.05891) | 19–21 |
| 0.35 | −0.09176 (+0.03608) | −0.09307 (+0.02857) | −0.10308 (+0.03770) | 25–27 |
| 0.50 | −0.10977 (+0.01807) | −0.10492 (+0.01672) | −0.11876 (+0.02202) | 33–36 |
| 0.75 | −0.11626 (+0.01157) | −0.11037 (+0.01127) | −0.13232 (+0.00846) | 44–48 |
| 1.00 | −0.12030 (+0.00754) | −0.11643 (+0.00521) | −0.13590 (+0.00488) | 50–56 |

At 0.1R the pool gross is −0.02389 / −0.02523 / −0.02664 — **three independent months
agreeing within 0.003 R.** Break-even stops are worth nothing by comparison (+0.0028 /
+0.0024 / +0.0156 at be=0.25R, and ≤ +0.002 at every wider level).

**And now the caveat that halves it — §6.**

---

## 6. E5-F6 — A SUBSTRATE DEFECT THE WHOLE SWARM IS CARRYING: the fill bar is over-credited

`w0_ws.walk(require_fill=True)` starts the walk at the first bar whose adverse extreme
reaches `entry_price`, and then credits **that same bar's full favourable extreme**. For a
limit resting on the far side of the market, that assumes the bar's high came *after* the
fill. For a limit being approached from above (a long limit below market), the opposite
ordering is the likelier one.

Three conventions, all with the conservative same-bar stop rule:

* **V0** — as measured today (fill bar's favourable extreme credited)
* **V1** — favourable excursion credited only from the bar *after* the fill bar; the fill
  bar can still stop you out. The honest lower bound.
* **HYBRID** — V0 on `born_at_limit` and `born_marketable` (where the entry *is* the market
  price, so the bar genuinely follows the fill) and V1 on `born_resting` only. **This is the
  correct convention** and it is what the numbers below use.

Born census under the hybrid (ex-past-stop): January 14,681 at_limit / 7,945 resting /
1,257 marketable; February 13,642 / 7,015 / 1,417; March 14,621 / 8,461 / 1,612.

**The trail's value under each convention (POOL, trail 0.10 minus as-shipped, /7.3):**

| convention | JAN | FEB | MAR |
|---|---:|---:|---:|
| V0 (as the swarm measures it) | +0.10395 | +0.09641 | +0.11414 |
| **HYBRID (correct)** | **+0.07345** | **+0.05778** | **+0.07570** |
| V1 (conservative bound) | +0.05027 | +0.03850 | +0.05861 |

**30–40 % of the measured trail value is the fill-bar ordering assumption.** The trail
survives — it is still +0.058 to +0.076 R/trade and still beats every fixed-time control —
but any lane quoting a trail, break-even, or scale-out number off `w0_ws.walk` is carrying
this. On XAUUSD it is worth **+0.129 / +0.182 / +0.199 R/trade**, i.e. it is the entire
result there. The as-shipped contract is barely affected (POOL V0 −0.30375 vs hybrid
−0.30532 in January) because without a trail the fill bar's high rarely decides anything;
**it is specifically the tight-trail family that the convention inflates.**

---

## 7. E5-F7 — the BOUNDARY. One cell in 720 clears its own cost, and it is +0.073 R/trade

### 7.1 Symbol level, unstopped 2-hour mark (the limit case of L2-F6's own lever)

Pre-specified rule R2: no stop, no target, mark at the 2-hour horizon. Gap = G − C/7.3.
The beta control is the LONG/SHORT split; a directional edge must show on both sides.

| symbol | JAN gap | FEB gap | MAR gap | both sides + |
|---|---:|---:|---:|---|
| XAUUSD | **+0.1221** | **+0.2019** | −0.0261 | never (Jan long +0.413 / short −0.065) |
| GER40 | **+0.0880** | −0.1136 | −0.1545 | **January only** |
| XAGUSD | −0.0547 | −0.1192 | −0.0397 | |
| EURUSD | −0.1407 | −0.2485 | −0.0462 | |
| US30_cash | −0.0801 | −0.1421 | −0.2275 | |
| JP225 | −0.1048 | −0.8086 | −0.2332 | |
| BTCUSD | −0.1901 | −0.7550 | −0.3148 | |
| NAS100 | −0.5956 | −0.2742 | −0.6999 | |
| … 16 more, all negative in all three months | | | | |

**No symbol is positive in all three months. No symbol passes the both-sides control in
more than one month.** GER40's January result — the only cell where the unstopped mark beat
cost on both sides — is **LOCALIZED TO JANUARY** (+0.0880 → −0.1136 → −0.1545).

Same at family level: `current_breaker_re_entry` +0.1978 both-sides in March only;
`structural_distance_extreme` +0.0513 in March after −0.4266/−0.5033; `current_ob_retest`
+0.0144 both-sides in February only. **No family is positive in more than one month.**
Same at session level: the most stable are `london` (−0.153/−0.146/+0.050) and
`moonshot_h10_11` (−0.121/−0.108/−0.095) — consistently the least negative, never crossing.

### 7.2 The one survivor, under every control

Trailed 0.25R, net at the corrected spread, **V0 convention**, all 24 symbols:

| symbol | JAN | FEB | MAR | min | 3/3 positive | months both-sides + |
|---|---:|---:|---:|---:|---|---:|
| **XAUUSD** | **+0.0889** | **+0.0713** | **+0.0992** | **+0.0713** | **YES** | **3** |
| XAGUSD | −0.0614 | −0.0334 | −0.1061 | −0.1061 | | 0 |
| GER40 | −0.1614 | −0.1575 | −0.1780 | −0.1780 | | 0 |
| … 21 more, all negative in all three months, down to NAS100 −0.5458 | | | | | | |

XAUUSD detail (V0): bootstrap CI95 [+0.0623, +0.1161] / [+0.0434, +0.0987] / [+0.0741,
+0.1226] — all exclude zero. LONG +0.1777/+0.1316/+0.1327, SHORT +0.0041/+0.0252/+0.0630.
At trail 0.10: +0.1651/+0.1655/+0.1822. Positive even at the **frozen** spread
(+0.1156/+0.1155/+0.1091). Break-even spread divisor 0.33/0.33/0.44 — it would still clear
at 2.3–3.0× the already-overcharged frozen spread. Median +0.165/+0.178/+0.187 (not
tail-driven; top-5 % carry 39–49 % of total). **55 of 63 trading days positive**
(18/21, 17/20, 20/22). Robust to +0.05R of extra exit slippage (+0.115/+0.115/+0.132).

### 7.3 It is one CELL, not a symbol — and de-duplication makes it stronger

The whole of it is **XAUUSD × `current_fvg_fill`**. XAUUSD's other seven families are
−0.0568 / −0.0289 / −0.0449.

| cut | JAN | FEB | MAR |
|---|---:|---:|---:|
| as emitted | n=1,500 **+0.28446** CI[+0.250,+0.316] | n=1,564 **+0.25061** CI[+0.220,+0.280] | n=1,697 **+0.27638** CI[+0.249,+0.301] |
| first emission only (w0-F1) | n=290 **+0.32858** CI[+0.253,+0.403] | n=271 **+0.36808** CI[+0.305,+0.437] | n=328 **+0.34214** CI[+0.286,+0.398] |
| one row per setup-day | n=304 **+0.32751** | n=283 **+0.34463** | n=341 **+0.33664** |

The pseudo-replication control **strengthens** it (the repeats dilute, they do not create
it), and the three de-duplicated point estimates agree within **0.017 R** across three
independent months. The same `current_fvg_fill` cell on every other symbol is negative:
BTCUSD −0.670/−0.336/−0.405, NAS100 −0.601/−0.441/−0.524, SPX500 −0.509/−0.409/−0.391,
UK100 −0.257/−0.201/−0.188, GER40 −0.124/−0.137/−0.132, US30 −0.157/−0.204/−0.176,
JP225 −0.245/−0.159/−0.142, ETHUSD −0.650/−0.452/−0.511. (XAGUSD +0.058/+0.164 on n=22/16 —
too thin to read.)

### 7.4 …and then the fill-bar convention takes most of it away

**XAUUSD × `current_fvg_fill`, one row per setup-day, HYBRID convention, trail 0.10:**

| | JAN | FEB | MAR |
|---|---:|---:|---:|
| n | 304 | 283 | 341 |
| as-shipped contract, /7.3 | −0.19014 | −0.02218 | −0.05022 |
| **trail 0.10, /7.3** | **+0.10346** | **+0.07316** | **+0.04231** |
| bootstrap CI95 (1,000) | **[+0.024, +0.181]** | [−0.010, +0.154] | [−0.031, +0.117] |
| trail 0.10, FROZEN | +0.04446 | +0.01003 | **−0.04603** |
| price-space G | +0.15582 | +0.12066 | +0.09283 |
| positive share | 70.4 % | 71.7 % | 68.0 % |

**This is the honest size of the only surviving cell: ~+0.073 R/trade averaged over three
months, on ~310 setups per month, consistently signed in all three, individually
significant in January only, and dependent on the spread correction being real.**
At symbol level under the hybrid, XAUUSD as a whole is +0.0362 (CI [+0.008,+0.062]) /
−0.0170 / −0.0168 — i.e. **the symbol does not survive; only the cell does.**

---

## 8. E5-F8 — the full repair stack, per month, at constant bet size

Every step is a per-trade R number at the original risk unit, so the steps are additive and
none of them is a disguised position-size change. V0 convention (as the swarm measures).

| step | JAN n / net / Δ | FEB n / net / Δ | MAR n / net / Δ |
|---|---|---|---|
| 0 as shipped, full pool, frozen | 27,658 / **−0.89988** | 24,239 / **−0.63315** | 26,484 / **−0.59320** |
| 1 drop `born_past_stop` | 24,143 / −0.78891 / **+0.11097** | 22,412 / −0.58209 / **+0.05106** | 24,958 / −0.54587 / **+0.04733** |
| 2 require fill | 23,902 / −0.79307 / −0.00416 | 22,074 / −0.58616 / −0.00407 | 24,694 / −0.54804 / −0.00217 |
| 3 corrected spread /7.3 | 23,902 / −0.30375 / **+0.48932** | 22,074 / −0.25357 / **+0.33260** | 24,694 / −0.26063 / **+0.28741** |
| 4 trail 0.25R | 23,902 / −0.25671 / +0.04704 | 22,074 / −0.21201 / +0.04156 | 24,694 / −0.20171 / +0.05891 |
| 5 trail 0.10R | 23,902 / −0.19980 / +0.05691 | 22,074 / −0.15716 / +0.05485 | 24,694 / −0.14649 / +0.05522 |
| 6 cheapest 30 % by total cost | 7,170 / **−0.02197** / +0.17784 | 6,622 / **−0.04075** / +0.11641 | 7,408 / **−0.06130** / +0.08519 |
| 7 …and XAUUSD only | 1,964 / **+0.16865** | 1,719 / **+0.12815** | 1,368 / **+0.12290** |
| S(10) shrink applied on top of step 5 (per NEW risk unit) | −0.06932 | −0.06411 | −0.06377 |

**Everything the estate knows, stacked, still lands 0.022–0.061 R/trade short of zero.**
The two largest single steps are not exit policy at all — they are the frozen-cost defect
(+0.29 … +0.49) and the born-past-stop artifact (+0.047 … +0.111).

---

## 9. E5-F9 — entry-side selection cannot cross zero out of sample either

L2-F6's ceiling argument is about *exit* levers, which only change how much of a
negatively-drifting instrument you hold. Entry selection is a different operator. Protocol:
threshold chosen on **January**, applied unchanged to February and March.

| exit \| selector | q (chosen on Jan) | JAN | FEB | MAR | mean FEB+MAR |
|---|---:|---:|---:|---:|---:|
| trail0.10 \| cheapest total cost | 0.30 | **−0.02197** | −0.04075 | −0.06130 | **−0.05103** |
| as-shipped \| cheapest total cost | 0.02 | −0.03124 | −0.09234 | −0.08245 | −0.08739 |
| trail0.10 \| cheapest spread_r | 0.40 | −0.09456 | −0.08374 | −0.09255 | −0.08815 |
| trail0.25 \| cheapest total cost | 0.30 | −0.06341 | −0.08147 | −0.10841 | −0.09494 |
| trail0.10 \| widest stop % of price | 0.02 | −0.02674 | −0.06837 | −0.18222 | −0.12529 |
| trail0.25 \| widest stop % of price | 0.02 | −0.04684 | −0.08098 | −0.17225 | −0.12661 |
| as-shipped \| widest stop % of price | 0.02 | −0.00758 | −0.08224 | −0.17932 | −0.13078 |
| … 11 more, all more negative | | | | | |

**All 18 exit × selector combinations are negative out of sample.** The best in-sample
January cell (−0.0076, widest-stop 2 %) degrades to −0.082/−0.179. The best out-of-sample
survivor is the cheap-cost + tight-trail stack at −0.041/−0.061 — the same stack as step 6
above.

---

## 10. Side findings worth carrying forward

**E5-F10 — the `born_past_stop` artifact is JANUARY-HEAVY.** w0-capture measured 12.72 % of
the January pool. February is **7.54 %** (1,827 / 24,239) and March **5.76 %** (1,526 /
26,484). Its removal is worth +0.11097 / +0.05106 / +0.04733 R/trade at frozen cost. The
defect is real in all three months; its published magnitude is a January number.

**E5-F11 — the pool's long/short asymmetry REVERSES between January and March**, so any
symbol- or family-level result carried by one side is month-specific market drift, not edge:

| month | n LONG | G_long | n SHORT | G_short |
|---|---:|---:|---:|---:|
| january | 10,685 | **+0.0166** | 13,217 | −0.1563 |
| february | 10,203 | −0.0377 | 11,871 | −0.2201 |
| march | 12,502 | −0.2184 | 12,192 | **+0.0089** |

This is what kills XAUUSD's raw +0.168 unstopped January number (long +0.413, short −0.065)
and every other single-sided cell in §7.1.

**E5-F12 — "the stop is killing it" is a January-only statement, and small.** No-stop-no-
target 2-hour mark vs the shipped −1R stop, price space:

| month | no stop (C0) | shipped stop (C1) | shipped stop+target (C2) | stop costs | full contract costs |
|---|---:|---:|---:|---:|---:|
| january | −0.07904 | −0.11799 | −0.12784 | **+0.03895** | +0.04880 |
| february | −0.13577 | −0.11744 | −0.12164 | **−0.01833** | −0.01413 |
| march | −0.10622 | −0.10409 | −0.14078 | **−0.00213** | +0.03456 |

The stop *helps* in February and is neutral in March.

**E5-F13 — the placebo design note.** A "shuffled paths within symbol" null (N3) was run and
is **uninformative by construction** — re-pairing side-signed paths with other rows'
geometry is a mean-preserving permutation, and it returned p≈0.5 and excess ≈0.000 in every
cell, exactly as it must. It is recorded so nobody re-runs it. The random-sign null (N2)
*is* informative — observed is above it at 0/200 in every cell — but its own mean is
−0.10 to −0.17 rather than 0, because flipping the side changes which bar counts as the
fill, so it is not a clean zero-centred null either. **The fixed-time and holding-time-
matched-permutation controls in §5, and the fill-bar bound in §6, are the ones that carry
weight.**

---

## 11. Verdict on the handed-over finding

| L2-F6's claim | verdict | evidence |
|---|---|---|
| the rule recovers +0.674 frozen / +0.224 corrected | **REPRODUCED EXACTLY** | §0 |
| it replicates elsewhere | **HOLDS, SHRINKING** — Feb 69 %/77 %, Mar 61 %/73 % of January | §1 |
| both numerator terms are k-invariant | **PARTLY FALSE** — invariant to 0.013–0.042 R under the fixed-target convention, but moves up to 0.059 R once the target scales | §2 |
| the ceiling is zero | **HOLDS IN ALL THREE MONTHS AT POOL LEVEL** — max_k G − C/7.3 = −0.245 / −0.245 / −0.217 | §2 |
| it is "loss reduction identical to trading smaller" | **CONFIRMED AND SHARPENED** — measured factorisation puts WIDEN at −0.0062…+0.0021 (13/15 cells negative), i.e. the stop move is worth *nothing*; 87–99 % is bet size | §3 |
| …"not edge" | **REFINED** — 19–54 % of the shrink is `cov(1/k, net)` = +0.031…+0.055 R/trade, a genuine cost-targeting term, positive in all 12 cells | §4 |
| (unstated) the trail is incidental | **REFUTED** — it is the only lever that beats a holding-time-matched control (p = 0/200, 3/3 months), worth +0.058…+0.076 R/trade under the correct fill convention | §5, §6 |

**Where the ceiling is NOT zero:** exactly one cell out of 24 symbols × 10 families ×
3 months — **XAUUSD × `current_fvg_fill` with a tight trail, +0.073 R/trade on ~310
setups/month**, positive in all three, significant in one.

---

## 12. What would make this bankable

The XAUUSD × `current_fvg_fill` × tight-trail cell is the only thing here worth money, and
it is **not** bankable today. In priority order:

1. **The fill-bar ordering must be resolved with ticks, not assumed.** The cell is
   +0.328 under V0 and +0.103 under the hybrid — a 3.2× swing that is entirely an intrabar
   assumption. The tick sources for January are already in the lane hold
   (`sources/ticks/`, 12 symbols). Replaying ~930 XAUUSD fvg fills against ticks settles
   whether the bar high preceded or followed the limit fill and collapses the range to one
   number. **This is the single highest-value next measurement in the lane.** Until it is
   done the cell's size is unknown to within a factor of three.
2. **A third and fourth out-of-sample month.** April and May M1 sources exist in the lane
   hold but **no candidate pool does**, so this needs a replay to generate the fvg
   candidates — not a data fetch. Absent that, the cell has n≈310/month × 3 months and one
   significant month.
3. **The spread correction must be ratified as an economic input, not a research note.**
   The cell is +0.103/+0.073/+0.042 at /7.3 and +0.044/+0.010/**−0.046** at frozen. Its sign
   in March depends entirely on which spread is true. The corrected spread is measured
   (7.3–8.5×) but the frozen model is what every published economic figure still uses.
4. **Execution realism for a 0.1R trail on gold.** The trail's value is monotone in
   tightness down to the smallest level measured, which is the classic signature of a rule
   that will be eaten by microstructure. XAUUSD's corrected `spread_r` is ≈0.008 R, so a
   0.1R trail is ≈12× the true spread — comfortable — but the exit is a market order at a
   local extreme and the flat 0.02 R slippage allowance is the pool's own constant, not a
   measurement. The cell survives +0.05 R of extra slippage at the symbol level; it has not
   been tested at the cell level with a measured gold slippage distribution.
5. **A declared candidate-family entry.** This cell was found by scanning 24 symbols × 10
   families × 3 exit contracts. At `CANDIDATE_BOOK_V1` discipline that is a large look bill
   and the January CI is [+0.024, +0.181]. It needs to be declared *before* the next month
   is read, not after.

---

## 13. Artifacts

Scripts (all under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):
`e5_lib.py`, `e5_build_month.py`, `e5_validate_jan.py`, `e5_01_jan_ceiling.py`,
`e5_02_jan_boundary.py`, `e5_03_three_months.py`, `e5_04_time_curve.py`,
`e5_05_decomposition.py`, `e5_06_trail.py`, `e5_07_selection.py`, `e5_08_survivor.py`,
`e5_09_stack.py`, `e5_10_placebo.py`, `e5_11_xau_robust.py`, `e5_12_cell.py`,
`e5_13_fillbar.py`, `e5_14_hybrid.py`

Data: `e5_january_WS_V1.jsonl.gz`, `e5_february_WS_V1.jsonl.gz`, `e5_march_WS_V1.jsonl.gz`
(+ `e5_<month>_BUILD_V1.json`)

Results: `E5_JAN_VALIDATION_V1.json`, `E5_JAN_CEILING_V1.json`, `E5_JAN_BOUNDARY_V1.json`,
`E5_THREE_MONTHS_V1.json`, `E5_TIME_CURVE_V1.json`, `E5_DECOMPOSITION_V1.json`,
`E5_TRAIL_V1.json`, `E5_SELECTION_V1.json`, `E5_SURVIVOR_V1.json`, `E5_STACK_V1.json`,
`E5_PLACEBO_V1.json`, `E5_XAU_ROBUST_V1.json`, `E5_CELL_V1.json`, `E5_FILLBAR_V1.json`,
`E5_HYBRID_V1.json`, `e5_RESULT.json`
