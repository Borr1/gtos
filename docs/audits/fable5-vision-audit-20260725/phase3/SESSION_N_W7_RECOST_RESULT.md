# Session N — the W7 validation, re-costed at broker truth

**Stage 1.2. Branch `phase3/w7-recost` off `phase3/broker-truth` @ `7e36ac9dc`. Blocks B150–B164.**

Reproduce: `python3 scripts/recost_w7_validation.py && python3 scripts/build_survivor_book.py`
Artifacts: `research/operations/w7_recost_2026_07_27/{W7_RECOST_V1.json,SURVIVOR_BOOK_V1.json,SURVIVOR_BOOK_V1.md}`
Tests: `pytest tests/test_w7_recost.py -q` → **21 passed**. Full-suite A/B: `ab/SESSION_N_AB.md`.

---

## 0. The answer

**The W7 book survives contact with what trading actually costs. It is not a kill — but it is not
the result the third review predicted either, and the reason matters more than the verdict.**

`THIRD_REVIEW.md` §1.2 expected a positive validation contaminated by a missing commission charge,
repairable by adding commission back. Measured on the validation's own 8,503 trades:

- **Commission at the validation's own stop geometry is small.** Exactly **0.0000 R** on the index
  sleeve, **0.0019–0.0040 R** on metals, **0.014–0.022 R** on crypto. It is material only on the two
  JPY sleeves (**0.096–0.114 R**), which carry `conf 0.15` each.
- **The legacy cost map got the *direction* wrong as often as the magnitude.** It charged a flat
  per-class R against every trade regardless of stop distance. Against broker truth it **over-charged
  7 of the 11 sleeves** — crypto by 2.6×, `vp_euidx_pocgrav` by 2.4×, `sub_mid_dn_revert` by 2.1×,
  `sub_xvol_pullback` by 2.2×, `idxrev` by 1.9× — and **under-charged 4**: `fx_jpy` 2.10×,
  `fx_jpy_ny` 1.94×, `metals_core` 1.42×, `energy_agri` 1.23×.
- Net on the book of record, FTMO, one night of average carry, same composition as the published
  final: **daily mean 0.10956 → 0.09604, −12.3 %**. Like-for-like against the same book *without* the
  F39 erosion credit, the re-cost alone accounts for **−9.7 %**; the rest is removal of the credit.

**What actually threatens the book is carry, not commission.** Swap is the largest single broker cost
for eight of the eleven sleeves, and no exit index survives in any cache — so for eight sleeves
holding time is still an upper bound rather than a measurement. It is **not** unmeasurable, as an
earlier version of this document claimed: the live W7 window measured three of the eleven directly
(§8.1). Each sleeve is asked how long its average trade can run before carry consumes its edge — a
hold in hours, against the longest hold its own exit horizon permits — and answered with a measurement
where one exists. That sorts the book into five tiers:

| tier | FTMO |
|---|---|
| **UNCONDITIONAL** — no reachable hold takes the edge to zero | `metals_core`, `crypto`, `energy_agri`, `sub_xvol_pullback` |
| **MEASURED LIVE CARRY** — the live window measured it *and* a structural bound backs the measurement | `fx_jpy` |
| **CARRY-CONDITIONAL, live-supported** — nine live positions on the surviving side, but no structural bound | `fx_jpy_ny` |
| **CARRY-CONDITIONAL** — survives iff the mean hold is under its break-even; **not measured** | `metals_softband` (198 h of a 320 h max), `vp_euidx_pocgrav` (251 h), `sub_mid_dn_revert` (269 h) |
| **DEAD BEFORE COST** — negative gross of every broker cost | `metals_ob_micro`, `idxrev` |

**No sleeve is killed by commission.** Two were already negative before the validation charged
anything. Of the other nine, one is settled by a structural bound plus 32 live positions, one has nine
live positions on the surviving side, four are safe at any reachable hold, and **three remain
genuinely open** — all on the same unmeasured number.

---

## 1. What licenses these numbers

Before anything else: **charge every row exactly what the validation charged, rebuild the book, and it
reproduces the published result to five decimals.**

| | rebuilt here | `INTEG_W7_FINAL_RESULT.json` |
|---|---|---|
| daily mean, `base` variant | **0.09127** | 0.09127 |
| daily std, `base` variant | **0.59970** | 0.5997 |
| `n_days` | **1679** | 1679 |
| `sd_book` | **0.56859** | 0.56859 |

That is the machinery's null control (`tests/test_w7_recost.py::test_pipeline_reproduces_published_base_variant`).
The 11-column matrix, the confidence weights, the day-mean pooling, the clean_3 fold, the Kelly
handset and the vol-matching are reconstructed correctly, and the MC engine is the route's own
`INTEG_portfolio_build_w2.mc_series`, imported rather than reimplemented.

**But be precise about what it licenses, because an earlier draft of this document overstated it.**
The parity path runs on `R_legacy = R` and never reads `charged_cost_r`, `R_gross`, `sl_price`,
`entry_price` or any `cost_*` field. It is structurally blind to the cost recovery — and it matched to
five decimals while `metals_core`'s charged cost was wrong by 2× (§9.1). **Parity licenses the
day-matrix and the MC. It licenses nothing in the cost path.** Two controls do that job instead:
`test_every_clean_stopout_grosses_to_exactly_minus_one` (a clean stop is −1.0 R before cost by
construction, whatever it was charged) and `test_perturbing_the_charged_cost_moves_the_restated_book`.

**The restatement itself is arithmetic, not a re-backtest.** `geometry_lib.simulate` subtracts a
scalar cost in R at the end of every trade (`:36,38,43,44,53,55,60,61`), so
`R_cached = wins(R_geometric − charged_cost)`. The winsor is **inert on this book** — the extreme
cached values are −1.1601 and +4.8111, both strictly inside `[-1.3, +5]` — therefore
`R_gross = R_cached + charged_cost` **exactly, for every row**.

`charged_cost` is recovered three ways on all **102** (sleeve, symbol) pairs: from source (the class
map through `w1.cost_for`, divided by the sleeve's `stop_atr`), from `D4_COMBINED_TRADE_LEDGER.jsonl`'s
own `resim.cost`, and **from the data** — a full stop-out books exactly `−(1 + charged_cost)`, so
`idxrev` stop-outs sit at −1.042533 (= −1 − 0.0638/1.5) and `fx_jpy` at −1.1148.

**Only the third witness is independent, and it is the one that matters.** A and B both read the same
flat class map, and D4's metals rows are a re-simulation the session brief warns diverges by 0.60 R.
**90 of 102 pairs are charged a flat cost; 12 are charged per trade** —
`INTEG_portfolio_build_w3.py:89` scales `metals_core` by `0.5 × ATR14(H4) / sd_h4`, and the energy
cascade does the same at `EXEC_exit_variants.py:45`. Those 12 are detected from the *dispersion* of
their own stop-out rows, priced exactly on the 106 rows that are clean stops, and banded elsewhere
(`W7_RECOST_V1.json:variable_charge_pairs`). Zero pairs disagree.

---

## 2. Three of the six "known answers" in my prompt are wrong, and they fail the same way

The prompt supplied six checks from `GATE_G1B_RECEIPT.md` §5.2a with the instruction that a
disagreement must be resolved before publishing. Three do not survive.

**The common error is the one B112 named:** applying a per-symbol R value measured on the *live*
fills as if it were a *rate*. `BROKER_TRUE_COSTS_V1.json`'s own `conventions` block says it outright —
*"The receipt's per-symbol R values are window-specific and are NOT rates."* Commission in R is
`usd_per_lot / (sl_distance_price × usd_per_price_unit_per_lot)`, so it scales inversely with stop
distance, and the validation's stops are not the live book's.

| prompt's known answer | verdict | measured on the validation's own rows |
|---|---|---|
| Commission zero on the six measured index CFDs | **confirmed** | 0.0000 R on all 4,939 priced `idxrev` rows, both accounts |
| Near-zero on XAU/XAG (0.0054 / 0.0013 R) | **confirmed in kind** | 0.0024 / 0.0006 R — *smaller*, because the validation's metals stops are wider than the live scalp stops |
| 0.09–0.20 R on the measured FX/JPY legs and BTC | **half confirmed** | FX/JPY 0.086–0.114 R ✓. BTC **0.023 R**, not 0.11–0.14 |
| **"Commission alone kills USDJPY on the validation's own rows: +0.116 gross − 0.195 → negative"** | **refuted** | see below |
| "It dents but does not kill GBPJPY: +0.219 gross − 0.093" | right conclusion, wrong basis | see below |
| **"BTC takes a ~13 % haircut"** | **refuted** | BTC gets **cheaper**: cached +1.0887 → cost-true **+1.1473**, a **+5.4 %** improvement |

### 2.1 USDJPY is not killed by commission

Two errors compound in that claim.

**First, +0.116 is not gross.** `fx_jpy · USDJPY` measures **gross +0.2307**, charged 0.1148, **cached
net +0.1159**. The prompt's "+0.116" *is* the cached net — the number that has already had 0.1148 of
cost taken out of it. Subtracting commission from it charges cost twice. (The same holds for GBPJPY:
the prompt's "+0.219" is exactly this session's cached net **+0.2192**.)

**Second, 0.195 is a live-window value.** The validation's `fx_jpy · USDJPY` stop has median
**0.0806** against the live fills' **0.043** — 1.9× wider — so commission is **0.1140 R**, not 0.195.

Correctly: `+0.2307 gross − 0.1140 commission = +0.1167`. **Commission alone leaves USDJPY
comfortably positive.** Full cost ex-swap: **+0.0451** on FTMO, **+0.0015** on redacted_account.

USDJPY does die — but on **carry**, not commission. `fx_jpy`'s break-even is **0.44 nights** on FTMO
and **0.10 nights** on redacted_account, because redacted_account charges swap on *both* legs of USDJPY
(`swap_long −19.59`, `swap_short −40.76` points) where FTMO pays the long leg (`+1.85`).

### 2.2 What the sixth answer got right

"Commission is unmeasured for energy/agri, DASHUSD, the four metal crosses, and ~24 % of `idxrev`'s
index universe" — **confirmed.** The transferred `idxrev` rows are EU50 (937) + FRA40 (331) +
US2000 (266) = **1,534 of 6,473 = 23.70 %**, and the artifact's own
`accounts.FTMO.sleeves.idxrev.coverage` reports `{MEASURED: 4939, TRANSFERRED: 1534}` independently.

*(An earlier draft gave 1,563 / 24.15 % using each symbol's **book-wide** row count against an
`idxrev`-only denominator — two different populations. The conclusion held; the derivation did not.)*

---

## 3. Per-sleeve economics — FTMO, at the 2.00 % live dial

`cost_multiple` is true cost ÷ what the validation charged; below 1.00 means the validation
**over**-charged. `metals_core` and `energy_agri` were charged **per trade** by their generators, so
their `charged` column is the measured per-row mean, not a class constant.

| sleeve | conf | n | gross R | charged | broker truth | ×mult | swap/night | net @0 | break-even hold | max hold | carry basis | tier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sub_xvol_pullback` | 0.45 | 90 | 1.3070 | 0.0692 | 0.0317 | 0.46 | 0.0099 | 1.2752 | *never reached* | 320 h | horizon (modelled) | **UNCOND** |
| `crypto` | 0.85 | 104 | 1.2121 | 0.0953 | 0.0367 | 0.39 | 0.0289 | 1.1753 | *never reached* (975 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `metals_core` | 1.0 | 131 | 0.9103 | 0.0232 | 0.0329 | 1.42 | 0.0431 | 0.8774 | *never reached* (489 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `energy_agri` | 0.8 | 162 | 0.5386 | 0.0580 | 0.0712 | 1.23 | 0.0081 | 0.4675 | *never reached* (1383 h > 320 h max) | 320 h | horizon (modelled) | **UNCOND** |
| `fx_jpy` | 0.15 | 530 | 0.2823 | 0.1148 | 0.2411 | 2.1 | 0.1301 | 0.0412 | *never reached* | 12 h | live 0 · structural | **MEASURED** |
| `fx_jpy_ny` | 0.15 | 197 | 0.2690 | 0.1148 | 0.2227 | 1.94 | 0.1304 | 0.0462 | **9 h** (75 % of max) | 12 h | live 0 · zero swap | cond. *(9 live obs)* |
| `metals_softband` | 0.5 | 70 | 0.3780 | 0.0459 | 0.0441 | 0.96 | 0.0405 | 0.3339 | **198 h** (62 % of max) | 320 h | horizon (modelled) | **cond.** |
| `vp_euidx_pocgrav` | 0.3 | 341 | 0.2982 | 0.0638 | 0.0265 | 0.41 | 0.0260 | 0.2717 | **251 h** (78 % of max) | 320 h | horizon (modelled) | **cond.** |
| `sub_mid_dn_revert` | 0.2 | 398 | 0.3166 | 0.0969 | 0.0456 | 0.47 | 0.0242 | 0.2710 | **269 h** (84 % of max) | 320 h | horizon (modelled) | **cond.** |
| `idxrev` | 0.15 | 6473 | 0.0059 | 0.0425 | 0.0221 | 0.52 | 0.0137 | -0.0162 | — | 240 h | live mean hold | dead before cost |
| `metals_ob_micro` | 0.3 | 7 | -0.5000 | 0.0459 | 0.0349 | 0.76 | 0.0200 | -0.5349 | — | 320 h | horizon (modelled) | dead before cost |

#### live carry evidence
| sleeve | live positions | paid swap | median hold | max hold | horizon | % of horizon used | nights charged |
|---|---:|---:|---:|---:|---:|---:|---:|
| `fx_jpy` | 32 | **0** (0.0 %) | 0.51 h | 7.36 h | 12 h | 4.2 % | **0.0** |
| `fx_jpy_ny` | 9 | **0** (0.0 %) | 0.71 h | 1.26 h | 12 h | 5.9 % | **0.0** |
| `idxrev` | 59 | **39** (66.1 %) | 15.02 h | 89.99 h | 240 h | 6.3 % | **0.923** |

The percentage after each break-even is the fraction of the sleeve's own maximum hold the *average*
trade would have to run before the sleeve turns negative. None is comfortable, and none is measured.

**Night ceilings are measured, not assumed.** `SLEEVE_MAX_NIGHTS` is computed by sweeping
`rollover_nights` over all 168 (weekday × hour) entry instants for each sleeve's horizon: a 320 h hold
charges a mean of **13.37** nights (max 14), 240 h charges 10.04 (max 13), and a 12 h hold charges
0.51 (**max 3** — a Wednesday-midnight crossing is a triple). See §9.2 for the version of this that
was wrong.

---

## 4. The placebo says the re-cost did not decide the sleeve set

Per `WAVE_3_WORKING_AGREEMENT` §3.1, the improvement claim carries its null control in the same
receipt. The control permutes the per-symbol true-cost vector across symbols — preserving the cost
distribution exactly, destroying only its assignment to instruments — 1,000 times.

**Result: `cost_truth_decided = False` for all 11 sleeves, on both accounts.** Every sleeve's
ex-swap survive/die verdict is a **gross-edge** fact: survival rate is 1.000 for the nine positive
sleeves and 0.000 for the two negative ones, regardless of which symbol carries which cost. Ex-swap
costs (0.02–0.25 R) are one to two orders of magnitude below the gross edges they are subtracted from.

Read plainly: **at the ex-swap level, re-costing changed no sleeve's sign.** The thing that changes
signs is carry — which the placebo cannot test, because carry is the term with no measurement.

---

## 5. F39 is sharper than "which reading was intended"

The prompt asked for both readings of what `ULTIMATE_REAL_COST_MAP.json` contained, published as a
band, on the grounds that the record cannot settle it. It cannot — the map enters as a **ten-line
JSON-only commit with no generator, 59 readers and zero producers** (confirmed; note the commit
`450a275f8` cited in `src/costs/model.py:528` and in `BROKER_TRUE_COSTS_V1.json` **does not exist in
this repository** — it resolves only in the legacy clone `~/Documents/gtos/repo/ai-trading-agent`).

But **that ambiguity is not what F39 is**, and it does not reach this restatement.

**It does not reach the restatement** because whatever the map's 0.0459 *meant*, 0.0459 is what was
subtracted, so adding it back recovers the geometric R either way. The restatement is invariant to the
reading; both are published in `W7_RECOST_V1.json:f39_band` for attribution only.

**What F39 actually is: a gross/net key-selection error on one line.** `KB7_tick_mc.py:38` computes
the erosion as `tick_real − modeled`. `modeled` is net of the cost map; `tick_real` is net of
**nothing**, because `COMMISSION_R` is hardcoded identically zero (`KB7_tick_truth.py:64`,
`KB7_tick_crypto.py:46`, `KB7_tick_jpy.py:107-108`). The difference therefore contains the entire cost
map, added back — measured from the ledgers at **+0.1144 R for USDJPY against a map value of 0.1148**.
`KB7_tick_mc.py:66` then adds that to a row that had already paid the cost.

The correct comparator, `tick_costmap − modeled`, is computed on the adjacent line in every producer,
is designated "the like-for-like execution erosion" by `KB7_tick_truth.py:28`, and is published
per-symbol in `KB7_TICK_TRUTH_RESULT.json`. It was simply not the key selected. Three symbols change
sign under it: USDJPY (−0.0964 → +0.0179), XAUUSD (−0.0026 → +0.0190), USOIL (+0.0195 → +0.0370). The
positive credits were then fanned across **five further sleeve columns that were never tick-measured**
(`INTEG_W7_final_book.py:95-107`). The defect is duplicated independently at
`KB7_tick_book_restate.py:41,62`.

So F39 has a correct answer, not a band. **This restatement charges neither the map nor the erosion —
it charges measured broker truth — so it is clear of both.**

---

## 6. Calendar-day restatement — the headline overstates by 1.71×

`INTEG_W7_final_book.grid` computes `monthly_pct = mean_per_book_day × risk × 21`. That is right only
if the book fires on ~21 days a calendar month. It does not.

| | book-days | weekday sessions | density | book-days / calendar month | overstatement |
|---|---:|---:|---:|---:|---:|
| full window 2015-02-25 → 2026-06-12 | 1,679 | 2,948 | **57.0 %** | **12.26** | **1.71×** |
| forward window 2025-01-02 → 2026-06-12 | 382 | 377 | **101.3 %** | 21.22 | 0.99× |

The 1,679 rows are days on which the book fired *at all*, and the early years are nearly empty — 8
book-days in 2015, 14 in 2016, against 263 in 2025. So the published **3.453 %/month** at the 2.00 %
dial reads as **≈2.0 %/month** on the full-window basis, or stays at ≈3.4 % if you assume the forward
window's density persists. Median days-to-pass moves the same way: 49 book-days is **88 calendar days**
at full-window density, **49** at forward density.

Both bases are published. Neither is called "the" number — the choice is an assumption about which
regime continues, and that is a judgement, not a measurement.

I checked whether the forward window's density is an artefact of the two dying JPY sleeves. **It is
not:** only **5 of 382** forward book-days (1.3 %) are carried by `fx_jpy`/`fx_jpy_ny` alone.

---

## 7. A defect in the cost layer this session depends on

`scripts/build_broker_true_costs.py:106-107` classifies any instrument whose MT5 `path` head starts
with `"Cash"` as `index`. FTMO files its oil CFDs under **`Cash II CFD\`**, so `USOIL.cash` and
`UKOIL.cash` are classified `index` and inherit the index class's fitted **zero** commission — while
the identical instruments on redacted_account sit under `Commodities\`, are classified `energy`, and are
**MEASURED at $5.00/lot**. They are the only two instruments where the accounts' classes disagree.

The classifier already carves out exactly this kind of exception for metals (redacted_account files them
under Commodities), so the shape of the fix is established.

**Quantified: +0.0144 R/trade on `energy_agri`** (conf 0.80) at the validation's own stops, against a
net of 0.4675 — about 3 % of the sleeve's edge. Book mean at 1 night moves 0.10982 → 0.10883. **It
does not change any verdict here**, which is why this is reported rather than absorbed:
`W7_RECOST_V1.json:accounts.FTMO.sensitivities.ftmo_oil_charged_redacted_account_rate` carries it, and
regenerating Session J's sealed artifact mid-wave for a 3 % effect is not worth the churn. Filed for
integration.

Strictly, FTMO's own `energy` class (`NATGAS.cash`, `HEATOIL.c`) has commission **`unknown`**, so the
honest statement is: **FTMO oil commission is unmeasured, and the artifact currently reports it as
zero through a path-string match.**

---

## 8. What remains unproven — read this before OD-3

## 8.1 Holding time — measured for one sleeve, evidenced for a second, still an upper bound for the rest

The first version of this document said holding time was "not recoverable from the caches" and reported
everything across a band from zero carry to the sleeve's structural horizon. The first half was right.
The second half was too pessimistic: **the live W7 window measured the carry of three of these eleven
sleeves directly**, and the tree holds that measurement — outside the caches.

### The evidence

Two sources, derived separately: `ultimate_book_runtime_learning_packets.jsonl.gz` (99,112 packets,
151 `position_closed`, at `vps-export-20260725/extracted/05_shadow_logs/`, outside the repo), and
`LIVE_TRADE_ROWS.jsonl` (Session J, built from MT5 `history_deals_get`).

**The broker's realized `swap` field is the load-bearing witness, and it validates perfectly against
its own structure.** Of the 300 rows, 76 cross a broker midnight (`entry_time_broker`.date ≠
`exit_time_broker`.date) and **74 of those carry nonzero swap**; 224 do not cross, and **all 224 are
exactly 0.0 — no false positives.** The two exceptions are a Sat→Sun AVAUSD hold (weekend, nothing
charged) and one SPX500 rounding to 0.00 against its sibling's −0.40. Swap sums close to the cent
against the raw deals export, and no `DEAL_TYPE_INTEREST`/`COMMISSION`/`CHARGE` rows exist anywhere,
so nothing is booked on an unjoined row. The field is what it claims to be.

**Zero of the 41 live JPY-sleeve positions were charged any swap** (`fx_jpy` 0 of 32, `fx_jpy_ny` 0 of
9). `idxrev`: 39 of 59 (66 %) paid, median hold 15.02 h.

### `fx_jpy` — structural, and the premise is measured

`fx_jpy` enters at the close of the 08:45 M15 bar (`INTEG_portfolio_build.py:227-229`, `hour >= 8`,
`iw = lon[3]`) = **09:00**, and `simulate` cannot exit past bar `i+48` (`geometry_lib.py:33,50`), so
the hold ceiling is **21:00 the same broker day** — three hours short of a rollover. Replicating the
index arithmetic on the real M15 series: **0 broker midnights in 292 of 292 sample days.**

**That argument rests entirely on the export's timebase, and an earlier draft of this document got
that wrong.** It claimed the result was robust "under either reading" of the timebase. It is not: if
the column were true UTC, the 21:00 ceiling would be **21:00 UTC = 00:00 broker in summer** — exactly
the rollover instant. So the premise had to be measured, not assumed. Measured from the bars
themselves: the FX week **opens Monday 00:00** (56 of 60 symbol-weeks) and **closes Friday 23:45**
(60 of 60). A UTC column would open Sunday ~21:00. The column is broker-server-local, and the
structural argument stands on that measurement.

### `fx_jpy_ny` — not structural, and it is back in the conditional tier

`fx_jpy_ny` shares the 48-bar ceiling but enters at **16:00** (`session_open_mom(..., 15, 4, ...)`),
so its ceiling is **04:00 the next broker day** — it crosses a midnight on roughly four days in five,
and a Friday entry runs across the weekend close to Monday 04:15, a span of **60.75 h**. Its nine
live positions all closed within 1.26 h and paid nothing, but that is an observation, not a bound.
**It stays carry-conditional, with nine observations on the surviving side.** An earlier draft of this
section promoted it alongside `fx_jpy`; that was wrong and is withdrawn.

### Why the holds transfer at all — same geometry, not an identical specification

Checked field by field rather than assumed:

| | live | validation | |
|---|---|---|---|
| `fx_jpy` horizon / target / stop | `time_stop_bars` 48 M15, `final_target_r` 2.5, stop 1.0×ATR (`ultimate_book/sleeves/fx_jpy.py:84-95`) | `maxbars=48`, `target_dist=2.5*a`, `stop_dist=1.0*a` | ✓ |
| entry hour (broker) | 9 (21 of 22 closes) | 09:00 on 146 of 146 days per symbol | ✓ |
| `idxrev` horizon / target | 960 M15 = 240 h / 0.75 | `MAXBARS=60` H4 = 240 h / `TGT_R=0.75` | ✓ |
| symbols | GBPJPY+USDJPY; UK100/JP225/US30/SPX500/GER40 | the same pairs; the same 8-index pocket | ✓ |

Extra live management is **empirically absent**, which was the obvious objection: all 31 JPY packets
show `policy_selected=time_stop`, `be_trigger_r=2.5` — equal to the target, so break-even is inert —
no trailing, no derisk fired. But "same specification" would still be too strong. Four differences:
the validation's `len(lon) >= 6` session-completeness filter is deliberately dropped live
(`sleeves/fx_jpy.py:56-66`); live adds a `_CATCHUP_GRACE = 2` window with no validation analogue;
live exits fill on ticks against broker-resident SL/TP while the validation is bar-resolution with
stop-wins-ties; and **1 of 32 live entries fired at 06:00 broker rather than 09:00**.

### The limits, including the ones that survived attack

1. **The live sample never reached the ceiling.** Max hold 7.36 h against a 12 h bound; close reasons
   33 `sl` / 7 `tp` / 1 `expert`. It contains **zero observations at the horizon where carry would be
   incurred**, so it measures realized holds in a 13-trading-day window, not structural exposure.
2. **Window.** JPY-family closes span **2026-06-15 → 07-01**, 39 of 41 in June — narrower than the
   packet export's 2026-06-18 → 07-24, which an earlier draft quoted. Contiguity is the redeeming
   feature: the validation's own `fx_jpy` rows end **2026-06-09**, six days earlier.
3. **Sleeve identity is one witness counted twice.** The two sources are genuinely independent on
   *timing* (holds differ by a median 28 s, never exactly) and on *money* (the packets carry no
   monetary fields at all — only `swap_source_status` strings). But both take the sleeve label from
   the MT5 order comment written by the same live runtime, so a misattribution would appear in both
   identically. All 41 JPY rows resolve `exact`, and the combined family — immune to any
   `fx_jpy`/`fx_jpy_ny` mis-split, which matters because one name is a prefix of the other — gives
   n=41, zero swap, median 0.51 h.
4. **Coverage — 3 of 11 sleeves.** 76 of 148 live closes are sleeves this book does not contain.
5. **Poll bias is median-accurate with a heavy tail.** Median 28.1 s over the 89 packets carrying both
   bases, but mean **526 s** and max **9.57 h**; two XAUUSD positions are overstated by 1,247 %. On
   the JPY sleeves specifically the max is **83.7 s**. And the 3 closes whose holds do not derive are
   among the longest in the file (15.7 h, 15.9 h, **87.6 h**), so any median taken from the derived
   sample is biased short. None of this touches the JPY conclusion, which uses the deal-derived holds.

### What it changes

| sleeve | account | net at horizon carry | net at measured carry | |
|---|---|---:|---:|---|
| `fx_jpy` | FTMO | −0.0246 | **+0.0412** | flips — structural + measured |
| `fx_jpy` | redacted_account | −0.1754 | **+0.0196** | flips |
| `fx_jpy_ny` | FTMO | −0.0198 | +0.0462 | conditional; 9 observations on this side |
| `fx_jpy_ny` | redacted_account | −0.1667 | +0.0222 | conditional |
| `idxrev` | FTMO | −0.1541 | −0.0289 | unchanged — negative before any cost |

`idxrev` earns its keep by **validating the carry model**: 0.92 modelled mean nights against 66 % of
its live positions actually charged.

### What no analogy reaches

`metals_softband`, `vp_euidx_pocgrav` and `sub_mid_dn_revert` never fired live. I tried to close them
by analogy — the three live sleeves each used only 4–9 % of their horizon at the median — and **the
attempt refuted itself**: across all twelve live sleeves that fraction runs **0.4 % to 105 %**, three
exceed their nominal horizon (`ny_crypto_momentum` p90 = **271 %**), and `idxrev` is the only
long-horizon sleeve with any live evidence at all. Their band stands exactly as published, and **the
generator re-run remains the only thing that closes them.**

## 8.2 The rest of what remains unproven

**8.2 In-sample selection bias, and it is concentrated.** **46.9 % of the survivor book's edge rests
on 194 trades** — `crypto` (104 trades, 37.7 %, mean gross **1.212 R/trade**, history starts
2024-09-19) and `sub_xvol_pullback` (90 trades, 9.2 %, mean gross **1.307 R/trade**, a cell selected
from a substrate scan). Mean gross R of 1.2–1.3 per trade on a 3R-target geometry implies a ~55 % hit
rate on the target; that is not impossible, but it is the profile of a selected cell, and neither
sleeve has an out-of-sample window. This session did not test it and cannot: **re-costing cannot
detect overfitting, only mispricing.**

**8.3 The live fortnight cannot adjudicate most of this.** Per B63/B99b, **88.5 % of the book's
confidence weight is unmeasured by its own live window**; the measured 11.5 % split JPY-negative and
`idxrev`-positive. So the live evidence neither confirms nor refutes the seven surviving sleeves.
Notably the two the live window *did* measure are the two this re-cost also kills — the only
independent corroboration available, and it is consistent.

**8.4 Coverage.** Of 8,503 rows: **6,398 priced** by `cost_r` from measured broker truth, **1,956
class-transferred** (labelled, with the pool named), **149 unpriced** and never charged zero — agri and
the two FTMO energy symbols whose commission is genuinely `unknown`. Dropping the unpriced rows
entirely moves the FTMO book mean 0.10982 → 0.09090 and keeps every sleeve's tier unchanged.

**8.5 Two conservative directions, and one assumption that measurement contradicts.** Slippage is
charged at Session J's live-geometry R value, which does not rescale with stop distance — on the
validation's wider stops this **over-charges**. The 2026 tick-spread archive applied to a 2015–2026
window is a `TRANSFERRED` act.

The spread is era-scaled here by the row's own price, on the assumption that quoted spread moves with
price level. **The only direct test available contradicts that.** A second same-broker XAUUSD tick
measurement exists in-tree — `ULTIMATE_TICK_SPREAD_GOLD.json`, window 2025-10..2026-04, 1,288,483
ticks, median spread 0.37 — against `TICK_SPREAD_MEASUREMENT.json`'s 0.46 for 2026-06..07. Between the
two windows **price fell ~9–14 % while spread rose 24 %**: the opposite sign to proportionality.
Removing the era rescale entirely costs the FTMO headline **−2.9 %** (0.09604 → ~0.09327 at one night)
and **flips no tier**, so the assumption is decision-invariant here — but it is an assumption that one
in-tree measurement disagrees with, and it should not be carried forward as settled.

**8.6 The gross-cap shed has zero live evidence.** Unchanged from the third review, and outside what
this session could touch.

---

## 9. For the forward packet-emitter work — what this measurement needed and nearly did not get

A separate session is hardening what the VPS emits going forward. This is the backward view: what
the existing export made answerable, and what it did not.

**11.1 Realized `swap` per closed position is the field that decided this, and the packet stream
carries it on only 64 of 151 closes.** The broker-accounting block
(`broker_position_aggregate_swap` / `broker_exit_swap`) is present when exit reconciliation
completed and absent otherwise. I could only get it at full coverage from Session J's separate
`history_deals_get` extraction. **If every `position_closed` packet carried realized swap,
commission and fee, the carry question would be answerable from the packet stream alone** — no
second extraction, no join. This is the single highest-value addition for work of this kind.

**11.2 Broker deal timestamps are on 89 of 151 (59 %).** Where `broker_fill_time_utc` /
`broker_exit_time_utc` are absent, holding time falls back to the book's own observation
timestamps. I measured that fallback at a median of 28 seconds, so it did no harm **here** — but
that is luck, not design, and nothing in the packet tells a reader which basis they are on without
checking for the field. Emitting both timestamps on every close makes hold time broker-truth at
100 % and makes the basis explicit.

**11.3 `policy_clock_elapsed_m15_bars` exists but is backfilled-absent on the older packets** —
`policy_clock_diagnostic` says so in its own words: *"historical packet emitted before policy-clock
capture existed; elapsed/due bars intentionally not fabricated"* (correct behaviour, and worth
noting as such). Universal capture of elapsed-bars-at-close, next to the already-present
`gtos_vnext_dynamic_time_stop_bars`, gives hold-versus-horizon directly, without any timestamp
arithmetic or timezone reasoning.

**11.4 `spread_r` is `None` on all 99,112 packets**, with `slippage_source_status:
"not_measured_in_packet"`. Already on the forward list; recorded here only to confirm it from the
export.

**11.5 The limit no emitter change can lift, stated plainly so it is not mistaken for a gap.**
Eight of this book's eleven sleeves never fired live. No forward emission makes their holding time
decidable, because there is nothing to emit. That needs the generator re-run against
`data/mt5_research_exports/bridge_ftmo_deep_h4_*`, and it is a data fetch rather than a sealed
window.

---

## 10. Claims I made during this session and then withdrew

Kept per `WAVE_3_WORKING_AGREEMENT` §6, and because these are the ones a later reader would otherwise
have to rediscover.

1. **The carry layer had three defects, all pointing the same way, all found by an adversarial
   verifier after the first commit.** (a) `SLEEVE_MAX_NIGHTS` scaled each horizon by **5/7** on the
   reasoning that weekend midnights are not charged. That reads `rollover_nights:239` and stops two
   lines early: `:241-243` collects the weekend on the triple-swap weekday at weight 3.0, so **a full
   week charges seven nights, not five** — every H4 ceiling was understated 1.40×, and the claim that
   the JPY sleeves "cannot pay three nights of carry no matter what is assumed" was simply false (a
   12 h hold crossing a Wednesday midnight charges exactly 3). (b) Class-transferred rows were given a
   frozen *total* cost, so up to 66 % of a sleeve's rows were inert to the carry sweep, one night of
   carry leaked into the published `true_cost_ex_swap_r`, and the published `swap_r_per_night` was
   diluted by the transferred share. (c) `resolve_price` had no timeframe guard — the same M15/H4
   defect as item 5, fixed in `attach_stops` only. All three are corrected; the ceilings are now swept
   from `rollover_nights` itself and asserted in
   `test_night_ceilings_come_from_rollover_nights_not_a_weekday_fraction`.

   **This changed the answer.** Under the corrected ceilings `metals_softband`, `vp_euidx_pocgrav` and
   `sub_mid_dn_revert` move out of "survives" into carry-conditional, and the survivor tier that is
   safe at *any* reachable hold is four sleeves, not seven.

2. **"`survives_at_max_carry`" was a worst case presented as a verdict.** It charged every sleeve's
   structural maximum to every trade and printed the result in a column headed `survives`. Most trades
   exit on stop or target long before their horizon. Replaced with the three-tier scheme and a
   break-even expressed in **hold hours against the maximum possible hold**, which is the unit that
   makes a 12 h sleeve and a 320 h sleeve comparable.

3. **`metals_core` and `energy_agri` were charged a flat class cost. They were not.** This is the
   session's largest error and it survived into the first commit (`98563e83f`). Their generators scale
   the cost per trade by stop tightness — `INTEG_portfolio_build_w3.py:89`,
   `EXEC_exit_variants.py:45` — so `metals_core`'s real charge is ~0.023 R, not 0.0459, and I
   **over-added ~0.023 R to gross on the conf-1.00 sleeve**. Corrected: its `cost_multiple` flips from
   0.93 (over-charged) to **under-charged**, gross 0.9330 → 0.9103, book mean at one night
   0.11123 → 0.10982. *(Those were the values at the moment of that correction; the timeframe-guard
   fix in item 1c moved them again, and `metals_core`'s current multiple is **1.42** — the live table
   in §3 is generated from `W7_RECOST_V1.json` and is the one to read.)* **No sleeve tier changed**,
   but the error
   ran in the optimistic direction and the §0 narrative was wrong.

   **Why the witness scheme missed it, which is the more useful part.** It required ≥2 *identical*
   stop-out rows before it would accept the data witness — so a pair with a genuinely per-trade cost,
   whose stop-outs are all distinct by construction, was recorded as "no independent witness" and fell
   back to the two witnesses that share the defect. **The absence of a mode was the signal, and the
   estimator treated it as missing evidence.** Now inverted: dispersion promotes the whole sleeve to
   per-trade pricing, and a single stop-out that disagrees with source promotes it too
   (`metals_core/XAUAUD`, n=1, 0.014993 against 0.0459). Found by an adversarial verifier, not by me.

4. **"The parity test licenses every restated number in this file."** It does not — it never reads the
   cost path, and it matched to five decimals with the defect above live in the artifact. Corrected in
   §1, and two controls that *are* sensitive to the cost path were added.

5. **"The F39 band collapses entirely under a gross restatement, so it need not be published."**
   Half right, and the half that was wrong matters. The band does not reach the *restatement* — that
   part holds. But it does bear on the **attribution** of the error between F38 and F39, which is what
   a reader of the third review will want. Both readings are published.

6. **"Charging the class-median true cost to unpriced rows is fine because they are only 3 % of the
   book."** Wrong twice. The unpriced set turned out to be 149 rows *after* transfer but 2,100 before
   it, and it is concentrated in `energy_agri` (conf 0.80), not spread thinly. Replaced with three
   explicit policies reported side by side.

7. **First stop-distance tier used in-tree H4 bars for `fx_jpy_ny`.** Those sleeves stop at
   1.0 × ATR14(**M15**); reading an H4 ATR inflated their stop ~5× and divided their commission by 5,
   which showed up as `fx_jpy_ny` costing 0.072 R against `fx_jpy`'s 0.226 R for the same two symbols
   on the same geometry. Caught by the discrepancy, fixed by keying the ATR pools on timeframe, and
   now guarded by `test_jpy_sleeve_stop_is_m15_not_h4`.

8. **"`metals_core`'s cascaded LTF exits never book a clean stop."** False, and it was the excuse that
   let item 1 through. It books **47** clean stops out of 131. They are all *distinct* — which is the
   evidence that its cost is per-trade, not evidence that it has none.

---

## 11. What this session did **not** do

- **It did not decide the book.** Sleeve composition, the dial, and the activation candidate are
  Borhen's at OD-3. `SURVIVOR_BOOK_V1` measures the cost-surviving subset; it does not propose it.
- **It did not land the `broker_net_cost_engine` commission fix** (OD-J1) — R2-bound, and Session J
  already established Stage 1.2 does not need it.
- **The full-suite A/B is now run and committed** — `ab/SESSION_N_AB.md`, **673 bad → 673 bad by
  failure set, 0 regressed, +18 net new passing tests**, both captures hand-checked. It was
  deliberately deferred while Session K held the machine at ~79 MB free, which is the condition that
  produced the killed-capture defect in the first place.
- **It did not read a sealed window.** March remains outcome-unread.
