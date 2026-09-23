# LANE a1 — PRICE IT JOINTLY, AND TEST IT WHERE IT WAS NOT FOUND

Wave 19, phase 19. One scorer built from the anatomy wave's published levers, priced jointly on
January, then read **unchanged** on February, March, April and May 2026.

Population: the **at-market (live-expressible) cohort** — `entry_price` == the decision-instant
market price — 69,480 candidates over five months (Jan 14,905 · Feb 13,966 · Mar 14,884 ·
Apr 13,837 · May 11,888). l10-X3 measured 296/296 live captures at-market; the live engine has
never placed a pending entry order, so this is the only cohort whose economics can be carried.

Machine-readable: `a1_RESULT.json`. Measurement files: `A1_VALIDATE_V1.json`, `A1_BOOK_V1.json`,
`A1_COSTGATE_V1.json`, `A1_DIAG_V1.json`, `A1_FADE_BAND_V1.json`, `A1_CRUX_V1.json`,
`A1_MECH_V1.json`. Substrate: `a1_WIN_2026{01..05}.npz` (+ `_META.json`), built by
`a1_10_build.py` from the lane hold's true-UTC M1 CSVs.

---

## 0. THE ANSWER, IN FOUR SENTENCES

**a1-SCORER-V1 is net-negative in every month, in and out of sample: −0.2059 R/trade on January,
−0.1696 on February+March, −0.1912 on April+May** (n = 9,436 / 18,402 / 16,457; day-clustered
t = −6.56 / −7.94 / −7.78; bootstrap P(net ≤ 0) = 1.000 in all three). It is **not** the same trap
as b1 — it is a **worse** one, and a new one: b1's book failed because a cost-selected edge did not
travel, whereas a1's limbs never had an edge at all. Two of the three gates are, measured,
**affordability filters wearing an edge filter's clothes** (geo↔cost Spearman −0.46 in all five
months; the confirm gate keeps rows that are 0.10–0.15 R/trade cheaper while booking **less** gross),
and the third — x4's confirm minute, the wave's strongest published separator — **is worth +0.457 R
of gross at a fill it cannot have and −0.06…+0.03 R at every fill it can**.

**One thing in the anatomy wave is not a trap.** The entry delay is a real, persistent, directional
edge: **+0.0736 / +0.0754 / +0.0735 / +0.0581 / +0.0988 R/trade of gross in five consecutive
months**, every bootstrap CI clear of zero, 88/101 trading days positive, 98 % of it directional by
the exact mirror, and it survives the equal-holding-time control. It is worth about **+0.075 R/trade
against a toll of 0.14–0.29 R/trade** — real, and about a third of what would be needed.

---

## 1. SUBSTRATE, AND THE PROOF IT IS RIGHT

`a1_10_build.py` stores M1 O/H/L/C for stamps **D−15 … D+125** around every at-market candidate.
Convention (w0-capture / x3 / x4 / x5): a bar stamped `T` covers `[T, T+1min)` and **closes at
T+1min**; the trigger M15 bar interior is stamps D−15…D−1; the decision-instant price is the close
of stamp D−1; **`c0` is the close of stamp D, knowable at D+60 s**; a market order sent at D+k min
fills at the close of stamp D+k−1.

`a1_20_validate.py` → `A1_VALIDATE_V1.json`:

| check | result |
|---|---|
| V1 at-market anchor: close of the last bar strictly before D == `entry_price` | **exact, 0.0 relative error, 69,480 / 69,480 rows, all five months** |
| V2 reproduce h5/e-stack's pre-walked `K0_STOPONLY` and `K5_STOPONLY` | **max abs diff 5.0 × 10⁻⁹, share within 1e-6 = 1.0000, 43,755 / 43,755 rows** |
| V3 reproduce b1's four cost bases | `cost_true` 0.1818338358036221, `cost_true_hour` 0.2203278250081534, **h1 four-term 0.2452135183479202 R / 2.9744108489957553 bps** — identical to `B1_COSTJOIN_V1.json` to the last digit |
| V6 the confirm minute exists | bar stamped D present on 98.93 / 99.28 / 99.69 / 99.27 / 99.06 % of rows |

Two substrate defects were found by this validation and fixed before anything was priced:
float32 storage moved one row's stop verdict by 2.23 R, and a head back-fill let a candidate whose
window opened mid-gap inherit a price from the **future**. Both are gone; the anchor check above is
the proof.

**a1-F1 — the entry convention is worth −0.0344 R/trade on b1's own book, and nobody has priced
it.** b1/h5/e-stack walk **bar counts** (the k-th *available* M1 bar after D); a live book waking on
a 60 s clock gets **D+k minutes**. On b1's own 3,728 rows only **49.4 %** are identical between the
two readings. b1-BOOK-V1's gate reproduces exactly (n = **3,728**, cost **0.046671 R**, instruments
**GER40 / NAS100 / US30_cash**), but its headline moves:

| | b1's k=3 (bar count) | a1's k=3 (wall clock) | Δ |
|---|---:|---:|---:|
| net R/trade, Jan–Mar | **+0.076498** | **+0.042075** | **−0.034423** [−0.0815, +0.0141] |
| net R/trade at k=5 | +0.028320 | +0.027293 | −0.001027 |

The k=3 cell is convention-sensitive; k=5 is not. `A1_CRUX_V1.json` → `X2_entry_convention_on_b1_book`.

---

## 2. THE SPECIFICATION — `a1-SCORER-V1`

Every threshold was published by another lane **before** a1 ran. Nothing is fitted here.

```
POPULATION  at-market (live-expressible) candidates, all 24 instruments.
            No instrument name and no cost term appears anywhere in the rule.

G  GEO      admit if  risk_distance / range(M1 stamps D-15..D-1)  >  0.60
            [x4: refusing geo<=0.60 refuses 23.1 % of the pool booking -0.30378]
            knowable AT the decision instant.

C  CONFIRM  admit if  c0 > -0.15,  c0 = signed R of the close of stamp D
            [x4-F3: refused -0.66506 vs kept -0.05327 on the whole pool]
            knowable at D+60 s -- the live book's CURRENT poll cadence (run_book.py:99).

S  STOPGONE refuse if the ORIGINAL stop was already traded through in [D, D+5min)
            [the at-market analogue of x5's cancel; a1's own construction]

K  DELAY    MARKET entry at D+5 min, filling at the close of stamp D+4
            [l7 +0.0670 / x3 +0.0568 / x5 +0.0585 / x4 re-anchor +0.06672]
            risk distance UNCHANGED -> the stop re-anchors to fill-1R and cost_r is
            invariant across every arm in this receipt.

X  EXIT     stop at fill-1R, NO take-profit, market close at D+120 min
            [b1 / h6 cell B; trail-free, so no bar-resolution trail premium]

COST        h1 four-term broker-true (hour spread + commission + slippage + swap),
            charged once, in R units of the unchanged risk distance.
```

---

## 3. Q1 — PRICED JOINTLY

`A1_BOOK_V1.json` → `windows`.

| | **January (IS)** | **Feb+Mar (OOS)** | **Apr+May (OOS2)** | all five |
|---|---:|---:|---:|---:|
| trades | 9,436 | 18,402 | 16,457 | 44,295 |
| admitted share of cohort | 63.3 % | 63.8 % | 63.9 % | 63.7 % |
| trading days | 21 | 42 | 38 | 101 |
| **gross R/trade** | −0.00516 | −0.01753 | −0.00731 | −0.01110 |
| **cost R/trade** | 0.20072 | 0.15206 | 0.18394 | 0.17427 |
| **NET R/trade** | **−0.20588** | **−0.16959** | **−0.19124** | **−0.18537** |
| gross bps | −0.0108 | −0.7979 | −0.2591 | −0.4301 |
| cost bps | 3.0437 | 2.9991 | 2.9024 | 2.9727 |
| **NET bps** | **−3.0545** | **−3.7970** | **−3.1615** | **−3.4027** |
| edge : toll | −0.026 | −0.115 | −0.040 | −0.064 |
| win rate (net / gross) | 35.11 / 38.86 % | 36.52 / 39.39 % | 36.28 / 39.90 % | 36.13 / 39.47 % |
| t (trade / day-clustered) | −13.32 / −6.56 | −17.04 / −7.94 | −17.92 / −7.78 | −28.05 / −12.95 |
| day-block 95 % CI | [−0.2662, −0.1455] | [−0.2122, −0.1264] | [−0.2354, −0.1434] | [−0.2140, −0.1574] |
| **P(net ≤ 0)** | **1.000** | **1.000** | **1.000** | **1.000** |
| **days net-positive** | **3 / 21** | **4 / 42** | **5 / 38** | **12 / 101** |
| total R | −1,942.7 | −3,120.8 | −3,147.3 | −8,210.8 |
| max drawdown R | 1,883.8 | 3,042.5 | 3,152.4 | 8,151.9 |
| **truncation share** (bell) | **56.32 %** | 57.37 % | 59.03 % | 57.76 % |
| stopped | 43.68 % | 42.63 % | 40.97 % | 42.24 % |

Equity paths are in `A1_BOOK_V1.json` → `windows.*.equity_by_day`; every one of them is a straight
line down. The book has no positive window, no positive month, and no positive fortnight.

---

## 4. Q2 — RUN UNCHANGED ON FEBRUARY AND MARCH (and April and May)

Per month, frozen specification, `A1_BOOK_V1.json` → `per_month`:

| month | n | gross | cost | **net** | days+ |
|---|---:|---:|---:|---:|---|
| 2026-01 | 9,436 | −0.00516 | 0.20072 | **−0.20588** | 3/21 |
| **2026-02** | 8,837 | +0.00183 | 0.16891 | **−0.16708** | — |
| **2026-03** | 9,565 | −0.03542 | 0.13649 | **−0.17191** | — |
| 2026-04 | 8,859 | −0.00497 | 0.17223 | **−0.17719** | — |
| 2026-05 | 7,598 | −0.01004 | 0.19759 | **−0.20763** | — |

The gate shares are stable to the third decimal across all five months (G 0.793–0.798,
C 0.757–0.759, S 0.893–0.897, book 0.633–0.643) — the rule is **stationary**; it is the economics
that are absent, not the rule's behaviour.

---

## 5. Q3 — IS IT THE SAME TRAP? **NO — IT IS A WORSE ONE, AND IT IS NEW**

### 5.1 The b1 decomposition, applied to a1

| | b1-BOOK-V1 (hunt → Apr+May) | **a1-SCORER-V1 (Jan → Feb+Mar)** |
|---|---:|---:|
| Δ net | **−0.11323** | **+0.03629** |
| edge component (Δ gross) | **−0.11190** (gross retained **2.7 %**) | **−0.01237** (gross retained 3.40× — of a number that is ~0) |
| cost component (−Δ cost) | −0.00132 (toll moved **+2.8 %**) | **+0.04866** (toll moved **−24.2 %**) |
| verdict | a cost-selected edge that did not travel | **there was no edge to travel; the whole out-of-sample move is the toll** |

a1's out-of-sample number is *less bad* than its in-sample number, and **134 %** of that improvement
is the toll being 24 % cheaper in February–March. The edge component is **negative**. Applied to
April+May the same arithmetic gives Δ net +0.01464 = edge −0.00214 + cost +0.01678 — again, all toll.

### 5.2 Rank persistence, January → February+March, all 24 instruments

| quantity | at a1's contract (k=5, stop-only) | at the shipped contract (k=0, 2R/−1R) |
|---|---:|---:|
| **cost** | **+0.8948** | **+0.8948** |
| **gross edge** | **−0.4374** | +0.4800 |

This is the third independent reproduction of the estate's cost/edge asymmetry (h5 0.826/0.024;
b1 0.9922/0.1478; a1 0.8948/−0.4374). The gross rank does not merely fail to persist — **it changes
sign when the exit contract changes**, which is the sharpest possible statement that per-instrument
edge is not a property of the instrument.

### 5.3 The mechanism: **a1's gates are cost filters**, and one of them is so by construction

`A1_MECH_V1.json` → `M1_separator_is_a_cost_proxy`. `geo = risk_distance / bar_range` and
`cost_R = cost_price / risk_distance` share a denominator, so they are mechanically anti-correlated:

| month | ρ(geo, cost_R) | cost_R geo>0.60 | cost_R geo≤0.60 | cost_R c0>−0.15 | cost_R c0≤−0.15 |
|---|---:|---:|---:|---:|---:|
| 2026-01 | −0.4604 | 0.2209 | 0.5568 | 0.2548 | 0.4008 |
| 2026-02 | −0.4555 | 0.1901 | 0.4631 | 0.2150 | 0.3357 |
| 2026-03 | −0.4741 | 0.1485 | 0.4069 | 0.1775 | 0.2763 |
| 2026-04 | −0.4742 | 0.1886 | 0.4770 | 0.2189 | 0.3411 |
| 2026-05 | −0.4486 | 0.2149 | 0.5204 | 0.2375 | 0.3692 |

Both gates keep rows that are **2.2–2.7× cheaper**. And they keep rows that earn **less gross**:
under the executable contract each gate's *refused* set books the **higher** gross —
`GATE_G_refused` +0.1232 / +0.0905 / +0.1874 versus a book gross of −0.0052 / +0.0018 / −0.0354.

**The cost-stratified test settles it** (`A1_DIAG_V1.json` → `C4`). Inside a cost decile the confirm
gate's gross gap is **−0.00475 in January (5 of 10 deciles positive)** and **−0.04977 in
February+March (2 of 10)** — while its unconditional cost gap is −0.1460 and −0.1096. **Zero of the
gate's value survives conditioning on affordability.**

**The placebo agrees** (`C3`). Shuffling `c0` within (symbol, day) destroys the cost gap
(−0.005…−0.020 versus the real −0.099…−0.146) and the real gate's *gross* gap is negative in four of
five months. The gate is reading the fee schedule.

---

## 6. a1-F2 — **THE WAVE'S STRONGEST SEPARATOR IS A 60-SECOND STALE FILL**

This is the correction that reaches every prior number built on x4's confirm minute.

**Precision first, because x4 is not simply wrong.** x4 priced its split on a *resting-limit* fill
(`fill_honest_walk_r` on the `bars_to_entry_touch == 1` cohort), and for an order **already resting
in the market** filling at `entry_price` is legitimate. The correction below applies to the
**live-expressible** reading — the at-market cohort, which is the only one the live engine can
place (l10-X3: 296/296; `TRADE_ACTION_PENDING` is defined once and never used for entry). On that
cohort the gate has no order in the market to fill it, so it must send one *after* reading `c0`.

`c0` is the close of `[D, D+1min)`. A book that **acts** on it cannot fill at the D price — that
price is 60 s old by the time the gate can be read. Price the identical gate at both fills
(`A1_CRUX_V1.json` → `crux_pooled`, `A1_MECH_V1.json` → `M3`):

**Gross gap of `c0 > −0.15` (kept − refused), by fill, per month:**

| month | k=0, fill at the D price *(NOT EXECUTABLE)* | k=1 (INC) | k=1 (stop-only) | k=5 (stop-only) |
|---|---:|---:|---:|---:|
| 2026-01 | **+0.4577** | −0.0196 | −0.0183 | −0.0310 |
| 2026-02 | **+0.4686** | +0.0123 | −0.0338 | −0.0288 |
| 2026-03 | **+0.4543** | −0.0647 | −0.0507 | −0.0568 |
| 2026-04 | **+0.4612** | +0.0082 | −0.0015 | −0.0170 |
| 2026-05 | **+0.4412** | −0.0542 | −0.0228 | +0.0311 |

**The whole book, pooled** (`crux_pooled`, all five months, n = 69,480):

| arm | n | gross | net | executable? |
|---|---:|---:|---:|---|
| A shipped: k=0, 2R/−1R, ungated | 69,480 | −0.07750 | −0.32767 | yes |
| B **k=0 + `c0>−0.15`** | 52,598 | **+0.03354** | −0.18652 | **NO** |
| B2 **k=0 + `c0>0`** | 29,612 | **+0.14147** | −0.07459 | **NO** |
| C k=1, ungated | 69,480 | −0.03807 | −0.28825 | yes |
| D **k=1 + `c0>−0.15`** | 52,598 | **−0.04384** | −0.26391 | yes |
| E k=5, stop-only, ungated | 69,480 | +0.01350 | −0.23668 | yes |
| F k=5, stop-only + `c0>−0.15` | 52,598 | +0.00811 | −0.21195 | yes |

Read C→D: **applying the gate at the first fill it can have makes the book worse by 0.00577 R of
gross.** The +0.11 to +0.22 R that the gate appears to be worth is entirely the 60 seconds between
observing `c0` and being able to trade on it.

**The substitution surface says the same thing without any gate arithmetic**
(`A1_DIAG_V1.json` → `C7`, gross, January):

| | c0>−∞ | c0>−0.50 | c0>−0.25 | c0>−0.15 | c0>−0.05 | c0>0 |
|---|---:|---:|---:|---:|---:|---:|
| **k=0** *(not executable)* | −0.0505 | −0.0070 | +0.0325 | +0.0643 | +0.1179 | **+0.1671** |
| **k=1** | −0.0192 | −0.0223 | −0.0230 | −0.0236 | −0.0251 | −0.0337 |
| k=3 | +0.0121 | +0.0047 | +0.0056 | +0.0084 | +0.0059 | −0.0061 |
| k=5 | +0.0231 | +0.0147 | +0.0131 | +0.0157 | +0.0128 | +0.0041 |

The gradient across the top row is enormous and **it vanishes completely one row down.** The
confirm minute and the entry delay are not complements; they are the **same information**, and the
delay is the executable way to hold it.

---

## 7. a1-F3 — THE ONE THING THAT TRAVELS: THE ENTRY DELAY

`A1_COSTGATE_V1.json` → `delay_ladder` / `lever_persistence`, `A1_FADE_BAND_V1.json` →
`delay_lever_stress`, `A1_DIAG_V1.json` → `C1`, `C2`, `C6`.

**Gross delta of a 5-minute market delay against the identical contract at the close, paired,
same rows, day-block bootstrap:**

| month | n | Δ gross | 95 % CI | P(Δ ≤ 0) |
|---|---:|---:|---|---:|
| 2026-01 | 14,905 | **+0.07359** | [+0.04840, +0.09903] | 0.0000 |
| 2026-02 | 13,966 | **+0.07537** | [+0.03974, +0.11166] | 0.0000 |
| 2026-03 | 14,884 | **+0.07353** | [+0.04486, +0.10390] | 0.0000 |
| 2026-04 | 13,837 | **+0.05813** | [+0.02822, +0.08963] | 0.0000 |
| 2026-05 | 11,888 | **+0.09879** | [+0.06960, +0.13245] | 0.0000 |

Positive at **every** delay from 1 to 30 minutes in **every** month (k=1 +0.0442 mean · k=3 +0.0709 ·
k=5 +0.0759 · k=10 +0.0868 · k=30 +0.0946; sd across months 0.013–0.026; 5/5 months positive at all
eight rungs). The **entry + exit repair together** (k=0/2R-target → k=5/stop-only) is
+0.0857 / +0.0866 / +0.1049 / +0.0822 / +0.0956, every CI clear of zero.

**It is not a shorter hold** (`C1`). Moving the bell to D+125 so the holding time is identical:
Δ = +0.0716 / +0.0800 / +0.0656 / +0.0530 / +0.1000, every P(Δ≤0) = 0.0000.

**It is 98 % directional information, not drift** (`C2`, exact mirror — same fill price, same risk
distance, stop reflected, opposite side):

| month | Δ original | Δ mirror | side-free drift | **directional info** | info share |
|---|---:|---:|---:|---:|---:|
| 2026-01 | +0.07359 | −0.07061 | +0.00149 | **+0.07210** | 98.0 % |
| 2026-02 | +0.07537 | −0.07219 | +0.00159 | **+0.07378** | 97.9 % |
| 2026-03 | +0.07353 | −0.06496 | +0.00428 | **+0.06925** | 94.2 % |
| 2026-04 | +0.05813 | −0.09528 | −0.01857 | **+0.07671** | 132 % |
| 2026-05 | +0.09879 | −0.08089 | +0.00895 | **+0.08984** | 90.9 % |

This is the **opposite** of x5's finding for *earliness* (82.5 % of that prize is unreachable
look-ahead). The delay's value is directional but it points the other way: **the market moves
against the signal in the first minutes after the M15 close, and waiting is how you decline to pay
for that.** The info level (`M4`; >0 means the signal's own side is wrong) is
**+0.084 / +0.080 / +0.072 / +0.095 / +0.114 at the close** and decays to ≈0 by minute 5–8 in all
five months — an independent five-month reproduction of x5's January-only info curve (+0.0744 → ~0).

**Cross-sectional persistence, January → Feb+Mar** (`C6`): **family Spearman 1.0000** (7 families,
7/7 sign agreement), symbol 0.4765 (20/24 signs agree), broker hour 0.3904 (22/24). Unlike every
edge the estate has tested, this one's cross-section travels.

**Symmetric stress** (`delay_lever_stress`): median 0.0 (47 % of rows are exactly unchanged;
27.1 % positive, 24.6 % negative); trimming 1 % from **both** tails leaves +0.0450 / +0.0490 /
+0.0503; trimming 5 % from both leaves +0.0085 / +0.0079 / +0.0142; **days positive 19/21, 35/42,
34/38 — 88/101 overall**; P(≤0)=0.0000 in every window. It is tail-weighted (dropping only the top
1 % takes it negative) but the sign survives a symmetric trim and 87 % of trading days.

**And it is not enough.** +0.075 R/trade against a broker-true toll of 0.174 R/trade on the same
cohort. The delay closes **43 %** of the gap.

---

## 8. Q4 — ABLATION, ON THE SAME ROWS

**Add-one-in** from the shipped reference (January; `A1_BOOK_V1.json` → `per_month.202601`):

| arm | n | net R | Δ vs baseline |
|---|---:|---:|---:|
| baseline: k=0, 2R/−1R, all rows | 14,905 | −0.35248 | — |
| + G only | 11,819 | −0.27860 | +0.07388 |
| + C only *(not executable at k=0)* | 11,325 | −0.20748 | +0.14501 |
| + S only | 14,905 | −0.35248 | +0.00000 |
| + K only (delay 5) | 14,905 | −0.29072 | +0.06177 |
| + X only (trail-free stop-only) | 14,905 | −0.34035 | +0.01214 |
| + K + X | 14,905 | −0.26675 | +0.08573 |
| + G + C | 9,575 | −0.19915 | +0.15334 |
| **all five (= BOOK)** | 9,436 | **−0.20588** | **+0.14660** |

**Add-one deltas sum to +0.29279 against a joint gain of +0.14660 — the limbs OVER-count by
99.7 %, i.e. they are almost exactly 2× redundant.** This is the mirror image of b1's 32.7 %
*under*-count and it is the arithmetic signature of substitution: G, C and K are three readings of
the same quantity (the adverse move in the first minutes, and the risk distance that scales it).
Adding the whole gate stack to the delay is worth **less** than the delay alone was.

**Leave-one-out** (January; gate limbs on their own rows, contract limbs on the book's rows):

| variant | n | gross | cost | net | Δ vs BOOK |
|---|---:|---:|---:|---:|---:|
| **BOOK** | 9,436 | −0.00516 | 0.20072 | **−0.20588** | — |
| no G | 10,934 | +0.01066 | 0.24570 | −0.23504 | −0.02916 |
| no C | 11,306 | −0.01061 | 0.21286 | −0.22347 | −0.01759 |
| no S | 9,575 | −0.00341 | 0.20391 | −0.20732 | −0.00144 |
| k=0 instead of 5 *(not executable with G/C)* | 9,575 | +0.01580 | 0.20391 | −0.18811 | +0.01777 |
| k=1 | 9,574 | −0.02610 | 0.20392 | −0.23002 | −0.02414 |
| k=3 | 9,525 | −0.01359 | 0.20315 | −0.21674 | −0.01086 |
| k=10 | 9,144 | −0.00177 | 0.19169 | −0.19346 | +0.01242 |
| k=30 | 7,862 | +0.02383 | 0.18083 | −0.15700 | +0.04888 |
| exit = 2R target | 9,436 | −0.02652 | 0.20072 | −0.22724 | −0.02136 |
| exit = 3R target | 9,436 | −0.02459 | 0.20072 | −0.22531 | −0.01943 |

Note the two rows in which the "improvement" is entirely the cost channel: dropping G *raises*
gross by +0.0158 and *raises* cost by +0.0450.

---

## 9. THE COST BAND — WHERE ANY OF THIS COULD PAY, AND HOW FRAGILE IT IS

a1's rule contains no cost term. Bolting b1's ex-ante toll gate onto it (`A1_FADE_BAND_V1.json` →
`cost_band_sweep`; the swept threshold is the only fitted number anywhere in this receipt, and it is
swept, not chosen) gives the sensitivity curve, at **k=3, stop-only, no anatomy gates**:

| toll cap (bps) | n (Jan) | Jan | **Feb+Mar** | **Apr+May** | all five | days+ |
|---|---:|---:|---:|---:|---:|---|
| 0.40 | 272 | −0.01871 | +0.03684 | +0.01413 | +0.01630 | 41/101 |
| **0.45** | 464 | **+0.03996** | **+0.08141** | **+0.09680** | **+0.07300** | 53/101 |
| 0.50 | 1,100 | +0.03696 | +0.03013 | +0.05061 | +0.03529 | 46/101 |
| 0.55 | 1,228 | +0.03038 | +0.05646 | **−0.03568** | +0.02855 | 48/101 |
| **0.60** (b1's) | 1,288 | +0.02838 | +0.04930 | **−0.07604** | +0.00846 | 48/101 |
| 0.65 | 1,537 | −0.01328 | +0.05665 | −0.08195 | −0.00306 | 46/101 |
| 0.70 | 2,372 | −0.07995 | +0.00807 | −0.11550 | −0.05130 | 34/101 |
| 1.00 | 4,728 | −0.14592 | −0.03965 | −0.17428 | −0.11406 | 21/101 |

**The out-of-sample sign flips between a cap of 0.50 and 0.55 bps.** b1's 0.60 sits one notch past
the edge; that is the whole of b1's April–May failure, and it means the surviving cell at 0.45 is a
knife edge, not a discovery. Of **72** grid cells with n ≥ 80 in all three windows, **6** are
positive in all three — against ~9 expected if each window were a coin flip — and **all six are at
toll ≤ 0.45**, i.e. one band, ~1,671 trades over five months, on the same three index CFDs
(`band_instrument_composition`). Even the best cell is net-positive on only **53 of 101** days.

**a1-F4 — the exact mirror (fade) of every candidate is positive GROSS in all five months**
(`C2`): +0.1180 / +0.1090 / +0.0946 / +0.1266 / +0.1257 at the close, stop-only, against the
original's −0.0505 / −0.0505 / −0.0502 / −0.0631 / −0.1016. Priced as a book it does **not**
survive the toll: fade net on all rows is −0.172 / −0.121 / −0.132 (Jan / Feb+Mar / Apr+May), and
inside the cost bands its sign flips between windows (`fade_windows`). It is a statement about the
generator's direction, not a tradeable book — but it is the cleanest five-month statement the estate
has that **the signal's own side is worse than its opposite at the moment it is allowed to act.**

---

## 10. Q5 — THE PLAIN ANSWER

**Is a1-SCORER-V1 net-positive out of sample? No.**
February+March: **−0.16959 R/trade** (−3.7970 bps) on **n = 18,402** over 42 days, trade-level
**t = −17.04**, day-clustered **t = −7.94**, day-block 95 % CI **[−0.21223, −0.12635]**,
**P(net ≤ 0) = 1.000**, **4 of 42 days positive**. It is not net-positive in sample either
(**−0.20588**, t_day −6.56, 3 of 21 days). April+May, also read once: **−0.19124**, t_day −7.78.

**How far short:** the book has no gross to multiply — out of sample its gross is **−0.01753 R**, so
no cost cut of any size reaches break-even and the required gross multiple (−8.67) is meaningless. Against
the toll of 0.152 R/trade out of sample it is short by **0.170 R/trade**. The single genuine lever
in the wave, the entry delay, supplies **+0.075** of that, which is **43 %** — the same order as, and
no better than, what b1's cost gate supplies by simply refusing to trade expensive instruments.

---

## 11. WHAT THIS LANE HANDS FORWARD

1. **Never price a gate at a fill it cannot have.** Any confirm-style rule must be re-priced with the
   fill moved to the first instant the rule is knowable. On this substrate that single correction
   removes **+0.111 R/trade** of apparent book gross at `c0 > −0.15` and **+0.219** at `c0 > 0`
   (arms A→B and A→B2 in §6), in all five months, at the same sign — which is precisely why it read
   as robust.
2. **Any separator whose formula contains `risk_distance` is a cost variable until proven otherwise.**
   Test it inside cost deciles before believing it. `geo` fails that test at ρ = −0.46.
3. **The entry delay is the estate's first cross-sectionally persistent gross edge** (family Spearman
   1.0000 IS→OOS) and it is free: `run_book.py --poll-seconds 60` already wakes 15× more often than
   it decides. It is worth +0.075 R/trade and it does not reach the toll on its own.
4. **b1's headline should be restated at +0.0421 R/trade** until someone decides which entry
   convention the live book will actually run.
5. The delay is directional and **points against the signal**. Combined with the fade result, the
   next question is not "how do we enter earlier" — x5 already priced that ceiling as 82.5 %
   unreachable — but **"is the generator's declared side the right one at all."**

---

## 12. REPRODUCE

```bash
cd docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery
python3 a1_10_build.py 202601 202602 202603 202604 202605   # ~30 s, deterministic
python3 a1_20_validate.py                                   # V1..V6
python3 a1_30_book.py                                       # A1_BOOK_V1.json
python3 a1_40_costgate.py                                   # A1_COSTGATE_V1.json
python3 a1_50_diag.py                                       # A1_DIAG_V1.json
python3 a1_60_fade_band.py                                  # A1_FADE_BAND_V1.json
python3 a1_70_crux.py                                       # A1_CRUX_V1.json
python3 a1_80_mech.py                                       # A1_MECH_V1.json
```

**Caveats that bound everything above.** (a) The horizon is hard-capped at decision+120 min by the
M1 window; no claim here reaches beyond two hours. (b) The population is at-market only — 63 % of
the true-UTC pool by row count; POI/limit families are not priced here. (c) Costs are modelled
(h1 four-term broker-true), not realised fills; exit slippage is not charged. (d) `a1_10_build.py`
forward-fills the close across minutes with no ticks, which is what a market order would get, and
leaves high/low NaN so no touch is invented. (e) No multiplicity correction is applied anywhere;
the cost-band sweep is 14 thresholds × 2 directions × 3 contracts and is reported as a sweep.
