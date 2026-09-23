# THREE-SLEEVE BOOK RESTATEMENT — the economics of the book that exists today

**Wave 21, outcome-authority swarm. 2026-08-11.** Receipts: `three_sleeve_receipts/`.

**Measurement only.** No live path, no config, no broker call, no VPS touch, no `src/` byte.
Confers no arming, sizing, promotion or activation authority. Two live changes landed today
and both are verified; this prices the result, it does not alter it.

Basis and method: `W7_INSTRUMENT_RESTATEMENT_V1.md` (commit `90824c858`), whose central
lesson governs every figure below — **`p_pass 0.9172` was published with the simulation's
standard error (±0.001125) instead of the evidence's (±0.149).** Every number here carries a
sample size and an interval, or is refused as too thin.

---

## 0. HEADLINE

> **On the surface it can actually trade, the armed three-sleeve book's expected monthly rate
> on FTMO is +2.10 %/month with a 95 % joint band of [−0.005, +4.236] — a band whose lower
> edge is zero — and its two-phase `p_pass` is 0.8522 with a 95 % joint band of
> [0.2803, 0.9927] against a driftless floor of 0.3058 measured on that very series.
> **The FTMO book cannot be distinguished from a driftless account at the 2.5 % tail, and its
> monthly rate cannot be distinguished from zero.** That is not a claim the edge is absent —
> the in-window edge is +0.3298 R/book-day with t = 2.325 on 69 book-days, and the joint
> median is 0.85 — it is a statement about what 69 book-days can support. redacted_account's own
> cell is better separated (joint `p_pass` 0.9791 [0.6310, 1.0000] against a floor of 0.3448,
> monthly band [+0.479, +3.945]) on 47 book-days, and it has traded nothing.**

Four sub-headlines, each measured here:

1. **The sleeve pull costs ~⅓ of the frequency, not the 53 % its population share implies, and
   it is nearly free on redacted_account.** Two independent populations agree: book-days fall
   32.4 % on the W7 cache and correlated units fall 35.4 % on the archive. On FTMO's own
   surface the corrected `p_pass` moves **0.8600 → 0.8414** and the rate **+2.327 → +2.101
   %/month**. On redacted_account's own surface it moves the **other way** — `p_pass`
   **0.9696 → 0.9873**, rate **+1.901 → +2.120 %/month**. The two accounts disagree about
   whether the pull helped, and both differences are small beside their own intervals.
2. **The two substrate sleeves never competed for the capped slot — the premise is refuted.**
   Over 431 substrate cluster-days in the archive: 393 were `sub_mid_dn_revert` alone, 37 were
   `sub_xvol_pullback` alone, and **exactly one had both** (won by the survivor). Forward
   2025+: 40 / 11 / **zero**. So the pull is a straight subtraction of its own days and
   `sub_xvol_pullback` inherits essentially nothing.
3. **Keep the cluster cap.** Its benefit is intact (`p_pass` +0.0895 on three sleeves against
   +0.0904 on four; `p_fail_daily` → **exactly 0.0000** in every cell) and the failure mode it
   removes got **worse** without it (0.0185 → 0.0264). Its cost rose from −36.0 % to −39.1 %
   of R/day, but the **total R it forgoes over the corpus is unchanged** (−52.3 R against
   −53.7 R) — it is the same bill concentrated into 65 % fewer days. And there is a new,
   independent reason: for a three-sleeve book **cluster == sleeve**, so the cap now aligns
   the live book with the exact convention every published `p_pass` is computed on.
4. **The live record was never evidence of a defect, and is less so now.** Lane F's 1 trade in
   12.85 days is consistent with *every* rate tested — P(X ≤ 1) = 0.21 at the 7/month
   expectation and **0.52** at the honest three-sleeve surface rate of 3.83 book-days/month.
   The honest expectation going forward is **~3.8 book-days/month on FTMO and ~2.9 on
   redacted_account**, not 6.5–7.

---

## 1. WHAT CHANGED, AND WHY NOTHING PUBLISHED DESCRIBES THE CURRENT BOOK

| | before 2026-08-11 | now |
|---|---|---|
| armed sleeves, **both** accounts | `crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert` | **`crypto, energy_agri, sub_xvol_pullback`** |
| `ultimate_book_one_unit_per_cluster_per_day` | `false` | **`true`** (10:39:42Z) |
| FTMO armed symbol slots | 42 | **22** |
| redacted_account **reachable** slots | 29 | **15** |
| `substrate` cluster | two sleeves, 38 of 42 slots | **one sleeve**, 18 of 22 slots |

`SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md` §6.1 states the gap this document closes: *"The armed
book is now three sleeves and every published economic figure prices four… **Nothing in this
document should be read as the new expected economics** — that is a measurement, and it has
not been made."* §6.2 states the second: the cluster envelope *"was priced on both being
present… Its measured value should be expected to change; the direction is not obvious and is
not guessed here."*

The removed sleeve was **398 of the four sleeves' 754 cache trades (52.8 %)**, **20 of FTMO's
42 slots**, and **20 of the substrate cluster's 38 slots** — so this is not a marginal
restatement, and neither is it the halving the trade share suggests. §5 measures which.

---

## 2. METHOD, AND THE CONTROLS THAT MAKE IT READABLE

*Receipts: `three_sleeve_receipts/three_sleeve_book.py` → `THREE_SLEEVE_BOOK_V1.json`.*

Every figure crosses three axes at once, at the **deployable** convention throughout
(`KELLY_HALF`, `RISK_LIVE_NOMINAL`, 2.0 % dial, `nights="max"` worst carry, forward 2025+,
`P2_BOTH_PHASES` — a payout requires both phases):

- **Composition** — `THREE_SLEEVE_ARMED` (resolved from `armed_sleeves()`, not hardcoded)
  against `FOUR_SLEEVE_PRIOR` as the control, so the pull's effect is isolated by difference.
- **Universe** — `AS_PUBLISHED` (every cache symbol) / `CURRENT_SURFACE` (what each sleeve can
  generate on today) / `FN_TRADEABLE` (that, minus the 7 canonicals redacted_account's broker does
  not list). The universe filter and the FN-absent set are `LIVE_BOOK_INTEGRITY_V1.md` §1.1's,
  measured on the live terminal by `symbols_get` exhaustion.
- **Instrument** — uncorrected (the caches are **PRE-REPAIR**: their walker has no
  `entry_price` parameter and never loads a spread column, W7 §2) against a quote-side
  correction transferred structurally from r1's 22,354-row corrected walk: per-sleeve
  `target → stop` migration from its Jeffreys posterior `Beta(k+½, n−k+½)`, trail/maxbars
  deltas resampled from r1's own empirical pool, **stops exactly zero (13,221/13,221)**.

**Two intervals, never the simulation's seed noise.** The *instrument* band is 250 replicates
of the correction. The *joint* band is 250 replicates of (correction × moving-block bootstrap
over the book-day series, block 5) — the band the evidence supports.

### 2.1 Four controls, all passed

| control | expected | measured | verdict |
|---|---|---|---|
| FTMO / 3-sleeve / `AS_PUBLISHED` R per book-day | 0.38077 over 117 days (`W7_INSTRUMENT_STATE_V1.json`, `FN_UNIVERSE_RESTATEMENT_V1.json`) | **0.38077 / 117** | reproduces |
| all 12 uncorrected point cells | `FN_UNIVERSE_RESTATEMENT_V1.json` | identical to 5 dp on every R/book-day; `p_pass` within MC seed noise | reproduces |
| corrected `p_pass`, FTMO 3-sleeve `AS_PUBLISHED` | W7 §3.2: 0.90328 [0.77568, 0.93189] | **0.9005 [0.7933, 0.9309]** | reproduces within replicate noise |
| driftless floor, FTMO / FN `AS_PUBLISHED` | W7 §1.2: 0.2995 / 0.3230 | **0.29947 / 0.32295** | reproduces |

### 2.2 A hydration hazard found by the first control, worth recording

`recost_w7_validation`'s D4 re-simulation reads `PRICE_DIRS = data/historical*`. On a sparse
checkout **without** `data/`, it **fails OPEN**: no error, no warning, and FTMO's three-sleeve
mean R per book-day silently reads **0.41478 instead of 0.38077 (+8.9 %)**, with `book_days`
and `sd_book` both reproducing exactly — so the two conventional controls do *not* catch it.
The measurement script now asserts the published value before it measures anything and exits
with a named error if it drifts. This is the same shape as the LFS hazard in `CLAUDE.md` H1:
a fails-open input read as a real result.

---

## 3. THE THREE-SLEEVE BOOK, BOTH ACCOUNTS, WITH INTERVALS

*Receipt: `THREE_SLEEVE_BOOK_V1.json`.*

### 3.1 Read the honest cell, not the published one

`LIVE_BOOK_INTEGRITY_V1.md` §1.4 established that **44.9 % of the published three-sleeve book
is trades on instruments neither account's sleeves can generate today**. Restated for the
three-sleeve book:

| universe | trades | % of published | `crypto` | `energy_agri` | `sub_xvol_pullback` | book-days | per calendar month |
|---|---:|---:|---:|---:|---:|---:|---:|
| `AS_PUBLISHED` | 356 | 100 % | 104 | 162 | 90 | 117 | 6.500 |
| **`CURRENT_SURFACE`** (FTMO's real book) | **196** | **55.1 %** | 68 | 59 | 69 | **69** | **3.833** |
| **`FN_TRADEABLE`** (redacted_account's real book) | **142** | **39.9 %** | 31 | 59 | 52 | **47** | **2.938** |

`energy_agri` loses 63.6 % of its population to the surface on both accounts — its published
economics are mostly agricultural and refined-product trades against a live surface of exactly
`USOIL_cash` + `UKOIL_cash`.

### 3.2 The honest cells, in full

**FTMO — three sleeves, `CURRENT_SURFACE`, 196 trades over 69 book-days**

| quantity | value |
|---|---|
| mean R per book-day | **+0.3298**, sd 1.1785, se 0.1419 |
| **CI95 on the edge itself** | **[+0.0517, +0.6079]**, t = **2.325** on n = 69 |
| worst book-day | −0.9096 R |
| `p_pass` (2-phase) uncorrected | 0.8875 *(MC seed se 0.00129 — do not quote this as the uncertainty)* |
| `p_pass` **instrument-corrected** | **0.8414**, 95 % **[0.6690, 0.8849]** |
| **`p_pass` JOINT (instrument × sampling)** | **0.8522**, 95 % **[0.2803, 0.9927]**, p10 0.5264 |
| **driftless floor, this series** | **0.3058** |
| %/month uncorrected | +2.528 |
| **%/month corrected** | **+2.101**, 95 % [+1.218, +2.506] |
| **%/month JOINT** | **+2.055**, 95 % **[−0.005, +4.236]** |
| **median CALENDAR days to a two-phase pass** | **175**, 95 % [159, 230] *(112 [102, 148] on the estate's weekday-session convention — see §3.5)* |

**redacted_account — three sleeves, `FN_TRADEABLE`, 142 trades over 47 book-days**

| quantity | value |
|---|---|
| mean R per book-day | **+0.4026**, sd 1.0071, se 0.1469 |
| **CI95 on the edge itself** | **[+0.1147, +0.6905]**, t = **2.740** on n = 47 |
| worst book-day | −0.8459 R |
| `p_pass` (2-phase) uncorrected | 0.9895 *(MC seed se 0.00042)* |
| `p_pass` **instrument-corrected** | **0.9873**, 95 % **[0.8824, 0.9892]** |
| **`p_pass` JOINT** | **0.9791**, 95 % **[0.6310, 1.0000]**, p10 0.7854 |
| **driftless floor, this series** | **0.3448** |
| **%/month corrected** | **+2.120**, 95 % [+1.498, +2.352] |
| **%/month JOINT** | **+2.060**, 95 % **[+0.479, +3.945]** |
| **median CALENDAR days to a two-phase pass** | **186**, 95 % [176, 238] *(126 [119, 161] on the weekday-session convention)* |
| **at the live `size_cap_multiplier` 0.622928** | **+1.473 %/month**, `p_pass` 0.9994, **269 calendar days** |

**The last row is the one no published figure has ever carried.** redacted_account runs a live
`size_cap_multiplier: 0.622928` (`reason: derisking_into_maxdd_wall`, from its pre-arming
−3.77 %). At that size its expected rate is **+1.47 %/month** and its median time to a
two-phase pass is **269 calendar days**. *Receipt: `FN_SIZE_CAP_V1.json`.*

### 3.3 The published cell, restated — for anyone still quoting 4.5 %/month

| book · universe · account | uncorrected | **corrected** | **joint 95 %** | **%/month corrected** |
|---|---:|---:|---:|---:|
| 3 · `AS_PUBLISHED` · FTMO | 0.9340 | **0.9005** [0.7933, 0.9309] | **[0.5165, 0.9946]** | **+4.198** [+2.922, +4.894] |
| 3 · `AS_PUBLISHED` · redacted_account | 0.9534 | 0.9296 [0.8484, 0.9516] | [0.6134, 0.9975] | +4.552 |
| 3 · **`CURRENT_SURFACE`** · **FTMO** | 0.8875 | **0.8414** [0.6690, 0.8849] | **[0.2803, 0.9927]** | **+2.101** |
| 3 · `CURRENT_SURFACE` · redacted_account | 0.9326 | 0.9032 [0.7596, 0.9313] | [0.4766, 0.9982] | +2.324 |
| 3 · `FN_TRADEABLE` · FTMO | 0.9908 | 0.9892 [0.8782, 0.9906] | [0.6576, 1.0000] | +2.185 |
| 3 · **`FN_TRADEABLE`** · **redacted_account** | 0.9895 | **0.9873** [0.8824, 0.9892] | **[0.6310, 1.0000]** | **+2.120** |

**`AS_PUBLISHED` overstates the rate the accounts can produce by roughly 2×** — the same
finding `LIVE_BOOK_INTEGRITY_V1.md` §1.3 made for the four-sleeve book, and it survives the
composition change.

### 3.4 What the pull itself did — the control difference

Same universe, same account, same code path, composition the only change:

| cell | 4-sleeve corrected `p_pass` | **3-sleeve** | Δ | 4-sleeve %/mo | **3-sleeve** | Δ |
|---|---:|---:|---:|---:|---:|---:|
| `CURRENT_SURFACE` · FTMO | 0.8600 [0.7045, 0.9025] | **0.8414** [0.6690, 0.8849] | **−0.019** | +2.327 | **+2.101** | −0.23 pp |
| `FN_TRADEABLE` · redacted_account | 0.9696 [0.8711, 0.9803] | **0.9873** [0.8824, 0.9892] | **+0.018** | +1.901 | **+2.120** | **+0.22 pp** |
| `AS_PUBLISHED` · FTMO | 0.8725 [0.7156, 0.9171] | 0.9005 [0.7933, 0.9309] | +0.028 | +4.359 | +4.198 | −0.16 pp |

**The two accounts disagree about the sign, and every difference is an order of magnitude
smaller than its own interval.** The honest statement is that **the pull is not measurable in
`p_pass` on either account** — which is what one expects of removing a sleeve whose corrected
net expectancy at maximum carry was −0.2446 R/trade [−0.3507, −0.1240] (W7 §3.4) but whose
registry confidence was 0.20, the lowest of the four.

### 3.5 A time-to-pass labelling defect, found while writing §3.2

*Receipt: `time_to_pass_convention.py` → `TIME_TO_PASS_CONVENTION_V1.json`.*

`mc_firm_rules._derived` publishes a field named **`median_calendar_days_to_pass`** and builds
it as `med_days_pass × weekday_sessions / book_days`, where `weekday_sessions`
(`mc_firm_rules.py:245-247`) counts only `weekday() < 5`. **It is a count of weekday sessions
wearing a calendar label.** `SURVIVOR_BOOK_V1.json`, `BOOKS_MC_V1.json` and
`LIVE_BOOK_INTEGRITY_V1.md` §1.3 ("48 → 112 days") all quote it.

`W7_INSTRUMENT_RESTATEMENT_V1.md` §1.6 quotes the **other** convention for the same cell —
`med_days_pass / book_days_per_calendar_month × 30.4369` — and gets **89** where `_derived`
gets **57**. Both reproduce exactly here. **Two conventions, one name, 1.48–1.56× apart.**

| cell | med book-days | as published (weekday sessions) | **TRUE calendar days** |
|---|---:|---:|---:|
| 3 · `AS_PUBLISHED` · FTMO | 19 | 57 | **89** |
| 3 · `CURRENT_SURFACE` · FTMO | 20 | 102 | **159** |
| 3 · `FN_TRADEABLE` · redacted_account | 16 | 112 | **166** |
| 4 · `CURRENT_SURFACE` · FTMO | 26 | 92 | **136** |

Every time figure in this document is on the **calendar** convention, with the
weekday-session value shown alongside so either published source can be reconciled. This is a
naming defect, not an arithmetic one — no `p_pass` or `%/month` anywhere is affected.

### 3.6 Per-sleeve, per-universe expectancy: TOO THIN — refused

`crypto` has **31** surviving trades on redacted_account's surface, `sub_xvol_pullback` **52**, and
`sub_xvol_pullback` fires on only **13 distinct days** in the entire 18-month forward window.
A per-sleeve × per-universe point estimate on those counts would be exactly the practice Lane A
found nowhere-intervalled in phases 19–21. **Not published.** The per-sleeve figures that do
exist are W7 §3.4's, on the full cache population, and they carry intervals there.

---

## 4. THE CLUSTER CAP, RE-PRICED ON THE BOOK THAT EXISTS

*Receipt: `cluster_cap_reprice.py` → `CLUSTER_CAP_REPRICE_V1.json`. Same instrument, same
population and same code path as `LIVE_BOOK_INTEGRITY_V1.md` §2.3, parameterised by sleeve set
so both books are measured in one run — a within-corpus A/B/A/B. **The four-sleeve column
reproduces §2.3 exactly** (bind 24.21 %, −36.0 %, +0.0904, +0.1071, `p_fail_daily` → 0.0000),
which is the control.*

### 4.1 The re-price

| | **FOUR-sleeve** (what was priced) | **THREE-sleeve** (what runs) |
|---|---:|---:|
| `(cluster, day)` buckets, all years | 603 | **210** |
| buckets where the cap binds | 146 (**24.21 %**) | 69 (**32.86 %**) |
| correlated units blocked | 168 (21.79 %) | 91 (**30.23 %**) |
| … blocked unit is a **repeat of a symbol already on** | 89.3 % | **95.6 %** |
| median gap first bar → blocked bar | 4.0 h | 4.0 h |
| R/day, all years | +0.2538 → +0.1625 (**−36.0 %**) | +0.6498 → +0.3958 (**−39.1 %**) |
| R/day, forward 2025+ | +0.8139 → +0.4868 (−40.2 %) | +1.1738 → +0.6910 (**−41.1 %**) |
| paired Δ R/day, all years | −0.0914, CI95 [−0.157, −0.033], t −2.90 | **−0.2540**, CI95 [−0.434, −0.091], t −2.89 |
| **total R forgone over the corpus** | −0.0914 × 588 d = **−53.7 R** | −0.2540 × 206 d = **−52.3 R** |
| worst day, all years | −2.550 → −1.650 | −2.550 → −1.650 |
| worst day, forward | −2.550 → −1.050 | −2.550 → **−0.850** |

**The relative price rose (−36 % → −39 %) and the absolute bill did not.** The cap forgoes the
same ~53 R over the archive either way; the three-sleeve book simply concentrates it into 65 %
fewer trading days, so the *per-day* number looks worse while the *total* is unchanged.

### 4.2 What it still buys

| window · account · risk | Δ `p_pass` FOUR | **Δ `p_pass` THREE** | `p_fail_daily` OFF → ON, THREE |
|---|---:|---:|---|
| all-years · FTMO · 2.000 % | +0.0904 | **+0.0895** | **0.0264 → 0.0000** |
| all-years · FTMO · 1.1968 % | +0.0493 | +0.0378 | 0.0000 → 0.0000 |
| all-years · FN · 2.000 % | +0.0856 | +0.0870 | **0.0222 → 0.0000** |
| fwd-2025+ · FTMO · 2.000 % | +0.1071 | **+0.1036** | **0.0541 → 0.0000** |
| fwd-2025+ · FN · 2.000 % | +0.0988 | +0.0979 | **0.0513 → 0.0000** |

**The benefit is intact, and the hazard it removes got worse.** Without the cap the
three-sleeve book's all-years daily-breach probability is **0.0264** against the four-sleeve
book's 0.0185 — a *narrower* book concentrates its bad days. `p_fail_daily` still goes to
**exactly 0.0000** in every cell where it was non-zero, and that failure mode is account
death, not a drawdown you trade out of.

### 4.3 The mechanism changed, and it is worth knowing

| cluster | buckets, FOUR | buckets, THREE | binding buckets, THREE |
|---|---:|---:|---:|
| `crypto` | 133 | **133** (unchanged) | **42** |
| `energy` | 39 | **39** (unchanged) | 6 |
| `substrate` | 431 | **38** (−91.2 %) | 21 |

**The cap is now a crypto instrument, not a substrate instrument.** 42 of its 69 binding
buckets are `crypto` — a two-symbol sleeve re-firing on a later bar — where under the
four-sleeve book substrate supplied 98 of 146. `LIVE_BOOK_INTEGRITY_V1.md` §2.1's framing
("38 of 42 armed slots sit in one cluster") is still true of the *slots* (18 of 22) and no
longer describes where the cap actually acts.

### 4.4 A second, independent reason to keep it — the cap now agrees with the published ruler

*Receipt: `cache_convention_vs_cap.py` → `CACHE_CONVENTION_VS_CAP_V1.json`.*

Every published `p_pass` rests on `recost_w7_validation.build_matrix_from`, which reduces each
sleeve to **one value per date** — the mean of that sleeve's trades that day. That is a third
convention, neither cap-OFF nor cap-ON. **For a three-sleeve book it becomes the cap's own
convention on the count axis**: `crypto`→crypto, `energy_agri`→energy,
`sub_xvol_pullback`→substrate are three distinct clusters, so one-unit-per-cluster-per-day and
one-row-per-sleeve-per-day count the *same* units. They did not for the four-sleeve book.

What remains is an outcome difference — the capped book takes the **first** bar-group's R, the
cache takes the day's **average** — and it runs in the book's favour:

| three-sleeve, archive | cache convention | cap ON | difference |
|---|---:|---:|---|
| R/day, all years | +0.2988 | **+0.3958** | **+0.0970**, CI95 [+0.0398, +0.1611], t 3.14 |
| R/day, forward 2025+ | +0.5664 | **+0.6910** | **+0.1246**, CI95 [+0.0289, +0.2417], t 2.27 |
| `p_pass` FTMO 2 %, all years | 0.7215 | **0.7812** | +0.060 |
| `p_pass` FTMO 2 %, forward | 0.8662 | **0.8850** | +0.019 |

**The later-bar fires the cap blocks are worse than the first**, so the published convention
— which averages them in — understates the capped book. Direction and rough magnitude only:
this is the archive at the correlated-unit scale, not the cache, so it does not restate §3's
levels. But it means the §3 figures are **conservative** for the capped book on this axis, not
optimistic.

### 4.5 Recommendation: **KEEP the cap.** Reversible in two minutes if the owner disagrees.

The trade the owner accepted on 2026-08-12 — pay ~36 % of R/day to remove the daily-breach
mode and buy +4.7…+10.7 pp of `p_pass` — is **still the trade**, at ~39 % instead of ~36 %,
with the same benefit and a **worse** uncapped hazard. Nothing here is a reason to revert.

Two things the owner should nonetheless be told, because they are new:

1. **The bill is now lumpier.** Same total R forgone, concentrated into 65 % fewer days. On a
   short live window that will be more visible as "the book saw a signal and did not take it."
2. **It is a crypto cap now.** If a future composition decision drops `crypto`, this pricing
   expires the same way §2.3's did today — 42 of its 69 binding buckets go with it.

The rollback procedure is unchanged and is recorded at `LIVE_BOOK_INTEGRITY_V1.md` §3.3:
restore the backup, re-mint both tokens, restart. **This document does not recommend it.**

---

## 5. THE FREQUENCY INTERACTION — the premise was wrong

*Receipt: `substrate_frequency.py` → `SUBSTRATE_FREQUENCY_V1.json`.*

### 5.1 They never competed

The head-to-head can only be resolved on the archive, because it is the only per-trade
artifact carrying an `entry_utc` — the W7 cache has a date and no bar index, and that is
stated rather than worked around.

| substrate cluster-days | all years | forward 2025+ |
|---|---:|---:|
| total | **431** | **51** |
| only `sub_mid_dn_revert` fired | **393 (91.2 %)**, Wilson 95 % [88.1, 93.5] | **40 (78.4 %)**, Wilson 95 % [65.4, 87.5] |
| only `sub_xvol_pullback` fired | 37 | 11 |
| **both fired — the contested case** | **1** | **0** |
| … won by the survivor | 1 | — |

**The two sleeves fired on disjoint days.** In twenty years of archive there is exactly one day
on which both fired, and none in the forward window. So:

- The removal is a **straight subtraction of `sub_mid_dn_revert`'s own days**, not a hand-over.
- `sub_xvol_pullback` **inherits essentially nothing** — at most one day's unit in 20 years.
- The worry that the pulled sleeve "usually fired first" and was therefore consuming the slot
  is technically true (it consumed 393 of 431) but economically empty: on 392 of those 393
  days there was no competing `sub_xvol_pullback` signal to consume it *from*.

### 5.2 What the pull actually costs in frequency

Two populations, and they agree:

| measure | four-sleeve | three-sleeve | change |
|---|---:|---:|---:|
| **W7 cache, forward** — trades | 754 | 356 | **−52.8 %** |
| **W7 cache, forward** — **book-days** | 173 | 117 | **−32.4 %** |
| W7 cache — book-days per calendar month | 9.611 | 6.500 | −32.4 % |
| **archive, forward** — trades | 202 | 138 | −31.7 % |
| **archive, forward** — correlated units **under the cap** | 113 | 73 | **−35.4 %** |
| archive, forward — trading days | 107 | 70 | −34.6 % |
| archive — units per month under the cap | 5.947 | 4.056 | −31.8 % |
| **FTMO own surface** — book-days/month | 5.833 | **3.833** | −34.3 % |
| **redacted_account own surface** — book-days/month | 4.167 | **2.938** | −29.5 % |

**The frequency loss is ~32–35 %, not 53 %.** The trade-count share overstates it by ~1.6×
because the cache already collapses each sleeve to one unit per day and the cap collapses each
cluster to one, and `sub_mid_dn_revert` was the sleeve firing most often *within* a day.

The per-day edge moves the other way and absorbs most of it: **+0.28659 → +0.38077 R per
book-day (+32.9 %)** on `AS_PUBLISHED`, because the sleeve removed carried registry confidence
0.20 — the lowest of the four — and the estate's highest quote-side migration rate (19.3 %).
Net effect on the published monthly rate: **+5.509 → +4.950 %/month, −10.2 %.**

### 5.3 Where the frequency actually comes from

Distinct forward-window days on which each sleeve produces a value, W7 cache:

| sleeve | forward days (18 months) | per month |
|---|---:|---:|
| `energy_agri` | 61 | 3.39 |
| `crypto` | 56 | 3.11 |
| **`sub_xvol_pullback`** | **13** | **0.72** |

**The book's clock is `crypto` and `energy_agri`.** `sub_xvol_pullback` — the highest per-trade
gross R in the survivor book (+1.307, and the least damaged by the quote-side correction at
−0.1 %) — fires on fewer than one day a month. Any expectation of trade frequency should be
formed from the first two rows.

### 5.4 Reconciling with Lane F's live record

*Receipt: `live_rate_reconciliation.py` → `LIVE_RATE_RECONCILIATION_V1.json`. `p_pass` is
invariant to frequency (`p_timeout` = 0.0000, W7 §1.6): frequency scales the monthly rate and
the calendar clock and nothing else.*

Lane F: **1 book trade in 12.85 days armed on FTMO** (+$493.20, +0.382 R); **0 in 12.17 days on
redacted_account**, the latter blocked by a token-digest defect rather than by absence of signal. The
whole observation window ran the **four-sleeve** book with the cap **OFF**, so that is the
expectation the observation should be tested against:

| assumed rate | book-days/month | E[days] in 12.85 d | **P(X ≤ 1)** | verdict |
|---|---:|---:|---:|---|
| `CLAUDE.md`'s stated expectation | 7.000 | 2.96 | 0.206 | consistent |
| `AS_PUBLISHED` three-sleeve cache | 6.500 | 2.74 | 0.241 | consistent |
| **four-sleeve, FTMO's own surface** (what ran) | 5.833 | 2.46 | **0.295** | consistent |
| **three-sleeve, FTMO's own surface** (going forward) | 3.833 | 1.62 | **0.519** | consistent |

**No rate in this table is refuted by the live record, and the honest one is the least
surprised by it.** The observed count was never evidence of a defect; it is what a
3.8-book-days/month book looks like over twelve days.

Restating FTMO's honest cell at each rate — the corrected monthly rate and the median calendar
time to a two-phase pass:

| at | %/month corrected | 95 % | median CALENDAR days to pass (§3.5 convention) |
|---|---:|---:|---:|
| 7.000 book-days/month | +3.836 | [+2.22, +4.58] | 87 |
| 6.500 | +3.562 | [+2.07, +4.25] | 94 |
| **3.833 (honest)** | **+2.100** | **[+1.22, +2.51]** | **159** |

---

## 6. redacted_account, RESTATED SEPARATELY

*Receipt: `fn_slot_restatement.py` → `FN_SLOT_RESTATEMENT_V1.json`, arithmetic on the
2026-08-11T10:26Z live symbol probe. No broker was contacted for this section.*

### 6.1 How much of its book survives

| | FTMO | redacted_account |
|---|---:|---:|
| symbols the broker lists at all | 166 | **76** |
| four-sleeve slots | 42 | 42 declared, **29 reachable** |
| **three-sleeve slots** | **22** | 22 declared, **15 reachable** |
| reachable lost to the pull | 20 (−47.6 %) | **14 (−48.28 %)** |
| still unreachable, three-sleeve book | 0 | **7** |

The 7 that remain unreachable: **`DASHUSD`** (`crypto` — half that sleeve's surface) and
**`XAUEUR, XAGEUR, XAUAUD, XAGAUD, CORN_c, COTTON_c`** (`sub_xvol_pullback`, 6 of its 18).
None exists on that broker under any probed name; this is a property of the account and cannot
be repaired by config.

### 6.2 Have the accounts converged or diverged?

**Diverged, by 1.3 % — which is to say, not materially.** The reachable-slot ratio
FTMO : redacted_account moves **1.4483 → 1.4667**. Both accounts lost almost exactly the same
fraction (47.6 % vs 48.3 %) because `sub_mid_dn_revert` and `sub_xvol_pullback` were missing
the *same six* symbols on redacted_account. The structural gap
`LIVE_BOOK_INTEGRITY_V1.md` §1.5 established — expect redacted_account to trade about
three-quarters as often as FTMO, indefinitely, for universe reasons — **survives the
composition change unchanged.**

### 6.3 Its economics, and the one term nobody has priced

redacted_account's own cell is in §3.2. Three things distinguish it from FTMO's:

1. **It is better separated from zero**, not worse: t = 2.740 on the edge against FTMO's 2.325,
   joint `p_pass` 0.9791 [0.6310, 1.0000] against a driftless floor of 0.3448. Restricting to
   its real universe removes the tails at both ends (sd 1.007 against FTMO's 1.178, worst day
   −0.846 against −0.910) — a smaller, calmer book, exactly as §1.3 of the integrity lane found.
2. **The pull HELPED it** (§3.4): `p_pass` +0.018, rate +0.22 pp/month. `sub_mid_dn_revert`'s
   redacted_account-tradeable rows were the worse half of an already-negative sleeve.
3. **It is slower than any published figure says, and slower again at the size it runs.** At
   nominal 2.0 %: +2.120 %/month, median **186 calendar days**. At its live
   `size_cap_multiplier` **0.622928**: **+1.473 %/month, median 269 calendar days**. No published figure carries that
   multiplier. It is the single largest unpriced term on that account.

**redacted_account has still never placed a book trade.** Everything in this section is expectation.

---

## 7. THE HONEST EXPECTED ECONOMICS, IN ONE PARAGRAPH

> **The armed book is now three sleeves on both accounts, and on the instruments each account
> can actually trade it is expected to earn roughly 2 % a month — about +2.1 % on FTMO and
> +2.1 % on redacted_account (+1.5 % at the reduced size redacted_account is currently running) — taking
> a trade on about 4 days a month on FTMO and 3 on redacted_account, with a median of roughly six
> months to pass both challenge phases (175 calendar days on FTMO, 186 on redacted_account, and 269
> at the size redacted_account is running). That is less than half the 4.5–5.5 %/month that has
> been published, and the difference is not a new defect: it is that the published figure
> prices trades on instruments the accounts cannot reach. The honest uncertainty is much
> larger than the honest estimate. FTMO's 95 % band on that monthly rate is [−0.005, +4.236] —
> its lower edge is zero — and its band on the probability of passing is [0.28, 0.99] against
> a coin-flip-with-no-edge floor of 0.31, so on 69 days of evidence the FTMO book cannot be
> told apart from an account with no edge at all. redacted_account's band is better ([+0.48, +3.95]
> and [0.63, 1.00] against a floor of 0.34) and rests on even less data, 47 days, and it has
> never placed a trade. Against that, the ground truth: one trade in 12.5 days for +$493.20,
> which is +0.25 % of the $200,000 at risk and is consistent with every rate above and with
> zero; and the full eleven-sleeve book's own recost expectancy of −0.088 R/trade published /
> −0.127 corrected against a live measured −0.068, which agree — the machinery is honest, and
> every positive number in this programme is a statement about the three sleeves selected out
> of those eleven, on the window that selected them. The right action on this evidence is to
> keep running the book at its current size, keep the cluster cap on, and expect to need six
> months to a year of live record before the question "does this book have an edge" has an
> answer. It is too early for the number to mean anything, and that is the finding, not a
> hedge.**

---

## 8. WHAT THIS DID NOT SETTLE

- **No re-walk was possible**, for the same reason W7 §6 gives: the deep H4 archive
  (`data/mt5_research_exports/bridge_ftmo_deep_h4_*`) is absent from this machine and its
  loader fails open. §3's instrument correction is a structural transfer with published
  intervals, not a regeneration. Fetching those two export sets would convert every instrument
  interval here into a point estimate and is still the cheapest remaining upgrade.
- **The cluster cap's price and the §3 economics are on different populations.** §4 is the
  archive at the correlated-unit scale; §3 is the W7 cache at the book-day scale. §4.4
  measures the direction of the gap and its rough size, and that is all it can support. A
  cap-aware `p_pass` on the cache population would need the cache to carry a bar index, and it
  does not (W7 §2.4).
- **The redacted_account `size_cap_multiplier` is priced but not explained.** Whether 0.622928
  persists, decays, or resets on a phase boundary is a runtime question this lane did not open.
- **Per-sleeve × per-universe expectancy is refused as too thin** (§3.6) and stays open until
  either the archive fetch lands or the live record grows.
- **Nothing here re-prices realised P&L.** Lane F remains the only broker-true live record and
  it is one trade.
- **The 2.0 % dial is taken as given.** §4.2 shows the cap's `p_pass` benefit is 2–3× larger at
  2.000 % than at the measured live 1.1968 %, so the dial and the cap interact; the dial is
  Borhen's call and was not modelled as a variable here.

---

## 9. RECEIPTS

| file | what |
|---|---|
| `three_sleeve_receipts/three_sleeve_book.py` → `THREE_SLEEVE_BOOK_V1.json` | §2, §3 — 12 cells × (point, instrument band, joint band), 250 replicates, census, hydration control |
| `three_sleeve_receipts/cluster_cap_reprice.py` → `CLUSTER_CAP_REPRICE_V1.json` | §4.1–4.3 — cap A/B on both books, 4 cost bands, both weightings, ±2 h clock control |
| `three_sleeve_receipts/cache_convention_vs_cap.py` → `CACHE_CONVENTION_VS_CAP_V1.json` | §4.4 — cap-OFF / cap-ON / cache-convention, three arms on one population |
| `three_sleeve_receipts/substrate_frequency.py` → `SUBSTRATE_FREQUENCY_V1.json` | §5.1–5.3 — head-to-head, unit and book-day frequency, two populations |
| `three_sleeve_receipts/live_rate_reconciliation.py` → `LIVE_RATE_RECONCILIATION_V1.json` | §5.4 — Poisson reconciliation and calendar restatement at four rates |
| `three_sleeve_receipts/fn_slot_restatement.py` → `FN_SLOT_RESTATEMENT_V1.json` | §6.1–6.2 — per-account slot restatement and the divergence ratio |
| `three_sleeve_receipts/FN_SIZE_CAP_V1.json` | §6.3 — redacted_account at its live `size_cap_multiplier` |
| `three_sleeve_receipts/DRIFTLESS_FLOOR_V1.json` | §0, §3.2 — driftless floor per universe; reproduces W7 §1.2 on `AS_PUBLISHED` |

Inputs bound: `INTEG_W3_streams_cache.pkl`, `INTEG_W5_new_streams_cache.pkl`,
`BROKER_TRUE_COSTS_V1.json`, `phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz` (22,354 rows),
`phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz`,
`swarm/live_book_integrity_receipts/SYMBOL_UNIVERSE_V1.json`,
`swarm/lane_f_receipts/LANE_F_EMPIRICAL_R_V1.json`.
Machinery: `scripts/mc_firm_rules.py`, `scripts/recost_w7_validation.py`,
`src/components/ultimate_book/admission.py`, `src/safety/armed_set.py` — all imported
unchanged. No sealed route edited, no `src/` byte changed.
