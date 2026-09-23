# LANE 4 — the throttles, the breadth ceiling, and how to get out of the low-breadth trap

**Owner question this lane serves:** *"The book trades four days a month. A previous lane called that a
blocker and stopped. Breadth is a design variable — map every throttle, price it, and give me a ladder
I can climb."*

Date 2026-08-12. Lane 4 of the owner-commissioned swarm 2. **Measurement only** — no live path, no
config byte, no broker call, no VPS contact, no `src/` edit, no git write. Receipts under
`lane4_receipts/`; every script that produced a number under `lane4_receipts/scripts/`. Seed 20260812
throughout.

---

## 0. THE FOUR NUMBERS THE OWNER ASKED FOR

> **1. A six-week answer needs an annualised information ratio of 7.92. The armed book's is 1.90.**
> That gap is **17.4× the effective breadth at today's edge quality**, or **4.2× the edge quality at
> today's breadth** — Grinold both ways. In units you can act on: **67 book-day-equivalents per month
> against today's 3.83.**
>
> **2. Rearranging the existing estate cannot supply it, and I can prove that rather than assert it.**
> Every composition I measured lands on the same iso-detectability curve — armed 3 at **26.2 months**,
> a 9-sleeve out-of-selection basket with 17× the trades at **16.0 months**, the whole 29-sleeve estate
> at **211 months** (it is negative). Adding bets divides the edge almost exactly as fast as it
> multiplies the count: regressing log(edge per trade) on log(trades per month) across 28 sleeves gives
> a slope of **−0.425 ± 0.148 (p = 0.008)**, and R/month is statistically flat in trade count
> (Spearman −0.067, p = 0.74).
>
> **3. There is exactly one measured channel where breadth converts to speed, and it converts by 335×.**
> A **paired treatment** — the same trade scored two ways — has a difference-SD of **0.3437 R** against
> the estate's unpaired **1.4566 R**, a **4.25× noise reduction**. At the estate's 542.6 shadow
> trades/month, a **0.05 R treatment effect resolves in 3.0 weeks**. The identical question asked of the
> armed three sleeves takes **994 weeks**.
>
> **4. Breadth in this system is a step function of one number: cost per trade.** At a residual cost of
> **0.038 R**, 17 sleeves clear break-even at **220 trades/month**. At **0.05 R**, 14 clear at **87**.
> **Twelve thousandths of an R changes the estate's breadth by 2.5×.** The book trades four days a month
> because ~0.11 R of round-trip cost is a hurdle only rare, large-move setups clear — the low breadth is
> not conservatism, it is the *solution* the estate found to its cost constraint.

**The ladder's first rung, stated so it can be executed this week:** run the **full 29-sleeve estate as
a read-only shadow book** on the already-deployed dual-lane runner, and evaluate every open treatment
question (cost band, entry hour, exit frontier, spread floor, cluster cap) as a **paired difference**
rather than as a book. It costs zero risk, breaches no prop rule, touches no armed sleeve, and it moves
the estate's measurement clock from **years to weeks** — 3.0 weeks for a 0.05 R effect, 0.74 weeks for a
0.10 R effect. §7 prices it; §6 ranks it against six alternatives.

---

## 1. WHAT WAS MEASURED, ON WHAT, AND THE ONE INSTRUMENT CAVEAT THAT GOVERNS EVERY SLEEVE NUMBER

Two populations, because the system has two decision surfaces and they behave oppositely.

| population | what it is | rows | span | used for |
|---|---|---:|---|---|
| **funnel surface** | `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` via lane I's `/tmp/lane_i/pop.parquet` | 632,934 occurrences, **382,181 eligible**, **84,721 filled**, 9,577 decision windows, 100 trading days, 24 symbols, 10 families | Feb/Apr/May/Jun/Jul 2026 | §3 throttle A/B, §4 breadth ceiling |
| **sleeve surface** | `phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz` | **22,354** quote-corrected walked trades, 29 sleeves, 37 symbols, M15+H4+D1 | 2000-05-26 → 2026-07-26 (313.96 months); forward 2025+ = 10,180 trades / 18.76 months | §4–§7 |

Protocol work reuses lane I's `protocol.py`, which was **proved byte-equivalent** to the frozen
`w21_score_feb_market_top_r2.py::select` on all 5 months × 3 policies
(`lane_i_receipts/PART1_PROTOCOL_EQUIVALENCE.json`, `all_identical: true`). Nothing in this lane gets a
different protocol from anything else.

> **THE CAVEAT THAT GOVERNS EVERY SLEEVE FIGURE BELOW, STATED FIRST BECAUSE IT KILLED MY FIRST
> CONCLUSION.** `r_new_mid` is the r1 quote-side-corrected walker at the **mid spread band**. It charges
> **spread only** — no commission, no slippage, no swap. Every per-trade sleeve number in this document
> is therefore **gross of commission and swap**. I write it as `mean_r_spread_only` everywhere and
> apply an explicit residual-cost haircut `c` when an economic claim is made. The funnel population's
> own median components (`G_PAIRED_AND_COSTLINE_V1.json`) put the residual after spread at **0.020 R**
> for an intraday trade (`expected_slippage_r` 0.020, `commission_r` 0.000 at the median,
> `swap_cost_r` 0.000 at the median), against a total median `cost_r` of **0.1124 R** of which
> **0.0670 R is spread**. Overnight carry is *not* in that 0.020: `SURVIVOR_BOOK_V1.json` records
> `swap_r_per_night` from **0.0137** (`idxrev`) to **0.1304** (`fx_jpy_ny` on FTMO, **0.3735** on
> redacted_account), against mean holds of 0.5 to 13.4 nights. **A flat `c` therefore understates the cost of
> any multi-night sleeve, and I flag the two places it matters.**

---

## 2. (A) THE THROTTLE CENSUS

The brief asked for one census. There are **two**, on two surfaces, and conflating them is the error
that produced the "low-breadth blocker" reading. **Nine throttles bound the live sleeve book; six bound
the candidate funnel; they do not interact.**

### 2.1 The live book — `run_book.py` → `BookLauncher` → `BookOwner`

| # | throttle | `file:line` | what it removes | cost in book-days/month | stated reason |
|---|---|---|---|---:|---|
| **L1** | `--tags` sleeve restriction | `run_book.py:100`, `:383`; `sleeves/registry.py:142-144` | 31 of 34 registered specs; **115 of 137 (spec × symbol) slots** | **the whole throttle**: 4.64 → measured against 232.5 trades/month for all 29 | the arming mechanism itself; there is no `confidence_floor` key anywhere and none could express the armed set (B324) |
| **L2** | include-flag registry filter (`include_clean3`, `include_candidate_book`, `include_market_expansion_book`) | `book_engine.py:283-295`, `:518` (DF-1) | drops any spec outside `_active_sleeve_names()` **before generation**, so a dropped sleeve cannot even inflate the Kelly conviction count | 0 today — all three flags are `true` on the host | one source of truth across generation / sizing / conviction count |
| **L3** | one-unit-per-`(sleeve, symbol, decision_bar)` — idempotency | `book_owner.py:2045-2048` | re-placement on the same bar across 60 s ticks | 0 (pure idempotency) | the launcher ticks repeatedly; without it every tick double-places |
| **L4** | one-unit-per-`(sleeve, symbol, day)` | `book_owner.py:2056-2059` | a later-bar same-day re-fire of the same sleeve | **subsumed by L5 for a 3-sleeve book — measured identical, 87 trades either way** | "the 4 % gross cap only bounds CONCURRENT, not sequential, risk" |
| **L5** | one-unit-per-`(cluster, day)` cap | `book_owner.py:2062-2070`; flag read at `:269-274`; ledger at `placement_ledger.py:173-184`; config `agent_config.yaml:1391` (mainline **`false`**, **host set `true` 2026-08-11 10:39:42Z**) | later-bar same-cluster re-fires | **−37 % of trades, −47 % of R/month** (138 → 87 trades, +8.93 → +4.76 R/month, forward) | the certified risk envelope for the 2.0 % dial; `p_fail_daily` → **exactly 0.0000** in every cell |
| **L6** | decision-timeframe set (`[16388]` = H4-only) | `launcher.py:106-109` | nothing independently | **0 — this is not a throttle** | **derived**: `self._tf_tags` is built *from* `self._active_specs(tags)`. All three armed sleeves are H4, so the book runs H4. Arm an M15 sleeve and the set becomes `[15, 16388]` with no config change. **Correcting the brief: there is no timeframe restriction to relax.** |
| **L7** | gross open-risk cap 4 % | `admission.py:811`, enforced `:1335-1337` | **any unit beyond `0.04 / dial`** | at the 2.0 % dial: **max 2 concurrent units**. At 1.0 %: 4. At 0.5 %: 8 | ">4× headroom" over the worst measured book-day |
| **L8** | soft daily stop −3 % / max-DD entry buffer / de-risk band | `admission.py:804`, `:1320-1321`, `:1331-1333`, `:1340-1345` | new entries below −3 % intraday or inside the DD buffer; multiplicative shrink from `derisk_start_dd 0.07` | 0 today (both accounts flat, in profit) | the −5 % hard daily and −10 % static wall are prop-fatal |
| **L9** | Kelly-lite conviction bins | `admission.py:928` `((1,1,0.748),(2,3,0.991),(4,99,1.241))` | nothing — it is a **sizing** dial, not a count dial | 0 on breadth; **+2.1 % to +4.1 % on time-to-answer** (§8) | half-Kelly, breach-free conservative form |

**Measured today (forward 2025+, `C_SLEEVE_SURFACE_V1.json`):** armed 3 with L4+L5 on = **4.637
trades/month on 3.731 book-days/month**, which reproduces `THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` §3.2's
**3.833 book-days/month** on an entirely different population and instrument. Two independent routes to
the same frequency is why I treat it as settled.

**The one structural surprise: L4 is currently a no-op.** With three sleeves in three distinct clusters,
one-unit-per-cluster-per-day *is* one-unit-per-sleeve-per-day. Turning L4 off alone changes the trade
count by **zero** (87 → 87). Turning L5 off alone moves it **4.637 → 4.904 trades/month (+5.8 %)**.
Turning both off moves it to **7.356 (+59 %)**. This is the same fact
`THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` §4.4 reached from the accounting side ("for a three-sleeve book
cluster == sleeve"), arrived at here from the trade ledger.

### 2.2 The candidate funnel — the frozen MARKET-top-choice protocol

| # | throttle | `file:line` | what it removes | measured cost | stated reason |
|---|---|---|---|---|---|
| **F1** | `predecision_geometry_valid` | `candidate_funnel_analysis.py:225`, `:263` | rows with `submission ≥ expiry` or `risk ≤ 0` | 5,619 rows over 5 months, of which **0 are filled** — it costs literally nothing | a decision that cannot be taken |
| **F2** | `cost_r ≤ 0.20` eligibility gate | `candidate_funnel_analysis.py:52`, `:263` | **245,134 rows (49,027/month), 62,024 of them filled** | **the removed rows average −0.4224 R/fill against −0.0928 kept** | admission on modelled cost |
| **F3** | same-symbol occupancy | `w21_score_feb_market_top_r2.py:243-246` | any candidate on a symbol with a live position | 47.40 → 49.80 trades/month if removed | one position per symbol |
| **F4** | one trade per decision window | `:250` (`max(available)`, then `continue`) | every candidate but the argmax | 47.40 → 59.20 trades/month at k=5 | one decision per window |
| **F5** | `MIN_EXPECTED_NET_R = 0.10` floor | `:251-253`; constant at `candidate_funnel_analysis.py:53` | windows whose **top** pick scores below 0.10 | 47.40 → 114.20 trades/month if removed | do not trade a predicted loser |
| **F6** | MARKET-top-abstain | `:254-256` | windows whose top pick is a LIMIT order — **the whole window, not just that candidate** | 47.40 → 184.60 trades/month if removed | LIMIT fill is not modelled at M1 |

### 2.3 Every funnel throttle is doing real work, and relaxing any of them destroys value

`A_THROTTLE_CENSUS_FUNNEL_V1.json`. Ten arms, identical population, identical tie-breaks, five months.
Score is the cache's month-boundary ridge fit (`pred_month_boundary`) — the same `ridge_oos_frozen`
predictor lane I used; the committed validation ran a *daily* prequential refit, so levels differ from
the published +0.19 R/month and only the **A/B contrasts** are load-bearing here.

| arm | trades/month | net R/month | months positive |
|---|---:|---:|---:|
| **A0 frozen rule** | **47.4** | **−1.85** | 2/5 |
| A1 rerank to MARKET first | 54.4 | −4.41 | 2/5 |
| A2 no MARKET abstain (mixed) | 184.6 | −3.82 | 2/5 |
| A3 no 0.10 floor | 114.2 | −9.39 | 1/5 |
| A4 no floor, no abstain | 1,808.4 | −38.17 | 0/5 |
| A5 two per window | 54.8 | −2.87 | 2/5 |
| A6 five per window | 59.2 | −2.76 | 1/5 |
| A7 no symbol occupancy | 49.8 | −2.69 | 2/5 |
| A8 all off, k=5 | 9,050.0 | −98.13 | 0/5 |
| **A9 all throttles off** | **76,436.0** | **−1,571.83** | 0/5 |

**A9 reproduces lane I's independently computed pool net sum of −1,571.8 R/month exactly**
(`PART1_ORACLE_BAND.json`), which is the control that says the harness is right.

**Read the table plainly: on the funnel there is no low-breadth trap.** Every throttle removes
candidates whose expectancy is *worse* than what it keeps, monotonically, in every month. The funnel is
not throttled below its opportunity — it is throttled down to the least-bad corner of a surface whose
marginal candidate loses 0.42 R. **Do not relax a single funnel throttle.**

---

## 3. (B) THE BREADTH CEILING — RAW AND EFFECTIVE

`B_BREADTH_CEILING_V1.json`. Effective breadth is estimated from the **day-portfolio variance ratio**,
not assumed: for groups of `K` same-day bets, `Var(ΣR) / (K·σ²) = 1 + (K̄−1)·ρ̄` solves for the average
pairwise correlation `ρ̄`, and `N_eff = K̄ / (1 + (K̄−1)ρ̄)`. Bootstrap CI over groups, 400 resamples.

### 3.1 The funnel surface — enormous, and genuinely close to independent

| unit | raw per group | variance inflation | **ρ̄** (95 % CI) | **N_eff per group** |
|---|---:|---:|---:|---:|
| all filled eligible in one **trading day** | 847.21 | 4.163 | **0.00362** [0.00225, 0.00528] | **208.57** |
| one candidate per **symbol** per day | 23.98 | 1.736 | 0.03200 | **13.82** |
| all filled in one **decision window** | 10.09 | 1.732 | 0.05135 [0.04547, 0.05715] | 6.88 |
| same day + same **family** | 85.06 | 5.349 | 0.01890 [0.01394, 0.02360] | 32.86 |

Cross-sectional correlation of the 24 symbols on day-mean net R: **mean +0.0186, median +0.0163**, p95
+0.207, only 6.2 % of the 276 pairs above 0.2. The whole correlation structure sits in two clusters:
**UKOIL/USOIL +0.658** and **BTCUSD/ETHUSD +0.440**; the JPY complex follows at +0.27 to +0.33.

> **An independent check that the `N_eff` estimator is sound.** The per-bet SD on the one-per-symbol-
> per-day book is **0.95971** and the equal-weight day-portfolio SD is **0.25798** — a ratio of
> **3.7201**. `√N_eff = √13.8177 = 3.7172`. The two agree to **0.08 %**, and they were computed by
> different routes (a variance-ratio solve versus a direct portfolio construction).

| funnel breadth | per month | per year |
|---|---:|---:|
| eligible candidates | 76,436 | 917,234 |
| filled eligible (an outcome you could have taken) | 16,944 | 203,331 |
| decision windows | **1,847** | 22,169 |
| **effective independent bets** (20 days × 208.57) | **4,171** | **50,057** |

### 3.2 The sleeve surface — small, and heavily correlated where it is armed

| unit | raw per day | variance inflation | **ρ̄** (95 % CI) | **N_eff per day** |
|---|---:|---:|---:|---:|
| all 29 sleeves, same day | 7.746 | 1.941 | 0.0535 [0.0440, 0.0637] | **5.69** |
| all 29, same (day, cluster) | 2.900 | 1.839 | 0.2030 [0.1721, 0.2324] | 2.09 |
| **armed 3, same day** | 1.631 | 2.016 | **0.6464** [0.2526, 0.9789] | **1.158** |

**This is the trap, quantified.** The armed three sleeves are **0.646-correlated within a day** — 18×
the funnel's 0.036 — so on the 45.7 % of book-days when two of them fire, they supply 1.16 independent
bets, not 2. The 29-sleeve estate is far better diversified (ρ̄ 0.053, N_eff 5.69/day) *because* it
spans clusters; sleeve-pair correlation on day-mean R has mean +0.0436 but a p95 of **+0.482**, with
`mx_us100 / mx_us500 +0.857`, `crypto / mx_btcusd +0.639`, `metals_core / metals_softband +0.573`.

### 3.3 The two surfaces side by side

| | armed live book | funnel surface | ratio |
|---|---:|---:|---:|
| raw decisions per month | 4.64 trades on 3.73 days | 1,847 windows | 397× |
| **effective independent bets per year** | **46** | **50,057** | **1,088×** |

**The funnel already has a thousand times the armed book's effective breadth.** It is not
breadth-starved and never has been. §5 shows what that buys it.

---

## 4. (C) THE DETECTABILITY LADDER — AND THE ISO-IR LAW

`D_LADDER_AND_SIZING_V1.json`, `J_ISO_IR_TABLE_V1.json`. Design: two-sided α = 0.05, power 80 %, so
`n = k·(σ/μ)²` with `k = (z₀.₉₇₅ + z₀.₈₀)² = 7.8489`. Correlation enters through the effective-bet
count, never by assumption.

### 4.1 The ladder for the armed book

Months to a powered answer, as a function of breadth multiple `B` and edge-dilution factor `k`
(`μ' = μ/k`), from `μ = 0.3298`, `σ = 1.1785` R per book-day, 3.833 book-days/month:

| breadth | bets/month | k = 1.0 | k = 1.25 | k = 1.5 | k = 2.0 | k = 3.0 |
|---|---:|---:|---:|---:|---:|---:|
| ×1 (today) | 3.83 | **26.15** | 40.86 | 58.83 | 104.6 | 235.3 |
| ×5 | 19.2 | 5.23 | 8.17 | 11.77 | 20.9 | 47.1 |
| ×10 | 38.3 | 2.62 | 4.09 | 5.88 | 10.5 | 23.5 |
| **×17.4** | **66.7** | **1.50 ← six weeks** | 2.35 | 3.38 | 6.01 | 13.5 |
| ×100 | 383.3 | 0.26 | 0.41 | 0.59 | 1.05 | 2.35 |
| ×1000 | 3,833 | 0.026 | 0.041 | 0.059 | 0.105 | 0.235 |

**Minimum detectable effect** at the same anchor (R per book-day, and as a multiple of the measured
+0.3298 edge):

| breadth | 6 weeks | 3 months | 6 months | 12 months |
|---|---|---|---|---|
| ×1 | 1.377 R (**4.18×** the edge) | 0.974 (2.95×) | 0.689 (2.09×) | 0.487 (1.48×) |
| ×10 | 0.435 (1.32×) | 0.308 (0.93×) | 0.218 (0.66×) | 0.154 (0.47×) |
| ×17.4 | **0.330 (1.00×)** | 0.233 (0.71×) | 0.165 (0.50×) | 0.117 (0.35×) |
| ×100 | 0.138 (0.42×) | 0.097 (0.30×) | 0.069 (0.21×) | 0.049 (0.15×) |

**Answering the owner's question exactly: 17.4× today's breadth — 67 book-day-equivalents per month,
about 3.1 bets every calendar day — turns a 26-month question into a 6-week one, and only if the added
bets carry the same edge.** At 1.5× dilution the requirement is **39×**; at 2× dilution, **70×**.

### 4.2 The iso-IR law — why rearranging the estate cannot get there

`J_ISO_IR_TABLE_V1.json`. Same statistic, every configuration I could build:

| configuration | IC per bet (μ/σ) | effective bets/yr | **IR annualised** | **months to answer** | ×breadth for 6 wks |
|---|---:|---:|---:|---:|---:|
| armed 3, FTMO, per book-day | +0.2798 | 46.0 | **1.898** | **26.15** | 17.4 |
| armed 3, redacted_account | +0.3998 | 35.3 | 2.374 | 16.72 | 11.1 |
| armed 3, r1 archive, per trade | +0.4656 | 55.6 | 3.473 | 7.81 | 5.2 |
| **9-sleeve out-of-selection basket, per trade** | **+0.0863** | **790.0** | **2.426** | **16.00** | 10.7 |
| same basket, one unit of risk per **day** | +0.0604 | 271.8 | 0.995 | 95.10 | 63.4 |
| all 29 sleeves, day level | −0.0636 | 110.3 | −0.668 | 211.24 | 140.8 |
| funnel, **measured** within-window edge | +0.0026 | 22,169 | 0.390 | **620.45** | 413.6 |
| funnel, **if** it had the break-even edge | +0.0790 | 22,169 | **11.767** | **0.68** | 0.45 |

**Read the fourth row against the first.** The out-of-selection basket has **17.2× the bets** and lands
at **16.0 months against 26.2** — a 1.28× improvement, not 17×, because its IC per bet is **5.4× lower**
(+0.0863 vs +0.4656). √17.2 = 4.15 and 4.66/0.086 = 5.4: the count went up as √breadth predicts and the
edge came down slightly faster. That is Grinold's law running in reverse across the estate's own
inventory.

Three independent confirmations of the same law, so it is not one regression:

1. **Cross-sleeve regression** (`F_LAW_AND_LADDER_V1.json`, 28 sleeves with n ≥ 20, forward window):
   log(|mean R per trade|) on log(trades per month) has slope **−0.4254 ± 0.1482, r = −0.491,
   p = 0.0080**. Spearman of trades/month against **R/month** is **−0.067, p = 0.74** — flat.
2. **The iso-IR table above** — six configurations spanning 46 to 790 effective bets/year all land in a
   1.0–3.5 IR band.
3. **The cost line** (§4.3) — the mechanism that generates the law.

### 4.3 The mechanism: breadth is a step function of cost per trade

`G_PAIRED_AND_COSTLINE_V1.json`. Sleeves clearing break-even at a residual cost `c` (charged on top of
the spread the walker already deducted), forward window:

| residual cost `c` | sleeves clearing | trades/month | net R/month after `c` |
|---|---:|---:|---:|
| 0.000 R | 17 | 220.2 | +29.59 |
| 0.020 R | 17 | 220.2 | +25.19 |
| **0.038 R** | **17** | **220.2** | **+21.22** |
| **0.050 R** | **14** | **86.9** | **+19.47** |
| 0.075 R | 13 | 75.0 | +17.56 |
| 0.150 R | 11 | 30.0 | +14.09 |
| 0.500 R | 5 | 13.4 | +6.62 |
| 1.000 R | 2 | 4.2 | +2.95 |

**Between 0.038 R and 0.050 R the estate's tradeable frequency falls 2.5× (220 → 87 trades/month).**
Twelve thousandths of an R. That single step is the whole explanation of "why four trades a month": the
armed three sleeves are the ones whose per-trade edge (0.563, 1.455, 1.927 R spread-only) clears the
cost line by an order of magnitude, and they are rare *because* large-edge setups are rare. Nobody
chose four days a month. **The cost line chose it.**

This is the sleeve-level restatement of lane I §7.1's finding — "entered blind, this market is a fair
game gross and the entire deficit is cost" — and it is why lane I's F4 (cost drag falls as 1/√t) is the
single most valuable structural fact either lane found.

---

## 5. (D) THE LADDER — EACH RUNG PRICED, ORDERED, PROP-FLAGGED

Prop arithmetic uses each firm's **measured** rules (`SESSION_Q_MC_TRUE_TARGET_RESULT.md`): FTMO static
**$90,000** floor, redacted_account **trailing**, both **5 % daily on the initial balance**, both **5 %
phase-2 target**. Worst-case daily loss = `max_concurrent_units × dial`, bounded by the 4 % gross cap at
`admission.py:811`.

| rung | change | breadth after | expectancy evidence | realised risk | prop rules | `p_pass` | verdict |
|---|---|---:|---|---|---|---|---|
| **0** | *(today)* 3 sleeves, cluster cap ON, 2.0 % dial | 3.83 book-days/mo | +0.3298 R/book-day, t 2.325, n 69 | worst book-day −0.910 R | 2 units × 2.0 % = **4.0 %**, inside 5 % (1.25× headroom) | 0.8522 joint [0.2803, 0.9927] | — |
| **1** | **Full-estate READ-ONLY shadow book (29 sleeves), paired-treatment evaluation** | **542.6 trades/mo of measurement**, 29.6 days/mo | n/a — measurement only | **zero** | **none touched** | unchanged | **DO THIS FIRST** — §7 |
| **2** | Cluster cap OFF (L5) | 4.90 trades/mo (**+5.8 %**) | mean 1.027 → 1.014 R (−1.2 %); **+0.22 R/mo** | `p_fail_daily` **0.0000 → 0.0264** all-years, **0.0541** forward | still inside | **−0.0895 to −0.1036** | **REJECT.** Buys 5.8 % of breadth, sells 9–10 pp of `p_pass`, and re-opens an account-death mode |
| **3** | Both caps OFF (L4+L5) | 7.36 trades/mo (**+59 %**) | mean 1.027 → **1.214** (+18 %); **+4.17 R/mo** | same failure mode, larger | inside the 4 % cap only because concurrency ≤ 2 | same −9 to −10 pp | **OWNER'S CALL, NOT A RECOMMENDATION.** The only rung that raises breadth *and* edge. It is a straight `p_pass`-for-rate trade at 2× the size the restatement priced |
| **4** | **Incubation cohort: 9 out-of-selection sleeves at registry confidence 0.025** | **+65.8 trades/mo on +22.7 days/mo — 17.2× the trade count, 6.1× the days** | mean **+0.178 R** spread-only, **t 4.22**, out-of-selection (§5.1) | 9 × (0.025 × 2.0 %) = **0.45 %** worst-case day if all fire | **0.45 % + 4.0 % = 4.45 %, inside the 5 % daily; inside the 4 % gross cap** | ≈ unchanged (risk is 1/44th of a unit) | **RECOMMENDED SECOND.** Precedent exists: `mx_btcusd` was armed at exactly 0.025 on 2026-07-31 |
| **5** | Dial 2.0 % → 1.0 %, concurrency cap 2 → 4 | up to 7.67 units/mo | R/month doubles, %/month **unchanged** (R × dial) | worst day still 4.0 % | unchanged | **improves** — halved per-event loss | **VIABLE, but it is a dial change = OD-4, Borhen's alone.** Time-to-answer improves 2× at identical expected return |
| **6** | Arm all 29 sleeves at full size | 232.5 trades/mo | **mean −0.011 R, t −0.50, −2.55 R/month** | 18.3 trades/day mean, **max 42** | **BREACH.** 42 units × 2.0 % = 84 %; the 4 % gross cap would reject 40 of 42, silently | catastrophic | **NON-STARTER** |
| **7** | Relax any funnel throttle (F1–F6) | up to 76,436/mo | **−1,571.8 R/month** (§2.3) | n/a | n/a | n/a | **NON-STARTER** |

**Rung 6's failure mode deserves a line of its own, because it is the one that would look healthy in the
logs.** The gross cap does not *warn*; `admission.py:1335-1337` returns
`GovernorDecision(False, 0.0, ..., "gross_risk_cap_exhausted")` and the intent is skipped. On the 86 %
of forward days with ≥ 5 same-day trades, a 29-sleeve book at 2.0 % would place two and silently discard
the rest, so the realised book would be an **arbitrary function of intra-day arrival order**, not of any
selection rule. That is worse than not arming them.

### 5.1 The adversarial control on rung 4, because it is my only positive

The rung-4 cohort is selected on **pre-2025 data (295.2 months)** and scored on **2025+ (18.76 months)**,
and the three currently-armed sleeves are **excluded** so nothing in it was chosen on the scoring window
(`H_OUT_OF_SELECTION_CONTROL_V1.json`, `I_ARMED_EXCLUDED_CONTROL_V1.json`):

| selection bar | sleeves | fwd trades | trades/mo | days/mo | mean R (spread-only) | **t** | net R/mo after `c` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `c` = 0.038 R, armed excluded | 12 | 1,825 | 97.3 | 28.5 | +0.1328 | **3.826** | +9.23 |
| `c` = 0.050 R, armed excluded | 9 | 1,235 | 65.8 | 22.7 | +0.1779 | **4.220** | +8.42 |

Sleeve-level sign persistence across the split: **78.6 % of 28 sleeves agree in sign**, Spearman
**+0.681 (p = 0.0001)**, Pearson **+0.582 (p = 0.0012)**. **Sleeve-level mean R is persistent out of
selection** — which is a genuinely different result from lane I's row-level null, and the two are
consistent: lane I measured that you cannot predict *which trade* pays; this measures that you can
predict *which rule* pays.

**Four things that must be said against my own rung 4, in descending severity.**

1. **The instrument charges spread only.** `c` is a flat haircut and it is **wrong for multi-night
   sleeves**. `SURVIVOR_BOOK_V1.json` prices `idxrev` at `gross_r +0.00585`, `true_cost_ex_swap
   0.02205`, mean **10.04 nights** at `swap 0.0137/night` — net **−0.0162 at zero carry, −0.1549 at its
   own mean hold**, tier **DEAD_BEFORE_COST**. My archive reads `idxrev` at **+0.0455 R forward** and it
   is in the `c` = 0.038 cohort. `fx_jpy_ny` is worse: `swap_r_per_night` **0.1304 FTMO / 0.3735
   redacted_account**. **Any rung-4 execution must re-price the cohort at each sleeve's own carry before
   arming, and I expect that to remove at least the two named here.**
2. **The day-portfolio t is much weaker than the per-trade t** — **1.351** at `c` = 0.038 and **2.284**
   at `c` = 0.050, with an implied `N_eff` of only **2.2–2.4 bets/day**. The per-trade t of 3.83–4.22
   assumes you deploy a full risk unit on *every one* of 97 trades/month, which is 21× today's deployed
   risk. At **fixed daily risk** the cohort is worth **+2.49 R/month** (0.10985 × 22.65) against the
   armed book's +1.264 — about **2×**, not 21×.
3. **Multiplicity.** 28 sleeve-level looks. t = 4.22 survives BH at α = 0.10 comfortably (p ≈ 2.4e-5),
   but the cohort was *also* filtered by a threshold I chose (`c`), and the estate's ratified rule
   (`CANDIDATE_BOOK_V1`, all-declared, α = 0.10) would want that declared before the look.
4. **`asian_fade` carries a known unresolved defect.** It is the cohort's largest contributor by trade
   count (42.9/month) and `phase12/SESSION_AU_CONTRACT_WIRING_RESULT.md` §2 measures it losing
   **0.3365 R/day** at B613's honest trail bound. Its 0.1009 R spread-only mean is above the 0.038 line
   and below the 0.1124 total-cost line — **it is exactly the marginal case the cost step decides**, and
   it should be priced individually rather than carried by the cohort.

---

## 6. (E) POSITION SIZING AS A BREADTH SUBSTITUTE — REFUSED, WITH THE MECHANISM

The brief asked whether many small vol-targeted bets beat few large ones at the same risk budget. **On
this population, no — and the reason is structural, not empirical, which makes it worth stating rather
than just reporting.**

Three tests, all on the funnel's one-per-symbol-per-day book (2,398 bets over 100 days,
`D_LADDER_AND_SIZING_V1.json`, `E_EXPANSION_AND_SIZING_V1.json`):

| weighting scheme at fixed daily risk | day-portfolio mean | SD | t | **breadth-equivalent vs equal weight** |
|---|---:|---:|---:|---:|
| equal weight | −0.11929 | 0.25798 | −4.624 | 1.000 |
| inverse predicted dispersion (ATR-quintile SD) | −0.11902 | 0.25808 | −4.612 | **0.995** |
| inverse `atr14/atr50` | −0.11563 | 0.26690 | −4.332 | **0.878** |
| **stop re-pegged from ATR14 to ATR50** | −0.09497 | 0.20797 | −4.567 | **0.975** |

**Not one scheme adds a single effective bet.** The mechanism is visible in the last row: re-pegging the
stop cuts the per-bet SD from **0.9597 to 0.7948 (−17.2 %)** and cuts the per-bet mean from **−0.1192
to −0.0950 (−20.3 %)** — **both by the same factor**. In R space, changing the stop scale is a change of
numeraire: it rescales μ and σ together and cannot move μ/σ. **Stop-scaling and position-scaling are
leverage decisions, not information decisions.**

This also resolves an apparent tension with lane I's F2. Lane I measured a **1.42× monotone
ATR14/ATR50 effect on forward travel in ATR units** and called it a geometry defect. It is one — but the
estate's own risk unit is *already* ATR14-pegged (`stop_distance_atr` median 0.986), so the defect is
**already absorbed into the R normalisation** and cannot be harvested a second time by sizing. Confirmed
directly: dispersion across ATR quintiles is nearly flat in R (per-quintile SD **1.098 → 1.164**, a 6 %
range) while a regression of |net R| on four pre-decision features reaches **R² = 0.175**. The features
predict dispersion; R-normalisation has already spent it.

**What *does* work, and it is the same arithmetic seen from the other side:** splitting one unit of daily
risk across `N_eff` genuinely independent bets divides the day's SD by `√N_eff`. Measured at
**3.7201×** on the funnel, against `√13.8177 = 3.7172` predicted — a 0.08 % match. That is a real,
free, prop-neutral variance reduction and it is exactly what the armed book does **not** have: its
`N_eff` is **1.158**, so it captures 1.08× of a possible 3.72×.

**Live sizing variance is a small tax, not a lever.** The half-Kelly bins
(`admission.py:928`: 0.748 / 0.991 / 1.241) give `CV_size` **0.144–0.203** depending on the firing
distribution, hence a variance inflation of **1.021–1.041** — time-to-answer is **2.1 % to 4.1 % longer**
because of conviction-count sizing. redacted_account's live `size_cap_multiplier` 0.622928 and the governor's
de-risk band scale μ and σ **together** and therefore change the **money** and **not the clock** at all.

---

## 7. (F) THE CONSTRUCTIVE CONCLUSION — THE ONE EXPANSION WORTH DOING

### 7.1 The single highest-value breadth expansion

> **Run the full 29-sleeve estate as a read-only shadow book, and convert every open question in the
> estate from a book question into a PAIRED-TREATMENT question.**

`G_PAIRED_AND_COSTLINE_V1.json`. A paired treatment scores the *same* trade two ways and tests the
difference, so all the common variance cancels. Measured on the estate's own artifact, which already
contains two such pairs:

| instrument | n | SD of the difference | **SD ratio vs unpaired** | t |
|---|---:|---:|---:|---:|
| unpaired reference, 29 sleeves | 10,180 | **1.4566** | 1.000 | — |
| cost band low → high (a pure cost treatment) | 10,180 | **0.3437** | **0.2374** | −10.18 |
| quote-side correction `r_old → r_new_mid` | 10,180 | 0.7763 | 0.5330 | −23.39 |
| **same cost treatment, armed 3 only** | **138** | 0.7318 | 0.3336 | −1.75 |

**Time to a powered answer on a treatment effect, at the estate's 542.6 shadow trades/month against the
armed book's 7.4:**

| treatment effect size | **full estate (29 sleeves)** | **armed 3 only** | speed-up |
|---|---:|---:|---:|
| 0.10 R | **0.74 weeks** | 248 weeks | **335×** |
| 0.05 R | **3.0 weeks** | 994 weeks | **335×** |
| 0.02 R | 18.6 weeks | 6,211 weeks | 335× |
| 0.01 R | 74.3 weeks | 24,844 weeks | 335× |

**This is the only measured route from years to weeks in this entire lane, and it is free.** It buys
nothing in return — it buys the *clock*, which is precisely what the owner said he would not wait six
months for. Every one of these is a live open question today: `--frontier-exits` (rolled back 08-10
pending a corrected-quote price, Lane H §2), `--entry-hour` (ratified 2026-07-30, never implemented),
`--spread-geometry-floor` on more sleeves, the cluster cap's own price, `--vol-level-tilt`, and the
significance-gate question H-1 whose 25 sleeves all fail on one gate. Each of them is a **paired**
question — same trade, two contracts — and each of them currently waits on either a 16.5 h sealed
replay or a multi-year live record. At 542.6 shadow trades/month **the estate can answer any of them in
under a month.**

**Expected effect on time-to-answer:** 335× on any treatment question; **nil** on the question "does the
armed book have an edge", which no amount of breadth can accelerate because adding a different sleeve
adds evidence about a different sleeve.

**Expected effect on monthly return: zero, by construction.** It is read-only. That is the honest
trade and it is why it ranks first: rung 4 offers ~2× the R/month at fixed daily risk with four named
caveats, and rung 1 offers a 335× faster measurement with none.

**Risk cost:** the shadow runner already exists, is deployed, and performs **zero broker mutation by
construction** (`FORWARD_SHADOW_DEPLOYED_20260811.md`, `eed6c496b`, daily prequential refit
`1c9266850`). Extending its sleeve list touches no `--tags`, no token, no config digest, no armed book.

**The measurement that would prove it unsafe** — stated as the brief requires, because a read-only
change still has one failure mode: **shadow-to-live fidelity**. If the shadow's modelled fills diverge
from broker truth, every treatment answer it produces is an answer about a simulator. The test is
already specified and half-blocked: reconcile shadow-modelled slippage against **broker-true captured
slippage** per symbol; Lane H records that **6 of 16 symbols (AUDJPY, CHFJPY, EURJPY, UKOIL.cash,
USOIL.cash, XAGUSD) lack reconciled price-domain samples**, which is exactly why the inverted-breaker
candidate's ADMIT flipped to REJECT at q 0.3169. **If that reconciliation fails on the treatment-bearing
symbols, rung 1 is unsafe and must be run at incubation size on live instead** — which is rung 4, and
which is why the two rungs belong together in that order.

### 7.2 The honest summary of what breadth can and cannot do here

- **Breadth cannot make the funnel work.** At 1,088× the armed book's effective breadth and a
  measured within-window edge of +0.003 ± 0.005 R, the funnel needs **620 months**. At the +0.09 R it
  would need to break even it would answer in **3 weeks**. **The funnel's problem was never breadth and
  its breadth was never wasted** — it is the fastest measuring instrument the estate owns, pointed at a
  quantity that is not there.
- **Breadth cannot validate the armed book faster.** 17.4× is arithmetically required and no
  composition of the existing 29 sleeves supplies it without diluting the edge by more than it
  multiplies the count (measured slope −0.425, p = 0.008).
- **Breadth converts to speed through paired treatments, at 335×,** and that is a channel the estate
  has never systematically used.
- **Breadth converts to return only by moving the cost line.** 0.038 R → 0.050 R of residual cost is
  worth **2.5× the tradeable frequency**. Lane I's F4 (cost drag falls as 1/√t while conditional IR does
  not fall) is therefore not a footnote — **it is the only measured lever that moves both breadth and
  return at once**, and neither lane has priced a lengthened contract on the sleeve surface.

---

## 8. WHAT I GOT WRONG, AND THE LIMITS

- **My first draft's headline was wrong and its own control killed it.** I found `asian_fade`
  (+0.101 R, 42.9 trades/mo), `idxrev` (+0.046, 83.4/mo) and `fx_jpy_ny` (+0.040, 47.0/mo) in the
  archive and wrote them up as the breadth answer. Then I checked them against
  `SURVIVOR_BOOK_V1.json` and found `idxrev` at **`gross_r +0.00585` against `true_cost_ex_swap
  0.02205`, tier DEAD_BEFORE_COST**, with **10.04 nights** of mean carry at 0.0137 R/night. **Not one
  of the three clears the estate's own median total cost of 0.1124 R.** The instrument caveat in §1
  exists because of that error, and the finding it replaced (§4.3's cost step) is stronger than the one
  it killed.
- **I initially treated the decision-timeframe restriction `[16388]` as a throttle.** It is not.
  `launcher.py:106-109` derives `_tf_tags` from `_active_specs(tags)`, so H4-only is the *shadow* of the
  armed set. There is nothing there to relax and the brief's inclusion of it should be struck.
- **The funnel arms are scored with the cache's month-boundary ridge fit, not the daily prequential
  refit the committed validation used.** Levels therefore differ from the published +0.19 R/month; only
  the A/B contrasts in §2.3 are load-bearing, and A9's exact reproduction of lane I's independently
  computed −1,571.8 R/month is the control that says the harness is right.
- **The `N_eff` estimator assumes equicorrelation within a group.** Real correlation is clustered
  (UKOIL/USOIL 0.658, BTC/ETH 0.440 against a 0.019 mean), so a single ρ̄ understates diversification in
  the tails of the distribution and overstates it in the clusters. The direct portfolio check in §3.1
  (3.7201 measured vs 3.7172 predicted) says the aggregate is right even though the decomposition is a
  simplification.
- **`ρ̄ = 0.646` for the armed 3 rests on 206 group-days and its CI is [0.253, 0.979].** The point
  estimate is the least reliable number in §3.2. Its *direction* — far more correlated than the funnel —
  is not in doubt at either end of that interval.
- **Rung 4's flat residual haircut `c` is wrong per sleeve**, understating multi-night carry by up to
  0.37 R/night (`fx_jpy_ny` on redacted_account). §5.1 caveat 1 states which sleeves I expect it to remove.
  Repairing it needs the deep H4 archive (`data/mt5_research_exports/bridge_ftmo_deep_h4_*`), which is
  **absent from this machine** — the same blocker `THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` §8 records.
- **The forward window (18.76 months) is the window that selected the armed three.** §5.1 excludes them
  from the cohort for exactly that reason, but the *comparison baseline* (armed 3 at +4.76 R/month)
  remains in-sample and should be read as an upper bound on the incumbent.
- **The concurrency figures are same-day counts, an upper bound on true concurrency** — positions may
  close before the next fires. Rung 6's breach verdict is therefore conservative in the *safe*
  direction, and rung 5's headroom claim is conservative in the same direction.
- **No candidate was declared and no rule is proposed.** Every number here is a population property, a
  null, or an A/B on an existing artifact. §5.1's cohort is offered as pre-registration material for a
  future look, not as a look already taken.
- **Not measured and it would change rung 1's priority: shadow-to-live fill fidelity** on the six
  symbols Lane H names. That is the gate on the whole recommendation and §7.1 states it as such.

---

## 9. RECEIPTS

| file | what |
|---|---|
| `lane4_receipts/A_THROTTLE_CENSUS_FUNNEL_V1.json` | §2.2–2.3 — ten protocol arms × 5 months, cost-gate and geometry-gate A/B |
| `lane4_receipts/B_BREADTH_CEILING_V1.json` | §3.1 — raw/effective breadth, variance ratios, 400-resample ρ̄ CIs, 276 symbol pairs |
| `lane4_receipts/C_SLEEVE_SURFACE_V1.json` | §2.1, §3.2, §5 — 29-sleeve tables both windows, cap A/B ladder, sleeve-pair correlation |
| `lane4_receipts/D_LADDER_AND_SIZING_V1.json` | §4.1, §6 — anchors, ladder, MDE grids, three weighting schemes |
| `lane4_receipts/E_EXPANSION_AND_SIZING_V1.json` | §5–§6 — per-symbol armed surface, registry slot census, ATR re-peg, live sizing CV |
| `lane4_receipts/F_LAW_AND_LADDER_V1.json` | §4.2–4.3, §5 — breadth/edge regression, per-sleeve break-evens, concurrency, prop-rule rungs |
| `lane4_receipts/G_PAIRED_AND_COSTLINE_V1.json` | §4.3, §7.1 — paired-treatment channel, cost-line curve, funnel cost components |
| `lane4_receipts/H_OUT_OF_SELECTION_CONTROL_V1.json` | §5.1 — pre-2025 selection scored on 2025+, sign persistence |
| `lane4_receipts/I_ARMED_EXCLUDED_CONTROL_V1.json` | §5.1 — same, with the three armed sleeves removed |
| `lane4_receipts/J_ISO_IR_TABLE_V1.json` | §4.2 — the iso-IR table, eight configurations |
| `lane4_receipts/scripts/` | every producing script, including the two adversarial controls |

**Inputs bound, none mutated:** `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` and
lane I's derived `/tmp/lane_i/pop.parquet` (read-only);
`docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz`;
`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json`;
`src/components/ultimate_book/{admission,book_owner,book_engine,launcher,placement_ledger}.py` and
`sleeves/registry.py` (imported unchanged, for cluster and spec resolution only);
`swarm/LANE_I_EDGE_CEILING_AND_STRUCTURE_MAP_V1.md`, `swarm/THREE_SLEEVE_BOOK_RESTATEMENT_V1.md`,
`swarm/LANE_H_CONFIG_CONSERVATISM_AUDIT_V1.md`.

**No live path, no config byte, no R2-bound file, no VPS, no git write, no `src/` edit.**
