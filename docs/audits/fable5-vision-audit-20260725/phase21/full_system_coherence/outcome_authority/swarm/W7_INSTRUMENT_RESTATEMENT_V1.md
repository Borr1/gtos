# W7 INSTRUMENT RESTATEMENT — what the owner should believe about the money at risk

**Wave 21, outcome-authority swarm. 2026-08-11.** Receipts: `w7_restatement_receipts/`.

**Measurement only.** No live path, no config, no broker call, no VPS touch, no `src/` byte.
Confers no arming, sizing, promotion or activation authority.

---

## 0. HEADLINE

> **The W7 recost caches ARE pre-repair — every cached `R` comes from a walker that has no
> way to represent a spread at all — but the correction is worth only −0.031, so the armed
> three's two-phase `p_pass` restates from the published **0.9172** to **0.9033** (joint
> median 0.9062), a change
> of −0.0139 that does NOT materially alter what the owner was shown; the two things that
> DO are that `sub_mid_dn_revert`, armed on both accounts today, loses 82.5 % of its gross
> and its corrected net expectancy at maximum carry is **−0.2446 R/trade with a 95 %
> interval entirely below zero**, and that `p_pass 0.9172` was published with a stated
> uncertainty of ±0.0011 when the evidence behind it supports a **95 % band of
> [0.474, 0.995]** once instrument and sampling uncertainty are carried jointly — a band
> whose lower edge sits *below* the driftless coin-flip value for a single phase.**

The −0.0139 is a net of two offsetting errors that had to be separated to be seen at all:
the quote-side instrument correction is **−0.031**, and cost-artifact drift since publication
is **+0.017**. Reported alone, either one misstates the answer.

Three sub-headlines, each measured here and each stated in its own direction:

1. **The instrument correction is real but small on armed money, and its size is
   predictable**: the armed sleeves are exactly the low spread-over-risk ones
   (`crypto` s/d 0.0093, `energy_agri` 0.0147, `sub_xvol_pullback` 0.0183). Lane D's
   inference that the defect reaches the W7 caches is **correct in fact and modest in
   consequence** — except on the fourth armed sleeve, where it is decisive.
2. **`p_pass 0.9172` is not reproducible at HEAD even before any instrument correction.**
   Identical machinery, identical 117-book-day population, current cost layer: **0.9340**.
   The cost artifact has been extended twice since publication, and the drift moves the
   number **UP** by +0.017 — so the published figure is stale in the *conservative*
   direction, and it happens to offset half the instrument correction. Phase 21's own
   `PRIOR_RECONCILIATION_V1.json` already stamps this:
   `GEOMETRY_AND_NONCOST_BLOCKS_REPRODUCED_COST_BLOCK_DRIFTED`.
3. **The simulation is not assuming a fantasy at the book level — and this is the one
   genuinely reassuring finding.** The full 11-sleeve W7 book's own recost expectancy at
   maximum carry is **−0.088 R/trade** published / **−0.127** corrected, and the live
   broker-true 142-trade record is **−0.068 R/trade** (z = +0.20 / +0.58). They agree. The
   positive `p_pass` comes **entirely from selecting the three or four positive sleeves out
   of eleven** — which is a selection question, not a simulation-drift question.

---

## 1. THE FIRST-PRINCIPLES CONSISTENCY CHECK

*Receipt: `w7_restatement_receipts/W7_IMPLIED_EDGE_V1.json`, script `w7_implied_edge.py`.*
*All scenarios are a per-trade shift to `R_gross` pushed through the UNMODIFIED
`mc_firm_rules.series()` + `mc()` path — same sizing, same Kelly bins, same cost pricing,
same carry, same firm rule ladder.*

### 1.1 The implied edge, stated as a number for the first time

The published cell is FTMO / armed three / forward 2025+ / worst carry / live-nominal
half-Kelly / `P2_BOTH_PHASES`. Its drift is not hidden — it is the per-trade expectancy of
its own 232 trades:

| quantity | FTMO armed 3 | redacted_account armed 3 |
|---|---:|---:|
| trades in window | 232 | 232 |
| mean **gross** R/trade | **+1.0570** (se 0.1240) | +1.0570 (se 0.1240) |
| mean **net** R/trade at max carry | **+0.8293** (se 0.1233) | +0.8258 (se 0.1225) |
| CI95 on net R/trade | **[+0.5877, +1.0710]** | [+0.5858, +1.0658] |
| per-trade net R implied by the *published* `p_pass` | **+0.7866** | +0.7682 |

**So `p_pass 0.9172` assumes +0.787 R per trade, net of broker-true cost, at 1.98 trades
per book-day.** That number has never appeared in any document.

### 1.2 The driftless floor, measured on the real barriers

| benchmark | FTMO | redacted_account |
|---|---:|---:|
| analytic gambler's ruin, **phase 1 only** (`b/(a+b)`) | **0.5000** (10/20) | **0.5556** (10/18) |
| analytic gambler's ruin, **both phases** (equity resets each phase) | **0.3333** | **0.3704** |
| **measured** driftless — same barriers, same block bootstrap, same daily rule, same sizing, book-day series demeaned | **0.2995** | **0.3230** |

The measured floor sits **below** the analytic one, exactly as expected: the daily-loss rule
and the path cap can only subtract. FTMO's two-phase driftless floor is **0.2995**, not
0.50 — the 0.50 figure is phase 1 alone, and a payout requires both.

### 1.3 `p_pass` recomputed at every edge that has actually been measured

FTMO, armed three, `P2_BOTH_PHASES`, 60,000 paths:

| edge assumption | R/book-day | %/month | **`p_pass`** |
|---|---:|---:|---:|
| published instrument, HEAD cost layer *(this harness)* | +0.38077 | +4.950 | **0.9340** |
| published artifact, 2026-07-29 cost layer *(what the owner was shown)* | +0.34623 | +4.501 | **0.9172** |
| driftless — book-day series demeaned | 0.00000 | 0.000 | **0.2995** |
| zero per-trade **net** edge | −0.10109 | −1.314 | **0.1331** |
| **live broker-true 142-trade mean, −0.068 R/trade** | −0.14060 | −1.828 | **0.0892** |
| zero per-trade **gross** edge (cost still charged) | −0.23336 | −3.034 | **0.0284** |

redacted_account, same ladder: 0.9534 / 0.9331 published / 0.3230 driftless / 0.2029 zero-net /
0.1480 at the live mean / 0.0576 zero-gross.

### 1.4 Where the implied edge does and does not exceed what has been measured

The comparison must name populations, because three different ones are in play:

| measured quantity | population | value | vs the implied +0.83 R/trade net |
|---|---|---:|---|
| archive walk, **the same three sleeve names, like-for-like whole span** | r1's 336 archive trades, 2006–2026 | uncorrected **+0.79321** → corrected **+0.72097** R/trade gross, against the cache's whole-span **+0.92962** → **+0.86860** (n = 356) | **same sign, 85 % of the magnitude uncorrected and 83 % corrected — an independent walk on an independent archive reproduces this edge. It is corroborated, not invented.** |
| live broker-true, **full W7 book** | 142 trades, 2026-06-19→07-02, pre-arming | **−0.068 R/trade** | different population — the whole book, not the armed subset |
| Lane G's funnel pool | 74,249 broad-V4 fills | `E[gross + spread_r]` **+0.0078 ± 0.0042 R/fill** | **a different programme entirely** — the broad V4 family, not the W7 sleeves. Not evidence about these sleeves in either direction. |

**Verdict on the consistency check: the implied per-trade edge is large but it is NOT an
assumption the simulation invented.** Two independent walks — the W7 cache's generator on the
absent deep-H4 archive, and r1's corrected walk on `vps-bars-20260727` — measure the same
three sleeves at the same sign and within 15 % of each other on a like-for-like whole-span
basis. **The hypothesis that `p_pass 0.9172` requires a drift nobody has ever measured is
NOT supported, and this report will not claim it.** These are high-target, low-frequency
sleeves (4R runners); a per-trade R near +1 is what their geometry produces, and it is the
reason `sub_xvol_pullback` alone carries +1.31 R/trade.

**What is not supported is different and is quantified in §4:** the *frequency* and the
*window*. The same three sleeves earn **0.313 %/month** on the archive against
**4.501 %/month** in the cache's forward window, and 77 % of that gap is firing rate.

### 1.5 The book-level reconciliation — the strongest single result in this report

| | FTMO | redacted_account |
|---|---:|---:|
| full 11-sleeve book, net R/trade at max carry, **published instrument** | **−0.08797** | −0.16569 |
| same, **quote-side corrected** (median of 150 replicates) | **−0.12713** | −0.20484 |
| 95 % interval on the corrected figure | [−0.15330, −0.10841] | [−0.23100, −0.18612] |
| **live broker-true, 142 trades** | **−0.06807** (se 0.1015) | −0.06807 |
| z (live vs published / vs corrected) | **+0.20 / +0.58** | +0.96 / +1.35 |

**The W7 recost already said the book as a whole loses money, and the live record agrees
with it to within a fifth of a standard error.** Nothing about the machinery is fantastical.
Every positive number in this programme is a statement about a **subset** of that book.

### 1.6 The frequency assumption does **not** inflate `p_pass`

*Receipt: `W7_RATIO_AND_FREQUENCY_V1.json`.*

`p_timeout` is **0.0000** — the MC draws book-days until a barrier is hit, with a 2,000-day
path cap that never binds. **`p_pass` is therefore mathematically invariant to trade
frequency.** Frequency scales the headline rate and the calendar clock, and nothing else:

| book-days/month | source | %/month | median **calendar** days to pass |
|---:|---|---:|---:|
| 6.50 | the MC's in-window assumption | **+4.950** | **89** |
| 7.00 | `CLAUDE.md`'s stated expectation | +5.331 | 83 |
| **2.37** | **Lane F, measured live** (1 signal day in 12.85 d) | **+1.804** | **244** |
| 0.83 | the archive, whole span | +0.633 | 696 |

So Lane F's low observed trade count is **not** a reason to discount `p_pass`. It *is* a
reason to discount the **4.501 %/month headline by 2.74×** and to expect **~8 months, not
~2**, to a first payout. Lane F's own Poisson check (P(X ≤ 1 | λ = 2.96) = 0.206) says the
observed rate is not yet a contradiction.

---

## 2. INSTRUMENT STATE OF EACH CACHE

*Receipt: `W7_INSTRUMENT_STATE_V1.json`, script `w7_instrument_state.py`.*

### 2.1 The answer

| artifact | instrument | how established |
|---|---|---|
| `INTEG_W3_streams_cache.pkl` | **PRE-REPAIR** | code path + population identity |
| `INTEG_W5_new_streams_cache.pkl` | **PRE-REPAIR** | same |
| `W7_RECOST_V1.json` | **PRE-REPAIR (inherited)** | arithmetic only on the cached `R`; no bar is ever re-read |
| `SURVIVOR_BOOK_V1.json` | **PRE-REPAIR (inherited)** | `import recost_w7_validation as M` → `M.build()` |
| `MC_FIRM_TRUE_V1.json` | **PRE-REPAIR (inherited)** | same |
| `ARMED_SET_MC_V1.json` | **PRE-REPAIR (inherited)** | same |
| `phase8/receipts/BOOKS_MC_V1.json` | **PRE-REPAIR (inherited)** | `import mc_firm_rules as Q` → `M.build()` |

**Independently corroborated the same day, from a different lane.** The barrier-clock
blast-radius assessment (`71226c7b6`) reached the identical structural conclusion by a
different route: *"Every named figure — AD/AK/AQ/AU frontier cells, `mx_btcusd @ target_5R`,
`SURVIVOR_BOOK_V1` tiers, the `p_pass` series — sits on that lineage or on **cached daily-R
arithmetic with no walk at all**."* That is `recost_w7_validation.py:688`, found from the
opposite direction. It also clears these caches of BCD-1: the sleeve estate's entry is the
signal bar's close and every barrier loop starts at `i+1`, so decision instant == fill
instant.

**There is one `R` population, not five.** `build_survivor_book.py:54`, `mc_firm_rules.py:104`,
`armed_set_mc.py:73-74` and `ai_books_mc.py:69` all reach the same two pickles through
`recost_w7_validation.build()`. Correct or fail to correct the caches and every published
`p_pass`, every %/month and every survivor tier moves together.

### 2.2 Proof 1 — the code path (constructive, and decisive)

The repair has exactly one degree of freedom: the `entry_price` keyword on
`src/research_infra/walkforward/exits.py:359`, which lane r1 fills with
`replay_anchor(...) = bar_close + direction × spread`.

The walker that produced every cached `R` is
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/geometry_lib.py:21`:

- `:27` — `entry = bars[i].c`. **No `entry_price` parameter exists.**
- `:9-11` — `Bar` carries `o, h, l, c, v`. There is no field that could hold an ask or a spread.
- `wave1_structure_setups_ict.py:71-73` — the CSV loader constructs `Bar(open, high, low,
  close, volume)` and **discards the archive's `spread` column**.
- `:36, 38, 43, 44, 53, 55, 60, 61` — every return subtracts a flat scalar `cost`.

**A walk cannot cross a spread it never loaded.** This is a statement about the function's
type signature, not an inference from prose. The bars themselves are BID: r1 measured
`close == last tick BID` on **33 of 33** symbols and `(close − mid)/spread = −0.500000`
across 87,060 M15 bars (`R1_QUOTESIDE_M15_V1.json`).

And the recost never re-walks. `scripts/recost_w7_validation.py:688` is the whole method:

```python
r["R_gross"] = r["R"] + r["charged_cost_r"]
```

No `import geometry_lib`, no `simulate(`, no `_H4.csv` read, no `w1.load` anywhere in
`recost_w7_validation.py`, `build_survivor_book.py`, `mc_firm_rules.py` or `armed_set_mc.py`.

### 2.3 Proof 2 — the population identity (measured here)

If the walk had crossed a per-trade spread, the cached `R` would carry a per-trade
`spread / stop_distance` term. That term provably varies: the estate's own spread model
measures era ratios spanning **50×** (EURUSD 2000–2003) to **0.18×** (XAUUSD 2020–2024), and
r1 measures per-sleeve `s/d` medians from **0.0093** to **0.0889**.

Measured on the caches: for every `(sleeve, symbol)` pair charged a **flat** class cost —
**81 of 81 pairs with stop-outs, covering 3,814 stop-out rows spanning 2015–2026** — the cost
recovered from the stop-out rows has **exactly one distinct value**. Zero dispersion, to nine
decimal places, over eleven years.

The eight pairs that *do* show dispersion are exactly the twelve `charge_kind: per_trade`
pairs (`metals_core`, `energy_agri`), whose generator scales the class cost by
`0.5 × ATR14(H4) / sd_h4` at `INTEG_portfolio_build_w3.py:89` — a documented volatility
scaling, not a spread. Across all 102 witness pairs the recost's up-to-three independent
cost recoveries (source cost-map, D4 re-sim, stop-out) **agree 102/102**.

**The charge for crossing the market in these caches is a scalar constant per instrument
across the whole span. No spread-crossing walk can produce that.**

### 2.4 Proof 3 — a per-row identity is impossible, not merely absent

The cached `R` identifies its own exit reason exactly (a stop books `−1 − c`, a target
books `T − c`, both to float precision). Reconstructed over 8,503 rows:

| exit | rows | share |
|---|---:|---:|
| stop | 3,920 | **46.1 %** |
| target | 4,272 | 50.2 % |
| trail / maxbars / other | 311 | 3.7 % |

But the cache carries **no decision timestamp, no direction and no exit index**. On its only
available join key `(sleeve, symbol, date)` the maximum multiplicity is **6**, and **4,111 of
8,503 rows (48.35 %)** sit on a non-unique key. So Lane G's per-row-identity method **cannot
be transferred to this cache** — and that is a property of the artifact, not a gap in this
work. Phase 21's own `PRIOR_RECONCILIATION_V1.json` stamps the same conclusion independently:
`exact_rejoinable_from_cache_key: false` on all four armed sleeves.

**This is why §3 is a structural transfer and not a re-walk, and why it carries an interval.**

### 2.5 Why a re-walk is impossible on this machine

`wave1_structure_setups_ict.py:46-47` reads
`data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022` and `..._2022_2026`. Neither exists
in this worktree, in `/Users/borr/GTOSActive/repo/data/mt5_research_exports/` (which holds
nine other export sets), or anywhere on this machine. Worse, **the loader fails OPEN**:
`:61-62` returns an empty universe for a missing directory rather than raising, and
`INTEG_portfolio_build_w5.py:181` short-circuits to the existing pickle if it is present. A
naive rebuild attempt would not error — it would silently produce empty streams.

---

## 3. THE RESTATEMENT, WITH INTERVALS

*Receipts: `W7_INSTRUMENT_STATE_V1.json`, `W7_SURVIVOR_TIERS_V1.json`,
`W7_PASS_INTERVALS_V1.json`, `W7_JOINT_INTERVAL_V1.json`.*

### 3.1 The transfer, and the identity that makes it exact where it matters

r1's 22,354-row corrected walk gives the correction's exact structure:

| migration | rows | delta |
|---|---:|---|
| `stop → stop` | **13,221 / 13,221** | **0.0**, max abs 1.12e-12 |
| `target → target` | **6,816** | **0.0**, max abs 5.27e-13 |
| `target → stop` | 732 | `−(1 + T)` |
| `trail → trail` | 1,042 | continuous |
| `maxbars → maxbars` | 362 | continuous |
| `trail → stop` | 127 | large |
| `maxbars → stop` | 50 | large |
| `target → maxbars` | 4 | large |

**The correction is identically zero on every level exit that does not migrate.** Because the
cache reconstructs its own exit reason, **46.1 % of the book is provably unmoved** and only the
target rows (50.2 %) and trail/maxbars rows (3.7 %) carry any uncertainty at all. That
uncertainty is propagated by drawing each sleeve's `target → stop` migration rate from its
Jeffreys posterior `Beta(k + ½, n − k + ½)` and each trail/maxbars delta from r1's own
empirical distribution for that sleeve — **300 replicates**, each pushed through the full
unmodified pipeline.

Per-sleeve migration rates (r1, mid band): `sub_mid_dn_revert` **0.1929** (38/197) — the
estate's highest — `fx_jpy` 0.1089, `crypto` 0.1053, `fx_jpy_ny` 0.0682, `metals_softband`
0.0423, `metals_core` 0.0345, `idxrev` 0.0107, `energy_agri` / `sub_xvol_pullback` /
`metals_ob_micro` **0.0000**.

### 3.2 The restated book

`P2_BOTH_PHASES`, forward 2025+, worst carry, live-nominal half-Kelly, at the HEAD cost layer.
**The uncorrected column is the control** — same harness, same day, instrument the only change.

The full ladder for the headline cell, so nobody reads one step as the whole answer:

| step | `p_pass` | change |
|---|---:|---:|
| published artifact (2026-07-29 costs, uncorrected walk) | **0.9172** | — |
| + cost-artifact drift to HEAD | 0.9340 | **+0.0168** |
| + quote-side instrument correction | **0.9033** | **−0.0307** |
| **net vs what the owner was shown** | | **−0.0139** |

`0.9033` is the number to use going forward: it is the current cost layer and the corrected
instrument. It is not "the published number re-walked" — that quantity is not well defined,
because the cost artifact the published number used no longer exists at HEAD.

| book | uncorrected | **CORRECTED (median)** | **95 % instrument interval** | Δ |
|---|---:|---:|---:|---:|
| **FTMO armed 3** | 0.93398 | **0.90328** | **[0.77568, 0.93189]** | **−0.0307** |
| redacted_account armed 3 | 0.95340 | **0.93225** | [0.82871, 0.95227] | −0.0212 |
| **FTMO armed 4** *(the launcher's actual set)* | 0.92760 | **0.87405** | **[0.71039, 0.91421]** | **−0.0536** |
| redacted_account armed 4 | 0.94995 | **0.91000** | [0.77557, 0.93942] | −0.0400 |

Monthly rate, same cells:

| book | uncorrected %/mo | **CORRECTED %/mo** | 95 % interval |
|---|---:|---:|---:|
| FTMO armed 3 | +4.950 | **+4.185** | [+2.695, +4.861] |
| redacted_account armed 3 | +5.304 | **+4.539** | [+3.050, +5.216] |
| FTMO armed 4 | +5.509 | **+4.329** | [+2.667, +5.091] |
| redacted_account armed 4 | +5.928 | **+4.748** | [+3.087, +5.510] |

### 3.3 The interval that actually matters, and the one that was published

Lane A found no confidence interval anywhere in phases 19–21. Here is the concrete cost of that.

| | FTMO armed 3 | FTMO armed 4 |
|---|---:|---:|
| book-days of evidence | **117** | 173 |
| mean R/book-day | +0.38077 | +0.28659 |
| **CI95 on the edge itself** | **[+0.16777, +0.59377]** | [+0.12692, +0.44627] |
| t on the mean | 3.50 | 3.52 |
| published `se_p_pass` (MC seed noise only) | **±0.001125** | — |
| **moving-block bootstrap CI95 on `p_pass`** | **[0.70053, 0.99761]** | [0.65902, 0.99590] |

**The published uncertainty on `p_pass 0.9172` was ±0.0011. The evidence supports ±0.149.
The stated interval was 67× too narrow, because it reported the simulation's noise instead
of the sample's.** The edge is distinguishable from zero *on its own window* (t = 3.50) —
but that window is the window that selected the sleeves.

### 3.3b The joint band — the number to quote

Instrument correction **and** sampling uncertainty together: 250 replicates of
(quote-side migration posterior × moving-block bootstrap over book-days × full firm-rule MC).
*Receipt: `W7_JOINT_INTERVAL_V1.json`.*

| book | **median `p_pass`** | **95 % joint band** | 10th pct | %/month | 95 % band |
|---|---:|---:|---:|---:|---:|
| **FTMO armed 3** | **0.9062** | **[0.4736, 0.9953]** | 0.7047 | +4.210 | [+0.855, +7.270] |
| redacted_account armed 3 | 0.9486 | [0.6438, 0.9987] | 0.7821 | +4.590 | [+1.606, +7.306] |
| **FTMO armed 4** *(the launcher's set)* | **0.8598** | **[0.3719, 0.9838]** | 0.6137 | +4.033 | [+0.434, +7.510] |
| redacted_account armed 4 | 0.9053 | [0.5780, 0.9933] | 0.7358 | +4.554 | [+1.587, +7.375] |

**Read the lower bounds against §1.2.** FTMO's armed-three band reaches **0.474** — below the
analytic phase-1 driftless value of 0.500. FTMO's armed-**four** band reaches **0.372**, which
is the two-phase driftless floor of 0.333 to within four points. **117 book-days of evidence
cannot distinguish the armed book from a driftless account at the 2.5 % tail.** That is not a
claim that the edge is absent — the median is 0.86–0.91 and the in-window edge carries
t = 3.50 — it is a statement about how much 117 book-days can support, and it is the single
most important correction this report makes to how `p_pass` has been presented.

### 3.4 Per-sleeve restatement — and the one row that matters

FTMO, 150 replicates. `net@max` is `sleeve_table(...)['net_r']['n_max']`, the predicate the
survivor book itself reads.

| sleeve | n | gross published → **corrected** | Δ | net@max published → **corrected** | 95 % interval |
|---|---:|---|---:|---|---|
| `crypto` **(armed)** | 104 | +1.2121 → **+1.0099** | −16.7 % | +0.7836 → **+0.5815** | [+0.2353, +0.7716] |
| `energy_agri` **(armed)** | 162 | +0.5386 → **+0.5348** | −0.7 % | +0.5197 → **+0.5159** | [+0.4257, +0.5166] |
| `sub_xvol_pullback` **(armed)** | 90 | +1.3070 → **+1.3061** | −0.1 % | +1.0072 → **+1.0063** | [+0.8730, +1.0064] |
| **`sub_mid_dn_revert` (ARMED)** | 398 | +0.3166 → **+0.0553** | **−82.5 %** | **+0.0167 → −0.2446** | **[−0.3507, −0.1240]** |
| `fx_jpy` | 530 | +0.2823 → +0.1436 | −49.1 % | +0.2823 → +0.1436 | [+0.0842, +0.1965] |
| `fx_jpy_ny` | 197 | +0.2690 → +0.1797 | −33.2 % | +0.2690 → +0.1797 | [+0.0908, +0.2473] |
| `vp_euidx_pocgrav` | 341 | +0.2982 → +0.1948 | −34.7 % | −0.0787 → −0.1821 | [−0.2516, −0.1385] |
| `metals_softband` | 70 | +0.3780 → +0.3306 | −12.5 % | −0.3264 → −0.3738 | [−0.5083, −0.3265] |
| `metals_core` | 131 | +0.9103 → +0.8872 | −2.5 % | +0.1754 → +0.1523 | [+0.1303, +0.1639] |
| `idxrev` | 6,473 | +0.0059 → **−0.0057** | **sign flip** | −0.1825 → −0.1940 | [−0.1988, −0.1893] |
| `metals_ob_micro` | 7 | −0.5000 → −0.5000 | 0 % | −0.8137 → −0.8137 | [−1.0637, −0.8137] |

**`sub_mid_dn_revert` is armed on both accounts and its corrected net expectancy at maximum
carry is negative with a 95 % interval that excludes zero.** This is corroborated
independently: lane m3 measured **−59.6 %** of published gross for the same sleeve on the
*archive* population; here it is **−82.5 %** on the *cache* population. Two populations, two
walkers, same direction. It has the estate's highest migration rate (19.3 %) and its second
highest spread-over-risk (0.0871).

### 3.5 Survivor tiers

| account | as published (2026-07-29) | current cost layer, uncorrected | **corrected** |
|---|---|---|---|
| **FTMO** | crypto, energy_agri, **metals_core**, sub_xvol_pullback (4) | + fx_jpy, fx_jpy_ny, **sub_mid_dn_revert** (7) | crypto, energy_agri, fx_jpy, fx_jpy_ny, metals_core, sub_xvol_pullback (**6**) |
| **redacted_account** | crypto, energy_agri, sub_xvol_pullback, **vp_euidx_pocgrav** (4) | + fx_jpy, fx_jpy_ny, sub_mid_dn_revert (7) | crypto, energy_agri, fx_jpy, fx_jpy_ny, sub_xvol_pullback (**5**) |

**Tiers that change under the correction: `sub_mid_dn_revert` loses survivor status on both
accounts (P(survives) = 0.000 over 300 replicates), and `vp_euidx_pocgrav` loses it on
redacted_account.** Note also that the *cost layer alone* — with no instrument change — already
moved the survivor count from the published 4 to 7 on both accounts. `SURVIVOR_BOOK_V1.json`
is stale on two independent axes.

**One transfer caveat, stated rather than buried.** `vp_euidx_pocgrav` has **no counterpart
in r1's estate walk**, so its correction uses the pooled estate calibration. Its cache exit
mix is 219 stop / 0 target / 122 other, so the target-migration mechanism does not apply to
it at all and its entire correction comes from the pooled trail/maxbars pool. Treat its
tier change as **weaker evidence** than `sub_mid_dn_revert`'s.

---

## 4. THE 14.38× VERDICT — instrument, population, or period?

*Receipt: `W7_RATIO_AND_FREQUENCY_V1.json`.*

**Neither. It is period × population × edge, and the instrument contributes exactly zero.**

The ratio decomposes exactly and reproduces the published figure:

```
14.38  =  1.837 (R per book-day)  ×  7.826 (book-days per calendar month)
       =  1.84 × 14.377  ✓  (published 14.38)
```

| factor | value | log share |
|---|---:|---:|
| edge per book-day (0.34623 vs 0.18846) | **1.837×** | 22.8 % |
| **firing frequency** (6.500 vs 0.831 book-days/month) | **7.826×** | **77.2 %** |

**The frequency factor then splits again**, measured inside the archive walk itself so no
new population is introduced:

| | signal days/month | |
|---|---:|---|
| archive, whole span 2006-05→2026-06 (242 months) | 0.851 | |
| **archive, its own 2025+ window** (18 months) | **3.889** | |
| **within-archive PERIOD factor** | **4.568×** | the archive's thin pre-2025 history |
| residual **POPULATION** factor (cache 6.500 vs archive-2025+ 3.889) | **1.713×** | the cache's generator fires denser than AA's re-walk in the same window |

**Final attribution: 14.38× = 4.57× period × 1.71× population × 1.84× edge.**

**Instrument is zero by construction** — both sides of the published ratio were computed on
the same uncorrected walk, so the correction cancels in the numerator and denominator alike.

**What this means for whether the in-window economics were ever meaningful.** The largest
single factor is **not** an edge claim: it is that the same sleeves barely fired before 2025
in an archive whose early coverage is thin. Comparing 4.501 %/month against 0.313 %/month is
therefore **not** an in-sample-vs-out-of-sample comparison of *edge* — three-quarters of it is
a statement about how many days each population contains. The honest out-of-window question is
the **1.84× edge factor**, and 1.84× is a real degradation but it is an order of magnitude
smaller than the headline gap implies. `CLAUDE.md`'s standing instruction — "treat the small
number as the expected case" — is right for the wrong reason, and the right reason is §1.6:
at Lane F's measured firing rate the honest headline is **+1.80 %/month, not +4.50 %**.

---

## 5. THE CONSEQUENCE FOR THE LIVE BOOK

**In one sentence:** *After correcting the instrument, the currently armed book's honest
expected economics are `p_pass` **0.903** two-phase on FTMO (95 % instrument interval
[0.776, 0.932], 95 % sampling interval [0.70, 1.00]) at **+4.19 %/month** in-window — or
**+1.80 %/month** at the trade rate the accounts are actually firing — and the one survivor
tier that changes is `sub_mid_dn_revert`, which is armed on both accounts today and whose
corrected net expectancy at maximum carry is **−0.2446 R/trade with a 95 % interval entirely
below zero**.*

Ranked by what a decision would turn on:

1. **`sub_mid_dn_revert` is the only armed-money item this work moves.** Two independent
   populations agree it loses most of its edge to the quote-side repair. It fails the survivor
   predicate in 300 of 300 replicates on both accounts. **This belongs in front of Borhen
   before any further sizing decision.** It is not a recommendation to disarm — that is his
   call and it interacts with §1.5's point that removing sleeves is exactly the selection
   operation the whole book already rests on.
2. **The other three armed sleeves survive the correction with room to spare.** `crypto`
   −16.7 % gross but net@max still +0.58 [+0.24, +0.77]; `energy_agri` and
   `sub_xvol_pullback` move by ≤ 0.7 %. This is not luck — they are the low-`s/d` sleeves.
3. **Two published artifacts are stale and should stop being quoted as-is.**
   `SURVIVOR_BOOK_V1.json`'s tiers are wrong on both the cost axis and the instrument axis;
   `BOOKS_MC_V1.json`'s `p_pass 0.917167 / 0.9331` is not reproducible at HEAD (0.9340 /
   0.9534 on identical machinery).
4. **Every future `p_pass` must carry the sampling interval, not the seed noise.** ±0.0011 was
   never the uncertainty of anything the owner cares about.
5. **The honest survival band, floors included.** FTMO two-phase: driftless floor **0.2995**;
   at the live full-book −0.068 R/trade, **0.0892**; at the corrected in-window edge, median
   **0.9062** with a **joint 95 % band of [0.4736, 0.9953]** — and **[0.3719, 0.9838]** for
   the four-sleeve set the launcher actually runs. The lower edge of that band is the
   driftless floor. The spread across it is the whole open question of this programme, and it
   is a question about **selection, window and sample size**, not about the ruler.

---

## 6. WHAT THIS WORK DID NOT SETTLE

- **No re-walk was possible.** The deep H4 archive is absent; §3 is a structurally faithful
  transfer with published intervals, not a regeneration. Fetching
  `bridge_ftmo_deep_h4_2015_2022` and `..._2022_2026` would convert every interval in §3 into
  a point estimate, and it is the cheapest remaining upgrade to this answer.
- **`vp_euidx_pocgrav`'s correction is transferred from the pooled estate**, not from its own
  sleeve. Its tier change is the weakest claim here.
- **The `target → stop` migration rate is transferred at the sleeve level**, so it assumes the
  cache's trades and the archive's trades of the same sleeve share a migration propensity.
  The two populations differ in size on every sleeve (e.g. `idxrev` 6,473 vs 5,597).
- **The 1.84× edge factor is not decomposed further.** Whether it is era, symbol mix, or
  genuine in-sample selection is open, and it is now the *only* part of the 14.38× that
  carries an economic claim.
- **Nothing here re-prices the live book's realised P&L.** Lane F remains the only broker-true
  live record, and it is one trade since arming.

---

## 7. RECEIPTS

| file | what |
|---|---|
| `w7_restatement_receipts/w7_implied_edge.py` → `W7_IMPLIED_EDGE_V1.json` | §1 — implied edge, driftless floors, `p_pass` at every measured edge |
| `w7_restatement_receipts/w7_instrument_state.py` → `W7_INSTRUMENT_STATE_V1.json` | §2 — instrument proofs; §3.2 — restated books, 300 replicates |
| `w7_restatement_receipts/w7_survivor_tiers.py` → `W7_SURVIVOR_TIERS_V1.json` | §3.5 — survivor tiers three ways |
| `w7_restatement_receipts/w7_pass_intervals.py` → `W7_PASS_INTERVALS_V1.json` | §3.3 — moving-block bootstrap on `p_pass` |
| `w7_restatement_receipts/w7_ratio_and_frequency.py` → `W7_RATIO_AND_FREQUENCY_V1.json` | §4, §1.6 |
| `w7_restatement_receipts/w7_joint_interval.py` → `W7_JOINT_INTERVAL_V1.json` | §3.3b — joint instrument × sampling band |
| `w7_restatement_receipts/w7_per_sleeve.py` → `W7_PER_SLEEVE_V1.json` | §3.4 — per-sleeve gross and net@max with intervals |
| `w7_restatement_receipts/W7_FULLBOOK_VS_LIVE_V1.json` | §1.5 — full-book recost vs the live 142-trade record |

Inputs bound: `INTEG_W3_streams_cache.pkl`, `INTEG_W5_new_streams_cache.pkl`,
`W7_RECOST_V1.json`, `SURVIVOR_BOOK_V1.json`, `BOOKS_MC_V1.json`,
`phase20/receipts/r1/R1_ESTATE_ROWS_V1.json.gz` (22,354 rows),
`phase21/w7_recost/PRIOR_RECONCILIATION_V1.json`, `LANE_F_EMPIRICAL_R_V1.json`.
Machinery: `scripts/mc_firm_rules.py` and `scripts/recost_w7_validation.py`, imported
unchanged. No sealed route edited.
