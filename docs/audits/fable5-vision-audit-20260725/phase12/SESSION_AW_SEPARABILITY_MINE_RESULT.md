# Session AW — the separability mine (wave 12, B1750–B1799)

**The owner's challenge, answered with a measurement.** Borhen, 2026-07-30, on the parked B7.5
campaign: *"i dont think you ever checked the actual results and the intelligence there, you saw
it negative and instantly threw it away, maybe there was something wrong, maybe if with some
fixes it becomes positive, maybe if you run it more you can figure out what's wrong exactly."*

He was right that the question was open. `JANUARY_BANK.md` §3 says so in its own words — whether
the reference arm's 28,519-row diagnostic pool is separable by ANY rule is *"open and unmeasured
at any useful resolution."* This session measured it, for the first time, and the answer is
**no — and not because of cost.**

---

## 0. Findings first

1. **The reader exists and reproduces the seal exactly.** `src/research_infra/b7_5_diagnostic_pool.py`
   streams the four sealed January arms plus April's partial (≈32 GB of JSONL, 55 s) and
   recomputes every number the sealed matrix audit publishes — rows, diagnostic-scoreable rows,
   positive/negative counts, and **both net-R sums to 8 decimal places** — on all four arms.
   `all_arms_match_seal: true`. **`JANUARY_BANK.md` §7.5 is closed**: the arms did emit a
   readable ledger; what was missing was a reader.
2. **April is a real secondary holdout — 11,258 diagnostic rows over 9 trading days**, not the
   "31 scoreable rows" a careless reading of the bank suggests. §5 corrects that denominator.
3. **Zero of 212 declared cells separate the pool.** Not one cell, on any axis, at any cut, has
   a positive mean R on the training days. The best is **−0.1440 R/row** against a pool mean of
   **−1.0135**. The pool is negative on **21 of 21** January days, **8 of 8** holdout days and
   **9 of 9** April days.
4. **The axes are genuinely informative, and it does not help.** Train→holdout Spearman over cell
   means is **0.919**; train→April **0.903**. A fitted model reaches **AUC 0.712 on held-out days**
   and **0.669 on April**. The information is real and transferable; it is simply nowhere near
   enough. The pool needs **+0.947 R/row** to break even and the best conditioning delivers
   **+0.87** — consistently **0.15–0.25 R/row short**.
5. **It is not a cost problem, which is the part that answers the owner directly.** Mean **gross**
   R — before any cost is charged — is **−0.2199**. The pure 2R-target/1R-stop population hits
   **16.9 %** against a **33.3 %** break-even. Only **2 of 212** cells are gross-positive in
   train and **neither survives** to the holdout or to April. There is no directional edge for a
   cost repair to rescue.
6. **The costs the replay never charged make it worse, and one of them is a live defect.** F38 is
   confirmed present: `commission_r` is **identically 0.0 on all 28,519 rows**, while broker truth
   prices all 24 symbols (0 unpriced) at a mean of **0.0654 R/row**. With F31's gap-through and
   broker-true commission charged, the pool goes **−24,483.87 → −27,016.30 R** and the precision
   a selector must reach rises **63.92 % → 65.52 %**.
7. **What the mine DID find is a generator defect, and it reaches the estate.** `spread_r` is
   `spread_price / sl_distance_price`, so a cost above 1 R means **the proposed stop is narrower
   than the round-trip spread**. **4,701 rows (16.5 %) carry a cost above 1 R and 49.6 % of the
   pool's entire loss**; the maximum is **18.856 R**. The estate has the same disease: at band
   `mid`, **33.7 % of its 21,769 priced archive trades exceed the sealed B7.5 `spread_r ≤ 0.10`
   limit** and **52.9 % exceed the `total ≤ 0.15` limit**, with `asia_pdl_fade` reaching a
   **spread_r of 28.6**.
8. **Applying that sealed limit out of window moves real sleeves, passes its controls on two of
   them, and admits nothing.** `asia_pdl_fade` goes **−0.902 → +0.095 R/day** (+0.998), while
   dropping the *cheapest* trades instead takes it to **−2.728** (−1.825) and dropping the same
   count at random moves it **−0.041 ± 0.075**. On armed money `sub_mid_dn_revert` goes
   **+0.121 → +0.547** (p 0.163 → 0.023). **All four currently-armed sleeves improve.** But
   estate-wide the filter beats random on **10 of 23** sleeves against random's **11 of 26**, so
   it is **a per-sleeve repair, not an estate-wide rule**. Nothing admits: the closest is
   `sub_xvol_pullback` at **raw p 0.0020**, which would admit at a declared family of **≤ 50**
   — the estate's ratified family is **53** and this session's own bill is **486**.

**The honest one-line verdict.** The B7.5 broad-family pool is not separable by any of the 477
declared looks, a fitted model's ceiling on it is below break-even, and the reason is that the
mechanism family has no directional edge to rescue — not that its costs were mis-modelled. The
transferable value of the exercise is a **cost-geometry defect** that the estate shares and that
is worth a per-sleeve repair.

---

## 1. AW-1 — the reader, and the seal check that is its test

`src/research_infra/b7_5_diagnostic_pool.py` (new; **not** an R2-bound path — H1 membership
checked at start and end, 2 UNHYDRATED-LFS both times, no drift). It resolves each arm's
`*_MISSED_OPPORTUNITY_LEDGER.jsonl` through the route's own
`b7_5_cold_evidence.RawOrColdResolver`, which refuses ambiguous raw+cold representations and
verifies each zstd shard's hash as it inflates it. Nothing is copied; the ledgers are read where
they were written (H4).

| arm | ledger rows | diagnostic-scoreable | positive | negative | +R | −R | matches seal |
|---|---:|---:|---:|---:|---:|---:|:--:|
| S0R0 | 154,299 | 28,519 | 8,006 | 20,513 | +6,916.94750286 | −31,400.82177687 | ✅ |
| S1R0 | 154,312 | 28,530 | 8,012 | 20,518 | +6,922.59393961 | −31,405.38242771 | ✅ |
| S0R1 | 154,302 | 28,523 | 8,009 | 20,514 | +6,919.49514546 | −31,401.06791085 | ✅ |
| S1R1 | 154,316 | 28,535 | 8,016 | 20,519 | +6,926.18946999 | −31,405.59305302 | ✅ |
| APR_S1R1_PARTIAL | — | **11,258** | 2,846 | 8,412 | +2,658.50 | −11,445.66 | (no sealed comparand) |

**The seal comparison IS the test of the fast path.** The reader skips the 81.5 % of rows that
are not diagnostic-scoreable with a byte-level prefilter before parsing — a ~5× saving on 7.6 GB
per arm — and a prefilter that dropped a single row would move `diagnostic_scoreable_rows` off
the sealed value. It does not, on any of the four arms. 16 behavioural tests
(`tests/research_infra/test_b7_5_diagnostic_pool.py`) run on synthetic ledgers so they pass on a
machine that does not hold 32 GB of sealed evidence, including a test that the prefilter and a
full parse return the same rows in the same order.

**Features and outcomes are separated by construction.** `FEATURE_NAMES` carries no column
beginning `outcome_`, and identity columns are not offered as features either — a miner that
iterates `FEATURE_NAMES` cannot leak a label into a rule by accident. Pinned by test.

### 1.1 The bar, stated before the first look

`pool_summary()` returns it so it cannot drift:

| | raw | +F31 | +F31 +broker-true commission (`net_r_aw`) |
|---|---:|---:|---:|
| pool net R | −24,483.87 | −25,152.24 | **−27,016.30** |
| mean R/row | −0.8585 | −0.8819 | **−0.9473** |
| base rate (share positive) | 0.2807 | 0.2804 | **0.2652** |
| mean winner | +0.8640 | +0.8519 | +0.8375 |
| mean loser | −1.5308 | −1.5575 | −1.5913 |
| **break-even precision** | 0.6392 | 0.6464 | **0.6552** |

**The "±38,317 R of separable opportunity" framing overstates what is capturable.** A perfect
selector captures the +6,917 R, not the 38,317; and any real rule must reach **65.5 % precision
against a 26.5 % base rate** — a 2.47× lift — before it earns a single R. Every cell below is
judged against that number.

---

## 2. AW-0 — what was declared, before any outcome was read

`AW_MINE_PROTOCOL_V1.json`, sealed with `cells_sha256`; `--stage mine` refuses to run if that
hash has moved. `--stage declare` reads **feature distributions and the train split only**.

- **Split:** chronological. January's 21 trading days → **TRAIN = first 13** (01-02 … 01-20),
  **HOLDOUT = last 8** (01-21 … 01-30). Not random: a random split over one month puts the same
  regime on both sides.
- **Cuts:** categorical level-wise (≥ 200 train rows); numeric **train tertiles** (q33/q67 from
  TRAIN only). One cut rule per kind, fixed in advance — AO's pair admission died on an
  undeclared median cut and the wave-11 agreement makes the *cut rule* declarable, not just the
  axis.
- **Funnel:** F1 train mean > 0 → F2 holdout mean > 0 → F3 holdout day-positive ≥ 0.50 →
  F4 April mean > 0 → F5 positive on all three other January arms.
- **Inference:** unit is the trading day; exact day-blocked sign-flip permutation; the
  `1/2^n_days` resolution floor reported on every p.
- **Family:** `CANDIDATE_FAMILY_V7.json` adds `B7_5_SEPARABILITY_MINE_V1` (265 members / 243
  looks) and carries V6's three families forward byte-for-byte. It validates through
  `candidate_family.load_candidate_family` and every V6 family's `effective_size()` is unchanged.

**Two declaration rules worth stating because they cut both ways.**

*Aliases are one member, not three.* `origin_family`, `route_family` and `framework` label the
**same partition** of the 28,519 rows with different strings; eight more alias groups exist
(`cost_r`/`expected_cost_r`/`cost_over_rr`, `authority_session`/`kill_zone`,
`candidate_ev_r`/`expectancy_r`, …). Three rows would be three looks on the record and one look
in fact — the mirror image of the defect the ratchet closes. Detected by hashing the induced
partition, not the values, which is what catches the relabelled cases.

*Degenerate axes are declared and bill nothing.* **22** members carry `look_taken=false` with the
distinct-value count as evidence, the same rule `candidate_family.Member` applies to a zero-trade
sleeve. Two of them are findings in their own right:

- **`candidate_confidence` is 0.55 on every row and `confidence_default_applied` is True on every
  row.** The scheduler's missing-confidence default was applied to the entire window, so
  confidence carried **no information at all** in the campaign that was testing selection.
- **`commission_r` is 0.0 on every row** — F38, present and measurable (§4.1).

---

## 3. AW-2 — the mine

### 3.1 The funnel

| stage | cells |
|---|---:|
| DEGENERATE (no hypothesis testable) | 22 |
| **F1 — train mean R > 0** | **fails: 212** |
| F2 / F3 / F4 / F5 | 0 reached |
| **SURVIVORS** | **0** |

Every cell is measured on **every** split regardless of where it fails, so the funnel label names
the first gate a cell fails rather than the point where measurement stopped — the deliverable is
the map, and a map with holes where the answer was bad is a highlight reel.

**The best cells, ranked by train mean R** (pool baseline train **−1.0135**):

| cell | train n | train R | train prec | holdout R | April R |
|---|---:|---:|---:|---:|---:|
| `final_blocker_class==execution_fillability` | 232 | **−0.1440** | 0.591 | −0.1372 | −0.1609 |
| `risk_finalizer_reason==scheduler_option_status_not_executable…` | 1,198 | −0.1947 | 0.412 | −0.1972 | −0.2708 |
| `selector_reason==admission_quality_off_configured_session_entry_blocked` | 820 | −0.2007 | 0.441 | −0.3345 | −0.3270 |
| `miss_reason==scheduler_vetoed_candidate_package_fill_floor…` | 1,141 | −0.2040 | 0.419 | −0.2618 | −0.3355 |
| `symbol==XAUUSD` | 1,513 | −0.2064 | 0.492 | −0.1869 | −0.2954 |

The best cell lifts the mean by **+0.87 R/row** — 86 % of the way to zero — and still does not
get there. Its precision, **0.591**, is **2.2× the base rate** and still **below the 0.655 it
needs**. That shape recurs everywhere: **the pool's problem is payoff asymmetry, not hit rate.**

### 3.2 The information is real. That is the interesting part.

| axis family | cells | train→holdout Spearman | best train R | best holdout R |
|---|---:|---:|---:|---:|
| A_INSTRUMENT | 35 | 0.921 | −0.206 | −0.187 |
| B_TIME | 81 | 0.760 | −0.573 | −0.501 |
| C_COST | 17 | **0.975** | −0.251 | −0.342 |
| D_SCORE | 20 | 0.964 | −0.318 | −0.337 |
| E_SELECTOR | 49 | 0.737 | −0.144 | −0.128 |
| F_GEOMETRY | 5 | 1.000 | −0.475 | −0.498 |
| **all** | **208** | **0.919** (April 0.903) | | |

A rank correlation of 0.919 with **zero** cells above zero is the "real but insufficient"
diagnosis, and it has a different prescription from "absent": the axes work, the pool is too far
underwater for them to matter.

### 3.3 Interactions and the model ceiling

The declared top-8 TRAIN-ranked cells, crossed pairwise: **26 fail F1, 2 are disjoint, 0
survive.** One combination is positive on *both* splits —
`final_blocker_class==execution_fillability AND miss_reason==scheduler_vetoed…` at train
**+0.1849** / holdout **+0.0096** — on **n = 38**, below the declared 200-row floor. It is
reported because it is the only positive-on-both thing the session found, and it is not
evidence.

**The ceiling** (`AW_MODEL_CEILING_V1.json`, 247 features, declared in advance):

| model | AUC holdout | AUC April | holdout top decile | April top decile |
|---|---:|---:|---|---|
| L2 logistic | 0.705 | 0.669 | −0.167 R, prec 0.465 | −0.272 R, prec 0.332 |
| HGB depth 3 | **0.712** | 0.669 | −0.178 R, prec 0.490 | −0.256 R, prec 0.335 |
| **holdout-refit control** (fit ON the holdout) | 0.792 | 0.658 | **+0.162 R, prec 0.651** | −0.300 R, prec 0.315 |

The control is the strongest statement available: **a model allowed to see the answers barely
reaches break-even precision on its own data (0.651 vs 0.655), and none of it transfers.** No
selection rule over these features can be built that this ceiling does not bound.

---

## 4. The decomposition — why "some fixes" cannot make it positive

### 4.1 Where the −0.947 R/row goes

| term | R/row |
|---|---:|
| **gross (before any cost)** | **−0.2199** |
| replay spread | −0.5638 |
| replay slippage (flat 0.02) | −0.0200 |
| replay swap | −0.0548 |
| F31 gap-through, level exits | −0.0234 |
| broker-true commission (F38, never charged) | −0.0654 |
| **net (`net_r_aw`)** | **−0.9473** |

The gross line is the answer. **Before a single unit of cost, the pool loses 0.22 R/row.** The
pure binary population — 15,678 stops at −1 R and 3,185 targets at +2 R — hits **16.885 %**
against a **33.3 %** break-even. That is not a cost model that needs repairing; it is a
mechanism family that is wrong about direction by roughly a factor of two.

Charging F38 is a real correction, not an accounting flourish: broker truth prices **all 24
symbols with 0 unpriced**, and it is heterogeneous exactly as Session N found — `US500.cash`,
`GER40.cash`, `US30.cash`, `JP225.cash`, `UK100.cash`, `USOIL.cash`, `UKOIL.cash` are MEASURED
zeros; `XAUUSD`, `BTCUSD`, `ETHUSD`, `USDCAD`, `XAGUSD` are notional-bp; the FX majors are
per-lot. A flat constant would have been wrong in both directions.

### 4.2 The pre-cost view, billed honestly

Asking "does this cell have directional edge before cost" is a **second hypothesis about the same
rows**, so `CANDIDATE_FAMILY_V8.json` re-declares all 212 with a `history` entry and the bill
rises **265 → 477**. Rewriting the sealed V7 would have been the dishonest option: the net looks
were taken and cannot be un-taken.

**2 of 212 cells are gross-positive on TRAIN. Neither survives.**

| cell | train gross | holdout gross | April gross |
|---|---:|---:|---:|
| `effective_admission_count::T3` (n = 11) | +0.8535 | −0.6033 | −1.0000 |
| `symbol==GER40` (n = 940) | +0.0270 | −0.0380 | −0.3600 |

The cost-executable third of the pool — the 8,760 rows the incumbent's own cost gate would have
passed, at a mean cost of 0.079 R — is **still gross-negative at −0.163** and nets **−0.299**.
**The clean, cheap subset loses money too.**

### 4.3 The cost tail is a generator defect

`spread_r = spread_price / sl_distance_price`. A value above 1 means the proposed stop is
narrower than the round-trip spread.

| | value |
|---|---:|
| rows with cost > 1 R | 4,701 (16.5 %) |
| rows with cost > 2 R | 2,101 |
| rows with cost > 5 R | 352 |
| max cost | **18.856 R** |
| share of the pool's total loss carried by cost > 1 R rows | **49.6 %** |

This is the one finding that transfers, and §5 takes it out of window.

---

## 5. AW-3 — out of window, on the fast machinery

**AW-2 produced no survivor, so the commission's literal input to AW-3 is empty, and this session
says so rather than manufacturing one.** What it ran instead is the mine's largest measured term
— the cost-to-stop ratio — at thresholds taken from the **sealed** B7.5 decision contract, which
the January ledger prints verbatim in its own block reason:

```
broker_cost_packet_refused:spread_r_exceeds_selected_cell_limit:0.162063>0.100000
                          |total_cost_r_exceeds_limit:0.182063>0.150000
```

**spread_r ≤ 0.10, total cost_r ≤ 0.15.** Pre-registered 2026-07-16, not fitted here. The *axis*
was chosen after 477 looks, so the bill carries all of them (`CANDIDATE_FAMILY_V9`, **486** with
AW-3's own nine arms).

### 5.1 The census needs no gate, and it is about the live book

22,354 archive trades over 29 sleeves (`AQ_ESTATE_TRADES_V2`), priced by the gate's own cost
layer at `BROKER_TRUE_COSTS_V1_1`:

| band | over `spread_r ≤ 0.10` | over `total ≤ 0.15` |
|---|---:|---:|
| flat 37-day snapshot | 24.3 % | 45.9 % |
| low | 30.7 % | 50.6 % |
| **mid** | **33.7 %** | **52.9 %** |
| high | 37.8 % | 55.2 % |

Per sleeve at `mid`, the extremes: `vss_fxcross_london_up_low` 98.3 %, `liq_asia_up_low_metal`
91.7 %, `mx_nzdjpy_d1_donchian_20_breakout` 82.1 %, **`asia_pdl_fade` 73.0 % with a maximum
`spread_r` of 28.6**. The armed four: `sub_mid_dn_revert` **46.9 %**, `crypto` 11.1 %,
`sub_xvol_pullback` 7.7 %, `energy_agri` 3.8 %. (`fx_jpy` was 44.3 % and was pulled from both
books at ~14:57 UTC on AV's own evidence — `phase8/receipts/FXJPY_PULL_20260730.md`. This
session did not cause that pull and its filter arm makes `fx_jpy` *worse*, which is a fact about
the pulled sleeve worth keeping visible.)

### 5.2 The gate, with the controls that make it a measurement

A cost filter **mechanically** raises post-cost mean R by removing expensive trades, so the arm
is worthless without controls. Two were declared: `inverse_cheapest_matched` drops the same
count but the **cheapest**; five `random_matched` seeds drop the same count at **random**. Every
arm is judged at the same sample size. Band `mid`, Δ = arm − control, in pooled OOS R/day:

| sleeve | control | Δ spread filter | Δ inverse (cheapest) | Δ random (mean ± sd) |
|---|---:|---:|---:|---:|
| `asia_pdl_fade` | −0.9024 | **+0.9977** | **−1.8251** | −0.0413 ± 0.0749 |
| `sub_mid_dn_revert` ★ | +0.1206 | **+0.4260** | −0.0601 | +0.0641 ± 0.0655 |
| `sub_xvol_pullback` ★ | +1.0215 | +0.2644 | −0.0792 | +0.1359 ± 0.0753 |
| `energy_agri` ★ | +0.4065 | +0.2118 | −0.0000 | +0.0158 ± 0.0323 |
| `metals_core` | −0.2077 | +0.1141 | −0.0169 | +0.0214 ± 0.0278 |
| `crypto` ★ | +0.2611 | +0.0664 | +0.0318 | −0.0504 ± 0.0340 |
| `mx_btcusd_d1_donchian_20_breakout` | +0.3894 | **+0.0000** | +0.0000 | +0.0013 ± 0.0105 |
| `metals_softband` | +0.0902 | −0.1755 | −0.0607 | +0.0330 ± 0.0692 |
| `fx_jpy` (pulled) | −0.2140 | −0.1721 | +0.0322 | −0.0113 ± 0.0273 |

★ = currently armed.

**What passes its controls.** `asia_pdl_fade` is unambiguous: dropping the dearest trades is
worth +1.00 R/day and dropping the cheapest costs −1.83 R/day at the identical sample size, with
random at −0.04. That sign flip is the evidence that the cost axis carries information about the
**trade**, not just about the bill. `sub_mid_dn_revert` is the same shape on armed money
(+0.426 against a random +0.064 ± 0.066, and inverse negative).

**What does not.** `sub_xvol_pullback`'s +0.264 sits only ~1.7 sd above a random control that
itself improves by +0.136 — on n = 79. `energy_agri`'s +0.212 comes from dropping **2 trades of
64**. Both are suggestive and neither is established.

**Estate-wide the rule is not an improvement.** Median Δ is **0.0000** for the filter, the
inverse and random alike; the filter improves **10 of 23** evaluable sleeves against random's
**11 of 26**. It is a per-sleeve repair, and treating it as a blanket policy would be exactly the
error AR's session named.

### 5.3 Nothing admits, and the near-miss has a number

**0 ADMIT** across all 12 hypothesis runs and all 24 control runs.

- `sub_xvol_pullback` + the spread filter: **raw p 0.0020** (mid and high), pooled **+1.286 R/day**
  on 79 trades, q **0.9719** at family 486. `max_size_that_admits(0.0020, α=0.10) = 50`; the
  estate's ratified `CANDIDATE_BOOK_V1` is **53**. **It misses at every defensible bill**, by 3
  members at the most generous and by an order of magnitude at its own.
- `asia_pdl_fade`: the filter does not admit it (p 0.169 at mid, 0.091 at high) but it **changes
  the failure mode**. Control rejects on `expectancy (per trade)` and `lifetime` — the sleeve
  loses money. Filtered, it rejects on `stability` and `robustness` — it makes money in one fold
  of five. That is a different sleeve and a different repair queue entry.
- **The estate's one standing admission is untouched.** `mx_btcusd @ target_5R` sees exactly
  2 of 232 trades dropped at `mid` and its p is bit-identical at 0.006399. Whatever is decided
  about this filter, it does not disturb the admission.

---

## 6. What I got wrong

1. **I nearly declared April's ledgers absent.** My first `find` over `/Users/borr/GTOSActive`
   returned nothing and I read that as "the April partial's outputs do not exist on this
   machine". It was a **`timeout` that expired silently** — the exit code I printed belonged to
   the `head` at the end of the pipe, not to `find`. The ledgers were there all along, under
   `attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_20260725T070249Z/`, and finding them turned a
   single-window mine into one with an out-of-month holdout. **Never read an exit code through a
   pipe.**
2. **I misread the bank's April coverage figure, and the correction matters.** `JANUARY_BANK.md`
   §5.1's *"25.8 % (8 of 31 scoreable rows)"* is the **level-exit price coverage for the F31
   gap-through measurement**. It is not the size of April's diagnostic pool, which is **11,258
   rows**. The two denominators differ by 363×, and reading the smaller one as "April has 31
   rows" would have discarded a usable holdout. The bank's sentence is correct; it is easy to
   carry wrongly, so it is corrected here explicitly.
3. **My first funnel measured only as far as the first failed gate**, so cells that failed F1 had
   no holdout or April number at all. With zero survivors that would have produced a result doc
   saying "nothing passed" and nothing else — a highlight reel of an empty set. Rewritten to
   measure every split for every cell; the persistence finding (§3.2) exists only because of
   that rewrite, and it is the most interesting thing in the mine.
4. **My interaction stage ranked among F1 passers, which the protocol did not say.** The sealed
   declaration says the occupant of each interaction slot "is decided by TRAIN order alone". With
   F1 empty, my code would have silently spent zero of the 28 declared interaction looks and
   reported nothing — a declared budget quietly unspent reads exactly like a budget that found
   nothing. Fixed to match the declaration rather than amending the declaration to match the
   code.
5. **`describe()` returned a short dict for empty cells** and the first full-map run died on a
   `KeyError` at the rarest input. Every key is now always present with `None` where undefined.
6. **I initially charged the F31 constant and stopped there.** The commission says "F31
   gap-through *and* broker-true costs", and the census then showed `commission_r` is identically
   zero across the window — so the second half was not a formality, it was 0.0654 R/row and 6.9 %
   of the pool's loss. Charging only F31 would have understated the answer.

---

## 7. Handoff

1. **`asia_pdl_fade` has a named, controlled repair and is not armed.** −0.902 → +0.095 R/day at
   `mid` (+0.167 at `high`) when trades with `spread_r > 0.10` are excluded, with the inverse
   control at −1.825. It still fails `stability` and `robustness` (one fold of five carries it),
   so the next question is whether the surviving 532 trades are a regime or an edge. Repair row
   appended.
2. **`sub_mid_dn_revert` is ARMED and 46.9 % of its archive trades exceed the sealed spread
   limit.** The filter takes it +0.121 → +0.547 R/day (p 0.163 → 0.023) and passes its controls.
   This is a live-book question, not a research one, and it belongs in front of Borhen alongside
   the other sizing decisions. **It is not an admission** and nothing here arms or disarms
   anything.
3. **The B7.5 pool's repair paths are now enumerated, and they are thin.** What would be needed
   to go further, stated as data requirements rather than as hope: (a) a feature the ledgers do
   **not** carry — every predecision field they do carry has been screened; (b) a mechanism
   family other than the ten `origin_family` values, since all ten are gross-negative; (c) a
   different exit geometry, since the 2R/1R binary hits 16.9 % against a 33.3 % break-even. None
   of the three is reachable by re-reading January, April or March.
4. **The sealed-window confirmation is a PRICED option and this session did not pay it**, per
   `JANUARY_BANK.md` §7.1/§7.2: reading another window's outcomes requires the pooled
   promote/reject/inconclusive evaluator **and** its pooling weights to be written and sealed
   FIRST — neither exists in any Python in the tree. The price is ~36 machine-hours serial
   (April 16.5 + May ~2.7 + March 16.5), +16.5 MH to re-run January if any bound file is edited,
   and promotion needs pooled *q* > +0.1 from −0.152268451308. **This session's measurement makes
   that option cheaper to decline**: the pool has no gross edge, so no window can find one.
5. **March was not read, not featured, not split.** No sealed window was run. Nothing under
   `src/` that the R2 contract binds was touched; the drift count is 2 UNHYDRATED-LFS at start
   and at end.
6. **The family ratchet grew 265 → 477 → 486 inside one session and every step is documented in
   `history`.** A reader who wants the cheaper bill can ask for `basis=LOOKS_TAKEN` (464); a
   reader who wants to know what a rule from this session costs should use 486.
7. **`research/operations/broker_truth_layer_2026_07_29/` was added to this worktree's sparse
   checkout** so `BROKER_TRUE_COSTS_V1_1.json` resolves. No tracked content changed; the
   orchestrator may want that path in the default cone, since three wave-8/12 receipts already
   reference it by absolute path.
8. **The block-citation guard needed a parser repair and it is the third of its kind.** Writing
   B1750–B1785 raised the ceiling past B1670 and `WAVE_11_WORKING_AGREEMENT.md`'s citation of
   B1670 fell out of the forward-allocation exemption — but the block **is** written: AV's
   `**B1668–B1670 — receipts.**` is one paragraph covering a run of three ids, and the parser
   saw only the first. Repaired the same way this file records two earlier times ("teach the
   parser the shape rather than rewrite the prose"), restricted to **bold, tightly-set** ranges
   so section headings like `## B1750–B1799` cannot define fifty blocks nobody wrote, and pinned
   by a new test that asserts the three near-miss shapes expand to nothing. AW's own in-flight
   range was retired by its own author, per §4's ownership rule. **B1669, B1670, B1784 and
   B1785 were written and invisible; they are visible now.**

---

## 8. Artifacts

| path | what |
|---|---|
| `src/research_infra/b7_5_diagnostic_pool.py` | the reader — closes `JANUARY_BANK.md` §7.5 |
| `tests/research_infra/test_b7_5_diagnostic_pool.py` | 16 behavioural tests, synthetic ledgers |
| `phase12/receipts/aw_separability_mine.py` | census → declare → mine → gross → model |
| `phase12/receipts/aw_archive_gate.py` | AW-3 census + gate with controls |
| `phase12/receipts/AW_FEATURE_CENSUS_V1.json` | 75 axes, alias groups, degeneracy, the charge model |
| `phase12/receipts/AW_MINE_PROTOCOL_V1.json` | the sealed declaration (234 cells, `cells_sha256`) |
| `phase12/receipts/AW_SEPARABILITY_MAP_V1.json` | every cell on every split — the map |
| `phase12/receipts/AW_GROSS_VIEW_V1.json` | the pre-cost decomposition |
| `phase12/receipts/AW_MODEL_CEILING_V1.json` | the fitted ceiling and its in-sample control |
| `phase12/receipts/AW_ESTATE_COST_CENSUS_V1.json` | 22,354 estate trades vs the sealed limits |
| `phase12/receipts/AW_ARCHIVE_GATE_V1.json` | 36 gate runs: 3 hypothesis arms + 6 controls × 4 bands |
| `phase12/receipts/CANDIDATE_FAMILY_V{7,8,9}.json` | the ratchet, three declared steps |
| `phase12/receipts/SESSION_AW_AB.md` | the scoped A/B |

The built pool (`.aw_diagnostic_pool_v1.jsonl.gz`, 34 MB) is **not committed**: it rebuilds in
55 s from the sealed ledgers, which are machine-bound anyway (H4), and the repo does not need
another 34 MB inline blob (CLAUDE.md §8).
