# LANE d2 — IS IT THE USAGE? Every downstream layer priced against its own oracle

**Wave 19 broad forensic.** Worktree `wave19-broad-forensic-20260801`, branch `phase19/broad-forensic`.
Scripts: `d2_layers.py`, `d2_pool.py`, `d2_entry.py`, `d2_rank.py`, `d2_rank2.py`, `d2_rankfeas.py`,
`d2_stack.py`, `d2_gate.py`, `d2_master.py`. Machine artifacts under `/tmp/d2/out/`:
`D2_RESULT.json` (master), `D2_POOLED_V1.json`, `D2_STACK_V1.json`, `D2_RANKFEAS_V1.json`,
`D2_RANK_V1.json`, `D2_RANK2_V1.json`, `D2_GATE_ROSTER_V1.json`, eight `D2_<month>_V1.json`
+ `_ROWS.npz`. Nothing is sampled.

---

## 0. HEADLINE

**The usage is not destroying a good signal — the usage is already at 84 % of everything it can
reach, and everything still reachable is +0.00553 R/trade priced jointly out of sample, against a
0.31553 R/trade toll and a +0.29226 R/trade gap to breakeven.**

The layer with the largest real-vs-oracle gap is **RANKING** (+2.267 R/trade of range at the
system's own 3-trades-per-day capacity). **87.2 % of that gap is unreachable from any
pre-decision observable**: a 38-feature ridge fit on seven months and scored on the eighth books
**−0.00009 R/trade** at the same capacity — statistically indistinguishable from ranking on the
fee schedule alone (`-cost_r` books −0.01045). The real system already captures 10.81 % of the
range; the reachable ceiling is 12.80 %.

And the joint pricing kills the arithmetic that would otherwise look like a repair. The three
deployable improvements this lane found are worth **+0.01778 / +0.00621 / +0.09714 alone** and
**+0.00553 together, out of sample — a double-count factor of 21.9×**, 2.5× worse than the worst
overlap the estate had previously recorded.

---

## 1. VALIDATION ANCHOR (read before believing anything below)

Population: Session PB's reproduced sealed roster, close-only (`k=15`), **AT-MARKET cohort**
(the seven families the live engine can place), eight windows Oct-2025 … May-2026.
**n = 141,230 rows, 172 trading days, 841.4 emissions/day.** Tape, cost model, walkers and frame
builder are f2's, unchanged.

| | published (f2, January) | d2 recomputation | abs diff |
|---|---:|---:|---:|
| n | 17,722 | 17,722 | 0 |
| gross R/trade | +0.038179684 | +0.038179684 | 0 |
| cost R/trade | 0.335605167 | 0.335605167 | 0 |
| net R/trade | −0.297425483 | −0.297425483 | 0 |

Pooled R1 over eight windows: n 141,230, gross **+0.02328**, cost **0.31553**, net **−0.29226**
(day-block CI95 [−0.30865, −0.27662], p(≤0) 1.000).

---

## 2. THE LAYER TABLE — leave-one-oracle-in, from the FULL REAL STACK, same rows

Full real stack = shipped cost gate + shipped M15-close instant + shipped 2R/−1R exit:
**n 58,618, gross +0.00223, cost 0.06848, net −0.06625.**

| layer | NULL | **REAL** | FEASIBLE (out of sample) | ORACLE | oracle gap | **reachable share of gap** |
|---|---:|---:|---:|---:|---:|---:|
| **GATE** | −0.27843 *(random, same size)* | **−0.06625** | −0.02534 | +0.98796 | +1.05421 | **3.88 %** |
| **RANK** *(K=3/day)* | −0.29025 *(random pick)* | see §5 | −0.00009 | +1.97717 | +2.26742 | **12.80 %** |
| **ENTRY TIMING** | −0.29226 *(= the shipped instant)* | **−0.29226** | −0.27600 *(fixed j=5)* | +0.28724 | +0.57950 | **2.80 %** |
| **EXIT** | −0.06288 *(random contract from its own menu)* | **−0.06625** | −0.04847 *(`stop_only_horizon`)* | +0.70074 | +0.76699 | **2.32 %** |
| **SIZING** | — | **constant** | — | +0.97362 | +0.99294 | **layer does not exist** |

Capture fractions, `(REAL − NULL) / (ORACLE − NULL)`:

| layer | capture of the oracle | capture of its own REACHABLE ceiling |
|---|---:|---:|
| GATE | **16.75 %** | **83.8 %** (0.1675 / 0.1999) |
| RANK | **10.81 %** | **84.5 %** (0.1081 / 0.1280) |
| EXIT | **−0.44 %** on the gate-admitted book, **−0.96 %** on the full population — *destroys value either way* | negative |
| ENTRY TIMING | **0 %** — no such layer exists; the shipped instant IS the null | 0 % |
| SIZING | undefined — the layer is a constant | — |

**Answer to "which layer has the largest absolute gap": RANKING, +2.267 R/trade of range.**
**Answer to "is it therefore the highest-value engineering target": no — 87.2 % of that gap is
unreachable, and the system is already at 84.5 % of the reachable part.**

### 2.1 The oracle denominators are mostly not signal

f2's matched placebo, on these exact rows: every oracle rung is **98.2–100.8 % reproduced by a
coin flip on the same rows, instants and risk distances**. Signal-attributable levels:

| rung | real net | placebo net | **signal** |
|---|---:|---:|---:|
| R1 shipped | −0.29226 | −0.29447 | +0.00221 |
| oracle exit (menu) | +1.07007 | +1.05073 | **+0.01933** |
| oracle exit (path) | +1.71862 | +1.69333 | **+0.02529** |
| oracle entry + menu exit | +1.94958 | +1.92389 | **+0.02569** |

So the +1.05 / +2.27 / +0.77 "gaps" in the table above are path volatility available to any
participant. **The signal-attributable size of every layer's headroom is ≈ +0.02 R/trade against
a 0.3155 R/trade toll.**

---

## 3. GATE — the only layer that earns its keep, and it is nearly done

| book | n | gross | cost | net |
|---|---:|---:|---:|---:|
| admit all | 141,230 | +0.02328 | 0.31553 | −0.29226 |
| random book, same daily size | — | — | — | −0.27843 |
| **shipped cost gate** (`spread_r ≤ 0.10 & cost_r ≤ 0.15`) | 58,618 | +0.00223 | 0.06848 | **−0.06625** |
| + session gate (P9) | 31,364 | −0.00088 | 0.06732 | −0.06820 |
| oracle, same admit rate | 59,222 | +1.22412 | 0.23616 | +0.98796 |
| anti-oracle | 59,222 | −0.95423 | 0.45172 | −1.40594 |

**8/8 months: REAL beats RANDOM.** The gate's entire value is toll removal — it takes gross from
+0.02328 to +0.00223 (i.e. **the gate makes the directional content slightly WORSE**) while
cutting the toll 4.6×.

**The feasible gate.** A grid over every pre-decision observable (toll cap × risk-distance floor ×
session), fit on seven months and tested on the eighth: pooled OOS **−0.02534** — better than the
shipped gate by +0.04091, but **positive on only 2 of 8 held-out months** (Oct +0.0115, Nov +0.0085;
the other six run −0.015 to −0.058). The in-sample winner is always `cost_r ≤ 0.03`, which is the
affordability trap the swarm already buried.

**The gate turns harmful the moment the toll stops binding.** With an oracle exit, `gate=null`
books **+1.07007** and `gate=real` books **+0.70074** — the shipped gate costs **−0.36933** once
the toll is not the constraint. Mechanism: it selects on affordability, and affordability is
anti-correlated with path range.

### 3.1 The 8-gate opportunity ledger, recomputed on the ROSTER

l6 built this on the January pool (27,658 rows, 100 % counterfactual). Here it is on the roster —
**all ten families, all eight windows, 1,167,100 emissions, honest first-touch fill** — where a
refusal *rate* is meaningful for the first time.

Population: gross −0.02441, cost 0.08388, **net −0.10829**, fill rate 29.53 %, past-stop 2.01 %.
(At-market sub-cohort: 141,331 rows, fill 99.03 %, net −0.31665. POI: 1,025,769 rows, fill 19.95 %,
net −0.07959.)

| predicate | refusal rate | refused set net | kept set net | **marginal Δnet from keeping it** | unique blocks | verdict |
|---|---:|---:|---:|---:|---:|---|
| `P2 cost_r > 0.15` | 49.80 % | −0.17838 | −0.03877 | **+0.01320** | 29,918 | **earns its keep — the only one** |
| `P1 spread_r > 0.10` | 47.04 % | −0.15515 | −0.06668 | **+0.00264** | 36,216 | marginally positive |
| `P9 off_configured_session` | 70.56 % | −0.11397 | −0.09470 | **−0.00478** | **293,488** | **net harmful, largest by count** |
| `P6 fill_prob < 0.45` | — | — | — | **0** | 0 | structurally cannot fire (§3.2) |
| `P7 fill_prob < 0.80` | — | — | — | **0** | 0 | structurally cannot fire (§3.2) |
| `P3/P4/P8` EV floors | — | — | — | — | — | l6 measured 0 unique blocks; carried, not re-derived |

Reconstructable 3-gate stack: **n 178,573, gross −0.01984, cost 0.02251, net −0.04235,
25 of 171 days net-positive.**

**l6's conclusion survives the population change with one sign flip.** P2 is still the only gate
that pays (+0.01320 here vs +0.03235 on the pool); P9 is still net harmful and still the biggest
by count (−0.00478 vs −0.00923); **P1 flips sign** (+0.00264 here, −0.00391 on the pool) — a
gate whose verdict was an artifact of the pool's conditioning.

### 3.2 P6/P7 are structurally inert on the live-expressible book — measured, not assumed

`poi_execution_lifecycle.py:162-176` sets `limit_marketable = (LONG and entry >= current) or
(SHORT and entry <= current)`; `:174-194` then returns a flat **0.92** for a marketable limit.
An at-market emission's entry **is** the decision-instant close, so every one of the 141,331
at-market roster rows carries `execution_fill_probability = 0.92`, above both the 0.45 selector
floor and the 0.80 scheduler floor. **The two fill-probability gates cannot fire on the cohort the
live engine can actually trade.**

---

## 4. THE LARGEST GATE IN THE SYSTEM HAS NEVER BEEN NAMED, AND IT IS A LOOK-AHEAD

Joining the roster to the diagnostic pool on `(symbol, decision_time_utc, entry_price)`:

| | n | share | **fill rate** | past-stop | gross | cost | net |
|---|---:|---:|---:|---:|---:|---:|---:|
| in the pool | 208,852 | **17.90 %** | **99.43 %** | 10.57 % | −0.18246 | 0.25444 | −0.43690 |
| **not in the pool** | 958,248 | **82.10 %** | **14.29 %** | 0.15 % | +0.01004 | 0.04671 | −0.03667 |

The pool's admission test is `opportunity_net_proxy_r is not None`
(`v4_timewarp_simulated_live_research_loop.py:28130-28140`), and a candidate whose entry level is
never touched has no proxy to compute. **The measured consequence: the diagnostic pool is
overwhelmingly the subset whose entry was reached — a 7.0× enrichment in fill rate and a 70×
enrichment in born-past-stop rows, conditioned on what price did AFTER the decision.**

Every number the estate has published "on the pool" is therefore computed on a path-conditioned
sample. This does not invalidate findings *about the gate* (correctly measured there), and it is
the quantitative form of f1's "the pool is the wrong object".

---

## 5. RANK — the biggest gap, the smallest reachable share, and the system is nearly at its ceiling

### 5.1 Where the system's actual picks landed

l12 tested the 15-component score inside the pool, which contains no pick by construction. Here
each decision window is rebuilt as **pool (refused) ∪ taken (executed)**, honest fill, broker-true
toll, all eight windows: **203,784 rows, 507 executed picks, 19.9 alternatives per selected window.**

| | net R/trade |
|---|---:|
| window oracle (best available that instant) | **+1.70546** |
| **the system's actual pick** | **−0.12609** |
| reconstructed production score's own pick | −0.18675 |
| random pick from the same window | −0.34809 |
| window worst | −1.54453 |

**Mean outcome percentile of the real pick inside its own window: 0.5835** (median 0.5641),
better than 0.5 in **8 of 8 windows**. **Capture 10.81 %** of the available range; the production
score alone captures **7.86 %** — i.e. **the shipped stack picks better than its own score does.**

### 5.2 …and the advantage is instrument selection, not candidate selection

Paired inside the window, n = 507:

| | value | t |
|---|---:|---:|
| Δ net vs window mean | **+0.22199** | **4.352** |
| — of which Δ gross | **+0.20029** | 3.987 |
| — of which cheaper toll | +0.02170 | — (9.8 % of the total) |
| Δ net, **same window + same symbol + toll ±25 %** | **+0.01241** | **0.099** (n=116) |
| Δ net, same window + toll ±25 %, any symbol | +0.19024 | 2.849 (n=398) |

**Holding the instrument fixed inside the same decision window destroys the advantage
(+0.0124, t 0.099).** Holding only the toll fixed does not (+0.1902, t 2.849). The real ranker's
value is *which instrument to be in that minute*, not *which candidate on that instrument*.
(n=116 for the symbol-matched arm — thin, and stated as such.)

### 5.3 The score orders the fee schedule

Reconstructed production score (weights from `l12b_full_score.py`, read out of the allocator and
selector), 177,284 rows carrying every term:

| Spearman of score with | ρ |
|---|---:|
| **net R** | **+0.18620** |
| **gross R** | **+0.07939** |
| **toll (cost_r)** | **−0.30623** |

| decile | n | gross | cost | net | win |
|---:|---:|---:|---:|---:|---:|
| 1 | 17,729 | −0.26107 | 0.40245 | **−0.66351** | 0.2749 |
| 5 | 17,728 | −0.24575 | 0.25502 | −0.50077 | 0.3019 |
| 10 | 17,729 | −0.10131 | 0.14818 | **−0.24949** | 0.3842 |

The d10−d1 net spread is +0.41402, of which **+0.15976 is gross and −0.25427 is toll: 61.4 % of
the entire ordering is the fee schedule.** Every decile is net-negative. `risk_finalizer_rank` —
the pipeline's own emitted rank — has Spearman with net of **−0.049 … +0.099 across seven windows
with the sign flipping**, i.e. nothing.

### 5.4 The reachable ceiling: a ranker fit on pre-decision information only

Ridge (38 features: toll, spread, risk distance, session, hour, 24 instrument dummies, 7 family
dummies) fit on seven months, top-3 per day of the held-out eighth, at the arm's own realised
capacity of **507 trades / 172 roster trading days = 2.948/day**:

| ranker | pooled OOS net | months beating random |
|---|---:|---:|
| oracle | **+1.97717** (gross exactly +2.00000 — every day contains ≥3 full-target winners) | 8/8 |
| **ridge, out of sample** | **−0.00009** | **8/8** |
| single field `−cost_r` | −0.01045 | — |
| single field `−spread_r` | −0.07095 | — |
| single field `risk_distance_bps` | −0.08242 | — |
| random | −0.29025 | — |
| anti-oracle | −5.61441 | — |

**Capture 12.80 %; the single cheapest-toll-first field alone captures 12.34 %.** Thirty-eight
features add 0.46 pp over one. The reachable range of the ranking layer is
**random −0.290 → breakeven −0.0001**, and the real system is already at 84.5 % of it.

---

## 6. ENTRY TIMING — the system has no such layer, and its default is the worst minute

`j=0` is the shipped M15-close instant; `j=1…14` are the M1 stamps covering the following M15 bar,
risk distance held at the generator's own `d`, shipped 2R/−1R contract.

| offset | pooled n | gross | net | offset | net |
|---|---:|---:|---:|---|---:|
| **j=0 (shipped)** | 141,230 | +0.02328 | **−0.29226** | j=7 | −0.28476 |
| j=1 | 139,671 | +0.01937 | −0.28485 | j=8 | −0.28879 |
| j=2 | 139,696 | +0.02003 | −0.28323 | j=9 | −0.28902 |
| j=3 | 139,630 | +0.02355 | −0.27924 | j=10 | −0.28734 |
| j=4 | 139,559 | +0.02622 | −0.27626 | j=11 | −0.28761 |
| **j=5 (best)** | 139,511 | +0.02620 | **−0.27600** | j=12 | −0.28780 |
| j=6 | 139,920 | +0.02355 | −0.28793 | j=13 | −0.29067 |
| | | | | j=14 | −0.28795 |

**j=5 beats j=0 in 8 of 8 months**; `j=0`'s rank among the 15 offsets is 13, 14, 15, 7, 14, 12, 4,
15 — **median 13.5 of 15**. This reproduces the swarm's "the M15 close is the worst entry minute"
independently, on the correct population, at-market, over eight windows. **Value: +0.01626
R/trade.** Oracle per-row best instant: +0.28724 (gross +0.60208 vs shipped +0.02328); the shipped
instant is already the per-row best on 57.2 % of rows.

---

## 7. EXIT — the only layer with NEGATIVE capture

Every exit contract a live engine can run, priced on the same paths, pooled, full population:

| contract | gross | **net** | win |
|---|---:|---:|---:|
| **`stop_only_horizon`** | +0.05828 | **−0.25726** | 0.3375 |
| `timestop_60` | +0.05154 | −0.26339 | 0.3894 |
| `trail_1R` | +0.05115 | −0.26439 | 0.4971 |
| `be_runner` | +0.04933 | −0.26620 | 0.2651 |
| `target_5.0R` | +0.04822 | −0.26731 | 0.3466 |
| `no_stop_horizon` | +0.03767 | −0.27786 | 0.4975 |
| *mean over the menu (the NULL)* | +0.03617 | **−0.27936** | — |
| `target_3.0R` | +0.03590 | −0.27964 | 0.3674 |
| `timestop_30` | +0.03197 | −0.28276 | 0.4231 |
| `timestop_15` | +0.02731 | −0.28722 | 0.4468 |
| **`target_2.0R` — SHIPPED** | +0.02328 | **−0.29226** | 0.3996 |
| `target_1.5R` | +0.01436 | −0.30117 | 0.4339 |
| `target_1.0R` | +0.00069 | −0.31484 | 0.4972 |

**The shipped exit is 10th of 12 and sits BELOW the menu mean: capture −0.96 %.** Swapping it for
`stop_only_horizon` is worth **+0.03500 R/trade** on the full population (day-block CI95
[+0.01854, +0.05163], **p(≤0) 0.0000**) and **+0.01778** on the gate-admitted book (CI95
[+0.00608, +0.03180], p 0.0035). **8/8 months positive** (+0.020 … +0.060), and
`stop_only_horizon` is the leave-one-month-out winner in **all eight** folds — the most stable
result in the lane. Per-trade oracle over the menu: +1.07007; path-max-close oracle: +1.71862.

---

## 8. SIZING — the layer does not exist on this population

All 507 executed trades carry `approved_risk_pct = 0.1` and `risk_cash = 100.0` **exactly**
(coefficient of variation 0.00000). `risk_per_trade_pct` takes three values (0.5 / 1.0 / 2.0) but
is the per-symbol config, not the applied size: risk-weighting by it moves the book by
**−0.00000 R/trade**. This is the S0R0 factorial arm's own definition (neutral selection, fixed
sizing), and it means **every published broad-family number is computed on a book with no sizing
layer at all.** Oracle sizing on the same 507 rows (all weight on the 45.04 % winners): **+0.97362
vs −0.01932 flat** — a +0.99294 gap that is 100 % hindsight and 0 % measurable capture.

---

## 9. JOINT ABLATION — never sum these, and here is the factor

### 9.1 Gate × exit are nearly additive

| | exit=null | exit=**real** | exit=feasible | exit=oracle |
|---|---:|---:|---:|---:|
| gate=null | −0.27936 | −0.29226 | −0.25726 | **+1.07007** |
| gate=**real** | −0.06288 | **−0.06625** | −0.04847 | +0.70074 |
| gate=oracle | +0.82397 | +0.98796 | +1.07178 | +2.14950 |

gate alone +0.21648, exit alone −0.01289, sum +0.20359, **joint +0.21312 → factor 0.955**
(mildly complementary, not double-counted).

### 9.2 The three DEPLOYABLE levers, priced jointly and out of sample — factor 21.9×

From the shipped stack (`gate on | j=0 | target_2R` = −0.06625), K=3/day, ranker fit on 7 months
and scored on the 8th:

| lever | alone | |
|---|---:|---|
| swap exit → `stop_only_horizon` | **+0.01778** | |
| shift entry → `j=5` | **+0.00621** | |
| add the pre-decision ranker at K=3 | **+0.09714** | |
| **sum of the three** | **+0.12114** | |
| **all three together, out of sample** | **+0.00553** | |
| | **double-count factor 21.9×** | |

The 32-cell lattice (`gate × 4 entry/exit arms × 4 rankers`) has exactly one net-positive
non-oracle cell: **`gate_on | shipped exit | shipped instant | ranker` = +0.03089 R/trade,
n=516, 5/8 months positive, +15.94 total R over eight months.** Equal-weight-by-month it is
+0.03283, **t = 1.652** (not significant); dropping February alone halves it to +0.01583. Against
the matched random-selection control at the same capacity it is **+0.12111, t = 2.084, 6/8 months**.

**Adding either of the other two "improvements" to that cell makes it worse**
(`+ stop_only` → −0.01363; `+ j=5 + stop_only` → −0.06072). At 3 trades/day the levers compete
for the same rows and the pre-decision signal is too weak to survive the re-fit.

---

## 10. WHAT WOULD HAVE TO BE TRUE

Total remaining reachable headroom, layer by layer, priced **alone** (each measured against the
same shipped stack, so these overlap and MUST NOT be read as a total):
gate **+0.04091** (positive in only 2/8 held-out months) · exit **+0.01778** (8/8, p 0.0035 on the
gate-admitted book; +0.03500 p 0.0000 on the full population) · timing **+0.01626** (8/8) ·
rank **+0.04512** → **sum +0.12007 R/trade**. Priced **jointly, out of sample: +0.00553.**

The book's gross is **+0.02328** and its toll is **0.31553**. Closing the gap needs
**+0.29226 R/trade** — **52.9× the joint deployable headroom, 2.43× even the (invalid) sum of the
standalone headrooms, and 6.5× the largest single-layer reachable improvement** (ranking, +0.04512).

**And the arithmetic lands on an exact, checkable statement.** The distance from a random book to
the best pre-decision ranker this estate can build is **+0.29016 R/trade** (−0.29025 → −0.00009);
the shipped book's distance to breakeven is **+0.29226 R/trade**. They are the same number to
within 0.7 %. So: **perfect reachable usage takes the broad family from −0.292 to exactly zero
(−0.00009 at 3 trades a day) and stops there.** The best cell in the whole 32-cell lattice reaches
**+0.031 R/trade on 516 trades — +15.9 R over eight months, 3 of 8 months negative, t = 1.652.**
That is what the usage is worth when every part of it is done as well as the information allows.

---

## 11. LIMITS

1. The layer ladder is the **AT-MARKET cohort only** (7 families, 141,230 rows). POI limits —
   46.1 % of pool rows and 88 % of roster emissions — are priced in §3.1 and §5 but not in §2;
   the live engine cannot place them (l10-X3).
2. §2's rank row and §5's rank numbers live on **different populations** (roster at-market vs
   pool∪taken). Both are stated with their own controls; the capture fractions are not pooled.
3. The gate ledger reconstructs **three** predicates. The enacted gates (`cost_authority`,
   `package_executable_authority_required_not_met`, `source_bound_router_refusal`,
   `scheduler_vetoed_*`) are pipeline-internal and are not reconstructable from roster geometry;
   l6's pool-based ledger remains the only measurement of those.
4. §5.2's symbol-matched control has **n = 116**. It is the weakest number quoted here.
5. `d2_gate.py` walks at-market rows with a **first-touch limit** contract, which is stricter than
   a market order; its at-market book (−0.31665) is therefore conservative against `d2_layers.py`'s
   market-fill book (−0.29226). The gate ledger's *relative* verdicts are unaffected.
6. The three READ_RESTRICTED 2025 windows (June / August / September) were **not opened.**
