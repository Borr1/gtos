# e-stack — do the levers ADD UP?

Lane key `e-stack`. Wave 2 of the wave-19 broad-forensic swarm. Everything below is measured on
this machine; every table reproduces from the scripts named at the bottom. Companion machine-readable
receipt: `e-stack_RESULT.json`.

**The question.** Wave 1 produced eleven lanes of independent claims, each priced alone. Nobody had
scored them together. Three families were believed independent — capture (the exit contract), cost
denomination, and conditioning (selection). This lane builds ONE combined offline scorer, runs all
2⁶ = 64 lever combinations, ablates, reports the interaction structure, and repeats the whole thing on
February and March.

---

## 0. The answer in five lines

| | measured |
|---|---|
| **Sum of the six levers priced ALONE** | +1.26603 R/opportunity (Jan) · +0.98553 (Feb) · +0.85081 (Mar) |
| **What they deliver TOGETHER** | +0.42086 (Jan) · +0.34035 (Feb) · +0.31166 (Mar) |
| **Double-counted** | **66.8 % · 65.5 % · 63.4 %** |
| **Of 30 ordered lever pairs** | 26 substitutes, 2 trivially independent, 2 "complements" worth +0.00012 |
| **Is the stacked system positive?** | Jan −0.0524 R/trade · Feb **+0.0062** · Mar **+0.0052** — and the Feb/Mar positives sit on a cohort the pool cannot sample honestly (§6) |

**The one place the levers DO add up, and it is the live-expressible one:** entry re-timing and the
trailing exit are **95.0 % additive** on the at-market cohort (delay alone +0.06624, exit alone
+0.04311, sum +0.10935, joint +0.10392, n = 43,755 over three months). Their joint gross edge is
**+0.0383 R/trade at t = 12.35** — and the broker-true cost of the same trades is **0.1818 R/trade.**
In price space: **the signal is worth +0.231 bps and costs 2.457 bps. It earns 9.4 % of its own toll.**

---

## 1. Substrate — one scorer, three months, validated

`e_build_month.py` rebuilds the CQ path-sidecar convention from raw true-UTC M1 bars so February and
March are scored by the identical code that scored January. Validated by rebuilding January and
diffing against the sealed sidecar (`e_VALIDATE_JAN_REBUILD_V1.json`):

| quantity | sidecar mean | rebuild mean | exact frac | max abs diff |
|---|---:|---:|---:|---:|
| `mkt_r` (decision anchor) | −0.663331 | −0.663331 | 1.000000 | 0.0 |
| `mfe_r` | 1.098013 | 1.098013 | 0.021 | 5e−05 |
| `mae_r` | −3.130569 | −3.130570 | 0.021 | 5e−05 |
| `R_INC` (2R/−1R honest) | −0.236906 | −0.236906 | 0.723 | 5e−05 |
| `R_TS90S1` | −0.222005 | −0.222005 | 0.604 | 5e−05 |
| `n_bars` | 116.792229 | 116.792229 | 1.000000 | 0 |
| `cost_true` | 0.189310 | 0.189310 | 1.000000 | 0.0 |
| `cost_frozen` | 0.663097 | 0.663097 | 1.000000 | 0.0 |

`t_first` (first entry touch) is **identical on 100.000 % of 27,641 common rows**. Born census
reproduces to one row (3,516 vs 3,515 past-stop; 2 rows unanchored because the decision precedes the
first bar of the month). The residual 5e−05 is the sidecar's own 6-decimal rounding. One
`R_TRAIL025` row differs by 0.95 (1 of 27,641) at a trail-arming boundary.

Anchor convention is w0-capture's corrected one: bars are OPEN-stamped, so the bar that *closes at*
the decision instant is the one stamped `decision − 1 min`. Zero look-ahead.

### 1.1 The three months as substrate

| | n pool | days | born_at_limit | born_resting | born_marketable | born_past_stop | bar-1 fill share | never fills | pool gross | honest 2R/−1R | cost_true | cost_frozen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **2026-01** | 27,658 | 21 | 14,911 | 7,949 | 1,265 | 3,516 | 61.288 % | 241 | −0.217496 | −0.237151 | 0.189297 | 0.663161 |
| **2026-02** | 24,239 | 20 | 13,973 | 7,019 | 1,420 | 1,827 | 60.304 % | 338 | −0.150551 | −0.185856 | 0.156229 | 0.489470 |
| **2026-03** | 26,500 | 22 | 14,890 | 8,468 | 1,616 | 1,526 | 58.743 % | 260 | −0.176720 | −0.188031 | 0.124748 | 0.404585 |

March is extracted from the never-decoded `FA2_M_R0` arm's MISSED_OPPORTUNITY ledger by the same
diagnostic-scoreable filter that built January's pool: 130,004 ledger rows → 26,500 pool rows
(20.4 %; January was 27,658/153,425 = 18.0 %). The frozen cost model's overcharge shrinks month to
month (3.50× / 3.13× / 3.24× against broker truth) but the January **structure** — a ~60 % bar-1 fill
share, a ~54 % at-market cohort, a ~29 % resting cohort — reproduces on both never-used months.

---

## 2. The exit contract, chosen on TRAIN and read on TEST

Fifteen contracts walked on the capture-clean population (A1+A2+A3 on), fit Jan 01–15 (10 days),
read Jan 16–31 (11 days). `risk` = whether the contract carries a defined stop, i.e. whether R is a
real risk unit.

| contract | risk | n | train gross | test gross | train net | test net | all net/trade | all net/opp | win |
|---|:--:|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD | **F** | 10,413 | −0.0051 | +0.1839 | −0.1917 | +0.0320 | −0.0750 | −0.02823 | 0.511 |
| TS90 | **F** | 9,387 | −0.0052 | +0.1166 | −0.1939 | −0.0381 | −0.1124 | −0.03814 | 0.509 |
| TS90S3 | T | 9,387 | −0.0027 | +0.0682 | −0.1914 | −0.0865 | −0.1365 | −0.04634 | 0.489 |
| **TRAIL025** | **T** | **10,413** | **+0.0492** | **+0.0526** | **−0.1375** | **−0.0994** | −0.1176 | −0.04426 | 0.759 |
| TS90S2 | T | 9,387 | −0.0082 | +0.0437 | −0.1968 | −0.1110 | −0.1519 | −0.05155 | 0.462 |
| TS60 | F | 8,060 | −0.0007 | +0.0444 | −0.1926 | −0.1146 | −0.1518 | −0.04423 | 0.497 |
| T5S2 | T | 10,413 | −0.0022 | +0.0312 | −0.1889 | −0.1207 | −0.1533 | −0.05772 | 0.458 |
| TRAIL050 | T | 10,413 | −0.0020 | +0.0172 | −0.1886 | −0.1347 | −0.1605 | −0.06042 | 0.631 |
| STOPONLY | T | 10,413 | −0.0631 | +0.0086 | −0.2497 | −0.1433 | −0.1942 | −0.07311 | 0.360 |
| TS90S1 | T | 9,387 | −0.0547 | −0.0005 | −0.2433 | −0.1551 | −0.1972 | −0.06692 | 0.379 |
| T3S1 | T | 10,413 | −0.0437 | −0.0202 | −0.2304 | −0.1721 | −0.2000 | −0.07529 | 0.377 |
| **INC (shipped 2R/−1R)** | T | 10,413 | −0.0556 | −0.0235 | −0.2423 | −0.1754 | −0.2074 | −0.07808 | 0.400 |
| TS60S1 | T | 8,060 | −0.0540 | −0.0180 | −0.2459 | −0.1770 | −0.2099 | −0.06117 | 0.398 |
| T2S1M90 | T | 9,387 | −0.0533 | −0.0263 | −0.2420 | −0.1810 | −0.2101 | −0.07129 | 0.409 |
| TS30S1 | T | 6,062 | −0.0633 | −0.0302 | −0.2601 | −0.1940 | −0.2254 | −0.04940 | 0.439 |

**TRAIL025 (no target, initial stop −1R, stop trails 0.25 R behind the running MFE) is the pick on
both TRAIN criteria and it holds on TEST to within 0.0034 R.** It is used as the `B1_EXIT` lever
everywhere below. The two contracts that beat it on *net* — HOLD and TS90 — have **no stop at all**,
so their R is not a risk unit (l2 measured the no-stop tail to −135 R); they are reported as an upper
bound, never as the headline. Nothing in the menu is net-positive.

---

## 3. The 64-arm enumeration — January

Ordered `A1 A2 A3 B1 C1 C2`. `net/opp` = broker-true net R per candidate-opportunity;
`cost` = mean broker-true cost charged per trade taken.

**Top and bottom of the 64 (full table in `E_STACK_MAIN_V1.json → months.2026-01.all_arms`):**

| mask | n trades | gross/opp | net/opp | gross/trade | net/trade | win | t | days net+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `..1111` = `1.1111` = `.11111` = `111111` | 1,855 | +0.00132 | **−0.00352** | +0.0197 | −0.0524 | 0.750 | −4.01 | 7/21 |
| `...111` = `1..111` = `.1.111` = `11.111` | 1,894 | +0.00091 | −0.00402 | +0.0133 | −0.0587 | 0.744 | −4.47 | 7/21 |
| `.1111.` = `11111.` | 5,061 | +0.00104 | −0.01145 | +0.0057 | −0.0626 | 0.731 | −7.90 | 6/21 |
| `..111.` = `1.111.` | 5,086 | +0.00108 | −0.01148 | +0.0059 | −0.0624 | 0.731 | −7.91 | 6/21 |
| `..1.11` = `1.1.11` | 1,855 | −0.00708 | −0.01192 | −0.1056 | −0.1777 | 0.409 | −7.58 | 2/21 |
| … | | | | | | | | |
| `11....` | 22,644 | −0.09608 | −0.25320 | −0.1174 | −0.3093 | 0.361 | −40.35 | 0/21 |
| `1.....` | 23,901 | −0.11057 | −0.27227 | −0.1280 | −0.3151 | 0.357 | −42.58 | 0/21 |
| `.1.1..` | 26,160 | −0.17930 | −0.36194 | −0.1896 | −0.3827 | 0.589 | −83.55 | 0/21 |
| `...1..` | 27,417 | −0.19320 | −0.38043 | −0.1949 | −0.3838 | 0.583 | −86.29 | 0/21 |
| `.1....` | 26,160 | −0.22266 | −0.40530 | −0.2354 | −0.4285 | 0.313 | −62.08 | 0/21 |
| `......` (as shipped) | 27,417 | −0.23715 | −0.42438 | −0.2392 | −0.4281 | 0.311 | −63.89 | 0/21 |

**Four masks are byte-identical at the top.** `A1_STOPVALID` and `A2_NOMKT` change nothing once
`C2_DEPTH` is on, because a limit resting ≥ 1 R from the market is by definition neither past its own
stop nor already through the market. That is the first substitution, and it is structural.

### 3.1 The C2-off slice (32 arms) — the ablation without the nesting

| mask (A1A2A3B1C1) | n | gross/opp | net/opp | gross/trade | net/trade | cost | win | days net+ | max DD (R) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `.1111` = `11111` | 5,061 | +0.00104 | −0.01145 | +0.0057 | −0.0626 | 0.068 | 0.731 | 6 | −316.7 |
| `..111` = `1.111` | 5,086 | +0.00108 | −0.01148 | +0.0059 | −0.0624 | 0.068 | 0.731 | 6 | −317.4 |
| `.11.1` = `111.1` | 5,061 | −0.01149 | −0.02398 | −0.0628 | −0.1311 | 0.068 | 0.424 | 2 | −663.4 |
| `..1.1` = `1.1.1` | 5,086 | −0.01156 | −0.02412 | −0.0628 | −0.1311 | 0.068 | 0.423 | 2 | −667.0 |
| `.111.` | 10,414 | +0.01923 | −0.04422 | **+0.0511** | −0.1174 | 0.169 | 0.759 | 2 | −1,223.0 |
| `1111.` | 10,413 | +0.01918 | −0.04426 | +0.0509 | −0.1176 | 0.169 | 0.759 | 2 | −1,224.3 |
| `..11.` | 10,466 | +0.01937 | −0.04435 | +0.0512 | −0.1172 | 0.168 | 0.759 | 2 | −1,226.5 |
| `1.11.` | 10,465 | +0.01931 | −0.04439 | +0.0510 | −0.1173 | 0.168 | 0.759 | 2 | −1,227.7 |
| `11.11` | 10,898 | −0.02090 | −0.04783 | −0.0530 | −0.1214 | 0.068 | 0.691 | 0 | −1,322.8 |
| `1..11` | 11,770 | −0.03062 | −0.05919 | −0.0720 | −0.1391 | 0.067 | 0.671 | 0 | −1,637.0 |
| `11..1` | 10,898 | −0.03853 | −0.06545 | −0.0978 | −0.1661 | 0.068 | 0.397 | 1 | −1,810.3 |
| `.1.11` | 11,648 | −0.04785 | −0.07699 | −0.1136 | −0.1828 | 0.069 | 0.646 | 0 | −2,129.5 |
| `1...1` | 11,770 | −0.04907 | −0.07764 | −0.1153 | −0.1824 | 0.067 | 0.388 | 1 | −2,147.3 |
| `111..` | 10,413 | −0.01464 | −0.07808 | −0.0389 | −0.2074 | 0.169 | 0.400 | 1 | −2,159.5 |
| `.11..` | 10,414 | −0.01467 | −0.07812 | −0.0390 | −0.2075 | 0.169 | 0.400 | 1 | −2,160.7 |
| `1.1..` | 10,465 | −0.01461 | −0.07831 | −0.0386 | −0.2070 | 0.168 | 0.400 | 1 | −2,166.0 |
| `..1..` | 10,466 | −0.01464 | −0.07835 | −0.0387 | −0.2071 | 0.168 | 0.400 | 1 | −2,167.1 |
| `...11` | 12,520 | −0.05757 | −0.08836 | −0.1272 | −0.1952 | 0.068 | 0.631 | 0 | −2,443.7 |
| `.1..1` | 11,648 | −0.06532 | −0.09447 | −0.1551 | −0.2243 | 0.069 | 0.372 | 0 | −2,612.8 |
| `....1` | 12,520 | −0.07587 | −0.10665 | −0.1676 | −0.2356 | 0.068 | 0.365 | 0 | −2,949.7 |
| `11.1.` | 22,644 | −0.05260 | −0.20972 | −0.0643 | −0.2562 | 0.192 | 0.680 | 0 | −5,800.5 |
| `1..1.` | 23,901 | −0.06651 | −0.22821 | −0.0770 | −0.2641 | 0.187 | 0.668 | 0 | −6,311.8 |
| `11...` | 22,644 | −0.09608 | −0.25320 | −0.1174 | −0.3093 | 0.192 | 0.361 | 0 | −7,002.9 |
| `1....` | 23,901 | −0.11057 | −0.27227 | −0.1280 | −0.3151 | 0.187 | 0.357 | 0 | −7,530.5 |
| `.1.1.` | 26,160 | −0.17930 | −0.36194 | −0.1896 | −0.3827 | 0.193 | 0.589 | 0 | −10,010.6 |
| `...1.` | 27,417 | −0.19320 | −0.38043 | −0.1949 | −0.3838 | 0.189 | 0.583 | 0 | −10,522.0 |
| `.1...` | 26,160 | −0.22266 | −0.40530 | −0.2354 | −0.4285 | 0.193 | 0.313 | 0 | −11,209.8 |
| `.....` | 27,417 | −0.23715 | −0.42438 | −0.2392 | −0.4281 | 0.189 | 0.311 | 0 | −11,737.4 |

**`A3_DELAY` alone (`..1..`) removes 93.8 % of the whole gross deficit** (−0.23715 → −0.01464 per
opportunity). Adding `A1_STOPVALID` on top of it changes the book by 0.00004 R.

---

## 4. Marginals, ablation, interaction — the three-month answer

### 4.1 Each lever ALONE (baseline + one), Δ net R per opportunity

| lever | 2026-01 | 2026-02 | 2026-03 |
|---|---:|---:|---:|
| A1_STOPVALID | +0.15211 | +0.08870 | +0.06585 |
| A2_NOMKT | +0.01908 | +0.02034 | +0.02745 |
| A3_DELAY | +0.34602 | +0.28406 | +0.25674 |
| B1_EXIT | +0.04395 | +0.04011 | +0.05831 |
| C1_GATE | +0.31773 | +0.24476 | +0.16365 |
| C2_DEPTH | +0.38715 | +0.30756 | +0.27880 |
| **SUM of alone** | **+1.26603** | **+0.98553** | **+0.85081** |
| **JOINT (all six)** | **+0.42086** | **+0.34035** | **+0.31166** |
| **OVERLAP** | **66.8 %** | **65.5 %** | **63.4 %** |

### 4.2 ABLATION — full stack MINUS one lever

| lever removed | 2026-01 | 2026-02 | 2026-03 | n trades (Jan, without it) |
|---|---:|---:|---:|---:|
| A1_STOPVALID | **0.00000** | **0.00000** | **0.00000** | 1,855 |
| A2_NOMKT | **0.00000** | **0.00000** | **0.00000** | 1,855 |
| A3_DELAY | +0.00051 | +0.00052 | +0.00057 | 1,894 |
| B1_EXIT | +0.00840 | +0.00525 | +0.01676 | 1,855 |
| C1_GATE | +0.01146 | +0.00717 | +0.00344 | 4,469 |
| C2_DEPTH | +0.00793 | +0.00416 | +0.00288 | 5,061 |
| **SUM of ablation marginals** | +0.02829 | +0.01710 | +0.02364 | |

The six ablation marginals sum to **6.7 % (Jan), 5.0 % (Feb), 7.6 % (Mar) of the joint effect.** The
stack is massively over-determined: remove any one lever and the book barely moves, because five
others are already doing its job.

### 4.3 Decline-set geometry (January, cost-free — pure population overlap)

| pair | n(A) | n(B) | ∩ | Jaccard | containment |
|---|---:|---:|---:|---:|---|
| A1_STOPVALID & A2_NOMKT | 3,516 | 1,265 | 0 | 0.000 | disjoint by construction |
| A1_STOPVALID & A3_DELAY | 3,516 | 16,951 | **3,515** | 0.207 | **99.97 % of A1 ⊂ A3** |
| A1_STOPVALID & C1_GATE | 3,516 | 15,029 | 2,766 | 0.175 | 78.7 % of A1 |
| A1_STOPVALID & C2_DEPTH | 3,516 | 23,065 | 3,516 | 0.152 | **A1 ⊂ C2 exactly** |
| A2_NOMKT & A3_DELAY | 1,265 | 16,951 | 1,205 | 0.071 | 95.3 % of A2 |
| A2_NOMKT & C1_GATE | 1,265 | 15,029 | 388 | 0.024 | 30.7 % of A2 |
| A2_NOMKT & C2_DEPTH | 1,265 | 23,065 | 1,265 | 0.055 | **A2 ⊂ C2 exactly** |
| A3_DELAY & C1_GATE | 16,951 | 15,029 | 9,517 | 0.424 | |
| A3_DELAY & C2_DEPTH | 16,951 | 23,065 | 16,827 | 0.726 | 99.3 % of A3 ⊂ C2 |
| C1_GATE & C2_DEPTH | 15,029 | 23,065 | 12,330 | 0.479 | |

### 4.4 Pairwise interaction, January (Δ of i alone vs Δ of i given j, all other levers off)

| i given j | alone | given j | interaction | kind |
|---|---:|---:|---:|---|
| A3_DELAY given C2_DEPTH | +0.34602 | +0.00290 | −0.34313 | substitute |
| C2_DEPTH given A3_DELAY | +0.38715 | +0.04403 | −0.34313 | substitute |
| C1_GATE given C2_DEPTH | +0.31773 | +0.02436 | −0.29337 | substitute |
| C2_DEPTH given C1_GATE | +0.38715 | +0.09378 | −0.29337 | substitute |
| A3_DELAY given C1_GATE | +0.34602 | +0.08253 | −0.26349 | substitute |
| C1_GATE given A3_DELAY | +0.31773 | +0.05424 | −0.26349 | substitute |
| A1_STOPVALID given C2_DEPTH | +0.15211 | +0.00000 | −0.15211 | substitute (total) |
| C2_DEPTH given A1_STOPVALID | +0.38715 | +0.23505 | −0.15211 | substitute |
| A1_STOPVALID given A3_DELAY | +0.15211 | +0.00004 | −0.15206 | substitute (total) |
| A3_DELAY given A1_STOPVALID | +0.34602 | +0.19396 | −0.15206 | substitute |
| A1_STOPVALID given C1_GATE | +0.15211 | +0.02901 | −0.12309 | substitute |
| C1_GATE given A1_STOPVALID | +0.31773 | +0.19464 | −0.12309 | substitute |
| A1_STOPVALID given A2_NOMKT | +0.15211 | +0.15211 | 0.00000 | independent |
| A2_NOMKT given A1_STOPVALID | +0.01908 | +0.01908 | 0.00000 | independent |
| A1_STOPVALID given B1_EXIT | +0.15211 | +0.15222 | **+0.00012** | "complement" |
| B1_EXIT given A1_STOPVALID | +0.04395 | +0.04406 | **+0.00012** | "complement" |

**Census over all 30 ordered pairs: 26 substitutes, 2 independent, 2 complements — and both
complements are +0.00012 R, i.e. rounding.** The only pair that is genuinely independent
(A1 & A2) is independent because their decline sets are *disjoint by definition*, not because they
measure different things.

**Why.** `mkt_r` — how far the entry sits from the decision-instant market, in R — is a single axis.
`born_past_stop` is `mkt_r ≤ −1`, `born_marketable` is `−1 < mkt_r < 0`, `born_at_limit` is
`mkt_r = 0`, `DEPTH` is `mkt_r ≥ 1`. A bar-1 fill is what happens when `mkt_r ≤ 0`. And `cost_r` is
`spread_price / risk_distance`, which l5-F3 measured is a rank-perfect proxy for `1/risk_distance`
(Spearman ≥ 0.9966 on 18 of 24 symbols). Six wave-1 lanes found six defects. **They are two
quantities: where the entry sits relative to the market, and how tight the stop is.**

---

## 5. The stacked book, stated plainly

`FULL` = all six levers, contract TRAIL025, depth 1.0 R, broker-true cost.

| | n pool | n trades | gross/trade | cost/trade | **net/trade** | net/opp | total net R | win | t | days net+ | max DD (R) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-01 as-shipped | 27,658 | 27,417 | −0.2392 | 0.1889 | −0.4281 | −0.42438 | −11,737.4 | 0.311 | −63.89 | 0/21 | −11,737.4 |
| **2026-01 FULL** | 27,658 | 1,855 | +0.0197 | 0.0721 | **−0.0524** | −0.00352 | −97.3 | 0.750 | −4.01 | 7/21 | −97.3 |
| 2026-02 as-shipped | 24,239 | 23,901 | −0.1885 | 0.1561 | −0.3445 | −0.33974 | −8,235.0 | 0.331 | −47.51 | 0/20 | −8,235.0 |
| **2026-02 FULL** | 24,239 | 2,368 | +0.0782 | 0.0720 | **+0.0062** | +0.00060 | +14.6 | 0.785 | +0.49 | 9/20 | −89.5 |
| 2026-03 as-shipped | 26,500 | 26,240 | −0.1899 | 0.1242 | −0.3141 | −0.31104 | −8,242.5 | 0.329 | −46.19 | 0/22 | −8,242.5 |
| **2026-03 FULL** | 26,500 | 3,202 | +0.0684 | 0.0633 | **+0.0052** | +0.00063 | +16.6 | 0.794 | +0.52 | 12/22 | −79.3 |

Day-block bootstrap on net R per opportunity (400 resamples, seed 20260806):

| month | observed | 95 % CI | P(≤ 0) | days |
|---|---:|---|---:|---:|
| 2026-01 | −0.003517 | [−0.006978, +0.000231] | 0.9650 | 21 |
| 2026-02 | +0.000604 | [−0.004842, +0.005863] | 0.4125 | 20 |
| 2026-03 | +0.000625 | [−0.003837, +0.005681] | 0.3850 | 22 |

Three-month total: **−66.1 R on 7,425 trades = −0.0089 R/trade.** Neither positive month is
significant (t = 0.49, 0.52). The stack removes 99.2 % / 100.2 % / 100.2 % of the deficit and lands
on zero.

**Equity path, FULL stack, daily cumulative net-true R** (`E_EQUITY_V1.json`):

- 2026-01: −18.1 −15.7 −18.8 −23.2 −23.9 −31.0 −25.4 −19.8 −36.9 −43.9 −42.8 −46.2 −59.5 −33.8 −58.4 −51.5 −61.2 −70.0 −62.9 −84.7 **−97.3**
- 2026-02: +13.7 +10.0 +33.3 +17.8 −2.6 −19.9 −4.7 −27.2 −23.5 −27.7 −22.7 −32.6 −44.4 −56.2 −27.1 −14.6 −6.5 +20.4 +15.0 **+14.6**
- 2026-03: −15.5 +4.0 +13.6 +35.1 +28.4 +43.8 +34.1 +49.1 +62.5 +38.2 +33.6 +37.8 +31.4 +20.2 +4.3 −16.9 −6.5 +3.5 +14.1 +18.0 +15.8 **+16.6**

February's path draws down to −56.2 R (n = 2,368, i.e. −3.8 × its own final gain) before recovering
in the last three days. March peaks at +62.5 on day 9 and gives back 74 %. Neither is a book.

**Composition of the FULL stack** (top symbols / families):

| month | top symbols | top families |
|---|---|---|
| 2026-01 | XAUUSD 419, US30_cash 216, GER40 210, NAS100 207, JP225 134 | current_fvg_fill 1,203 · current_ob_retest 455 · current_breaker_re_entry 197 |
| 2026-02 | XAUUSD 613, GER40 306, US30_cash 225, JP225 177, UK100 173 | current_fvg_fill 1,679 · current_ob_retest 524 · current_breaker_re_entry 165 |
| 2026-03 | XAUUSD 823, GER40 384, UK100 347, US30_cash 313, NAS100 245 | current_fvg_fill 2,432 · current_ob_retest 599 · current_breaker_re_entry 171 |

---

## 6. The caveat that governs everything above — the stack selects the one cohort the pool cannot sample

`v4_timewarp_simulated_live_research_loop.py:60309-60310` returns `None` for any candidate whose entry
was never traded, and the pool filter requires `opportunity_net_proxy_r is not None`. **The pool
therefore contains no resting limit that failed to fill** (l7-F4). Measured here on all three months,
against a symmetric control — the mirror level at the same distance on the *other* side of the market,
which price must reach for the same "the market came to me" event to have occurred by chance:

| month | cohort | n | P(entry touched) | P(mirror touched) | magnet |
|---|---|---:|---:|---:|---:|
| 2026-01 | all resting | 7,949 | 0.9996 | 0.3682 | 2.715× |
| 2026-01 | **depth ≥ 1 R** | 4,593 | **1.0000** | **0.1866** | **5.359×** |
| 2026-01 | depth ≥ 2 R | 2,171 | 1.0000 | 0.1193 | 8.382× |
| 2026-02 | all resting | 7,019 | 0.9994 | 0.3726 | 2.683× |
| 2026-02 | **depth ≥ 1 R** | 4,015 | **1.0000** | **0.1811** | **5.523×** |
| 2026-02 | depth ≥ 2 R | 1,820 | 1.0000 | 0.1060 | 9.430× |
| 2026-03 | all resting | 8,468 | 0.9996 | 0.3674 | 2.721× |
| 2026-03 | **depth ≥ 1 R** | 4,603 | **1.0000** | **0.1758** | **5.690×** |
| 2026-03 | depth ≥ 2 R | 2,068 | 1.0000 | 0.0924 | 10.827× |

`C2_DEPTH` selects `mkt_r ≥ 1 R`, i.e. exactly the cohort where the pool's fill rate is 100.00 % and
the honest one is 17.6–18.7 %. **The February and March positives in §5 are measured on a population
that is conditioned on the fill, by a factor of 5.4–5.7×, in every month.** The magnitude of the
resulting bias is measured directly in §7.2 (the same instrument, same month, same contract, books
+0.154 R/trade in the conditioned cohort and −0.025 in the unconditioned one).

---

## 7. The live-expressible stack — the only version that can reach a book

l10-X3 measured 296/296 live broker captures where the requested entry price **equals** the executable
quote to floating-point exactness; `TRADE_ACTION_PENDING` is defined once in
`src/mt5/mt5_interface.py:63` and never used for an entry. **The live engine has never placed a limit
order and cannot.** The only cohort it can express is `born_at_limit` — entry price = the
decision-instant market price — which is also the only cohort free of §6's conditioning, because an
at-market order fills by definition and nothing was dropped upstream.

Cohort sizes: **Jan 14,905 · Feb 13,966 · Mar 14,884 = 43,755 candidates.**

The lever available there is not a *selection* but a *re-timing*: enter at the CLOSE of path bar k
(fully knowable at that instant), walk the same contract from bar k+1, R frame rebased by the new
entry (`r_new = r_old − cls[k−1]`), stop still at −1 R from the new entry.

### 7.1 delay × contract, gross R/trade / net-true R/trade

**2026-01, n = 14,905**

| k | INC | TRAIL025 | TS90S1 | STOPONLY | T3S1 | TS60S1 |
|---:|---|---|---|---|---|---|
| 0 | −0.0597/−0.2718 | −0.0101/−0.2223 | −0.0298/−0.2420 | −0.0461/−0.2583 | −0.0558/−0.2680 | −0.0301/−0.2423 |
| 1 | −0.0039/−0.2161 | +0.0333/−0.1789 | +0.0285/−0.1837 | +0.0190/−0.1932 | +0.0009/−0.2113 | +0.0187/−0.1935 |
| 2 | −0.0085/−0.2207 | +0.0365/−0.1757 | +0.0185/−0.1936 | +0.0100/−0.2022 | −0.0008/−0.2130 | +0.0142/−0.1980 |
| 3 | +0.0004/−0.2118 | +0.0412/−0.1710 | +0.0339/−0.1783 | +0.0262/−0.1860 | +0.0097/−0.2025 | +0.0281/−0.1841 |
| 5 | +0.0072/−0.2050 | **+0.0450**/−0.1672 | +0.0255/−0.1867 | +0.0153/−0.1969 | +0.0081/−0.2041 | +0.0242/−0.1880 |
| 10 | −0.0009/−0.2130 | +0.0375/−0.1746 | +0.0217/−0.1904 | +0.0081/−0.2040 | +0.0094/−0.2027 | +0.0222/−0.1899 |
| 15 | −0.0031/−0.2152 | +0.0414/−0.1707 | +0.0139/−0.1981 | +0.0055/−0.2066 | +0.0079/−0.2042 | +0.0106/−0.2015 |
| 20 | −0.0008/−0.2127 | +0.0431/−0.1689 | +0.0327/−0.1793 | +0.0294/−0.1825 | +0.0044/−0.2075 | +0.0252/−0.1867 |
| 30 | −0.0191/−0.2310 | +0.0413/−0.1706 | +0.0117/−0.2002 | +0.0093/−0.2026 | −0.0064/−0.2183 | +0.0095/−0.2023 |
| 45 | −0.0030/−0.2154 | +0.0360/−0.1763 | +0.0223/−0.1900 | +0.0170/−0.1954 | +0.0066/−0.2058 | +0.0145/−0.1979 |
| 60 | −0.0085/−0.2210 | +0.0279/−0.1846 | +0.0037/−0.2088 | +0.0045/−0.2079 | −0.0042/−0.2167 | +0.0000/−0.2124 |

**2026-02, n = 13,966**

| k | INC | TRAIL025 | TS90S1 | STOPONLY | T3S1 | TS60S1 |
|---:|---|---|---|---|---|---|
| 0 | −0.0569/−0.2419 | −0.0241/−0.2090 | −0.0606/−0.2456 | −0.0461/−0.2311 | −0.0467/−0.2316 | −0.0750/−0.2599 |
| 1 | −0.0165/−0.2015 | +0.0334/−0.1515 | −0.0049/−0.1898 | +0.0128/−0.1722 | −0.0043/−0.1893 | −0.0274/−0.2123 |
| 2 | −0.0033/−0.1883 | +0.0426/−0.1424 | +0.0042/−0.1808 | +0.0284/−0.1566 | +0.0072/−0.1778 | −0.0181/−0.2030 |
| 3 | −0.0010/−0.1860 | +0.0413/−0.1437 | +0.0105/−0.1745 | +0.0350/−0.1499 | +0.0129/−0.1721 | −0.0115/−0.1964 |
| 5 | +0.0092/−0.1758 | +0.0388/−0.1462 | +0.0224/−0.1626 | +0.0447/−0.1402 | +0.0187/−0.1663 | +0.0024/−0.1826 |
| 10 | +0.0167/−0.1682 | +0.0383/−0.1466 | +0.0276/−0.1573 | +0.0465/−0.1384 | +0.0243/−0.1606 | +0.0023/−0.1826 |
| 15 | +0.0147/−0.1703 | +0.0381/−0.1468 | +0.0244/−0.1605 | +0.0415/−0.1435 | +0.0253/−0.1596 | +0.0047/−0.1802 |
| 20 | +0.0269/−0.1581 | +0.0423/−0.1427 | +0.0225/−0.1625 | +0.0414/−0.1436 | +0.0307/−0.1542 | +0.0075/−0.1775 |
| 30 | +0.0131/−0.1716 | **+0.0521**/−0.1326 | +0.0230/−0.1617 | +0.0489/−0.1358 | +0.0235/−0.1612 | +0.0084/−0.1763 |
| 45 | +0.0195/−0.1655 | +0.0466/−0.1384 | +0.0222/−0.1627 | +0.0462/−0.1388 | +0.0291/−0.1559 | −0.0054/−0.1904 |
| 60 | +0.0189/−0.1665 | +0.0466/−0.1388 | +0.0242/−0.1612 | +0.0478/−0.1376 | +0.0307/−0.1547 | +0.0000/−0.1854 |

**2026-03, n = 14,884**

| k | INC | TRAIL025 | TS90S1 | STOPONLY | T3S1 | TS60S1 |
|---:|---|---|---|---|---|---|
| 0 | −0.0796/−0.2281 | −0.0334/−0.1819 | −0.0452/−0.1937 | −0.0487/−0.1972 | −0.0775/−0.2260 | −0.0434/−0.1920 |
| 1 | −0.0176/−0.1661 | +0.0235/−0.1251 | +0.0101/−0.1384 | +0.0046/−0.1439 | −0.0159/−0.1644 | +0.0101/−0.1384 |
| 2 | −0.0131/−0.1616 | +0.0317/−0.1169 | +0.0171/−0.1314 | +0.0168/−0.1317 | −0.0064/−0.1549 | +0.0130/−0.1355 |
| 3 | −0.0118/−0.1603 | +0.0256/−0.1229 | +0.0270/−0.1215 | +0.0267/−0.1218 | −0.0024/−0.1509 | +0.0186/−0.1299 |
| 5 | −0.0139/−0.1624 | +0.0312/−0.1173 | +0.0086/−0.1399 | +0.0070/−0.1415 | −0.0062/−0.1547 | +0.0008/−0.1477 |
| 10 | +0.0001/−0.1483 | +0.0366/−0.1118 | +0.0411/−0.1073 | +0.0427/−0.1057 | +0.0071/−0.1413 | +0.0331/−0.1153 |
| 15 | −0.0011/−0.1495 | +0.0341/−0.1143 | +0.0312/−0.1172 | +0.0296/−0.1188 | +0.0061/−0.1423 | +0.0308/−0.1175 |
| 20 | −0.0100/−0.1584 | +0.0384/−0.1100 | +0.0290/−0.1194 | +0.0194/−0.1290 | −0.0012/−0.1496 | +0.0120/−0.1364 |
| 30 | −0.0098/−0.1581 | **+0.0405**/−0.1077 | +0.0302/−0.1180 | +0.0163/−0.1319 | −0.0054/−0.1536 | +0.0178/−0.1304 |
| 45 | +0.0016/−0.1466 | +0.0329/−0.1154 | +0.0268/−0.1215 | +0.0166/−0.1317 | +0.0096/−0.1387 | +0.0098/−0.1385 |
| 60 | −0.0053/−0.1535 | +0.0340/−0.1142 | +0.0254/−0.1228 | +0.0109/−0.1372 | +0.0019/−0.1463 | +0.0000/−0.1482 |

**k = 0 — entering at the decision instant, as shipped — is gross-negative in all 18 month × contract
cells. Every k ≥ 1 with TRAIL025 is gross-positive in all three months.**

### 7.2 The at-market ablation (D = delay 5 min, E = TRAIL025, G = broker-true cost gate)

| arm | 2026-01 n / gross / cost / net / net-per-opp | 2026-02 | 2026-03 |
|---|---|---|---|
| D0E0G0 | 14,905 / −0.0597 / 0.2122 / −0.2718 / −0.27185 | 13,966 / −0.0569 / 0.1850 / −0.2419 / −0.24190 | 14,884 / −0.0796 / 0.1485 / −0.2281 / −0.22811 |
| D0E0G1 | 7,317 / −0.0564 / 0.0687 / −0.1251 / −0.06139 | 7,707 / −0.0063 / 0.0665 / −0.0728 / −0.04017 | 9,466 / −0.0579 / 0.0602 / −0.1181 / −0.07512 |
| D0E1G0 | 14,905 / −0.0101 / 0.2122 / −0.2223 / −0.22228 | 13,966 / −0.0241 / 0.1850 / −0.2090 / −0.20903 | 14,884 / −0.0334 / 0.1485 / −0.1819 / −0.18186 |
| D0E1G1 | 7,317 / −0.0199 / 0.0687 / −0.0886 / −0.04351 | 7,707 / −0.0050 / 0.0665 / −0.0715 / −0.03946 | 9,466 / −0.0304 / 0.0602 / −0.0907 / −0.05765 |
| D1E0G0 | 14,905 / +0.0072 / 0.2122 / −0.2050 / −0.20495 | 13,966 / +0.0092 / 0.1850 / −0.1758 / −0.17579 | 14,884 / −0.0139 / 0.1485 / −0.1624 / −0.16239 |
| D1E0G1 | 7,317 / −0.0266 / 0.0687 / −0.0953 / −0.04679 | 7,707 / +0.0148 / 0.0665 / −0.0517 / **−0.02855** | 9,466 / −0.0152 / 0.0602 / −0.0755 / −0.04799 |
| D1E1G0 | 14,905 / +0.0450 / 0.2122 / −0.1672 / −0.16718 | 13,966 / +0.0388 / 0.1850 / −0.1462 / −0.14615 | 14,884 / +0.0312 / 0.1485 / −0.1173 / −0.11727 |
| **D1E1G1** | 7,317 / +0.0169 / 0.0687 / −0.0518 / **−0.02542** | 7,707 / +0.0116 / 0.0665 / −0.0549 / −0.03032 | 9,466 / +0.0066 / 0.0602 / −0.0536 / **−0.03410** |

**Every arm of the live-expressible stack is net-negative in every month.** Best is −0.0518 R/trade
(Jan), −0.0517 (Feb), −0.0536 (Mar).

**Pooled over three months (n = 43,755 / 24,490 gated):**

| arm | n | gross | t(gross) | cost | net | t(net) |
|---|---:|---:|---:|---:|---:|---:|
| D0E0G0 | 43,755 | −0.0656 | −11.79 | 0.1818 | −0.2474 | −43.65 |
| D0E0G1 | 24,490 | −0.0412 | −6.16 | 0.0647 | −0.1059 | −15.83 |
| D0E1G0 | 43,755 | −0.0225 | −6.25 | 0.1818 | −0.2043 | −54.84 |
| D0E1G1 | 24,490 | −0.0193 | −5.08 | 0.0647 | −0.0840 | −22.11 |
| D1E0G0 | 43,755 | +0.0007 | +0.12 | 0.1818 | −0.1812 | −31.72 |
| D1E0G1 | 24,490 | −0.0092 | −1.38 | 0.0647 | −0.0739 | −11.08 |
| **D1E1G0** | 43,755 | **+0.0383** | **+12.35** | 0.1818 | −0.1435 | −44.88 |
| D1E1G1 | 24,490 | +0.0113 | +3.15 | 0.0647 | −0.0535 | −14.91 |

**GROSS ADDITIVITY, the one place the levers add up:** delay alone +0.06624, exit alone +0.04311,
sum +0.10935, joint +0.10392 → **overlap 5.0 %.** These two are complements, and they are the two
that operate on *different objects* (the entry instant and the exit rule) rather than on the same
`mkt_r` axis.

**Equity, at-market D1E1G0** (all 43,755 candidates traded, no selection at all):
gross +670.8 R (Jan) / +541.9 (Feb) / +464.9 (Mar) = **+1,677.6 R gross**;
net −2,491.8 / −2,041.2 / −1,745.5 = **−6,278.5 R**. **Zero net-positive days in 63.**

### 7.2b Significance and de-duplication of the one real finding

Day-block bootstrap of the **gross** edge of the delay+trail arm (D1E1G0), pooled over all 63 trading
days of the three months, 2,000 resamples, seed 20260806:

| | value |
|---|---|
| observed gross R/trade | **+0.038342** |
| 95 % CI | **[+0.030076, +0.046177]** |
| P(≤ 0) | **0.0000** |
| n | 43,755 trades over 63 days |
| days with positive gross | **53 / 63** — Jan 20/21 (mean +0.04501), Feb 17/20 (+0.03880), Mar 16/22 (+0.03123) |

De-duplication (W0-F1 pseudo-replication) does not touch it: the at-market cohort is **99.35 %
first-emission** (14,808 of 14,905 in January, the only month where the flag exists), and on
first emissions only the numbers are `K0_INC` −0.059388 (all: −0.059658), `K5_TRAIL025` +0.045589
(all: +0.045007), **delay gain +0.066119 (all: +0.066894)**.

So the gross edge is real, significant, day-stable and dedup-robust. It is also 0.231 bps against a
2.457 bps toll.

### 7.3 What the delay lever IS — measured, not inferred

Mean signed R of the market against the signal, at-market cohort, at k minutes after the decision
(`E_ENTRY_DRIFT_V1.json`):

| k (min) | 2026-01 R / bps | 2026-02 R / bps | 2026-03 R / bps |
|---:|---|---|---|
| 1 | −0.064669 / −0.657 | −0.076711 / −0.831 | −0.067815 / −1.131 |
| 2 | −0.067941 / −0.624 | −0.086186 / −1.075 | −0.066937 / −1.059 |
| 3 | −0.072941 / −0.736 | −0.088508 / −1.163 | −0.063831 / −1.142 |
| 5 | −0.074037 / −0.908 | −0.094387 / −0.984 | −0.064852 / −1.343 |
| 10 | −0.064993 / −0.961 | −0.095784 / −1.341 | −0.074744 / −1.948 |
| 15 | −0.064089 / −0.927 | −0.103559 / −1.628 | −0.075328 / −2.191 |
| 30 | −0.063113 / −1.138 | −0.121534 / −1.697 | −0.061945 / −2.164 |
| 60 | −0.062381 / −0.829 | −0.133597 / −1.927 | −0.035917 / −2.657 |

Measured gain of delaying to k = 5, on the shipped 2R/−1R contract:
**+0.06689 (Jan) · +0.06610 (Feb) · +0.06572 (Mar)** — three independent months agreeing to three
significant figures, and matching l7-F1's independently-measured +0.0670 on January alone.

That gain is exactly the entry concession: **the market is −0.065 to −0.077 R worse than the price the
generator takes, within sixty seconds, and the entire delay lever is recovering it.** All seven
generating families enter at `entry = bar.close` — the extreme of the very bar whose extremeness
triggered them (l7-F5, `broader_origin_generators.py:745-752, :862-897, :1023-1032`). The lever is
not a forecast; it is declining to pay for the trigger bar's own tail.

In price units the concession is **0.66–1.13 bps** against a broker-true round-trip of **2.457 bps** —
27–46 % of the toll, recoverable, and not enough.

### 7.4 Where the money goes — cost bands and geometry, at-market k = 5 TRAIL025

By broker-true cost band, n / gross / cost / net:

| band (R) | 2026-01 | 2026-02 | 2026-03 |
|---|---|---|---|
| 0–0.02 | 613 / +0.0320 / 0.0139 / **+0.0181** | 807 / +0.0043 / 0.0136 / −0.0093 | 1,543 / +0.0152 / 0.0125 / **+0.0027** |
| 0.02–0.04 | 1,325 / +0.0158 / 0.0301 / −0.0143 | 1,448 / +0.0246 / 0.0302 / −0.0057 | 1,940 / +0.0001 / 0.0295 / −0.0294 |
| 0.04–0.06 | 1,391 / +0.0326 / 0.0501 / −0.0175 | 1,431 / +0.0175 / 0.0497 / −0.0322 | 1,628 / −0.0027 / 0.0497 / −0.0524 |
| 0.06–0.08 | 1,303 / −0.0014 / 0.0700 / −0.0713 | 1,272 / +0.0196 / 0.0696 / −0.0500 | 1,465 / −0.0004 / 0.0696 / −0.0699 |
| 0.08–0.12 | 2,100 / +0.0203 / 0.0993 / −0.0790 | 2,184 / +0.0127 / 0.0991 / −0.0864 | 2,333 / +0.0197 / 0.0987 / −0.0790 |
| 0.12–0.20 | 3,025 / +0.0237 / 0.1549 / −0.1312 | 2,661 / +0.0204 / 0.1544 / −0.1339 | 2,467 / +0.0373 / 0.1554 / −0.1182 |
| 0.20–0.40 | 3,040 / +0.0603 / 0.2826 / −0.2223 | 2,549 / +0.0665 / 0.2813 / −0.2148 | 2,311 / +0.0753 / 0.2788 / −0.2035 |
| 0.40+ | 2,108 / +0.1370 / 0.6722 / −0.5352 | 1,614 / +0.1247 / 0.6347 / −0.5100 | 1,197 / +0.1123 / 0.5791 / −0.4669 |

By risk-distance decile (cuts frozen on January so February and March are read out of month), pooled
across three months:

| decile | Jan median stop (% of price) | n | gross | cost | net | **edge : cost** | t |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0188 % | 3,526 | +0.1417 | 0.5694 | −0.4277 | 0.249 | −26.54 |
| 1 | 0.0325 % | 3,662 | +0.0961 | 0.3164 | −0.2203 | 0.304 | −16.55 |
| 2 | 0.0481 % | 3,976 | +0.0621 | 0.2244 | −0.1623 | 0.277 | −14.96 |
| 3 | 0.0667 % | 4,037 | +0.0178 | 0.1795 | −0.1617 | 0.099 | −15.99 |
| 4 | 0.0890 % | 4,104 | +0.0254 | 0.1506 | −0.1251 | 0.169 | −12.41 |
| 5 | 0.1193 % | 4,318 | +0.0240 | 0.1286 | −0.1047 | 0.186 | −11.20 |
| 6 | 0.1613 % | 4,627 | +0.0307 | 0.1268 | −0.0961 | 0.242 | −10.23 |
| 7 | 0.2324 % | 4,665 | +0.0200 | 0.1157 | −0.0957 | 0.173 | −11.24 |
| 8 | 0.3805 % | 4,815 | +0.0058 | 0.0970 | −0.0912 | 0.059 | −10.90 |
| 9 | 0.8043 % | 6,025 | +0.0061 | 0.0675 | −0.0614 | 0.091 | −9.17 |

**The edge : cost ratio never exceeds 0.31 in any decile of any month.** It is not a cost-band
problem and not a stop-width problem: it is flat-and-losing across a 43× range of cost and a 43×
range of stop width.

### 7.5 Per symbol, at-market k = 5 TRAIL025, pooled three months

| symbol | n | gross R | cost R | **net R** | t | edge bps | cost bps | ratio | Jan / Feb / Mar net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **GER40** | 1,858 | +0.0646 | 0.0466 | **+0.0180** | +1.23 | +0.911 | 0.501 | **1.39** | +0.012 / +0.019 / +0.023 |
| US30_cash | 1,942 | +0.0325 | 0.0519 | −0.0194 | −1.43 | +0.375 | 0.403 | 0.63 | −0.060 / −0.006 / +0.011 |
| XAUUSD | 1,996 | +0.0466 | 0.0713 | −0.0247 | −1.77 | +0.906 | 1.282 | 0.65 | −0.034 / −0.049 / +0.009 |
| NAS100 | 1,904 | +0.0237 | 0.0516 | −0.0279 | −2.05 | +0.259 | 0.575 | 0.46 | −0.032 / +0.004 / −0.053 |
| UK100 | 2,002 | +0.0615 | 0.1015 | −0.0399 | −2.78 | +0.726 | 0.822 | 0.61 | −0.085 / −0.024 / −0.014 |
| JP225 | 1,627 | +0.0348 | 0.0795 | −0.0448 | −2.96 | +1.297 | 1.462 | 0.44 | −0.070 / −0.025 / −0.040 |
| BTCUSD | 1,415 | +0.0422 | 0.1227 | −0.0805 | −4.77 | −0.255 | 4.593 | 0.34 | −0.096 / −0.085 / −0.061 |
| SPX500 | 1,850 | +0.0249 | 0.1184 | −0.0935 | −6.50 | +0.429 | 0.941 | 0.21 | −0.163 / −0.039 / −0.071 |
| EURUSD | 1,863 | +0.0586 | 0.1692 | −0.1106 | −6.61 | +0.083 | 0.686 | 0.35 | −0.127 / −0.124 / −0.085 |
| USDJPY | 2,442 | +0.0643 | 0.1837 | −0.1194 | −9.04 | +0.317 | 0.829 | 0.35 | −0.082 / −0.141 / −0.134 |
| GBPUSD | 2,054 | +0.0344 | 0.1557 | −0.1214 | −7.41 | −0.037 | 0.746 | 0.22 | −0.120 / −0.134 / −0.112 |
| AUDUSD | 1,627 | +0.0294 | 0.1518 | −0.1224 | −7.89 | −0.139 | 1.156 | 0.19 | −0.152 / −0.120 / −0.097 |
| USDCHF | 1,854 | +0.0443 | 0.2121 | −0.1679 | −10.26 | +0.125 | 1.117 | 0.21 | −0.168 / −0.201 / −0.139 |
| XAGUSD | 1,968 | +0.0360 | 0.2062 | −0.1702 | −11.37 | +0.561 | 9.670 | 0.17 | −0.211 / −0.128 / −0.163 |
| EURJPY | 1,564 | +0.0278 | 0.2143 | −0.1865 | −10.49 | +0.088 | 1.094 | 0.13 | −0.151 / −0.190 / −0.219 |
| ETHUSD | 1,366 | +0.0022 | 0.1908 | −0.1886 | −11.44 | −2.122 | 9.832 | 0.01 | −0.196 / −0.176 / −0.193 |
| CHFJPY | 1,547 | +0.0428 | 0.2385 | −0.1957 | −10.13 | +0.244 | 1.348 | 0.18 | −0.194 / −0.219 / −0.176 |
| AUDJPY | 1,604 | +0.0361 | 0.2321 | −0.1961 | −11.86 | +0.101 | 1.801 | 0.16 | −0.243 / −0.167 / −0.178 |
| GBPJPY | 1,978 | +0.0457 | 0.2455 | −0.1998 | −14.44 | +0.146 | 1.274 | 0.19 | −0.225 / −0.162 / −0.213 |
| USDCAD | 2,010 | +0.0205 | 0.2621 | −0.2416 | −15.61 | −0.118 | 0.851 | 0.08 | −0.245 / −0.258 / −0.223 |
| NZDUSD | 1,943 | +0.0371 | 0.2824 | −0.2454 | −14.61 | +0.020 | 1.883 | 0.13 | −0.290 / −0.241 / −0.206 |
| EURGBP | 1,865 | +0.0377 | 0.3166 | −0.2789 | −19.47 | +0.026 | 1.015 | 0.12 | −0.293 / −0.293 / −0.253 |
| USOIL_cash | 1,777 | +0.0352 | 0.3428 | −0.3076 | −18.91 | +0.348 | 9.772 | 0.10 | −0.402 / −0.399 / −0.112 |
| UKOIL_cash | 1,699 | +0.0152 | 0.3387 | −0.3235 | −18.98 | +0.530 | 8.710 | 0.04 | −0.436 / −0.363 / −0.150 |

**GER40 is the only symbol net-positive at broker truth, and it is positive in all three months**
(+0.012 / +0.019 / +0.023, n = 1,858, edge : cost 1.39, t = +1.23). One instrument out of 24, on a
4.2 %-of-population slice, at a t that does not clear any bar. It is a lead for the next month, not
a result.

Price-space totals, at-market k = 5 TRAIL025: **pooled edge +0.231 bps vs cost 2.457 bps (ratio
0.094)**; Jan +0.390 / 2.440 (0.160), Feb −0.027 / 2.507 (−0.011), Mar +0.314 / 2.428 (0.129).

---

## 8. The gold result, and why it is a measurement of the bias rather than an edge

On the fill-conditioned population (all born states, delay-selection on, TRAIL025), XAUUSD books:

| month | n | gross | **net (broker-true)** | t |
|---|---:|---:|---:|---:|
| 2026-01 | 1,594 | +0.2750 | **+0.1512** | +9.26 |
| 2026-02 | 1,535 | +0.2484 | **+0.1541** | +9.09 |
| 2026-03 | 1,747 | +0.2439 | **+0.1543** | +10.73 |

Three independent months, n ≈ 1,600 each, agreeing **to ±0.0016 R**, at t ≈ 9–11. It corroborates
l1-F5, which found XAUUSD net +0.1091 (t 4.545, n 2,329) on a completely different contract
(T0.75/S3.00) in January.

**And it is not tradeable.** The same instrument, same months, same contract, in the
fill-unconditioned at-market cohort books **−0.0247 R/trade** (§7.5). The gap of **0.179 R/trade** is
the fill-conditioning bias, measured on one instrument.

Diagnostic — gold is not *more* magnet-conditioned than anything else; it is more *R-leveraged*:

| month | XAU resting share | XAU median depth (R) | others | XAU mirror-touch | others | XAU median MFE (R) | others |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-01 | 64.6 % | 1.9085 | 1.0933 | 0.3719 | 0.3674 | **2.6841** | 1.0626 |
| 2026-02 | 66.9 % | 1.5653 | 1.0836 | 0.4000 | 0.3650 | **2.4641** | 1.1145 |
| 2026-03 | 69.9 % | 1.7975 | 0.9781 | 0.3582 | 0.3697 | **2.6961** | 1.1096 |

Gold's declared stop is small relative to its own 2-hour range — median MFE **2.5–2.7 R** against
1.06–1.11 R for every other symbol — so both its resting depths and its R-denominated excursions are
~2.5× everything else. Under fill conditioning that leverage becomes the whole number; without it,
it does not survive the spread.

---

## 9. Two negative results worth banking

**9.1 A tighter cost ceiling cannot rescue the book.** True-cost ceiling sweep on January
(delay + TRAIL025, no depth), train Jan 01–15 / test Jan 16–31:

| cap (R) | train n / gross / net | test n / gross / net | all n / gross / net / net-per-opp / t / days+ |
|---|---|---|---|
| 0.010 | 15 / −0.0093 / −0.0164 | 23 / +0.0137 / +0.0059 | 38 / +0.0046 / −0.0029 / −0.00000 / −0.04 / 6 |
| 0.015 | 31 / +0.0121 / +0.0023 | 152 / −0.0780 / −0.0895 | 183 / −0.0628 / −0.0739 / −0.00049 / −2.30 / 9 |
| 0.020 | 61 / +0.0414 / +0.0279 | 238 / −0.1192 / −0.1327 | 299 / −0.0864 / −0.0999 / −0.00108 / −3.70 / 11 |
| 0.025 | 106 / +0.0304 / +0.0130 | 318 / −0.1085 / −0.1244 | 424 / −0.0738 / −0.0900 / −0.00138 / −3.71 / 10 |
| 0.030 | 190 / +0.0295 / +0.0077 | 598 / −0.0547 / −0.0761 | 788 / −0.0344 / −0.0559 / −0.00159 / −3.27 / 10 |
| 0.040 | 367 / −0.0772 / −0.1057 | 858 / −0.0470 / −0.0726 | 1,225 / −0.0561 / −0.0825 / −0.00365 / −5.67 / 5 |
| 0.050 | 535 / −0.1269 / −0.1605 | 1,177 / −0.0113 / −0.0423 | 1,712 / −0.0474 / −0.0793 / −0.00491 / −6.13 / 7 |
| 0.075 | 1,024 / −0.0577 / −0.1048 | 2,043 / +0.0110 / −0.0336 | 3,067 / −0.0119 / −0.0574 / −0.00636 / −5.72 / 6 |
| 0.100 | 1,479 / −0.0329 / −0.0924 | 2,654 / +0.0262 / −0.0283 | 4,133 / +0.0051 / −0.0512 / −0.00765 / −5.88 / 7 |
| 0.150 | 2,580 / +0.0084 / −0.0795 | 3,722 / +0.0326 / −0.0413 | 6,302 / +0.0227 / −0.0569 / −0.01297 / −7.90 / 4 |
| 0.250 | 3,995 / +0.0479 / −0.0782 | 4,600 / +0.0351 / −0.0615 | 8,595 / +0.0410 / −0.0693 / −0.02152 / −10.70 / 3 |
| 0.500 | 4,761 / +0.0448 / −0.1164 | 5,234 / +0.0446 / −0.0812 | 9,995 / +0.0447 / −0.0980 / −0.03540 / −15.84 / 3 |
| 1.000 | 4,980 / +0.0491 / −0.1329 | 5,445 / +0.0516 / −0.0958 | 10,425 / +0.0504 / −0.1135 / −0.04280 / −18.48 / 2 |
| none | 5,001 / +0.0497 / −0.1369 | 5,465 / +0.0526 / −0.0992 | 10,466 / +0.0512 / −0.1172 / −0.04435 / −19.01 / 2 |

Tightening the ceiling from ∞ to 0.10 R cuts the cost 3× **and cuts the gross 10×** (+0.0512 →
+0.0051). Below 0.03 R the gross goes negative. There is no cost cap at which the trade is
net-positive at meaningful n; the apparent improvement in net-per-opportunity as the cap tightens is
the trivial fact that a book that trades 38 times has a per-opportunity number of zero.

**9.2 The best single conditioning cell on January is a fill-conditioning artifact.** On the
delay + TRAIL025 population (n = 10,466 in January), the only cohorts with net > −0.05 are XAUUSD
(+0.1512), USDCHF (−0.0395), GER40 (−0.0445); the best family is `regime_transition_break`
(−0.0013, n = 69) and the best session is `ny` (−0.0581, n = 1,816, train −0.0199 / test −0.0981).
`born` split: marketable −0.0670 (n 52), resting −0.1140 (n 7,037), at_limit −0.1251 (n 3,373).
Nothing but gold clears zero, and gold is §8.

---

## 10. Answers to the five questions asked

1. **The combined book.** January 1,855 trades, win 0.750, gross +0.0197 R/trade, broker-true cost
   0.0721, net **−0.0524 R/trade**, total −97.3 R, max DD −97.3 R, 7/21 days net-positive.
   February 2,368 trades, win 0.785, net **+0.0062**, total +14.6 R, DD −89.5, 9/20 days.
   March 3,202 trades, win 0.794, net **+0.0052**, total +16.6 R, DD −79.3, 12/22 days.
   Equity paths in §5.

2. **Ablation.** At the full stack: A1 and A2 contribute **exactly 0.00000** in all three months;
   A3 contributes +0.0005; the only levers with any residual value are B1 EXIT (+0.005…+0.017),
   C1 GATE (+0.003…+0.011) and C2 DEPTH (+0.003…+0.008). Full tables §4.2.

3. **Interaction structure.** 26 of 30 ordered pairs are **substitutes**; the two "independent" pairs
   are independent only because their decline sets are disjoint by definition; the two "complements"
   are +0.00012 R. `A1 ⊂ C2` and `A2 ⊂ C2` **exactly**; 99.97 % of `A1 ⊂ A3`. The exception, and the
   only genuine complement in the lane, is **entry re-timing × exit rule on the at-market cohort:
   95.0 % additive** (§7.2).

4. **February and March.** Full stack: +0.0062 and +0.0052 R/trade (t 0.49, 0.52), overlap 65.5 % and
   63.4 %. Live-expressible stack: net-negative in every arm and month. The delay lever reproduces at
   +0.0661 and +0.0657 against January's +0.0669.

5. **Is the stacked system positive?** **No, on the population that can be traded.** On the
   live-expressible at-market cohort — 43,755 candidates, three months, no selection — the best stack
   is **−0.1435 R/trade** ungated and **−0.0535 R/trade** cost-gated, at t = −44.88 and −14.91, with
   **zero net-positive days out of 63**. It is marginally positive (+0.0062, +0.0052, t ≈ 0.5) on
   February and March **only** on the deep-resting cohort, where the pool's fill rate is 100.00 %
   against a 17.6–18.7 % symmetric control.

---

## 11. What this lane says the mechanism is

The six wave-1 levers are not six defects. They are **two quantities measured six ways**:

- **where the entry sits relative to the market at the decision instant** (`mkt_r`) — this is
  A1, A2, A3 and C2, and it also drives `execution_fill_probability`, `fill_realism_class`, and
  `limit_marketable_at_decision`;
- **how tight the stop is** (`risk_distance`) — this is C1, because `cost_r = spread_price /
  risk_distance` and l5-F3 measured that identity at Spearman ≥ 0.9966.

Fixing them in sequence recovers 0.42 R/opportunity of *accounting* and lands the book on zero,
because the deficit those levers removed was never edge — it was **the pool describing orders that
could not have been placed** (a limit already past its own stop, a limit already through the market,
a fill credited before the entry was traded).

What remains after all of it, on the only cohort a live book can express, is one real and one fatal
number:

- **real:** the generator enters at the extreme of its own trigger bar and gives up **0.65–1.13 bps**
  within sixty seconds, in three independent months, and waiting one to five minutes recovers it —
  **+0.0669 / +0.0661 / +0.0657 R/trade**, the most reproducible quantity in the entire wave. Combined
  with a 0.25 R trailing exit it is **+0.0383 R/trade at t = 12.35 over 43,755 trades**, and the two
  are **95 % additive**.
- **fatal:** the broker-true round trip on those same trades is **2.457 bps** and the signal is worth
  **0.231 bps**. The system earns **9.4 %** of its own toll, and the ratio never exceeds **0.31** in
  any decile of stop width or cost, in any of the three months.

**The edge is real, it is measurable, it reproduces out of month, and it is an order of magnitude too
small for the instruments this book trades.** The next question is not another lever on this pool —
it is whether the same mechanism, at the same +0.23 bps, exists on a horizon or an instrument where
the toll is 0.2 bps instead of 2.5.

---

## 11b. Independent corroboration — a prior partial e-lane run on this disk

The discovery directory already carried `E_FINAL_V1.json`, `E_LIVEBOOK_V1.json`, `E_NESTING_V1.json`,
`E_STRUCTURE_V1.json`, `E_PRICESPACE_V1.json`, `E_DECOMP_V1.json`, `E_REALCOST_V1.json`,
`E_CONVENTION_V1.json`, `E_SIGNALTEST_V1.json`, `E_ADJUDICATE_V1.json`, `E_EXITADJ_V1/V2.json` and
scripts `e_01_decomp.py` … `e_08_exitadjudicate.py` from an earlier e-lane attempt that produced no
`_RESULT.md`. Those artifacts are **left untouched** and are worth reading, because a completely
separate implementation reproduces this lane's January numbers exactly:

| quantity | prior run (`E_LIVEBOOK_V1.json`) | this lane (§7.2, D0E0G0 / D0E0G1) |
|---|---:|---:|
| live at-market cohort n | 14,911 | 14,905 (6 rows dropped for a <5-bar path) |
| gross R/trade, market convention, k = 0 | −0.05965 | −0.0597 |
| broker-true cost R/trade | 0.212406 | 0.2122 |
| net R/trade | −0.272055 | −0.2718 |
| true-cost-gated n / gross / cost / net | 7,317 / −0.056356 / 0.068703 / −0.125058 | 7,317 / −0.0564 / 0.0687 / −0.1251 |
| delay repair, 1 minute, paired | +0.055779 (se 0.00652, 39.39 % of rows change) | +0.0558 |

Two of its results are **not** reproduced elsewhere in this receipt and should be carried forward:

1. **`E_FINAL_V1.json` — the naive sum of thirteen published wave-1 lane headlines is
   +1.91271 R/trade**, and it names the reason it is not additive: *"8 of the 13 are the SAME
   46.088 % of rows seen from different angles, 2 are accounting corrections that move zero
   dollars, and 2 reverse sign on the placeable cohort."* Its mechanism-location table shows five
   mechanisms with `n_on_live_cohort = 0`: w0-capture's 3,516 past-stop rows, the 9,214
   entry-the-market-has-left rows, and both fill-floor cohorts (6,729 at 0.80 and 3,407 at 0.45).
2. **`E_NESTING_V1.json` — the fill-probability inversion is identically zero on the live cohort.**
   `execution_fill_probability` has 7,399 distinct values over the pool but exactly **two** on the
   at-market cohort (0.92 on 14,708 rows = 98.64 %, 0.95 on 107). Every configured floor —
   0.45, 0.70, 0.80 — **refuses 0 of 14,815 at-market rows.** So l9-F1's +0.1067 and l12's +0.2275,
   the largest selection claims in wave 1, are defined entirely on orders the live engine cannot
   place. Over the pool the inversions reproduce (floor 0.45: kept −0.264803 vs refused −0.036850,
   inversion 0.227953; floor 0.70: 0.215385).

That is the same conclusion this lane reached by a different route, on one month instead of three,
and it is the reason both runs converge on the at-market cohort as the only place the question can
be honestly asked.

## 12. Artifacts

Scripts (all under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):

| script | what it does |
|---|---|
| `e_lib.py` | the exit menu (15 contracts), the honest walk with the l11 trail fix, l10's broker-true cost ported verbatim |
| `e_build_jan.py` | January base from the sealed w0 working set + R paths + w0-capture anchor |
| `e_build_month.py` | any month's base rebuilt from raw true-UTC M1 bars (validated against the sidecar) |
| `e_build_atmkt.py` | the at-market cohort with delayed entry at the close of bar k, R frame rebased |
| `e_extract_march.py` | March pool from the never-decoded `FA2_M_R0` MISSED_OPPORTUNITY ledger |
| `e_score.py` | the six levers, the 64-arm enumeration, the day-block bootstrap |
| `e_run_stack.py` | 64 arms × 3 months, marginals, ablation, interaction, decline-set overlap |

Data (same directory):

`e_JAN_BASE_V1.jsonl.gz` (27,658 × ~70) · `e_FEB_BASE_V1.jsonl.gz` (24,239) ·
`e_MAR_BASE_V1.jsonl.gz` (26,500) · `e_JANREBUILD_BASE_V1.jsonl.gz` (validation) ·
`e_MARCH_POOL_V1.jsonl.gz` (26,500) · `e_JAN_ATMKT_V1.jsonl.gz` (14,905) ·
`e_FEB_ATMKT_V1.jsonl.gz` (13,966) · `e_MAR_ATMKT_V1.jsonl.gz` (14,884)

Receipts: `e-stack_RESULT.json` (everything, 0.24 MB) · `E_STACK_MAIN_V1.json` ·
`E_CONTRACT_SELECT_V1.json` · `E_FILLCOND_V1.json` · `E_COSTCAP_SWEEP_JAN_V1.json` ·
`E_COHORT_SEARCH_JAN_V1.json` · `E_ATMKT_GRID_V1.json` · `E_ATMKT_COSTBAND_V1.json` ·
`E_ATMKT_RDPDECILE_V1.json` · `E_ATMKT_PERSYMBOL_V1.json` · `E_ATMKT_POOLED_V1.json` ·
`E_XAU_AND_ATMKT_ABLATION_V1.json` · `E_ATMKT_BOOTSTRAP_V1.json` · `E_ENTRY_DRIFT_V1.json` · `E_EQUITY_V1.json` ·
`E_FULLSTACK_SIG_V1.json` · `E_MONTH_SUBSTRATE_V1.json` · `e_VALIDATE_JAN_REBUILD_V1.json`

Source citations used above: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:60309-60310`
(the fill-conditioning gate), `:378` / `:63902` (the 120-minute wall),
`src/components/broker_net_cost_engine.py:859-866` and `:923-927` (the two cost limbs),
`src/components/poi_execution_lifecycle.py:164-194` (`execution_fill_probability`),
`src/mt5/mt5_interface.py:63` (`TRADE_ACTION_PENDING`, defined and unused for entry),
`src/components/broader_origin_generators.py:745-752, :862-897, :1023-1032` (`entry = bar.close`).
